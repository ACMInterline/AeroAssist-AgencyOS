# Agency Onboarding Guide

## Before Starting

Confirm the agency owner has the correct invitation and that the agency record is newly created. Historical agencies without an onboarding profile are intentionally exempt and must not be forced through first-time setup.

## Setup Sequence

1. Record the agency and legal names, primary contact, address, country, time zone, and currency.
2. Set normal working days and hours. These provide context for operations and deadlines.
3. Upload a suitable PNG, JPEG, or WEBP logo up to 2 MB, or explicitly keep the default branding.
4. Record email configuration status and choose dashboard and notification preferences. This step does not send a message or configure an external provider.
5. Choose a synthetic demo profile and create the linked demo workspace.
6. Review every setup item and complete onboarding.

Progress is saved after each step. Close and return safely if information is not yet available.

## Validation and Recovery

- Correct invalid contact, country, time-zone, currency, or working-hour values in the same step.
- If logo processing fails, retry with a supported image or use default branding.
- Demo generation is deterministic and idempotent. A safe retry reuses its stable synthetic records.
- Do not complete onboarding while the review step reports missing required setup.

After completion, open **Operations** and follow the [First-day checklist](first-day-checklist.md).
