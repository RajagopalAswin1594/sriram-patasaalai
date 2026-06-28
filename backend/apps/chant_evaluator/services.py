import re
import unicodedata
from difflib import SequenceMatcher

from django.conf import settings
from django.db import transaction

from apps.chant_evaluator.models import ChantEvaluation, EvaluationMode
from apps.core.media_storage import MediaStorageService


class SanskritPhoneticScorer:
    DIACRITIC_REPLACEMENTS = {
        "ā": "a", "ī": "i", "ū": "u", "ṛ": "r", "ṝ": "r", "ḷ": "l", "ḹ": "l",
        "ē": "e", "ō": "o", "ṃ": "m", "ḥ": "h", "ś": "s", "ṣ": "s", "ṭ": "t",
        "ḍ": "d", "ṇ": "n", "ñ": "n",
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
    }

    @classmethod
    def normalize(cls, text: str) -> str:
        if not text:
            return ""
        text = unicodedata.normalize("NFKD", text.lower())
        for src, dst in cls.DIACRITIC_REPLACEMENTS.items():
            text = text.replace(src, dst)
        text = re.sub(r"[^a-z\s]", "", text)
        return re.sub(r"\s+", " ", text).strip()

    @classmethod
    def syllables(cls, text: str) -> list[str]:
        normalized = cls.normalize(text)
        if not normalized:
            return []
        return [s for s in re.split(r"[\s|]+", normalized) if s]

    @classmethod
    def score(cls, reference: str, spoken: str) -> dict:
        ref_syllables = cls.syllables(reference)
        spoken_syllables = cls.syllables(spoken)
        ref_joined = " ".join(ref_syllables)
        spoken_joined = " ".join(spoken_syllables)
        overall = round(SequenceMatcher(None, ref_joined, spoken_joined).ratio() * 100, 1)

        syllable_scores = []
        max_len = max(len(ref_syllables), len(spoken_syllables), 1)
        for i in range(max_len):
            ref = ref_syllables[i] if i < len(ref_syllables) else ""
            spk = spoken_syllables[i] if i < len(spoken_syllables) else ""
            if ref and spk:
                s = round(SequenceMatcher(None, ref, spk).ratio() * 100, 1)
            elif ref or spk:
                s = 0.0
            else:
                s = 100.0
            syllable_scores.append({"index": i + 1, "expected": ref, "spoken": spk, "score": s})

        feedback = cls._feedback(overall, syllable_scores)
        return {
            "phonetic_score": overall,
            "syllable_scores": syllable_scores,
            "normalized_reference": ref_joined,
            "normalized_spoken": spoken_joined,
            "feedback": feedback,
        }

    @staticmethod
    def _feedback(overall: float, syllable_scores: list) -> str:
        weak = [s for s in syllable_scores if s["score"] < 70 and s["expected"]]
        if overall >= 90:
            return "Excellent pronunciation. Maintain this clarity and rhythm."
        if overall >= 75:
            return "Good effort. Focus on the highlighted syllables for refinement."
        if weak:
            parts = ", ".join(f"'{s['expected']}'" for s in weak[:3])
            return f"Practice these syllables slowly: {parts}."
        return "Keep practicing with the reference audio. Match vowel length and stress."


class ChantTranscriptionService:
    @classmethod
    def transcribe(cls, audio_bytes: bytes, reference_text: str) -> tuple[str, str]:
        api_url = getattr(settings, "CHANT_STT_API_URL", "")
        if api_url and getattr(settings, "CHANT_STT_ENABLED", False):
            import requests

            response = requests.post(
                api_url,
                headers={"Authorization": f"Bearer {getattr(settings, 'CHANT_STT_API_TOKEN', '')}"},
                files={"audio": ("chant.webm", audio_bytes, "audio/webm")},
                data={"language": "sa", "reference": reference_text},
                timeout=30,
            )
            response.raise_for_status()
            return response.json().get("transcript", ""), EvaluationMode.AI

        return cls._demo_transcribe(reference_text), EvaluationMode.DEMO

    @classmethod
    def _demo_transcribe(cls, reference_text: str) -> str:
        syllables = SanskritPhoneticScorer.syllables(reference_text)
        if not syllables:
            return reference_text
        mutated = []
        for i, syl in enumerate(syllables):
            if i == len(syllables) // 3 and len(syl) > 2:
                mutated.append(syl[:-1])
            else:
                mutated.append(syl)
        return " ".join(mutated)


class ChantEvaluationService:
    @classmethod
    @transaction.atomic
    def evaluate(cls, student, reference_text: str, audio_bytes: bytes, lesson=None, duration_seconds=None):
        transcribed, mode = ChantTranscriptionService.transcribe(audio_bytes, reference_text)
        result = SanskritPhoneticScorer.score(reference_text, transcribed)

        s3_key = MediaStorageService.build_key("chant_evaluations", student.id, "recording.webm")
        if MediaStorageService.is_s3_enabled():
            import boto3

            client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME,
            )
            bucket = settings.AWS_STORAGE_BUCKET_NAME
            client.put_object(Bucket=bucket, Key=s3_key, Body=audio_bytes, ContentType="audio/webm")
            audio_bucket = bucket
        else:
            from apps.certifications.services import _BytesFile

            MediaStorageService.save_local_file(s3_key, _BytesFile(audio_bytes, "recording.webm"))
            audio_bucket = "local"

        return ChantEvaluation.objects.create(
            student=student,
            lesson=lesson,
            reference_text=reference_text,
            transcribed_text=transcribed,
            phonetic_score=result["phonetic_score"],
            syllable_scores=result["syllable_scores"],
            feedback=result["feedback"],
            evaluation_mode=mode,
            audio_s3_bucket=audio_bucket,
            audio_s3_key=s3_key,
            duration_seconds=duration_seconds,
        )
