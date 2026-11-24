import json
from unittest.mock import patch

from django.test import TestCase

from ussd.models import USSDSession
from ussd.views import welcome_message

USER_ID = "AIK12345"


class UssdMenuTests(TestCase):
    def setUp(self):
        patcher = patch("ussd.views.NALO_USER_ID", None)
        patcher.start()
        self.addCleanup(patcher.stop)

    def post(self, userdata, msgtype, session_id="session-1", user_id=USER_ID):
        payload = {
            "USERID": user_id,
            "MSISDN": "233244123456",
            "USERDATA": userdata,
            "MSGTYPE": msgtype,
            "SESSIONID": session_id,
        }
        response = self.client.post(
            "/ussd/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        body = response.json()
        return response, body

    def test_welcome_screen(self):
        response, body = self.post("*920#", True)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(body["MSGTYPE"])
        self.assertEqual(body["MSG"], welcome_message())
        self.assertIn("Hello. Welcome.", body["MSG"])
        self.assertIn("1. Feeling fine", body["MSG"])
        self.assertIn("2. Feeling sad", body["MSG"])
        self.assertIn("3. Feeling frisky", body["MSG"])
        self.assertLessEqual(len(body["MSG"]), 120)

    def test_each_feeling_shows_the_same_reasons(self):
        for choice, feeling in (("1", "fine"), ("2", "sad"), ("3", "frisky")):
            with self.subTest(feeling=feeling):
                self.post("*920#", True, session_id=f"feel-{choice}")
                response, body = self.post(choice, False, session_id=f"feel-{choice}")

                self.assertEqual(response.status_code, 200)
                self.assertTrue(body["MSGTYPE"])
                self.assertIn(f"You are feeling {feeling} because...", body["MSG"])
                self.assertIn("1. Family issues", body["MSG"])
                self.assertIn("2. Money problems", body["MSG"])
                self.assertIn("3. Relationship issues", body["MSG"])
                self.assertLessEqual(len(body["MSG"]), 120)

    def test_family_issues_closes_the_session(self):
        self.post("*920#", True)
        self.post("2", False)
        response, body = self.post("1", False)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(body["MSGTYPE"])
        self.assertEqual(
            body["MSG"],
            "You are feeling sad because of family issues.\nGet well soon.",
        )
        session = USSDSession.objects.get(session_id="session-1")
        self.assertEqual(session.feeling, "sad")
        self.assertEqual(session.reason, "family issues")
        self.assertEqual(session.current_step, "complete")

    def test_fine_closes_with_feel_well_soon(self):
        self.post("*920#", True, session_id="fine-session")
        self.post("1", False, session_id="fine-session")
        response, body = self.post("1", False, session_id="fine-session")

        self.assertFalse(body["MSGTYPE"])
        self.assertEqual(
            body["MSG"],
            "You are feeling fine because of family issues.\nFeel well soon.",
        )

    def test_bad_choice_repeats_the_current_screen(self):
        self.post("*920#", True)
        response, body = self.post("9", False)
        self.assertTrue(body["MSGTYPE"])
        self.assertIn("How are you feeling today?", body["MSG"])

        self.post("1", False)
        response, body = self.post("9", False)
        self.assertTrue(body["MSGTYPE"])
        self.assertIn("You are feeling fine because...", body["MSG"])

    def test_string_msgtype_is_accepted(self):
        response, body = self.post("*920#", "true", session_id="string-type")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Hello. Welcome.", body["MSG"])

    def test_any_user_id_is_accepted_when_none_is_configured(self):
        response, body = self.post("*920#", True, user_id="SOMEONE")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Hello. Welcome.", body["MSG"])

    def test_overlong_user_id_is_rejected(self):
        response, body = self.post("*920#", True, user_id="X" * 21)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(body["error"], "Invalid USERID")

    @patch("ussd.views.NALO_USER_ID", "AIK12345")
    def test_wrong_user_id_is_rejected_when_one_is_configured(self):
        response, body = self.post("*920#", True, user_id="SOMEONE")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(body["error"], "Invalid USERID")