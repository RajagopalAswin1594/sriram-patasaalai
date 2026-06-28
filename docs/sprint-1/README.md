# Sprint 1 – Foundation Platform

**Project:** Digital Veda Gurukulam ERP & Learning Platform  
**Sprint:** 1 – Foundation Platform  
**Status:** Implemented  
**Stack:** Django REST Framework + PostgreSQL/SQLite + Next.js + TypeScript + Tailwind CSS

---

## 1. Sprint objective

Establish the secure, auditable, multi-branch foundation that all future Gurukulam modules will build on:

- Authentication (JWT, refresh rotation, password lifecycle)
- Role-based access control (RBAC)
- User management (7 personas)
- Role & permission management
- Branch management
- Audit logging (entity changes + auth events)

---

## 2. Deliverables

| Artifact | Location |
|----------|----------|
| Backend API | `backend/` |
| Admin UI | `frontend/` |
| Database migrations | `backend/apps/*/migrations/` |
| Seed data command | `backend/apps/core/management/commands/seed_foundation.py` |
| Docker PostgreSQL | `docker-compose.yml` |
| API tests | `backend/apps/accounts/tests/test_sprint1.py` |
| This document | `docs/sprint-1/README.md` |

---

## 3. Architecture

```mermaid
flowchart TB
    subgraph client [Frontend]
        UI[Next.js Admin UI]
    end
    subgraph api [Backend - Modular Monolith]
        AUTH[accounts - Authentication]
        RBAC[rbac - Roles & Permissions]
        BR[branches - Multi-Branch]
        AUD[audit - Logging]
        CORE[core - AuditableModel]
    end
    DB[(PostgreSQL / SQLite)]

    UI -->|REST /api/v1| AUTH
    UI --> RBAC
    UI --> BR
    UI --> AUD
    AUTH --> CORE
    RBAC --> CORE
    BR --> CORE
    AUD --> DB
    CORE --> DB
```

### Design principles applied

- **UUID** primary keys on all domain entities
- **Soft delete** via `AuditableModel` (`is_deleted`, `deleted_at`, `deleted_by`)
- **Audit-first** — immutable `AuditLog` + `AuthenticationEvent`; auto entity tracking via signals
- **Multi-branch** — `UserBranchMembership` + branch-scoped role assignments
- **Versioned APIs** — all routes under `/api/v1/`
- **RBAC** — permission codenames `{module}.{action}`; super admin bypass with full audit trail

---

## 4. Domain model summary

### 4.1 Users & authentication

| Entity | Purpose |
|--------|---------|
| `User` | Core identity (email login, account status, lockout) |
| `UserProfile` | Shared contact/demographic data |
| `{Type}Profile` | Student, Parent, Acharya, BranchAdmin, Donor, HostelWarden |
| `RefreshToken` | Hashed refresh tokens with rotation & revocation |
| `PasswordResetToken` | Single-use password reset |

**User types:** `STUDENT`, `PARENT`, `ACHARYA`, `BRANCH_ADMIN`, `SUPER_ADMIN`, `DONOR`, `HOSTEL_WARDEN`

**Account statuses:** `PENDING_VERIFICATION`, `ACTIVE`, `INACTIVE`, `SUSPENDED`, `LOCKED`

### 4.2 RBAC

| Entity | Purpose |
|--------|---------|
| `Role` | Named permission set (`GLOBAL` or `BRANCH` scope) |
| `Permission` | Atomic grant (`users.view`, `roles.change`, etc.) |
| `RolePermission` | Role ↔ permission mapping |
| `UserRoleAssignment` | User ↔ role ↔ optional branch |

### 4.3 Branches

| Entity | Purpose |
|--------|---------|
| `Branch` | Gurukulam center (code, status, HQ flag) |
| `UserBranchMembership` | User ↔ branch with primary branch |

### 4.4 Audit

| Entity | Purpose |
|--------|---------|
| `AuditLog` | Append-only entity change log (CREATE/UPDATE/DELETE/RESTORE) |
| `AuthenticationEvent` | Login, logout, token refresh, password events |

---

## 5. API reference

**Base URL:** `http://localhost:8000/api/v1/`  
**Auth header:** `Authorization: Bearer <access_token>`  
**Branch context:** `X-Branch-Id: <uuid>`

### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health/` | No | Health check |
| POST | `/auth/login/` | No | Login → access + refresh tokens |
| POST | `/auth/refresh/` | No | Rotate refresh token |
| POST | `/auth/logout/` | Yes | Revoke refresh token |
| GET | `/auth/me/` | Yes | Current user + permissions |
| POST | `/auth/password-reset/` | No | Request reset (no email enumeration) |
| POST | `/auth/password-reset/confirm/` | No | Confirm reset |
| POST | `/auth/password-change/` | Yes | Change password (revokes sessions) |

### Users

| Method | Endpoint | Permission |
|--------|----------|------------|
| GET/POST | `/users/` | `users.view` / `users.add` |
| GET/PATCH/DELETE | `/users/{id}/` | `users.view` / `users.change` / `users.delete` |
| POST | `/users/{id}/status/` | `users.change` |
| POST | `/users/{id}/verify-email/` | `users.change` |
| POST | `/users/{id}/force-logout/` | `users.change` |

