import pytest
from pawpal_system import Task, Pet


def test_task_completion():
    task = Task(title="Feed the cat", duration_minutes=10, priority="medium", task_type="feeding")
    task.mark_complete()  # Assuming mark_complete sets a status attribute to "completed"
    assert task.status == "completed"

def test_add_task_to_pet():
    pet = Pet(name="Whiskers", species="cat", age=3)
    initial_task_count = len(pet.tasks)
    new_task = Task(title="Play with laser", duration_minutes=15, priority="low", task_type="enrichment")
    pet.add_task(new_task)
    assert len(pet.tasks) == initial_task_count + 1
    assert pet.tasks[-1].title == "Play with laser"
