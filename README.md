# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

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


## System Design
# 3 Core actions
1. Add a task
2. Add a pet
3. Generate a daily schedule

# Building blocks
Owner
    Attributes:

    name: str
    available_minutes: int
    preferences: list[str] — e.g. ["morning walks only", "no tasks after 8pm"]
    pets: list[Pet]
    Methods:

    add_pet(pet: Pet) -> None
    remove_pet(pet_name: str) -> None
    get_pets() -> list[Pet]
    set_available_time(minutes: int) -> None
    
Pet
    Attributes:

    name: str
    species: str — "dog", "cat", "other"
    age: int
    special_needs: list[str] — e.g. ["diabetic", "senior"]
    tasks: list[Task]
    Methods:

    add_task(task: Task) -> None
    remove_task(task_title: str) -> None
    get_tasks() -> list[Task]
    get_high_priority_tasks() -> list[Task]

Task
    Attributes:

    title: str
    duration_minutes: int
    priority: str — "low", "medium", "high"
    task_type: str — "walk", "feeding", "meds", "grooming", "enrichment"
    notes: str
    Methods:

    get_priority_score() -> int — maps "high"→3, "medium"→2, "low"→1 for sorting
    is_feasible(available_minutes: int) -> bool — returns duration_minutes <= available_minutes
    to_dict() -> dict — returns all attributes as a dictionary for display

Schedule
    Attributes:

    date: str
    owner: Owner
    pet: Pet
    entries: list[dict] — each dict: {task, start_time, end_time, reason}
    skipped_tasks: list[dict] — each dict: {task, reason} for tasks that didn't fit
    Methods:

    generate() -> None — main entry point; orchestrates filtering, sorting, and time assignment
    _filter_feasible(tasks: list[Task]) -> list[Task] — removes tasks that exceed available time
    _sort_by_priority(tasks: list[Task]) -> list[Task] — sorts using get_priority_score()
    _assign_times(tasks: list[Task]) -> list[dict] — walks through tasks, assigns start/end times, builds entries
    get_total_duration() -> int — sums duration of all scheduled entries
    get_explanation() -> str — returns a human-readable string explaining each scheduling decision
    display() -> list[dict] — returns entries formatted for st.table()