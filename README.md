# Gatekeeper System

## Project Overview

Gatekeeper is a secure multi-domain intelligence platform created for CST1510
Coursework Two. It contains two interfaces that share the same SQLite database:

- A Streamlit web application for account access, dashboard visualisation,
  profile management, password recovery, and SmartBoyAI.
- A Rich command-line application for account administration, CSV migration,
  data previews, and exports of the latest safe preview.

The project is written to remain understandable for a first-year Computer
Science demonstration. Security, data access, interface presentation, and
dataset logic are separated into small Python modules.

## Main Features

- Registration and login using bcrypt password hashing.
- Password-strength validation and username validation.
- Normal-user and administrator roles in the CLI.
- Recovery-email management and SendGrid password-reset codes.
- Protected Streamlit Dashboard, Profile, and SmartBoyAI pages.
- Role-protected Admin monitoring page for users, saved results, and database tables.
- Cyber-incident metrics, filters, charts, heatmap, timeline, and paginated table.
- User-selectable dashboard visualisations with all four charts enabled by default.
- Streamlit dashboard summaries saved to the shared SQLite results table.
- SmartBoyAI support for cybersecurity, IT tickets, and dataset questions.
- SQLite storage for users, migrated datasets, and saved results.
- CSV-to-SQLite migration from the required `DATA/` coursework files.
- Rich CLI panels, tables, and coloured status messages.
- Shared text, CSV, and SQLite result-saving helpers.

### Coursework Core and Extensions

The assessed coursework path is registration/login, bcrypt password handling,
SQLite user CRUD, CSV migration, modular `app_model` code, a dynamic Streamlit
dashboard, protected multipage access, and a dataset-aware chat assistant.

Profile management, SendGrid recovery, role-based Admin monitoring, Rich CLI
presentation, theme styling, pagination, heatmaps, and saved dashboard summaries
are extensions. They support the core system rather than replacing any required
coursework feature.

## Project Structure

```text
home.py                         Streamlit entry, login, registration, recovery
main.py                         Rich command-line application
pages/1_dashboard.py            Protected cyber-incident dashboard
pages/2_SmartBoyAI.py           Protected Groq assistant
pages/3_Profile.py              Protected account profile
pages/4_Admin.py                Role-protected monitoring and account management
app_model/db.py                 SQLite connection and data paths
app_model/schema.py             Database table creation
app_model/users.py              User database operations
app_model/security.py           Shared validation and live strength feedback
app_model/email_service.py      SendGrid configuration and email delivery
app_model/recovery.py           Reset-code generation and password recovery
app_model/export_service.py     Text, CSV, and SQLite result saving
app_model/logic/                Dataset migration and query modules
DATA/                           Required CSV files and local SQLite database
DATA/external/                  External threat-intelligence CSV extension
assets/logos/                   Gatekeeper, Dashboard, and SmartBoyAI logos
.streamlit/config.toml          Streamlit interface configuration
```

Forgot Password is intentionally part of `home.py`, not a visible page inside
`pages/`.

## Installation

Python 3.12 or newer is recommended. From the project directory, install the
required packages:

```powershell
python -m pip install -r requirements.txt
```

Using a virtual environment is recommended:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Important direct dependencies include:

- `streamlit` for the web interface.
- `pandas` for CSV and tabular data.
- `altair` for dashboard visualisations.
- `bcrypt` for password hashing and verification.
- `groq` for SmartBoyAI responses.
- `sendgrid` for password-recovery email.
- `twilio` for optional SMS two-factor authentication.
- `rich` for CLI panels, tables, and colours.

## Secrets and API Keys

Create the local secrets file from the provided example:

```powershell
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
```

On macOS or Linux:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Then replace only the placeholder values inside `.streamlit/secrets.toml`.

```toml
GROQ_API_KEY = "your_groq_api_key_here"
SENDGRID_API_KEY = "your_sendgrid_api_key_here"
SENDGRID_FROM_EMAIL = "your_verified_sender_email_here"
ALLOW_LOCAL_RESET_FALLBACK = false
TWILIO_ACCOUNT_SID = "put_your_twilio_account_sid_here"
TWILIO_AUTH_TOKEN = "put_your_twilio_auth_token_here"
TWILIO_VERIFY_SERVICE_SID = "put_your_twilio_verify_service_sid_here"
```

- `GROQ_API_KEY` enables SmartBoyAI.
- `SENDGRID_API_KEY` and `SENDGRID_FROM_EMAIL` enable recovery email delivery.
- The SendGrid sender address must be verified in the SendGrid account.
- `ALLOW_LOCAL_RESET_FALLBACK` is disabled by default. Enable it only for
  intentional local testing when email delivery is unavailable.
- The three Twilio values enable optional SMS 2FA through a Twilio Verify
  Service.

