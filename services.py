import uuid
from datetime import date, timedelta

from config import get_setting
from db import execute, fetch_all, fetch_one, set_client_status


# --------------------------------------------------
# ROLE VALIDATION
# --------------------------------------------------

def verify_trainer(actor_user_id):
    user = fetch_one(
        """
        SELECT id, role, status
        FROM users
        WHERE id=?
        """,
        (actor_user_id,)
    )

    if not user:
        raise PermissionError("Trainer account not found.")

    if user[1] != "trainer" or user[2] != "active":
        raise PermissionError("Trainer permission required.")

    return user


def get_active_trainer_user_id():
    trainer = fetch_one(
        """
        SELECT id
        FROM users
        WHERE role = 'trainer'
          AND status = 'active'
        ORDER BY id ASC
        LIMIT 1
        """
    )
    return int(trainer[0]) if trainer else None


# --------------------------------------------------
# TRAINER PROFILE
# --------------------------------------------------

def initialize_trainer_profile(trainer_user_id):
    verify_trainer(trainer_user_id)

    existing = fetch_one(
        """
        SELECT id
        FROM trainer_profiles
        WHERE trainer_user_id=?
        """,
        (trainer_user_id,)
    )

    if existing:
        return

    name = get_setting("TRAINER_NAME", "FITPRO Trainer")
    title = get_setting("TRAINER_TITLE", "Certified Personal Trainer")
    experience = get_setting("TRAINER_EXPERIENCE", "Fitness Professional")
    achievements = get_setting("TRAINER_ACHIEVEMENTS", "")

    execute(
        """
        INSERT INTO trainer_profiles(
            trainer_user_id,
            display_name,
            professional_title,
            experience,
            achievements
        )
        VALUES(?, ?, ?, ?, ?)
        """,
        (
            trainer_user_id,
            name,
            title,
            experience,
            achievements
        )
    )


def get_trainer_profile(trainer_user_id):
    verify_trainer(trainer_user_id)

    return fetch_one(
        """
        SELECT
            id,
            display_name,
            professional_title,
            experience,
            photo_url,
            achievements,
            bio,
            updated_at
        FROM trainer_profiles
        WHERE trainer_user_id=?
        """,
        (trainer_user_id,)
    )


def update_trainer_profile(
    trainer_user_id,
    name,
    title,
    experience,
    photo_url,
    achievements,
    bio
):
    verify_trainer(trainer_user_id)

    clean_name = (name or "").strip()
    if not clean_name:
        raise ValueError("Trainer name is required.")

    execute(
        """
        UPDATE trainer_profiles
        SET
            display_name=?,
            professional_title=?,
            experience=?,
            photo_url=?,
            achievements=?,
            bio=?,
            updated_at=CURRENT_TIMESTAMP
        WHERE trainer_user_id=?
        """,
        (
            clean_name,
            (title or "").strip(),
            (experience or "").strip(),
            (photo_url or "").strip(),
            (achievements or "").strip(),
            (bio or "").strip(),
            trainer_user_id
        )
    )

    execute(
        """
        INSERT INTO audit_logs(
            actor_user_id,
            event_type,
            details
        )
        VALUES(?, ?, ?)
        """,
        (
            trainer_user_id,
            "trainer_profile_updated",
            "Trainer profile updated."
        )
    )


# --------------------------------------------------
# DASHBOARD STATISTICS
# --------------------------------------------------

def dashboard_statistics(trainer_user_id):
    verify_trainer(trainer_user_id)

    total = fetch_one(
        "SELECT COUNT(*) FROM users WHERE role='client'"
    )[0]

    active = fetch_one(
        "SELECT COUNT(*) FROM users WHERE role='client' AND status='active'"
    )[0]

    pending = fetch_one(
        "SELECT COUNT(*) FROM users WHERE role='client' AND status='pending'"
    )[0]

    rejected = fetch_one(
        "SELECT COUNT(*) FROM users WHERE role='client' AND status='rejected'"
    )[0]

    disabled = fetch_one(
        "SELECT COUNT(*) FROM users WHERE role='client' AND status='disabled'"
    )[0]

    return {
        "total": total,
        "active": active,
        "pending": pending,
        "rejected": rejected,
        "disabled": disabled
    }


# --------------------------------------------------
# CLIENT REGISTRATION REQUESTS
# --------------------------------------------------

def get_pending_requests(trainer_user_id):
    verify_trainer(trainer_user_id)

    return fetch_all(
        """
        SELECT
            u.id,
            u.username,
            c.full_name,
            c.email,
            c.phone,
            c.age,
            c.height_cm,
            c.fitness_goal,
            u.created_at
        FROM users u
        JOIN clients c
        ON c.user_id=u.id
        WHERE u.role='client'
          AND u.status='pending'
        ORDER BY u.created_at DESC
        """
    )


def approve_client(trainer_user_id, client_user_id):
    verify_trainer(trainer_user_id)

    set_client_status(
        client_user_id,
        "active",
        trainer_user_id
    )


def reject_client(trainer_user_id, client_user_id):
    verify_trainer(trainer_user_id)

    set_client_status(
        client_user_id,
        "rejected",
        trainer_user_id
    )


# --------------------------------------------------
# CLIENT MANAGEMENT
# --------------------------------------------------

def get_all_clients(trainer_user_id):
    verify_trainer(trainer_user_id)

    return fetch_all(
        """
        SELECT
            c.id,
            c.user_id,
            c.full_name,
            u.username,
            c.email,
            c.phone,
            c.age,
            c.height_cm,
            c.fitness_goal,
            u.status,
            c.created_at
        FROM clients c
        JOIN users u
        ON c.user_id=u.id
        WHERE u.role='client'
        ORDER BY c.created_at DESC
        """
    )


def get_client_details(trainer_user_id, client_id):
    verify_trainer(trainer_user_id)

    return fetch_one(
        """
        SELECT
            c.id,
            c.user_id,
            c.full_name,
            u.username,
            c.email,
            c.phone,
            c.age,
            c.height_cm,
            c.fitness_goal,
            u.status,
            c.created_at
        FROM clients c
        JOIN users u
        ON c.user_id=u.id
        WHERE c.id=?
          AND u.role='client'
        """,
        (client_id,)
    )


def update_client_details(
    trainer_user_id,
    client_id,
    full_name,
    email,
    phone,
    age,
    height,
    goal
):
    verify_trainer(trainer_user_id)

    clean_full_name = (full_name or "").strip()
    if not clean_full_name:
        raise ValueError("Client name is required.")

    client = get_client_details(trainer_user_id, client_id)
    if not client:
        raise ValueError("Client does not exist.")

    execute(
        """
        UPDATE clients
        SET
            full_name=?,
            email=?,
            phone=?,
            age=?,
            height_cm=?,
            fitness_goal=?
        WHERE id=?
        """,
        (
            clean_full_name,
            (email or "").strip() or None,
            (phone or "").strip() or None,
            age,
            height,
            goal,
            client_id
        )
    )

    execute(
        """
        INSERT INTO audit_logs(
            actor_user_id,
            event_type,
            target_username,
            details
        )
        VALUES(?, ?, ?, ?)
        """,
        (
            trainer_user_id,
            "client_profile_updated",
            client[3],
            f"Client ID {client_id} profile updated."
        )
    )


def activate_client(trainer_user_id, client_user_id):
    verify_trainer(trainer_user_id)

    set_client_status(
        client_user_id,
        "active",
        trainer_user_id
    )


