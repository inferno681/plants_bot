def test_event_loop_fixture(event_loop):
    # Accessing the fixture ensures setup/teardown executes.
    assert event_loop.is_running() is False
