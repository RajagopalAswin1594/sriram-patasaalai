from django.urls import path

from apps.academics.views import (
    AcademicYearListCreateView,
    BatchDetailView,
    BatchListCreateView,
    ShakhaListCreateView,
    VedicCourseListCreateView,
)

urlpatterns = [
    path("academics/shakhas/", ShakhaListCreateView.as_view(), name="shakha-list"),
    path("academics/academic-years/", AcademicYearListCreateView.as_view(), name="academic-year-list"),
    path("academics/courses/", VedicCourseListCreateView.as_view(), name="course-list"),
    path("academics/batches/", BatchListCreateView.as_view(), name="batch-list"),
    path("academics/batches/<uuid:id>/", BatchDetailView.as_view(), name="batch-detail"),
]
