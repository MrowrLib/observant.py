from dataclasses import dataclass

from assertpy import assert_that

from observant import ObservableProxy


@dataclass
class Person:
    name: str
    age: int
    email: str
    is_active: bool = True


class TestObservableProxyIntegration:
    """Unit tests for integration between different features in ObservableProxy class."""

    def test_validation_with_computed(self) -> None:
        """Test that validation errors for computed fields show up in validation_errors()."""
        # Arrange
        person = Person(name="Alice", age=30, email="alice@example.com")
        proxy = ObservableProxy(person)

        # Register a computed property
        proxy.register_computed(
            "full_info",
            lambda: f"{proxy.observable(str, 'name').get()} ({proxy.observable(int, 'age').get()}) - {proxy.observable(str, 'email').get()}",
            dependencies=["name", "age", "email"],
        )

        # Add a validator for the computed property
        proxy.add_validator("full_info", lambda v: "Too long" if len(v) > 50 else None)

        # Assert - initially valid
        assert_that(proxy.is_valid().get()).is_true()
        assert_that(proxy.validation_errors()).is_empty()

        # Act - make the computed property invalid by changing a dependency
        proxy.observable(str, "name").set("Alice with a very long name that will make the full_info too long")

        # Assert - validation error should appear
        assert_that(proxy.is_valid().get()).is_false()
        assert_that(proxy.validation_errors()).is_not_empty()
        assert_that(proxy.validation_errors()).contains_key("full_info")
        assert_that(proxy.validation_for("full_info").get()).contains("Too long")

    def test_undo_with_computed(self) -> None:
        """Test that undo/redo operations don't affect computed fields directly."""
        # Arrange
        person = Person(name="Alice", age=30, email="alice@example.com")
        proxy = ObservableProxy(person, undo=True)

        # Register a computed property
        proxy.register_computed(
            "name_and_age",
            lambda: f"{proxy.observable(str, 'name').get()} ({proxy.observable(int, 'age').get()})",
            dependencies=["name", "age"],
        )

        # Get the initial computed value
        initial_computed = proxy.computed(str, "name_and_age").get()
        assert_that(initial_computed).is_equal_to("Alice (30)")

        # Act - change a dependency
        proxy.observable(str, "name").set("Bob")

        # Assert - computed value should update
        assert_that(proxy.computed(str, "name_and_age").get()).is_equal_to("Bob (30)")

        # Assert - computed fields should not be undoable directly
        assert_that(proxy.can_undo("name_and_age")).is_false()
        assert_that(proxy.can_redo("name_and_age")).is_false()

        # Act - try to undo/redo the computed field (should be no-ops)
        proxy.undo("name_and_age")  # Should do nothing
        proxy.redo("name_and_age")  # Should do nothing

        # Assert - computed value should remain unchanged
        assert_that(proxy.computed(str, "name_and_age").get()).is_equal_to("Bob (30)")

        # Act - undo the change to the dependency
        assert_that(proxy.can_undo("name")).is_true()
        proxy.undo("name")

        # Assert - computed value should update based on the undone dependency
        assert_that(proxy.computed(str, "name_and_age").get()).is_equal_to("Alice (30)")

    def test_validation_with_dirty(self) -> None:
        """Test that fixing validation errors doesn't affect dirty state."""
        # Arrange
        person = Person(name="Alice", age=30, email="alice@example.com")
        proxy = ObservableProxy(person)

        # Add validators
        proxy.add_validator("email", lambda v: "Invalid email" if "@" not in v else None)
        proxy.add_validator("age", lambda v: "Must be positive" if v <= 0 else None)

        # Act - make a field invalid and dirty
        proxy.observable(str, "email").set("invalid-email")

        # Assert - field should be invalid and dirty
        assert_that(proxy.is_valid().get()).is_false()
        assert_that(proxy.is_dirty()).is_true()
        assert_that(proxy.dirty_fields()).contains("email")

        # Act - fix the validation error
        proxy.observable(str, "email").set("valid@example.com")

        # Assert - field should be valid but still dirty
        assert_that(proxy.is_valid().get()).is_true()
        assert_that(proxy.is_dirty()).is_true()
        assert_that(proxy.dirty_fields()).contains("email")

        # Act - reset dirty state
        proxy.reset_dirty()

        # Assert - field should be valid and not dirty
        assert_that(proxy.is_valid().get()).is_true()
        assert_that(proxy.is_dirty()).is_false()
        assert_that(proxy.dirty_fields()).is_empty()

        # Act - make a field invalid again
        proxy.observable(int, "age").set(-5)

        # Assert - field should be invalid and dirty
        assert_that(proxy.is_valid().get()).is_false()
        assert_that(proxy.is_dirty()).is_true()
        assert_that(proxy.dirty_fields()).contains("age")

        # Act - reset validation but not dirty state
        proxy.reset_validation()

        # Assert - field should be valid (because validation was reset) but still dirty
        assert_that(proxy.is_valid().get()).is_true()
        assert_that(proxy.is_dirty()).is_true()
        assert_that(proxy.dirty_fields()).contains("age")

    def test_computed_with_dirty(self) -> None:
        """Test that computed fields never appear in dirty_fields()."""
        # Arrange
        person = Person(name="Alice", age=30, email="alice@example.com")
        proxy = ObservableProxy(person)

        # Register a computed property
        proxy.register_computed(
            "name_and_age",
            lambda: f"{proxy.observable(str, 'name').get()} ({proxy.observable(int, 'age').get()})",
            dependencies=["name", "age"],
        )

        # Act - change a dependency
        proxy.observable(str, "name").set("Bob")

        # Assert - dependency should be dirty, but computed field should not
        assert_that(proxy.is_dirty()).is_true()
        assert_that(proxy.dirty_fields()).contains("name")
        assert_that(proxy.dirty_fields()).does_not_contain("name_and_age")

        # Act - change another dependency
        proxy.observable(int, "age").set(40)

        # Assert - both dependencies should be dirty, but computed field should not
        assert_that(proxy.dirty_fields()).contains("name")
        assert_that(proxy.dirty_fields()).contains("age")
        assert_that(proxy.dirty_fields()).does_not_contain("name_and_age")

        # Act - reset dirty state
        proxy.reset_dirty()

        # Assert - no fields should be dirty
        assert_that(proxy.is_dirty()).is_false()
        assert_that(proxy.dirty_fields()).is_empty()

    def test_save_to_includes_computed_fields(self) -> None:
        """Test that save_to() includes computed fields if they shadow real fields."""

        # Arrange
        @dataclass
        class PersonWithFullName:
            first_name: str
            last_name: str
            full_name: str  # This field will be shadowed by a computed property
            age: int

        # Create two objects
        person1 = PersonWithFullName(first_name="Alice", last_name="Smith", full_name="", age=30)
        person2 = PersonWithFullName(first_name="Bob", last_name="Jones", full_name="", age=40)

        # Create a proxy with a computed property that shadows a real field
        proxy = ObservableProxy(person1)

        # Make sure we have observables for all fields
        proxy.observable(str, "first_name")
        proxy.observable(str, "last_name")
        proxy.observable(int, "age")
        proxy.register_computed(
            "full_name",
            lambda: f"{proxy.observable(str, 'first_name').get()} {proxy.observable(str, 'last_name').get()}",
            dependencies=["first_name", "last_name"],
        )

        # Assert - computed property should have the correct value
        assert_that(proxy.computed(str, "full_name").get()).is_equal_to("Alice Smith")

        # Act - save to the second object
        proxy.save_to(person2)

        # Assert - computed field should be saved to the real field in the target object
        assert_that(person2.full_name).is_equal_to("Alice Smith")
        assert_that(person2.first_name).is_equal_to("Alice")
        assert_that(person2.last_name).is_equal_to("Smith")
        assert_that(person2.age).is_equal_to(30)

    def test_load_dict_triggers_validation(self) -> None:
        """Test that load_dict() triggers validation for the loaded fields."""
        # Arrange
        person = Person(name="Alice", age=30, email="alice@example.com")
        proxy = ObservableProxy(person)

        # Add validators
        proxy.add_validator("email", lambda v: "Invalid email" if "@" not in v else None)
        proxy.add_validator("age", lambda v: "Must be positive" if v <= 0 else None)

        # Assert - initially valid
        assert_that(proxy.is_valid().get()).is_true()

        # Act - load invalid values
        proxy.load_dict({"email": "invalid-email", "age": -5})

        # Assert - validation errors should be triggered
        assert_that(proxy.is_valid().get()).is_false()
        assert_that(proxy.validation_errors()).contains_key("email")
        assert_that(proxy.validation_errors()).contains_key("age")
        assert_that(proxy.validation_for("email").get()).contains("Invalid email")
        assert_that(proxy.validation_for("age").get()).contains("Must be positive")

        # Act - load valid values
        proxy.load_dict({"email": "valid@example.com", "age": 25})

        # Assert - validation should pass
        assert_that(proxy.is_valid().get()).is_true()
        assert_that(proxy.validation_errors()).is_empty()

    def test_reset_dirty_does_not_affect_validation(self) -> None:
        """Test that reset_dirty() does not affect validation state."""
        # Arrange
        person = Person(name="Alice", age=30, email="alice@example.com")
        proxy = ObservableProxy(person)

        # Add validators
        proxy.add_validator("email", lambda v: "Invalid email" if "@" not in v else None)

        # Act - make a field invalid and dirty
        proxy.observable(str, "email").set("invalid-email")

        # Assert - field should be invalid and dirty
        assert_that(proxy.is_valid().get()).is_false()
        assert_that(proxy.is_dirty()).is_true()
        assert_that(proxy.validation_errors()).contains_key("email")

        # Act - reset dirty state
        proxy.reset_dirty()

        # Assert - field should still be invalid but not dirty
        assert_that(proxy.is_valid().get()).is_false()
        assert_that(proxy.is_dirty()).is_false()
        assert_that(proxy.validation_errors()).contains_key("email")

        # Act - reset validation
        proxy.reset_validation()

        # Assert - field should be valid and not dirty
        assert_that(proxy.is_valid().get()).is_true()
        assert_that(proxy.is_dirty()).is_false()
        assert_that(proxy.validation_errors()).is_empty()
