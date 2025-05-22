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