def deactivate_client(trainer_user_id, client_user_id):
    verify_trainer(trainer_user_id)

    set_client_status(
        client_user_id,
        "disabled",
        trainer_user_id
    )


# --------------------------------------------------
# RECENT ACTIVITY
# --------------------------------------------------

def get_recent_clients(trainer_user_id, limit=10):
    verify_trainer(trainer_user_id)

    safe_limit = max(1, min(int(limit), 50))

    return fetch_all(
        """
        SELECT
            c.full_name,
            u.username,
            u.status,
            c.created_at
        FROM clients c
        JOIN users u
        ON c.user_id=u.id
        WHERE u.role='client'
        ORDER BY c.created_at DESC
        LIMIT ?
        """,
        (safe_limit,)
    )


def get_audit_logs(trainer_user_id, limit=50):
    verify_trainer(trainer_user_id)

    safe_limit = max(1, min(int(limit), 200))

    return fetch_all(
        """
        SELECT
            event_type,
            target_username,
            details,
            created_at
        FROM audit_logs
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (safe_limit,)
    )


# ==================================================
# PHASE 3 — SECURE CLIENT DASHBOARD SERVICES
# ==================================================

def verify_client(client_user_id):
    user = fetch_one(
        """
        SELECT id, role, status
        FROM users
        WHERE id=?
        """,
        (client_user_id,)
    )

    if not user:
        raise PermissionError("Account not found.")

    if user[1] != "client":
        raise PermissionError("Client access required.")

    if user[2] != "active":
        raise PermissionError("Your account is not active.")

    return user


def get_my_client_profile(client_user_id):
    verify_client(client_user_id)

    profile = fetch_one(
        """
        SELECT
            c.id,
            c.user_id,
            c.full_name,
            u.username,
            c.email,
            c.phone,
            c.age,
            c.height_cm,
            c.fitness_goal,
            u.status,
            c.created_at
        FROM clients c
        INNER JOIN users u
        ON c.user_id = u.id
        WHERE c.user_id = ?
          AND u.role = 'client'
          AND u.status = 'active'
        LIMIT 1
        """,
        (client_user_id,)
    )

    if not profile:
        raise PermissionError("Your personal profile is unavailable.")

    return profile


def get_my_trainer_information(client_user_id):
    verify_client(client_user_id)

    return fetch_one(
        """
        SELECT
            tp.display_name,
            tp.professional_title,
            tp.experience,
            tp.photo_url,
            tp.achievements,
            tp.bio
        FROM trainer_profiles tp
        INNER JOIN users u
        ON tp.trainer_user_id = u.id
        WHERE u.role = 'trainer'
          AND u.status = 'active'
        ORDER BY tp.id ASC
        LIMIT 1
        """
    )


def get_my_dashboard(client_user_id):
    profile = get_my_client_profile(client_user_id)
    trainer = get_my_trainer_information(client_user_id)

    return {
        "profile": profile,
        "trainer": trainer
    }


def get_my_account_status(client_user_id):
    verify_client(client_user_id)

    account = fetch_one(
        """
        SELECT
            username,
            role,
            status,
            created_at
        FROM users
        WHERE id=?
          AND role='client'
        """,
        (client_user_id,)
    )

    if not account:
        raise PermissionError("Account not found.")

    return account


# ==========================================================
# PHASE 4 - FITNESS PROGRESS TRACKING
# ==========================================================

def _validate_positive_number(value, field_name):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a valid number.")

    if number <= 0:
        raise ValueError(f"{field_name} must be greater than zero.")

    if number > 500:
        raise ValueError(f"{field_name} is outside the allowed range.")

    return number


def _verify_trainer_client(trainer_user_id, client_user_id):
    verify_trainer(trainer_user_id)

    client = fetch_one(
        """
        SELECT id, role, status
        FROM users
        WHERE id = ? AND role = 'client'
        """,
        (client_user_id,)
    )

    if not client:
        raise PermissionError("Client account not found.")

    if client[2] != "active":
        raise PermissionError("Client account is not active.")

    return client


def _calculate_bmi(weight_kg, height_cm):
    if not height_cm:
        return None

    height_m = float(height_cm) / 100
    if height_m <= 0:
        return None

    return round(float(weight_kg) / (height_m ** 2), 2)


def add_weight_entry(
    trainer_user_id,
    client_user_id,
    weight_kg,
    recorded_on=None,
    notes=""
):
    _verify_trainer_client(trainer_user_id, client_user_id)

    weight = _validate_positive_number(weight_kg, "Weight")

    if recorded_on is None:
        recorded_on = date.today().isoformat()

    try:
        date.fromisoformat(str(recorded_on))
    except ValueError:
        raise ValueError("Invalid recording date.")

    profile = fetch_one(
        "SELECT height_cm FROM clients WHERE user_id = ?",
        (client_user_id,)
    )

    if not profile:
        raise ValueError("Client profile not found.")

    bmi = _calculate_bmi(weight, profile[0])
    log_id = str(uuid.uuid4())

    execute(
        """
        INSERT INTO weight_logs (
            id,
            client_user_id,
            trainer_user_id,
            weight_kg,
            bmi,
            notes,
            recorded_on
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            log_id,
            client_user_id,
            trainer_user_id,
            weight,
            bmi,
            str(notes or "").strip()[:1000],
            str(recorded_on)
        )
    )

    return log_id


def get_client_weight_history(trainer_user_id, client_user_id):
    _verify_trainer_client(trainer_user_id, client_user_id)

    return fetch_all(
        """
        SELECT id, weight_kg, bmi, notes, recorded_on
        FROM weight_logs
        WHERE client_user_id = ?
          AND trainer_user_id = ?
        ORDER BY recorded_on DESC, created_at DESC
        """,
        (client_user_id, trainer_user_id)
    )


def update_weight_entry(
    trainer_user_id,
    client_user_id,
    log_id,
    weight_kg,
    recorded_on,
    notes=""
):
    _verify_trainer_client(trainer_user_id, client_user_id)

    weight = _validate_positive_number(weight_kg, "Weight")

    try:
        date.fromisoformat(str(recorded_on))
    except ValueError:
        raise ValueError("Invalid recording date.")

    profile = fetch_one(
        "SELECT height_cm FROM clients WHERE user_id = ?",
        (client_user_id,)
    )

    if not profile:
        raise ValueError("Client profile not found.")

    bmi = _calculate_bmi(weight, profile[0])

    execute(
        """
        UPDATE weight_logs
        SET weight_kg = ?,
            bmi = ?,
            recorded_on = ?,
            notes = ?
        WHERE id = ?
          AND client_user_id = ?
          AND trainer_user_id = ?
        """,
        (
            weight,
            bmi,
            str(recorded_on),
            str(notes or "").strip()[:1000],
            log_id,
            client_user_id,
            trainer_user_id
        )
    )


def delete_weight_entry(trainer_user_id, client_user_id, log_id):
    _verify_trainer_client(trainer_user_id, client_user_id)

    execute(
        """
        DELETE FROM weight_logs
        WHERE id = ?
          AND client_user_id = ?
          AND trainer_user_id = ?
        """,
        (log_id, client_user_id, trainer_user_id)
    )


