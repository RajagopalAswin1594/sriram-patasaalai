from rest_framework import serializers

from apps.rbac.models import Permission, Role, UserRoleAssignment


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "codename", "module", "action", "name", "description", "is_system"]


class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)

    class Meta:
        model = Role
        fields = [
            "id",
            "code",
            "name",
            "description",
            "scope_type",
            "is_system",
            "is_active",
            "priority",
            "permissions",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "is_system", "created_at", "updated_at"]


class RoleCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["code", "name", "description", "scope_type", "is_active", "priority"]


class RolePermissionSerializer(serializers.Serializer):
    permission_id = serializers.UUIDField()


class UserRoleAssignmentSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(write_only=True)
    role_id = serializers.UUIDField(write_only=True)
    branch_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    user = serializers.StringRelatedField(read_only=True)
    role = RoleSerializer(read_only=True)
    branch_code = serializers.CharField(source="branch.code", read_only=True, allow_null=True)

    class Meta:
        model = UserRoleAssignment
        fields = [
            "id",
            "user_id",
            "role_id",
            "branch_id",
            "user",
            "role",
            "branch_code",
            "assigned_at",
            "expires_at",
            "is_active",
        ]
        read_only_fields = ["id", "assigned_at", "is_active"]

    def validate(self, attrs):
        from apps.accounts.models import User
        from apps.branches.models import Branch

        user = User.objects.filter(id=attrs.pop("user_id")).first()
        role = Role.objects.filter(id=attrs.pop("role_id")).first()
        branch_id = attrs.pop("branch_id", None)
        branch = Branch.objects.filter(id=branch_id).first() if branch_id else None

        if not user:
            raise serializers.ValidationError({"user_id": "User not found."})
        if not role:
            raise serializers.ValidationError({"role_id": "Role not found."})

        attrs["user"] = user
        attrs["role"] = role
        attrs["branch"] = branch
        return attrs
