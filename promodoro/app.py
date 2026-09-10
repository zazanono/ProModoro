"""Mouse and keyboard interface for the timer."""

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Digits, Footer, Input, Label, Static

from promodoro.timer import Durations, Phase, Timer, format_time, parse_duration


class SettingsScreen(ModalScreen[Durations | None]):
    BINDINGS = [Binding("escape", "dismiss(None)", "Cancel")]

    def __init__(self, durations: Durations) -> None:
        super().__init__()
        self.durations = durations

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="settings-dialog"):
            yield Label("Timer settings", id="settings-title")
            yield Static("Enter minutes, 90s, or 25:00. Range: 1s to 180m.")
            for phase in Phase:
                yield Label(phase.label)
                yield Input(
                    format_time(self.durations.for_phase(phase)),
                    id=f"duration-{phase.value}",
                    select_on_focus=True,
                    max_length=12,
                )
            yield Static("", id="settings-error", markup=False)
            yield Static("Changing the current duration resets and pauses its timer.")
            with Horizontal(classes="dialog-actions"):
                yield Button("Cancel", id="cancel")
                yield Button("Save", id="save", variant="primary")

    @on(Button.Pressed, "#cancel")
    def cancel(self) -> None:
        self.dismiss(None)

    @on(Button.Pressed, "#save")
    @on(Input.Submitted)
    def save(self) -> None:
        values = {}
        for phase in Phase:
            field = self.query_one(f"#duration-{phase.value}", Input)
            try:
                values[phase.value] = parse_duration(field.value)
            except ValueError as error:
                self.query_one("#settings-error", Static).update(
                    f"{phase.label}: {error}"
                )
                field.focus()
                return
        self.dismiss(Durations(**values))


