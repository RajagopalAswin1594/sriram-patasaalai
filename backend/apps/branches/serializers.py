from rest_framework import serializers

from apps.branches.models import Branch, BranchStatus, UserBranchMembership


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = [
            "id",
            "code",
            "name",
            "slug",
            "status",
            "address_line_1",
            "address_line_2",
            "city",
            "state",
            "postal_code",
            "country",
            "phone",
            "email",
            "timezone",
            "is_headquarters",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]


class UserBranchMembershipSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(write_only=True)
    branch_id = serializers.UUIDField(write_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)
    branch_code = serializers.CharField(source="branch.code", read_only=True)

    class Meta:
        model = UserBranchMembership
        fields = [
            "id",
            "user_id",
            "branch_id",
            "user_email",
            "branch_code",
            "is_primary",
            "joined_at",
            "left_at",
            "is_active",
        ]
        read_only_fields = ["id", "joined_at", "left_at", "is_active"]

    def validate(self, attrs):
        from apps.accounts.models import User

        user = User.objects.filter(id=attrs.pop("user_id")).first()
        branch = Branch.objects.filter(id=attrs.pop("branch_id")).first()
        if not user:
            raise serializers.ValidationError({"user_id": "User not found."})
        if not branch:
            raise serializers.ValidationError({"branch_id": "Branch not found."})
        attrs["user"] = user
        attrs["branch"] = branch
        return attrs
