from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
import re


PRIORITY_MAP = {"high": 3, "medium": 2, "low": 1}
DEFAULT_START_HOUR = 8  # Schedule begins at 08:00 by default


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str        # "low", "medium", "high"
    task_type: str       # "walk", "feeding", "meds", "grooming", "enrichment"
    notes: str = ""
    status: str = "pending"        # "pending" or "completed"
    frequency: str = "once"        # "once", "daily", "weekly"
    due_date: str = ""             # ISO date string, e.g. "2025-03-29"

    def __post_init__(self):
        """Validate fields immediately after construction."""
        if not self.title.strip():
            raise ValueError("Task title cannot be empty.")
        if self.duration_minutes <= 0:
            raise ValueError(
                f"duration_minutes must be greater than 0, got {self.duration_minutes}."
            )
        if self.priority.lower() not in PRIORITY_MAP:
            raise ValueError(
                f"Invalid priority '{self.priority}'. Must be one of: {list(PRIORITY_MAP)}."
            )

    def mark_complete(self) -> None:
        """Marks the task as completed. Idempotent — safe to call more than once."""
        self.status = "completed"

    def mark_incomplete(self) -> None:
        """Resets the task back to pending (e.g. for recurring tasks)."""
        self.status = "pending"

    def is_completed(self) -> bool:
        """Returns True if the task has already been completed."""
        return self.status == "completed"

    def get_priority_score(self) -> int:
        """Maps priority string to a numeric score (high=3, medium=2, low=1, unknown=0)."""
        return PRIORITY_MAP.get(self.priority.lower(), 0)

    def is_feasible(self, available_minutes: int) -> bool:
        """Returns True if the task duration fits within the given available minutes."""
        return self.duration_minutes <= available_minutes

    def get_next_occurrence(self, from_date: str) -> "Task | None":
        """
        For recurring tasks, returns a new Task due on the next occurrence.
        - "daily"  → from_date + 1 day
        - "weekly" → from_date + 7 days
        Returns None for one-off tasks (frequency == "once").
        """
        if self.frequency == "once":
            return None
        base = date.fromisoformat(from_date)
        delta = timedelta(days=1) if self.frequency == "daily" else timedelta(weeks=1)
        next_due = (base + delta).isoformat()
        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            task_type=self.task_type,
            notes=self.notes,
            frequency=self.frequency,
            due_date=next_due,
        )

    def to_dict(self) -> dict:
        """Returns all attributes as a flat dictionary for display or serialisation."""
        return {
            "title": self.title,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "task_type": self.task_type,
            "notes": self.notes,
            "status": self.status,
            "frequency": self.frequency,
            "due_date": self.due_date,
        }


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    species: str         # "dog", "cat", "other"
    age: int
    special_needs: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)

    def __post_init__(self):
        """Validate fields immediately after construction."""
        if not self.name.strip():
            raise ValueError("Pet name cannot be empty.")
        if self.age < 0:
            raise ValueError(f"Pet age cannot be negative, got {self.age}.")

    def add_task(self, task: Task) -> None:
        """
        Adds a task to the pet's list.
        Raises ValueError on duplicate title (case-insensitive).
        """
        for existing in self.tasks:
            if existing.title.lower() == task.title.lower():
                raise ValueError(
                    f"Task '{task.title}' already exists for {self.name}. "
                    "Remove it first or use a different title."
                )
        self.tasks.append(task)

    def remove_task(self, task_title: str) -> None:
        """
        Removes a task by title (case-insensitive).
        Raises ValueError if the task is not found.
        """
        original_count = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.title.lower() != task_title.lower()]
        if len(self.tasks) == original_count:
            raise ValueError(f"Task '{task_title}' not found for {self.name}.")

    def get_tasks(self) -> list[Task]:
        """Returns a shallow copy of the task list."""
        return list(self.tasks)

    def get_high_priority_tasks(self) -> list[Task]:
        """Returns tasks with priority set to 'high'."""
        return [t for t in self.tasks if t.priority.lower() == "high"]


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    def __init__(
        self,
        name: str,
        available_minutes: int,
        preferences: list[str] = None,
    ):
        if not name.strip():
            raise ValueError("Owner name cannot be empty.")
        if available_minutes < 0:
            raise ValueError("available_minutes cannot be negative.")
        self.name: str = name
        self.available_minutes: int = available_minutes
        self.preferences: list[str] = preferences if preferences is not None else []
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """
        Adds a pet to the owner's list.
        Raises ValueError on duplicate pet name (case-insensitive).
        """
        for existing in self.pets:
            if existing.name.lower() == pet.name.lower():
                raise ValueError(
                    f"A pet named '{pet.name}' already exists. "
                    "Each pet must have a unique name."
                )
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> None:
        """
        Removes a pet by name (case-insensitive).
        Raises ValueError if the pet is not found.
        """
        original_count = len(self.pets)
        self.pets = [p for p in self.pets if p.name.lower() != pet_name.lower()]
        if len(self.pets) == original_count:
            raise ValueError(f"Pet '{pet_name}' not found.")

    def get_pets(self) -> list[Pet]:
        """Returns a shallow copy of the pet list."""
        return list(self.pets)

    def set_available_time(self, minutes: int) -> None:
        """Updates today's available time budget. Must be non-negative."""
        if minutes < 0:
            raise ValueError("Available time cannot be negative.")
        self.available_minutes = minutes


