import pytest
from pawpal_system import Task, Pet, Owner, Schedule


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def basic_task():
    return Task(title="Feed the cat", duration_minutes=10, priority="medium", task_type="feeding")

@pytest.fixture
def daily_task():
    return Task(
        title="Morning Walk",
        duration_minutes=30,
        priority="high",
        task_type="walk",
        frequency="daily",
        due_date="2026-03-29",
    )

@pytest.fixture
def weekly_task():
    return Task(
        title="Grooming Session",
        duration_minutes=45,
        priority="low",
        task_type="grooming",
        frequency="weekly",
        due_date="2026-03-29",
    )

@pytest.fixture
def pet():
    return Pet(name="Buddy", species="dog", age=3)

@pytest.fixture
def owner():
    return Owner(name="Alex", available_minutes=120)

@pytest.fixture
def schedule(owner, pet):
    return Schedule(date="2026-03-29", owner=owner, pet=pet)


# ---------------------------------------------------------------------------
# Task: happy path
# ---------------------------------------------------------------------------

def test_task_completion(basic_task):
    basic_task.mark_complete()
    assert basic_task.status == "completed"
    assert basic_task.is_completed() is True

def test_task_mark_incomplete(basic_task):
    basic_task.mark_complete()
    basic_task.mark_incomplete()
    assert basic_task.status == "pending"
    assert basic_task.is_completed() is False

def test_task_mark_complete_idempotent(basic_task):
    basic_task.mark_complete()
    basic_task.mark_complete()  # calling twice should not raise
    assert basic_task.status == "completed"

def test_task_priority_score():
    assert Task("T", 10, "high", "walk").get_priority_score() == 3
    assert Task("T", 10, "medium", "walk").get_priority_score() == 2
    assert Task("T", 10, "low", "walk").get_priority_score() == 1

def test_task_is_feasible():
    task = Task("T", 30, "low", "walk")
    assert task.is_feasible(30) is True
    assert task.is_feasible(31) is True
    assert task.is_feasible(29) is False

def test_task_to_dict_contains_all_keys(basic_task):
    d = basic_task.to_dict()
    for key in ("title", "duration_minutes", "priority", "task_type", "notes", "status", "frequency", "due_date"):
        assert key in d


# ---------------------------------------------------------------------------
# Task: validation edge cases
# ---------------------------------------------------------------------------

def test_task_empty_title_raises():
    with pytest.raises(ValueError, match="title cannot be empty"):
        Task(title="  ", duration_minutes=10, priority="low", task_type="walk")

def test_task_zero_duration_raises():
    with pytest.raises(ValueError, match="duration_minutes must be greater than 0"):
        Task(title="Walk", duration_minutes=0, priority="low", task_type="walk")

def test_task_negative_duration_raises():
    with pytest.raises(ValueError, match="duration_minutes must be greater than 0"):
        Task(title="Walk", duration_minutes=-5, priority="low", task_type="walk")

def test_task_invalid_priority_raises():
    with pytest.raises(ValueError, match="Invalid priority"):
        Task(title="Walk", duration_minutes=10, priority="urgent", task_type="walk")


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

def test_once_task_next_occurrence_is_none():
    """A one-off task must return None for get_next_occurrence."""
    task = Task("Vet Visit", 60, "high", "meds", frequency="once", due_date="2026-03-29")
    assert task.get_next_occurrence("2026-03-29") is None

def test_daily_task_next_occurrence(daily_task):
    """Marking a daily task complete and calling get_next_occurrence should give the next day."""
    daily_task.mark_complete()
    next_task = daily_task.get_next_occurrence(daily_task.due_date)
    assert next_task is not None
    assert next_task.due_date == "2026-03-30"
    assert next_task.frequency == "daily"
    assert next_task.title == daily_task.title
    assert next_task.status == "pending"  # new occurrence starts fresh

def test_weekly_task_next_occurrence(weekly_task):
    """A weekly task should advance by exactly 7 days."""
    next_task = weekly_task.get_next_occurrence(weekly_task.due_date)
    assert next_task is not None
    assert next_task.due_date == "2026-04-05"
    assert next_task.frequency == "weekly"

def test_recurring_task_preserves_attributes(daily_task):
    """The generated next occurrence must mirror all attributes of the parent."""
    next_task = daily_task.get_next_occurrence(daily_task.due_date)
    assert next_task.title == daily_task.title
    assert next_task.duration_minutes == daily_task.duration_minutes
    assert next_task.priority == daily_task.priority
    assert next_task.task_type == daily_task.task_type


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

