# Epic 2 – User & Portal Management

## Feature 2.1: Student Profile & Course Enrollment

### Backend (`apps/students`, `apps/academics`)
- **Shakha** → **VedicCourse** → **Batch** (M2M via `BatchCourse`)
- **StudentBranchEnrollment** + **BatchEnrollment** with `effective_from` / `effective_to` for safe mid-year transfers
- **ParentChildLink** with verified parent→child mapping
- **ParentAccessService** scopes parent API access to linked children only

### APIs
| Method | Endpoint | Permission |
|--------|----------|------------|
| POST | `/students/create/` | `students.add` |
| GET | `/students/enrollments/` | `students.view` |
| POST | `/students/bulk-batch-assign/` | `students.change` |
| POST | `/students/batch-transfer/` | `students.change` |
| GET/POST | `/students/parent-links/` | `students.view` / `students.change` |
| GET | `/students/my-children/` | `students.view` (parent portal) |
| GET/POST | `/academics/shakhas/`, `/courses/`, `/batches/` | `academics.*` |

### Admin UI
- `/dashboard/students` – create active students, bulk batch assignment, parent linking
- `/dashboard/academics` – shakhas, courses, batches

---

## Feature 2.2: Acharya Faculty Allocation & Calendar

### Backend (`apps/scheduling`)
- **AcharyaShakhaSpecialization** – shakha registration per Acharya
- **AcharyaBranchAssignment** – branch mapping
- **TeachingSession** – calendar entries with IANA timezone field
- **Conflict detection** – rejects overlapping sessions for the same Acharya (HTTP 409)

### APIs
| Method | Endpoint | Permission |
|--------|----------|------------|
| POST | `/scheduling/acharyas/register/` | `scheduling.add` |
| POST | `/scheduling/acharyas/mapping/` | `scheduling.change` |
| GET | `/scheduling/acharyas/portal/` | `scheduling.view` (Acharya) |
| GET/POST | `/scheduling/sessions/` | `scheduling.view` / `scheduling.add` |

### UI
- `/dashboard/scheduling` – register Acharya, map branches/shakhas, schedule sessions
- `/portal/acharya` – Acharya teaching calendar, branches, specializations
- `/portal/parent` – linked children only (RBAC-scoped)

---

## Setup

```bash
cd backend
python manage.py migrate
python manage.py seed_foundation   # adds students/academics/scheduling permissions
python manage.py seed_epic2        # shakhas, sample batch
```

Re-run `seed_foundation` on existing DBs to pick up new permission codenames for branch_admin / acharya / parent roles.

## Tests

```bash
python manage.py test apps.students.tests.test_epic2
```
