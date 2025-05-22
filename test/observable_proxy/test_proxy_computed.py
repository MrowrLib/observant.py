from dataclasses import dataclass

from assertpy import assert_that

from observant import ObservableProxy


@dataclass
class Library:
    title: str
    books: list[str]


@dataclass
class UserProfile:
    username: str
    preferences: dict[str, str]
    age: int


class TestObservableProxyComputed:
    """Unit tests for computed properties in ObservableProxy class."""

    def test_basic_computed_property(self) -> None:
        """Test that a basic computed property works correctly."""
        # Arrange
        profile = UserProfile(username="Ada", preferences={}, age=36)
        proxy = ObservableProxy(profile, sync=False)

        # Register a computed property
        proxy.register_computed("username_upper", lambda: proxy.observable(str, "username").get().upper(), ["username"])

        # Act & Assert
        assert_that(proxy.computed(str, "username_upper").get()).is_equal_to("ADA")

    def test_computed_property_updates_when_dependency_changes(self) -> None:
        """Test that a computed property updates when its dependency changes."""
        # Arrange
        profile = UserProfile(username="Ada", preferences={}, age=36)
        proxy = ObservableProxy(profile, sync=False)

        # Register a computed property
        proxy.register_computed("username_upper", lambda: proxy.observable(str, "username").get().upper(), ["username"])

        # Act
        proxy.observable(str, "username").set("Grace")

        # Assert
        assert_that(proxy.computed(str, "username_upper").get()).is_equal_to("GRACE")

    def test_computed_property_with_multiple_dependencies(self) -> None:
        """Test that a computed property with multiple dependencies works correctly."""
        # Arrange
        profile = UserProfile(username="Ada", preferences={}, age=36)
        proxy = ObservableProxy(profile, sync=False)

        # Register a computed property
        proxy.register_computed("description", lambda: f"{proxy.observable(str, 'username').get()} is {proxy.observable(int, 'age').get()} years old", ["username", "age"])

        # Act & Assert
        assert_that(proxy.computed(str, "description").get()).is_equal_to("Ada is 36 years old")

        # Update one dependency
        proxy.observable(int, "age").set(37)
        assert_that(proxy.computed(str, "description").get()).is_equal_to("Ada is 37 years old")

        # Update another dependency
        proxy.observable(str, "username").set("Grace")
        assert_that(proxy.computed(str, "description").get()).is_equal_to("Grace is 37 years old")

    def test_computed_property_with_list_dependency(self) -> None:
        """Test that a computed property can depend on a list."""
        # Arrange
        library = Library(title="SciFi", books=["Dune", "Foundation"])
        proxy = ObservableProxy(library, sync=False)

        # Register a computed property
        proxy.register_computed("book_count", lambda: len(proxy.observable_list(str, "books")), ["books"])

        # Act & Assert
        assert_that(proxy.computed(int, "book_count").get()).is_equal_to(2)

        # Update the list
        proxy.observable_list(str, "books").append("Neuromancer")
        assert_that(proxy.computed(int, "book_count").get()).is_equal_to(3)

    def test_computed_property_with_dict_dependency(self) -> None:
        """Test that a computed property can depend on a dict."""
        # Arrange
        profile = UserProfile(username="Ada", preferences={"theme": "dark"}, age=36)
        proxy = ObservableProxy(profile, sync=False)

        # Register a computed property
        proxy.register_computed("has_theme", lambda: "theme" in proxy.observable_dict((str, str), "preferences"), ["preferences"])

        # Act & Assert
        assert_that(proxy.computed(bool, "has_theme").get()).is_true()

        # Update the dict
        prefs = proxy.observable_dict((str, str), "preferences")
        del prefs["theme"]
        assert_that(proxy.computed(bool, "has_theme").get()).is_false()

    def test_computed_property_on_change_callback(self) -> None:
        """Test that on_change callbacks work for computed properties."""
        # Arrange
        profile = UserProfile(username="Ada", preferences={}, age=36)
        proxy = ObservableProxy(profile, sync=False)

        # Register a computed property
        proxy.register_computed("username_upper", lambda: proxy.observable(str, "username").get().upper(), ["username"])

        # Set up a callback
        changes = []
        proxy.computed(str, "username_upper").on_change(lambda v: changes.append(v))

        # Act
        proxy.observable(str, "username").set("Grace")

        # Assert
        assert_that(changes).contains("GRACE")

    def test_computed_property_depending_on_another_computed(self) -> None:
        """Test that a computed property can depend on another computed property."""
        # Arrange
        profile = UserProfile(username="Ada", preferences={}, age=36)
        proxy = ObservableProxy(profile, sync=False)

        # Register first computed property
        proxy.register_computed("username_upper", lambda: proxy.observable(str, "username").get().upper(), ["username"])

        # Register second computed property that depends on the first
        proxy.register_computed("greeting", lambda: f"Hello, {proxy.computed(str, 'username_upper').get()}!", ["username_upper"])

        # Act & Assert
        assert_that(proxy.computed(str, "greeting").get()).is_equal_to("Hello, ADA!")

        # Update the original dependency
        proxy.observable(str, "username").set("Grace")
        assert_that(proxy.computed(str, "greeting").get()).is_equal_to("Hello, GRACE!")
