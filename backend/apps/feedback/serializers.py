from rest_framework import serializers

from apps.feedback.models import Feedback, FeedbackAnalysis, FeedbackComment, FeedbackHistory, GitHubIssueMapping


class FeedbackAnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackAnalysis
        fields = (
            "sentiment",
            "ai_category",
            "ai_summary",
            "root_cause_suggestion",
            "confidence",
            "recommended_priority",
            "recommended_team",
            "create_github_issue",
            "raw_analysis",
        )


class GitHubIssueMappingSerializer(serializers.ModelSerializer):
    class Meta:
        model = GitHubIssueMapping
        fields = ("issue_number", "issue_url", "repo", "labels", "state", "sync_mode", "http_status", "api_error", "branch_name", "milestone")


class FeedbackSerializer(serializers.ModelSerializer):
    analysis = FeedbackAnalysisSerializer(read_only=True)
    github_issue = GitHubIssueMappingSerializer(read_only=True)
    duplicate_of_number = serializers.CharField(source="duplicate_of.feedback_number", read_only=True, allow_null=True)

    class Meta:
        model = Feedback
        fields = (
            "id",
            "feedback_number",
            "reporter_id",
            "reporter_email",
            "reporter_type",
            "is_anonymous",
            "branch_id",
            "category",
            "source_module",
            "environment",
            "platform",
            "app_version",
            "browser_device",
            "screen_name",
            "title",
            "description",
            "steps_to_reproduce",
            "expected_result",
            "actual_result",
            "status",
            "severity",
            "priority",
            "duplicate_of_id",
            "duplicate_of_number",
            "assigned_team",
            "analysis",
            "github_issue",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("status", "severity", "priority", "assigned_team", "feedback_number")


class FeedbackSubmitSerializer(serializers.Serializer):
    category = serializers.ChoiceField(choices=[c[0] for c in Feedback._meta.get_field("category").choices], required=False)
    source_module = serializers.ChoiceField(choices=[c[0] for c in Feedback._meta.get_field("source_module").choices], required=False)
    environment = serializers.ChoiceField(choices=[c[0] for c in Feedback._meta.get_field("environment").choices], required=False)
    platform = serializers.ChoiceField(choices=[c[0] for c in Feedback._meta.get_field("platform").choices], required=False)
    app_version = serializers.CharField(required=False, allow_blank=True, max_length=30)
    browser_device = serializers.CharField(required=False, allow_blank=True, max_length=255)
    screen_name = serializers.CharField(required=False, allow_blank=True, max_length=200)
    title = serializers.CharField(max_length=255)
    description = serializers.CharField()
    steps_to_reproduce = serializers.CharField(required=False, allow_blank=True)
    expected_result = serializers.CharField(required=False, allow_blank=True)
    actual_result = serializers.CharField(required=False, allow_blank=True)
    reporter_email = serializers.EmailField(required=False, allow_blank=True)
    is_anonymous = serializers.BooleanField(default=False)


class FeedbackStatusUpdateSerializer(serializers.Serializer):
    status = serializers.CharField()
    reason = serializers.CharField(required=False, allow_blank=True)


class FeedbackCommentSerializer(serializers.ModelSerializer):
    author_email = serializers.CharField(source="author.email", read_only=True, allow_null=True)

    class Meta:
        model = FeedbackComment
        fields = ("id", "body", "author_email", "is_internal", "created_at")


class FeedbackCommentCreateSerializer(serializers.Serializer):
    body = serializers.CharField()
    is_internal = serializers.BooleanField(default=True)


class FeedbackHistorySerializer(serializers.ModelSerializer):
    changed_by_email = serializers.CharField(source="changed_by.email", read_only=True, allow_null=True)

    class Meta:
        model = FeedbackHistory
        fields = ("from_status", "to_status", "changed_by_email", "reason", "occurred_at")
