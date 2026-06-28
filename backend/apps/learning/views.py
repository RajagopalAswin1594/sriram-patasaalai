from django.conf import settings
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User, UserType
from apps.academics.models import Batch
from apps.core.branch_scope import branch_scoped_queryset
from apps.core.context import set_audit_context
from apps.core.media_storage import MediaStorageService, PRACTICE_AUDIO_TYPES
from apps.curriculum.models import Lesson
from apps.learning.models import Exam, PracticeSubmission, PracticeStatus
from apps.learning.serializers import (
    AttendanceMarkSerializer,
    AttendanceSessionSerializer,
    ExamScoreSerializer,
    ExamScoreWriteSerializer,
    ExamSerializer,
    PracticePresignSerializer,
    PracticeReviewSerializer,
    PracticeSubmissionSerializer,
    TranscriptSerializer,
)
from apps.learning.services import AttendanceService, ExamScoreService, PracticeReviewService
from apps.rbac.permissions import require_permission
from apps.rbac.services import PermissionService


class PracticeListView(generics.ListAPIView):
    permission_classes = [require_permission("learning.view")]
    serializer_class = PracticeSubmissionSerializer

    def get_queryset(self):
        qs = PracticeSubmission.objects.select_related("student", "batch").filter(is_deleted=False)
        qs = branch_scoped_queryset(self.request.user, qs)
        if self.request.user.user_type == UserType.STUDENT:
            qs = qs.filter(student=self.request.user)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs.order_by("-created_at")

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({"success": True, "data": response.data})


class PracticePresignView(APIView):
    permission_classes = [require_permission("learning.add")]

    def post(self, request):
        serializer = PracticePresignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        batch = generics.get_object_or_404(Batch, id=data["batch_id"])
        lesson = None
        if data.get("lesson_id"):
            lesson = generics.get_object_or_404(Lesson, id=data["lesson_id"])
        presigned = MediaStorageService.generate_presigned_upload(
            "practice",
            request.user.id,
            data["file_name"],
            data["content_type"],
            data["file_size"],
            allowed_types=PRACTICE_AUDIO_TYPES,
            max_mb=getattr(settings, "PRACTICE_MAX_AUDIO_MB", 25),
        )
        submission = PracticeSubmission.objects.create(
            student=request.user,
            batch=batch,
            lesson=lesson,
            title=data["title"],
            file_name=data["file_name"],
            content_type=data["content_type"],
            file_size=data["file_size"],
            s3_bucket=presigned["bucket"],
            s3_key=presigned["key"],
        )
        return Response({"success": True, "data": {"submission_id": str(submission.id), "upload": presigned}})


class PracticeReviewView(APIView):
    permission_classes = [require_permission("learning.approve")]

    def post(self, request, id):
        submission = generics.get_object_or_404(PracticeSubmission, id=id, is_deleted=False)
        serializer = PracticeReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        submission = PracticeReviewService.review(
            submission,
            request.user,
            serializer.validated_data["feedback"],
            serializer.validated_data.get("oral_grade", ""),
        )
        return Response({"success": True, "data": PracticeSubmissionSerializer(submission).data})


class AttendanceMarkView(APIView):
    permission_classes = [require_permission("learning.change")]

    def post(self, request):
        serializer = AttendanceMarkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        batch = generics.get_object_or_404(Batch, id=data["batch_id"])
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        session = AttendanceService.mark_session(
            batch,
            data["session_date"],
            request.user,
            data["records"],
            data.get("notes", ""),
        )
        from apps.learning.models import AttendanceSession

        session = AttendanceSession.objects.prefetch_related("records__student").get(id=session.id)
        return Response({"success": True, "data": AttendanceSessionSerializer(session).data})


class AttendanceAlertsView(APIView):
    permission_classes = [require_permission("learning.view")]

    def get(self, request):
        batch_id = request.query_params.get("batch_id")
        batch = generics.get_object_or_404(Batch, id=batch_id)
        alerts = AttendanceService.low_attendance_students(batch)
        return Response({"success": True, "data": alerts})


