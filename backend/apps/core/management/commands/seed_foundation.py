from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import AccountStatus, User, UserProfile
from apps.branches.models import Branch, BranchStatus, UserBranchMembership
from apps.rbac.models import Permission, PermissionAction, Role, RolePermission, RoleScopeType, UserRoleAssignment


PERMISSIONS = [
    ("auth", PermissionAction.VIEW, "auth.view", "View authentication settings"),
    ("users", PermissionAction.VIEW, "users.view", "View users"),
    ("users", PermissionAction.ADD, "users.add", "Add users"),
    ("users", PermissionAction.CHANGE, "users.change", "Change users"),
    ("users", PermissionAction.DELETE, "users.delete", "Delete users"),
    ("roles", PermissionAction.VIEW, "roles.view", "View roles"),
    ("roles", PermissionAction.ADD, "roles.add", "Add roles"),
    ("roles", PermissionAction.CHANGE, "roles.change", "Change roles"),
    ("roles", PermissionAction.DELETE, "roles.delete", "Delete roles"),
    ("permissions", PermissionAction.VIEW, "permissions.view", "View permissions"),
    ("branches", PermissionAction.VIEW, "branches.view", "View branches"),
    ("branches", PermissionAction.ADD, "branches.add", "Add branches"),
    ("branches", PermissionAction.CHANGE, "branches.change", "Change branches"),
    ("branches", PermissionAction.DELETE, "branches.delete", "Delete branches"),
    ("audit", PermissionAction.VIEW, "audit.view", "View audit logs"),
    ("admissions", PermissionAction.VIEW, "admissions.view", "View admission applications"),
    ("admissions", PermissionAction.ADD, "admissions.add", "Create admission applications"),
    ("admissions", PermissionAction.CHANGE, "admissions.change", "Change admission applications"),
    ("admissions", PermissionAction.DELETE, "admissions.delete", "Delete admission applications"),
    ("admissions", PermissionAction.APPROVE, "admissions.approve", "Approve or reject applications"),
    ("students", PermissionAction.VIEW, "students.view", "View student enrollments"),
    ("students", PermissionAction.ADD, "students.add", "Create student profiles"),
    ("students", PermissionAction.CHANGE, "students.change", "Manage enrollments and parent links"),
    ("students", PermissionAction.DELETE, "students.delete", "Delete student records"),
    ("academics", PermissionAction.VIEW, "academics.view", "View courses and batches"),
    ("academics", PermissionAction.ADD, "academics.add", "Add courses and batches"),
    ("academics", PermissionAction.CHANGE, "academics.change", "Change courses and batches"),
    ("academics", PermissionAction.DELETE, "academics.delete", "Delete courses and batches"),
    ("scheduling", PermissionAction.VIEW, "scheduling.view", "View teaching calendar"),
    ("scheduling", PermissionAction.ADD, "scheduling.add", "Schedule teaching sessions"),
    ("scheduling", PermissionAction.CHANGE, "scheduling.change", "Manage acharya mappings"),
    ("scheduling", PermissionAction.DELETE, "scheduling.delete", "Cancel teaching sessions"),
    ("curriculum", PermissionAction.VIEW, "curriculum.view", "View curriculum and lessons"),
    ("curriculum", PermissionAction.ADD, "curriculum.add", "Add curriculum content"),
    ("curriculum", PermissionAction.CHANGE, "curriculum.change", "Change and publish syllabi"),
    ("curriculum", PermissionAction.DELETE, "curriculum.delete", "Delete curriculum content"),
    ("learning", PermissionAction.VIEW, "learning.view", "View practice, attendance, exams"),
    ("learning", PermissionAction.ADD, "learning.add", "Submit practice and schedule exams"),
    ("learning", PermissionAction.CHANGE, "learning.change", "Mark attendance and enter scores"),
    ("learning", PermissionAction.APPROVE, "learning.approve", "Review practice submissions"),
    ("certifications", PermissionAction.VIEW, "certifications.view", "View certificates"),
    ("certifications", PermissionAction.APPROVE, "certifications.issue", "Issue certificates"),
    ("donations", PermissionAction.VIEW, "donations.view", "View donations and receipts"),
    ("donations", PermissionAction.ADD, "donations.add", "Record donations"),
    ("hostel", PermissionAction.VIEW, "hostel.view", "View hostel occupancy and rooms"),
    ("hostel", PermissionAction.CHANGE, "hostel.change", "Manage hostel rooms and assignments"),
    ("notifications", PermissionAction.VIEW, "notifications.view", "View notification templates and logs"),
    ("notifications", PermissionAction.CHANGE, "notifications.change", "Manage notification templates"),
    ("community", PermissionAction.VIEW, "community.view", "View community events and forums"),
    ("community", PermissionAction.ADD, "community.add", "RSVP, post, and flag community content"),
    ("community", PermissionAction.CHANGE, "community.change", "Manage community events"),
    ("community", PermissionAction.APPROVE, "community.moderate", "Moderate forum content and flags"),
    ("chant", PermissionAction.VIEW, "chant.view", "View chant evaluation history"),
    ("chant", PermissionAction.ADD, "chant.evaluate", "Submit chant recordings for AI evaluation"),
    ("alumni", PermissionAction.VIEW, "alumni.view", "View alumni directory"),
    ("alumni", PermissionAction.ADD, "alumni.add", "Register as alumni"),
    ("feedback", PermissionAction.VIEW, "feedback.view", "View application development feedback (Super Admin)"),
    ("feedback", PermissionAction.ADD, "feedback.add", "Submit application development feedback (Super Admin)"),
    ("feedback", PermissionAction.CHANGE, "feedback.manage", "Triage application feedback and GitHub issues (Super Admin)"),
    ("gurukulam_feedback", PermissionAction.VIEW, "gurukulam_feedback.view", "View own Gurukulam feedback"),
    ("gurukulam_feedback", PermissionAction.ADD, "gurukulam_feedback.add", "Submit Gurukulam feedback"),
    ("gurukulam_feedback", PermissionAction.CHANGE, "gurukulam_feedback.manage", "Review and respond to Gurukulam feedback"),
]

