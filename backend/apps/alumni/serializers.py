from rest_framework import serializers

from apps.alumni.models import AlumniProfile


class AlumniProfileSerializer(serializers.ModelSerializer):
    email = serializers.CharField(source="user.email", read_only=True)
    display_name = serializers.SerializerMethodField()
    branch_name = serializers.CharField(source="branch.name", read_only=True, allow_null=True)

    class Meta:
        model = AlumniProfile
        fields = (
            "id",
            "user_id",
            "email",
            "display_name",
            "graduation_year",
            "batch_name",
            "branch_id",
            "branch_name",
            "current_city",
            "current_occupation",
            "bio",
            "is_directory_visible",
        )
        read_only_fields = ("user_id",)

    def get_display_name(self, obj):
        return getattr(obj.user.profile, "display_name", obj.user.email)


class AlumniRegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=12, write_only=True)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    phone = serializers.CharField(required=False, allow_blank=True, max_length=20)
    graduation_year = serializers.IntegerField(min_value=1950, max_value=2100)
    batch_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    branch_id = serializers.UUIDField(required=False, allow_null=True)
    current_city = serializers.CharField(required=False, allow_blank=True, max_length=100)
    current_occupation = serializers.CharField(required=False, allow_blank=True, max_length=200)
    bio = serializers.CharField(required=False, allow_blank=True)
    is_directory_visible = serializers.BooleanField(default=True)
