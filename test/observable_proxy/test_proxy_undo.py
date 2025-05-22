import time
from dataclasses import dataclass

from assertpy import assert_that

from observant import ObservableProxy


@dataclass
class UserProfile:
    username: str
    preferences: dict[str, str]
    age: int


@dataclass
class Library:
    title: str
    books: list[str]


class TestObservableProxyUndo:
    """Unit tests for undo/redo functionality in ObservableProxy class."""

    def test_scalar_undo_single_change(self) -> None:
        """Test undoing a single change to a scalar field."""
        # Arrange
        profile = UserProfile(username="original", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Act
        proxy.observable(str, "username").set("modified")
        proxy.undo("username")

        # Assert
        assert_that(proxy.observable(str, "username").get()).is_equal_to("original")

    def test_scalar_undo_multiple_changes(self) -> None:
        """Test undoing multiple changes to a scalar field."""
        # Arrange
        profile = UserProfile(username="first", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Act
        proxy.observable(str, "username").set("second")
        proxy.observable(str, "username").set("third")
        proxy.undo("username")

        # Assert
        assert_that(proxy.observable(str, "username").get()).is_equal_to("second")

        # Act again
        proxy.undo("username")

        # Assert again
        assert_that(proxy.observable(str, "username").get()).is_equal_to("first")

    def test_scalar_redo_after_undo(self) -> None:
        """Test redoing a change after undoing it."""
        # Arrange
        profile = UserProfile(username="original", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Act
        proxy.observable(str, "username").set("modified")
        proxy.undo("username")
        proxy.redo("username")

        # Assert
        assert_that(proxy.observable(str, "username").get()).is_equal_to("modified")

    def test_scalar_redo_stack_cleared_on_new_change(self) -> None:
        """Test that the redo stack is cleared when a new change is made."""
        # Arrange
        profile = UserProfile(username="original", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Act
        proxy.observable(str, "username").set("modified")
        proxy.undo("username")
        proxy.observable(str, "username").set("new_value")  # This should clear the redo stack

        # Assert
        assert_that(proxy.can_redo("username")).is_false()

    def test_scalar_undo_respects_debounce_window(self) -> None:
        """Test that changes within the debounce window are grouped into a single undo step."""
        # Arrange
        profile = UserProfile(username="original", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False, undo_debounce_ms=500)

        # Act
        proxy.observable(str, "username").set("change1")
        proxy.observable(str, "username").set("change2")  # Within debounce window
        proxy.undo("username")

        # Assert
        assert_that(proxy.observable(str, "username").get()).is_equal_to("original")
        assert_that(proxy.can_undo("username")).is_false()  # No more undo steps

    def test_scalar_undo_creates_new_step_after_debounce(self) -> None:
        """Test that changes after the debounce window create a new undo step."""
        # Arrange
        profile = UserProfile(username="original", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False, undo_debounce_ms=100)

        # Act
        proxy.observable(str, "username").set("change1")
        time.sleep(0.2)  # Wait longer than the debounce window
        proxy.observable(str, "username").set("change2")

        # Undo the second change
        proxy.undo("username")

        # Assert
        assert_that(proxy.observable(str, "username").get()).is_equal_to("change1")

        # Undo the first change
        proxy.undo("username")

        # Assert
        assert_that(proxy.observable(str, "username").get()).is_equal_to("original")

    def test_list_undo_append(self) -> None:
        """Test undoing an append operation on a list field."""
        # Arrange
        library = Library(title="Test", books=["Book1"])
        proxy = ObservableProxy(library, sync=False)

        # Act
        proxy.observable_list(str, "books").append("Book2")
        proxy.undo("books")

        # Assert
        assert_that(proxy.observable_list(str, "books")).contains_only("Book1")

    def test_list_undo_remove(self) -> None:
        """Test undoing a remove operation on a list field."""
        # Arrange
        library = Library(title="Test", books=["Book1", "Book2"])
        proxy = ObservableProxy(library, sync=False)

        # Act
        proxy.observable_list(str, "books").pop(1)  # Remove "Book2"
        proxy.undo("books")

        # Assert
        assert_that(proxy.observable_list(str, "books")).contains("Book1", "Book2")

    def test_list_undo_clear(self) -> None:
        """Test undoing a clear operation on a list field."""
        # Arrange
        library = Library(title="Test", books=["Book1", "Book2"])
        proxy = ObservableProxy(library, sync=False)

        # Act
        proxy.observable_list(str, "books").clear()
        proxy.undo("books")

        # Assert
        assert_that(proxy.observable_list(str, "books")).contains("Book1", "Book2")

    def test_list_redo_after_undo(self) -> None:
        """Test redoing a list operation after undoing it."""
        # Arrange
        library = Library(title="Test", books=["Book1"])
        proxy = ObservableProxy(library, sync=False)

        # Act
        proxy.observable_list(str, "books").append("Book2")
        proxy.undo("books")
        proxy.redo("books")

        # Assert
        assert_that(proxy.observable_list(str, "books")).contains("Book1", "Book2")

    def test_dict_undo_set_key(self) -> None:
        """Test undoing a set key operation on a dict field."""
        # Arrange
        profile = UserProfile(username="user", preferences={"theme": "dark"}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Act
        proxy.observable_dict((str, str), "preferences")["language"] = "en"
        proxy.undo("preferences")

        # Assert
        assert_that(proxy.observable_dict((str, str), "preferences")).does_not_contain_key("language")

    def test_dict_undo_delete_key(self) -> None:
        """Test undoing a delete key operation on a dict field."""
        # Arrange
        profile = UserProfile(username="user", preferences={"theme": "dark"}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Act
        del proxy.observable_dict((str, str), "preferences")["theme"]
        proxy.undo("preferences")

        # Assert
        assert_that(proxy.observable_dict((str, str), "preferences")).contains_key("theme")
        assert_that(proxy.observable_dict((str, str), "preferences")["theme"]).is_equal_to("dark")

    def test_dict_redo_after_undo(self) -> None:
        """Test redoing a dict operation after undoing it."""
        # Arrange
        profile = UserProfile(username="user", preferences={"theme": "dark"}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Act
        proxy.observable_dict((str, str), "preferences")["language"] = "en"
        proxy.undo("preferences")
        proxy.redo("preferences")

        # Assert
        assert_that(proxy.observable_dict((str, str), "preferences")).contains_key("language")
        assert_that(proxy.observable_dict((str, str), "preferences")["language"]).is_equal_to("en")

    def test_undo_stack_respects_max_size(self) -> None:
        """Test that the undo stack respects the maximum size."""
        # Arrange
        profile = UserProfile(username="original", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False, undo_max=2)

        # Act - make 3 changes
        proxy.observable(str, "username").set("change1")
        proxy.observable(str, "username").set("change2")
        proxy.observable(str, "username").set("change3")

        # Undo twice
        proxy.undo("username")
        proxy.undo("username")

        # Assert - the first change should be lost due to max size
        assert_that(proxy.observable(str, "username").get()).is_equal_to("change1")
        assert_that(proxy.can_undo("username")).is_false()  # No more undo steps

    def test_can_undo_and_can_redo_flags(self) -> None:
        """Test the can_undo and can_redo flags."""
        # Arrange
        profile = UserProfile(username="original", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Assert - initially no undo/redo
        assert_that(proxy.can_undo("username")).is_false()
        assert_that(proxy.can_redo("username")).is_false()

        # Act - make a change
        proxy.observable(str, "username").set("modified")

        # Assert - can undo, can't redo
        assert_that(proxy.can_undo("username")).is_true()
        assert_that(proxy.can_redo("username")).is_false()

        # Act - undo
        proxy.undo("username")

        # Assert - can't undo, can redo
        assert_that(proxy.can_undo("username")).is_false()
        assert_that(proxy.can_redo("username")).is_true()

        # Act - redo
        proxy.redo("username")

        # Assert - can undo, can't redo
        assert_that(proxy.can_undo("username")).is_true()
        assert_that(proxy.can_redo("username")).is_false()

    def test_undo_after_save_does_not_crash(self) -> None:
        """Test that undoing after saving doesn't crash."""
        # Arrange
        profile = UserProfile(username="original", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Act
        proxy.observable(str, "username").set("modified")
        proxy.save_to(profile)
        proxy.undo("username")

        # Assert
        assert_that(proxy.observable(str, "username").get()).is_equal_to("original")

    def test_global_undo_config_applied_to_all_fields(self) -> None:
        """Test that the global undo config is applied to all fields."""
        # Arrange
        profile = UserProfile(username="original", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False, undo_max=1)

        # Act - make 2 changes to username
        proxy.observable(str, "username").set("change1")
        proxy.observable(str, "username").set("change2")

        # Act - make 2 changes to age
        proxy.observable(int, "age").set(31)
        proxy.observable(int, "age").set(32)

        # Undo both fields
        proxy.undo("username")
        proxy.undo("age")

        # Assert - only the most recent change should be undoable
        assert_that(proxy.observable(str, "username").get()).is_equal_to("change1")
        assert_that(proxy.observable(int, "age").get()).is_equal_to(31)
        assert_that(proxy.can_undo("username")).is_false()
        assert_that(proxy.can_undo("age")).is_false()

    def test_set_undo_config_before_field_creation(self) -> None:
        """Test setting undo config before field creation."""
        # Arrange
        profile = UserProfile(username="original", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Set config before creating the observable
        proxy.set_undo_config("username", undo_max=1)

        # Act - make 2 changes
        proxy.observable(str, "username").set("change1")
        proxy.observable(str, "username").set("change2")

        # Undo
        proxy.undo("username")

        # Assert - only the most recent change should be undoable
        assert_that(proxy.observable(str, "username").get()).is_equal_to("change1")
        assert_that(proxy.can_undo("username")).is_false()

    def test_set_undo_config_after_field_creation(self) -> None:
        """Test setting undo config after field creation."""
        # Arrange
        profile = UserProfile(username="original", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Create the observable first
        proxy.observable(str, "username")

        # Set config after creating the observable
        proxy.set_undo_config("username", undo_max=1)

        # Act - make 2 changes
        proxy.observable(str, "username").set("change1")
        proxy.observable(str, "username").set("change2")

        # Undo
        proxy.undo("username")

        # Assert - only the most recent change should be undoable
        assert_that(proxy.observable(str, "username").get()).is_equal_to("change1")
        assert_that(proxy.can_undo("username")).is_false()

    def test_override_undo_config_on_observable_creation(self) -> None:
        """Test overriding undo config on observable creation."""
        # Arrange
        profile = UserProfile(username="original", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False, undo_max=3)

        # Create observable with overridden config
        proxy.observable(str, "username", undo_max=1)

        # Act - make 2 changes
        proxy.observable(str, "username").set("change1")
        proxy.observable(str, "username").set("change2")

        # Undo
        proxy.undo("username")

        # Assert - only the most recent change should be undoable
        assert_that(proxy.observable(str, "username").get()).is_equal_to("change1")
        assert_that(proxy.can_undo("username")).is_false()

    def test_undo_on_untracked_field_does_nothing(self) -> None:
        """Test that undoing on an untracked field does nothing."""
        # Arrange
        profile = UserProfile(username="original", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Act
        proxy.undo("nonexistent")

        # Assert - no crash
        assert_that(proxy.observable(str, "username").get()).is_equal_to("original")

    def test_redo_on_untracked_field_does_nothing(self) -> None:
        """Test that redoing on an untracked field does nothing."""
        # Arrange
        profile = UserProfile(username="original", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Act
        proxy.redo("nonexistent")

        # Assert - no crash
        assert_that(proxy.observable(str, "username").get()).is_equal_to("original")

    def test_undo_when_stack_empty_does_nothing(self) -> None:
        """Test that undoing when the stack is empty does nothing."""
        # Arrange
        profile = UserProfile(username="original", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Create observable but don't make changes
        proxy.observable(str, "username")

        # Act
        proxy.undo("username")

        # Assert - no crash
        assert_that(proxy.observable(str, "username").get()).is_equal_to("original")

    def test_redo_when_stack_empty_does_nothing(self) -> None:
        """Test that redoing when the stack is empty does nothing."""
        # Arrange
        profile = UserProfile(username="original", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Create observable but don't make changes
        proxy.observable(str, "username")

        # Act
        proxy.redo("username")

        # Assert - no crash
        assert_that(proxy.observable(str, "username").get()).is_equal_to("original")