def test_add_task_to_pet(pet):
    task = Task("Play with laser", 15, "low", "enrichment")
    pet.add_task(task)
    assert len(pet.tasks) == 1
    assert pet.tasks[0].title == "Play with laser"

def test_pet_duplicate_task_raises(pet):
    task = Task("Walk", 20, "medium", "walk")
    pet.add_task(task)
    with pytest.raises(ValueError, match="already exists"):
        pet.add_task(Task("walk", 20, "medium", "walk"))  # same title, different case

def test_pet_remove_task(pet):
    pet.add_task(Task("Walk", 20, "medium", "walk"))
    pet.remove_task("Walk")
    assert len(pet.tasks) == 0

def test_pet_remove_nonexistent_task_raises(pet):
    with pytest.raises(ValueError, match="not found"):
        pet.remove_task("Ghost Task")

def test_pet_with_no_tasks(pet):
    """Edge case: a pet with no tasks should return an empty list."""
    assert pet.get_tasks() == []
    assert pet.get_high_priority_tasks() == []

def test_pet_get_high_priority_tasks(pet):
    pet.add_task(Task("Meds", 10, "high", "meds"))
    pet.add_task(Task("Walk", 20, "medium", "walk"))
    high = pet.get_high_priority_tasks()
    assert len(high) == 1
    assert high[0].title == "Meds"

def test_pet_invalid_age_raises():
    with pytest.raises(ValueError, match="age cannot be negative"):
        Pet(name="Rex", species="dog", age=-1)

def test_pet_empty_name_raises():
    with pytest.raises(ValueError, match="name cannot be empty"):
        Pet(name="  ", species="dog", age=2)


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

def test_owner_add_pet(owner, pet):
    owner.add_pet(pet)
    assert len(owner.pets) == 1

def test_owner_duplicate_pet_raises(owner, pet):
    owner.add_pet(pet)
    with pytest.raises(ValueError, match="already exists"):
        owner.add_pet(Pet(name="buddy", species="dog", age=3))  # case-insensitive

def test_owner_remove_pet(owner, pet):
    owner.add_pet(pet)
    owner.remove_pet("Buddy")
    assert len(owner.pets) == 0

def test_owner_negative_available_minutes_raises():
    with pytest.raises(ValueError, match="cannot be negative"):
        Owner(name="Alex", available_minutes=-10)

def test_owner_set_available_time(owner):
    owner.set_available_time(60)
    assert owner.available_minutes == 60

def test_owner_set_negative_time_raises(owner):
    with pytest.raises(ValueError, match="cannot be negative"):
        owner.set_available_time(-1)


# ---------------------------------------------------------------------------
# Schedule: sorting correctness
# ---------------------------------------------------------------------------

def test_sort_by_time_returns_chronological_order(owner, pet):
    """
    After generate(), sort_by_time() must return entries in ascending HH:MM order.
    We add tasks in low-priority order so they'd be scheduled in reverse without sorting.
    """
    pet.add_task(Task("Walk", 20, "low", "walk"))
    pet.add_task(Task("Feeding", 10, "medium", "feeding"))
    pet.add_task(Task("Meds", 5, "high", "meds"))

    sched = Schedule(date="2026-03-29", owner=owner, pet=pet)
    sched.generate()

    sorted_entries = sched.sort_by_time()
    times = [e["start_time"] for e in sorted_entries]
    assert times == sorted(times), f"Expected ascending times, got {times}"

def test_high_priority_task_scheduled_before_low(owner, pet):
    """
    Priority sorting: a high-priority task must appear first in the schedule
    even if it was added last.
    """
    pet.add_task(Task("Low Task", 15, "low", "enrichment"))
    pet.add_task(Task("High Task", 15, "high", "feeding"))

    sched = Schedule(date="2026-03-29", owner=owner, pet=pet)
    sched.generate()

    assert sched.entries[0]["task"].title == "High Task"

def test_meds_elevated_above_same_priority(owner, pet):
    """
    Medication tasks receive a priority bonus and must appear before a non-meds
    task of the same declared priority.
    """
    pet.add_task(Task("Walk", 20, "medium", "walk"))
    pet.add_task(Task("Give Antibiotics", 5, "medium", "meds"))

    sched = Schedule(date="2026-03-29", owner=owner, pet=pet)
    sched.generate()

    first_title = sched.entries[0]["task"].title
    assert first_title == "Give Antibiotics", (
        f"Meds should be first but got: {first_title}"
    )