# ---------------------------------------------------------------------------
# Schedule  (the "brain" / scheduler)
# ---------------------------------------------------------------------------

class Schedule:
    def __init__(self, date: str, owner: Owner, pet: Pet):
        """
        Args:
            date:  ISO date string, e.g. "2024-05-01"
            owner: Owner instance (supplies available_minutes and preferences)
            pet:   Pet instance whose tasks will be scheduled
        """
        self.date: str = date
        self.owner: Owner = owner
        self.pet: Pet = pet
        self.entries: list[dict] = []        # {task, start_time, end_time, reason}
        self.skipped_tasks: list[dict] = []  # {task, reason}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self) -> None:
        """
        Main entry point. Clears any previous results, then:
          1. Filters out individually infeasible tasks.
          2. Sorts remaining tasks by priority (with meds elevated).
          3. Greedily assigns start/end times while respecting preferences.
        """
        self.entries = []
        self.skipped_tasks = []

        all_tasks = self.pet.get_tasks()
        if not all_tasks:
            return

        # Skip tasks already marked complete — no need to re-schedule them.
        pending, already_done = [], []
        for task in all_tasks:
            (already_done if task.is_completed() else pending).append(task)

        for task in already_done:
            self.skipped_tasks.append({
                "task": task,
                "reason": "Already completed — no action needed today.",
            })

        feasible, too_long = self._filter_feasible(pending)

        # Tasks that are longer than the entire day budget are permanently skipped.
        for task in too_long:
            self.skipped_tasks.append({
                "task": task,
                "reason": (
                    f"Task duration ({task.duration_minutes} min) exceeds the total "
                    f"available time ({self.owner.available_minutes} min)."
                ),
            })

        sorted_tasks = self._sort_by_priority(feasible)
        self.entries = self._assign_times(sorted_tasks)

    def get_total_duration(self) -> int:
        """Returns the sum of durations for all scheduled entries (in minutes)."""
        return sum(entry["task"].duration_minutes for entry in self.entries)

    def get_explanation(self) -> str:
        """
        Returns a human-readable narrative of every scheduling decision:
        which tasks were scheduled and why, and which were skipped and why.
        """
        if not self.entries and not self.skipped_tasks:
            return f"No tasks available to schedule for {self.pet.name} on {self.date}."

        lines = [
            f"Schedule for {self.pet.name} on {self.date}",
            f"Owner: {self.owner.name} | Available time: {self.owner.available_minutes} min\n",
        ]

        if self.entries:
            lines.append("Scheduled tasks:")
            for entry in self.entries:
                t = entry["task"]
                lines.append(
                    f"  {entry['start_time']} – {entry['end_time']}  "
                    f"[{t.priority.upper()}] {t.title} ({t.duration_minutes} min)\n"
                    f"    → {entry['reason']}"
                )

        if self.skipped_tasks:
            lines.append("\nSkipped tasks:")
            for skipped in self.skipped_tasks:
                lines.append(f"  ✗ {skipped['task'].title} — {skipped['reason']}")

        lines.append(
            f"\nTotal scheduled: {self.get_total_duration()} / {self.owner.available_minutes} min"
        )
        return "\n".join(lines)

    def sort_by_time(self) -> list[dict]:
        """
        Returns scheduled entries sorted chronologically by start_time.
        Uses a lambda key on the HH:MM string — lexicographic order works
        correctly for zero-padded 24-hour times.
        """
        return sorted(self.entries, key=lambda entry: entry["start_time"])

    def filter_by_status(self, status: str) -> list[Task]:
        """
        Returns this pet's tasks filtered by completion status.
        Args:
            status: "pending" or "completed"
        """
        return [t for t in self.pet.tasks if t.status == status]

    @staticmethod
    def find_conflicts(schedules: "list[Schedule]") -> list[str]:
        """
        Detects time-slot overlaps across multiple pet schedules.
        Two entries conflict when one starts before the other ends
        (standard interval-overlap test).  Returns warning strings —
        never raises, so callers can decide how to handle conflicts.
        """
        warnings: list[str] = []
        # Flatten: [(pet_name, entry), ...]
        all_entries = [
            (sched.pet.name, entry)
            for sched in schedules
            for entry in sched.entries
        ]
        for i, (pet_a, ea) in enumerate(all_entries):
            for pet_b, eb in all_entries[i + 1:]:
                if pet_a == pet_b:
                    continue  # same pet — sequential, never self-conflicts
                # HH:MM strings are lexicographically comparable
                if ea["start_time"] < eb["end_time"] and eb["start_time"] < ea["end_time"]:
                    warnings.append(
                        f"CONFLICT: {pet_a}'s '{ea['task'].title}' "
                        f"({ea['start_time']}–{ea['end_time']}) overlaps with "
                        f"{pet_b}'s '{eb['task'].title}' "
                        f"({eb['start_time']}–{eb['end_time']})"
                    )
        return warnings

    def display(self) -> list[dict]:
        """
        Returns entries as a list of flat dicts ready for st.table() or st.dataframe().
        """
        return [
            {
                "Time": f"{entry['start_time']} – {entry['end_time']}",
                "Task": entry["task"].title,
                "Type": entry["task"].task_type,
                "Priority": entry["task"].priority,
                "Duration (min)": entry["task"].duration_minutes,
                "Notes": entry["task"].notes,
            }
            for entry in self.entries
        ]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _filter_feasible(
        self, tasks: list[Task]
    ) -> tuple[list[Task], list[Task]]:
        """
        Splits tasks into:
          - feasible:  duration <= owner.available_minutes  (can possibly be scheduled)
          - too_long:  duration >  owner.available_minutes  (can never fit today)
        """
        feasible, too_long = [], []
        for task in tasks:
            if task.is_feasible(self.owner.available_minutes):
                feasible.append(task)
            else:
                too_long.append(task)
        return feasible, too_long

    def _sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """
        Sorts tasks highest-priority first.

        Tie-breaking rules (in order):
          1. "meds" task_type gets a +1 safety bonus so medication is never bumped
             by a same-priority non-medical task.
          2. Among tasks still tied, shorter duration comes first (fit more tasks in).
        """
        def sort_key(task: Task):
            type_bonus = 1 if task.task_type.lower() == "meds" else 0
            effective_score = task.get_priority_score() + type_bonus
            # Negate duration so shorter tasks rank higher on a reverse sort
            return (effective_score, -task.duration_minutes)

        return sorted(tasks, key=sort_key, reverse=True)

    def _parse_preferences(self) -> tuple:
        """
        Parses owner.preferences strings into structured constraints.

        Supported patterns (case-insensitive):
          - "no tasks after Xpm" / "no tasks after X:XXpm"
            → no task may start at or after that hour
          - "morning walks only"
            → walk-type tasks must finish before 12:00

        Returns:
            cutoff_hour (int | None): 24-h hour after which tasks are blocked
            morning_walks_only (bool): restrict walks to before noon
        """
        cutoff_hour = None
        morning_walks_only = False

        for pref in self.owner.preferences:
            pref_lower = pref.lower()

            # Match "no tasks after X(pm|am)" optionally with minutes
            match = re.search(
                r'no tasks after (\d+)(?::\d+)?\s*(am|pm)', pref_lower
            )
            if match:
                hour = int(match.group(1))
                period = match.group(2)
                if period == "pm" and hour != 12:
                    hour += 12
                elif period == "am" and hour == 12:
                    hour = 0
                # Keep the earliest (most restrictive) cutoff if multiple preferences clash
                if cutoff_hour is None or hour < cutoff_hour:
                    cutoff_hour = hour

            if "morning" in pref_lower and "walk" in pref_lower:
                morning_walks_only = True

        return cutoff_hour, morning_walks_only

    def _assign_times(self, tasks: list[Task]) -> list[dict]:
        """
        Greedy assignment loop. Walks through priority-sorted tasks and schedules
        each one if it fits within the remaining time budget and satisfies all
        preference constraints. Tasks that cannot be scheduled are appended to
        self.skipped_tasks with an explanation.

        Returns the list of scheduled entry dicts.
        """
        cutoff_hour, morning_walks_only = self._parse_preferences()

        current_dt = datetime.strptime(
            f"{self.date} {DEFAULT_START_HOUR:02d}:00", "%Y-%m-%d %H:%M"
        )
        remaining_minutes = self.owner.available_minutes
        entries = []

        for task in tasks:
            skip_reason = self._check_constraints(
                task, current_dt, remaining_minutes, cutoff_hour, morning_walks_only
            )

            if skip_reason:
                self.skipped_tasks.append({"task": task, "reason": skip_reason})
                continue

            end_dt = current_dt + timedelta(minutes=task.duration_minutes)
            entries.append({
                "task": task,
                "start_time": current_dt.strftime("%H:%M"),
                "end_time": end_dt.strftime("%H:%M"),
                "reason": self._build_reason(task),
            })
            current_dt = end_dt
            remaining_minutes -= task.duration_minutes

        return entries

    def _check_constraints(
        self,
        task: Task,
        current_dt: datetime,
        remaining_minutes: int,
        cutoff_hour: int | None,
        morning_walks_only: bool,
    ) -> str | None:
        """
        Evaluates all scheduling constraints for a single task.
        Returns a skip-reason string if the task cannot be scheduled, else None.
        """
        end_dt = current_dt + timedelta(minutes=task.duration_minutes)

        # 1. Time budget
        if task.duration_minutes > remaining_minutes:
            return (
                f"Not enough time remaining ({remaining_minutes} min left, "
                f"needs {task.duration_minutes} min)."
            )

        # 2. Cutoff: task must not start at or after cutoff hour
        if cutoff_hour is not None and current_dt.hour >= cutoff_hour:
            return (
                f"Slot starts at {current_dt.strftime('%H:%M')}, which is at or after "
                f"the owner's cutoff of {cutoff_hour:02d}:00."
            )

        # 3. Cutoff: task must not end after cutoff hour (partial overlap is still a violation)
        if cutoff_hour is not None and (
            end_dt.hour > cutoff_hour
            or (end_dt.hour == cutoff_hour and end_dt.minute > 0)
        ):
            return (
                f"Would end at {end_dt.strftime('%H:%M')}, past the owner's "
                f"cutoff of {cutoff_hour:02d}:00."
            )

        # 4. Morning-walks-only preference
        if morning_walks_only and task.task_type.lower() == "walk":
            if current_dt.hour >= 12:
                return (
                    f"Owner preference 'morning walks only' — slot starts at "
                    f"{current_dt.strftime('%H:%M')}, which is after noon."
                )
            # Also ensure the walk finishes before noon
            if end_dt.hour >= 12 and end_dt.minute > 0:
                return (
                    f"Owner preference 'morning walks only' — walk would end at "
                    f"{end_dt.strftime('%H:%M')}, which crosses noon."
                )

        return None  # All constraints satisfied

    def _build_reason(self, task: Task) -> str:
        """
        Composes a short, plain-English explanation for why a task was scheduled.
        Mentions priority, any medical elevation, special needs, and notes.
        """
        parts = [f"Scheduled as {task.priority}-priority {task.task_type}."]

        if task.task_type.lower() == "meds":
            parts.append("Medication tasks are elevated to protect pet health.")

        if self.pet.special_needs:
            needs = ", ".join(self.pet.special_needs)
            parts.append(f"{self.pet.name} has special needs ({needs}).")

        if task.notes:
            parts.append(f"Note: {task.notes}")

        return " ".join(parts)
