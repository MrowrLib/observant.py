from dataclasses import dataclass
from typing import Any

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


class TestObservableProxyValidation:
    """Unit tests for validation in ObservableProxy class."""

    def test_initially_valid(self) -> None:
        """Test that a new proxy starts with no validation errors."""
        # Arrange
        profile = UserProfile(username="valid", preferences={}, age=25)
        proxy = ObservableProxy(profile, sync=False)

        # Assert
        assert_that(proxy.is_valid()).is_true()
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
        assert_that(proxy.is_valid()).is_true()

        # Act - set invalid value
        proxy.observable(str, "username").set("abc")

        # Assert - now invalid
        assert_that(proxy.is_valid()).is_false()
        assert_that(proxy.validation_errors()).contains_key("username")
        assert_that(proxy.validation_for("username").get()).contains("Username too short")

        # Act - set valid value
        proxy.observable(str, "username").set("valid_name")

        # Assert - valid again
        assert_that(proxy.is_valid()).is_true()
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
        assert_that(proxy.is_valid()).is_false()
        assert_that(proxy.validation_for("age").get()).contains("Age must be positive")

        # Act - set another invalid value
        proxy.observable(int, "age").set(150)

        # Assert - still invalid but different error
        assert_that(proxy.is_valid()).is_false()
        assert_that(proxy.validation_for("age").get()).contains("Age must be under 120")

        # Act - set valid value
        proxy.observable(int, "age").set(30)

        # Assert - now valid
        assert_that(proxy.is_valid()).is_true()
        assert_that(proxy.validation_for("age").get()).is_empty()

    def test_list_field_validation(self) -> None:
        """Test validation for list fields."""
        # Arrange
        library = Library(title="Test", books=["Book1"])
        proxy = ObservableProxy(library, sync=False)

        # Add validator that requires at least 2 books
        proxy.add_validator("books", lambda v: "Need at least 2 books" if len(v) < 2 else None)

        # Assert - initially invalid
        assert_that(proxy.is_valid()).is_false()
        assert_that(proxy.validation_for("books").get()).contains("Need at least 2 books")

        # Act - add a book
        books = proxy.observable_list(str, "books")
        books.append("Book2")

        # Assert - now valid
        assert_that(proxy.is_valid()).is_true()
        assert_that(proxy.validation_for("books").get()).is_empty()

    def test_dict_field_validation(self) -> None:
        """Test validation for dict fields."""
        # Arrange
        profile = UserProfile(username="user", preferences={"theme": "dark"}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Add validator that requires 'language' key
        proxy.add_validator("preferences", lambda v: "Missing language preference" if "language" not in v else None)

        # Assert - initially invalid
        assert_that(proxy.is_valid()).is_false()
        assert_that(proxy.validation_for("preferences").get()).contains("Missing language preference")

        # Act - add required key
        prefs = proxy.observable_dict((str, str), "preferences")
        prefs["language"] = "en"

        # Assert - now valid
        assert_that(proxy.is_valid()).is_true()
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
        assert_that(proxy.is_valid()).is_false()
        assert_that(proxy.validation_for("username").get()[0]).contains("Something went wrong")

    def test_different_exceptions_in_validators(self) -> None:
        """Test that different types of exceptions in validators are caught and reported."""
        # Arrange
        profile = UserProfile(username="user", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Add validators that throw different types of exceptions
        def type_error_validator(_: Any) -> str | None:
            raise TypeError("Type error occurred")

        def key_error_validator(_: Any) -> str | None:
            raise KeyError("Missing key")

        def custom_error_validator(_: Any) -> str | None:
            class CustomError(Exception):
                pass

            raise CustomError("Custom error message")

        # Add the validators to different fields
        proxy.add_validator("username", type_error_validator)
        proxy.add_validator("age", key_error_validator)
        proxy.add_validator("preferences", custom_error_validator)

        # Assert - all validator errors are captured with appropriate messages
        assert_that(proxy.is_valid()).is_false()
        assert_that(proxy.validation_for("username").get()[0]).contains("Type error occurred")
        assert_that(proxy.validation_for("age").get()[0]).contains("Missing key")
        assert_that(proxy.validation_for("preferences").get()[0]).contains("Custom error message")

    def test_multiple_validators_return_errors_simultaneously(self) -> None:
        """Test that multiple validators for a field can return errors simultaneously."""
        # Arrange
        profile = UserProfile(username="a", preferences={}, age=150)
        proxy = ObservableProxy(profile, sync=False)

        # Add multiple validators for the same field that will all fail
        proxy.add_validator("username", lambda v: "Too short" if len(v) < 3 else None)
        proxy.add_validator("username", lambda v: "No uppercase" if not any(c.isupper() for c in v) else None)
        proxy.add_validator("username", lambda v: "No digits" if not any(c.isdigit() for c in v) else None)

        # Assert - all validators run and collect errors
        assert_that(proxy.is_valid()).is_false()
        username_errors = proxy.validation_for("username").get()
        assert_that(username_errors).is_length(3)
        assert_that(username_errors).contains("Too short")
        assert_that(username_errors).contains("No uppercase")
        assert_that(username_errors).contains("No digits")

        # Act - fix one validation issue but not others
        proxy.observable(str, "username").set("abc")

        # Assert - remaining validators still fail
        assert_that(proxy.is_valid()).is_false()
        username_errors = proxy.validation_for("username").get()
        assert_that(username_errors).is_length(2)
        assert_that(username_errors).contains("No uppercase")
        assert_that(username_errors).contains("No digits")

        # Act - fix another validation issue
        proxy.observable(str, "username").set("Abc")

        # Assert - only one validator still fails
        assert_that(proxy.is_valid()).is_false()
        username_errors = proxy.validation_for("username").get()
        assert_that(username_errors).is_length(1)
        assert_that(username_errors).contains("No digits")

        # Act - fix all validation issues
        proxy.observable(str, "username").set("Abc1")

        # Assert - now valid
        assert_that(proxy.is_valid()).is_true()
        assert_that(proxy.validation_for("username").get()).is_empty()

    def test_validation_state_after_undo_redo(self) -> None:
        """Test that validation state is updated correctly after undo/redo operations."""
        # Arrange
        profile = UserProfile(username="valid_name", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Add validator that requires username to be at least 5 characters
        proxy.add_validator("username", lambda v: "Username too short" if len(v) < 5 else None)

        # Enable undo tracking
        proxy.set_undo_config("username", enabled=True)

        # Assert - initially valid
        assert_that(proxy.is_valid()).is_true()

        # Act - set invalid value
        proxy.observable(str, "username").set("abc")

        # Assert - now invalid
        assert_that(proxy.is_valid()).is_false()
        assert_that(proxy.validation_for("username").get()).contains("Username too short")

        # Act - undo the change
        proxy.undo("username")

        # Assert - validation state IS updated after undo (fixed behavior)
        assert_that(proxy.is_valid()).is_true()  # Now valid again
        assert_that(proxy.validation_for("username").get()).is_empty()  # No more errors

        # And the actual value is restored
        assert_that(proxy.observable(str, "username").get()).is_equal_to("valid_name")

        # Act - redo the change
        proxy.redo("username")

        # Assert - validation state IS updated after redo (fixed behavior)
        assert_that(proxy.is_valid()).is_false()  # Now invalid again
        assert_that(proxy.validation_for("username").get()).contains("Username too short")

        # And the actual value is restored
        assert_that(proxy.observable(str, "username").get()).is_equal_to("abc")

    def test_computed_field_validation(self) -> None:
        """Test that computed fields can be validated."""
        # Arrange
        profile = UserProfile(username="user", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Register a computed property for full name
        proxy.register_computed("full_name", lambda: f"{proxy.observable(str, 'username').get()} Smith", ["username"])

        # Add validator that requires full name to be at least 10 characters
        proxy.add_validator("full_name", lambda v: "Full name too short" if len(v) < 10 else None)

        # Assert - initially valid (since "user Smith" is 10 characters)
        assert_that(proxy.is_valid()).is_true()
        assert_that(proxy.validation_for("full_name").get()).is_empty()

        # Act - change username to make full name shorter
        proxy.observable(str, "username").set("bob")  # "bob Smith" is 9 characters

        # Get the computed value
        computed_value = proxy.computed(str, "full_name").get()

        # Assert - the computed value is updated correctly
        assert_that(computed_value).is_equal_to("bob Smith")

        # Fixed behavior: validation IS triggered for computed fields when dependencies change
        assert_that(proxy.is_valid()).is_false()  # Now invalid due to computed field
        assert_that(proxy.validation_errors()).contains_key("full_name")
        assert_that(proxy.validation_for("full_name").get()).contains("Full name too short")

    def test_load_dict_triggers_validation(self) -> None:
        """Test that load_dict() triggers validation for the fields it sets."""
        # Arrange
        profile = UserProfile(username="valid", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Add validator that requires username to be at least 5 characters
        proxy.add_validator("username", lambda v: "Username too short" if len(v) < 5 else None)

        # Assert - initially valid
        assert_that(proxy.is_valid()).is_true()

        # Act - load dict with invalid value
        proxy.load_dict({"username": "abc"})

        # Assert - validation triggered
        assert_that(proxy.is_valid()).is_false()
        assert_that(proxy.validation_errors()).contains_key("username")
        assert_that(proxy.validation_for("username").get()).contains("Username too short")

        # Act - load dict with valid value
        proxy.load_dict({"username": "valid_name"})

        # Assert - validation passes
        assert_that(proxy.is_valid()).is_true()
        assert_that(proxy.validation_errors()).does_not_contain_key("username")
        assert_that(proxy.validation_for("username").get()).is_empty()

    def test_validator_returns_string_representation(self) -> None:
        """Test that validators return string representations of different data types."""
        # Arrange
        profile = UserProfile(username="user", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Add validators that return string representations of different types
        proxy.add_validator("username", lambda v: "Error code: 42" if len(v) < 5 else None)
        proxy.add_validator("age", lambda v: "Multiple errors: Error1, Error2" if v < 18 else None)
        proxy.add_validator("preferences", lambda v: "Invalid preferences: {'error': 'Invalid'}" if not v else None)

        # Act - make fields invalid
        proxy.observable(str, "username").set("abc")  # Too short
        proxy.observable(int, "age").set(10)  # Too young

        # Assert - validation errors are strings
        assert_that(proxy.is_valid()).is_false()

        # Check username validation error
        username_errors = proxy.validation_for("username").get()
        assert_that(username_errors).is_length(1)
        assert_that(username_errors[0]).is_equal_to("Error code: 42")

        # Check age validation error
        age_errors = proxy.validation_for("age").get()
        assert_that(age_errors).is_length(1)
        assert_that(age_errors[0]).is_equal_to("Multiple errors: Error1, Error2")

        # Check preferences validation error
        pref_errors = proxy.validation_for("preferences").get()
        assert_that(pref_errors).is_length(1)
        assert_that(pref_errors[0]).is_equal_to("Invalid preferences: {'error': 'Invalid'}")
