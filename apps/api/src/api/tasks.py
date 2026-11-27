from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from api.auth import get_current_user_id
from api.database import SessionLocal
from api.models import Task

router = APIRouter()


class TaskCreate(BaseModel):
    """What the browser sends to ADD a task."""
    title: str = Field(min_length=1, max_length=200)
    notes: str | None = None
    due_date: date | None = None


class TaskUpdate(BaseModel):
    """What the browser sends to CHANGE a task. Every field is optional:
    send only what changed, e.g. {"done": true}."""
    title: str | None = Field(default=None, min_length=1, max_length=200)
    notes: str | None = None
    due_date: date | None = None
    done: bool | None = None


class TaskOut(BaseModel):
    """What the API sends back."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    notes: str | None
    due_date: date | None
    done: bool
    created_at: datetime


def get_db():
    """Opens a database session for one request and ALWAYS closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_own_task(task_id: int, user_id: str, db: Session) -> Task:
    """Finds a task ONLY if it belongs to this user. Otherwise: 404."""
    task = db.query(Task).filter_by(id=task_id, user_id=user_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.get("", response_model=list[TaskOut])
def list_tasks(user_id: str = Depends(get_current_user_id), db: Session = Depends(get_db)):
    # Not-done first, then by due date (no date last), newest first.
    return (
        db.query(Task)
        .filter_by(user_id=user_id)
        .order_by(Task.done, Task.due_date.asc().nulls_last(), Task.created_at.desc())
        .all()
    )


@router.post("", response_model=TaskOut, status_code=201)
def create_task(
    body: TaskCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    task = Task(user_id=user_id, **body.model_dump())
    db.add(task)
    db.commit()       # actually saves it in Postgres
    db.refresh(task)  # reloads it, to get the id and created_at the database filled in
    return task


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: int,
    body: TaskUpdate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    task = get_own_task(task_id, user_id, db)

    # Only the fields the browser actually sent: {"done": true} must not wipe notes/due_date.
    changes = body.model_dump(exclude_unset=True)
    if "title" in changes and changes["title"] is None:
        raise HTTPException(status_code=422, detail="Title can't be empty")

    for field, value in changes.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    task = get_own_task(task_id, user_id, db)
    db.delete(task)
    db.commit()
