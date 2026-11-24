# NALO USSD Application

A menu-driven USSD application built with Python and Django, designed to communicate with the NALO USSD gateway.

## Project Overview

This application allows users to interact with a USSD menu using their mobile phones. Users can select how they are feeling and choose a reason that best describes their feelings.

The application receives JSON requests from the NALO gateway and returns JSON responses.

## Features

- Interactive USSD menu.
- User input validation.
- Database-backed USSD session management.
- Dynamic menu options based on user selections.
- Session completion and termination.
- JSON communication with the NALO USSD gateway.

## Technology Stack

- Python 3
- Django
- SQLite for local development
- PostgreSQL for production
- NALO USSD Gateway
- Git and GitHub

## USSD Menu Flow

1. User dials the assigned USSD shortcode.
2. Welcome screen: `Hello. Welcome. How are you feeling today?` with `1. Feeling fine`, `2. Feeling sad`, `3. Feeling frisky`.
3. Reason screen: `You are feeling fine because...` (or sad, or frisky). The same three options are shown every time: `1. Family issues`, `2. Money problems`, `3. Relationship issues`.
4. Final screen ends the session. Example: `You are feeling sad because of family issues.` followed by `Get well soon.` Feeling fine and feeling frisky close with `Feel well soon.`

Point the Nalo callback URL at `https://<your-render-host>/ussd/`. Nalo posts JSON (`USERID`, `MSISDN`, `USERDATA`, `MSGTYPE`, `SESSIONID`) and this app answers with `MSG` and `MSGTYPE` (`true` keeps the session open, `false` ends it).

Set `NALO_USER_ID` to the user id Nalo gave you. The default in this project is `AIK12345`.

## Project Setup

### 1. Clone the repository

```bash
git clone YOUR_REPOSITORY_URL
cd nalo-ussd-project
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
```

### 5. Apply database migrations

```bash
python manage.py migrate
```

### 6. Run the development server

```bash
python manage.py runserver 8001
```

The local USSD endpoint is:

`http://127.0.0.1:8001/ussd/`

## NALO Gateway Communication

The application accepts POST requests containing JSON data, including:

- `USERID`
- `MSISDN`
- `USERDATA`
- `MSGTYPE`
- `SESSIONID`

It returns JSON responses containing:

- `USERID`
- `MSISDN`
- `MSG`
- `MSGTYPE`

## Deployment

The application is prepared for deployment on Render using PostgreSQL for production database storage.

## Author

Isaac Lamptey