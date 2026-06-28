from django.urls import path

from apps.students.views import (
    BatchTransferView,
    BulkBatchAssignView,
    CreateStudentView,
    MyChildrenView,
    ParentChildLinkListCreateView,
    StudentEnrollmentListView,
)

urlpatterns = [
    path("students/enrollments/", StudentEnrollmentListView.as_view(), name="student-enrollment-list"),
    path("students/create/", CreateStudentView.as_view(), name="student-create"),
    path("students/bulk-batch-assign/", BulkBatchAssignView.as_view(), name="bulk-batch-assign"),
    path("students/batch-transfer/", BatchTransferView.as_view(), name="batch-transfer"),
    path("students/parent-links/", ParentChildLinkListCreateView.as_view(), name="parent-child-links"),
    path("students/my-children/", MyChildrenView.as_view(), name="my-children"),
]
