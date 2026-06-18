# Security Test Cases

1. Receptionist cannot read clinical notes through API.
2. Quality manager cannot view patient phone/address in aggregate dashboard.
3. User from organization A cannot access patient from organization B.
4. Expired session cannot call write endpoint.
5. Missing CSRF token blocks browser state-changing request where applicable.
6. Invalid vital sign payload is rejected.
7. Attempted audit log update/delete is rejected.
8. Export action requires role permission and writes audit event.
9. Logs redact phone, address and free-text PHI.
10. Patient communication without approved template is blocked.
11. Patient communication without consent is blocked.
12. AI feature flag disabled blocks AI routes.
