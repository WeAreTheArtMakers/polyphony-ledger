import { redirect } from 'next/navigation';

const SAFE_LANDING_ROUTES = new Set([
  '/sales',
  '/dashboard',
  '/transactions',
  '/ledger',
  '/analytics',
  '/replay',
  '/traces'
]);

export default function HomePage(): null {
  const configuredLandingRoute = process.env.NEXT_PUBLIC_HOME_ROUTE || '/sales';
  const landingRoute = SAFE_LANDING_ROUTES.has(configuredLandingRoute) ? configuredLandingRoute : '/sales';
  redirect(landingRoute);
}
