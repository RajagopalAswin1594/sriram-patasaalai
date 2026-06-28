from apps.feedback.github_sync import GitHubSyncResult, IntegrationMessage


def feedback_api_response(feedback, messages: list[IntegrationMessage] | None = None, github_sync: GitHubSyncResult | None = None, **extra):
    from apps.feedback.serializers import FeedbackSerializer

    payload = {
        "success": True,
        "data": FeedbackSerializer(feedback).data,
        "messages": [m.as_dict() for m in (messages or [])],
    }
    if github_sync is not None:
        payload["github_sync"] = github_sync.as_dict()
    payload.update(extra)
    return payload
