from datetime import date
import streamlit as st
from pawpal_system import Owner, Pet, Task, Schedule

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

# ── Session-state initialisation ──────────────────────────────────────────────
# st.session_state is the "vault" — objects stored here survive page reruns.
# We check once at the top before anything else renders.
if "owner" not in st.session_state:
    st.session_state.owner = None          # will hold the Owner object
if "active_pet_name" not in st.session_state:
    st.session_state.active_pet_name = None
if "last_schedule" not in st.session_state:
    st.session_state.last_schedule = None
if "last_schedules" not in st.session_state:
    st.session_state.last_schedules = {}   # pet_name → Schedule (for conflict detection)

# ── Sidebar: Owner Setup ───────────────────────────────────────────────────────
with st.sidebar:
    st.title("🐾 PawPal+")
    st.subheader("Owner Setup")

    if st.session_state.owner is None:
        # No owner yet → show creation form
        with st.form("owner_form"):
            o_name      = st.text_input("Your name", placeholder="e.g. Jordan")
            o_available = st.number_input(
                "Available time today (minutes)", min_value=1, max_value=480, value=90
            )
            o_prefs_raw = st.text_area(
                "Preferences (one per line)",
                placeholder="e.g.\nmorning walks only\nno tasks after 8pm",
            )
            owner_submit = st.form_submit_button("Create Owner Profile")

        if owner_submit:
            prefs = [p.strip() for p in o_prefs_raw.splitlines() if p.strip()]
            try:
                st.session_state.owner = Owner(o_name, o_available, prefs)
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    else:
        # Owner exists → show summary and controls
        owner: Owner = st.session_state.owner
        st.success(f"Logged in as **{owner.name}**")
        st.metric("Available today", f"{owner.available_minutes} min")

        if owner.preferences:
            st.caption("Preferences:")
            for pref in owner.preferences:
                st.caption(f"• {pref}")

        st.divider()

        # Allow updating available time without losing all data
        new_time = st.number_input(
            "Update available time (min)",
            min_value=0, max_value=480,
            value=owner.available_minutes,
            key="sidebar_time_input",
        )
        if st.button("Update time"):
            try:
                owner.set_available_time(new_time)
                st.session_state.last_schedule = None   # stale schedule — clear it
                st.success("Updated!")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

        if st.button("Reset owner profile", type="secondary"):
            st.session_state.owner = None
            st.session_state.active_pet_name = None
            st.session_state.last_schedule = None
            st.session_state.last_schedules = {}
            st.rerun()

# ── Guard: require owner before showing any main content ─────────────────────
if st.session_state.owner is None:
    st.title("Welcome to PawPal+")
    st.info("Fill in your **Owner Setup** in the sidebar to get started.")
    st.stop()

# Convenience alias used throughout the rest of the script
owner: Owner = st.session_state.owner

st.title(f"🐾 PawPal+ — {owner.name}'s Dashboard")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_pets, tab_schedule = st.tabs(["🐾 Pets & Tasks", "📅 Schedule"])