SYSTEM_ROLES = [
    ("super_admin", "Super Admin", RoleScopeType.GLOBAL, 1000, ["*"]),
    ("branch_admin", "Branch Admin", RoleScopeType.BRANCH, 900, [
        "users.view", "users.add", "users.change",
        "roles.view", "roles.change",
        "permissions.view",
        "branches.view", "branches.change",
        "audit.view",
        "admissions.view", "admissions.change", "admissions.approve",
        "students.view", "students.add", "students.change",
        "academics.view", "academics.add", "academics.change",
        "scheduling.view", "scheduling.add", "scheduling.change",
        "curriculum.view", "curriculum.add", "curriculum.change",
        "learning.view", "learning.change", "learning.approve",
        "certifications.view", "certifications.issue",
        "donations.view", "donations.add",
        "hostel.view", "hostel.change",
        "notifications.view", "notifications.change",
        "community.view", "community.add", "community.change", "community.moderate",
        "chant.view", "chant.evaluate",
        "gurukulam_feedback.view", "gurukulam_feedback.add", "gurukulam_feedback.manage",
    ]),
    ("acharya", "Acharya", RoleScopeType.BRANCH, 500, [
        "users.view", "branches.view", "students.view", "scheduling.view",
        "curriculum.view", "curriculum.add", "curriculum.change",
        "learning.view", "learning.add", "learning.change", "learning.approve",
        "community.view", "community.add", "community.moderate",
        "chant.view",
        "gurukulam_feedback.view", "gurukulam_feedback.add",
    ]),
    ("student", "Student", RoleScopeType.BRANCH, 100, [
        "users.view", "branches.view", "scheduling.view",
        "curriculum.view", "learning.view", "learning.add",
        "community.view", "community.add",
        "chant.view", "chant.evaluate",
        "gurukulam_feedback.view", "gurukulam_feedback.add",
    ]),
    ("parent", "Parent", RoleScopeType.BRANCH, 100, [
        "users.view", "branches.view", "students.view",
        "gurukulam_feedback.view", "gurukulam_feedback.add",
    ]),
    ("donor", "Donor", RoleScopeType.GLOBAL, 100, [
        "users.view", "donations.view",
        "gurukulam_feedback.view", "gurukulam_feedback.add",
    ]),
    ("hostel_warden", "Hostel Warden", RoleScopeType.BRANCH, 400, [
        "users.view", "branches.view", "students.view",
        "hostel.view", "hostel.change",
        "gurukulam_feedback.view", "gurukulam_feedback.add",
    ]),
    ("alumni", "Alumni", RoleScopeType.BRANCH, 200, [
        "users.view", "branches.view",
        "community.view", "community.add",
        "alumni.view", "alumni.add",
        "gurukulam_feedback.view", "gurukulam_feedback.add",
    ]),
]


