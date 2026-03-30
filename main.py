from pawpal_system import Task, Pet, Owner, Schedule
from datetime import date

# ---------------------------------------------------------------------------
# Setup: Owner and Pets
# ---------------------------------------------------------------------------

owner = Owner(
    name="Jordan",
    available_minutes=120,
    preferences=["no tasks after 9pm", "morning walks only"],
)

mochi = Pet(name="Mochi", species="dog", age=7, special_needs=["senior"])
luna  = Pet(name="Luna",  species="cat", age=2)

# ---------------------------------------------------------------------------
# Tasks for Mochi — added intentionally OUT OF PRIORITY ORDER
# to show that sort_by_time() still produces a chronological list.
# ---------------------------------------------------------------------------

mochi.add_task(Task("Enrichment toy", 20,  "medium", "enrichment", "snuffle mat",      frequency="daily"))
mochi.add_task(Task("Insulin shot",    5,  "high",   "meds",       "give before breakfast", frequency="daily"))
mochi.add_task(Task("Brushing",       15,  "low",    "grooming",   "focus on hind legs", frequency="weekly"))
mochi.add_task(Task("Morning walk",   30,  "high",   "walk",       "gentle pace, no stairs", frequency="daily"))
mochi.add_task(Task("Breakfast",      10,  "high",   "feeding",    "half cup kibble + wet food", frequency="daily"))

# ---------------------------------------------------------------------------
# Tasks for Luna
# ---------------------------------------------------------------------------

luna.add_task(Task("Morning feeding", 5,   "high",   "feeding",    "1/4 cup dry food",  frequency="daily"))
luna.add_task(Task("Playtime",        15,  "medium", "enrichment", "feather wand",      frequency="daily"))
luna.add_task(Task("Nail trim",       10,  "low",    "grooming",   "just front paws today"))

owner.add_pet(mochi)
owner.add_pet(luna)

# ---------------------------------------------------------------------------
# Generate schedules
# ---------------------------------------------------------------------------

today = date.today().isoformat()

schedule_mochi = Schedule(today, owner, mochi)
schedule_luna  = Schedule(today, owner, luna)

schedule_mochi.generate()
schedule_luna.generate()

# ---------------------------------------------------------------------------
# Display helpers (unchanged)
# ---------------------------------------------------------------------------

DIVIDER = "=" * 60
SUBDIV  = "-" * 60


def print_schedule(schedule: Schedule) -> None:
    pet   = schedule.pet
    owner = schedule.owner

    print(DIVIDER)
    print(f"  TODAY'S SCHEDULE — {pet.name.upper()} ({pet.species})")
    print(f"  Owner: {owner.name}  |  Budget: {owner.available_minutes} min  |  {schedule.date}")
    print(DIVIDER)

    if not schedule.entries:
        print("  No tasks could be scheduled today.")
    else:
        print(f"  {'TIME':<14} {'TASK':<22} {'TYPE':<12} {'PRI':<8} {'MIN':>4}  {'FREQ'}")
        print(SUBDIV)
        for entry in schedule.entries:
            t    = entry["task"]
            time = f"{entry['start_time']}–{entry['end_time']}"
            print(f"  {time:<14} {t.title:<22} {t.task_type:<12} {t.priority:<8} {t.duration_minutes:>4}  {t.frequency}")

    print(SUBDIV)
    print(f"  Scheduled: {schedule.get_total_duration()} / {owner.available_minutes} min")

    if schedule.skipped_tasks:
        print(f"\n  Skipped ({len(schedule.skipped_tasks)}):")
        for skipped in schedule.skipped_tasks:
            print(f"    x {skipped['task'].title:<22}  {skipped['reason']}")

    print()
    print("  Reasoning:")
    for entry in schedule.entries:
        print(f"    * {entry['task'].title}: {entry['reason']}")
    print()


print_schedule(schedule_mochi)
print_schedule(schedule_luna)

# ---------------------------------------------------------------------------
# Step 2 — Sorting by time
# Tasks were added out of priority order; after scheduling and sorting
# the output is guaranteed to be chronological.
# ---------------------------------------------------------------------------

print(DIVIDER)
print("  SORT BY TIME — Mochi's entries in chronological order")
print(DIVIDER)
sorted_entries = schedule_mochi.sort_by_time()
for entry in sorted_entries:
    t = entry["task"]
    print(f"  {entry['start_time']}–{entry['end_time']}  {t.title} ({t.priority})")
print()

# ---------------------------------------------------------------------------
# Step 2 — Filtering by status
# Mark one of Mochi's tasks complete, then filter to show pending vs done.
# ---------------------------------------------------------------------------

print(DIVIDER)
print("  FILTER BY STATUS — mark 'Brushing' complete, then filter")
print(DIVIDER)

# Find and mark "Brushing" complete
for task in mochi.tasks:
    if task.title == "Brushing":
        task.mark_complete()
        break

pending_tasks   = schedule_mochi.filter_by_status("pending")
completed_tasks = schedule_mochi.filter_by_status("completed")

print(f"  Pending  ({len(pending_tasks)}): {[t.title for t in pending_tasks]}")
print(f"  Completed({len(completed_tasks)}): {[t.title for t in completed_tasks]}")
print()

# ---------------------------------------------------------------------------
# Step 3 — Recurring tasks
# When a daily/weekly task is marked complete, get_next_occurrence()
# produces a fresh Task due the next day (or next week).
# ---------------------------------------------------------------------------

print(DIVIDER)
print("  RECURRING TASKS — next occurrences after today")
print(DIVIDER)

for task in mochi.tasks:
    if task.frequency != "once":
        task.mark_complete()          # simulate finishing today's task
        nxt = task.get_next_occurrence(today)
        if nxt:
            print(f"  {task.title:<22} ({task.frequency:<6}) -> next due: {nxt.due_date}")

print()

# ---------------------------------------------------------------------------
# Step 4 — Conflict detection
# Both Mochi and Luna schedules start at 08:00, so many entries overlap —
# the owner cannot physically attend to two pets simultaneously.
# find_conflicts() surfaces all overlapping pairs as warning strings.
# ---------------------------------------------------------------------------

print(DIVIDER)
print("  CONFLICT DETECTION — cross-pet schedule overlaps")
print(DIVIDER)

conflicts = Schedule.find_conflicts([schedule_mochi, schedule_luna])

if conflicts:
    for warning in conflicts:
        print(f"  {warning}")
else:
    print("  No conflicts detected.")

print()
print(f"  Total conflicts found: {len(conflicts)}")
print()
