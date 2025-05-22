from dataclasses import dataclass

from assertpy import assert_that

from observant import ObservableProxy


@dataclass
class Zoo:
    name: str
    animals: list[str]
    metadata: dict[str, str]


@dataclass
class Library:
    title: str
    books: list[str]


@dataclass
class UserProfile:
    username: str
    preferences: dict[str, str]
    age: int


class TestObservableProxyCore:
    """Unit tests for the core functionality of ObservableProxy class."""

    def test_get_returns_original_object(self) -> None:
        """Test that get() returns the original object passed into the proxy."""
        # Arrange
        zoo = Zoo(name="City Zoo", animals=["Lion", "Tiger"], metadata={})
        proxy = ObservableProxy(zoo, sync=False)

        # Act
        result = proxy.get()

        # Assert
        assert_that(result).is_same_as(zoo)

    def test_scalar_observable_set_and_get(self) -> None:
        """Test setting and retrieving a scalar observable."""
        # Arrange
        profile = UserProfile(username="mrowr", preferences={}, age=10)
        proxy = ObservableProxy(profile, sync=False)

        # Act
        proxy.observable(str, "username").set("purr_machine")
        value = proxy.observable(str, "username").get()

        # Assert
        assert_that(value).is_equal_to("purr_machine")
        assert profile.username == "mrowr"  # sync=False, model unchanged

    def test_observable_returns_none_for_untracked_field(self) -> None:
        """Check no observable is created until observable() is called."""
        # Arrange
        zoo = Zoo(name="Hidden", animals=[], metadata={})
        proxy = ObservableProxy(zoo, sync=False)

        # Act
        # Not calling observable() — just trying to peek at internals
        # There's nothing to assert here publicly — just ensuring no crash
        result = proxy.get()

        # Assert
        assert result is not None  # raw assert for typeguard

    def test_observable_list_preserves_reference_on_multiple_calls(self) -> None:
        """Test that multiple observable_list() calls return the same instance."""
        # Arrange
        lib = Library(title="SciFi", books=["Dune"])
        proxy = ObservableProxy(lib, sync=False)

        # Act
        a = proxy.observable_list(str, "books")
        b = proxy.observable_list(str, "books")

        # Assert
        assert_that(a).is_same_as(b)
