# OrgNexus

A Django web application that replaces Sky's Excel-based registry of
engineering teams. Built for **5COSC021W Software Development Group
Project (CW2)** at the University of Westminster.

**Group 5CS13_C**
- Aditya Mitter (W19869650)
- Noah Gil De Matos Jimenez

---

## What's in here

OrgNexus is a small intranet portal where engineers can:

- discover other engineering teams (search by name, manager, Slack, etc.)
- read a team's mission, members, code repos and contact channels
- explore upstream and downstream team dependencies
- send messages, save drafts, and read an inbox
- schedule meetings and respond to invites
- export a PDF or Excel report of the org
- view two Chart.js dashboards (teams per department, projects per department)

Single user category, with the Django admin used for back-office work.

## Stack

- Django 5.1 (Python 3.12)
- SQLite (mandated by the brief)
- Bootstrap 5 + Bootstrap Icons + a few hundred lines of vanilla JS / custom CSS
- django-axes for brute-force lockout
- reportlab for PDF reports, openpyxl for Excel reports
- Chart.js (CDN) for the analytics page

## Running it

```bash
# 1. Create a virtualenv. We use uv but plain venv works too.
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Migrate and seed.
python manage.py migrate
python manage.py load_seed                 # reads ../04_team_data/team_registry.xlsx

# 3. Create a superuser (or use the seeded one - see below).
python manage.py createsuperuser

# 4. Run the dev server.
python manage.py runserver
```

Open http://127.0.0.1:8000/ and either log in or register a new account.
Email backend defaults to console output, so the verification link will
appear in the terminal where `runserver` is running.

## Test users

After running `load_seed`, you can log in with these accounts (all have
`email_verified=True` and `is_active=True`).

| Username             | Password            | Notes                                      |
| -------------------- | ------------------- | ------------------------------------------ |
| `admin`              | `AdminPassword!1`   | Superuser - full Django admin              |
| `oliviacarter`       | (set on first use)  | Team leader of "Code Warriors"             |
| `sebastianholt`      | (set on first use)  | Department head, xTV_Web                   |

To set a password on a seeded user:

```bash
python manage.py changepassword oliviacarter
```

## Layout

```
orgnexus/             # Django settings package
accounts/             # User model, register, login, profile, password reset
teams/                # Team list, search, detail, dependencies (Aditya)
organisation/         # Department, focus area, org structure (Noah)
messaging/            # Inbox, sent, drafts, send (Noah)
scheduler/            # Meetings, weekly + monthly views (Aditya)
reports/              # PDF + Excel exports (Aditya)
analytics/            # Chart.js endpoints (Aditya)
core/                 # Dashboard, search, audit log signals
templates/            # base.html, navbar, footer, app templates
static/               # orgnexus.css, orgnexus.js
fixtures/             # (empty for now; seed data comes from xlsx)
```

## Tests

```bash
python manage.py test --verbosity=2
```

31 tests cover authentication, team CRUD, search, dependency constraints,
audit-log signals, message + meeting flows and the PDF/XLSX export
endpoints. Each test docstring is laid out as a row in the CW2 report's
test plan (UC ID, pre-condition, steps, expected, post-condition,
priority).

## Security notes

- Passwords stored with PBKDF2 (Django default). Minimum length 10.
- django-axes locks an account after 5 failed sign-ins for 30 min.
- All session and CSRF cookies are HttpOnly and SameSite=Lax.
- `X-Frame-Options: DENY` to defeat clickjacking.
- Email verification on signup; password reset uses Django's signed-token
  flow.
- All views except the home page require `LoginRequiredMixin`.
- See the GROUP report (Section: "Security risks addressed") for the
  full register and the items still outstanding.

## Brief compliance

- 6 Departments seeded (>= 2 required)
- 46 Teams seeded (>= 3 per department required)
- 5 engineers per team (>= 5 required)
- Audit trail: `core.AuditLog` written via Django signals (CREATE / UPDATE / DELETE)
- All "missing use cases" from CW1 feedback are wired to URLs (login,
  logout, register, profile, change password, search, view team details,
  dependencies, contact channels, code repos, send message, inbox,
  schedule meeting, reports, charts).