### RBAC

| Method | Endpoint | Permission |
|--------|----------|------------|
| GET | `/permissions/` | `permissions.view` |
| GET/POST | `/roles/` | `roles.view` / `roles.add` |
| GET/PATCH/DELETE | `/roles/{id}/` | `roles.view` / `roles.change` / `roles.delete` |
| POST/DELETE | `/roles/{id}/permissions/` | `roles.change` |
| GET/POST | `/role-assignments/` | `roles.view` / `roles.change` |
| DELETE | `/role-assignments/{id}/` | `roles.change` |

### Branches

| Method | Endpoint | Permission |
|--------|----------|------------|
| GET/POST | `/branches/` | `branches.view` / `branches.add` |
| GET/PATCH/DELETE | `/branches/{id}/` | `branches.view` / `branches.change` / `branches.delete` |
| GET/POST | `/branch-memberships/` | `branches.view` / `branches.change` |
| DELETE | `/branch-memberships/{id}/` | `branches.change` |
| POST | `/users/{user_id}/branches/{branch_id}/set-primary/` | `branches.change` |

### Audit

| Method | Endpoint | Permission |
|--------|----------|------------|
| GET | `/audit/logs/` | `audit.view` |
| GET | `/audit/auth-events/` | `audit.view` |

### Response format

**Success (single resource):**
```json
{ "success": true, "data": { ... } }
```

**Paginated list:**
```json
{ "count": 42, "next": "...", "previous": null, "page": 1, "page_size": 20, "results": [] }
```

**Error:**
```json
{ "success": false, "error": { "code": "domain_error", "message": "..." } }
```

---

## 6. Seeded system data

Run: `python manage.py seed_foundation`

| Item | Value |
|------|-------|
| Super admin | `admin@gurukulam.local` / `Admin@Gurukulam1` |
| HQ branch | `HQ-01` – Headquarters |
| System roles | `super_admin`, `branch_admin`, `acharya`, `student`, `parent`, `donor`, `hostel_warden` |
| Permissions | 15 codenames across `auth`, `users`, `roles`, `permissions`, `branches`, `audit` |

---

## 7. Local development

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed_foundation
python manage.py runserver
```

### PostgreSQL (optional)

```bash
docker compose up -d
# Set in backend/.env:
# DATABASE_URL=postgres://postgres:postgres@localhost:5432/gurukulam
python manage.py migrate
```

### Frontend

```bash
cd frontend
npm install
copy .env.example .env.local
npm run dev
```

Open `http://localhost:3000` → login with seeded admin credentials.

### Run tests

```bash
cd backend
python manage.py test apps.accounts.tests.test_sprint1
```

---

## 8. Security controls (Sprint 1)

| Control | Implementation |
|---------|----------------|
| Password hashing | Argon2id (primary hasher) |
| Password policy | Min 12 chars, complexity validator |
| JWT access TTL | 15 minutes (configurable) |
| Refresh rotation | Old token revoked on refresh |
| Account lockout | 5 failed attempts → 30 min lock |
| Token storage | SHA-256 hash only (never raw) |
| Audit redaction | Passwords/tokens excluded from change diffs |
| CORS | `django-cors-headers` with explicit origins |
| Permission escalation | Cannot assign roles exceeding own permissions |

---

## 9. Frontend (Sprint 1 scope)

| Page | Route | Features |
|------|-------|----------|
| Login | `/login` | JWT auth, error handling |
| Dashboard | `/dashboard` | Session summary, module cards |
| Users | `/dashboard/users` | List, create users |
| Roles | `/dashboard/roles` | List roles + permission counts |
| Branches | `/dashboard/branches` | List, create branches |
| Audit | `/dashboard/audit` | Entity logs + auth events |

Branch selector in header sets `X-Branch-Id` for permission resolution.

---

## 10. Explicitly deferred (post–Sprint 1)

- MFA / SSO / API keys
- Parent–student relationships
- Alumni user type
- Branch hierarchy
- Email delivery for password reset
- Azure DevOps CI/CD pipeline
- AWS production deployment (EC2/RDS/S3)
- Mobile apps

---

## 11. Future module integration

All future sprints must:

1. Register permissions under `{module}.{action}`
2. Extend `AuditableModel` for mutable entities
3. Respect branch scoping via `X-Branch-Id`
4. Emit audit events (automatic via signals for registered models)
5. Use UUID PKs and soft delete

**Next sprint candidates:** Online Admissions, Student Management, Acharya Management.

---

## 12. Acceptance checklist

- [x] JWT login / refresh / logout
- [x] Password reset + change
- [x] Account status management + lockout
- [x] 7 user personas with type profiles
- [x] Dynamic multi-role assignment (branch-scoped + global)
- [x] CRUD permissions per module
- [x] Multi-branch membership + primary branch
- [x] Entity change audit (automatic)
- [x] Login/logout/session audit
- [x] Versioned REST API (`/api/v1/`)
- [x] UUID PKs + soft delete on all domain entities
- [x] Seed command for bootstrap data
- [x] Admin UI (Next.js)
- [x] API integration tests
- [x] Health check endpoint
- [x] CORS for frontend
