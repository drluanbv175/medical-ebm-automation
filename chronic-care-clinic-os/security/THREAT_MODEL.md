# Threat Model

## Assets

- Patient identity data.
- Clinical coordination data.
- Care plans and handouts.
- Audit logs.
- Clinical rules and content approvals.
- User/session data.

## Threats

- Unauthorized cross-organization access.
- Role bypass through direct API calls.
- PHI leakage in logs, exports, screenshots or analytics.
- XSS in patient notes or education content.
- CSRF against state-changing routes.
- Weak password storage.
- Session hijacking.
- Unsafe automation sending treatment content.
- Tampering with audit logs.
- Unapproved clinical rules running in production.

## Required controls

- Password hashing.
- Session expiration.
- Backend RBAC.
- Organization/site scoping.
- Rate limiting.
- CSRF protection where applicable.
- Input validation.
- SQL injection protection via Prisma parameterization.
- XSS escaping and content review.
- Secure headers.
- Encrypted secrets.
- Environment validation.
- Database backup and restore testing.
- No sensitive PHI in logs.
- No PHI sent to public AI API.
