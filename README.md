# Afah — Task Management Web Application

A full-stack web application built with **Python / Flask** that lets users register, manage personal tasks, receive automated email reminders before deadlines, and watch a live countdown timer that fires an alarm when time runs out.

---

## Table of Contents

1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Project Structure](#project-structure)
4. [Database Schema](#database-schema)
5. [Getting Started](#getting-started)
6. [Configuration](#configuration)
7. [Usage Guide](#usage-guide)
8. [Application Routes](#application-routes)
9. [How Each System Works](#how-each-system-works)

---

## Features

### 1. Authentication System
- **Register** — create an account with a unique username, email, and password (minimum 6 characters). Passwords are hashed with Werkzeug's PBKDF2-SHA256 before being stored.
- **Login** — sign in with either username or email, with an optional *remember me* session.
- **Logout** — session is cleared and the user is redirected to the login page.

### 2. Task Management (CRUD)
- **Create** — add a task with a title, description, deadline, priority (Low / Medium / High), and initial status.
- **Read** — browse all personal tasks on a filterable, sortable dashboard with live stats (total, completed, overdue, high-priority).
- **Update** — edit any field, or quick-switch the status directly from the task list or detail page.
- **Delete** — permanently remove a task with a confirmation prompt.

### 3. Email Reminder System
- A background scheduler runs every **5 minutes** and checks all pending/in-progress tasks.
- Sends a formatted HTML reminder email **24 hours** before the deadline.
- Sends a second reminder email **1 hour** before the deadline.
- Duplicate-send protection: each reminder window is tracked with a boolean flag per task.

### 4. Countdown & Alarm System
- Every task card on the dashboard shows a **live per-second mini countdown**.
- The task detail page shows a large **Days / Hours / Minutes / Seconds** countdown clock.
- When the deadline is reached the page shows a full-screen alarm overlay.
- Optional **browser notification** (Web Notifications API) when the deadline hits.
- Optional **audio alarm** (Web Audio API — no external file needed) when the deadline hits.
- Countdown syncs with the server every 60 seconds to stay accurate.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend framework | Flask 3.0 |
| Database ORM | Flask-SQLAlchemy 3.1 (SQLite) |
| Authentication | Flask-Login 0.6 |
| Password hashing | Werkzeug (PBKDF2-SHA256) |
| Email | Flask-Mail 0.10 |
| Background scheduling | APScheduler 3.10 |
| Environment variables | python-dotenv |
| Frontend UI | Bootstrap 5.3 + Bootstrap Icons |
| Countdown & Alarm | Vanilla JavaScript (Web Audio API, Notifications API) |

---

## Project Structure

```
afah/
├── app.py                  # Application factory, blueprint registration, DB init
├── config.py               # Configuration class (reads from .env)
├── extensions.py           # Shared Flask extensions (db, login_manager, mail)
├── models.py               # SQLAlchemy models: User, Task
├── scheduler.py            # APScheduler setup and email reminder logic
│
├── auth/
│   ├── __init__.py         # Auth blueprint definition
│   └── routes.py           # /auth/register  /auth/login  /auth/logout
│
├── tasks/
│   ├── __init__.py         # Tasks blueprint definition
│   └── routes.py           # Full CRUD routes + countdown JSON endpoint
│
├── templates/
│   ├── base.html           # Shared layout: navbar, flash messages
│   ├── auth/
│   │   ├── login.html
│   │   └── register.html
│   └── tasks/
│       ├── index.html      # Dashboard with filters, stats, mini countdowns
│       ├── create.html     # New task form
│       ├── edit.html       # Edit task form
│       └── detail.html     # Full countdown, alarm controls, status updater
│
├── static/
│   ├── css/style.css       # Custom styles on top of Bootstrap
│   └── js/countdown.js     # All countdown, alarm, and notification logic
│
├── requirements.txt
├── .env.example            # Template for environment variables
├── .gitignore
└── README.md
```

---

## Database Schema

### `users`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER | Primary key |
| username | VARCHAR(64) | Unique, required |
| email | VARCHAR(120) | Unique, required |
| password_hash | VARCHAR(256) | PBKDF2-SHA256 hash |
| created_at | DATETIME | UTC timestamp |

### `tasks`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER | Primary key |
| user_id | INTEGER | Foreign key → users.id |
| title | VARCHAR(128) | Required |
| description | TEXT | Optional |
| deadline | DATETIME | Required |
| priority | VARCHAR(16) | `low` / `medium` / `high` |
| status | VARCHAR(16) | `pending` / `in_progress` / `completed` / `overdue` |
| created_at | DATETIME | UTC timestamp |
| updated_at | DATETIME | Auto-updated on edit |
| reminder_24h_sent | BOOLEAN | Prevents duplicate 24-hour emails |
| reminder_1h_sent | BOOLEAN | Prevents duplicate 1-hour emails |

---

## Getting Started

### Prerequisites
- Python 3.10 or newer — [python.org/downloads](https://www.python.org/downloads/)
- A Gmail account (or any SMTP provider) for email reminders

### Installation

**1. Clone or download the project**
```bash
git clone <repository-url>
cd afah
```

**2. Create and activate a virtual environment**
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up environment variables**
```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```
Then open `.env` and fill in your values (see [Configuration](#configuration)).

**5. Run the application**
```bash
python app.py
```

**6. Open the app**

Navigate to `http://localhost:5000` in your browser.

---

## Configuration

All sensitive values are stored in the `.env` file and are **never committed to version control**.

```env
# Required — change this to a long random string in production
SECRET_KEY=your-secret-key-here

# SMTP settings (example uses Gmail)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password       # Gmail App Password, not your main password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

> **Gmail App Password:** Go to **Google Account → Security → 2-Step Verification → App Passwords** and generate a password for "Mail". Use that 16-character password as `MAIL_PASSWORD`.
>
> Email reminders are optional — the rest of the app works fully without configuring mail.

---

## Usage Guide

### Registering and logging in
1. Visit the app and click **Register**.
2. Fill in a username, email, and password (min 6 characters).
3. Log in with your username or email.

### Creating a task
1. Click **New Task** in the navigation bar.
2. Enter a title, optional description, deadline (date + time), priority, and status.
3. Click **Create Task** — you are taken directly to the task detail page.

### Managing tasks
- The **My Tasks** dashboard shows all your tasks as cards, colour-coded by priority.
- Use the filter bar to narrow by status or priority, and sort by deadline, priority, or created date.
- Click **View** to open the detail page with the full countdown and alarm controls.
- Click the pencil icon to edit, or the trash icon to delete.

### Countdown & Alarm
1. Open a task's detail page — the countdown starts automatically.
2. Click **Enable Alarm** to turn on the audio beep when time runs out.
3. Click **Notify Me** to grant browser notification permission.
4. When the deadline arrives, a full-screen overlay appears, the alarm sounds, and a browser notification is sent.

### Email reminders
- No action is needed — the scheduler runs in the background.
- You will receive an email 24 hours before and again 1 hour before each task's deadline, provided `MAIL_*` is configured in `.env`.

---

## Application Routes

| Method | URL | Description | Auth required |
|---|---|---|---|
| GET | `/` | Redirects to task dashboard | No |
| GET | `/auth/register` | Registration form | No |
| POST | `/auth/register` | Submit registration | No |
| GET | `/auth/login` | Login form | No |
| POST | `/auth/login` | Submit login | No |
| GET | `/auth/logout` | Logout current user | Yes |
| GET | `/tasks/` | Task dashboard (filter/sort) | Yes |
| GET | `/tasks/create` | New task form | Yes |
| POST | `/tasks/create` | Submit new task | Yes |
| GET | `/tasks/<id>` | Task detail + countdown | Yes |
| GET | `/tasks/<id>/edit` | Edit task form | Yes |
| POST | `/tasks/<id>/edit` | Submit task edits | Yes |
| POST | `/tasks/<id>/delete` | Delete a task | Yes |
| POST | `/tasks/<id>/status` | Quick status update | Yes |
| GET | `/tasks/<id>/countdown` | JSON countdown data | Yes |

---

## How Each System Works

### Authentication
Flask-Login manages the user session. On login, `login_user()` stores the user ID in a signed cookie. Every protected route is decorated with `@login_required`, which redirects unauthenticated requests to the login page. Passwords are never stored in plain text — only the Werkzeug hash is saved.

### Task CRUD
Tasks are stored in SQLite via SQLAlchemy. The `Task` model includes computed properties (`is_overdue`, `seconds_until_deadline`) that are used by both the server-rendered templates and the countdown JSON endpoint. Overdue status is recalculated on each dashboard load.

### Email Reminders
`APScheduler` starts a `BackgroundScheduler` thread when the app boots. Every 5 minutes it queries for tasks whose deadline falls within the next 24 hours (or 1 hour) and whose corresponding reminder flag is still `False`. It sends an HTML email via SMTP, then sets the flag to `True` so the email is never sent twice.

### Countdown & Alarm
The browser receives the initial `seconds_until_deadline` value rendered into the HTML by Jinja2. A JavaScript `setInterval` decrements it every second and updates the display. Every 60 seconds, a `fetch()` call to `/tasks/<id>/countdown` re-syncs the value with the server. When the counter reaches zero, the alarm overlay is shown, a browser notification is dispatched (if permitted), and the Web Audio API generates a beep sequence — no audio file is needed.
