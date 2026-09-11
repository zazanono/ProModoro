import unittest
from unittest.mock import patch

from promodoro.__main__ import main
from promodoro.timer import Durations


class CliTests(unittest.TestCase):
    def test_duration_defaults_and_overrides(self):
        cases = [
            ([], Durations()),
            (["50"], Durations(3000, 600, 1800)),
            (["--focus", "50"], Durations(3000, 600, 1800)),
            (["--focus", "50m"], Durations(3000, 600, 1800)),
            (["--focus", "50", "--short", "7"], Durations(3000, 420, 1800)),
            (["50", "--long", "20"], Durations(3000, 600, 1200)),
            (["--focus", "1s"], Durations(1, 1, 1)),
            (["--focus", "8s"], Durations(8, 2, 5)),
        ]
        for arguments, expected in cases:
            with (
                self.subTest(arguments=arguments),
                patch("sys.argv", ["pomo", *arguments]),
                patch("sys.stdin.isatty", return_value=True),
                patch("sys.stdout.isatty", return_value=True),
                patch("promodoro.app.PomodoroApp") as app,
            ):
                main()
                self.assertEqual(app.call_args.args[0], expected)
                app.return_value.run.assert_called_once()
