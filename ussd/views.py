import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import USSDSession

# Create your views here.

feelings = {
    '1': 'Fine',
    '2': 'Sad',
    '3': 'Feeling frisky'
}


reasons = {
    'Fine': [
        'Good news or achievement',
        'Good family relationships',
        'Everything is going well'
    ],

    'Sad': [
        'Relationship issues',
        'Money problems',
        'Family issues'
    ],

    'Feeling frisky': [
        'Feeling romantic',
        'Feeling playful',
        'Feeling energetic'
    ]
}




@csrf_exempt
def ussd_handler(request):

    # Only accept POST requests
    if request.method != 'POST':
        return JsonResponse(
            {'error': 'POST request required'},
            status=405
        )

    # Read and validate incoming JSON
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {'error': 'Invalid JSON data'},
            status=400
        )

    if not isinstance(data, dict):
        return JsonResponse(
            {'error': 'JSON data must be an object'},
            status=400
        )

    # Check required fields
    required_fields = ['USERID', 'MSISDN', 'SESSIONID']

    for field in required_fields:
        if not data.get(field):
            return JsonResponse(
                {'error': f'Missing required field: {field}'},
                status=400
            )

    # Get incoming request values
    user_id = data.get('USERID')
    phone_number = data.get('MSISDN')
    user_input = data.get('USERDATA', '')
    session_id = data.get('SESSIONID')
    incoming_msg_type = data.get('MSGTYPE')

    # Validate NALO USERID
    if not isinstance(user_id, str) or user_id != 'AIK12345':
        return JsonResponse(
            {'error': 'Invalid USERID'},
            status=400
        )

    # Validate phone number
    if not isinstance(phone_number, str) or len(phone_number) != 12:
        return JsonResponse(
            {'error': 'MSISDN must be 12 characters'},
            status=400
        )

    # Validate user input
    if not isinstance(user_input, str) or len(user_input) > 120:
        return JsonResponse(
            {'error': 'Invalid USERDATA'},
            status=400
        )

   
    # Validate session ID
    if not isinstance(session_id, str) or not session_id or len(session_id) > 100:
        return JsonResponse(
            {'error': 'Invalid SESSIONID'},
            status=400
        )

    # Validate incoming message type (NALO supports bool or 1/0)
    if isinstance(incoming_msg_type, int) and incoming_msg_type in (0, 1):
        incoming_msg_type = bool(incoming_msg_type)
    elif not isinstance(incoming_msg_type, bool):
        return JsonResponse(
            {'error': 'MSGTYPE must be a boolean (true/false or 1/0)'},
            status=400
        )


    # Find an existing session or create a new one
    session, created = USSDSession.objects.get_or_create(
        session_id=session_id,
        defaults={
            'user_id': user_id,
            'phone_number': phone_number
        }
    )

    # First screen: display the feeling menu
    if created:

        session.current_step = 'feeling'
        session.save()

        message = (
            f'Welcome to {user_id}\n'
            'How are you feeling today?\n'
            '1. Fine\n'
            '2. Sad\n'
            '3. Feeling frisky'
        )

        msg_type = True

    # Second screen: process the selected feeling
    elif session.current_step == 'feeling':

        if user_input in feelings:

            session.feeling = feelings[user_input]
            session.current_step = 'reason'
            session.save()

            reason_options = reasons[session.feeling]

            message = f'You are feeling {session.feeling}. Why?\n'

            for number, reason in enumerate(reason_options, start=1):
                message += f'{number}. {reason}\n'

        else:

            message = (
                'How are you feeling today?\n'
                '1. Fine\n'
                '2. Sad\n'
                '3. Feeling frisky'
            )

        msg_type = True

    # Third screen: process the selected reason
    elif session.current_step == 'reason':

        reason_options = reasons[session.feeling]

        if user_input in ['1', '2', '3']:

            selected_reason = reason_options[int(user_input) - 1]

            session.reason = selected_reason
            session.current_step = 'complete'
            session.save()

            message = (
                'Thank you!\n'
                f'You are feeling {session.feeling} because: '
                f'{session.reason}'
            )

            msg_type = False

        else:

            message = f'You are feeling {session.feeling}. Why?\n'

            for number, reason in enumerate(reason_options, start=1):
                message += f'{number}. {reason}\n'

            msg_type = True

    # Session already completed
    else:

        message = 'Thank you for using our service.'
        msg_type = False

    # Prepare response for NALO
    response = {
        'USERID': user_id,
        'MSISDN': phone_number,
        'USERDATA': user_input,
        'MSG': message,
        'MSGTYPE': msg_type
    }

    return JsonResponse(response)

   