class ExamListCreateView(generics.ListCreateAPIView):
    permission_classes = [require_permission("learning.view")]
    serializer_class = ExamSerializer

    def get_queryset(self):
        qs = Exam.objects.filter(is_deleted=False)
        return branch_scoped_queryset(self.request.user, qs)

    def get_permissions(self):
        if self.request.method == "POST":
            return [require_permission("learning.add")()]
        return super().get_permissions()

    def perform_create(self, serializer):
        set_audit_context(actor=self.request.user, branch=getattr(self.request, "branch", None))
        serializer.save(acharya=self.request.user)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({"success": True, "data": response.data})

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({"success": True, "data": response.data}, status=201)


class ExamScoreUpsertView(APIView):
    permission_classes = [require_permission("learning.change")]

    def post(self, request):
        serializer = ExamScoreWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        exam = generics.get_object_or_404(Exam, id=data["exam_id"])
        student = generics.get_object_or_404(User, id=data["student_id"], user_type=UserType.STUDENT)
        set_audit_context(actor=request.user, branch=getattr(request, "branch", None))
        score = ExamScoreService.upsert_score(
            exam,
            student,
            data["score"],
            data.get("oral_grade", ""),
            data.get("notes", ""),
            entered_by=request.user,
            reason=data.get("reason", ""),
        )
        return Response({"success": True, "data": ExamScoreSerializer(score).data})


class TranscriptGenerateView(APIView):
    permission_classes = [require_permission("learning.view")]

    def post(self, request):
        student_id = request.data.get("student_id")
        batch_id = request.data.get("batch_id")
        student = generics.get_object_or_404(User, id=student_id, user_type=UserType.STUDENT)
        batch = generics.get_object_or_404(Batch, id=batch_id)
        transcript = ExamScoreService.generate_transcript(student, batch)
        return Response({"success": True, "data": TranscriptSerializer(transcript).data})


class StudentProgressView(APIView):
    permission_classes = [require_permission("learning.view")]

    def get(self, request):
        from apps.certifications.models import Certificate
        from apps.learning.models import AttendanceRecord, ExamScore, PracticeSubmission

        student_id = request.query_params.get("student_id")
        if student_id and request.user.user_type != UserType.STUDENT:
            student = generics.get_object_or_404(User, id=student_id, user_type=UserType.STUDENT)
        else:
            student = request.user

        practice_count = PracticeSubmission.objects.filter(student=student, is_deleted=False).count()
        attendance_present = AttendanceRecord.objects.filter(
            student=student, status="PRESENT", is_deleted=False
        ).count()
        attendance_total = AttendanceRecord.objects.filter(student=student, is_deleted=False).count()
        exam_scores = ExamScore.objects.filter(student=student, is_deleted=False).select_related("exam")
        certificates = Certificate.objects.filter(student=student, is_deleted=False).count()

        return Response({
            "success": True,
            "data": {
                "student_id": str(student.id),
                "practice_submissions": practice_count,
                "attendance": {
                    "present": attendance_present,
                    "total": attendance_total,
                    "rate": round(attendance_present / attendance_total * 100, 1) if attendance_total else 0,
                },
                "exam_scores": [
                    {"exam_title": s.exam.title, "score": str(s.score), "oral_grade": s.oral_grade}
                    for s in exam_scores[:10]
                ],
                "certificates_issued": certificates,
            },
        })


class AttendanceReportView(APIView):
    permission_classes = [require_permission("learning.view")]

    def get(self, request):
        from django.db.models import Count

        from apps.learning.models import AttendanceRecord, AttendanceSession

        batch_id = request.query_params.get("batch_id")
        qs = AttendanceSession.objects.filter(is_deleted=False)
        if batch_id:
            qs = qs.filter(batch_id=batch_id)
        sessions = qs.order_by("-session_date")[:30]
        report = []
        for session in sessions:
            records = AttendanceRecord.objects.filter(session=session, is_deleted=False)
            counts = records.values("status").annotate(c=Count("id"))
            status_map = {row["status"]: row["c"] for row in counts}
            report.append({
                "session_id": str(session.id),
                "batch_id": str(session.batch_id),
                "session_date": session.session_date.isoformat(),
                "present": status_map.get("PRESENT", 0),
                "absent": status_map.get("ABSENT", 0),
                "late": status_map.get("LATE", 0),
                "excused": status_map.get("EXCUSED", 0),
            })
        return Response({"success": True, "data": report})

