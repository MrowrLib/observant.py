import io
import sys
from dataclasses import dataclass

from assertpy import assert_that

from observant import ObservableProxy


@dataclass
class UserProfile:
    username: str
    preferences: dict[str, str]
    age: int


class TestObservableProxyUndoConfig:
    """Unit tests for undo configuration in ObservableProxy class."""

    def test_undo_disabled_by_default(self) -> None:
        """Test that undo is disabled by default."""
        # Arrange
        profile = UserProfile(username="original", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)  # undo=False by default

        # Act
        proxy.observable(str, "username").set("modified")

        # Assert - undo should not be available
        assert_that(proxy.can_undo("username")).is_false()

    def test_undo_enabled_explicitly(self) -> None:
        """Test that undo can be enabled explicitly."""
        # Arrange
        profile = UserProfile(username="original", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False, undo=True)

        # Act
        proxy.observable(str, "username").set("modified")

        # Assert - undo should be available
        assert_that(proxy.can_undo("username")).is_true()

    def test_sync_and_undo_prints_warning(self) -> None:
        """Test that enabling both sync and undo prints a warning."""
        # Arrange - redirect stdout to capture the warning
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            # Act
            profile = UserProfile(username="original", preferences={}, age=30)
            proxy = ObservableProxy(profile, sync=True, undo=True)

            # Assert - check that a warning was printed
            output = sys.stdout.getvalue()
            assert_that(output).contains("Warning")
            assert_that(output).contains("sync=True with undo=True")
        finally:
            # Restore stdout
            sys.stdout = old_stdout

    def test_undo_config_defaults_applied_correctly(self) -> None:
        """Test that undo config defaults are applied correctly."""
        # Arrange
        profile = UserProfile(username="original", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False, undo=True)

        # Act - make more changes than the default max
        for i in range(60):  # Default max is 50
            proxy.observable(str, "username").set(f"change{i}")

        # Undo all possible changes
        undo_count = 0
        while proxy.can_undo("username"):
            proxy.undo("username")
            undo_count += 1

        # Assert - should be able to undo the default max number of changes
        assert_that(undo_count).is_less_than_or_equal_to(50)

    def test_undo_config_custom_values_applied(self) -> None:
        """Test that custom undo config values are applied correctly."""
        # Arrange
        profile = UserProfile(username="original", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False, undo=True, undo_max=5)

        # Act - make more changes than the custom max
        for i in range(10):
            proxy.observable(str, "username").set(f"change{i}")

        # Undo all possible changes
        undo_count = 0
        while proxy.can_undo("username"):
            proxy.undo("username")
            undo_count += 1

        # Assert - should be able to undo exactly the custom max number of changes
        assert_that(undo_count).is_equal_to(5)

    def test_scalar_undo_with_sync_true_affects_model(self) -> None:
        """Test that undoing a scalar change with sync=True affects the model."""
        # Arrange
        profile = UserProfile(username="original", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=True, undo=True)

        # Act
        proxy.observable(str, "username").set("modified")

        # Assert - model should be updated
        assert_that(profile.username).is_equal_to("modified")

        # Act - undo
        proxy.undo("username")

        # Assert - model should be reverted
        assert_that(profile.username).is_equal_to("original")

    def test_list_undo_with_sync_true_affects_model(self) -> None:
        """Test that undoing a list change with sync=True affects the model."""
        # Arrange
        profile = UserProfile(username="user", preferences={}, age=30)
        profile.preferences = {"theme": "dark"}
        proxy = ObservableProxy(profile, sync=True, undo=True)

        # Act
        prefs = proxy.observable_dict((str, str), "preferences")
        prefs["language"] = "en"

        # Assert - model should be updated
        assert_that(profile.preferences).contains_key("language")

        # Act - undo
        proxy.undo("preferences")

        # Assert - model should be reverted
        assert_that(profile.preferences).does_not_contain_key("language")

    def test_dict_undo_with_sync_true_affects_model(self) -> None:
        """Test that undoing a dict change with sync=True affects the model."""
        # Arrange
        profile = UserProfile(username="user", preferences={}, age=30)
        profile.preferences = {"theme": "dark"}
        proxy = ObservableProxy(profile, sync=True, undo=True)

        # Act
        prefs = proxy.observable_dict((str, str), "preferences")
        prefs["language"] = "en"

        # Assert - model should be updated
        assert_that(profile.preferences).contains_key("language")

        # Act - undo
        proxy.undo("preferences")

        # Assert - model should be reverted
        assert_that(profile.preferences).does_not_contain_key("language")
