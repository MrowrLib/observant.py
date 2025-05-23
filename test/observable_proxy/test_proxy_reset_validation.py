from dataclasses import dataclass

from assertpy import assert_that

from observant import ObservableProxy


@dataclass
class User:
    username: str
    email: str
    age: int


class TestObservableProxyResetValidation:
    """Unit tests for the reset_validation feature in ObservableProxy class."""

    def test_reset_validation_clears_all_errors(self) -> None:
        """Test that reset_validation() clears all validation errors."""
        # Arrange
        user = User(username="user", email="invalid-email", age=15)
        proxy = ObservableProxy(user)

        # Add validators that will fail
        proxy.add_validator("username", lambda v: "Username too short" if len(v) < 5 else None)
        proxy.add_validator("email", lambda v: "Invalid email" if "@" not in v else None)
        proxy.add_validator("age", lambda v: "Must be 18+" if v < 18 else None)

        # Assert - all fields should have validation errors
        assert_that(proxy.is_valid()).is_false()
        assert_that(proxy.validation_errors()).is_not_empty()
        assert_that(proxy.validation_for("username").get()).is_not_empty()
        assert_that(proxy.validation_for("email").get()).is_not_empty()
        assert_that(proxy.validation_for("age").get()).is_not_empty()

        # Act - reset validation
        proxy.reset_validation()

        # Assert - all validation errors should be cleared
        assert_that(proxy.is_valid()).is_true()
        assert_that(proxy.validation_errors()).is_empty()
        assert_that(proxy.validation_for("username").get()).is_empty()
        assert_that(proxy.validation_for("email").get()).is_empty()
        assert_that(proxy.validation_for("age").get()).is_empty()

    def test_reset_validation_with_revalidate(self) -> None:
        """Test that reset_validation(revalidate=True) re-runs validators."""
        # Arrange
        user = User(username="user", email="invalid-email", age=15)
        proxy = ObservableProxy(user)

        # Add validators that will fail
        proxy.add_validator("username", lambda v: "Username too short" if len(v) < 5 else None)
        proxy.add_validator("email", lambda v: "Invalid email" if "@" not in v else None)
        proxy.add_validator("age", lambda v: "Must be 18+" if v < 18 else None)

        # Assert - all fields should have validation errors
        assert_that(proxy.is_valid()).is_false()
        assert_that(proxy.validation_errors()).is_not_empty()

        # Act - fix the validation issues
        proxy.observable(str, "username").set("longer_username")
        proxy.observable(str, "email").set("valid@example.com")
        proxy.observable(int, "age").set(21)

        # Reset validation with revalidate=True
        proxy.reset_validation(revalidate=True)

        # Assert - validation should pass now
        assert_that(proxy.is_valid()).is_true()
        assert_that(proxy.validation_errors()).is_empty()

        # Act - make a field invalid again
        proxy.observable(int, "age").set(15)

        # Reset validation without revalidating
        proxy.reset_validation(revalidate=False)

        # Assert - validation errors should be cleared even though the field is invalid
        assert_that(proxy.is_valid()).is_true()
        assert_that(proxy.validation_errors()).is_empty()

        # Act - reset validation with revalidate=True
        proxy.reset_validation(revalidate=True)

        # Assert - validation should fail again for the age field
        assert_that(proxy.is_valid()).is_false()
        assert_that(proxy.validation_errors()).is_not_empty()
        assert_that(proxy.validation_for("age").get()).is_not_empty()
        assert_that(proxy.validation_for("username").get()).is_empty()
        assert_that(proxy.validation_for("email").get()).is_empty()

    def test_reset_validation_for_specific_field(self) -> None:
        """Test that reset_validation(field) clears only that field's errors."""
        # Arrange
        user = User(username="user", email="invalid-email", age=15)
        proxy = ObservableProxy(user)

        # Add validators that will fail
        proxy.add_validator("username", lambda v: "Username too short" if len(v) < 5 else None)
        proxy.add_validator("email", lambda v: "Invalid email" if "@" not in v else None)
        proxy.add_validator("age", lambda v: "Must be 18+" if v < 18 else None)

        # Assert - all fields should have validation errors
        assert_that(proxy.is_valid()).is_false()
        assert_that(proxy.validation_errors()).is_not_empty()
        assert_that(proxy.validation_for("username").get()).is_not_empty()
        assert_that(proxy.validation_for("email").get()).is_not_empty()
        assert_that(proxy.validation_for("age").get()).is_not_empty()

        # Act - reset validation for just the username field
        proxy.reset_validation("username")

        # Assert - username validation errors should be cleared, others remain
        assert_that(proxy.is_valid()).is_false()  # Still invalid due to other fields
        assert_that(proxy.validation_for("username").get()).is_empty()
        assert_that(proxy.validation_for("email").get()).is_not_empty()
        assert_that(proxy.validation_for("age").get()).is_not_empty()

        # Act - reset validation for email field with revalidate=True
        proxy.observable(str, "email").set("valid@example.com")  # Fix the email
        proxy.reset_validation("email", revalidate=True)

        # Assert - email validation should now pass
        assert_that(proxy.validation_for("email").get()).is_empty()

        # Act - reset validation for age field with revalidate=True
        proxy.reset_validation("age", revalidate=True)

        # Assert - age validation should still fail because we didn't fix it
        assert_that(proxy.validation_for("age").get()).is_not_empty()

        # Act - fix age and revalidate
        proxy.observable(int, "age").set(21)
        proxy.reset_validation("age", revalidate=True)

        # Assert - all validation should pass now
        assert_that(proxy.is_valid()).is_true()
        assert_that(proxy.validation_errors()).is_empty()
