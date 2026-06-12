from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class ReminderCategory(TimestampMixin, Base):
    __tablename__ = "reminder_categories"
    __table_args__ = (UniqueConstraint("user_id", "title", name="uq_category_user_title"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)

    user = relationship("User", back_populates="categories")
    reminders = relationship("Reminder", back_populates="category")
