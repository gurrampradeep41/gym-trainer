import sqlite3
import libsql

from config import get_setting


SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE COLLATE NOCASE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('trainer', 'client')),
        status TEXT NOT NULL DEFAULT 'active'
        CHECK(status IN ('pending', 'active', 'rejected', 'disabled')),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL UNIQUE,
        full_name TEXT NOT NULL,
        email TEXT,
        phone TEXT,
        age INTEGER,
        height_cm REAL,
        fitness_goal TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS login_attempts (
        username TEXT PRIMARY KEY COLLATE NOCASE,
        failed_attempts INTEGER NOT NULL DEFAULT 0,
        locked_until INTEGER NOT NULL DEFAULT 0,
        last_attempt_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        actor_user_id INTEGER,
        event_type TEXT NOT NULL,
        target_username TEXT,
        details TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(actor_user_id) REFERENCES users(id)
        ON DELETE SET NULL
    )
    """,

    """
    CREATE TABLE IF NOT EXISTS trainer_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trainer_user_id INTEGER NOT NULL UNIQUE,
        display_name TEXT NOT NULL,
        professional_title TEXT,
        experience TEXT,
        photo_url TEXT,
        achievements TEXT,
        bio TEXT,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(trainer_user_id) REFERENCES users(id)
        ON DELETE CASCADE
    )
    """,

    "CREATE INDEX IF NOT EXISTS idx_clients_user_id ON clients(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_users_role_status ON users(role, status)",
    "CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_logs(created_at)"
]


def _database_config():
    local_path = get_setting("FITPRO_LOCAL_DB_PATH")

    if local_path:
        return "local", str(local_path), None

    url = get_setting("TURSO_DATABASE_URL")
    token = get_setting("TURSO_AUTH_TOKEN")

    if not url or not token:
        raise RuntimeError(
            "Missing Turso database URL or authentication token."
        )

    return "turso", str(url), str(token)


def connect():
    mode, database, token = _database_config()

    if mode == "local":
        conn = sqlite3.connect(database, timeout=15)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    conn = libsql.connect(
        database=database,
        auth_token=token
    )
    try:
        conn.execute("PRAGMA foreign_keys = ON")
    except Exception:
        pass
    return conn


def _run_statements(statements):
    conn = connect()
    try:
        for statement in statements:
            conn.execute(statement)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database():
    _run_statements(SCHEMA)


def fetch_one(sql, params=()):
    conn = connect()
    try:
        cursor = conn.execute(sql, params)
        return cursor.fetchone()
    finally:
        conn.close()


def fetch_all(sql, params=()):
    conn = connect()
    try:
        cursor = conn.execute(sql, params)
        return cursor.fetchall()
    finally:
        conn.close()


def execute(sql, params=()):
    conn = connect()
    try:
        cursor = conn.execute(sql, params)
        conn.commit()
        return getattr(cursor, "lastrowid", None)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def create_client_account(
    username,
    password_hash,
    full_name,
    email,
    phone,
    age,
    height,
    goal
):
    conn = connect()
    try:
        conn.execute(
            """
            INSERT INTO users(
                username,
                password_hash,
                role,
                status
            )
            VALUES(?, ?, 'client', 'pending')
            """,
            (username, password_hash)
        )

        user = conn.execute(
            "SELECT id FROM users WHERE username=?",
            (username,)
        ).fetchone()

        if not user:
            raise RuntimeError("Failed to retrieve created user ID.")

        user_id = user[0]

        conn.execute(
            """
            INSERT INTO clients(
                user_id,
                full_name,
                email,
                phone,
                age,
                height_cm,
                fitness_goal
            )
            VALUES(?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                full_name,
                email or None,
                phone or None,
                age,
                height,
                goal
            )
        )

        conn.execute(
            """
            INSERT INTO audit_logs(
                actor_user_id,
                event_type,
                target_username,
                details
            )
            VALUES(
                NULL,
                'client_registration_submitted',
                ?,
                'New client registration request'
            )
            """,
            (username,)
        )

        conn.commit()
        return user_id

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def set_client_status(user_id, status, actor_user_id):
    allowed = ("active", "rejected", "disabled")

    if status not in allowed:
        raise ValueError("Invalid client status.")

    conn = connect()
    try:
        row = conn.execute(
            "SELECT username FROM users WHERE id=? AND role='client'",
            (user_id,)
        ).fetchone()

        target_username = row[0] if row else None

        conn.execute(
            """
            UPDATE users
            SET status=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
              AND role='client'
            """,
            (status, user_id)
        )

        conn.execute(
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
                actor_user_id,
                f"client_{status}",
                target_username,
                f"Client user ID: {user_id}"
            )
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def database_health():
    result = fetch_one("SELECT 1")
    return bool(result and result[0] == 1)


