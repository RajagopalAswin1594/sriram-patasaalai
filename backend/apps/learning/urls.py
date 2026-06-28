from django.urls import path

from apps.learning.views import (
    AttendanceAlertsView,
    AttendanceMarkView,
    AttendanceReportView,
    ExamListCreateView,
    ExamScoreUpsertView,
    PracticeListView,
    PracticePresignView,
    PracticeReviewView,
    StudentProgressView,
    TranscriptGenerateView,
)

urlpatterns = [
    path("learning/practice/", PracticeListView.as_view(), name="practice-list"),
    path("learning/practice/presign/", PracticePresignView.as_view(), name="practice-presign"),
    path("learning/practice/<uuid:id>/review/", PracticeReviewView.as_view(), name="practice-review"),
    path("learning/attendance/mark/", AttendanceMarkView.as_view(), name="attendance-mark"),
    path("learning/attendance/alerts/", AttendanceAlertsView.as_view(), name="attendance-alerts"),
    path("learning/attendance/reports/", AttendanceReportView.as_view(), name="attendance-reports"),
    path("learning/progress/", StudentProgressView.as_view(), name="student-progress"),
    path("learning/exams/", ExamListCreateView.as_view(), name="exam-list"),
    path("learning/exams/scores/", ExamScoreUpsertView.as_view(), name="exam-score-upsert"),
    path("learning/transcripts/generate/", TranscriptGenerateView.as_view(), name="transcript-generate"),
]
