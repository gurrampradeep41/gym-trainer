import re
import bcrypt

MIN_PASSWORD_LENGTH = 14
MAX_PASSWORD_BYTES = 72
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")


def validate_username(username: str):
    username = (username or "").strip()
    if not USERNAME_PATTERN.fullmatch(username):
        return (
            False,
            "Username must be 3–32 characters and use letters, numbers, dot, dash or underscore.",
        )
    return True, ""


def validate_password(password: str):
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must contain at least {MIN_PASSWORD_LENGTH} characters."
    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        return False, f"Password must be {MAX_PASSWORD_BYTES} bytes or fewer."
    return True, ""


def hash_password(password: str) -> str:
    """bcrypt password hash. Never store or log plaintext passwords."""
    if not isinstance(password, str) or len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValueError(f"Password must be text of at most {MAX_PASSWORD_BYTES} UTF-8 bytes.")
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    if not password or not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def validate_new_password(password):
    if not isinstance(password, str):
        raise ValueError("Password must be text.")

    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Password must contain at least {MIN_PASSWORD_LENGTH} characters."
        )

    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValueError(
            "Password is too long for bcrypt. "
            f"Use a password of at most {MAX_PASSWORD_BYTES} UTF-8 bytes."
        )

    if not any(char.isupper() for char in password):
        raise ValueError("Add at least one uppercase letter.")

    if not any(char.islower() for char in password):
        raise ValueError("Add at least one lowercase letter.")

    if not any(char.isdigit() for char in password):
        raise ValueError("Add at least one number.")

    if not any(not char.isalnum() for char in password):
        raise ValueError("Add at least one special character.")

    return True


def validate_text(value, field_name="Value", max_length=500):
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be text.")

    value = value.strip()

    if not value:
        raise ValueError(f"{field_name} cannot be empty.")

    if len(value) > max_length:
        raise ValueError(
            f"{field_name} cannot exceed {max_length} characters."
        )

    return value


def validate_email(email):
    email = validate_text(email, "Email", 254)

    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    if not re.fullmatch(pattern, email):
        raise ValueError("Enter a valid email address.")

    return email.lower()


def validate_phone(phone):
    phone = validate_text(phone, "Phone", 20)

    if not re.fullmatch(r"[0-9+\-\s()]{7,20}", phone):
        raise ValueError("Enter a valid phone number.")

    return phone


def validate_age(age):
    if isinstance(age, bool):
        raise ValueError("Age must be a valid number.")

    try:
        age = int(age)
    except (TypeError, ValueError):
        raise ValueError("Age must be a valid integer.")

    if age < 16 or age > 100:
        raise ValueError("Age must be between 16 and 100.")

    return age


def validate_weight(weight):
    if isinstance(weight, bool):
        raise ValueError("Weight must be a valid number.")

    try:
        weight = float(weight)
    except (TypeError, ValueError):
        raise ValueError("Weight must be a valid number.")

    if not 20 <= weight <= 350:
        raise ValueError("Weight must be between 20 and 350 kg.")

    return weight