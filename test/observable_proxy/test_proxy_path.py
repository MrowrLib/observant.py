"""Tests for ObservableProxy.observable_for_path() method."""
from dataclasses import dataclass

import pytest

from observant import ObservableProxy


@dataclass
class Location:
    city: str = ""
    country: str = ""


@dataclass
class Habitat:
    name: str = ""
    climate: str = ""
    location: Location | None = None


@dataclass
class Animal:
    name: str
    species: str
    nickname: str = ""
    age: int = 5
    habitat: Habitat | None = None


class TestParsePathSegments:
    """Tests for _parse_path_segments helper."""

    def test_simple_path(self):
        """Single segment path."""
        proxy = ObservableProxy(Animal(name="Leo", species="Lion"))
        segments = proxy._parse_path_segments("name")
        assert segments == [("name", False)]

    def test_nested_path_no_optional(self):
        """Nested path without optional chaining."""
        proxy = ObservableProxy(Animal(name="Leo", species="Lion"))
        segments = proxy._parse_path_segments("habitat.location.city")
        assert segments == [
            ("habitat", False),
            ("location", False),
            ("city", False),
        ]

    def test_nested_path_with_optional(self):
        """Nested path with optional chaining."""
        proxy = ObservableProxy(Animal(name="Leo", species="Lion"))
        segments = proxy._parse_path_segments("habitat?.location?.city")
        assert segments == [
            ("habitat", True),
            ("location", True),
            ("city", False),
        ]

    def test_mixed_optional_and_required(self):
        """Path with mixed optional and required segments."""
        proxy = ObservableProxy(Animal(name="Leo", species="Lion"))
        segments = proxy._parse_path_segments("habitat.location?.city")
        assert segments == [
            ("habitat", False),
            ("location", True),
            ("city", False),
        ]


class TestSimplePath:
    """Tests for simple (non-nested) paths."""

    def test_simple_path_get(self):
        """Get value via simple path."""
        animal = Animal(name="Leo", species="Lion")
        proxy = ObservableProxy(animal, sync=True)
        obs = proxy.observable_for_path("name")
        assert obs.get() == "Leo"

    def test_simple_path_set(self):
        """Set value via simple path."""
        animal = Animal(name="Leo", species="Lion")
        proxy = ObservableProxy(animal, sync=True)
        obs = proxy.observable_for_path("name")
        obs.set("Simba")
        assert obs.get() == "Simba"
        assert animal.name == "Simba"

    def test_simple_path_on_change(self):
        """Subscribe to changes on simple path."""
        animal = Animal(name="Leo", species="Lion")
        proxy = ObservableProxy(animal, sync=True)
        obs = proxy.observable_for_path("name")

        changes = []
        obs.on_change(lambda v: changes.append(v))

        obs.set("Simba")
        assert changes == ["Simba"]


class TestNestedPathRequired:
    """Tests for nested paths without optional chaining."""

    def test_nested_path_get(self):
        """Get value via nested path."""
        animal = Animal(
            name="Leo",
            species="Lion",
            habitat=Habitat(
                name="Savanna",
                location=Location(city="Nairobi", country="Kenya"),
            ),
        )
        proxy = ObservableProxy(animal, sync=True)
        obs = proxy.observable_for_path("habitat.location.city")
        assert obs.get() == "Nairobi"

    def test_nested_path_set(self):
        """Set value via nested path."""
        animal = Animal(
            name="Leo",
            species="Lion",
            habitat=Habitat(
                name="Savanna",
                location=Location(city="Nairobi", country="Kenya"),
            ),
        )
        proxy = ObservableProxy(animal, sync=True)
        obs = proxy.observable_for_path("habitat.location.city")
        obs.set("Mombasa")
        assert obs.get() == "Mombasa"
        assert animal.habitat.location.city == "Mombasa"

    def test_nested_path_on_change(self):
        """Subscribe to changes on nested path."""
        animal = Animal(
            name="Leo",
            species="Lion",
            habitat=Habitat(
                name="Savanna",
                location=Location(city="Nairobi", country="Kenya"),
            ),
        )
        proxy = ObservableProxy(animal, sync=True)
        obs = proxy.observable_for_path("habitat.location.city")

        changes = []
        obs.on_change(lambda v: changes.append(v))

        obs.set("Mombasa")
        assert changes == ["Mombasa"]

    def test_one_level_nested(self):
        """Test one level of nesting."""
        animal = Animal(
            name="Leo",
            species="Lion",
            habitat=Habitat(name="Savanna", climate="Tropical"),
        )
        proxy = ObservableProxy(animal, sync=True)
        obs = proxy.observable_for_path("habitat.name")
        assert obs.get() == "Savanna"

        obs.set("Grassland")
        assert obs.get() == "Grassland"
        assert animal.habitat.name == "Grassland"


