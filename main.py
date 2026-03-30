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
# Tasks for Mochi (dog)
# ---------------------------------------------------------------------------

mochi.add_task(Task("Insulin shot",    5,  "high",   "meds",       "give before breakfast"))
mochi.add_task(Task("Morning walk",   30,  "high",   "walk",       "gentle pace, no stairs"))
mochi.add_task(Task("Breakfast",      10,  "high",   "feeding",    "half cup kibble + wet food"))
mochi.add_task(Task("Enrichment toy", 20,  "medium", "enrichment", "snuffle mat"))
mochi.add_task(Task("Brushing",       15,  "low",    "grooming",   "focus on hind legs"))

# ---------------------------------------------------------------------------
# Tasks for Luna (cat)
# ---------------------------------------------------------------------------

luna.add_task(Task("Morning feeding", 5,   "high",   "feeding",    "1/4 cup dry food"))
luna.add_task(Task("Playtime",        15,  "medium", "enrichment", "feather wand"))
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
# Display
# ---------------------------------------------------------------------------

DIVIDER     = "=" * 60
SUBDIV      = "-" * 60

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
        print(f"  {'TIME':<14} {'TASK':<22} {'TYPE':<12} {'PRI':<8} {'MIN':>4}")
        print(SUBDIV)
        for entry in schedule.entries:
            t    = entry["task"]
            time = f"{entry['start_time']}–{entry['end_time']}"
            print(f"  {time:<14} {t.title:<22} {t.task_type:<12} {t.priority:<8} {t.duration_minutes:>4}")

    print(SUBDIV)
    print(f"  Scheduled: {schedule.get_total_duration()} / {owner.available_minutes} min")

    if schedule.skipped_tasks:
        print(f"\n  Skipped ({len(schedule.skipped_tasks)}):")
        for skipped in schedule.skipped_tasks:
            print(f"    ✗ {skipped['task'].title:<22}  {skipped['reason']}")

    print()
    print("  Reasoning:")
    for entry in schedule.entries:
        print(f"    • {entry['task'].title}: {entry['reason']}")

    print()


print_schedule(schedule_mochi)
print_schedule(schedule_luna)
