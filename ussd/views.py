import json
import os

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import USSDSession

# Nalo assigns this id. Override it on Render with NALO_USER_ID.
NALO_USER_ID = os.getenv("NALO_USER_ID")

# Screen 1. The word after "feeling" is what later screens repeat.
FEELINGS = {
    "1": "fine",
    "2": "sad",
    "3": "frisky",
}

# Screen 2. The same three reasons are shown for every feeling.
REASONS = {
    "1": "family issues",
    "2": "money problems",
    "3": "relationship issues",
}

CLOSINGS = {
    "fine": "Feel well soon.",
    "sad": "Get well soon.",
    "frisky": "Feel well soon.",
}


def welcome_message():
    return (
        "Hello. Welcome.\n"
        "How are you feeling today?\n"
        "1. Feeling fine\n"
        "2. Feeling sad\n"
        "3. Feeling frisky"
    )


def reason_message(feeling):
    lines = [f"You are feeling {feeling} because..."]
    for number, reason in REASONS.items():
        lines.append(f"{number}. {reason.capitalize()}")
    return "\n".join(lines)


def closing_message(feeling, reason):
    return (
        f"You are feeling {feeling} because of {reason}.\n"
        f"{CLOSINGS[feeling]}"
    )


def nalo_response(user_id, phone_number, user_input, session_id, message, keep_open):
    return JsonResponse(
        {
            "USERID": user_id,
            "MSISDN": phone_number,
            "USERDATA": user_input,
            "SESSIONID": session_id,
            "MSG": message,
            "MSGTYPE": keep_open,
        }
    )


def as_bool(value):
    """Nalo sends MSGTYPE as true/false, and sometimes as 1/0 or the strings."""
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "1"):
            return True
        if lowered in ("false", "0"):
            return False
    return None


@csrf_exempt
def ussd_handler(request):
    if request.method == "GET":
        return JsonResponse({"status": "ok", "endpoint": "/ussd/"})

    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=405)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "Invalid JSON data"}, status=400)

    if not isinstance(data, dict):
        return JsonResponse({"error": "JSON data must be an object"}, status=400)

    for field in ("USERID", "MSISDN", "SESSIONID"):
        if not data.get(field):
            return JsonResponse({"error": f"Missing required field: {field}"}, status=400)

    user_id = data.get("USERID")
    phone_number = data.get("MSISDN")
    user_input = str(data.get("USERDATA", "")).strip()
    session_id = data.get("SESSIONID")
    incoming_msg_type = as_bool(data.get("MSGTYPE"))

    if not isinstance(user_id, str) or len(user_id) > 20:
        return JsonResponse({"error": "Invalid USERID"}, status=400)

    if NALO_USER_ID and user_id != NALO_USER_ID:
        return JsonResponse({"error": "Invalid USERID"}, status=400)

    if not isinstance(phone_number, str) or len(phone_number) != 12:
        return JsonResponse({"error": "MSISDN must be 12 characters"}, status=400)

    if len(user_input) > 120:
        return JsonResponse({"error": "Invalid USERDATA"}, status=400)

    if not isinstance(session_id, str) or len(session_id) > 100:
        return JsonResponse({"error": "Invalid SESSIONID"}, status=400)

    if incoming_msg_type is None:
        return JsonResponse(
            {"error": "MSGTYPE must be a boolean (true/false or 1/0)"},
            status=400,
        )

    session, created = USSDSession.objects.get_or_create(
        session_id=session_id,
        defaults={
            "user_id": user_id,
            "phone_number": phone_number,
        },
    )

    # MSGTYPE true means the subscriber just dialled. Always start at welcome,
    # even if Nalo reuses a session id.
    if incoming_msg_type or created:
        session.current_step = "feeling"
        session.feeling = ""
        session.reason = ""
        session.save()
        return nalo_response(
            user_id, phone_number, user_input, session_id, welcome_message(), True
        )

    if session.current_step == "feeling":
        feeling = FEELINGS.get(user_input)
        if feeling is None:
            return nalo_response(
                user_id, phone_number, user_input, session_id, welcome_message(), True
            )

        session.feeling = feeling
        session.current_step = "reason"
        session.save()
        return nalo_response(
            user_id,
            phone_number,
            user_input,
            session_id,
            reason_message(feeling),
            True,
        )

    if session.current_step == "reason":
        reason = REASONS.get(user_input)
        if reason is None:
            return nalo_response(
                user_id,
                phone_number,
                user_input,
                session_id,
                reason_message(session.feeling),
                True,
            )

        session.reason = reason
        session.current_step = "complete"
        session.save()
        return nalo_response(
            user_id,
            phone_number,
            user_input,
            session_id,
            closing_message(session.feeling, reason),
            False,
        )

    return nalo_response(
        user_id,
        phone_number,
        user_input,
        session_id,
        "Thank you for using our service.",
        False,
    )
