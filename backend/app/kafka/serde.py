from __future__ import annotations

import importlib
import struct
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx
from google.protobuf.timestamp_pb2 import Timestamp

from app.config import get_settings
from app.logging import get_logger

logger = get_logger(__name__)

MAGIC_BYTE = 0

TX_RAW_SCHEMA_V1 = '''syntax = "proto3";
package polyphony.events;
import "google/protobuf/timestamp.proto";
message TxRaw {
  string payer_account = 1;
  string payee_account = 2;
  string asset = 3;
  string amount = 4;
  google.protobuf.Timestamp occurred_at = 5;
  string event_id = 6;
  string correlation_id = 7;
}
'''

TX_RAW_SCHEMA_V2 = '''syntax = "proto3";
package polyphony.events;
import "google/protobuf/timestamp.proto";
message TxRaw {
  string payer_account = 1;
  string payee_account = 2;
  string asset = 3;
  string amount = 4;
  google.protobuf.Timestamp occurred_at = 5;
  string event_id = 6;
  string correlation_id = 7;
  optional string payment_memo = 8;
  optional string workspace_id = 9;
  optional string client_id = 10;
}
'''

TX_VALIDATED_SCHEMA = '''syntax = "proto3";
package polyphony.events;
import "google/protobuf/timestamp.proto";
message TxValidated {
  string tx_id = 1;
  string event_id = 2;
  string correlation_id = 3;
  string payer_account = 4;
  string payee_account = 5;
  string asset = 6;
  string amount = 7;
  google.protobuf.Timestamp occurred_at = 8;
  string validation_version = 9;
  string workspace_id = 10;
  optional string payment_memo = 11;
  optional string client_id = 12;
}
'''

LEDGER_ENTRY_BATCH_SCHEMA = '''syntax = "proto3";
package polyphony.events;
import "google/protobuf/timestamp.proto";
message LedgerEntry {
  string tx_id = 1;
  string account_id = 2;
  string side = 3;
  string asset = 4;
  string amount = 5;
  string correlation_id = 6;
  string workspace_id = 7;
  google.protobuf.Timestamp occurred_at = 8;
}
message LedgerEntryBatch {
  string batch_id = 1;
  string tx_id = 2;
  string event_id = 3;
  string correlation_id = 4;
  string workspace_id = 5;
  google.protobuf.Timestamp created_at = 6;
  repeated LedgerEntry entries = 7;
}
'''


@dataclass
class DeserializedMessage:
    schema_id: int
    version: str
    message: Any