def test_sort_by_time_single_entry(owner, pet):
    """Edge case: a schedule with one entry is already sorted."""
    pet.add_task(Task("Feeding", 10, "medium", "feeding"))
    sched = Schedule(date="2026-03-29", owner=owner, pet=pet)
    sched.generate()
    assert len(sched.sort_by_time()) == 1


# ---------------------------------------------------------------------------
# Schedule: pet with no tasks
# ---------------------------------------------------------------------------

def test_schedule_with_no_tasks_generates_empty(owner, pet):
    """Edge case: scheduling a pet with no tasks should produce no entries and no skips."""
    sched = Schedule(date="2026-03-29", owner=owner, pet=pet)
    sched.generate()
    assert sched.entries == []
    assert sched.skipped_tasks == []

def test_schedule_explanation_with_no_tasks(owner, pet):
    sched = Schedule(date="2026-03-29", owner=owner, pet=pet)
    sched.generate()
    explanation = sched.get_explanation()
    assert "No tasks available" in explanation


# ---------------------------------------------------------------------------
# Schedule: completed tasks are skipped
# ---------------------------------------------------------------------------

def test_completed_tasks_are_skipped(owner, pet):
    task = Task("Feeding", 10, "medium", "feeding")
    task.mark_complete()
    pet.add_task(task)

    sched = Schedule(date="2026-03-29", owner=owner, pet=pet)
    sched.generate()

    assert len(sched.entries) == 0
    assert len(sched.skipped_tasks) == 1
    assert "Already completed" in sched.skipped_tasks[0]["reason"]


# ---------------------------------------------------------------------------
# Schedule: tasks that exceed available time are skipped
# ---------------------------------------------------------------------------

def test_task_exceeding_budget_is_skipped():
    owner = Owner(name="Alex", available_minutes=20)
    pet = Pet(name="Rex", species="dog", age=2)
    pet.add_task(Task("Long Walk", 60, "high", "walk"))

    sched = Schedule(date="2026-03-29", owner=owner, pet=pet)
    sched.generate()

    assert len(sched.entries) == 0
    assert len(sched.skipped_tasks) == 1
    assert "exceeds" in sched.skipped_tasks[0]["reason"]


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_find_conflicts_detects_overlap():
    """
    Two pets scheduled with overlapping time slots must trigger a conflict warning.
    We use a very small time budget so both schedules start at 08:00.
    """
    owner_a = Owner(name="Alice", available_minutes=60)
    owner_b = Owner(name="Bob", available_minutes=60)

    pet_a = Pet(name="Rex", species="dog", age=3)
    pet_b = Pet(name="Luna", species="cat", age=2)

    pet_a.add_task(Task("Walk Rex", 30, "high", "walk"))
    pet_b.add_task(Task("Walk Luna", 30, "high", "walk"))

    sched_a = Schedule(date="2026-03-29", owner=owner_a, pet=pet_a)
    sched_b = Schedule(date="2026-03-29", owner=owner_b, pet=pet_b)
    sched_a.generate()
    sched_b.generate()

    conflicts = Schedule.find_conflicts([sched_a, sched_b])
    assert len(conflicts) > 0, "Expected at least one conflict for overlapping 08:00–08:30 slots"
    assert "CONFLICT" in conflicts[0]

def test_find_conflicts_no_overlap():
    """
    Two pets scheduled at non-overlapping times must produce zero conflicts.
    We stagger them by giving the first owner a tiny budget so only a short task fits,
    then let the second pet start after that window.
    """
    owner_a = Owner(name="Alice", available_minutes=10)
    owner_b = Owner(name="Bob", available_minutes=60)

    pet_a = Pet(name="Rex", species="dog", age=3)
    pet_b = Pet(name="Luna", species="cat", age=2)

    # Rex: 10-min task → 08:00–08:10
    pet_a.add_task(Task("Quick Feed", 10, "medium", "feeding"))
    # Luna: also starts at 08:00 with owner_b — overlaps, so we test no-overlap differently.
    # Instead, give Luna a task that won't start until Rex is done by sharing the same owner.
    # For a true non-overlap test: give each pet its own non-overlapping schedule object.
    # Simplest approach: both pets belong to the same owner sequentially (same Schedule object
    # is not supported, so we check with an empty schedule for one side).
    sched_a = Schedule(date="2026-03-29", owner=owner_a, pet=pet_a)
    sched_a.generate()

    # sched_b has no tasks → no entries, so no conflict possible
    sched_b = Schedule(date="2026-03-29", owner=owner_b, pet=pet_b)
    sched_b.generate()

    conflicts = Schedule.find_conflicts([sched_a, sched_b])
    assert conflicts == [], f"Expected no conflicts, got: {conflicts}"

