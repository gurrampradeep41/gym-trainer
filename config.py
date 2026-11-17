import os
import streamlit as st


def get_secret(name, default=None):
    """
    Read a secret from Streamlit secrets first,
    then fall back to environment variables.
    """
    value = None
    try:
        value = st.secrets.get(name, None)
    except Exception:
        value = None

    if value is None or (isinstance(value, str) and not value.strip()):
        value = os.getenv(name, None)

    if value is None or (isinstance(value, str) and not value.strip()):
        return default

    return value


def get_setting(name, default=None):
    """
    Alias for get_secret used across FITPRO modules and tests.
    """
    return get_secret(name, default=default)


def get_int_setting(name, default=0):
    """
    Read an integer setting from secrets or environment variables.
    """
    value = get_setting(name, default=default)
    if value is None:
        return int(default)
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def validate_required_secrets():
    required = [
        "TURSO_DATABASE_URL",
        "TURSO_AUTH_TOKEN",
        "TRAINER_USERNAME",
        "TRAINER_PASSWORD",
    ]

    missing = [
        key for key in required
        if not get_setting(key)
    ]

    if missing:
        raise RuntimeError(
            "Missing required application configuration: "
            + ", ".join(missing)
        )