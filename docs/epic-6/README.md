# Epic 6: Future & Phase 2 Features

## 6.1 Community Events & Forums (`apps/community`)

- **Event calendar** with RSVP tracking and capacity limits
- **Moderated forums** — new threads/posts enter `PENDING` until approved
- **User flagging** — unique flag per user; auto-hide at 3 flags
- **Alumni user type** added to `accounts.UserType`

### Pages
- `/portal/community` — events + forums (students, alumni, acharya, parent)
- `/dashboard/community` — moderation queue (`community.moderate`)

### API
| Method | Path | Permission |
|--------|------|------------|
| GET/POST | `/community/events/` | `community.view` / `community.change` |
| POST | `/community/events/{id}/rsvp/` | `community.add` |
| GET | `/community/forum/categories/` | `community.view` |
| GET/POST | `/community/forum/threads/` | `community.view` / `community.add` |
| GET | `/community/forum/threads/{id}/` | `community.view` |
| POST | `/community/forum/threads/{id}/posts/` | `community.add` |
| POST | `/community/forum/threads/{id}/flag/` | `community.add` |
| GET | `/community/moderation/queue/` | `community.moderate` |
| PATCH | `/community/moderation/threads/{id}/` | `community.moderate` |

## 6.2 AI Chant Evaluator (`apps/chant_evaluator`)

- **Phonetic scoring** — IAST normalization + `SequenceMatcher` per syllable
- **STT integration** — optional external API via `CHANT_STT_ENABLED` + `CHANT_STT_API_URL`
- **Demo mode** — simulates imperfect transcription without ML dependencies
- **Low-latency preview** — `POST /chant/score-preview/` for text-only scoring

### Pages
- `/portal/student/chant` — record, evaluate, syllable heatmap

### API
| Method | Path | Permission |
|--------|------|------------|
| GET | `/chant/evaluations/` | `chant.view` |
| POST | `/chant/evaluate/` | `chant.evaluate` (multipart audio) |
| POST | `/chant/score-preview/` | `chant.evaluate` |

## Setup

```bash
cd backend
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_foundation
.\.venv\Scripts\python.exe manage.py seed_epic6
```

### Optional STT provider

```
CHANT_STT_ENABLED=true
CHANT_STT_API_URL=https://your-stt-provider/transcribe
CHANT_STT_API_TOKEN=...
```

## Tests

```bash
python manage.py test apps.community.tests.test_epic6
```

## Risk mitigations

- **Spam / inappropriate content**: pre-moderation queue + user flags + auto-hide threshold
- **Regional phonetic nuance**: demo mode documents limitations; production uses configurable STT API; syllable-level feedback highlights weak spots without binary pass/fail
