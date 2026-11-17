import unittest
from unittest.mock import patch

from services import (
    get_my_weight_history,
    get_my_measurement_history,
    get_my_workout_plans,
    get_my_diet_plans,
    get_my_notifications,
)


class TestClientIsolation(unittest.TestCase):

    @patch("services.fetch_all")
    @patch("services.verify_client")
    def test_client_only_receives_own_weight_history(
        self,
        mock_verify,
        mock_fetch_all
    ):
        client_a = 101
        own_records = [
            (75.0, 24.0, "Progress entry", "2026-11-01")
        ]
        mock_fetch_all.return_value = own_records

        result = get_my_weight_history(client_a)

        mock_verify.assert_called_once_with(client_a)
        self.assertEqual(result, own_records)

        query = mock_fetch_all.call_args[0][0]
        params = mock_fetch_all.call_args[0][1]

        self.assertIn("client_user_id = ?", query)
        self.assertEqual(tuple(params), (client_a,))

    @patch("services.fetch_all")
    @patch("services.verify_client")
    def test_unauthorized_client_blocked_before_query(
        self,
        mock_verify,
        mock_fetch_all
    ):
        mock_verify.side_effect = PermissionError("Access denied")

        with self.assertRaises(PermissionError):
            get_my_weight_history(999)

        mock_fetch_all.assert_not_called()

    @patch("services.fetch_all")
    @patch("services.verify_client")
    def test_client_only_receives_own_measurements(
        self,
        mock_verify,
        mock_fetch_all
    ):
        client_a = 101
        mock_fetch_all.return_value = []

        get_my_measurement_history(client_a)

        mock_verify.assert_called_once_with(client_a)
        query, params = mock_fetch_all.call_args[0]
        self.assertIn("client_user_id = ?", query)
        self.assertIn(client_a, params)

    @patch("services.fetch_all")
    @patch("services.verify_client")
    def test_client_only_receives_own_workouts_and_diet(
        self,
        mock_verify,
        mock_fetch_all
    ):
        client_a = 101
        mock_fetch_all.return_value = []

        get_my_workout_plans(client_a)
        workout_query, workout_params = mock_fetch_all.call_args[0]
        self.assertIn("client_user_id = ?", workout_query)
        self.assertIn(client_a, workout_params)

        get_my_diet_plans(client_a)
        diet_query, diet_params = mock_fetch_all.call_args[0]
        self.assertIn("client_user_id = ?", diet_query)
        self.assertIn(client_a, diet_params)

    @patch("services.fetch_all")
    def test_client_only_receives_own_notifications(
        self,
        mock_fetch_all
    ):
        client_a = 101
        mock_fetch_all.return_value = []

        get_my_notifications(client_a)

        query, params = mock_fetch_all.call_args[0]
        self.assertIn("user_id = ?", query)
        self.assertIn(client_a, params)


if __name__ == "__main__":
    unittest.main()