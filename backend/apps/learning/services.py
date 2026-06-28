from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.core.exceptions import ConflictError
from apps.learning.models import AttendanceRecord, AttendanceSession, AttendanceStatus, ExamScore, ExamScoreRevision, PracticeStatus, Transcript


class AttendanceService:
    LOW_ATTENDANCE_THRESHOLD = 0.75

    @classmethod
    @transaction.atomic
    def mark_session(cls, batch, session_date, acharya, records: list[dict], notes: str = ""):
        session, _ = AttendanceSession.objects.get_or_create(
            batch=batch,
            session_date=session_date,
            defaults={"acharya": acharya, "notes": notes},
        )
        for item in records:
            AttendanceRecord.objects.update_or_create(
                session=session,
                student_id=item["student_id"],
                defaults={
                    "status": item.get("status", AttendanceStatus.PRESENT),
                    "latitude": item.get("latitude"),
                    "longitude": item.get("longitude"),
                    "marked_offline": item.get("marked_offline", False),
                    "synced_at": timezone.now(),
                },
            )
        return session

    @classmethod
    def low_attendance_students(cls, batch, days=30):
        from datetime import timedelta

        from django.db.models import Count, Q

        cutoff = timezone.now().date() - timedelta(days=days)
        sessions = AttendanceSession.objects.filter(batch=batch, session_date__gte=cutoff, is_deleted=False)
        session_count = sessions.count()
        if session_count == 0:
            return []

        alerts = []
        student_ids = (
            AttendanceRecord.objects.filter(session__in=sessions, is_deleted=False)
            .values_list("student_id", flat=True)
            .distinct()
        )
        for student_id in student_ids:
            present = AttendanceRecord.objects.filter(
                session__in=sessions,
                student_id=student_id,
                status__in=[AttendanceStatus.PRESENT, AttendanceStatus.LATE],
            ).count()
            rate = present / session_count
            if rate < cls.LOW_ATTENDANCE_THRESHOLD:
                alerts.append({"student_id": str(student_id), "attendance_rate": round(rate, 2)})
        return alerts


class ExamScoreService:
    @classmethod
    @transaction.atomic
    def upsert_score(cls, exam, student, score, oral_grade="", notes="", entered_by=None, reason=""):
        existing = ExamScore.objects.select_for_update().filter(exam=exam, student=student, is_deleted=False).first()
        if existing:
            ExamScoreRevision.objects.create(
                exam_score=existing,
                previous_score=existing.score,
                new_score=score,
                previous_oral_grade=existing.oral_grade,
                new_oral_grade=oral_grade,
                changed_by=entered_by,
                reason=reason,
            )
            existing.score = score
            existing.oral_grade = oral_grade
            existing.notes = notes
            existing.revision += 1
            existing.entered_by = entered_by
            existing.save(update_fields=["score", "oral_grade", "notes", "revision", "entered_by", "updated_at"])
            return existing

        return ExamScore.objects.create(
            exam=exam,
            student=student,
            score=score,
            oral_grade=oral_grade,
            notes=notes,
            entered_by=entered_by,
        )

    @classmethod
    @transaction.atomic
    def generate_transcript(cls, student, batch):
        scores = ExamScore.objects.filter(
            student=student,
            exam__batch=batch,
            is_deleted=False,
        ).select_related("exam", "exam__course")
        grades = [
            {
                "exam": score.exam.title,
                "course": score.exam.course.code,
                "score": str(score.score),
                "oral_grade": score.oral_grade,
                "max_score": str(score.exam.max_score),
            }
            for score in scores
        ]
        transcript, _ = Transcript.objects.update_or_create(
            student=student,
            batch=batch,
            defaults={"grades": grades},
        )
        return transcript


class PracticeReviewService:
    @classmethod
    @transaction.atomic
    def review(cls, submission, acharya, feedback: str, oral_grade: str = ""):
        if submission.status == PracticeStatus.REVIEWED:
            raise ConflictError("Submission already reviewed.")
        submission.status = PracticeStatus.REVIEWED
        submission.acharya_feedback = feedback
        submission.oral_grade = oral_grade
        submission.reviewed_by = acharya
        submission.reviewed_at = timezone.now()
        submission.save(
            update_fields=["status", "acharya_feedback", "oral_grade", "reviewed_by", "reviewed_at", "updated_at"]
        )
        return submission
