from django.urls import path

from apps.chant_evaluator.views import ChantEvaluateView, ChantEvaluationListView, ChantScorePreviewView

urlpatterns = [
    path("chant/evaluations/", ChantEvaluationListView.as_view()),
    path("chant/evaluate/", ChantEvaluateView.as_view()),
    path("chant/score-preview/", ChantScorePreviewView.as_view()),
]