class SchemaRegistrySerde:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.registry_url = self.settings.schema_registry_url.rstrip("/")
        self._tx_raw_pb2: Any | None = None
        self._tx_validated_pb2: Any | None = None
        self._ledger_batch_pb2: Any | None = None
        self.schema_ids: dict[str, int] = {}
        self._ensure_generated_modules()

    def _ensure_generated_modules(self) -> None:
        try:
            self._tx_raw_pb2 = importlib.import_module("app.generated.tx_raw_pb2")
            self._tx_validated_pb2 = importlib.import_module("app.generated.tx_validated_pb2")
            self._ledger_batch_pb2 = importlib.import_module("app.generated.ledger_entry_batch_pb2")
            return
        except ModuleNotFoundError:
            self._compile_protos()
            self._tx_raw_pb2 = importlib.import_module("app.generated.tx_raw_pb2")
            self._tx_validated_pb2 = importlib.import_module("app.generated.tx_validated_pb2")
            self._ledger_batch_pb2 = importlib.import_module("app.generated.ledger_entry_batch_pb2")

    def _compile_protos(self) -> None:
        from grpc_tools import protoc
        from pkg_resources import resource_filename

        backend_root = Path(__file__).resolve().parents[2]
        repo_root = backend_root.parents[0]
        proto_dir = repo_root / "proto"
        out_dir = backend_root / "app" / "generated"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "__init__.py").touch()

        includes = resource_filename("grpc_tools", "_proto")
        args = [
            "grpc_tools.protoc",
            f"-I{proto_dir}",
            f"-I{includes}",
            f"--python_out={out_dir}",
            str(proto_dir / "tx_raw.proto"),
            str(proto_dir / "tx_validated.proto"),
            str(proto_dir / "ledger_entry_batch.proto"),
        ]
        result = protoc.main(args)
        if result != 0:
            raise RuntimeError(f"Protobuf generation failed with code {result}")

    def register_schemas(self) -> None:
        last_error: Exception | None = None
        for attempt in range(1, 31):
            try:
                with httpx.Client(timeout=10.0) as client:
                    client.put(
                        f"{self.registry_url}/config/tx_raw-value",
                        json={"compatibility": "BACKWARD"},
                    )
                    self.schema_ids["tx_raw_v1"] = self._register(
                        client,
                        "tx_raw-value",
                        TX_RAW_SCHEMA_V1,
                    )
                    self.schema_ids["tx_raw_v2"] = self._register(
                        client,
                        "tx_raw-value",
                        TX_RAW_SCHEMA_V2,
                    )
                    self.schema_ids["tx_validated"] = self._register(
                        client,
                        "tx_validated-value",
                        TX_VALIDATED_SCHEMA,
                    )
                    self.schema_ids["ledger_entry_batches"] = self._register(
                        client,
                        "ledger_entry_batches-value",
                        LEDGER_ENTRY_BATCH_SCHEMA,
                    )
                    return
            except Exception as exc:
                last_error = exc
                wait_seconds = min(2 * attempt, 10)
                logger.warning(
                    "schema_registry_retry",
                    extra={"attempt": attempt, "wait_seconds": wait_seconds, "error": str(exc)},
                )
                time.sleep(wait_seconds)
        raise RuntimeError(f"schema registration failed: {last_error}")

    def _register(self, client: httpx.Client, subject: str, schema: str) -> int:
        response = client.post(
            f"{self.registry_url}/subjects/{subject}/versions",
            json={"schemaType": "PROTOBUF", "schema": schema},
        )
        response.raise_for_status()
        schema_id = int(response.json()["id"])
        logger.info("registered_schema", extra={"subject": subject, "schema_id": schema_id})
        return schema_id

    @staticmethod
    def _encode_wire(schema_id: int, payload: bytes) -> bytes:
        return bytes([MAGIC_BYTE]) + struct.pack(">I", schema_id) + payload

    @staticmethod
    def _decode_wire(data: bytes) -> tuple[int, bytes]:
        if len(data) < 5:
            raise ValueError("payload too small")
        magic = data[0]
        if magic != MAGIC_BYTE:
            raise ValueError(f"unsupported magic byte: {magic}")
        schema_id = struct.unpack(">I", data[1:5])[0]
        return schema_id, data[5:]

    @staticmethod
    def _to_timestamp(value: datetime) -> Timestamp:
        ts = Timestamp()
        ts.FromDatetime(value.astimezone(timezone.utc))
        return ts

    @staticmethod
    def _from_timestamp(value: Timestamp) -> datetime:
        dt = value.ToDatetime()
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def serialize_tx_raw(self, record: dict[str, Any], force_v1: bool = False) -> bytes:
        if self._tx_raw_pb2 is None:
            raise RuntimeError("protobuf modules not loaded")
        msg = self._tx_raw_pb2.TxRaw(
            payer_account=record["payer_account"],
            payee_account=record["payee_account"],
            asset=record["asset"],
            amount=str(record["amount"]),
            event_id=record["event_id"],
            correlation_id=record["correlation_id"],
        )
        msg.occurred_at.CopyFrom(self._to_timestamp(record["occurred_at"]))
        if record.get("payment_memo"):
            msg.payment_memo = str(record["payment_memo"])
        if record.get("workspace_id"):
            msg.workspace_id = str(record["workspace_id"])
        if record.get("client_id"):
            msg.client_id = str(record["client_id"])

        schema_key = "tx_raw_v1" if force_v1 else "tx_raw_v2"
        schema_id = self.schema_ids[schema_key]
        return self._encode_wire(schema_id, msg.SerializeToString())

    def deserialize_tx_raw(self, payload: bytes) -> DeserializedMessage:
        if self._tx_raw_pb2 is None:
            raise RuntimeError("protobuf modules not loaded")
        schema_id, body = self._decode_wire(payload)
        msg = self._tx_raw_pb2.TxRaw()
        msg.ParseFromString(body)
        version = "v1" if schema_id == self.schema_ids.get("tx_raw_v1") else "v2"
        return DeserializedMessage(schema_id=schema_id, version=version, message=msg)

    def serialize_tx_validated(self, record: dict[str, Any]) -> bytes:
        if self._tx_validated_pb2 is None:
            raise RuntimeError("protobuf modules not loaded")
        msg = self._tx_validated_pb2.TxValidated(
            tx_id=record["tx_id"],
            event_id=record["event_id"],
            correlation_id=record["correlation_id"],
            payer_account=record["payer_account"],
            payee_account=record["payee_account"],
            asset=record["asset"],
            amount=str(record["amount"]),
            validation_version=record["validation_version"],
            workspace_id=record["workspace_id"],
        )
        msg.occurred_at.CopyFrom(self._to_timestamp(record["occurred_at"]))
        if record.get("payment_memo"):
            msg.payment_memo = str(record["payment_memo"])
        if record.get("client_id"):
            msg.client_id = str(record["client_id"])

        schema_id = self.schema_ids["tx_validated"]
        return self._encode_wire(schema_id, msg.SerializeToString())

    def deserialize_tx_validated(self, payload: bytes) -> DeserializedMessage:
        if self._tx_validated_pb2 is None:
            raise RuntimeError("protobuf modules not loaded")
        schema_id, body = self._decode_wire(payload)
        msg = self._tx_validated_pb2.TxValidated()
        msg.ParseFromString(body)
        return DeserializedMessage(schema_id=schema_id, version="v1", message=msg)

    def serialize_ledger_entry_batch(self, record: dict[str, Any]) -> bytes:
        if self._ledger_batch_pb2 is None:
            raise RuntimeError("protobuf modules not loaded")
        batch = self._ledger_batch_pb2.LedgerEntryBatch(
            batch_id=record["batch_id"],
            tx_id=record["tx_id"],
            event_id=record["event_id"],
            correlation_id=record["correlation_id"],
            workspace_id=record["workspace_id"],
        )
        batch.created_at.CopyFrom(self._to_timestamp(record["created_at"]))
        for entry in record["entries"]:
            item = batch.entries.add()
            item.tx_id = entry["tx_id"]
            item.account_id = entry["account_id"]
            item.side = entry["side"]
            item.asset = entry["asset"]
            item.amount = str(entry["amount"])
            item.correlation_id = entry["correlation_id"]
            item.workspace_id = entry["workspace_id"]
            item.occurred_at.CopyFrom(self._to_timestamp(entry["occurred_at"]))

        schema_id = self.schema_ids["ledger_entry_batches"]
        return self._encode_wire(schema_id, batch.SerializeToString())

    def deserialize_ledger_entry_batch(self, payload: bytes) -> DeserializedMessage:
        if self._ledger_batch_pb2 is None:
            raise RuntimeError("protobuf modules not loaded")
        schema_id, body = self._decode_wire(payload)
        msg = self._ledger_batch_pb2.LedgerEntryBatch()
        msg.ParseFromString(body)
        return DeserializedMessage(schema_id=schema_id, version="v1", message=msg)

    def tx_raw_to_dict(self, msg: Any) -> dict[str, Any]:
        return {
            "payer_account": msg.payer_account,
            "payee_account": msg.payee_account,
            "asset": msg.asset,
            "amount": Decimal(msg.amount),
            "occurred_at": self._from_timestamp(msg.occurred_at),
            "event_id": msg.event_id,
            "correlation_id": msg.correlation_id,
            "payment_memo": msg.payment_memo if msg.HasField("payment_memo") else None,
            "workspace_id": msg.workspace_id if msg.HasField("workspace_id") else "default",
            "client_id": msg.client_id if msg.HasField("client_id") else None,
        }

    def tx_validated_to_dict(self, msg: Any) -> dict[str, Any]:
        return {
            "tx_id": msg.tx_id,
            "event_id": msg.event_id,
            "correlation_id": msg.correlation_id,
            "payer_account": msg.payer_account,
            "payee_account": msg.payee_account,
            "asset": msg.asset,
            "amount": Decimal(msg.amount),
            "occurred_at": self._from_timestamp(msg.occurred_at),
            "validation_version": msg.validation_version,
            "workspace_id": msg.workspace_id or "default",
            "payment_memo": msg.payment_memo if msg.HasField("payment_memo") else None,
            "client_id": msg.client_id if msg.HasField("client_id") else None,
        }

    def ledger_batch_to_dict(self, msg: Any) -> dict[str, Any]:
        return {
            "batch_id": msg.batch_id,
            "tx_id": msg.tx_id,
            "event_id": msg.event_id,
            "correlation_id": msg.correlation_id,
            "workspace_id": msg.workspace_id or "default",
            "created_at": self._from_timestamp(msg.created_at),
            "entries": [
                {
                    "tx_id": entry.tx_id,
                    "account_id": entry.account_id,
                    "side": entry.side,
                    "asset": entry.asset,
                    "amount": Decimal(entry.amount),
                    "correlation_id": entry.correlation_id,
                    "workspace_id": entry.workspace_id or "default",
                    "occurred_at": self._from_timestamp(entry.occurred_at),
                }
                for entry in msg.entries
            ],
        }


_serde: SchemaRegistrySerde | None = None


def get_serde() -> SchemaRegistrySerde:
    global _serde
    if _serde is None:
        _serde = SchemaRegistrySerde()
        _serde.register_schemas()
    return _serde