# =============================================================================
# TAB 1 — Pets & Tasks
# =============================================================================
with tab_pets:

    # ── Add a Pet ─────────────────────────────────────────────────────────────
    with st.expander("➕ Add a New Pet", expanded=len(owner.pets) == 0):
        with st.form("add_pet_form"):
            ap_col1, ap_col2, ap_col3 = st.columns(3)
            with ap_col1:
                ap_name    = st.text_input("Pet name", placeholder="e.g. Mochi")
            with ap_col2:
                ap_species = st.selectbox("Species", ["dog", "cat", "other"])
            with ap_col3:
                ap_age     = st.number_input("Age (years)", min_value=0, max_value=30, value=1)
            ap_needs_raw = st.text_input(
                "Special needs (comma-separated, optional)",
                placeholder="e.g. senior, diabetic",
            )
            add_pet_btn = st.form_submit_button("Add Pet")

        if add_pet_btn:
            needs = [n.strip() for n in ap_needs_raw.split(",") if n.strip()]
            try:
                new_pet = Pet(name=ap_name, species=ap_species, age=ap_age, special_needs=needs)
                owner.add_pet(new_pet)
                st.session_state.active_pet_name = new_pet.name
                st.session_state.last_schedule = None
                st.session_state.last_schedules = {}   # pet list changed — clear stale schedules
                st.success(f"✅ {ap_name} added!")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    # ── Pet selector ──────────────────────────────────────────────────────────
    pets = owner.get_pets()

    if not pets:
        st.info("No pets yet — add one above to get started.")
    else:
        pet_names   = [p.name for p in pets]
        default_idx = (
            pet_names.index(st.session_state.active_pet_name)
            if st.session_state.active_pet_name in pet_names
            else 0
        )

        selected_name = st.selectbox("Select pet", pet_names, index=default_idx)
        st.session_state.active_pet_name = selected_name
        active_pet: Pet = next(p for p in pets if p.name == selected_name)

        # Pet summary row
        m1, m2, m3 = st.columns(3)
        m1.metric("Species", active_pet.species.capitalize())
        m2.metric("Age", f"{active_pet.age} yr")
        m3.metric("Tasks", len(active_pet.tasks))

        if active_pet.special_needs:
            st.caption(f"Special needs: {', '.join(active_pet.special_needs)}")

        # Remove pet button
        if st.button(f"Remove {active_pet.name}", type="secondary"):
            try:
                owner.remove_pet(active_pet.name)
                st.session_state.active_pet_name = None
                st.session_state.last_schedule = None
                st.session_state.last_schedules.pop(active_pet.name, None)
                st.rerun()
            except ValueError as e:
                st.error(str(e))

        st.divider()

        # ── Add a Task ────────────────────────────────────────────────────────
        with st.expander("➕ Add a Task"):
            with st.form("add_task_form"):
                at_col1, at_col2, at_col3 = st.columns(3)
                with at_col1:
                    at_title    = st.text_input("Task title", placeholder="e.g. Morning walk")
                with at_col2:
                    at_duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
                with at_col3:
                    at_priority = st.selectbox("Priority", ["high", "medium", "low"])
                at_col4, at_col5 = st.columns(2)
                with at_col4:
                    at_type  = st.selectbox(
                        "Task type", ["walk", "feeding", "meds", "grooming", "enrichment"]
                    )
                with at_col5:
                    at_notes = st.text_input("Notes (optional)", placeholder="e.g. gentle pace")
                add_task_btn = st.form_submit_button("Add Task")

            if add_task_btn:
                try:
                    new_task = Task(
                        title=at_title,
                        duration_minutes=int(at_duration),
                        priority=at_priority,
                        task_type=at_type,
                        notes=at_notes,
                    )
                    active_pet.add_task(new_task)
                    st.session_state.last_schedule = None  # tasks changed — clear stale schedule
                    st.success(f"✅ '{at_title}' added to {active_pet.name}!")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

        # ── Task list ─────────────────────────────────────────────────────────
        st.subheader(f"{active_pet.name}'s Tasks")

        if not active_pet.tasks:
            st.info("No tasks yet — add one above.")
        else:
            # ── High-priority alert (uses get_high_priority_tasks) ────────────
            pending_high = [
                t for t in active_pet.get_high_priority_tasks()
                if not t.is_completed()
            ]
            if pending_high:
                titles = ", ".join(f"**{t.title}**" for t in pending_high)
                st.warning(
                    f"⚠️ {len(pending_high)} high-priority task(s) still pending: {titles}. "
                    "Make sure these are scheduled today!"
                )

            # ── Status filter (uses filter_by_status via Schedule helper) ─────
            filter_status = st.radio(
                "Show tasks:", ["all", "pending", "completed"],
                horizontal=True, key=f"filter_{active_pet.name}"
            )
            if filter_status == "all":
                tasks_to_show = active_pet.tasks
            else:
                tasks_to_show = [t for t in active_pet.tasks if t.status == filter_status]

            if not tasks_to_show:
                st.info(f"No {filter_status} tasks.")
            else:
                PRIORITY_BADGE = {"high": "🔴", "medium": "🟡", "low": "🟢"}

                # Header row
                h1, h2, h3, h4, h5, h6 = st.columns([3, 2, 1, 2, 1, 1])
                h1.caption("**Task**")
                h2.caption("**Type · Priority**")
                h3.caption("**Min**")
                h4.caption("**Notes**")
                h5.caption("**Status**")
                h6.caption("**Del**")

                for i, task in enumerate(tasks_to_show):
                    c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 1, 2, 1, 1])
                    badge = PRIORITY_BADGE.get(task.priority, "")
                    c1.write(task.title)
                    c2.caption(f"{task.task_type} · {badge} {task.priority}")
                    c3.caption(str(task.duration_minutes))
                    c4.caption(task.notes or "—")

                    # Toggle complete / pending
                    toggle_label = "✅" if task.is_completed() else "⬜"
                    if c5.button(toggle_label, key=f"toggle_{active_pet.name}_{i}"):
                        if task.is_completed():
                            task.mark_incomplete()
                        else:
                            task.mark_complete()
                        st.session_state.last_schedule = None
                        st.rerun()

                    # Delete task
                    if c6.button("🗑", key=f"del_{active_pet.name}_{i}"):
                        try:
                            active_pet.remove_task(task.title)
                            st.session_state.last_schedule = None
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))

