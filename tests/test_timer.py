import unittest
from unittest.mock import patch

from promodoro.timer import Durations, Phase, Timer, parse_duration


class DurationTests(unittest.TestCase):
    def test_supported_durations(self):
        for value, expected in {
            "25": 1500,
            "90s": 90,
            "25:00": 1500,
            "4.1m": 246,
            "1.1h": 3960,
            "0.55h": 1980,
            "180m": 10800,
            "1s": 1,
        }.items():
            with self.subTest(value=value):
                self.assertEqual(parse_duration(value), expected)

    def test_invalid_durations(self):
        for value in (
            "0",
            "181m",
            "0.5s",
            "1:60",
            "nope",
            "1.00000000000000000000000000001s",
        ):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_duration(value)


class TimerTests(unittest.TestCase):
    def test_pause_preserves_partial_seconds(self):
        timer = Timer(Durations(focus=10))
        with patch("promodoro.timer.time.monotonic", return_value=100):
            timer.start()
        with patch("promodoro.timer.time.monotonic", return_value=102.25):
            timer.pause()
        self.assertEqual(timer.remaining, 7.75)
        with patch("promodoro.timer.time.monotonic", return_value=200):
            timer.start()
        self.assertEqual(timer.deadline, 207.75)

    def test_completion_cycle(self):
        timer = Timer()
        with patch("promodoro.timer.time.monotonic", return_value=100):
            for completed in range(1, 5):
                timer.start()
                timer.deadline = 100
                self.assertTrue(timer.tick())
                self.assertEqual(timer.completed, completed)
                expected = Phase.LONG if completed == 4 else Phase.SHORT
                self.assertEqual(timer.phase, expected)
                self.assertTrue(timer.running)
                self.assertFalse(timer.tick())
                timer.deadline = 100
                self.assertTrue(timer.tick())
                self.assertEqual(timer.phase, Phase.FOCUS)
                self.assertFalse(timer.running)
                self.assertEqual(timer.completed, completed)

    def test_skip_does_not_count_completion(self):
        timer = Timer()
        timer.start()
        timer.skip()
        self.assertEqual(timer.completed, 0)
        self.assertEqual(timer.phase, Phase.SHORT)
        self.assertFalse(timer.running)
