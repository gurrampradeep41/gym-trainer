import unittest
from security import (
    validate_username,
    validate_password,
    hash_password,
    verify_password,
    validate_new_password,
    validate_email,
    validate_phone,
    validate_age,
    validate_weight,
)


class SecurityTests(unittest.TestCase):
    def test_username_valid(self):
        self.assertTrue(validate_username("trainer_01")[0])

    def test_username_rejects_spaces_and_short_values(self):
        self.assertFalse(validate_username("ab")[0])
        self.assertFalse(validate_username("user name")[0])

    def test_password_minimum_length(self):
        self.assertFalse(validate_password("Short123!")[0])
        self.assertTrue(validate_password("A-Long-Unique-Passphrase-42")[0])

    def test_password_hash_is_not_plaintext_and_verifies(self):
        password = "A-Long-Unique-Passphrase-42"
        hashed = hash_password(password)
        self.assertNotEqual(password, hashed)
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("wrong-password-123", hashed))


class TestSecurityValidation(unittest.TestCase):
    def test_valid_password(self):
        self.assertTrue(
            validate_new_password("FitPro@Secure2026")
        )

    def test_short_password_rejected(self):
        with self.assertRaises(ValueError):
            validate_new_password("Fit@123")

    def test_password_without_special_character_rejected(self):
        with self.assertRaises(ValueError):
            validate_new_password("FitProSecure202612")

    def test_password_over_bcrypt_limit_rejected(self):
        with self.assertRaises(ValueError):
            validate_new_password("A" * 73)

    def test_valid_email(self):
        self.assertEqual(
            validate_email("TEST@example.com"),
            "test@example.com"
        )

    def test_invalid_email(self):
        with self.assertRaises(ValueError):
            validate_email("invalid-email")

    def test_valid_phone(self):
        self.assertTrue(validate_phone("+91 9876543210"))

    def test_invalid_phone(self):
        with self.assertRaises(ValueError):
            validate_phone("phone-number")

    def test_valid_age(self):
        self.assertEqual(validate_age(25), 25)

    def test_invalid_age(self):
        with self.assertRaises(ValueError):
            validate_age(10)

    def test_valid_weight(self):
        self.assertEqual(validate_weight(75), 75.0)

    def test_invalid_weight(self):
        with self.assertRaises(ValueError):
            validate_weight(500)


if __name__ == "__main__":
    unittest.main()