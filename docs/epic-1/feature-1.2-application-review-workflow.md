# Epic 1 – Feature 1.2: Application Review Workflow

**User story:** As a Branch Admin, I want to review incoming applications, approve/reject them, and trigger notifications.

## Implemented

### State machine
| From | To | Trigger |
|------|-----|---------|
| `PAYMENT_PENDING` | `PENDING` | Payment confirmed |
| `PENDING` | `APPROVED` | Branch admin approval |
| `PENDING` | `REJECTED` | Branch admin rejection |

Legacy `UNDER_REVIEW` is treated as `PENDING` for compatibility.

Every transition is recorded in **`ApplicationStatusHistory`** (append-only audit trail).

### Admin dashboard (`/dashboard/admissions`)
- Stats cards: Pending, Approved, Rejected, Stale (>7 days), Total
- Filter tabs: All / Pending / Approved / Rejected
- Review modal with rejection reason + internal notes
- Detail page: `/dashboard/admissions/[id]` with full PII, status timeline, notification log
- Branch-scoped: branch admins only see their branch applications

### Notifications
| Event | Channels |
|-------|----------|
| Application pending review | Email + WhatsApp |
| Approved | Email + WhatsApp |
| Rejected | Email + WhatsApp (includes reason) |

All sends logged in **`ApplicationNotification`** (success/failure audit).

- **Email:** Django mail backend (console in dev)
- **WhatsApp:** Stub logs in dev; enable via `WHATSAPP_ENABLED=true` + API URL/token

### GDPR / privacy
- **Consent required** on `/apply` (`data_consent`, `data_consent_at`, `data_consent_version`)
- **PII masking** on list API for users without `admissions.change` / `admissions.approve`
- Full PII on detail view for authorized reviewers only
- Internal `review_notes` never sent to applicants

### Stale application detection
`GET /api/v1/admissions/admin/stats/` returns `stale_pending` — applications in Pending >7 days.

## API endpoints (admin)

| Method | Endpoint | Permission |
|--------|----------|------------|
| GET | `/admissions/admin/applications/` | `admissions.view` |
| GET | `/admissions/admin/applications/{id}/` | `admissions.view` |
| GET | `/admissions/admin/stats/` | `admissions.view` |
| GET | `/admissions/admin/applications/{id}/history/` | `admissions.view` |
| POST | `/admissions/admin/applications/{id}/review/` | `admissions.approve` |
| POST | `/admissions/admin/applications/{id}/assign/` | `admissions.change` |

## Configuration

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
DEFAULT_FROM_EMAIL=admissions@yourdomain.com
WHATSAPP_ENABLED=false
WHATSAPP_API_URL=
WHATSAPP_API_TOKEN=
DATA_CONSENT_VERSION=v1.0
```

## Tests

```bash
python manage.py test apps.admissions.tests.test_review_workflow apps.admissions.tests.test_admissions
```

## Risk mitigations

| Risk | Mitigation |
|------|------------|
| Stuck in pending without audit | `ApplicationStatusHistory` on every transition; stale counter in stats |
| GDPR / data privacy | Consent capture, PII masking on lists, role-gated full PII access, notification audit log |