Real keys must be stored only in `.streamlit/secrets.toml` or environment
variables. `.streamlit/secrets.toml` is ignored by Git and must never be
committed. The application displays friendly configuration messages instead of
crashing when Groq, SendGrid, or Twilio keys are missing.

### Obtaining Optional Service Credentials

#### Groq — SmartBoyAI

1. Create or sign in to a GroqCloud account.
2. Open the Groq API Keys page:
   <https://console.groq.com/keys>
3. Select "Create API Key".
4. Copy the generated key into:

```toml
GROQ_API_KEY = "your_key_here"
```

Groq is required only for SmartBoyAI. The rest of Gatekeeper remains usable
without it.

#### SendGrid — Password-Recovery Email

1. Create or sign in to a Twilio SendGrid account.
2. Follow the official API-key instructions:
   <https://www.twilio.com/docs/sendgrid/ui/account-and-settings/api-keys>
3. In SendGrid, open Settings > API Keys and create an API key with permission
   to send mail.
4. Follow the official Single Sender Verification instructions:
   <https://www.twilio.com/docs/sendgrid/ui/sending-email/sender-verification>
5. Verify the email address that will send password-reset messages.
6. Enter the values in `secrets.toml`:

```toml
SENDGRID_API_KEY = "your_sendgrid_key_here"
SENDGRID_FROM_EMAIL = "the_exact_verified_sender_email"
```

The `SENDGRID_FROM_EMAIL` value must match a verified SendGrid sender. SendGrid
is required only for email password recovery.

#### Twilio Verify — Optional SMS Two-Factor Authentication

1. Create or sign in to a Twilio account.
2. Obtain the Account SID and Auth Token from the Twilio Console. Twilio
   documents that these credentials may be used for local testing:
   <https://www.twilio.com/docs/usage/requests-to-twilio>
3. Create a Twilio Verify Service by following:
   <https://www.twilio.com/docs/verify/api/service>
4. Copy the Verify Service SID, which normally begins with `VA`.
5. Enter the values in `secrets.toml`:

```toml
TWILIO_ACCOUNT_SID = "your_account_sid"
TWILIO_AUTH_TOKEN = "your_auth_token"
TWILIO_VERIFY_SERVICE_SID = "your_verify_service_sid"
```

Twilio is optional and is needed only for SMS 2FA. Trial Twilio accounts may
require recipient phone numbers to be verified first.

#### Security Note

Never place real credentials inside `secrets.toml.example`, Python files,
`README.md` or GitHub. Real credentials belong only inside the ignored local
`.streamlit/secrets.toml` file or environment variables.

Markers can run the core application without SendGrid or Twilio credentials.
Features that require an unavailable external service display a safe
configuration message instead of crashing.

## Running the Streamlit App

Run this command from the project directory:

```powershell
python -m streamlit run home.py
```

Using `python -m streamlit` is recommended on Windows because it can work when
the standalone `streamlit.exe` command is blocked or not available on `PATH`.
Open the local address printed in the terminal, normally
`http://localhost:8501`.

The standard workflow is:

1. Register with a username, recovery email, and strong password.
2. Log in to open the protected dashboard.
3. Use the sidebar to open Dashboard, SmartBoyAI, and Profile.
4. Use Profile to update the recovery email, password, or optional SMS 2FA.

## Running the CLI

Run the Rich command-line version with:

```powershell
python main.py
```

The CLI keeps password entry hidden with `getpass`. Administrator-only actions
include user listing, user deletion, CSV migration, and administrator account
management. Logged-in normal users can preview migrated data and manage their
own account credentials. After using the preview option, logged-in users can
export the latest displayed preview as a text file, CSV file, or SQLite
`saved_results` record.

If Rich is missing, the CLI prints:

```text
Please install Rich using: pip install rich
```

## Database Usage

Gatekeeper uses SQLite through `app_model/db.py`. The local database path is:

```text
DATA/project_data.db
```

Tables are created safely with `CREATE TABLE IF NOT EXISTS`. Important tables
include:

- `users`: usernames, bcrypt password hashes, recovery emails, and roles.
- `cyber_incidents`: migrated cyber-incident records.
- `it_tickets`: migrated IT-support ticket records.
- `datasets_metadata`: migrated dataset information.
- `saved_results`: summaries saved by the export helpers and Streamlit dashboard.

The database file is local and ignored by Git. On a fresh setup, the user table
is created automatically. Dataset tables are created when an administrator uses
CLI menu option 6 to migrate the CSV files.

## CSV Usage

The required coursework datasets are stored in `DATA/`:

```text
DATA/cyber_incidents.csv
DATA/datasets_metadata.csv
DATA/it_tickets.csv
```

