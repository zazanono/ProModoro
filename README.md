# ProModoro

A Pomodoro CLI inspired by [Pomofocus](https://pomofocus.io/). A large live countdown, clickable controls, and keyboard shortcuts, built with [Textual](https://textual.textualize.io/).

## Run

Requires Python 3.10 or newer and an interactive terminal.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
promodoro
```

To make `pomo` available from any directory without activating the environment,
link its launcher into a directory on your PATH:

```sh
mkdir -p ~/.local/bin
ln -s "$PWD/.venv/bin/pomo" ~/.local/bin/pomo
```

Keep this project and its `.venv` at the same location when using this link.
Ensure `~/.local/bin` is on your PATH.

```sh
pomo 50  # 50 minutes focus, 10 minutes short break, 30 minutes long break
pomo 25  # 25 minutes focus, 5 minutes short break, 15 minutes long break
pomo     # same as pomo 25
pomo 50 -s  # begin counting immediately
```

Positional minutes must be a whole number from 1 to 180. Short breaks use one
fifth of the focus time; long breaks use three fifths. You can override either
break with `--short` or `--long`, for example `pomo 50 --long 20`.
Press Start after launch, or pass `-s` or `--start` to begin immediately.

Set durations at launch. Plain numbers mean minutes; `m`, `s`, `h`, and `MM:SS` also work.

```sh
promodoro --focus 50 --short 10 --long 20
promodoro --focus 10s --short 5s --start
python -m promodoro
```

## Controls

Click the phase tabs, Start/Pause, Reset, Skip, or Settings. Mouse support depends on your terminal. Tab and Shift+Tab move between controls; Enter activates the selected button.

| Key | Action |
| --- | --- |
| Space | Start or pause |
| R | Reset the current timer |
| N | Skip to the next phase |
| 1 / 2 / 3 | Select focus / short break / long break |
| S | Edit durations |
| : | Open the command input |
| Escape | Close commands or cancel settings |
| Q / Ctrl+C | Quit |

In the command input, enter `focus 25`, `short 5m`, `long 15:00`, `start`, `pause`, `reset`, `skip`, or `help`, then press Enter. Durations must be between 1 second and 180 minutes. Settings apply to this launch only. Changing the active phase's duration resets and pauses that timer; editing another phase leaves it running.

## Timer behavior

- Defaults are 25 minutes of focus, 5 minutes for a short break, and 15 minutes for a long break.
- Focus is coral, short breaks are teal, and long breaks are blue. Text labels also identify each phase.
- Finishing focus starts a break automatically. Every fourth completed focus session starts a long break.
- Finishing a break prepares a fresh focus timer and waits for Start.
- Reset, Skip, and manually changing phases pause the timer. Skipped sessions do not count as completed.
- A monotonic deadline drives the countdown, preserving partial seconds when paused and avoiding drift from delayed screen updates.
- The app must remain open to count down. Session counts and settings are not saved when it exits.

## Completion alerts

When focus or a break finishes, the app shows a highlighted message and a
10-second toast. On macOS, it also sends a desktop notification and plays the
system Glass chime. Sound plays independently of desktop notification delivery.
Other platforms use the terminal bell, whose sound depends on terminal settings;
desktop notifications are currently supported only on macOS.

Use Settings to toggle desktop notifications and sound independently, or launch
with `pomo --no-sound`, `pomo --no-notifications`, or both. These preferences apply
to this launch only. Resetting, skipping, and manually changing phases do not
trigger completion alerts.

macOS notification permissions and Focus settings may suppress banners. After the
first alert, check System Settings > Notifications for the script's notification
entry if banners do not appear. Alerts run in the background so the next timer
keeps counting. If sound playback fails, the app falls back to the terminal bell.

An 80-column, 24-row terminal works; a taller terminal gives the layout more space. Small terminals can scroll.

## Development

```sh
python -m pip install -e '.[dev]'
ruff check .
ruff format --check .
```

For optional local browser inspection of the actual TUI:

```sh
python -m pip install -e '.[preview]'
python -c 'from textual_serve.server import Server; Server("python -m promodoro.app", host="127.0.0.1", port=8765).serve()'
```

Open the local URL printed by the server. The CLI itself does not need a browser or network access. Tasks, accounts, reports, and other productivity features are outside this first version.
