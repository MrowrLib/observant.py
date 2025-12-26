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


class TestObservableProxyDirty:
    """Unit tests for dirty tracking in ObservableProxy class."""

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

    def test_computed_fields_are_never_dirty(self) -> None:
        """Test that computed fields are never marked as dirty."""
        # Arrange
        profile = UserProfile(username="computed", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Register a computed property
        proxy.register_computed("full_name", lambda: f"{proxy.observable(str, 'username').get()} User", ["username"])

        # Act - change the dependency
        proxy.observable(str, "username").set("modified")

        # Assert - computed field should not be in dirty_fields
        assert_that(proxy.is_dirty()).is_true()
        assert_that(proxy.dirty_fields()).contains("username")
        assert_that(proxy.dirty_fields()).does_not_contain("full_name")

        # Act - change the computed field directly (if possible)
        try:
            proxy.computed(str, "full_name").set("Direct Change")
        except Exception:
            pass  # It's okay if this fails, we just want to make sure it doesn't mark as dirty

        # Assert - computed field should still not be in dirty_fields
        assert_that(proxy.dirty_fields()).does_not_contain("full_name")

    def test_validation_changes_do_not_affect_dirty_state(self) -> None:
        """Test that validation changes do not affect the dirty state."""
        # Arrange
        profile = UserProfile(username="valid", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Add a validator that requires username to be at least 5 characters
        proxy.add_validator("username", lambda value: "Username too short" if len(value) < 5 else None)

        # Assert - initially valid and not dirty
        assert_that(proxy.is_valid()).is_true()
        assert_that(proxy.is_dirty()).is_false()
        assert_that(proxy.dirty_fields()).is_empty()

        # Act - make the field invalid
        proxy.observable(str, "username").set("abc")  # Too short

        # Assert - now invalid but only username is dirty
        assert_that(proxy.is_valid()).is_false()
        assert_that(proxy.is_dirty()).is_true()
        assert_that(proxy.dirty_fields()).contains("username")
        assert_that(proxy.dirty_fields()).is_length(1)  # Only username, not validation state

        # Act - fix the validation error
        proxy.observable(str, "username").set("valid_again")

        # Assert - now valid again but username is still dirty
        assert_that(proxy.is_valid()).is_true()
        assert_that(proxy.is_dirty()).is_true()
        assert_that(proxy.dirty_fields()).contains("username")
        assert_that(proxy.dirty_fields()).is_length(1)

        # Act - reset dirty state
        proxy.reset_dirty()

        # Assert - still valid but no longer dirty
        assert_that(proxy.is_valid()).is_true()
        assert_that(proxy.is_dirty()).is_false()
        assert_that(proxy.dirty_fields()).is_empty()

    def test_undoing_change_reverts_dirty_state(self) -> None:
        """Test whether undoing a change reverts the dirty state."""
        # Arrange
        profile = UserProfile(username="original", preferences={}, age=30)
        proxy = ObservableProxy(profile, undo=True)

        # Assert - initially not dirty
        assert_that(proxy.is_dirty()).is_false()
        assert_that(proxy.dirty_fields()).is_empty()

        # Act - make a change to make it dirty
        proxy.observable(str, "username").set("modified")

        # Assert - now dirty
        assert_that(proxy.is_dirty()).is_true()
        assert_that(proxy.dirty_fields()).contains("username")

        # Act - undo the change
        proxy.undo("username")

        # Assert - check if dirty state is reverted
        # This assertion documents the current behavior, which may be that
        # undoing does not clear the dirty state
        assert_that(proxy.is_dirty()).is_true()  # Still dirty after undo
        assert_that(proxy.dirty_fields()).contains("username")

        # Act - make multiple changes and undo them all
        proxy.observable(str, "username").set("change1")
        proxy.observable(str, "username").set("change2")
        proxy.undo("username")  # Undo to change1
        proxy.undo("username")  # Undo to original

        # Assert - still dirty after undoing all changes
        assert_that(proxy.observable(str, "username").get()).is_equal_to("original")
        assert_that(proxy.is_dirty()).is_true()  # Still dirty after undoing all changes
        assert_that(proxy.dirty_fields()).contains("username")


class TestObservableProxyDirtyObservable:
    """Unit tests for is_dirty_observable() in ObservableProxy class."""

    def test_is_dirty_observable_initially_false(self) -> None:
        """Test that is_dirty_observable() starts as False."""
        # Arrange
        profile = UserProfile(username="clean", preferences={}, age=25)
        proxy = ObservableProxy(profile, sync=False)

        # Act
        dirty_obs = proxy.is_dirty_observable()

        # Assert
        assert_that(dirty_obs.get()).is_false()

    def test_is_dirty_observable_becomes_true_when_field_changes(self) -> None:
        """Test that is_dirty_observable() emits True when a field becomes dirty."""
        # Arrange
        profile = UserProfile(username="original", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)
        dirty_obs = proxy.is_dirty_observable()

        # Act
        proxy.observable(str, "username").set("modified")

        # Assert
        assert_that(dirty_obs.get()).is_true()

    def test_is_dirty_observable_becomes_false_after_reset(self) -> None:
        """Test that is_dirty_observable() emits False after reset_dirty()."""
        # Arrange
        profile = UserProfile(username="reset", preferences={}, age=60)
        proxy = ObservableProxy(profile, sync=False)
        dirty_obs = proxy.is_dirty_observable()
        proxy.observable(str, "username").set("modified")
        assert_that(dirty_obs.get()).is_true()

        # Act
        proxy.reset_dirty()

        # Assert
        assert_that(dirty_obs.get()).is_false()

    def test_is_dirty_observable_becomes_false_after_save_to(self) -> None:
        """Test that is_dirty_observable() emits False after save_to()."""
        # Arrange
        profile = UserProfile(username="save", preferences={}, age=70)
        proxy = ObservableProxy(profile, sync=False)
        dirty_obs = proxy.is_dirty_observable()
        proxy.observable(str, "username").set("saved")
        assert_that(dirty_obs.get()).is_true()

        # Act
        proxy.save_to(profile)

        # Assert
        assert_that(dirty_obs.get()).is_false()

    def test_is_dirty_observable_callback_fires_on_change(self) -> None:
        """Test that on_change callback fires when dirty state changes."""
        # Arrange
        profile = UserProfile(username="callback", preferences={}, age=40)
        proxy = ObservableProxy(profile, sync=False)
        dirty_obs = proxy.is_dirty_observable()

        callback_values: list[bool] = []
        dirty_obs.on_change(lambda v: callback_values.append(v))

        # Act - make dirty
        proxy.observable(str, "username").set("modified")

        # Assert - callback fired with True
        assert_that(callback_values).is_equal_to([True])

        # Act - reset
        proxy.reset_dirty()

        # Assert - callback fired with False
        assert_that(callback_values).is_equal_to([True, False])

    def test_is_dirty_observable_with_list_field(self) -> None:
        """Test that is_dirty_observable() works with list field changes."""
        # Arrange
        library = Library(title="SciFi", books=["Dune"])
        proxy = ObservableProxy(library, sync=False)
        dirty_obs = proxy.is_dirty_observable()

        # Act
        proxy.observable_list(str, "books").append("Foundation")

        # Assert
        assert_that(dirty_obs.get()).is_true()

    def test_is_dirty_observable_with_dict_field(self) -> None:
        """Test that is_dirty_observable() works with dict field changes."""
        # Arrange
        profile = UserProfile(username="user", preferences={"theme": "light"}, age=40)
        proxy = ObservableProxy(profile, sync=False)
        dirty_obs = proxy.is_dirty_observable()

        # Act
        proxy.observable_dict((str, str), "preferences")["language"] = "en"

        # Assert
        assert_that(dirty_obs.get()).is_true()