class Command(BaseCommand):
    help = "Seed Sprint 1 foundation data: permissions, roles, HQ branch, super admin."

    def add_arguments(self, parser):
        parser.add_argument("--admin-email", default="admin@gurukulam.local")
        parser.add_argument("--admin-password", default="Admin@Gurukulam1")

    @transaction.atomic
    def handle(self, *args, **options):
        permission_map = {}
        for module, action, codename, name in PERMISSIONS:
            permission, _ = Permission.objects.get_or_create(
                codename=codename,
                defaults={
                    "module": module,
                    "action": action,
                    "name": name,
                    "is_system": True,
                },
            )
            permission_map[codename] = permission

        all_permissions = list(permission_map.values())
        for code, name, scope, priority, perm_codes in SYSTEM_ROLES:
            role, _ = Role.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "scope_type": scope,
                    "is_system": True,
                    "is_active": True,
                    "priority": priority,
                },
            )
            if perm_codes == ["*"]:
                target_permissions = all_permissions
            else:
                target_permissions = [permission_map[c] for c in perm_codes if c in permission_map]
            for permission in target_permissions:
                RolePermission.objects.get_or_create(role=role, permission=permission)

        branch, _ = Branch.objects.get_or_create(
            code="HQ-01",
            defaults={
                "name": "Headquarters",
                "slug": "headquarters",
                "status": BranchStatus.ACTIVE,
                "city": "Chennai",
                "state": "Tamil Nadu",
                "country": "IN",
                "is_headquarters": True,
            },
        )

        admin_email = options.get("admin_email", "admin@gurukulam.local").lower()
        admin_password = options.get("admin_password", "Admin@Gurukulam1")
        admin_user = User.objects.filter(email=admin_email).first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                email=admin_email,
                password=admin_password,
            )
        else:
            admin_user.account_status = AccountStatus.ACTIVE
            admin_user.email_verified_at = timezone.now()
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.set_password(admin_password)
            admin_user.save()

        UserProfile.objects.filter(user=admin_user).update(
            first_name="Super",
            last_name="Admin",
            display_name="Super Admin",
        )

        super_admin_role = Role.objects.get(code="super_admin")
        UserRoleAssignment.objects.get_or_create(
            user=admin_user,
            role=super_admin_role,
            branch=None,
            defaults={"is_active": True},
        )
        UserBranchMembership.objects.get_or_create(
            user=admin_user,
            branch=branch,
            defaults={"is_primary": True, "is_active": True},
        )

        self.stdout.write(self.style.SUCCESS("Foundation seed completed."))
        self.stdout.write(f"Super admin: {admin_email}")
        self.stdout.write(f"HQ branch: {branch.code}")