class PomodoroApp(App):
    TITLE = "ProModoro"
    CSS_PATH = "app.tcss"
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [
        Binding("space", "toggle", "Start / pause", priority=True),
        Binding("r", "reset", "Reset"),
        Binding("n", "skip", "Skip"),
        Binding("s", "settings", "Settings"),
        Binding("colon", "command", "Command"),
        Binding("1", "phase('focus')", "Focus", show=False),
        Binding("2", "phase('short')", "Short break", show=False),
        Binding("3", "phase('long')", "Long break", show=False),
        Binding("escape", "leave_command", "Close command", show=False),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, durations: Durations | None = None, start: bool = False) -> None:
        super().__init__()
        self.timer = Timer(durations)
        self.start_immediately = start

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="page"):
            with Vertical(id="workspace"):
                with Horizontal(id="masthead"):
                    yield Static("◷  ProModoro", id="brand")
                    yield Static("A little time. One thing.", id="tagline")
                with Vertical(id="timer-card"):
                    with Horizontal(id="phases"):
                        for phase in Phase:
                            yield Button(phase.label, id=f"phase-{phase.value}")
                    yield Static("FOCUS / READY", id="phase-status")
                    yield Digits("25:00", id="countdown")
                    yield Static("", id="progress")
                    yield Static("", id="timing-detail")
                    with Horizontal(id="controls"):
                        yield Button("Start", id="toggle")
                        yield Button("Reset", id="reset")
                        yield Button("Skip ›", id="skip")
                    yield Static("", id="cycle")
                with Horizontal(id="bottom-row"):
                    yield Static("", id="up-next")
                    yield Button("Settings", id="settings")
                yield Static("", id="notice", markup=False)
                yield Input(
                    placeholder="focus 25  ·  short 5  ·  long 15  ·  help",
                    id="command",
                    max_length=100,
                )
        yield Footer()

    def on_mount(self) -> None:
        self.theme = "textual-dark"
        self.query_one("#command").display = False
        self.set_class(self.size.height < 32, "compact")
        self.set_class(self.size.width < 66, "narrow")
        if self.start_immediately:
            self.timer.start()
        self.set_interval(0.1, self.tick)
        self.render_timer()
        self.query_one("#toggle", Button).focus()

    def on_resize(self) -> None:
        self.set_class(self.size.height < 32, "compact")
        self.set_class(self.size.width < 66, "narrow")

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        # Let inputs receive spaces and shortcuts as ordinary text.
        if isinstance(self.focused, Input) and action not in {"leave_command", "quit"}:
            return False
        if isinstance(self.screen, SettingsScreen) and action != "quit":
            return False
        return True

    def tick(self) -> None:
        if self.timer.tick():
            self.bell()
            self.set_notice(
                "Break finished. Ready for another focus session?"
                if self.timer.phase == Phase.FOCUS
                else "Focus complete. Your break has started."
            )
        self.render_timer()

    def render_timer(self) -> None:
        # Query the base screen so countdowns keep running behind settings.
        root = self.screen_stack[0]
        for phase in Phase:
            self.set_class(self.timer.phase == phase, phase.value)
            root.query_one(f"#phase-{phase.value}", Button).set_class(
                self.timer.phase == phase, "selected"
            )
        state = (
            "RUNNING"
            if self.timer.running
            else ("READY" if self.timer.remaining == self.timer.total else "PAUSED")
        )
        root.query_one("#phase-status", Static).update(
            f"{self.timer.phase.label.upper()} / {state}"
        )
        root.query_one("#countdown", Digits).update(format_time(self.timer.remaining))
        elapsed = self.timer.total - self.timer.remaining
        width = max(12, min(44, self.size.width - 16))
        filled = min(width, int(elapsed / self.timer.total * width))
        root.query_one("#progress", Static).update(
            "━" * filled + "[dim]" + "─" * (width - filled) + "[/dim]"
        )
        root.query_one("#timing-detail", Static).update(
            f"{format_time(int(elapsed))} elapsed  /  "
            f"{format_time(self.timer.total)} total"
        )
        root.query_one("#toggle", Button).label = (
            "Pause"
            if self.timer.running
            else ("Start" if self.timer.remaining == self.timer.total else "Resume")
        )
        dots = " ".join(
            "●" if index < self.timer.completed % 4 else "○" for index in range(4)
        )
        root.query_one("#cycle", Static).update(
            f"{dots}   {self.timer.completed} completed"
        )
        following = self.timer.next_phase()
        root.query_one("#up-next", Static).update(
            f"Up next  {following.label} · "
            f"{format_time(self.timer.durations.for_phase(following))}"
        )

    def set_notice(self, message: str) -> None:
        self.screen_stack[0].query_one("#notice", Static).update(message)

    def action_toggle(self) -> None:
        self.tick()
        if self.timer.running:
            self.timer.pause()
        else:
            self.timer.start()
        self.set_notice("")
        self.render_timer()

    def action_reset(self) -> None:
        self.timer.reset()
        self.set_notice("Timer reset. Press Start when you're ready.")
        self.render_timer()

    def action_skip(self) -> None:
        self.timer.skip()
        self.set_notice("Skipped. Press Start when you're ready.")
        self.render_timer()

    def action_phase(self, phase: str) -> None:
        if self.timer.phase != Phase(phase):
            self.timer.select(Phase(phase))
            self.set_notice("")
            self.render_timer()

    def action_settings(self) -> None:
        self.push_screen(SettingsScreen(self.timer.durations), self.apply_settings)

    def apply_settings(self, durations: Durations | None) -> None:
        if durations is None:
            return
        current_changed = durations.for_phase(self.timer.phase) != self.timer.total
        self.timer.durations = durations
        if current_changed:
            self.timer.reset()
        self.set_notice(
            "Times updated. Current timer reset."
            if current_changed
            else "Times updated."
        )
        self.render_timer()

    def action_command(self) -> None:
        field = self.query_one("#command", Input)
        field.display = True
        field.focus()
        field.scroll_visible()

    def action_leave_command(self) -> None:
        field = self.query_one("#command", Input)
        field.value = ""
        field.display = False
        self.query_one("#toggle", Button).focus()

    @on(Input.Submitted, "#command")
    def submit_command(self, event: Input.Submitted) -> None:
        parts = event.value.strip().lower().lstrip(":").split()
        if not parts:
            self.action_leave_command()
            return
        name, *args = parts
        try:
            if name in {phase.value for phase in Phase}:
                if len(args) != 1:
                    raise ValueError(f"Use: {name} 25m")
                seconds = parse_duration(args[0])
                durations = Durations(**vars(self.timer.durations))
                setattr(durations, name, seconds)
                self.apply_settings(durations)
            elif not args and name in {"start", "pause", "reset", "skip"}:
                if name in {"start", "pause"}:
                    self.tick()
                    getattr(self.timer, name)()
                    self.set_notice("")
                    self.render_timer()
                else:
                    getattr(self, f"action_{name}")()
            elif name == "help" and not args:
                self.set_notice(
                    "focus 25m · short 5m · long 15m · start · pause · reset · skip"
                )
            else:
                raise ValueError("Unknown command. Type help for available commands.")
        except ValueError as error:
            self.set_notice(str(error))
            return
        self.action_leave_command()

    @on(Button.Pressed)
    def button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id.startswith("phase-"):
            self.action_phase(button_id.removeprefix("phase-"))
        elif button_id in {"toggle", "reset", "skip", "settings"}:
            getattr(self, f"action_{button_id}")()


if __name__ == "__main__":
    PomodoroApp().run()