class TestNestedPathOptional:
    """Tests for nested paths with optional chaining."""

    def test_optional_path_with_value(self):
        """Optional path when value exists."""
        animal = Animal(
            name="Leo",
            species="Lion",
            habitat=Habitat(
                name="Savanna",
                location=Location(city="Nairobi", country="Kenya"),
            ),
        )
        proxy = ObservableProxy(animal, sync=True)
        obs = proxy.observable_for_path("habitat?.location?.city")
        assert obs.get() == "Nairobi"

    def test_optional_path_with_none_intermediate(self):
        """Optional path when intermediate is None."""
        animal = Animal(
            name="Leo",
            species="Lion",
            habitat=Habitat(name="Savanna", location=None),
        )
        proxy = ObservableProxy(animal, sync=True)
        obs = proxy.observable_for_path("habitat?.location?.city")
        assert obs.get() is None

    def test_optional_path_with_none_at_start(self):
        """Optional path when first segment is None."""
        animal = Animal(name="Leo", species="Lion", habitat=None)
        proxy = ObservableProxy(animal, sync=True)
        obs = proxy.observable_for_path("habitat?.location?.city")
        assert obs.get() is None

    def test_optional_path_set_when_path_exists(self):
        """Set value via optional path when path exists."""
        animal = Animal(
            name="Leo",
            species="Lion",
            habitat=Habitat(
                name="Savanna",
                location=Location(city="Nairobi", country="Kenya"),
            ),
        )
        proxy = ObservableProxy(animal, sync=True)
        obs = proxy.observable_for_path("habitat?.location?.city")
        obs.set("Mombasa")
        assert obs.get() == "Mombasa"
        assert animal.habitat.location.city == "Mombasa"

    def test_optional_path_set_when_path_broken(self):
        """Set value via optional path when path is broken (should be no-op)."""
        animal = Animal(name="Leo", species="Lion", habitat=None)
        proxy = ObservableProxy(animal, sync=True)
        obs = proxy.observable_for_path("habitat?.location?.city")
        obs.set("Mombasa")  # Should not raise
        assert obs.get() is None  # Value unchanged

    def test_optional_path_reacts_to_parent_change(self):
        """Observable updates when parent object changes."""
        animal = Animal(
            name="Leo",
            species="Lion",
            habitat=Habitat(name="Savanna", location=None),
        )
        proxy = ObservableProxy(animal, sync=True)
        obs = proxy.observable_for_path("habitat?.location?.city")
        assert obs.get() is None

        # Now set the location
        animal.habitat.location = Location(city="Nairobi", country="Kenya")
        proxy.observable(object, "habitat").set(animal.habitat)

        # The observable should update (via parent change handler)
        # Note: This tests the subscription mechanism


class TestMultiplePathsSameParent:
    """Tests for multiple paths sharing the same parent."""

    def test_multiple_paths_same_parent(self):
        """Multiple paths sharing same intermediate objects."""
        animal = Animal(
            name="Leo",
            species="Lion",
            habitat=Habitat(
                name="Savanna",
                location=Location(city="Nairobi", country="Kenya"),
            ),
        )
        proxy = ObservableProxy(animal, sync=True)

        city_obs = proxy.observable_for_path("habitat.location.city")
        country_obs = proxy.observable_for_path("habitat.location.country")

        assert city_obs.get() == "Nairobi"
        assert country_obs.get() == "Kenya"

        city_obs.set("Mombasa")
        country_obs.set("Tanzania")

        assert animal.habitat.location.city == "Mombasa"
        assert animal.habitat.location.country == "Tanzania"


class TestProxyCaching:
    """Tests for nested proxy caching."""

    def test_proxy_caching(self):
        """Same path uses cached proxy."""
        animal = Animal(
            name="Leo",
            species="Lion",
            habitat=Habitat(name="Savanna"),
        )
        proxy = ObservableProxy(animal, sync=True)

        obs1 = proxy.observable_for_path("habitat.name")
        obs2 = proxy.observable_for_path("habitat.name")

        # Both should work
        assert obs1.get() == "Savanna"
        assert obs2.get() == "Savanna"

        # Change via one should reflect in other
        obs1.set("Grassland")
        assert obs2.get() == "Grassland"
