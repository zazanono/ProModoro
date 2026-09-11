"""Completion alerts without blocking the timer or requiring extra packages."""

import asyncio
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class AlertSettings:
    notifications: bool = True
    sound: bool = True


def supports_notifications() -> bool:
    return sys.platform == "darwin"


async def _run(*command: str) -> bool:
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
    except OSError:
        return False
    try:
        return await asyncio.wait_for(process.wait(), timeout=5) == 0
    except asyncio.TimeoutError:
        return False
    finally:
        if process.returncode is None:
            try:
                process.kill()
            except ProcessLookupError:
                pass
            await process.wait()


async def send_notification(message: str) -> bool:
    if not supports_notifications():
        return False
    # Pass text as an argument, never as executable AppleScript or shell code.
    return await _run(
        "/usr/bin/osascript",
        "-e",
        "on run argv\n"
        'display notification (item 1 of argv) with title "ProModoro"\n'
        "end run",
        message,
    )


async def play_sound() -> bool:
    if sys.platform != "darwin":
        return False
    return await _run("/usr/bin/afplay", "/System/Library/Sounds/Glass.aiff")