def add_body_measurement(
    trainer_user_id,
    client_user_id,
    waist_cm=None,
    chest_cm=None,
    hips_cm=None,
    left_arm_cm=None,
    right_arm_cm=None,
    left_thigh_cm=None,
    right_thigh_cm=None,
    recorded_on=None,
    notes=""
):
    _verify_trainer_client(trainer_user_id, client_user_id)

    if recorded_on is None:
        recorded_on = date.today().isoformat()

    try:
        date.fromisoformat(str(recorded_on))
    except ValueError:
        raise ValueError("Invalid recording date.")

    fields = {
        "waist": waist_cm,
        "chest": chest_cm,
        "hips": hips_cm,
        "left arm": left_arm_cm,
        "right arm": right_arm_cm,
        "left thigh": left_thigh_cm,
        "right thigh": right_thigh_cm
    }

    validated = {}
    for field, value in fields.items():
        if value is None:
            validated[field] = None
        else:
            validated[field] = _validate_positive_number(
                value, f"{field.title()} measurement"
            )

    measurement_id = str(uuid.uuid4())

    execute(
        """
        INSERT INTO body_measurements (
            id,
            client_user_id,
            trainer_user_id,
            waist_cm,
            chest_cm,
            hips_cm,
            left_arm_cm,
            right_arm_cm,
            left_thigh_cm,
            right_thigh_cm,
            notes,
            recorded_on
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            measurement_id,
            client_user_id,
            trainer_user_id,
            validated["waist"],
            validated["chest"],
            validated["hips"],
            validated["left arm"],
            validated["right arm"],
            validated["left thigh"],
            validated["right thigh"],
            str(notes or "").strip()[:1000],
            str(recorded_on)
        )
    )

    return measurement_id


def get_client_measurement_history(trainer_user_id, client_user_id):
    _verify_trainer_client(trainer_user_id, client_user_id)

    return fetch_all(
        """
        SELECT
            id,
            waist_cm,
            chest_cm,
            hips_cm,
            left_arm_cm,
            right_arm_cm,
            left_thigh_cm,
            right_thigh_cm,
            notes,
            recorded_on
        FROM body_measurements
        WHERE client_user_id = ?
          AND trainer_user_id = ?
        ORDER BY recorded_on DESC, created_at DESC
        """,
        (client_user_id, trainer_user_id)
    )


def get_my_weight_history(client_user_id):
    verify_client(client_user_id)

    return fetch_all(
        """
        SELECT weight_kg, bmi, notes, recorded_on
        FROM weight_logs
        WHERE client_user_id = ?
        ORDER BY recorded_on ASC, created_at ASC
        """,
        (client_user_id,)
    )


def get_my_measurement_history(client_user_id):
    verify_client(client_user_id)

    return fetch_all(
        """
        SELECT
            waist_cm,
            chest_cm,
            hips_cm,
            left_arm_cm,
            right_arm_cm,
            left_thigh_cm,
            right_thigh_cm,
            notes,
            recorded_on
        FROM body_measurements
        WHERE client_user_id = ?
        ORDER BY recorded_on DESC, created_at DESC
        """,
        (client_user_id,)
    )


def get_my_progress_summary(client_user_id):
    verify_client(client_user_id)

    history = get_my_weight_history(client_user_id)

    if not history:
        return {
            "starting_weight": None,
            "current_weight": None,
            "weight_change": None,
            "latest_bmi": None,
            "entries": 0
        }

    starting_weight = float(history[0][0])
    current_weight = float(history[-1][0])
    latest_bmi = history[-1][1]

    return {
        "starting_weight": starting_weight,
        "current_weight": current_weight,
        "weight_change": round(current_weight - starting_weight, 2),
        "latest_bmi": latest_bmi,
        "entries": len(history)
    }


# ==========================================================
# PHASE 5 - WORKOUT PLAN MANAGEMENT
# ==========================================================

def _verify_workout_client(trainer_user_id, client_user_id):
    _verify_trainer_client(trainer_user_id, client_user_id)


def _verify_plan_owner(trainer_user_id, plan_id):
    verify_trainer(trainer_user_id)

    plan = fetch_one(
        """
        SELECT id, client_user_id, status
        FROM workout_plans
        WHERE id = ? AND trainer_user_id = ?
        """,
        (plan_id, trainer_user_id)
    )

    if not plan:
        raise PermissionError("Workout plan not found.")

    return plan


def create_workout_plan(
    trainer_user_id,
    client_user_id,
    plan_name,
    description="",
    duration_weeks=4,
    start_date=None
):
    _verify_workout_client(trainer_user_id, client_user_id)

    plan_name = str(plan_name or "").strip()

    if not plan_name:
        raise ValueError("Workout plan name is required.")

    if len(plan_name) > 120:
        raise ValueError("Plan name must be 120 characters or fewer.")

    if not 1 <= int(duration_weeks) <= 52:
        raise ValueError("Duration must be between 1 and 52 weeks.")

    if start_date is None:
        start_date = date.today().isoformat()

    try:
        start = date.fromisoformat(str(start_date))
    except ValueError:
        raise ValueError("Invalid plan start date.")

    end = start + timedelta(weeks=int(duration_weeks))
    plan_id = str(uuid.uuid4())

    execute(
        """
        INSERT INTO workout_plans (
            id,
            trainer_user_id,
            client_user_id,
            plan_name,
            description,
            duration_weeks,
            start_date,
            end_date,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')
        """,
        (
            plan_id,
            trainer_user_id,
            client_user_id,
            plan_name,
            str(description or "").strip()[:2000],
            int(duration_weeks),
            start.isoformat(),
            end.isoformat()
        )
    )

    return plan_id


def add_workout_exercise(
    trainer_user_id,
    plan_id,
    workout_day,
    exercise_name,
    sets,
    reps,
    rest_seconds=60,
    instructions=""
):
    _verify_plan_owner(trainer_user_id, plan_id)

    exercise_name = str(exercise_name or "").strip()
    workout_day = str(workout_day or "").strip()
    reps = str(reps or "").strip()

    if not exercise_name:
        raise ValueError("Exercise name is required.")

    if not workout_day:
        raise ValueError("Workout day is required.")

    if len(exercise_name) > 120:
        raise ValueError("Exercise name is too long.")

    if len(workout_day) > 40:
        raise ValueError("Workout day is too long.")

    if not reps or len(reps) > 30:
        raise ValueError("Enter valid repetitions.")

    sets = int(sets)
    rest_seconds = int(rest_seconds)

    if not 1 <= sets <= 20:
        raise ValueError("Sets must be between 1 and 20.")

    if not 0 <= rest_seconds <= 1800:
        raise ValueError("Rest time must be between 0 and 1800 seconds.")

    exercise_id = str(uuid.uuid4())

    execute(
        """
        INSERT INTO workout_exercises (
            id,
            plan_id,
            trainer_user_id,
            workout_day,
            exercise_name,
            sets,
            reps,
            rest_seconds,
            instructions
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            exercise_id,
            plan_id,
            trainer_user_id,
            workout_day,
            exercise_name,
            sets,
            reps,
            rest_seconds,
            str(instructions or "").strip()[:1500]
        )
    )

    return exercise_id


def get_trainer_workout_plans(trainer_user_id):
    verify_trainer(trainer_user_id)

    return fetch_all(
        """
        SELECT
            wp.id,
            wp.client_user_id,
            c.full_name,
            wp.plan_name,
            wp.description,
            wp.duration_weeks,
            wp.start_date,
            wp.end_date,
            wp.status,
            wp.created_at
        FROM workout_plans wp
        INNER JOIN clients c ON c.user_id = wp.client_user_id
        WHERE wp.trainer_user_id = ?
        ORDER BY wp.created_at DESC
        """,
        (trainer_user_id,)
    )


def get_trainer_plan_exercises(trainer_user_id, plan_id):
    _verify_plan_owner(trainer_user_id, plan_id)

    return fetch_all(
        """
        SELECT
            id,
            workout_day,
            exercise_name,
            sets,
            reps,
            rest_seconds,
            instructions
        FROM workout_exercises
        WHERE plan_id = ? AND trainer_user_id = ?
        ORDER BY workout_day, created_at
        """,
        (plan_id, trainer_user_id)
    )


def delete_workout_exercise(trainer_user_id, plan_id, exercise_id):
    _verify_plan_owner(trainer_user_id, plan_id)

    execute(
        """
        DELETE FROM workout_completions
        WHERE plan_id = ? AND exercise_id = ?
        """,
        (plan_id, exercise_id)
    )

    execute(
        """
        DELETE FROM workout_exercises
        WHERE id = ?
          AND plan_id = ?
          AND trainer_user_id = ?
        """,
        (exercise_id, plan_id, trainer_user_id)
    )


def update_workout_plan_status(trainer_user_id, plan_id, status):
    _verify_plan_owner(trainer_user_id, plan_id)

    if status not in ("active", "completed", "paused"):
        raise ValueError("Invalid workout plan status.")

    execute(
        """
        UPDATE workout_plans
        SET status = ?
        WHERE id = ? AND trainer_user_id = ?
        """,
        (status, plan_id, trainer_user_id)
    )


def get_my_workout_plans(client_user_id):
    verify_client(client_user_id)

    return fetch_all(
        """
        SELECT
            id,
            plan_name,
            description,
            duration_weeks,
            start_date,
            end_date,
            status
        FROM workout_plans
        WHERE client_user_id = ?
          AND status = 'active'
        ORDER BY created_at DESC
        """,
        (client_user_id,)
    )


def get_my_workout_exercises(client_user_id, plan_id):
    verify_client(client_user_id)

    plan = fetch_one(
        """
        SELECT id
        FROM workout_plans
        WHERE id = ?
          AND client_user_id = ?
          AND status = 'active'
        """,
        (plan_id, client_user_id)
    )

    if not plan:
        raise PermissionError("This workout plan is not assigned to you.")

    return fetch_all(
        """
        SELECT
            id,
            workout_day,
            exercise_name,
            sets,
            reps,
            rest_seconds,
            instructions
        FROM workout_exercises
        WHERE plan_id = ?
        ORDER BY workout_day, created_at
        """,
        (plan_id,)
    )


def mark_exercise_complete(
    client_user_id,
    plan_id,
    exercise_id,
    completion_date=None,
    completed=True,
    notes=""
):
    verify_client(client_user_id)

    if completion_date is None:
        completion_date = date.today().isoformat()

    try:
        date.fromisoformat(str(completion_date))
    except ValueError:
        raise ValueError("Invalid completion date.")

    exercise = fetch_one(
        """
        SELECT we.id
        FROM workout_exercises we
        INNER JOIN workout_plans wp ON wp.id = we.plan_id
        WHERE we.id = ?
          AND wp.id = ?
          AND wp.client_user_id = ?
          AND wp.status = 'active'
        """,
        (exercise_id, plan_id, client_user_id)
    )

    if not exercise:
        raise PermissionError("Exercise does not belong to your workout plan.")

    existing = fetch_one(
        """
        SELECT id
        FROM workout_completions
        WHERE plan_id = ?
          AND exercise_id = ?
          AND client_user_id = ?
          AND completion_date = ?
        """,
        (plan_id, exercise_id, client_user_id, str(completion_date))
    )

    if existing:
        execute(
            """
            UPDATE workout_completions
            SET completed = ?, notes = ?
            WHERE id = ?
              AND client_user_id = ?
            """,
            (
                1 if completed else 0,
                str(notes or "").strip()[:1000],
                existing[0],
                client_user_id
            )
        )
    else:
        execute(
            """
            INSERT INTO workout_completions (
                id,
                plan_id,
                exercise_id,
                client_user_id,
                completion_date,
                completed,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                plan_id,
                exercise_id,
                client_user_id,
                str(completion_date),
                1 if completed else 0,
                str(notes or "").strip()[:1000]
            )
        )


def get_my_workout_completions(client_user_id, plan_id):
    verify_client(client_user_id)

    plan = fetch_one(
        """
        SELECT id
        FROM workout_plans
        WHERE id = ? AND client_user_id = ?
        """,
        (plan_id, client_user_id)
    )

    if not plan:
        raise PermissionError("Workout plan not found.")

    return fetch_all(
        """
        SELECT exercise_id, completion_date, completed, notes
        FROM workout_completions
        WHERE plan_id = ? AND client_user_id = ?
        ORDER BY completion_date DESC
        """,
        (plan_id, client_user_id)
    )


def get_workout_adherence(trainer_user_id, plan_id):
    _verify_plan_owner(trainer_user_id, plan_id)

    total_exercises = fetch_one(
        """
        SELECT COUNT(*)
        FROM workout_exercises
        WHERE plan_id = ?
          AND trainer_user_id = ?
        """,
        (plan_id, trainer_user_id)
    )

    completed_exercises = fetch_one(
        """
        SELECT COUNT(DISTINCT exercise_id)
        FROM workout_completions
        WHERE plan_id = ?
          AND completed = 1
        """,
        (plan_id,)
    )

    total = int(total_exercises[0] or 0)
    completed = int(completed_exercises[0] or 0)

    return {
        "total_exercises": total,
        "completed_entries": completed,
        "completion_percentage": (
            round(completed / total * 100, 2)
            if total else 0
        )
    }


def get_client_workout_activity(trainer_user_id, client_user_id):
    _verify_workout_client(trainer_user_id, client_user_id)

    return fetch_all(
        """
        SELECT
            wp.plan_name,
            we.workout_day,
            we.exercise_name,
            wc.completion_date,
            wc.completed,
            wc.notes
        FROM workout_completions wc
        INNER JOIN workout_plans wp ON wp.id = wc.plan_id
        INNER JOIN workout_exercises we ON we.id = wc.exercise_id
        WHERE wc.client_user_id = ?
          AND wp.trainer_user_id = ?
        ORDER BY wc.completion_date DESC
        """,
        (client_user_id, trainer_user_id)
    )


# ==========================================================
# PHASE 6 - DIET & NUTRITION MANAGEMENT
# ==========================================================

def _validate_nutrition_value(value, field_name, allow_zero=True):
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a valid number.")

    if number < 0 or (not allow_zero and number == 0):
        raise ValueError(f"{field_name} cannot be negative or zero.")

    if number > 10000:
        raise ValueError(f"{field_name} is outside the allowed range.")

    return round(number, 2)


def _verify_diet_plan_owner(trainer_user_id, plan_id):
    verify_trainer(trainer_user_id)

    plan = fetch_one(
        """
        SELECT id, client_user_id, status
        FROM diet_plans
        WHERE id = ? AND trainer_user_id = ?
        """,
        (plan_id, trainer_user_id)
    )

    if not plan:
        raise PermissionError("Diet plan not found.")

    return plan


def _verify_diet_client_plan(client_user_id, plan_id):
    verify_client(client_user_id)

    plan = fetch_one(
        """
        SELECT id, status
        FROM diet_plans
        WHERE id = ?
          AND client_user_id = ?
          AND status = 'active'
        """,
        (plan_id, client_user_id)
    )

    if not plan:
        raise PermissionError("This diet plan is not assigned to you.")

    return plan


def create_diet_plan(
    trainer_user_id,
    client_user_id,
    plan_name,
    description="",
    daily_calories=2000,
    protein_target=100,
    carbs_target=200,
    fat_target=60,
    start_date=None,
    duration_weeks=4
):
    _verify_trainer_client(trainer_user_id, client_user_id)

    plan_name = str(plan_name or "").strip()

    if not plan_name:
        raise ValueError("Diet plan name is required.")

    if len(plan_name) > 120:
        raise ValueError("Diet plan name must be 120 characters or fewer.")

    duration_weeks = int(duration_weeks)

    if not 1 <= duration_weeks <= 52:
        raise ValueError("Duration must be between 1 and 52 weeks.")

    calories = _validate_nutrition_value(
        daily_calories, "Daily calories", allow_zero=False
    )
    protein = _validate_nutrition_value(protein_target, "Protein target")
    carbs = _validate_nutrition_value(carbs_target, "Carbohydrate target")
    fat = _validate_nutrition_value(fat_target, "Fat target")

    if start_date is None:
        start_date = date.today().isoformat()

    try:
        start = date.fromisoformat(str(start_date))
    except ValueError:
        raise ValueError("Invalid diet plan start date.")

    end = start + timedelta(weeks=duration_weeks)
    plan_id = str(uuid.uuid4())

    execute(
        """
        INSERT INTO diet_plans (
            id,
            trainer_user_id,
            client_user_id,
            plan_name,
            description,
            daily_calories,
            protein_target,
            carbs_target,
            fat_target,
            start_date,
            end_date,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active')
        """,
        (
            plan_id,
            trainer_user_id,
            client_user_id,
            plan_name,
            str(description or "").strip()[:2000],
            calories,
            protein,
            carbs,
            fat,
            start.isoformat(),
            end.isoformat()
        )
    )

    return plan_id


def add_diet_meal(
    trainer_user_id,
    plan_id,
    meal_type,
    meal_name,
    food_items,
    quantity="",
    calories=0,
    protein=0,
    carbs=0,
    fat=0,
    instructions=""
):
    plan = _verify_diet_plan_owner(trainer_user_id, plan_id)

    if plan[2] != "active":
        raise ValueError("You can only add meals to an active plan.")

    allowed_meal_types = [
        "Breakfast",
        "Mid-Morning Snack",
        "Lunch",
        "Evening Snack",
        "Dinner",
        "Other"
    ]

    if meal_type not in allowed_meal_types:
        raise ValueError("Invalid meal type.")

    meal_name = str(meal_name or "").strip()
    food_items = str(food_items or "").strip()

    if not meal_name:
        raise ValueError("Meal name is required.")

    if not food_items:
        raise ValueError("Food items are required.")

    if len(meal_name) > 120:
        raise ValueError("Meal name is too long.")

    meal_id = str(uuid.uuid4())

    calories = _validate_nutrition_value(calories, "Calories")
    protein = _validate_nutrition_value(protein, "Protein")
    carbs = _validate_nutrition_value(carbs, "Carbohydrates")
    fat = _validate_nutrition_value(fat, "Fat")

    execute(
        """
        INSERT INTO diet_meals (
            id,
            plan_id,
            trainer_user_id,
            meal_type,
            meal_name,
            food_items,
            quantity,
            calories,
            protein,
            carbs,
            fat,
            instructions
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            meal_id,
            plan_id,
            trainer_user_id,
            meal_type,
            meal_name,
            food_items[:2000],
            str(quantity or "").strip()[:500],
            calories,
            protein,
            carbs,
            fat,
            str(instructions or "").strip()[:1500]
        )
    )

    return meal_id


def get_trainer_diet_plans(trainer_user_id):
    verify_trainer(trainer_user_id)

    return fetch_all(
        """
        SELECT
            dp.id,
            dp.client_user_id,
            c.full_name,
            dp.plan_name,
            dp.description,
            dp.daily_calories,
            dp.protein_target,
            dp.carbs_target,
            dp.fat_target,
            dp.start_date,
            dp.end_date,
            dp.status,
            dp.created_at
        FROM diet_plans dp
        INNER JOIN clients c ON c.user_id = dp.client_user_id
        WHERE dp.trainer_user_id = ?
        ORDER BY dp.created_at DESC
        """,
        (trainer_user_id,)
    )


def get_trainer_diet_meals(trainer_user_id, plan_id):
    _verify_diet_plan_owner(trainer_user_id, plan_id)

    return fetch_all(
        """
        SELECT
            id,
            meal_type,
            meal_name,
            food_items,
            quantity,
            calories,
            protein,
            carbs,
            fat,
            instructions
        FROM diet_meals
        WHERE plan_id = ?
          AND trainer_user_id = ?
        ORDER BY
            CASE meal_type
                WHEN 'Breakfast' THEN 1
                WHEN 'Mid-Morning Snack' THEN 2
                WHEN 'Lunch' THEN 3
                WHEN 'Evening Snack' THEN 4
                WHEN 'Dinner' THEN 5
                ELSE 6
            END,
            created_at
        """,
        (plan_id, trainer_user_id)
    )


def delete_diet_meal(trainer_user_id, plan_id, meal_id):
    _verify_diet_plan_owner(trainer_user_id, plan_id)

    execute(
        """
        DELETE FROM meal_logs
        WHERE plan_id = ? AND meal_id = ?
        """,
        (plan_id, meal_id)
    )

    execute(
        """
        DELETE FROM diet_meals
        WHERE id = ?
          AND plan_id = ?
          AND trainer_user_id = ?
        """,
        (meal_id, plan_id, trainer_user_id)
    )


def update_diet_plan_status(trainer_user_id, plan_id, status):
    _verify_diet_plan_owner(trainer_user_id, plan_id)

    if status not in ("active", "paused", "completed"):
        raise ValueError("Invalid diet plan status.")

    execute(
        """
        UPDATE diet_plans
        SET status = ?
        WHERE id = ? AND trainer_user_id = ?
        """,
        (status, plan_id, trainer_user_id)
    )


def get_my_diet_plans(client_user_id):
    verify_client(client_user_id)

    return fetch_all(
        """
        SELECT
            id,
            plan_name,
            description,
            daily_calories,
            protein_target,
            carbs_target,
            fat_target,
            start_date,
            end_date,
            status
        FROM diet_plans
        WHERE client_user_id = ?
          AND status = 'active'
        ORDER BY created_at DESC
        """,
        (client_user_id,)
    )


def get_my_diet_meals(client_user_id, plan_id):
    _verify_diet_client_plan(client_user_id, plan_id)

    return fetch_all(
        """
        SELECT
            id,
            meal_type,
            meal_name,
            food_items,
            quantity,
            calories,
            protein,
            carbs,
            fat,
            instructions
        FROM diet_meals
        WHERE plan_id = ?
        ORDER BY
            CASE meal_type
                WHEN 'Breakfast' THEN 1
                WHEN 'Mid-Morning Snack' THEN 2
                WHEN 'Lunch' THEN 3
                WHEN 'Evening Snack' THEN 4
                WHEN 'Dinner' THEN 5
                ELSE 6
            END,
            created_at
        """,
        (plan_id,)
    )


def log_meal_consumption(
    client_user_id,
    plan_id,
    meal_id,
    consumed_date=None,
    consumed=True,
    actual_calories=None,
    actual_protein=None,
    actual_carbs=None,
    actual_fat=None,
    notes=""
):
    _verify_diet_client_plan(client_user_id, plan_id)

    if consumed_date is None:
        consumed_date = date.today().isoformat()

    try:
        date.fromisoformat(str(consumed_date))
    except ValueError:
        raise ValueError("Invalid meal recording date.")

    meal = fetch_one(
        """
        SELECT id
        FROM diet_meals
        WHERE id = ? AND plan_id = ?
        """,
        (meal_id, plan_id)
    )

    if not meal:
        raise PermissionError("This meal does not belong to your plan.")

    actual_values = []
    for value, field in [
        (actual_calories, "Actual calories"),
        (actual_protein, "Actual protein"),
        (actual_carbs, "Actual carbohydrates"),
        (actual_fat, "Actual fat")
    ]:
        if value is None:
            actual_values.append(None)
        else:
            actual_values.append(_validate_nutrition_value(value, field))

    existing = fetch_one(
        """
        SELECT id
        FROM meal_logs
        WHERE plan_id = ?
          AND meal_id = ?
          AND client_user_id = ?
          AND consumed_date = ?
        """,
        (plan_id, meal_id, client_user_id, str(consumed_date))
    )

    if existing:
        execute(
            """
            UPDATE meal_logs
            SET consumed = ?,
                actual_calories = ?,
                actual_protein = ?,
                actual_carbs = ?,
                actual_fat = ?,
                notes = ?
            WHERE id = ?
              AND client_user_id = ?
            """,
            (
                1 if consumed else 0,
                *actual_values,
                str(notes or "").strip()[:1000],
                existing[0],
                client_user_id
            )
        )
    else:
        execute(
            """
            INSERT INTO meal_logs (
                id,
                plan_id,
                meal_id,
                client_user_id,
                consumed_date,
                consumed,
                actual_calories,
                actual_protein,
                actual_carbs,
                actual_fat,
                notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                plan_id,
                meal_id,
                client_user_id,
                str(consumed_date),
                1 if consumed else 0,
                *actual_values,
                str(notes or "").strip()[:1000]
            )
        )


def get_my_meal_logs(client_user_id, plan_id, consumed_date=None):
    _verify_diet_client_plan(client_user_id, plan_id)

    if consumed_date is None:
        consumed_date = date.today().isoformat()

    return fetch_all(
        """
        SELECT
            meal_id,
            consumed,
            actual_calories,
            actual_protein,
            actual_carbs,
            actual_fat,
            notes
        FROM meal_logs
        WHERE plan_id = ?
          AND client_user_id = ?
          AND consumed_date = ?
        """,
        (plan_id, client_user_id, str(consumed_date))
    )


def get_my_nutrition_summary(client_user_id, plan_id, consumed_date=None):
    _verify_diet_client_plan(client_user_id, plan_id)

    if consumed_date is None:
        consumed_date = date.today().isoformat()

    meals = get_my_diet_meals(client_user_id, plan_id)
    logs = get_my_meal_logs(client_user_id, plan_id, consumed_date)

    log_map = {row[0]: row for row in logs}

    totals = {
        "calories": 0.0,
        "protein": 0.0,
        "carbs": 0.0,
        "fat": 0.0
    }

    consumed_count = 0

    for meal in meals:
        log = log_map.get(meal[0])

        if not log or log[1] != 1:
            continue

        consumed_count += 1

        totals["calories"] += (
            float(log[2]) if log[2] is not None else float(meal[5] or 0)
        )
        totals["protein"] += (
            float(log[3]) if log[3] is not None else float(meal[6] or 0)
        )
        totals["carbs"] += (
            float(log[4]) if log[4] is not None else float(meal[7] or 0)
        )
        totals["fat"] += (
            float(log[5]) if log[5] is not None else float(meal[8] or 0)
        )

    return {
        "consumed_meals": consumed_count,
        "total_meals": len(meals),
        "calories": round(totals["calories"], 2),
        "protein": round(totals["protein"], 2),
        "carbs": round(totals["carbs"], 2),
        "fat": round(totals["fat"], 2)
    }


def get_client_nutrition_activity(
    trainer_user_id,
    client_user_id,
    consumed_date=None
):
    _verify_trainer_client(trainer_user_id, client_user_id)

    if consumed_date is None:
        consumed_date = date.today().isoformat()

    return fetch_all(
        """
        SELECT
            dp.plan_name,
            dm.meal_type,
            dm.meal_name,
            ml.consumed_date,
            ml.consumed,
            ml.actual_calories,
            ml.actual_protein,
            ml.actual_carbs,
            ml.actual_fat,
            ml.notes
        FROM meal_logs ml
        INNER JOIN diet_plans dp ON dp.id = ml.plan_id
        INNER JOIN diet_meals dm ON dm.id = ml.meal_id
        WHERE ml.client_user_id = ?
          AND dp.trainer_user_id = ?
          AND ml.consumed_date = ?
        ORDER BY dm.created_at
        """,
        (client_user_id, trainer_user_id, str(consumed_date))
    )


def get_diet_plan_adherence(trainer_user_id, plan_id, consumed_date=None):
    plan = _verify_diet_plan_owner(trainer_user_id, plan_id)

    if consumed_date is None:
        consumed_date = date.today().isoformat()

    total = fetch_one(
        """
        SELECT COUNT(*)
        FROM diet_meals
        WHERE plan_id = ?
          AND trainer_user_id = ?
        """,
        (plan_id, trainer_user_id)
    )

    consumed = fetch_one(
        """
        SELECT COUNT(*)
        FROM meal_logs
        WHERE plan_id = ?
          AND client_user_id = ?
          AND consumed_date = ?
          AND consumed = 1
        """,
        (plan_id, plan[1], str(consumed_date))
    )

    total_count = int(total[0] or 0)
    consumed_count = int(consumed[0] or 0)

    return {
        "total_meals": total_count,
        "consumed_meals": consumed_count,
        "adherence_percentage": (
            round(consumed_count / total_count * 100, 2)
            if total_count else 0
        )
    }


# ==========================================================
# PHASE 7 - SECURE CLIENT CONTEXT FOR AI
# ==========================================================

def get_ai_client_context(trainer_user_id, client_user_id):
    _verify_trainer_client(trainer_user_id, client_user_id)

    profile = fetch_one(
        """
        SELECT age, height_cm, fitness_goal
        FROM clients
        WHERE user_id = ?
        """,
        (client_user_id,)
    )

    if not profile:
        raise ValueError("Client profile not found.")

    weight_history = fetch_all(
        """
        SELECT weight_kg, bmi, recorded_on
        FROM weight_logs
        WHERE client_user_id = ?
          AND trainer_user_id = ?
        ORDER BY recorded_on DESC
        LIMIT 20
        """,
        (client_user_id, trainer_user_id)
    )

    workout_plans = fetch_all(
        """
        SELECT id, plan_name, description, duration_weeks,
               start_date, end_date, status
        FROM workout_plans
        WHERE client_user_id = ?
          AND trainer_user_id = ?
        ORDER BY created_at DESC
        LIMIT 5
        """,
        (client_user_id, trainer_user_id)
    )

    workout_details = []
    for plan in workout_plans:
        exercises = fetch_all(
            """
            SELECT workout_day, exercise_name, sets, reps,
                   rest_seconds, instructions
            FROM workout_exercises
            WHERE plan_id = ?
              AND trainer_user_id = ?
            ORDER BY workout_day, created_at
            LIMIT 50
            """,
            (plan[0], trainer_user_id)
        )

        workout_details.append({
            "plan_name": plan[1],
            "description": plan[2],
            "duration_weeks": plan[3],
            "start_date": plan[4],
            "end_date": plan[5],
            "status": plan[6],
            "exercises": [
                {
                    "day": item[0],
                    "exercise": item[1],
                    "sets": item[2],
                    "reps": item[3],
                    "rest_seconds": item[4],
                    "instructions": item[5]
                }
                for item in exercises
            ]
        })

    diet_plans = fetch_all(
        """
        SELECT id, plan_name, description, daily_calories,
               protein_target, carbs_target, fat_target,
               start_date, end_date, status
        FROM diet_plans
        WHERE client_user_id = ?
          AND trainer_user_id = ?
        ORDER BY created_at DESC
        LIMIT 5
        """,
        (client_user_id, trainer_user_id)
    )

    diet_details = []
    for plan in diet_plans:
        meals = fetch_all(
            """
            SELECT meal_type, meal_name, food_items,
                   quantity, calories, protein, carbs, fat
            FROM diet_meals
            WHERE plan_id = ?
              AND trainer_user_id = ?
            ORDER BY created_at
            LIMIT 50
            """,
            (plan[0], trainer_user_id)
        )

        diet_details.append({
            "plan_name": plan[1],
            "description": plan[2],
            "daily_calories": plan[3],
            "protein_target": plan[4],
            "carbs_target": plan[5],
            "fat_target": plan[6],
            "start_date": plan[7],
            "end_date": plan[8],
            "status": plan[9],
            "meals": [
                {
                    "meal_type": item[0],
                    "meal_name": item[1],
                    "food_items": item[2],
                    "quantity": item[3],
                    "calories": item[4],
                    "protein": item[5],
                    "carbs": item[6],
                    "fat": item[7]
                }
                for item in meals
            ]
        })

    return {
        "age": profile[0],
        "height_cm": profile[1],
        "fitness_goal": profile[2],
        "weight_history": [
            {
                "weight_kg": item[0],
                "bmi": item[1],
                "recorded_on": item[2]
            }
            for item in weight_history
        ],
        "workout_plans": workout_details,
        "diet_plans": diet_details
    }


# ==========================================================
# PHASE 8 - REPORTS & ANALYTICS DATA SERVICES
# ==========================================================

def _validate_report_dates(start_date, end_date):
    try:
        start = date.fromisoformat(str(start_date))
        end = date.fromisoformat(str(end_date))
    except ValueError:
        raise ValueError("Invalid report date range.")

    if start > end:
        raise ValueError("Start date cannot be after end date.")

    if (end - start).days > 3660:
        raise ValueError("Report date range is too large.")

    return start.isoformat(), end.isoformat()


def get_trainer_analytics(trainer_user_id):
    verify_trainer(trainer_user_id)

    clients = fetch_one(
        """
        SELECT COUNT(*)
        FROM clients c
        INNER JOIN users u ON u.id = c.user_id
        WHERE u.role = 'client'
          AND u.status = 'active'
        """
    )

    pending = fetch_one(
        """
        SELECT COUNT(*)
        FROM users
        WHERE role = 'client' AND status = 'pending'
        """
    )

    workout_plans = fetch_one(
        """
        SELECT COUNT(*)
        FROM workout_plans
        WHERE trainer_user_id = ?
        """,
        (trainer_user_id,)
    )

    diet_plans = fetch_one(
        """
        SELECT COUNT(*)
        FROM diet_plans
        WHERE trainer_user_id = ?
        """,
        (trainer_user_id,)
    )

    weight_entries = fetch_one(
        """
        SELECT COUNT(*)
        FROM weight_logs
        WHERE trainer_user_id = ?
        """,
        (trainer_user_id,)
    )

    workout_completions = fetch_one(
        """
        SELECT COUNT(*)
        FROM workout_completions wc
        INNER JOIN workout_plans wp ON wp.id = wc.plan_id
        WHERE wp.trainer_user_id = ?
          AND wc.completed = 1
        """,
        (trainer_user_id,)
    )

    meal_logs = fetch_one(
        """
        SELECT COUNT(*)
        FROM meal_logs ml
        INNER JOIN diet_plans dp ON dp.id = ml.plan_id
        WHERE dp.trainer_user_id = ?
          AND ml.consumed = 1
        """,
        (trainer_user_id,)
    )

    return {
        "active_clients": int(clients[0] or 0),
        "pending_clients": int(pending[0] or 0),
        "workout_plans": int(workout_plans[0] or 0),
        "diet_plans": int(diet_plans[0] or 0),
        "weight_entries": int(weight_entries[0] or 0),
        "completed_workouts": int(workout_completions[0] or 0),
        "consumed_meals": int(meal_logs[0] or 0)
    }


def get_client_report_data(
    trainer_user_id,
    client_user_id,
    start_date,
    end_date
):
    _verify_trainer_client(trainer_user_id, client_user_id)

    start_date, end_date = _validate_report_dates(start_date, end_date)

    profile = fetch_one(
        """
        SELECT
            c.full_name,
            u.username,
            c.email,
            c.age,
            c.height_cm,
            c.fitness_goal,
            u.created_at
        FROM clients c
        INNER JOIN users u ON u.id = c.user_id
        WHERE c.user_id = ?
          AND u.role = 'client'
          AND u.status = 'active'
        """,
        (client_user_id,)
    )

    if not profile:
        raise PermissionError("Client profile not available.")

    weights = fetch_all(
        """
        SELECT weight_kg, bmi, notes, recorded_on
        FROM weight_logs
        WHERE client_user_id = ?
          AND trainer_user_id = ?
          AND recorded_on BETWEEN ? AND ?
        ORDER BY recorded_on ASC
        """,
        (client_user_id, trainer_user_id, start_date, end_date)
    )

    measurements = fetch_all(
        """
        SELECT
            waist_cm, chest_cm, hips_cm,
            left_arm_cm, right_arm_cm,
            left_thigh_cm, right_thigh_cm,
            notes, recorded_on
        FROM body_measurements
        WHERE client_user_id = ?
          AND trainer_user_id = ?
          AND recorded_on BETWEEN ? AND ?
        ORDER BY recorded_on ASC
        """,
        (client_user_id, trainer_user_id, start_date, end_date)
    )

    workouts = fetch_all(
        """
        SELECT
            wp.plan_name,
            we.workout_day,
            we.exercise_name,
            wc.completion_date,
            wc.completed,
            wc.notes
        FROM workout_completions wc
        INNER JOIN workout_plans wp ON wp.id = wc.plan_id
        INNER JOIN workout_exercises we ON we.id = wc.exercise_id
        WHERE wc.client_user_id = ?
          AND wp.trainer_user_id = ?
          AND wc.completion_date BETWEEN ? AND ?
        ORDER BY wc.completion_date ASC
        """,
        (client_user_id, trainer_user_id, start_date, end_date)
    )

    diet_activity = fetch_all(
        """
        SELECT
            dp.plan_name,
            dm.meal_type,
            dm.meal_name,
            ml.consumed_date,
            ml.consumed,
            ml.actual_calories,
            ml.actual_protein,
            ml.actual_carbs,
            ml.actual_fat,
            ml.notes
        FROM meal_logs ml
        INNER JOIN diet_plans dp ON dp.id = ml.plan_id
        INNER JOIN diet_meals dm ON dm.id = ml.meal_id
        WHERE ml.client_user_id = ?
          AND dp.trainer_user_id = ?
          AND ml.consumed_date BETWEEN ? AND ?
        ORDER BY ml.consumed_date ASC
        """,
        (client_user_id, trainer_user_id, start_date, end_date)
    )

    return {
        "profile": profile,
        "start_date": start_date,
        "end_date": end_date,
        "weights": weights,
        "measurements": measurements,
        "workouts": workouts,
        "diet_activity": diet_activity
    }


def get_my_report_data(client_user_id, start_date, end_date):
    verify_client(client_user_id)

    start_date, end_date = _validate_report_dates(start_date, end_date)

    profile = fetch_one(
        """
        SELECT
            c.full_name,
            u.username,
            c.age,
            c.height_cm,
            c.fitness_goal,
            u.created_at
        FROM clients c
        INNER JOIN users u ON u.id = c.user_id
        WHERE c.user_id = ?
          AND u.role = 'client'
          AND u.status = 'active'
        """,
        (client_user_id,)
    )

    if not profile:
        raise PermissionError("Your profile is unavailable.")

    weights = fetch_all(
        """
        SELECT weight_kg, bmi, notes, recorded_on
        FROM weight_logs
        WHERE client_user_id = ?
          AND recorded_on BETWEEN ? AND ?
        ORDER BY recorded_on ASC
        """,
        (client_user_id, start_date, end_date)
    )

    measurements = fetch_all(
        """
        SELECT
            waist_cm, chest_cm, hips_cm,
            left_arm_cm, right_arm_cm,
            left_thigh_cm, right_thigh_cm,
            notes, recorded_on
        FROM body_measurements
        WHERE client_user_id = ?
          AND recorded_on BETWEEN ? AND ?
        ORDER BY recorded_on ASC
        """,
        (client_user_id, start_date, end_date)
    )

    workouts = fetch_all(
        """
        SELECT
            wp.plan_name,
            we.workout_day,
            we.exercise_name,
            wc.completion_date,
            wc.completed,
            wc.notes
        FROM workout_completions wc
        INNER JOIN workout_plans wp ON wp.id = wc.plan_id
        INNER JOIN workout_exercises we ON we.id = wc.exercise_id
        WHERE wc.client_user_id = ?
          AND wc.completion_date BETWEEN ? AND ?
        ORDER BY wc.completion_date ASC
        """,
        (client_user_id, start_date, end_date)
    )

    diet_activity = fetch_all(
        """
        SELECT
            dp.plan_name,
            dm.meal_type,
            dm.meal_name,
            ml.consumed_date,
            ml.consumed,
            ml.actual_calories,
            ml.actual_protein,
            ml.actual_carbs,
            ml.actual_fat,
            ml.notes
        FROM meal_logs ml
        INNER JOIN diet_plans dp ON dp.id = ml.plan_id
        INNER JOIN diet_meals dm ON dm.id = ml.meal_id
        WHERE ml.client_user_id = ?
          AND ml.consumed_date BETWEEN ? AND ?
        ORDER BY ml.consumed_date ASC
        """,
        (client_user_id, start_date, end_date)
    )

    return {
        "profile": profile,
        "start_date": start_date,
        "end_date": end_date,
        "weights": weights,
        "measurements": measurements,
        "workouts": workouts,
        "diet_activity": diet_activity
    }


# ==========================================================
# PHASE 9 - NOTIFICATIONS
# ==========================================================

def _ensure_notifications_table():
    execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            recipient_user_id INTEGER NOT NULL,
            recipient_role TEXT NOT NULL,
            notification_type TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            related_id TEXT,
            is_read INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


def create_notification(
    recipient_user_id,
    notification_type,
    title,
    message,
    related_id=None
):
    """Create a persistent notification for a valid trainer or client user."""
    _ensure_notifications_table()

    user = fetch_one(
        """
        SELECT id, role
        FROM users
        WHERE id = ?
        LIMIT 1
        """,
        (recipient_user_id,)
    )

    if not user:
        raise ValueError("Notification recipient does not exist.")

    role = user[1]
    if role not in ("trainer", "client"):
        raise PermissionError("Invalid notification recipient.")

    if not title or not message:
        raise ValueError("Notification title and message are required.")

    notification_id = str(uuid.uuid4())

    execute(
        """
        INSERT INTO notifications (
            id,
            recipient_user_id,
            recipient_role,
            notification_type,
            title,
            message,
            related_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            notification_id,
            recipient_user_id,
            role,
            str(notification_type)[:50],
            str(title)[:150],
            str(message)[:1000],
            str(related_id) if related_id is not None else None
        )
    )

    return notification_id


def notify_trainer_new_registration(client_username=""):
    """Helper to notify the active trainer when a new client registers."""
    trainer_id = get_active_trainer_user_id()
    if not trainer_id:
        return None

    detail = f" (@{client_username})" if client_username else ""
    return create_notification(
        recipient_user_id=trainer_id,
        notification_type="new_registration",
        title="New client registration",
        message=(
            f"A new client{detail} has submitted a registration request. "
            "Review it in Registration Requests."
        )
    )


def get_my_notifications(user_id, limit=50):
    """Return only the logged-in user's notifications."""
    _ensure_notifications_table()

    user = fetch_one(
        "SELECT id, role FROM users WHERE id = ?",
        (user_id,)
    )

    if not user:
        raise PermissionError("Account not found.")

    safe_limit = max(1, min(int(limit), 100))

    return fetch_all(
        """
        SELECT
            id,
            notification_type,
            title,
            message,
            is_read,
            created_at
        FROM notifications
        WHERE recipient_user_id = ?
          AND recipient_role = ?
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """,
        (user_id, user[1], safe_limit)
    )


def get_unread_notification_count(user_id):
    _ensure_notifications_table()

    user = fetch_one(
        "SELECT id, role FROM users WHERE id = ?",
        (user_id,)
    )

    if not user:
        raise PermissionError("Account not found.")

    result = fetch_one(
        """
        SELECT COUNT(*)
        FROM notifications
        WHERE recipient_user_id = ?
          AND recipient_role = ?
          AND is_read = 0
        """,
        (user_id, user[1])
    )

    return int(result[0] or 0)


def mark_notification_read(user_id, notification_id):
    """A user can mark only their own notification as read."""
    _ensure_notifications_table()

    notification = fetch_one(
        """
        SELECT id
        FROM notifications
        WHERE id = ?
          AND recipient_user_id = ?
        """,
        (notification_id, user_id)
    )

    if not notification:
        raise PermissionError("Notification not found.")

    execute(
        """
        UPDATE notifications
        SET is_read = 1
        WHERE id = ?
          AND recipient_user_id = ?
        """,
        (notification_id, user_id)
    )


def mark_all_notifications_read(user_id):
    _ensure_notifications_table()

    user = fetch_one(
        "SELECT id, role FROM users WHERE id = ?",
        (user_id,)
    )

    if not user:
        raise PermissionError("Account not found.")

    execute(
        """
        UPDATE notifications
        SET is_read = 1
        WHERE recipient_user_id = ?
          AND recipient_role = ?
          AND is_read = 0
        """,
        (user_id, user[1])
    )


def delete_my_notification(user_id, notification_id):
    """Delete only a notification belonging to the logged-in user."""
    _ensure_notifications_table()

    notification = fetch_one(
        """
        SELECT id
        FROM notifications
        WHERE id = ?
          AND recipient_user_id = ?
        """,
        (notification_id, user_id)
    )

    if not notification:
        raise PermissionError("Notification not found.")

    execute(
        """
        DELETE FROM notifications
        WHERE id = ?
          AND recipient_user_id = ?
        """,
        (notification_id, user_id)
    )