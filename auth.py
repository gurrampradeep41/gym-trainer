import time
import streamlit as st
from config import get_int_setting, get_setting
from db import fetch_one, execute
from security import hash_password, verify_password, validate_password, validate_username


def clear_auth_session():
    keys_to_clear = [
        "authenticated",
        "user",
        "user_id",
        "role",
        "last_activity",
        "login_time",
    ]
    for key in keys_to_clear:
        st.session_state.pop(key, None)


def bootstrap_trainer():
    """Create the initial trainer only if the configured username does not exist."""
    username = str(get_setting("TRAINER_USERNAME", "")).strip()
    password = str(get_setting("TRAINER_PASSWORD", ""))
    if not username or not password:
        raise RuntimeError(
            "Configure TRAINER_USERNAME and TRAINER_PASSWORD in Streamlit secrets."
        )

    ok, message = validate_username(username)
    if not ok:
        raise RuntimeError(f"Invalid TRAINER_USERNAME: {message}")

    ok, message = validate_password(password)
    if not ok:
        raise RuntimeError(f"Invalid TRAINER_PASSWORD: {message}")

    existing = fetch_one(
        "SELECT id FROM users WHERE LOWER(username)=LOWER(?)",
        (username,)
    )
    if existing:
        return False

    execute(
        """INSERT INTO users(username, password_hash, role, status)
           VALUES(?, ?, 'trainer', 'active')""",
        (username, hash_password(password))
    )
    execute(
        """INSERT INTO audit_logs(actor_user_id, event_type, target_username, details)
           VALUES(NULL, 'trainer_bootstrapped', ?, 'Initial trainer account created')""",
        (username,)
    )
    return True


def _lock_state(username: str):
    row = fetch_one(
        "SELECT failed_attempts, locked_until FROM login_attempts WHERE LOWER(username)=LOWER(?)",
        (username,)
    )
    if not row:
        return 0, 0
    return int(row[0]), int(row[1])


def _record_failure(username: str):
    normalized = username.lower()
    max_failures = get_int_setting("LOGIN_MAX_FAILURES", 5)
    lock_seconds = get_int_setting("LOGIN_LOCK_MINUTES", 15) * 60
    failures, locked_until = _lock_state(normalized)
    failures += 1
    if failures >= max_failures:
        locked_until = int(time.time()) + lock_seconds
        failures = 0

    execute(
        """INSERT INTO login_attempts(username, failed_attempts, locked_until, last_attempt_at)
           VALUES(?, ?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(username) DO UPDATE SET
             failed_attempts=excluded.failed_attempts,
             locked_until=excluded.locked_until,
             last_attempt_at=CURRENT_TIMESTAMP""",
        (normalized, failures, locked_until)
    )


def _clear_failures(username: str):
    execute(
        "DELETE FROM login_attempts WHERE LOWER(username)=LOWER(?)",
        (username,)
    )


def authenticate(username: str, password: str):
    username = (username or "").strip()
    if not username or not password:
        return None, "Enter both username and password."

    _, locked_until = _lock_state(username)
    now = int(time.time())
    if locked_until > now:
        minutes = max(1, (locked_until - now + 59) // 60)
        return None, f"Account temporarily locked. Try again in about {minutes} minute(s)."

    user = fetch_one(
        """SELECT id, username, password_hash, role, status
           FROM users WHERE LOWER(username)=LOWER(?)""",
        (username,)
    )

    # Do not reveal whether a username exists or whether it is pending.
    if not user or not verify_password(password, user[2]):
        _record_failure(username)
        return None, "Invalid username or password."

    if user[4] != "active":
        return None, "This account is not active. Contact the trainer."

    _clear_failures(username)
    execute(
        """INSERT INTO audit_logs(actor_user_id, event_type, target_username, details)
           VALUES(?, ?, ?, 'Successful login')""",
        (user[0], "login_success", user[1])
    )
    return {
        "id": int(user[0]),
        "username": user[1],
        "role": user[3],
        "login_at": now,
        "last_activity": now
    }, None


def logout_current_user():
    user = st.session_state.get("user")
    if user:
        try:
            execute(
                """INSERT INTO audit_logs(actor_user_id, event_type, target_username, details)
                   VALUES(?, ?, ?, 'User logged out')""",
                (user["id"], "logout", user["username"])
            )
        except Exception:
            pass
    clear_auth_session()
    st.rerun()


def enforce_session_timeout():
    user = st.session_state.get("user")
    if not user:
        return False

    timeout = get_int_setting("SESSION_IDLE_MINUTES", 60) * 60
    now = int(time.time())
    if now - int(user.get("last_activity", now)) > timeout:
        clear_auth_session()
        st.warning("Your session expired due to inactivity. Please log in again.")
        st.rerun()
        return False

    user["last_activity"] = now
    return True


def require_role(allowed_roles):
    """UI guard. Every sensitive database operation must also check ownership/role."""
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    user = st.session_state.get("user")
    if not user or user.get("role") not in allowed_roles:
        st.error("You are not authorized to view this page.")
        st.stop()
    return user