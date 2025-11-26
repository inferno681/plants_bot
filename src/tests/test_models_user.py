from __future__ import annotations

from bot.models.user import User


def test_user_update_sets_timestamp():
    user = User(
        user_id=1,
        first_name='First',
        last_name='Last',
        username='user',
        full_name='Full Name',
    )

    user.on_update_set_timestamps()

    assert user.updated_at is not None
