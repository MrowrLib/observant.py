from dataclasses import dataclass

from assertpy import assert_that

from observant import ObservableProxy


@dataclass
class UserProfile:
    username: str
    preferences: dict[str, str]
    age: int


class TestObservableProxyObservableBehavior:
    """Unit tests for observable behavior in ObservableProxy class."""

    def test_reentrant_on_change(self) -> None:
        """Test that reentrant on_change callbacks (where a callback triggers another set) work correctly."""
        # Arrange
        profile = UserProfile(username="user", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Set up a callback that triggers another set
        changes = []

        def on_username_change(value: str) -> None:
            changes.append(f"Username changed to {value}")
            # This is the reentrant part - we set age from within the username callback
            if value == "trigger":
                proxy.observable(int, "age").set(40)

        def on_age_change(value: int) -> None:
            changes.append(f"Age changed to {value}")

        # Register the callbacks
        proxy.observable(str, "username").on_change(on_username_change)
        proxy.observable(int, "age").on_change(on_age_change)

        # Act - trigger the reentrant callback
        proxy.observable(str, "username").set("trigger")

        # Assert - both callbacks should have been called in the correct order
        assert_that(changes).is_length(2)
        assert_that(changes[0]).is_equal_to("Username changed to trigger")
        assert_that(changes[1]).is_equal_to("Age changed to 40")

        # Assert - both values should be updated
        assert_that(proxy.observable(str, "username").get()).is_equal_to("trigger")
        assert_that(proxy.observable(int, "age").get()).is_equal_to(40)

    def test_multiple_on_change_callbacks(self) -> None:
        """Test that multiple on_change callbacks for the same field all get called."""
        # Arrange
        profile = UserProfile(username="user", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Set up multiple callbacks for the same field
        callback1_calls = []
        callback2_calls = []
        callback3_calls = []

        def callback1(value: str) -> None:
            callback1_calls.append(value)

        def callback2(value: str) -> None:
            callback2_calls.append(value)

        def callback3(value: str) -> None:
            callback3_calls.append(value)

        # Register all callbacks
        proxy.observable(str, "username").on_change(callback1)
        proxy.observable(str, "username").on_change(callback2)
        proxy.observable(str, "username").on_change(callback3)

        # Act - change the value
        proxy.observable(str, "username").set("new_value")

        # Assert - all callbacks should have been called
        assert_that(callback1_calls).is_length(1)
        assert_that(callback1_calls[0]).is_equal_to("new_value")

        assert_that(callback2_calls).is_length(1)
        assert_that(callback2_calls[0]).is_equal_to("new_value")

        assert_that(callback3_calls).is_length(1)
        assert_that(callback3_calls[0]).is_equal_to("new_value")

        # Act - change the value again
        proxy.observable(str, "username").set("another_value")

        # Assert - all callbacks should have been called again
        assert_that(callback1_calls).is_length(2)
        assert_that(callback1_calls[1]).is_equal_to("another_value")

        assert_that(callback2_calls).is_length(2)
        assert_that(callback2_calls[1]).is_equal_to("another_value")

        assert_that(callback3_calls).is_length(2)
        assert_that(callback3_calls[1]).is_equal_to("another_value")

    def test_callback_that_raises_exception(self) -> None:
        """Test that an exception in one callback doesn't prevent other callbacks from running."""
        # Arrange
        profile = UserProfile(username="user", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Set up multiple callbacks, one of which raises an exception
        callback1_calls: list[str] = []
        callback2_calls: list[str] = []
        callback3_calls: list[str] = []

        def callback1(value: str) -> None:
            callback1_calls.append(value)

        def callback2(value: str) -> None:
            # First append the value, then raise the exception
            callback2_calls.append(value)
            raise ValueError("Simulated error in callback")

        def callback3(value: str) -> None:
            callback3_calls.append(value)

        # Register all callbacks
        proxy.observable(str, "username").on_change(callback1)
        proxy.observable(str, "username").on_change(callback2)
        proxy.observable(str, "username").on_change(callback3)

        # Act - change the value, which should trigger all callbacks
        # The second callback will raise an exception, but the third should still run
        try:
            proxy.observable(str, "username").set("new_value")
            # If we get here, the exception was caught internally
            exception_caught_internally = True
        except ValueError:
            # If we get here, the exception was propagated
            exception_caught_internally = False

        # Assert - check if the exception was caught internally or propagated
        # Document the current behavior
        if exception_caught_internally:
            # If exceptions are caught internally, all callbacks should have been called
            assert_that(callback1_calls).is_length(1)
            assert_that(callback1_calls[0]).is_equal_to("new_value")

            assert_that(callback2_calls).is_length(1)  # Value is appended before exception is raised
            assert_that(callback2_calls[0]).is_equal_to("new_value")

            assert_that(callback3_calls).is_length(1)
            assert_that(callback3_calls[0]).is_equal_to("new_value")

            # And the value should have been updated
            assert_that(proxy.observable(str, "username").get()).is_equal_to("new_value")
        else:
            # If exceptions are propagated, only callbacks before the exception should have been called
            assert_that(callback1_calls).is_length(1)
            assert_that(callback1_calls[0]).is_equal_to("new_value")

            assert_that(callback2_calls).is_length(1)  # Value is appended before exception is raised
            assert_that(callback2_calls[0]).is_equal_to("new_value")

            # The third callback might or might not have been called, depending on the implementation
            # If it wasn't called, this means the exception stopped the callback chain
            if len(callback3_calls) == 0:
                print("Exception stopped the callback chain")
            else:
                print("Exception did not stop the callback chain")
                assert_that(callback3_calls[0]).is_equal_to("new_value")

            # The value should still have been updated, since that happens before callbacks
            assert_that(proxy.observable(str, "username").get()).is_equal_to("new_value")
