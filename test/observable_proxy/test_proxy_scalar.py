from dataclasses import dataclass

from assertpy import assert_that

from observant import ObservableProxy


@dataclass
class UserProfile:
    username: str
    preferences: dict[str, str]
    age: int


class TestObservableProxyScalar:
    """Unit tests for scalar operations in ObservableProxy class."""

    def test_scalar_sync_updates_model_immediately(self) -> None:
        """Test sync=True makes scalar changes reflect in the model immediately."""
        # Arrange
        profile = UserProfile(username="x", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=True)

        # Act
        proxy.observable(str, "username").set("y")

        # Assert
        assert_that(profile.username).is_equal_to("y")

    def test_save_to_writes_back_scalar(self) -> None:
        """Test save_to copies the current value back to the target model."""
        # Arrange
        profile = UserProfile(username="original", preferences={}, age=42)
        proxy = ObservableProxy(profile, sync=False)
        proxy.observable(str, "username").set("updated")

        # Act
        proxy.save_to(profile)

        # Assert
        assert_that(profile.username).is_equal_to("updated")

    def test_update_sets_multiple_scalar_fields(self) -> None:
        """Test update() sets multiple scalar observables at once."""
        # Arrange
        profile = UserProfile(username="one", preferences={}, age=5)
        proxy = ObservableProxy(profile, sync=False)

        # Act
        proxy.update(username="two", age=10)

        # Assert
        assert_that(proxy.observable(str, "username").get()).is_equal_to("two")
        assert_that(proxy.observable(int, "age").get()).is_equal_to(10)

    def test_load_dict_sets_scalar_values(self) -> None:
        """Test load_dict() applies multiple scalar fields via a dictionary."""
        # Arrange
        profile = UserProfile(username="old", preferences={}, age=1)
        proxy = ObservableProxy(profile, sync=False)

        # Act
        proxy.load_dict({"username": "new", "age": 99})

        # Assert
        assert_that(proxy.observable(str, "username").get()).is_equal_to("new")
        assert_that(proxy.observable(int, "age").get()).is_equal_to(99)
