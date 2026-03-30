# PawPal+ (Module 2 Project)

**PawPal+** is a Streamlit app that helps a busy pet owner plan and schedule daily care tasks for their pets — balancing priorities, time constraints, and personal preferences automatically.

---

## 📸 Demo

<a href='https://postimg.cc/SYxGLB2m' target='_blank'><img src='https://i.postimg.cc/SYxGLB2m/pawpal-screenshot.png' border='0' alt='pawpal-screenshot'></a>

<a href="/course_images/ai110/pawpal_screenshot.png" target="_blank"><img src='/course_images/ai110/pawpal_screenshot.png' title='PawPal App' width='' alt='PawPal App' class='center-block' /></a>

---

## Features

### Owner & Pet Management

- **Owner profile** — store name, daily time budget (in minutes), and scheduling preferences
- **Multi-pet support** — add multiple pets with species, age, and special needs (e.g., "senior", "diabetic")
- **Duplicate guard** — raises an error if you try to add a pet or task with a name that already exists (case-insensitive)

### Task Management

- **Flexible task creation** — each task has a title, duration, priority (high / medium / low), type (walk, feeding, meds, grooming, enrichment), and optional notes
- **Completion tracking** — mark tasks pending or complete; completed tasks are automatically skipped at schedule generation time
- **Recurring tasks** — tasks can repeat `once`, `daily`, or `weekly`; `get_next_occurrence()` returns a fresh copy of the task with the date advanced by 1 or 7 days, preserving all attributes

### Scheduling Algorithms

- **Priority-based sorting** — `_sort_by_priority()` converts priority strings to numeric scores (high → 3, medium → 2, low → 1) and sorts tasks in descending order so the most important tasks are scheduled first
- **Medication bonus** — medication tasks receive a +1 score bonus so they always outrank same-priority non-medical tasks, ensuring meds are never bumped from the schedule
- **Greedy time assignment** — `_assign_times()` walks through the sorted task list, greedily assigning a start and end time (beginning at 08:00 AM) while tracking remaining minutes; any task that no longer fits is moved to `skipped_tasks` with an explanatory reason
- **Feasibility filtering** — `_filter_feasible()` removes tasks whose duration alone exceeds the owner's total time budget before scheduling begins

### Conflict Detection

- **Cross-pet conflict warnings** — the static `find_conflicts(schedules)` method compares every pair of entries across multiple pets and flags any overlapping time intervals (e.g., two pets both needing a walk at 09:00–09:30)
- **Overlap algorithm** — uses zero-padded HH:MM strings with lexicographic comparison to detect whether two time intervals intersect; a pet's own sequential tasks are never flagged as conflicts

### Owner Preference Constraints

- **Cutoff-hour enforcement** — regex-based parsing of free-text preferences like "no tasks after 8pm" or "no tasks after 7:30pm" converts 12-hour times to 24-hour format and blocks any task that would run past the cutoff
- **Morning walks only** — the preference "morning walks only" restricts all walk-type tasks to finish before noon; afternoon walk attempts are moved to `skipped_tasks`
- **Most-restrictive rule** — if multiple conflicting cutoff preferences exist, the earliest cutoff wins

### Sorting & Filtering

- **Sort by time** — `sort_by_time()` returns schedule entries in ascending chronological order (works because times are zero-padded HH:MM strings)
- **Filter by status** — `filter_by_status(status)` returns only pending or only completed tasks for targeted display
- **High-priority extraction** — `get_high_priority_tasks()` returns a pet's high-priority tasks so the UI can surface warnings

### Explanation & Display

- **Human-readable reasoning** — `get_explanation()` produces a narrative summary of every scheduling decision: why each task was included or skipped, the meds bonus, special needs, and total time used vs. available
- **Streamlit-ready output** — `display()` returns a flat list of dictionaries (Time, Task, Type, Priority, Duration, Notes) that renders directly in `st.table()`

---

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

---

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

---

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

---

## System Design

### 3 Core actions

