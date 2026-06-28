# Epic 3 & 4 – Curriculum, Media, Learning & Certification

## Epic 3.1 – Course Creation & Lesson Planning
- **Apps:** `curriculum`
- Flat **Module → Lesson** hierarchy (avoids deep nesting query cost)
- **SyllabusVersion** with DRAFT / PUBLISHED / ARCHIVED and fork-on-new-version
- Unicode fields: `title_sa`, `title_ta`, `content_text`
- Resources: PDF, TEXT, VIDEO, AUDIO via presigned S3 / local upload

**UI:** `/dashboard/curriculum`

## Epic 3.2 – Media Repository & Streaming
- `MediaStorageService` + presigned stream URLs
- `MediaPlayer` component: video controls + multi-speed audio (0.75x–2x)
- **Student UI:** `/portal/student/lessons`

## Epic 4.1 – Practice Recording & Feedback
- `PracticeSubmission` with mp3/wav/m4a/webm support
- Acharya review via `learning.approve`
- **Student UI:** `/portal/student/practice` (MediaRecorder)

## Epic 4.2 – Attendance
- `AttendanceSession` + `AttendanceRecord` with optional geotag
- Low-attendance alerts (&lt;75% over 30 days)
- **UI:** `/dashboard/learning` attendance grid

## Epic 4.3 – Exams & Marks
- `Exam`, `ExamScore` with **append-only `ExamScoreRevision`** (no silent overwrites)
- Transcript generation JSON API
- Oral grade field for traditional scales

## Epic 4.4 – Certification
- PDF via ReportLab, unique `verification_code`
- Public verify: `/verify/[code]` → `GET /certifications/verify/{code}/`
- RBAC: `certifications.issue` required to generate

## Setup

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_foundation
python manage.py seed_epic2
```

## Tests

```bash
python manage.py test apps.learning.tests.test_epic34
```
