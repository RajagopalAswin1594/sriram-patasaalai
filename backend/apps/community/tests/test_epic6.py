from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User, UserType
from apps.branches.models import Branch, UserBranchMembership
from apps.chant_evaluator.services import ChantEvaluationService, SanskritPhoneticScorer
from apps.community.models import CommunityEvent, EventStatus, ForumCategory, ForumThread, ModerationStatus
from apps.community.services import EventService, FlagService, ForumService
from apps.core.management.commands.seed_epic6 import Command as SeedEpic6
from apps.core.management.commands.seed_foundation import Command as SeedFoundation
from apps.rbac.models import Role, UserRoleAssignment


class Epic6Tests(TestCase):
    def setUp(self):
        self.client = APIClient()
        SeedFoundation().handle()
        SeedEpic6().handle()
        self.branch = Branch.objects.first()
        self.student = User.objects.create_user(
            email="epic6student@test.local",
            password="Student@Epic6Test",
            user_type=UserType.STUDENT,
        )
        student_role = Role.objects.get(code="student")
        UserRoleAssignment.objects.create(user=self.student, role=student_role, branch=self.branch, is_active=True)
        self.moderator = User.objects.create_user(
            email="epic6mod@test.local",
            password="Moderator@Epic6T",
            user_type=UserType.ACHARYA,
        )
        for u in (self.student, self.moderator):
            UserBranchMembership.objects.get_or_create(user=u, branch=self.branch, defaults={"is_active": True})

    def test_event_rsvp(self):
        event = CommunityEvent.objects.filter(status=EventStatus.PUBLISHED).first()
        rsvp = EventService.rsvp(event, self.student)
        self.assertEqual(rsvp.status, "GOING")

    def test_forum_moderation_and_flagging(self):
        category = ForumCategory.objects.first()
        thread = ForumService.create_thread(category, self.student, "Test", "Dharma question?")
        self.assertEqual(thread.moderation_status, ModerationStatus.PENDING)
        ForumService.moderate_thread(thread, self.moderator, ModerationStatus.APPROVED)
        thread.refresh_from_db()
        self.assertEqual(thread.moderation_status, ModerationStatus.APPROVED)

        other = User.objects.create_user(email="epic6other@test.local", password="Other@Epic6Test", user_type=UserType.ALUMNI)
        u2 = User.objects.create_user(email="epic6u2@test.local", password="User2@Epic6Test", user_type=UserType.ALUMNI)
        u3 = User.objects.create_user(email="epic6u3@test.local", password="User3@Epic6Test", user_type=UserType.ALUMNI)
        FlagService.flag_thread(thread, other, "Spam content")
        FlagService.flag_thread(thread, u2, "Inappropriate")
        FlagService.flag_thread(thread, u3, "Off-topic")
        thread.refresh_from_db()
        self.assertEqual(thread.moderation_status, ModerationStatus.HIDDEN)

    def test_phonetic_scoring(self):
        ref = "oṃ namo bhagavate vāsudevāya"
        spoken = "om namo bhagavate vasudevaya"
        result = SanskritPhoneticScorer.score(ref, spoken)
        self.assertGreater(result["phonetic_score"], 70)

    def test_chant_evaluation_demo(self):
        ref = "oṃ namo bhagavate vāsudevāya"
        audio = b"fake-audio-bytes"
        evaluation = ChantEvaluationService.evaluate(self.student, ref, audio)
        self.assertGreater(float(evaluation.phonetic_score), 0)
        self.assertEqual(evaluation.evaluation_mode, "DEMO")

    def test_public_event_api(self):
        self.client.force_authenticate(self.student)
        res = self.client.get("/api/v1/community/events/")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data["success"])
