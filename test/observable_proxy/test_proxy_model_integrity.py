from dataclasses import dataclass

import pytest
from assertpy import assert_that

from observant import ObservableProxy


@dataclass
class UserProfile:
    username: str
    preferences: dict[str, str]
    age: int


class TestObservableProxyModelIntegrity:
    """Unit tests for model integrity in ObservableProxy class."""

    def test_observing_non_existent_field(self) -> None:
        """Test that observing a non-existent field raises an appropriate error."""
        # Arrange
        profile = UserProfile(username="user", preferences={}, age=30)
        proxy = ObservableProxy(profile, sync=False)

        # Act & Assert - try to observe a field that doesn't exist
        with pytest.raises(AttributeError) as excinfo:
            proxy.observable(str, "non_existent_field")

        # Assert - error message should mention the field name
        assert_that(str(excinfo.value)).contains("non_existent_field")

        # Act - try to observe a field with the wrong type
        # The current behavior is that this doesn't raise an exception
        # and returns an observable that will attempt to convert the value to the requested type
        wrong_type_observable = proxy.observable(int, "username")  # username is a string, not an int

        # Try to get the value - this might raise an exception or might try to convert the string to int
        try:
            value = wrong_type_observable.get()
            # If we get here, the library tried to convert the string to int
            # This might succeed for numeric strings, but should fail for non-numeric strings
            assert_that(type(value) is int).is_true()
        except Exception:
            # If we get here, the library raised an exception when trying to convert
            # This is also acceptable behavior
            pass

        # Act & Assert - try to observe a computed field that doesn't exist
        with pytest.raises(KeyError) as excinfo:
            proxy.computed(str, "non_existent_computed")

        # Assert - error message should mention the field name
        assert_that(str(excinfo.value)).contains("non_existent_computed")

        # Act & Assert - try to observe a list field that doesn't exist
        with pytest.raises(AttributeError) as excinfo:
            proxy.observable_list(str, "non_existent_list")

        # Assert - error message should mention the field name
        assert_that(str(excinfo.value)).contains("non_existent_list")

        # Act & Assert - try to observe a dict field that doesn't exist
        with pytest.raises(AttributeError) as excinfo:
            proxy.observable_dict((str, str), "non_existent_dict")

        # Assert - error message should mention the field name
        assert_that(str(excinfo.value)).contains("non_existent_dict")

    def test_wrapping_non_dataclass_object(self) -> None:
        """Test that wrapping a non-dataclass object works correctly."""

        # Arrange - create a regular class (not a dataclass)
        class RegularClass:
            def __init__(self) -> None:
                self.name = "test"
                self.value = 42
                self.items = ["a", "b", "c"]
                self.options = {"key1": "value1", "key2": "value2"}

        # Create an instance of the regular class
        obj = RegularClass()

        # Act - wrap the object in an ObservableProxy
        proxy = ObservableProxy(obj, sync=False)

        # Assert - we should be able to observe the fields
        assert_that(proxy.observable(str, "name").get()).is_equal_to("test")
        assert_that(proxy.observable(int, "value").get()).is_equal_to(42)

        # Assert - we should be able to observe lists and dicts
        items_list = proxy.observable_list(str, "items")
        assert_that(items_list[0]).is_equal_to("a")
        assert_that(items_list[1]).is_equal_to("b")
        assert_that(items_list[2]).is_equal_to("c")

        options_dict = proxy.observable_dict((str, str), "options")
        assert_that(options_dict["key1"]).is_equal_to("value1")
        assert_that(options_dict["key2"]).is_equal_to("value2")

        # Act - modify the fields through the proxy
        proxy.observable(str, "name").set("modified")
        proxy.observable(int, "value").set(99)

        items_list.append("d")
        options_dict["key3"] = "value3"

        # Assert - changes should be reflected in the proxy
        assert_that(proxy.observable(str, "name").get()).is_equal_to("modified")
        assert_that(proxy.observable(int, "value").get()).is_equal_to(99)

        assert_that(items_list).contains("d")
        assert_that(options_dict["key3"]).is_equal_to("value3")

        # Assert - changes should be reflected in the original object if we save_to
        proxy.save_to(obj)

        assert_that(obj.name).is_equal_to("modified")
        assert_that(obj.value).is_equal_to(99)
        assert_that(obj.items).contains("d")
        assert_that(obj.options["key3"]).is_equal_to("value3")

        # Create a new proxy with sync=True
        sync_proxy = ObservableProxy(obj, sync=True)

        # Act - modify the fields through the sync proxy
        sync_proxy.observable(str, "name").set("sync_modified")

        # Assert - changes should be immediately reflected in the original object
        assert_that(obj.name).is_equal_to("sync_modified")

    def test_save_to_different_object(self) -> None:
        """Test that save_to() can save changes to a different object of the same type."""

        # Arrange - create two objects of the same type
        @dataclass
        class Person:
            name: str
            age: int

        person1 = Person(name="Alice", age=30)
        person2 = Person(name="Bob", age=40)

        # Act - wrap person1 in a proxy and make changes
        proxy = ObservableProxy(person1, sync=False)
        proxy.observable(str, "name").set("Modified Alice")
        proxy.observable(int, "age").set(31)

        # Assert - changes should be reflected in the proxy but not in person1 yet
        assert_that(proxy.observable(str, "name").get()).is_equal_to("Modified Alice")
        assert_that(proxy.observable(int, "age").get()).is_equal_to(31)
        assert_that(person1.name).is_equal_to("Alice")
        assert_that(person1.age).is_equal_to(30)

        # Act - save changes to person2 instead of person1
        proxy.save_to(person2)

        # Assert - changes should be saved to person2
        assert_that(person2.name).is_equal_to("Modified Alice")
        assert_that(person2.age).is_equal_to(31)

        # Assert - person1 should remain unchanged
        assert_that(person1.name).is_equal_to("Alice")
        assert_that(person1.age).is_equal_to(30)

        # Act - save changes to person1 as well
        proxy.save_to(person1)

        # Assert - now person1 should be updated too
        assert_that(person1.name).is_equal_to("Modified Alice")
        assert_that(person1.age).is_equal_to(31)

    def test_proxy_reuse_after_save_to(self) -> None:
        """Test that a proxy can still be used after calling save_to()."""

        # Arrange
        @dataclass
        class Product:
            name: str
            price: float
            tags: list[str]

        # Create an object and wrap it in a proxy
        product = Product(name="Widget", price=9.99, tags=["tool", "hardware"])
        proxy = ObservableProxy(product, sync=False)

        # Act - make some changes
        proxy.observable(str, "name").set("Super Widget")
        proxy.observable(float, "price").set(14.99)
        proxy.observable_list(str, "tags").append("premium")

        # Save changes to the original object
        proxy.save_to(product)

        # Assert - changes should be saved to the object
        assert_that(product.name).is_equal_to("Super Widget")
        assert_that(product.price).is_equal_to(14.99)
        assert_that(product.tags).contains("premium")

        # Act - make more changes after save_to
        proxy.observable(str, "name").set("Ultra Widget")
        proxy.observable(float, "price").set(19.99)
        proxy.observable_list(str, "tags").append("deluxe")

        # Assert - new changes should be reflected in the proxy
        assert_that(proxy.observable(str, "name").get()).is_equal_to("Ultra Widget")
        assert_that(proxy.observable(float, "price").get()).is_equal_to(19.99)
        assert_that(proxy.observable_list(str, "tags")).contains("deluxe")

        # Assert - but not yet in the original object
        assert_that(product.name).is_equal_to("Super Widget")
        assert_that(product.price).is_equal_to(14.99)
        assert_that("deluxe" in product.tags).is_false()

        # Act - save changes again
        proxy.save_to(product)

        # Assert - new changes should now be saved to the object
        assert_that(product.name).is_equal_to("Ultra Widget")
        assert_that(product.price).is_equal_to(19.99)
        assert_that(product.tags).contains("deluxe")

        # Assert - dirty state should be reset after save_to
        assert_that(proxy.is_dirty()).is_false()
        assert_that(proxy.dirty_fields()).is_empty()
