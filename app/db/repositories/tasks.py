from datetime import datetime, time

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Task, TaskPriority, TaskStatus
from app.schemas.tasks import TaskCreate


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        user_id: int,
        data: TaskCreate,
    ) -> Task:
        task = Task(
            user_id=user_id,
            title=data.title.strip(),
            description=data.description.strip() if data.description else None,
            due_at=data.due_at,
            priority=data.priority,
            status=TaskStatus.TODO,
        )
        self.session.add(task)
        await self.session.flush()
        return task

    async def active_for_user(self, user_id: int) -> list[Task]:
        result = await self.session.execute(
            select(Task)
            .where(Task.user_id == user_id, Task.status != TaskStatus.DONE)
            .order_by(Task.due_at.is_(None), Task.due_at, Task.priority.desc())
        )
        return list(result.scalars())

    async def complete(self, user_id: int, task_id: int) -> bool:
        task = await self.get_for_user(user_id, task_id)
        if task is None:
            return False
        task.status = TaskStatus.DONE
        task.completed_at = datetime.now()
        await self.session.flush()
        return True

    async def get_for_user(self, user_id: int, task_id: int) -> Task | None:
        result = await self.session.execute(
            select(Task).where(Task.user_id == user_id, Task.id == task_id)
        )
        return result.scalar_one_or_none()

    async def dashboard_counts(self, user_id: int, now: datetime) -> dict[str, int]:
        start_today = datetime.combine(now.date(), time.min)
        end_today = datetime.combine(now.date(), time.max)

        active_count = await self.session.scalar(
            select(func.count(Task.id)).where(
                Task.user_id == user_id,
                Task.status != TaskStatus.DONE,
            )
        )
        overdue_count = await self.session.scalar(
            select(func.count(Task.id)).where(
                Task.user_id == user_id,
                Task.status != TaskStatus.DONE,
                Task.due_at < now,
            )
        )
        today_count = await self.session.scalar(
            select(func.count(Task.id)).where(
                Task.user_id == user_id,
                Task.status != TaskStatus.DONE,
                Task.due_at >= start_today,
                Task.due_at <= end_today,
            )
        )

        return {
            "active": active_count or 0,
            "overdue": overdue_count or 0,
            "today": today_count or 0,
        }
