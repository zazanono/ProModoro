import unittest
from unittest.mock import patch

from promodoro.alerts import AlertSettings
from promodoro.app import PomodoroApp
from promodoro.timer import Durations, Phase


class AppTests(unittest.IsolatedAsyncioTestCase):
    async def test_toggle_at_expiry_keeps_pause_intent(self):
        app = PomodoroApp(alerts=AlertSettings(False, False))
        async with app.run_test():
            for phase, following in (
                (Phase.FOCUS, Phase.SHORT),
                (Phase.SHORT, Phase.FOCUS),
                (Phase.LONG, Phase.FOCUS),
            ):
                with self.subTest(phase=phase):
                    app.timer.select(phase)
                    app.timer.deadline = 100
                    with patch("promodoro.timer.time.monotonic", return_value=100):
                        app.action_toggle()
                    self.assertEqual(app.timer.phase, following)
                    self.assertFalse(app.timer.running)
                    self.assertEqual(app.timer.remaining, app.timer.total)

    async def test_toggle_starts_and_pauses(self):
        app = PomodoroApp(alerts=AlertSettings(False, False))
        async with app.run_test():
            app.action_toggle()
            self.assertTrue(app.timer.running)
            app.action_toggle()
            self.assertFalse(app.timer.running)

    async def test_settings_only_reset_when_active_duration_changes(self):
        app = PomodoroApp(alerts=AlertSettings(False, False))
        async with app.run_test():
            app.timer.start()
            deadline = app.timer.deadline
            app.apply_settings(Durations(short=600))
            self.assertEqual(app.timer.deadline, deadline)
            app.apply_settings(Durations(focus=3000, short=600))
            self.assertFalse(app.timer.running)
            self.assertEqual(app.timer.remaining, 3000)