def create_phase4_tables():
    """Create fitness progress tables without changing existing records."""
    _run_statements([
        """
        CREATE TABLE IF NOT EXISTS weight_logs (
            id TEXT PRIMARY KEY,
            client_user_id TEXT NOT NULL,
            trainer_user_id TEXT NOT NULL,
            weight_kg REAL NOT NULL,
            bmi REAL,
            notes TEXT DEFAULT '',
            recorded_on TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_user_id) REFERENCES users(id),
            FOREIGN KEY (trainer_user_id) REFERENCES users(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS body_measurements (
            id TEXT PRIMARY KEY,
            client_user_id TEXT NOT NULL,
            trainer_user_id TEXT NOT NULL,
            waist_cm REAL,
            chest_cm REAL,
            hips_cm REAL,
            left_arm_cm REAL,
            right_arm_cm REAL,
            left_thigh_cm REAL,
            right_thigh_cm REAL,
            notes TEXT DEFAULT '',
            recorded_on TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_user_id) REFERENCES users(id),
            FOREIGN KEY (trainer_user_id) REFERENCES users(id)
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_weight_client_date
        ON weight_logs(client_user_id, recorded_on)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_measurements_client_date
        ON body_measurements(client_user_id, recorded_on)
        """
    ])


# ==========================================================
# PHASE 5 - WORKOUT PLAN DATABASE TABLES
# ==========================================================

def create_phase5_tables():
    _run_statements([
        """
        CREATE TABLE IF NOT EXISTS workout_plans (
            id TEXT PRIMARY KEY,
            trainer_user_id TEXT NOT NULL,
            client_user_id TEXT NOT NULL,
            plan_name TEXT NOT NULL,
            description TEXT DEFAULT '',
            duration_weeks INTEGER DEFAULT 4,
            start_date TEXT,
            end_date TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (trainer_user_id) REFERENCES users(id),
            FOREIGN KEY (client_user_id) REFERENCES users(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS workout_exercises (
            id TEXT PRIMARY KEY,
            plan_id TEXT NOT NULL,
            trainer_user_id TEXT NOT NULL,
            workout_day TEXT NOT NULL,
            exercise_name TEXT NOT NULL,
            sets INTEGER NOT NULL,
            reps TEXT NOT NULL,
            rest_seconds INTEGER DEFAULT 60,
            instructions TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plan_id) REFERENCES workout_plans(id),
            FOREIGN KEY (trainer_user_id) REFERENCES users(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS workout_completions (
            id TEXT PRIMARY KEY,
            plan_id TEXT NOT NULL,
            exercise_id TEXT NOT NULL,
            client_user_id TEXT NOT NULL,
            completion_date TEXT NOT NULL,
            completed INTEGER DEFAULT 1,
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plan_id) REFERENCES workout_plans(id),
            FOREIGN KEY (exercise_id) REFERENCES workout_exercises(id),
            FOREIGN KEY (client_user_id) REFERENCES users(id)
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_workout_plans_client
        ON workout_plans(client_user_id, status)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_workout_exercises_plan
        ON workout_exercises(plan_id, workout_day)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_workout_completion_client
        ON workout_completions(client_user_id, completion_date)
        """
    ])


# ==========================================================
# PHASE 6 - DIET & NUTRITION DATABASE TABLES
# ==========================================================

def create_phase6_tables():
    _run_statements([
        """
        CREATE TABLE IF NOT EXISTS diet_plans (
            id TEXT PRIMARY KEY,
            trainer_user_id TEXT NOT NULL,
            client_user_id TEXT NOT NULL,
            plan_name TEXT NOT NULL,
            description TEXT DEFAULT '',
            daily_calories REAL,
            protein_target REAL,
            carbs_target REAL,
            fat_target REAL,
            start_date TEXT,
            end_date TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (trainer_user_id) REFERENCES users(id),
            FOREIGN KEY (client_user_id) REFERENCES users(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS diet_meals (
            id TEXT PRIMARY KEY,
            plan_id TEXT NOT NULL,
            trainer_user_id TEXT NOT NULL,
            meal_type TEXT NOT NULL,
            meal_name TEXT NOT NULL,
            food_items TEXT NOT NULL,
            quantity TEXT DEFAULT '',
            calories REAL DEFAULT 0,
            protein REAL DEFAULT 0,
            carbs REAL DEFAULT 0,
            fat REAL DEFAULT 0,
            instructions TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plan_id) REFERENCES diet_plans(id),
            FOREIGN KEY (trainer_user_id) REFERENCES users(id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS meal_logs (
            id TEXT PRIMARY KEY,
            plan_id TEXT NOT NULL,
            meal_id TEXT NOT NULL,
            client_user_id TEXT NOT NULL,
            consumed_date TEXT NOT NULL,
            consumed INTEGER DEFAULT 1,
            actual_calories REAL,
            actual_protein REAL,
            actual_carbs REAL,
            actual_fat REAL,
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (plan_id) REFERENCES diet_plans(id),
            FOREIGN KEY (meal_id) REFERENCES diet_meals(id),
            FOREIGN KEY (client_user_id) REFERENCES users(id)
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_diet_plans_client
        ON diet_plans(client_user_id, status)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_diet_meals_plan
        ON diet_meals(plan_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_meal_logs_client_date
        ON meal_logs(client_user_id, consumed_date)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_meal_logs_plan_date
        ON meal_logs(plan_id, consumed_date)
        """
    ])


# ==========================================================
# PHASE 9 - NOTIFICATIONS DATABASE TABLE
# ==========================================================

def create_phase9_tables():
    _run_statements([
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            trainer_user_id TEXT NOT NULL,
            client_user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            notification_type TEXT NOT NULL,
            related_id TEXT,
            is_read INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_notifications_client
        ON notifications(client_user_id, is_read, created_at)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_notifications_trainer
        ON notifications(trainer_user_id, created_at)
        """
    ])