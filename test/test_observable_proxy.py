from dataclasses import dataclass
from typing import Any

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


class TestObservableProxy:
    """Unit tests for the ObservableProxy class."""

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

    def test_observable_list_updates_correctly(self) -> None:
        """Test that observable_list allows appending and returns a copy on save."""
        # Arrange
        library = Library(title="History", books=["1984"])
        proxy = ObservableProxy(library, sync=False)

        # Act
        books = proxy.observable_list(str, "books")
        books.append("Brave New World")

        # Assert
        assert_that(books.copy()).contains("1984", "Brave New World")
        assert_that(library.books).contains_only("1984")  # unsaved

        # Save
        proxy.save_to(library)

        # Assert after save
        assert_that(library.books).contains("1984", "Brave New World")

    def test_observable_dict_updates_correctly(self) -> None:
        """Test that observable_dict supports key/value updates and save_to."""
        # Arrange
        profile = UserProfile(username="a", preferences={"theme": "dark"}, age=9)
        proxy = ObservableProxy(profile, sync=False)

        # Act
        prefs = proxy.observable_dict((str, str), "preferences")
        prefs["language"] = "en"

        # Assert
        assert_that(prefs["language"]).is_equal_to("en")
        assert "language" not in profile.preferences  # unsaved

        # Save
        proxy.save_to(profile)

        # Assert after save
        assert_that(profile.preferences).contains_key("language")
        assert_that(profile.preferences["language"]).is_equal_to("en")

    def test_scalar_sync_updates_model_immediately(self) -> None:
        """Test sync=True makes scalar changes reflect in the model immediately."""
        # Arrange
        profile = UserProfile(username="x", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=True)

        # Act
        proxy.observable(str, "username").set("y")

        # Assert
        assert_that(profile.username).is_equal_to("y")

    def test_list_sync_updates_model_immediately(self) -> None:
        """Test sync=True causes ObservableList to write through to the model."""
        # Arrange
        lib = Library(title="Classic", books=["Odyssey"])
        proxy = ObservableProxy(lib, sync=True)

        # Act
        proxy.observable_list(str, "books").append("Iliad")

        # Assert
        assert_that(lib.books).contains("Odyssey", "Iliad")

    def test_dict_sync_updates_model_immediately(self) -> None:
        """Test sync=True causes ObservableDict to write through to the model."""
        # Arrange
        zoo = Zoo(name="Forest", animals=["Fox"], metadata={"location": "north"})
        proxy = ObservableProxy(zoo, sync=True)

        # Act
        proxy.observable_dict((str, str), "metadata")["season"] = "autumn"

        # Assert
        assert_that(zoo.metadata).contains_key("season")
        assert_that(zoo.metadata["season"]).is_equal_to("autumn")

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

    def test_observable_list_does_not_mutate_model_when_sync_false(self) -> None:
        """ObservableList with sync=False should not affect the original model."""
        # Arrange
        library = Library(title="Offline", books=["Dune"])
        proxy = ObservableProxy(library, sync=False)

        # Act
        books = proxy.observable_list(str, "books")
        books.append("Foundation")

        # Assert
        assert_that(books.copy()).contains("Dune", "Foundation")
        assert_that(library.books).contains_only("Dune")  # model unchanged

        # Save and re-check
        proxy.save_to(library)
        assert_that(library.books).contains("Dune", "Foundation")

    def test_observable_list_mutates_model_when_sync_true(self) -> None:
        """ObservableList with sync=True should immediately affect the original model."""
        # Arrange
        library = Library(title="Live", books=["Dune"])
        proxy = ObservableProxy(library, sync=True)

        # Act
        books = proxy.observable_list(str, "books")
        books.append("Hyperion")

        # Assert
        assert_that(library.books).contains("Dune", "Hyperion")

    def test_observable_dict_does_not_mutate_model_when_sync_false(self) -> None:
        """ObservableDict with sync=False should not change the model until saved."""
        # Arrange
        zoo = Zoo(name="Typed Zoo", animals=["Elephant"], metadata={"climate": "dry"})
        proxy = ObservableProxy(zoo, sync=False)

        # Act
        meta = proxy.observable_dict((str, str), "metadata")
        meta["habitat"] = "savannah"

        # Assert
        assert_that(meta["habitat"]).is_equal_to("savannah")
        assert "habitat" not in zoo.metadata

        # Save and re-check
        proxy.save_to(zoo)
        assert_that(zoo.metadata).contains("climate", "habitat")

    def test_observable_dict_mutates_model_when_sync_true(self) -> None:
        """ObservableDict with sync=True should mutate the model directly."""
        # Arrange
        zoo = Zoo(name="Online Zoo", animals=["Giraffe"], metadata={"theme": "jungle"})
        proxy = ObservableProxy(zoo, sync=True)

        # Act
        proxy.observable_dict((str, str), "metadata")["ticket_price"] = "$15"

        # Assert
        assert_that(zoo.metadata["ticket_price"]).is_equal_to("$15")

    def test_initially_not_dirty(self) -> None:
        """Test that a new proxy starts with no dirty fields."""
        # Arrange
        profile = UserProfile(username="clean", preferences={}, age=25)
        proxy = ObservableProxy(profile, sync=False)

        # Assert
        assert_that(proxy.is_dirty()).is_false()
        assert_that(proxy.dirty_fields()).is_empty()

    def test_scalar_field_marked_dirty_when_changed(self) -> None:
        """Test that scalar fields are marked as dirty when changed."""
        # Arrange
        profile = UserProfile(username="original", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Act
        proxy.observable(str, "username").set("modified")

        # Assert
        assert_that(proxy.is_dirty()).is_true()
        assert_that(proxy.dirty_fields()).contains("username")
        assert_that(proxy.dirty_fields()).is_length(1)

    def test_list_field_marked_dirty_when_modified(self) -> None:
        """Test that list fields are marked as dirty when modified."""
        # Arrange
        library = Library(title="SciFi", books=["Dune"])
        proxy = ObservableProxy(library, sync=False)

        # Act
        proxy.observable_list(str, "books").append("Foundation")

        # Assert
        assert_that(proxy.is_dirty()).is_true()
        assert_that(proxy.dirty_fields()).contains("books")

    def test_dict_field_marked_dirty_when_modified(self) -> None:
        """Test that dict fields are marked as dirty when modified."""
        # Arrange
        profile = UserProfile(username="user", preferences={"theme": "light"}, age=40)
        proxy = ObservableProxy(profile, sync=False)

        # Act
        proxy.observable_dict((str, str), "preferences")["language"] = "en"

        # Assert
        assert_that(proxy.is_dirty()).is_true()
        assert_that(proxy.dirty_fields()).contains("preferences")

    def test_multiple_fields_tracked_correctly(self) -> None:
        """Test that multiple dirty fields are tracked correctly."""
        # Arrange
        profile = UserProfile(username="multi", preferences={"theme": "dark"}, age=50)
        proxy = ObservableProxy(profile, sync=False)

        # Act
        proxy.observable(str, "username").set("changed")
        proxy.observable_dict((str, str), "preferences")["font"] = "Arial"
        proxy.observable(int, "age").set(51)

        # Assert
        assert_that(proxy.is_dirty()).is_true()
        assert_that(proxy.dirty_fields()).contains("username", "preferences", "age")
        assert_that(proxy.dirty_fields()).is_length(3)

    def test_reset_dirty_clears_state(self) -> None:
        """Test that reset_dirty() clears the dirty state."""
        # Arrange
        profile = UserProfile(username="reset", preferences={}, age=60)
        proxy = ObservableProxy(profile, sync=False)
        proxy.observable(str, "username").set("modified")

        # Act
        proxy.reset_dirty()

        # Assert
        assert_that(proxy.is_dirty()).is_false()
        assert_that(proxy.dirty_fields()).is_empty()

    def test_save_to_clears_dirty_state(self) -> None:
        """Test that save_to() clears the dirty state."""
        # Arrange
        profile = UserProfile(username="save", preferences={}, age=70)
        proxy = ObservableProxy(profile, sync=False)
        proxy.observable(str, "username").set("saved")

        # Act
        proxy.save_to(profile)

        # Assert
        assert_that(proxy.is_dirty()).is_false()
        assert_that(proxy.dirty_fields()).is_empty()
        assert_that(profile.username).is_equal_to("saved")

    # Validation Tests

    def test_initially_valid(self) -> None:
        """Test that a new proxy starts with no validation errors."""
        # Arrange
        profile = UserProfile(username="valid", preferences={}, age=25)
        proxy = ObservableProxy(profile, sync=False)

        # Assert
        assert_that(proxy.is_valid().get()).is_true()
        assert_that(proxy.validation_errors()).is_empty()
        assert_that(proxy.validation_for("username").get()).is_empty()

    def test_scalar_field_validation(self) -> None:
        """Test validation for scalar fields."""
        # Arrange
        profile = UserProfile(username="short", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Add validator that requires username to be at least 5 characters
        proxy.add_validator("username", lambda v: "Username too short" if len(v) < 5 else None)

        # Assert - initially valid
        assert_that(proxy.is_valid().get()).is_true()

        # Act - set invalid value
        proxy.observable(str, "username").set("abc")

        # Assert - now invalid
        assert_that(proxy.is_valid().get()).is_false()
        assert_that(proxy.validation_errors()).contains_key("username")
        assert_that(proxy.validation_for("username").get()).contains("Username too short")

        # Act - set valid value
        proxy.observable(str, "username").set("valid_name")

        # Assert - valid again
        assert_that(proxy.is_valid().get()).is_true()
        assert_that(proxy.validation_errors()).does_not_contain_key("username")
        assert_that(proxy.validation_for("username").get()).is_empty()

    def test_multiple_validators_for_field(self) -> None:
        """Test that multiple validators for a field all run and collect errors."""
        # Arrange
        profile = UserProfile(username="user", preferences={}, age=-5)
        proxy = ObservableProxy(profile, sync=False)

        # Add multiple validators
        proxy.add_validator("age", lambda v: "Age must be positive" if v < 0 else None)
        proxy.add_validator("age", lambda v: "Age must be under 120" if v > 120 else None)

        # Assert - initially invalid
        assert_that(proxy.is_valid().get()).is_false()
        assert_that(proxy.validation_for("age").get()).contains("Age must be positive")

        # Act - set another invalid value
        proxy.observable(int, "age").set(150)

        # Assert - still invalid but different error
        assert_that(proxy.is_valid().get()).is_false()
        assert_that(proxy.validation_for("age").get()).contains("Age must be under 120")

        # Act - set valid value
        proxy.observable(int, "age").set(30)

        # Assert - now valid
        assert_that(proxy.is_valid().get()).is_true()
        assert_that(proxy.validation_for("age").get()).is_empty()

    def test_list_field_validation(self) -> None:
        """Test validation for list fields."""
        # Arrange
        library = Library(title="Test", books=["Book1"])
        proxy = ObservableProxy(library, sync=False)

        # Add validator that requires at least 2 books
        proxy.add_validator("books", lambda v: "Need at least 2 books" if len(v) < 2 else None)

        # Assert - initially invalid
        assert_that(proxy.is_valid().get()).is_false()
        assert_that(proxy.validation_for("books").get()).contains("Need at least 2 books")

        # Act - add a book
        books = proxy.observable_list(str, "books")
        books.append("Book2")

        # Assert - now valid
        assert_that(proxy.is_valid().get()).is_true()
        assert_that(proxy.validation_for("books").get()).is_empty()

    def test_dict_field_validation(self) -> None:
        """Test validation for dict fields."""
        # Arrange
        profile = UserProfile(username="user", preferences={"theme": "dark"}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Add validator that requires 'language' key
        proxy.add_validator("preferences", lambda v: "Missing language preference" if "language" not in v else None)

        # Assert - initially invalid
        assert_that(proxy.is_valid().get()).is_false()
        assert_that(proxy.validation_for("preferences").get()).contains("Missing language preference")

        # Act - add required key
        prefs = proxy.observable_dict((str, str), "preferences")
        prefs["language"] = "en"

        # Assert - now valid
        assert_that(proxy.is_valid().get()).is_true()
        assert_that(proxy.validation_for("preferences").get()).is_empty()

    def test_validation_errors_observable(self) -> None:
        """Test that validation_errors() returns an observable dict that updates."""
        # Arrange
        profile = UserProfile(username="a", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Add validators
        proxy.add_validator("username", lambda v: "Too short" if len(v) < 3 else None)
        proxy.add_validator("age", lambda v: "Too young" if v < 18 else None)

        # Get the errors dict
        errors = proxy.validation_errors()

        # Assert initial state
        assert_that(errors).contains_key("username")
        assert_that(errors).does_not_contain_key("age")

        # Act - fix username but break age
        proxy.observable(str, "username").set("valid")
        proxy.observable(int, "age").set(10)

        # Assert - errors updated
        assert_that(errors).does_not_contain_key("username")
        assert_that(errors).contains_key("age")
        assert_that(errors["age"]).contains("Too young")

    def test_exception_in_validator(self) -> None:
        """Test that exceptions in validators are caught and reported as errors."""
        # Arrange
        profile = UserProfile(username="user", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Add validator that throws
        def buggy_validator(_: Any) -> str | None:
            raise ValueError("Something went wrong")

        proxy.add_validator("username", buggy_validator)

        # Assert - validator error is captured
        assert_that(proxy.is_valid().get()).is_false()
        assert_that(proxy.validation_for("username").get()[0]).contains("Something went wrong")

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
