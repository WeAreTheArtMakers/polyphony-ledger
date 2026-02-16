# Migration Notes

This demo initializes schema via `backend/app/db/schema.sql` mounted into the Postgres container.

For production:
1. Introduce a migration tool (`alembic` or `golang-migrate`).
2. Keep append-only triggers in all migration paths.
3. Roll out schema registry compatibility updates before producer deploy.
4. Run replay smoke tests after projection schema changes.
