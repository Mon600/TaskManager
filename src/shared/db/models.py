from datetime import date, datetime
import enum
from typing import Annotated, Optional

from sqlalchemy import String, ForeignKey, DateTime, func, UniqueConstraint, Integer, CheckConstraint, text, Date
from sqlalchemy.orm import mapped_column, Mapped, relationship

from src.shared.config import Base

pk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]
created_at = Annotated[date, mapped_column(server_default=text("TIMEZONE( 'utc', now())"))]

class TaskPriority(enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"

class TaskStatus(enum.Enum):
    processing = "processing"
    completed = "completed"
    ended = "ended"

class ProjectStatus(enum.Enum):
    open = "open"
    close = "close"


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(60), unique=True, index=True)
    avatar_url: Mapped[Optional[str]]
    project_members_rel: Mapped[list["ProjectMember"]] = relationship(back_populates="user_rel")
    owned_projects_rel: Mapped[list["Project"]] = relationship(back_populates='creator_rel')
    links_rel: Mapped[list["ProjectLink"]] = relationship(back_populates="creator_rel")


class Project(Base):
    __tablename__ = 'projects'

    id: Mapped[pk]
    name: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[Optional[str]] = mapped_column(String(1024))
    creator_user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    status: Mapped[ProjectStatus]
    created_at: Mapped[created_at]
    default_role_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('roles.id', ondelete="RESTRICT"), nullable=False)
    creator_rel: Mapped["User"] = relationship(back_populates="owned_projects_rel")
    tasks_rel: Mapped[list['Task']] = relationship(back_populates='project_rel', order_by="Task.started_at.desc()")
    project_members_rel: Mapped[list["ProjectMember"]] = relationship(back_populates="project_rel")
    roles_rel: Mapped[list["Role"]] = relationship(back_populates="project_rel", foreign_keys="[Role.project_id]")
    links_rel: Mapped[list["ProjectLink"]] = relationship(back_populates="project_rel")
    default_role_rel: Mapped[Optional["Role"]] = relationship(
        foreign_keys=[default_role_id],
        post_update=True,
    )


class ProjectMember(Base):
    __tablename__ = 'project_members'

    id: Mapped[pk]
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete="CASCADE"))
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id', ondelete="CASCADE"))
    role_id: Mapped[int] = mapped_column(ForeignKey('roles.id', ondelete="RESTRICT"), index=True)
    role_rel: Mapped["Role"] = relationship(back_populates="member_rel")
    user_rel: Mapped["User"] = relationship(back_populates="project_members_rel")
    project_rel: Mapped["Project"] = relationship(back_populates="project_members_rel")
    joined_at: Mapped[created_at]
    assigned_tasks_rel: Mapped[list["TaskAssignee"]] = relationship(back_populates="project_member_rel")

    __table_args__ = (UniqueConstraint('user_id', 'project_id', name='_user_project_uc'),)



class Role(Base):
    __tablename__ = 'roles'

    id: Mapped[pk]
    priority: Mapped[int] = mapped_column(Integer, default=1)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(50))
    create_tasks: Mapped[bool] = mapped_column(default=False)
    delete_tasks: Mapped[bool] = mapped_column(default=False)
    update_tasks: Mapped[bool] = mapped_column(default=False)
    update_project: Mapped[bool] = mapped_column(default=False)
    generate_url: Mapped[bool] = mapped_column(default=False)
    delete_users: Mapped[bool] = mapped_column(default=False)
    change_roles: Mapped[bool] = mapped_column(default=False)
    manage_links: Mapped[bool] = mapped_column(default=False)
    project_rel: Mapped["Project"] = relationship(back_populates="roles_rel", foreign_keys=[project_id])
    member_rel: Mapped[list["ProjectMember"]] = relationship(back_populates="role_rel")

    __table_args__ = (
        CheckConstraint("priority <= 10 AND priority >= 1", name="check_priority_range"),
    )



class Task(Base):
    __tablename__ = 'tasks'

    id: Mapped[pk]
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    name: Mapped[str] = mapped_column(String(50), index=True)
    description: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    deadline: Mapped[Optional[date]] = mapped_column(Date())
    completed_at: Mapped[Optional[date]] = mapped_column(Date(), nullable=True)
    is_ended: Mapped[bool] = mapped_column(default=False)
    status: Mapped[TaskStatus] = mapped_column(default='processing')
    priority: Mapped[TaskPriority]
    project_rel: Mapped['Project'] = relationship(back_populates='tasks_rel')
    assignees_rel: Mapped[list["TaskAssignee"]] = relationship(back_populates="task_rel")


class TaskAssignee(Base):
    __tablename__ = 'task_assignees'

    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    project_member_id: Mapped[int] = mapped_column(ForeignKey("project_members.id", ondelete="CASCADE"), primary_key=True)
    task_rel: Mapped["Task"] = relationship(back_populates="assignees_rel")
    project_member_rel: Mapped["ProjectMember"] = relationship(back_populates="assigned_tasks_rel")



class ProjectLink(Base):
    __tablename__ = 'links'

    id: Mapped[pk]
    link: Mapped[str]
    created_at: Mapped[created_at]
    end_at: Mapped[Optional[datetime]]
    is_active: Mapped[bool] = mapped_column(default=True)
    project_id: Mapped[int] = mapped_column(ForeignKey('projects.id', ondelete="CASCADE"), index=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete="CASCADE"), index=True)
    project_rel: Mapped["Project"] = relationship(back_populates="links_rel")
    creator_rel: Mapped["User"] = relationship(back_populates="links_rel")




class RefreshToken(Base):
    __tablename__ = 'tokens'

    id: Mapped[str] = mapped_column(primary_key=True, unique=True, index=True)
    token: Mapped[str] = mapped_column(index=True)
    exp: Mapped[datetime] = mapped_column(DateTime)