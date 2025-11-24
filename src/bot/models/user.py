from datetime import datetime, timezone

from beanie import Document, Insert, Replace, SaveChanges, before_event


class User(Document):
    """User model."""

    user_id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    full_name: str
    language_code: str | None = None
    is_premium: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @before_event(Insert)
    def on_insert_set_timestamps(self):
        """Set attributes at create."""
        now = datetime.now(timezone.utc)
        self.created_at = now
        self.updated_at = now
        object.__setattr__(self, 'updated_at', now)

    @before_event([Replace, SaveChanges])
    def on_update_set_timestamps(self):
        """Set attributes at update."""
        self.updated_at = datetime.now(timezone.utc)

    class Settings:
        name = 'users'
