# Epic 1 – Feature 1.1: Online Application

**User story:** As a prospective student/parent, I want to fill out an online application and upload documents to apply to the Patasala digitally.

## Implemented

### Frontend (`/apply`)
- Multi-step wizard with **large inputs**, **Tamil + English hints**, progress steps
- Branch selection, student/parent/address capture
- **Direct-to-storage uploads** (S3 presigned POST in production; local fallback in dev) with **XHR progress bar**
- Application fee payment (Razorpay when configured; demo mode otherwise)
- Confirmation screen with application reference number

### Backend (`apps/admissions`)
- `AdmissionApplication`, `ApplicationDocument`, `ApplicationPayment` models
- Public APIs secured with per-application `access_token`
- Admin review APIs with RBAC (`admissions.view`, `admissions.approve`)
- S3 presigned upload (bypasses app server for large files)
- Razorpay order + signature verification

## API endpoints

| Audience | Endpoint | Purpose |
|----------|----------|---------|
| Public | `GET /api/v1/admissions/branches/` | Active branches |
| Public | `POST /api/v1/admissions/applications/` | Start application |
| Public | `PATCH /api/v1/admissions/applications/{id}/` | Update draft |
| Public | `POST .../documents/presign/` | Get upload URL |
| Public | `POST .../documents/confirm/` | Confirm upload |
| Public | `POST .../submit/` | Submit for payment |
| Public | `POST .../payment/initiate/` | Start payment |
| Public | `POST .../payment/confirm/` | Complete payment |
| Admin | `GET /api/v1/admissions/admin/applications/` | List applications |
| Admin | `POST .../review/` | Approve / reject |

## Risk mitigations

| Risk | Mitigation |
|------|------------|
| Large uploads timeout | Presigned S3 POST — browser uploads directly to S3; server only issues URLs |
| Server resource strain | No file bytes through Django in production |
| Rural / non-technical users | Large touch targets, bilingual labels, step-by-step wizard, plain language |
| Payment complexity | Demo mode for dev; Razorpay for production |

## Configuration

See `backend/.env.example` for `AWS_*`, `RAZORPAY_*`, `ADMISSION_APPLICATION_FEE`.

## Admin UI

`/dashboard/admissions` — review applications (requires `admissions.view` / `admissions.approve`).

## Tests

```bash
python manage.py test apps.admissions.tests.test_admissions
```