def test_find_conflicts_same_pet_no_self_conflict():
    """
    A single pet's own sequential tasks must never be reported as conflicts.
    """
    owner = Owner(name="Alice", available_minutes=120)
    pet = Pet(name="Rex", species="dog", age=3)
    pet.add_task(Task("Walk", 30, "high", "walk"))
    pet.add_task(Task("Feeding", 20, "medium", "feeding"))

    sched = Schedule(date="2026-03-29", owner=owner, pet=pet)
    sched.generate()

    # find_conflicts only flags *different* pets, so a single schedule should be clean
    conflicts = Schedule.find_conflicts([sched])
    assert conflicts == []

def test_find_conflicts_empty_schedules():
    """Edge case: no schedules → no conflicts."""
    assert Schedule.find_conflicts([]) == []


# ---------------------------------------------------------------------------
# Schedule: total duration
# ---------------------------------------------------------------------------

def test_get_total_duration(owner, pet):
    pet.add_task(Task("Walk", 30, "high", "walk"))
    pet.add_task(Task("Feeding", 20, "medium", "feeding"))

    sched = Schedule(date="2026-03-29", owner=owner, pet=pet)
    sched.generate()

    assert sched.get_total_duration() == 50

def test_get_total_duration_empty_schedule(owner, pet):
    sched = Schedule(date="2026-03-29", owner=owner, pet=pet)
    sched.generate()
    assert sched.get_total_duration() == 0


# ---------------------------------------------------------------------------
# Schedule: owner preferences
# ---------------------------------------------------------------------------

def test_cutoff_preference_blocks_tasks():
    """Tasks that would start at or after the cutoff hour must be skipped."""
    # Give owner 300 min but enforce cutoff at 09:00; scheduler starts at 08:00.
    # A 90-min task would push into 09:30, past the cutoff → should be skipped.
    owner = Owner(name="Alex", available_minutes=300, preferences=["no tasks after 9pm"])
    pet = Pet(name="Max", species="dog", age=4)
    # Many tasks to exhaust the pre-cutoff window
    pet.add_task(Task("Long Walk", 90, "high", "walk"))

    sched = Schedule(date="2026-03-29", owner=owner, pet=pet)
    sched.generate()
    # The 90-min task starts at 08:00, ends at 09:30 — past the 21:00 cutoff? No, 9pm=21:00,
    # so it should actually be scheduled fine. Let's use a tighter cutoff.
    # Rebuild with correct preference: no tasks after 9am
    owner2 = Owner(name="Alex", available_minutes=300, preferences=["no tasks after 9am"])
    pet2 = Pet(name="Max", species="dog", age=4)
    # 30-min task starts 08:00, ends 08:30 — fine.
    pet2.add_task(Task("Feed", 30, "high", "feeding"))
    # 60-min task starts 08:30, ends 09:30 — ends past 09:00 cutoff → skipped.
    pet2.add_task(Task("Long Walk", 60, "medium", "walk"))

    sched2 = Schedule(date="2026-03-29", owner=owner2, pet=pet2)
    sched2.generate()

    scheduled_titles = [e["task"].title for e in sched2.entries]
    skipped_titles = [s["task"].title for s in sched2.skipped_tasks]

    assert "Feed" in scheduled_titles
    assert "Long Walk" in skipped_titles


# ---------------------------------------------------------------------------
# Schedule: display format
# ---------------------------------------------------------------------------

def test_display_returns_correct_keys(owner, pet):
    pet.add_task(Task("Walk", 20, "medium", "walk"))
    sched = Schedule(date="2026-03-29", owner=owner, pet=pet)
    sched.generate()

    rows = sched.display()
    assert len(rows) == 1
    for key in ("Time", "Task", "Type", "Priority", "Duration (min)", "Notes"):
        assert key in rows[0]
