from django.urls import path

from apps.curriculum.views import (
    ContentSearchView,
    LessonListCreateView,
    ModuleListCreateView,
    ResourceConfirmView,
    ResourcePresignView,
    ResourceStreamView,
    SyllabusDetailView,
    SyllabusListCreateView,
    SyllabusPublishView,
    TextResourceCreateView,
)

urlpatterns = [
    path("curriculum/syllabi/", SyllabusListCreateView.as_view(), name="syllabus-list"),
    path("curriculum/syllabi/<uuid:id>/", SyllabusDetailView.as_view(), name="syllabus-detail"),
    path("curriculum/syllabi/<uuid:id>/publish/", SyllabusPublishView.as_view(), name="syllabus-publish"),
    path("curriculum/modules/", ModuleListCreateView.as_view(), name="module-list"),
    path("curriculum/lessons/", LessonListCreateView.as_view(), name="lesson-list"),
    path("curriculum/resources/presign/", ResourcePresignView.as_view(), name="resource-presign"),
    path("curriculum/resources/confirm/", ResourceConfirmView.as_view(), name="resource-confirm"),
    path("curriculum/resources/text/", TextResourceCreateView.as_view(), name="resource-text"),
    path("curriculum/resources/<uuid:id>/stream/", ResourceStreamView.as_view(), name="resource-stream"),
    path("curriculum/search/", ContentSearchView.as_view(), name="content-search"),
]
