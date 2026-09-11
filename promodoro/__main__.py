"""Command-line entry point."""

import argparse
import sys

from promodoro.alerts import AlertSettings
from promodoro.timer import Durations, parse_duration


def duration(value: str) -> int:
    try:
        return parse_duration(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pomo",
        description="A Pomodoro timer with keyboard and mouse controls.",
        epilog="Duration flags accept minutes, 25m, 90s, 1h, or 25:00.",
    )
    parser.add_argument(
        "minutes",
        nargs="?",
        type=int,
        help="focus minutes, 1 to 180; breaks are 1/5 and 3/5 of this time",
    )
    parser.add_argument("--focus", type=duration, help="focus time, default 25m")
    parser.add_argument(
        "--short", type=duration, help="short break, overrides the proportional default"
    )
    parser.add_argument(
        "--long", type=duration, help="long break, overrides the proportional default"
    )
    parser.add_argument(
        "-s", "--start", action="store_true", help="start counting immediately"
    )
    parser.add_argument("--version", action="version", version="ProModoro 0.1.0")
    parser.add_argument(
        "--no-sound", action="store_true", help="disable completion sounds"
    )
    parser.add_argument(
        "--no-notifications",
        action="store_true",
        help="disable macOS desktop notifications",
    )
    args = parser.parse_args()
    if args.minutes is not None:
        if not 1 <= args.minutes <= 180:
            parser.error("focus minutes must be between 1 and 180")
        if args.focus is not None:
            parser.error("use either positional minutes or --focus, not both")
    minutes = args.minutes if args.minutes is not None else 25
    focus = args.focus if args.focus is not None else minutes * 60
    durations = Durations(
        focus=focus,
        short=args.short if args.short is not None else max(1, round(focus / 5)),
        long=args.long if args.long is not None else max(1, round(focus * 3 / 5)),
    )
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        parser.exit(
            2, "ProModoro needs an interactive terminal. Run it without piping.\n"
        )
    from promodoro.app import PomodoroApp

    PomodoroApp(
        durations,
        start=args.start,
        alerts=AlertSettings(
            notifications=not args.no_notifications, sound=not args.no_sound
        ),
    ).run()


if __name__ == "__main__":
    main()