CLI menu option 6 migrates these files into SQLite. Migration is administrator
only because it writes to and replaces dataset tables. Data preview is
read-only and is available to logged-in users through menu option 7.

The Streamlit dashboard reads cyber-incident data from SQLite, not directly
from the CSV file. If the dashboard reports a missing table, run the CLI
migration first.

## SmartBoyAI

SmartBoyAI does not directly connect to or query SQLite by itself. The Python
and Streamlit application reads project data and creates safe context such as:

- Total cyber incidents.
- Severity, category, and status counts.
- IT-ticket priority and status counts.
- Resolution-time information when available.
- Dataset metadata summaries.
- Bounded CISA KEV summaries and a small number of matching CVE rows.
- Limited matching dashboard rows when needed for a specific question.

This context is passed privately to Groq with the conversation history. The
approach is similar to retrieval-augmented generation, but it is implemented
manually and does not use LangChain.
SmartBoyAI streams Groq response chunks progressively in the Streamlit chat
interface, then stores the completed assistant reply in session history.

SmartBoyAI does not receive passwords, password hashes, API keys, or full raw
user-account tables. It refuses clearly unrelated requests such as recipes,
jokes, food, and football, while allowing questions and follow-ups about the
dashboard, cybersecurity, IT tickets, datasets, and the project database.
It can also answer relevant CISA KEV, CVE, vendor, ransomware, and CWE
questions using bounded context rather than the full external CSV.

## SendGrid Password Recovery

Users provide a recovery email during registration and can update it from the
Profile page. The Forgot Password control is available from the login view.

1. The user enters a username or unique recovery email.
2. Gatekeeper creates a six-digit reset code.
3. SendGrid sends the code to the stored recovery email.
4. The code expires after ten minutes.
5. The new password must pass the shared strength rules.
6. The password is stored as a new bcrypt hash, never as plain text.

Local on-screen reset codes are disabled unless
`ALLOW_LOCAL_RESET_FALLBACK = true` is explicitly configured. If email delivery
fails while fallback is disabled, Gatekeeper shows a safe error message.

## Optional SMS Two-Factor Authentication

SMS 2FA is optional and controlled by each user from the Profile page. It uses
Twilio Verify and does not replace the normal username/password login.

1. The user enters their username and password.
2. Gatekeeper checks the bcrypt password hash first.
3. If SMS 2FA is disabled, login completes normally.
4. If SMS 2FA is enabled, Gatekeeper asks Twilio Verify to send an SMS code.
5. Login is completed only when Twilio returns `approved` for the submitted code.

Phone numbers must use international E.164 format, such as `+23057953519`.
The app does not store SMS codes locally because Twilio handles code generation
and checking. Twilio credentials belong only in `.streamlit/secrets.toml` or
environment variables. Trial Twilio accounts may only send SMS messages to
recipient numbers verified in the Twilio account.

## Rich CLI Presentation

Rich improves terminal readability only. It does not change authentication,
roles, database operations, or password security. The CLI uses Rich for:

- A welcome panel and structured main menu.
- Coloured success, warning, information, and error messages.
- Registered-user tables.
- Dataset-preview tables.
- Export prompts for the latest displayed preview.

## Dashboard Saving and Export Helpers

The shared `app_model/export_service.py` module contains helper functions for:

1. Save to a UTF-8 text file.
2. Save to a CSV file.
3. Save to the SQLite database.

These helpers are reusable project utilities. The CLI uses them to export the
most recent safe dataset preview from option 12. Text and CSV helper outputs are
written to `DATA/exports/`. CSV helper exports preserve supplied rows and add
save metadata. Database helper saves are inserted into `saved_results`, which
stores:

```text
id, username, result_type, title, content, created_at, save_source
```

The protected Streamlit dashboard exposes the current saved-result feature. It
can save its current filtered summary to the same `saved_results` table. The
summary includes the active severity filter, incident total,
category/status/severity counts, and a note explaining that table pagination
does not change the saved totals. Users can view their recent saved dashboard
summaries from the Dashboard page. Users can also select which of the four
dashboard visualisations are displayed without removing any chart.
The visualisations follow standard data-visualisation principles: clear titles,
labelled axes, appropriate chart types, consistent colours, and reduced clutter.

## External CISA KEV Dataset

Gatekeeper includes one final external-data extension using the official CISA
Known Exploited Vulnerabilities Catalog. The local CSV is stored at:

```text
DATA/external/known_exploited_vulnerabilities.csv
```

The source organisation is the Cybersecurity and Infrastructure Security Agency
(CISA). The catalogue source page is:

```text
https://www.cisa.gov/known-exploited-vulnerabilities-catalog
```

This CSV is real public threat-intelligence data, not AI-generated data. It is
an additional extension and does not replace or alter the required coursework
CSV files. The local copy was downloaded on 12 July 2026 and does not update
automatically.

