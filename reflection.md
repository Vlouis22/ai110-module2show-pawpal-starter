# PawPal+ Project Reflection

## 1. System Design

I chose the follwowing 4 classes:
Owner: Represents the pet owner. It includes attributes like the owner's name, available time, preferences, and a list of their pets. Methods allow managing pets and setting available time.

    Pet: Represents a pet owned by the owner. It includes attributes like the pet's name, species, age, special needs, and a list of tasks. Methods allow managing tasks and retrieving high-priority tasks.

    Task: Represents a specific care task for a pet. Attributes include the task's title, duration, priority, type, and notes. Methods help determine task priority, feasibility, and provide task details as a dictionary.

    Schedule: Represents the daily schedule for pet care. It includes attributes like the date, the owner, the pet, scheduled entries, and skipped tasks. Methods handle generating the schedule, filtering tasks, sorting by priority, assigning times, and providing explanations for scheduling decisions.

**a. Initial design**

My initial UML had the same 4 classes. Owner held the time budget and preferences, Pet held the task list, Task held all the metadata about a single care activity, and Schedule was responsible for taking all of that and producing a plan. The responsibilities were pretty clean from the start because the scenario made it obvious what each object should own.

**b. Design changes**

Yes, the Task class grew during implementation. Originally it only had the attributes from the UML (title, duration, priority, type, notes). Once I started writing the scheduler I realized I needed to track whether a task was already done and whether it repeats, so I added status and frequency. The get_next_occurrence method came with that. It made more sense to put recurrence logic inside Task than to handle it externally because Task already knows everything about itself.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints: the owner's total time budget, task priority, and owner preferences like cutoff hours and morning walks only. I decided priority mattered most because the whole point of the app is making sure the important stuff actually gets done. Time budget is second because you can't schedule what you don't have time for. Preferences come last because they are more like soft rules, not hard limits on what is physically possible.

**b. Tradeoffs**

A tradeoff that the ai suggests was to group by pet first, then use product. Using the if statement "if pet_a == pet_b: continue" generates same-pet pairs only to throw them away after, grouing would eliminate that waste entirely.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?

  I find AI very useful for brainstorming, it increases my speed by a lot. I usually spend so much time brainstorming but now there's a tool that does it and even show more options than i could have come up with. Building this project myself with no ai, it would have taken me at least 2 hours just for brainstorming and coming up with the skeleton/diagram.

- What kinds of prompts or questions were most helpful?

  The kind of prompts that i find most useful is telling it to think of edge cases before implementing, it usually acuatlly finds 2-3 edge cases worth looking over.

**b. Judgment and verification**

One moment was when AI suggested adding a full calendar view with drag and drop rescheduling. I did not accept that because it was way out of scope for what the project needed. I evaluated it by asking myself if the core scheduling logic would be any more correct with that feature and the answer was no. It would have added a lot of complexity for something that is just visual. I kept the simple st.table display instead and focused the extra time on making the conflict detection actually work correctly.

---

## 4. Testing and Verification

**a. What you tested**

I tested task creation and validation, recurrence logic, pet and owner management, priority sorting with the meds bonus, conflict detection across pets, skipping logic for completed and over-budget tasks, and preference enforcement. These tests were important because the scheduling logic has a lot of moving parts and it is easy for one thing to quietly break another. For example without testing the meds bonus specifically I would not have caught a case where a medium priority med task was getting bumped by a medium priority walk.

**b. Confidence**

I am pretty confident the core cases work correctly. My confidence score is a 5 out of 5 for the behaviors I actually tested. If I had more time I would test what happens when two pets have tasks that perfectly share a boundary (one ends at 09:30, another starts at 09:30) to make sure that is not flagged as a conflict when it should not be. I would also test preference combinations like having both a cutoff and morning walks only active at the same time.

---

## 5. Reflection

**a. What went well**

I am most satisfied with the scheduling logic itself. The way priority sorting, the meds bonus, feasibility filtering, and preference constraints all chain together cleanly in generate() felt really good to build. It was one of those moments where the design actually matched the implementation and I did not have to fight the code to make it work.

**b. What you would improve**

If I had another iteration I would redesign how preferences are stored. Right now they are free-text strings that get parsed with regex at schedule time. That works but it is fragile. I would change it to a structured format like a dictionary so the owner can set a cutoff hour as an actual integer instead of typing "no tasks after 8pm" and hoping the regex catches it correctly.

**c. Key takeaway**

The biggest thing I learned is that AI is a multiplier, not a replacement for your own judgment. It can brainstorm faster than I can, catch edge cases I would miss, and generate boilerplate in seconds. But if you just accept everything it gives you without thinking, you end up with a bloated product that solves problems you do not have. The real skill is knowing when to take the suggestion and when to say no.
