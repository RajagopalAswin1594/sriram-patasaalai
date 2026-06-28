# Epic 5: Financials, Sponsorships & Operations

Epic 5 adds public donations with Razorpay, branch-scoped hostel management, and a unified notification center.

## Features

### 5.1 Razorpay Donations & Annadanam
- Public donation page: `/donate`
- Categories: Annadanam (Meals), General, Student Sponsorship
- Razorpay order creation + webhook (`POST /api/v1/donations/webhooks/razorpay/`)
- Idempotent webhook processing via `webhook_event_id`
- Auto-generated 12A / 80G PDF receipts (ReportLab) emailed via notification dispatcher

### 5.2 Branch & Hostel Management
- Models: `Hostel`, `HostelRoom`, `RoomAssignment` with `leave_status` and `mess_eligible`
- Admin UI: `/dashboard/hostel` (room mapping, occupancy grid)
- Warden portal: `/portal/warden` (leave toggles sync mess calculations)
- All queries scoped by branch via `HostelService.hostel_queryset`

### 5.3 Unified Notification Center
- App: `apps.notifications`
- Template manager: `/dashboard/notifications`
- Channels: Email (Django/SES), SMS, WhatsApp (stubs unless `SMS_ENABLED` / `WHATSAPP_ENABLED`)
- Idempotency via `NotificationLog.idempotency_key` per channel

## Setup

```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_foundation   # adds donations.*, hostel.*, notifications.* permissions
python manage.py seed_epic5        # categories, templates, sample hostel
```

### Environment (optional)

```
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
ORGANIZATION_LEGAL_NAME=Digital Veda Gurukulam Trust
DONATION_12A_REGISTRATION=12A/XXXX/XXXX
DONATION_80G_REGISTRATION=80G/XXXX/XXXX
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
WHATSAPP_ENABLED=false
SMS_ENABLED=false
```

## API endpoints

| Method | Path | Auth |
|--------|------|------|
| GET | `/donations/categories/` | Public |
| POST | `/donations/initiate/` | Public |
| POST | `/donations/confirm/` | Public |
| POST | `/donations/webhooks/razorpay/` | Webhook signature |
| GET | `/donations/` | `donations.view` |
| GET/POST | `/hostel/hostels/` | `hostel.view` / `hostel.change` |
| GET/POST | `/hostel/rooms/` | `hostel.view` / `hostel.change` |
| GET | `/hostel/occupancy/` | `hostel.view` |
| GET | `/hostel/warden-portal/` | `hostel.view` |
| PATCH | `/hostel/assignments/{id}/leave/` | `hostel.change` |
| GET/POST | `/notifications/templates/` | `notifications.view` / `notifications.change` |
| GET | `/notifications/logs/` | `notifications.view` |
| POST | `/notifications/test-send/` | `notifications.change` |

## Tests

```bash
cd backend
python manage.py test apps.donations.tests.test_epic5
```

## Risk mitigations

- **Webhook failures**: Idempotent `webhook_event_id`; client confirm endpoint as fallback
- **Cross-branch exposure**: `branch_scoped_queryset` on all hostel/donation admin lists
- **Notification loops**: `idempotency_key` unique per channel in `NotificationLog`
