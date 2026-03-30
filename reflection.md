# PawPal+ Project Reflection

## 1. System Design
I chose the follwowing 4 classes:
    Owner: Represents the pet owner. It includes attributes like the owner's name, available time, preferences, and a list of their pets. Methods allow managing pets and setting available time.

    Pet: Represents a pet owned by the owner. It includes attributes like the pet's name, species, age, special needs, and a list of tasks. Methods allow managing tasks and retrieving high-priority tasks.

    Task: Represents a specific care task for a pet. Attributes include the task's title, duration, priority, type, and notes. Methods help determine task priority, feasibility, and provide task details as a dictionary.

    Schedule: Represents the daily schedule for pet care. It includes attributes like the date, the owner, the pet, scheduled entries, and skipped tasks. Methods handle generating the schedule, filtering tasks, sorting by priority, assigning times, and providing explanations for scheduling decisions.

**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
