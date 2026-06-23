# Real Hostinger Deployment Notes

These notes record the verified first deployment state. They intentionally omit passwords and secrets.

## Verified State

- VPS OS: Ubuntu 24.04.3 LTS.
- Repository path: `/opt/aeroassist-agencyos`.
- Older AeroAssist app path: `/opt/aeroassist`.
- Older AeroAssist app still owns public port `80`.
- AeroAssist AgencyOS temporary public URL: `http://72.62.52.129:8080`.
- Deployed commit: `168f0d57cc28ac6ee8ad80bbeffa7989a0f0e708`.
- AgencyOS frontend container healthy.
- AgencyOS backend container healthy.
- AgencyOS MongoDB container healthy.
- `/api/health` returns OK.
- `/api/readiness` returns OK.
- Demo auth disabled.
- Seed on startup disabled.
- Seed endpoint disabled.
- Demo accounts endpoint returns 404.
- Demo credentials are rejected.
- Fake credentials are rejected.
- First production platform owner created:
  - email: `nn@avio.sk`
  - role: `platform_owner`
  - status: `active`
- Initial backup completed.
- Post-owner backup completed.
- Container restart persistence test passed.
- Owner survived container restart.
- Older app on port `80` still responded after AgencyOS restart.

## Pending Operations

- VPS reboot is still pending because Ubuntu reports `*** System restart required ***`.
- nginx/TLS/domain routing is not yet configured for AgencyOS.
- Port `8080` exposure is temporary and should not be final production exposure.

## Future Nginx/TLS Direction

Before moving AgencyOS to a final HTTPS domain:

1. Choose the final domain or subdomain.
2. Point DNS A record to `72.62.52.129`.
3. Decide whether the older app should remain on its current domain, move to another domain/subdomain, or be replaced.
4. Keep AgencyOS `FRONTEND_HTTP_PORT=127.0.0.1:8080` once host nginx owns public ports.
5. Update `CORS_ALLOWED_ORIGINS`, `FRONTEND_URL`, and `PUBLIC_APP_URL` to the final HTTPS origin.
6. Configure host nginx from `deploy/hostinger/nginx/aeroassist.conf.example`.
7. Obtain TLS with certbot.
8. Recreate affected containers and run `deploy/hostinger/scripts/smoke_production.sh`.
