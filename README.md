# FITPRO Phase 1 — Authentication & Database

Dark black + red Streamlit foundation for a single trainer / single gym.

## Phase 1 features
- Turso Cloud SQLite database initialization
- First trainer account bootstrapped from Streamlit secrets
- Client registration request with trainer approval/rejection
- bcrypt password hashing
- Role/status checks at login and dashboard entry
- Basic database-backed failed-login lockout
- Idle timeout in the Streamlit session
- Authentication audit events
- Local SQLite mode for development and tests

## 1. Create a Python environment (Windows PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Create Turso database

Follow Turso's current official CLI installation guide, then:

```bash
turso auth login
turso db create fitpro-gym
turso db show fitpro-gym --url
turso db tokens create fitpro-gym
```

Copy the URL and token. Do not paste them into source code or GitHub.

## 3. Configure Streamlit secrets

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`.
Replace the Turso URL/token and choose a strong trainer username/password.
The trainer password must be at least 14 characters. Use a unique password.

## 4. Run

```bash
streamlit run app.py
```

Tables are created automatically. The configured trainer account is inserted only if that username does not already exist.

## 5. Client onboarding

1. Client submits the registration form.
2. Account is created with `pending` status.
3. Trainer signs in and reviews the request.
4. Trainer approves or rejects it.
5. Only approved accounts can log in.

## 6. Run tests

```bash
python -m unittest discover -s tests -v
```

The tests use a temporary local SQLite database and do not require Turso credentials.

## 7. Local development without Turso (optional)

PowerShell:

```powershell
$env:FITPRO_LOCAL_DB_PATH = ".\fitpro-local.db"
streamlit run app.py
```

Remove the variable to return to Turso mode. Never use the local development database for a deployed production application.

## 8. Deploy to Streamlit Community Cloud

1. Push source files to a private or public GitHub repository.
2. Do not commit `.streamlit/secrets.toml`.
3. Create the app at https://share.streamlit.io.
4. Select `app.py` as the main file.
5. Paste the contents of your secrets file into the app's Secrets settings.
6. Deploy and test trainer and client logins.

## Security notes — read before real client data

This is a Phase 1 starter, not a production security certification.

- bcrypt hashes passwords; plaintext passwords are never stored.
- Client registration is pending until trainer approval.
- SQL parameters are bound rather than interpolated.
- Client accounts cannot choose their own role.
- The login lockout is a basic app-level control. Production needs edge-level rate limiting, monitoring and alerting.
- Streamlit session state is not a substitute for a dedicated hardened session/authentication service. The idle timeout is best-effort.
- The current phase does not yet implement client fitness records, password reset, MFA, verified email, account recovery, export/deletion workflows or comprehensive audit-log review.
- Before storing sensitive health/fitness data, add MFA, HTTPS, backups, retention/deletion policies, privacy notices/consent, least-privilege database access, and an independent security review.
- Keep Turso tokens and Streamlit secrets private. Rotate exposed credentials immediately.
