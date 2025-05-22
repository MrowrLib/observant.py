from dataclasses import dataclass

from assertpy import assert_that

from observant import ObservableProxy


@dataclass
class Zoo:
    name: str
    animals: list[str]
    metadata: dict[str, str]


@dataclass
class UserProfile:
    username: str
    preferences: dict[str, str]
    age: int


class TestObservableProxyDict:
    """Unit tests for dictionary operations in ObservableProxy class."""

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