1. Add a task
2. Add a pet
3. Generate a daily schedule

### Building blocks

**Owner**

Attributes:

- `name: str`
- `available_minutes: int`
- `preferences: list[str]` — e.g. ["morning walks only", "no tasks after 8pm"]
- `pets: list[Pet]`

Methods:

- `add_pet(pet: Pet) -> None`
- `remove_pet(pet_name: str) -> None`
- `get_pets() -> list[Pet]`
- `set_available_time(minutes: int) -> None`

---

**Pet**

Attributes:

- `name: str`
- `species: str` — "dog", "cat", "other"
- `age: int`
- `special_needs: list[str]` — e.g. ["diabetic", "senior"]
- `tasks: list[Task]`

Methods:

- `add_task(task: Task) -> None`
- `remove_task(task_title: str) -> None`
- `get_tasks() -> list[Task]`
- `get_high_priority_tasks() -> list[Task]`

---

**Task**

Attributes:

- `title: str`
- `duration_minutes: int`
- `priority: str` — "low", "medium", "high"
- `task_type: str` — "walk", "feeding", "meds", "grooming", "enrichment"
- `notes: str`

Methods:

- `get_priority_score() -> int` — maps "high"→3, "medium"→2, "low"→1 for sorting
- `is_feasible(available_minutes: int) -> bool` — returns `duration_minutes <= available_minutes`
- `to_dict() -> dict` — returns all attributes as a dictionary for display

---

**Schedule**

Attributes:

- `date: str`
- `owner: Owner`
- `pet: Pet`
- `entries: list[dict]` — each dict: `{task, start_time, end_time, reason}`
- `skipped_tasks: list[dict]` — each dict: `{task, reason}` for tasks that didn't fit

Methods:

- `generate() -> None` — main entry point; orchestrates filtering, sorting, and time assignment
- `_filter_feasible(tasks: list[Task]) -> list[Task]` — removes tasks that exceed available time
- `_sort_by_priority(tasks: list[Task]) -> list[Task]` — sorts using `get_priority_score()`
- `_assign_times(tasks: list[Task]) -> list[dict]` — walks through tasks, assigns start/end times, builds entries
- `get_total_duration() -> int` — sums duration of all scheduled entries
- `get_explanation() -> str` — returns a human-readable string explaining each scheduling decision
- `display() -> list[dict]` — returns entries formatted for `st.table()`

---

## Testing PawPal+

### Running

```bash
python -m pytest
```

### Test coverage

- **Task basics** — creating tasks, marking complete/incomplete, priority scores, feasibility checks, and serialization via `to_dict`
- **Task validation** — rejects empty titles, zero/negative durations, and invalid priority strings at construction time
- **Recurrence logic** — `get_next_occurrence` returns `None` for one-off tasks, advances by 1 day for daily, 7 days for weekly, and copies all attributes to the new task
- **Pet management** — adding/removing tasks, blocking duplicate task titles (case-insensitive), retrieving high-priority tasks, and the edge case of a pet with no tasks
- **Owner management** — adding/removing pets, blocking duplicate pet names, and validating the time budget
- **Sorting correctness** — `sort_by_time()` always returns entries in ascending chronological order; high-priority tasks are placed before low-priority ones; meds get a bonus that elevates them above same-priority non-medical tasks
- **Conflict detection** — `find_conflicts` flags overlapping time slots across different pets, returns nothing when slots don't overlap, never flags a single pet's own sequential tasks as conflicts, and handles an empty schedule list safely
- **Skipping logic** — already-completed tasks and tasks that exceed the owner's time budget are both moved to `skipped_tasks` with explanatory reasons
- **Owner preferences** — a cutoff-hour preference correctly blocks tasks that would run past the allowed window
- **Display/explanation** — `display()` returns all required keys; `get_explanation()` produces a meaningful message even when there are no tasks

**Confidence score: 5**

# Summarization

- Ai can be a very powerful companion if used correctly. If used incorrectly, it can actually amkes you more slow and have a sloppy product.
