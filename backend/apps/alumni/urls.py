from django.urls import path

from apps.alumni.views import AlumniDirectoryListView, AlumniMeView, AlumniRegisterView

urlpatterns = [
    path("alumni/register/", AlumniRegisterView.as_view()),
    path("alumni/directory/", AlumniDirectoryListView.as_view()),
    path("alumni/me/", AlumniMeView.as_view()),
]
