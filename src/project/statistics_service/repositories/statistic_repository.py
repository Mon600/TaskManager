import datetime

from asyncpg.pgproto.pgproto import timedelta
from sqlalchemy import select, func, cast, literal_column, Date
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.db.models import User, Task, ProjectMember, TaskAssignee, TaskStatus


class StatisticRepository:
    def __init__(self, session: AsyncSession):
        self.session = session


    async def get_all(self, project_id: int):
        stmt = (
        select(
            User.id,
            User.username,
            func.count(Task.id).label("completed_tasks_count")
        )
        .select_from(User)
        .join(ProjectMember, ProjectMember.user_id == User.id)
        .outerjoin(TaskAssignee, TaskAssignee.project_member_id == ProjectMember.id)
        .outerjoin(Task, (Task.id == TaskAssignee.task_id) & (Task.status == TaskStatus.completed))
        .where(ProjectMember.project_id == project_id)
        .group_by(User.id, User.username)
        .order_by(func.count(Task.id).desc())
    )

        res = await self.session.execute(stmt)
        result = list(res.all())
        return result


    async def get_with_day_limit(self, project_id: int, start_date: datetime.date, end_date: datetime.date):
        stmt = (
        select(
            User.id,
            User.username,
            func.count(Task.id).label("completed_tasks_count")
        )
        .select_from(User)
        .join(ProjectMember, ProjectMember.user_id == User.id)
        .outerjoin(TaskAssignee, TaskAssignee.project_member_id == ProjectMember.id)
        .outerjoin(
            Task,
            (Task.id == TaskAssignee.task_id)
            &
            (Task.status == TaskStatus.completed)
            &
            (Task.completed_at >= start_date)
            &
            (Task.completed_at <= end_date)
        )
        .where(ProjectMember.project_id == project_id)
        .group_by(User.id, User.username)
        .order_by(func.count(Task.id).desc())
    )
        res = await self.session.execute(stmt)
        result = list(res.all())
        return result

    async def get_current_month_stat(self, project_id: int, start_date: datetime.date, end_date: datetime.date):
        days = func.generate_series(start_date, end_date, timedelta(days=1)).alias('day')
        day_column = cast(literal_column("day"), Date)
        stmt = (select(

                day_column,
                func.count(Task.completed_at).label('task_count')

        )
                .select_from(
            days.outerjoin
            (
                Task, (Task.completed_at == day_column)
                      &
                      (Task.project_id == project_id)
             )
        ).group_by(day_column).order_by(day_column)
        )

        res = await self.session.execute(stmt)
        result = list(res.all())
        return result


    async def get_avg_completed_tasks(self, project_id: int):
        subq = (
            select(
                ProjectMember.id,
                func.count(Task.id).label("task_count")
            )
            .select_from(ProjectMember)
            .outerjoin(TaskAssignee, TaskAssignee.project_member_id == ProjectMember.id)
            .outerjoin(Task,
                (Task.id == TaskAssignee.task_id) &
                (Task.project_id == project_id) &
                (Task.status == TaskStatus.completed)
            )
            .where(ProjectMember.project_id == project_id)
            .group_by(ProjectMember.id)
            .subquery()
        )

        stmt = select(func.avg(subq.c.task_count).label("avg_completed_tasks"))

        result = await self.session.execute(stmt)
        avg = result.scalar()

        return avg or 0.0