Admin users migrate it with the normal CLI migration option. It is stored in a
separate SQLite table called `cisa_known_exploited_vulnerabilities`, not in
`cyber_incidents`. The dashboard shows a separate CISA KEV section with metrics,
filters, standard charts, a paginated CVE table, and a full-detail CVE expander.

## Admin Monitoring

The role-protected Admin page provides safe system monitoring. Administrators
can update user roles and add or replace recovery emails for users who cannot
reset their password. It also shows whether SMS 2FA and an SMS phone are
configured, without showing full phone numbers. The final administrator cannot
be demoted, and password hashes, reset codes, API keys, and secrets are never
displayed.

## Security and Privacy Notes

- Passwords are hashed with bcrypt before database storage.
- Live password-strength feedback is visual guidance; final validation and
  bcrypt hashing still happen in Python.
- Password hashes are not displayed in user listings.
- Login errors do not reveal whether a username or password was incorrect.
- Optional SMS 2FA starts only after bcrypt password verification succeeds.
- SMS verification codes are checked by Twilio Verify and are not stored locally.
- Streamlit protected pages check authenticated session state.
- CLI administrator actions require a logged-in administrator role.
- Secrets are loaded from ignored local configuration or environment variables.
- Admin monitoring never displays password hashes, reset codes, API keys,
  secrets, or full recovery email addresses. Its controlled write actions are
  limited to validated role and recovery-email updates.
- Native Streamlit text/password inputs do not reliably provide true
  per-keystroke updates for instant feedback. Gatekeeper therefore uses a small
  local frontend component only for the live strength display; final password
  validation and bcrypt hashing remain in Python.
- SmartBoyAI context excludes user accounts, password hashes, and API keys.
- Exported dashboard previews do not include account credentials.

`st.session_state` protects navigation during an active Streamlit browser
session, but it is not a replacement for a production identity provider. This
project is designed for first-year coursework and local demonstration.

## External Dataset Rules

Additional CSV datasets may be used only when all of the following are true:

- The dataset is relevant to the project.
- It is a real dataset, not AI-generated or invented data.
- A clear source link is provided.
- Its licence or usage conditions allow coursework use.
- It does not replace a required coursework CSV when the brief specifies a
  particular file.

Keep the required coursework CSV filenames and paths visible in their dataset
logic modules.

## Troubleshooting

### Missing packages

```powershell
python -m pip install -r requirements.txt
```

Make sure the same Python interpreter is used for installation and execution.

### Streamlit command is blocked or not found on Windows

Use the module command instead of the executable:

```powershell
python -m streamlit run home.py
```

### `.streamlit/secrets.toml` is missing

Copy `.streamlit/secrets.toml.example`, rename the copy to `secrets.toml`, then
replace the placeholders with local keys. Do not edit the example with real
secrets.

### SmartBoyAI reports a missing Groq key

Add a valid `GROQ_API_KEY` to `.streamlit/secrets.toml` and restart Streamlit.
Without internet or Groq API access, SmartBoyAI cannot generate a response.

### SendGrid does not send a recovery email

Check `SENDGRID_API_KEY`, verify `SENDGRID_FROM_EMAIL` in SendGrid, confirm the
account has a recovery email, and check internet access. Request a new code if
the previous code has expired.

### Database or table is missing

Run `python main.py`, log in as an administrator, and select menu option 6.
Confirm the three required CSV files exist inside `DATA/`.

### API or internet access is unavailable

The dashboard, profile, CLI, and local database remain usable. Groq responses
and SendGrid email delivery require working internet access and valid keys.

## Fresh Clone Setup Checklist

1. Clone or extract the project.
2. Open a terminal in the project directory.
3. Create and activate a virtual environment.
4. Run `python -m pip install -r requirements.txt`.
5. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`.
6. Add local API keys without committing the real secrets file.
7. Run `python main.py`; use option 10 to create the first administrator if needed.
8. Use CLI option 6 to migrate the required CSV files.
9. Run `python -m streamlit run home.py`.
10. Register or log in and test Dashboard, SmartBoyAI, Profile, and Recovery.

## Technical References

- Streamlit documentation for multipage apps, session state, secrets, and chat.
- Groq documentation for chat-completion requests.
- SendGrid documentation for verified senders and email delivery.
- SQLite documentation for parameterised queries and table creation.
- Rich documentation for console panels, rules, and tables.
- [Streamlit issue #4553: rerun on each new keystroke](https://github.com/streamlit/streamlit/issues/4553)
- [Streamlit forum: forcing `st.text_input` to rerun for every letter](https://discuss.streamlit.io/t/modify-st-text-input/29823)
- [`streamlit-keyup`: component-based keyup input](https://github.com/blackary/streamlit-keyup)
