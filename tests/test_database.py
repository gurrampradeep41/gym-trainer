import os
import tempfile
import unittest
from unittest.mock import patch


def _mock_setting(temp_db_path):
    def _get(key, default=None):
        if key == "FITPRO_LOCAL_DB_PATH":
            return temp_db_path
        if key in ("TURSO_DATABASE_URL", "TURSO_AUTH_TOKEN"):
            return None
        return default
    return _get


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp.close()

        self.db_patcher = patch(
            "db.get_setting",
            side_effect=_mock_setting(self.tmp.name)
        )
        self.config_patcher = patch(
            "config.get_setting",
            side_effect=_mock_setting(self.tmp.name)
        )
        self.db_patcher.start()
        self.config_patcher.start()

        from db import (
            initialize_database,
            create_phase4_tables,
            create_phase5_tables,
            create_phase6_tables,
            create_phase9_tables,
        )

        initialize_database()
        create_phase4_tables()
        create_phase5_tables()
        create_phase6_tables()
        create_phase9_tables()

    def tearDown(self):
        self.db_patcher.stop()
        self.config_patcher.stop()
        for suffix in ("", "-wal", "-shm"):
            try:
                os.unlink(self.tmp.name + suffix)
            except OSError:
                pass

    def test_database_health_check(self):
        from db import database_health
        self.assertTrue(database_health())

    def test_expected_tables_exist(self):
        from db import fetch_all
        rows = fetch_all("SELECT name FROM sqlite_master WHERE type='table'")
        names = {r[0] for r in rows}
        expected_core_tables = {
            "users",
            "clients",
            "login_attempts",
            "audit_logs",
        }
        self.assertTrue(expected_core_tables.issubset(names))

    def test_duplicate_username_is_rejected(self):
        from db import execute
        execute(
            "INSERT INTO users(username, password_hash, role, status) VALUES(?, ?, ?, ?)",
            ("trainer", "fakehash", "trainer", "active"),
        )
        with self.assertRaises(Exception):
            execute(
                "INSERT INTO users(username, password_hash, role, status) VALUES(?, ?, ?, ?)",
                ("TRAINER", "fakehash", "client", "pending"),
            )


if __name__ == "__main__":
    unittest.main()