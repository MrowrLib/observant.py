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
        prefs = proxy.observable_dict("preferences")
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
        proxy.observable_dict("metadata")["season"] = "autumn"

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
        meta = proxy.observable_dict("metadata")
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
        proxy.observable_dict("metadata")["ticket_price"] = "$15"

        # Assert
        assert_that(zoo.metadata["ticket_price"]).is_equal_to("$15")
