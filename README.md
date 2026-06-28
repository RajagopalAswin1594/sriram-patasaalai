# Digital Veda Gurukulam ERP & Learning Platform

Traditional Veda Patasala management system and learning platform — modular monolith (Django REST + Next.js).

Full product context: [docs/project-context.md](docs/project-context.md)

## Repository structure

```
├── backend/          # Django REST API (18 apps)
├── frontend/         # Next.js admin + portals + public site
├── docs/
│   ├── project-context.md
│   ├── sprint-1/README.md
│   └── epic-*/README.md
└── docker-compose.yml
```

## Quick start

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed_foundation
python manage.py seed_epic2
python manage.py seed_epic5
python manage.py seed_epic6
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

Open **http://localhost:3000**

- **Admin:** `admin@gurukulam.local` / `Admin@Gurukulam1`
- **Public:** `/` (home), `/apply`, `/donate`, `/alumni/register`, `/verify/[code]`

### PostgreSQL (optional)

```bash
docker compose up -d
# DATABASE_URL=postgres://postgres:postgres@localhost:5432/gurukulam
```

## Platform modules (vs project-context.md)

| Module | Backend app | Key routes |
|--------|-------------|------------|
| Admissions | `admissions` | `/apply`, `/dashboard/admissions` |
| Students & Parents | `students`, `accounts` | `/dashboard/students`, `/portal/parent` |
| Acharya & Scheduling | `scheduling`, `academics` | `/portal/acharya`, `/dashboard/scheduling` |
| Curriculum & Media | `curriculum` | `/dashboard/curriculum`, `/curriculum/search/` |
| Learning & Attendance | `learning` | `/dashboard/learning`, `/portal/student` |
| Certifications | `certifications` | `/verify/[code]` |
| Donations | `donations` | `/donate`, `/portal/donor`, `/dashboard/donations` |
| Hostel | `hostel` | `/dashboard/hostel`, `/portal/warden` |
| Notifications | `notifications` | `/dashboard/notifications` |
| Community | `community` | `/portal/community`, `/dashboard/community` |
| Alumni | `alumni` | `/alumni/register`, `/portal/alumni` |
| AI Chant Evaluator | `chant_evaluator` | `/portal/student/chant` |
| Feedback & Issues (dev) | `feedback` | `/dashboard/feedback/*` (Super Admin) |
| Gurukulam Feedback | `gurukulam_feedback` | `/feedback`, `/portal/feedback`, `/dashboard/gurukulam-feedback` |

## Tests

```bash
cd backend
python manage.py test apps.accounts.tests.test_sprint1 apps.learning.tests.test_epic34 apps.donations.tests.test_epic5 apps.community.tests.test_epic6
```

## CI

GitHub Actions runs backend tests and frontend build on push/PR (`.github/workflows/ci.yml`).

## Environment highlights

See `backend/.env.example` for Razorpay, AWS S3, WhatsApp/SMS, and `CHANT_STT_*` for production speech-to-text.