# =============================================================================
# TAB 2 — Schedule
# =============================================================================
with tab_schedule:
    st.subheader("Generate Today's Schedule")

    pets = owner.get_pets()

    if not pets:
        st.info("Add at least one pet and some tasks in the **Pets & Tasks** tab first.")
    else:
        s_col1, s_col2 = st.columns(2)
        with s_col1:
            sched_pet_name = st.selectbox(
                "Pet to schedule",
                [p.name for p in pets],
                key="sched_pet_select",
            )
        with s_col2:
            sched_date = st.date_input("Date", value=date.today())

        sched_pet: Pet = next(p for p in pets if p.name == sched_pet_name)

        if not sched_pet.tasks:
            st.info(f"{sched_pet.name} has no tasks yet. Add some in the Pets & Tasks tab.")
        else:
            if st.button("Generate Schedule", type="primary"):
                schedule = Schedule(
                    date=sched_date.isoformat(),
                    owner=owner,
                    pet=sched_pet,
                )
                schedule.generate()
                st.session_state.last_schedule = schedule
                # Store per-pet so we can detect cross-pet conflicts
                st.session_state.last_schedules[sched_pet_name] = schedule
                st.rerun()

            # ── Display last generated schedule ───────────────────────────────
            schedule: Schedule | None = st.session_state.last_schedule

            if schedule is not None and schedule.pet.name == sched_pet_name:
                total  = schedule.get_total_duration()
                budget = owner.available_minutes

                st.divider()

                # ── Cross-pet conflict detection ──────────────────────────────
                all_schedules = list(st.session_state.last_schedules.values())
                if len(all_schedules) > 1:
                    conflicts = Schedule.find_conflicts(all_schedules)
                    if conflicts:
                        st.warning(
                            f"⚠️ **Schedule Conflict Detected!** Two of your pets have "
                            "overlapping task times. As a pet owner this means you may not "
                            "be able to be in two places at once. Please adjust durations, "
                            "available time, or add preferences to space tasks apart."
                        )
                        for conflict_msg in conflicts:
                            st.warning(f"🕐 {conflict_msg}")

                # Summary metrics
                sm1, sm2, sm3 = st.columns(3)
                sm1.metric("Tasks scheduled", len(schedule.entries))
                sm2.metric("Time used", f"{total} min")
                sm3.metric("Time remaining", f"{budget - total} min")

                # ── Pending tasks not in schedule ─────────────────────────────
                pending_unscheduled = schedule.filter_by_status("pending")
                scheduled_titles = {e["task"].title for e in schedule.entries}
                leftover = [t for t in pending_unscheduled if t.title not in scheduled_titles]
                if leftover:
                    st.warning(
                        f"⚠️ {len(leftover)} pending task(s) could not be fit into today's "
                        f"schedule: {', '.join(t.title for t in leftover)}. "
                        "Consider increasing your available time or removing lower-priority tasks."
                    )

                # ── Schedule table (sorted chronologically via sort_by_time) ──
                if schedule.entries:
                    st.subheader("Schedule")
                    PRIORITY_BADGE = {"high": "🔴", "medium": "🟡", "low": "🟢"}
                    sorted_entries = schedule.sort_by_time()
                    display_rows = [
                        {
                            "Time": f"{e['start_time']} – {e['end_time']}",
                            "Task": e["task"].title,
                            "Type": e["task"].task_type,
                            "Priority": f"{PRIORITY_BADGE.get(e['task'].priority, '')} {e['task'].priority}",
                            "Duration (min)": e["task"].duration_minutes,
                            "Notes": e["task"].notes or "—",
                        }
                        for e in sorted_entries
                    ]
                    st.success(
                        f"✅ Schedule generated for **{sched_pet.name}** on {sched_date} — "
                        f"{len(schedule.entries)} task(s) across {total} minutes."
                    )
                    st.table(display_rows)
                else:
                    st.warning("No tasks could be scheduled with the current constraints.")

                # Skipped tasks table
                if schedule.skipped_tasks:
                    st.subheader("Skipped Tasks")
                    st.table([
                        {"Task": s["task"].title, "Reason": s["reason"]}
                        for s in schedule.skipped_tasks
                    ])

                # Full reasoning
                with st.expander("View full reasoning"):
                    st.text(schedule.get_explanation())
