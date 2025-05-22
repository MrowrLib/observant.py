from assertpy import assert_that

from observant import (
    ObservableCollectionChangeType,
    ObservableDict,
    ObservableDictChange,
    ObservableList,
    ObservableListChange,
)


class TestObservableList:
    """Unit tests for the ObservableList class."""

    def test_init_default(self) -> None:
        """Test creating an ObservableList with default values."""
        observable_list = ObservableList[int]()
        assert_that(len(observable_list)).is_equal_to(0)
        assert_that(list(observable_list)).is_empty()

    def test_init_with_items(self) -> None:
        """Test creating an ObservableList with initial items."""
        initial_items = [1, 2, 3]
        observable_list = ObservableList[int](initial_items)
        assert_that(len(observable_list)).is_equal_to(3)
        assert_that(list(observable_list)).is_equal_to(initial_items)

    def test_append(self) -> None:
        """Test appending an item to an ObservableList."""
        # Arrange
        observable_list = ObservableList[int]()
        changes: list[ObservableListChange[int]] = []
        observable_list.on_change(lambda change: changes.append(change))

        # Act
        observable_list.append(42)

        # Assert
        assert_that(len(observable_list)).is_equal_to(1)
        assert_that(observable_list[0]).is_equal_to(42)
        assert_that(changes).is_length(1)
        assert_that(changes[0].type).is_equal_to(ObservableCollectionChangeType.ADD)
        assert_that(changes[0].index).is_equal_to(0)
        assert_that(changes[0].item).is_equal_to(42)

    def test_extend(self) -> None:
        """Test extending an ObservableList with multiple items."""
        # Arrange
        observable_list = ObservableList[int]()
        changes: list[ObservableListChange[int]] = []
        observable_list.on_change(lambda change: changes.append(change))

        # Act
        observable_list.extend([1, 2, 3])

        # Assert
        assert_that(len(observable_list)).is_equal_to(3)
        assert_that(list(observable_list)).is_equal_to([1, 2, 3])
        assert_that(changes).is_length(1)
        assert_that(changes[0].type).is_equal_to(ObservableCollectionChangeType.ADD)
        assert_that(changes[0].index).is_equal_to(0)
        assert_that(changes[0].items).is_equal_to([1, 2, 3])

    def test_insert(self) -> None:
        """Test inserting an item into an ObservableList."""
        # Arrange
        observable_list = ObservableList[int]([1, 3])
        changes: list[ObservableListChange[int]] = []
        observable_list.on_change(lambda change: changes.append(change))

        # Act
        observable_list.insert(1, 2)

        # Assert
        assert_that(len(observable_list)).is_equal_to(3)
        assert_that(list(observable_list)).is_equal_to([1, 2, 3])
        assert_that(changes).is_length(1)
        assert_that(changes[0].type).is_equal_to(ObservableCollectionChangeType.ADD)
        assert_that(changes[0].index).is_equal_to(1)
        assert_that(changes[0].item).is_equal_to(2)

    def test_remove(self) -> None:
        """Test removing an item from an ObservableList."""
        # Arrange
        observable_list = ObservableList[int]([1, 2, 3])
        changes: list[ObservableListChange[int]] = []
        observable_list.on_change(lambda change: changes.append(change))

        # Act
        observable_list.remove(2)

        # Assert
        assert_that(len(observable_list)).is_equal_to(2)
        assert_that(list(observable_list)).is_equal_to([1, 3])
        assert_that(changes).is_length(1)
        assert_that(changes[0].type).is_equal_to(ObservableCollectionChangeType.REMOVE)
        assert_that(changes[0].index).is_equal_to(1)
        assert_that(changes[0].item).is_equal_to(2)

    def test_pop(self) -> None:
        """Test popping an item from an ObservableList."""
        # Arrange
        observable_list = ObservableList[int]([1, 2, 3])
        changes: list[ObservableListChange[int]] = []
        observable_list.on_change(lambda change: changes.append(change))

        # Act
        item = observable_list.pop()

        # Assert
        assert_that(item).is_equal_to(3)
        assert_that(len(observable_list)).is_equal_to(2)
        assert_that(list(observable_list)).is_equal_to([1, 2])
        assert_that(changes).is_length(1)
        assert_that(changes[0].type).is_equal_to(ObservableCollectionChangeType.REMOVE)
        assert_that(changes[0].index).is_equal_to(-1)
        assert_that(changes[0].item).is_equal_to(3)

    def test_pop_with_index(self) -> None:
        """Test popping an item from an ObservableList with a specific index."""
        # Arrange
        observable_list = ObservableList[int]([1, 2, 3])
        changes: list[ObservableListChange[int]] = []
        observable_list.on_change(lambda change: changes.append(change))

        # Act
        item = observable_list.pop(1)

        # Assert
        assert_that(item).is_equal_to(2)
        assert_that(len(observable_list)).is_equal_to(2)
        assert_that(list(observable_list)).is_equal_to([1, 3])
        assert_that(changes).is_length(1)
        assert_that(changes[0].type).is_equal_to(ObservableCollectionChangeType.REMOVE)
        assert_that(changes[0].index).is_equal_to(1)
        assert_that(changes[0].item).is_equal_to(2)

    def test_clear(self) -> None:
        """Test clearing an ObservableList."""
        # Arrange
        observable_list = ObservableList[int]([1, 2, 3])
        changes: list[ObservableListChange[int]] = []
        observable_list.on_change(lambda change: changes.append(change))

        # Act
        observable_list.clear()

        # Assert
        assert_that(len(observable_list)).is_equal_to(0)
        assert_that(list(observable_list)).is_empty()
        assert_that(changes).is_length(1)
        assert_that(changes[0].type).is_equal_to(ObservableCollectionChangeType.CLEAR)
        assert_that(changes[0].items).is_equal_to([1, 2, 3])

    def test_setitem(self) -> None:
        """Test setting an item in an ObservableList."""
        # Arrange
        observable_list = ObservableList[int]([1, 2, 3])
        changes: list[ObservableListChange[int]] = []
        observable_list.on_change(lambda change: changes.append(change))

        # Act
        observable_list[1] = 42

        # Assert
        assert_that(len(observable_list)).is_equal_to(3)
        assert_that(list(observable_list)).is_equal_to([1, 42, 3])
        assert_that(changes).is_length(2)
        assert_that(changes[0].type).is_equal_to(ObservableCollectionChangeType.REMOVE)
        assert_that(changes[0].index).is_equal_to(1)
        assert_that(changes[0].item).is_equal_to(2)
        assert_that(changes[1].type).is_equal_to(ObservableCollectionChangeType.ADD)
        assert_that(changes[1].index).is_equal_to(1)
        assert_that(changes[1].item).is_equal_to(42)

    def test_setitem_slice(self) -> None:
        """Test setting a slice of items in an ObservableList."""
        # Arrange
        observable_list = ObservableList[int]([1, 2, 3, 4, 5])
        changes: list[ObservableListChange[int]] = []
        observable_list.on_change(lambda change: changes.append(change))

        # Act
        observable_list[1:4] = [42, 43]

        # Assert
        assert_that(len(observable_list)).is_equal_to(4)
        assert_that(list(observable_list)).is_equal_to([1, 42, 43, 5])
        assert_that(changes).is_length(2)
        assert_that(changes[0].type).is_equal_to(ObservableCollectionChangeType.REMOVE)
        assert_that(changes[0].index).is_equal_to(1)
        assert_that(changes[0].items).is_equal_to([2, 3, 4])
        assert_that(changes[1].type).is_equal_to(ObservableCollectionChangeType.ADD)
        assert_that(changes[1].index).is_equal_to(1)
        assert_that(changes[1].items).is_equal_to([42, 43])

    def test_delitem(self) -> None:
        """Test deleting an item from an ObservableList."""
        # Arrange
        observable_list = ObservableList[int]([1, 2, 3])
        changes: list[ObservableListChange[int]] = []
        observable_list.on_change(lambda change: changes.append(change))

        # Act
        del observable_list[1]

        # Assert
        assert_that(len(observable_list)).is_equal_to(2)
        assert_that(list(observable_list)).is_equal_to([1, 3])
        assert_that(changes).is_length(1)
        assert_that(changes[0].type).is_equal_to(ObservableCollectionChangeType.REMOVE)
        assert_that(changes[0].index).is_equal_to(1)
        assert_that(changes[0].item).is_equal_to(2)

    def test_delitem_slice(self) -> None:
        """Test deleting a slice of items from an ObservableList."""
        # Arrange
        observable_list = ObservableList[int]([1, 2, 3, 4, 5])
        changes: list[ObservableListChange[int]] = []
        observable_list.on_change(lambda change: changes.append(change))

        # Act
        del observable_list[1:4]

        # Assert
        assert_that(len(observable_list)).is_equal_to(2)
        assert_that(list(observable_list)).is_equal_to([1, 5])
        assert_that(changes).is_length(1)
        assert_that(changes[0].type).is_equal_to(ObservableCollectionChangeType.REMOVE)
        assert_that(changes[0].index).is_equal_to(1)
        assert_that(changes[0].items).is_equal_to([2, 3, 4])

    def test_sort(self) -> None:
        """Test sorting an ObservableList."""
        # Arrange
        observable_list = ObservableList[int]([3, 1, 2])
        changes: list[ObservableListChange[int]] = []
        observable_list.on_change(lambda change: changes.append(change))

        # Act
        observable_list.sort()

        # Assert
        assert_that(len(observable_list)).is_equal_to(3)
        assert_that(list(observable_list)).is_equal_to([1, 2, 3])
        assert_that(changes).is_empty()  # No notifications for sort

    def test_reverse(self) -> None:
        """Test reversing an ObservableList."""
        # Arrange
        observable_list = ObservableList[int]([1, 2, 3])
        changes: list[ObservableListChange[int]] = []
        observable_list.on_change(lambda change: changes.append(change))

        # Act
        observable_list.reverse()

        # Assert
        assert_that(len(observable_list)).is_equal_to(3)
        assert_that(list(observable_list)).is_equal_to([3, 2, 1])
        assert_that(changes).is_empty()  # No notifications for reverse


class TestObservableDict:
    """Unit tests for the ObservableDict class."""

    def test_init_default(self) -> None:
        """Test creating an ObservableDict with default values."""
        observable_dict = ObservableDict[str, int]()
        assert_that(len(observable_dict)).is_equal_to(0)
        assert_that(dict(observable_dict.items())).is_empty()

    def test_init_with_items(self) -> None:
        """Test creating an ObservableDict with initial items."""
        initial_items = {"a": 1, "b": 2, "c": 3}
        observable_dict = ObservableDict[str, int](initial_items)
        assert_that(len(observable_dict)).is_equal_to(3)
        assert_that(dict(observable_dict.items())).is_equal_to(initial_items)

    def test_setitem_add(self) -> None:
        """Test adding an item to an ObservableDict using setitem."""
        # Arrange
        observable_dict = ObservableDict[str, int]()
        changes: list[ObservableDictChange[str, int]] = []
        observable_dict.on_change(lambda change: changes.append(change))

        # Act
        observable_dict["a"] = 1

        # Assert
        assert_that(len(observable_dict)).is_equal_to(1)
        assert_that(observable_dict["a"]).is_equal_to(1)
        assert_that(changes).is_length(1)
        assert_that(changes[0].type).is_equal_to(ObservableCollectionChangeType.ADD)
        assert_that(changes[0].key).is_equal_to("a")
        assert_that(changes[0].value).is_equal_to(1)

    def test_setitem_update(self) -> None:
        """Test updating an item in an ObservableDict using setitem."""
        # Arrange
        observable_dict = ObservableDict[str, int]({"a": 1})
        changes: list[ObservableDictChange[str, int]] = []
        observable_dict.on_change(lambda change: changes.append(change))

        # Act
        observable_dict["a"] = 42

        # Assert
        assert_that(len(observable_dict)).is_equal_to(1)
        assert_that(observable_dict["a"]).is_equal_to(42)
        assert_that(changes).is_length(1)
        assert_that(changes[0].type).is_equal_to(ObservableCollectionChangeType.UPDATE)
        assert_that(changes[0].key).is_equal_to("a")
        assert_that(changes[0].value).is_equal_to(42)

    def test_delitem(self) -> None:
        """Test deleting an item from an ObservableDict."""
        # Arrange
        observable_dict = ObservableDict[str, int]({"a": 1, "b": 2})
        changes: list[ObservableDictChange[str, int]] = []
        observable_dict.on_change(lambda change: changes.append(change))

        # Act
        del observable_dict["a"]

        # Assert
        assert_that(len(observable_dict)).is_equal_to(1)
        assert_that("a" in observable_dict).is_false()
        assert_that(changes).is_length(1)
        assert_that(changes[0].type).is_equal_to(ObservableCollectionChangeType.REMOVE)
        assert_that(changes[0].key).is_equal_to("a")
        assert_that(changes[0].value).is_equal_to(1)

    def test_get(self) -> None:
        """Test getting an item from an ObservableDict."""
        # Arrange
        observable_dict = ObservableDict[str, int]({"a": 1})
        changes: list[ObservableDictChange[str, int]] = []
        observable_dict.on_change(lambda change: changes.append(change))

        # Act
        value = observable_dict.get("a")
        default_value = observable_dict.get("b", 42)

        # Assert
        assert_that(value).is_equal_to(1)
        assert_that(default_value).is_equal_to(42)
        assert_that(changes).is_empty()  # No notifications for get

    def test_setdefault_existing(self) -> None:
        """Test setdefault with an existing key."""
        # Arrange
        observable_dict = ObservableDict[str, int]({"a": 1})
        changes: list[ObservableDictChange[str, int]] = []
        observable_dict.on_change(lambda change: changes.append(change))

        # Act
        value = observable_dict.setdefault("a", 42)

        # Assert
        assert_that(value).is_equal_to(1)
        assert_that(observable_dict["a"]).is_equal_to(1)
        assert_that(changes).is_empty()  # No notifications for setdefault with existing key

    def test_setdefault_new(self) -> None:
        """Test setdefault with a new key."""
        # Arrange
        observable_dict = ObservableDict[str, int]()
        changes: list[ObservableDictChange[str, int]] = []
        observable_dict.on_change(lambda change: changes.append(change))

        # Act
        value = observable_dict.setdefault("a", 42)

        # Assert
        assert_that(value).is_equal_to(42)
        assert_that(observable_dict["a"]).is_equal_to(42)
        assert_that(changes).is_length(1)
        assert_that(changes[0].type).is_equal_to(ObservableCollectionChangeType.ADD)
        assert_that(changes[0].key).is_equal_to("a")
        assert_that(changes[0].value).is_equal_to(42)

    def test_pop(self) -> None:
        """Test popping an item from an ObservableDict."""
        # Arrange
        observable_dict = ObservableDict[str, int]({"a": 1, "b": 2})
        changes: list[ObservableDictChange[str, int]] = []
        observable_dict.on_change(lambda change: changes.append(change))

        # Act
        value = observable_dict.pop("a")

        # Assert
        assert_that(value).is_equal_to(1)
        assert_that(len(observable_dict)).is_equal_to(1)
        assert_that("a" in observable_dict).is_false()
        assert_that(changes).is_length(1)
        assert_that(changes[0].type).is_equal_to(ObservableCollectionChangeType.REMOVE)
        assert_that(changes[0].key).is_equal_to("a")
        assert_that(changes[0].value).is_equal_to(1)

    def test_pop_with_default(self) -> None:
        """Test popping a non-existent item from an ObservableDict with a default value."""
        # Arrange
        observable_dict = ObservableDict[str, int]({"a": 1})
        changes: list[ObservableDictChange[str, int]] = []
        observable_dict.on_change(lambda change: changes.append(change))

        # Act
        value = observable_dict.pop("b", 42)

        # Assert
        assert_that(value).is_equal_to(42)
        assert_that(len(observable_dict)).is_equal_to(1)
        assert_that(changes).is_empty()  # No notifications for pop with default

    def test_popitem(self) -> None:
        """Test popping an item from an ObservableDict using popitem."""
        # Arrange
        observable_dict = ObservableDict[str, int]({"a": 1})
        changes: list[ObservableDictChange[str, int]] = []
        observable_dict.on_change(lambda change: changes.append(change))

        # Act
        key, value = observable_dict.popitem()

        # Assert
        assert_that(key).is_equal_to("a")
        assert_that(value).is_equal_to(1)
        assert_that(len(observable_dict)).is_equal_to(0)
        assert_that(changes).is_length(1)
        assert_that(changes[0].type).is_equal_to(ObservableCollectionChangeType.REMOVE)
        assert_that(changes[0].key).is_equal_to("a")
        assert_that(changes[0].value).is_equal_to(1)

    def test_clear(self) -> None:
        """Test clearing an ObservableDict."""
        # Arrange
        observable_dict = ObservableDict[str, int]({"a": 1, "b": 2})
        changes: list[ObservableDictChange[str, int]] = []
        observable_dict.on_change(lambda change: changes.append(change))

        # Act
        observable_dict.clear()

        # Assert
        assert_that(len(observable_dict)).is_equal_to(0)
        assert_that(dict(observable_dict.items())).is_empty()
        assert_that(changes).is_length(1)
        assert_that(changes[0].type).is_equal_to(ObservableCollectionChangeType.CLEAR)
        assert_that(changes[0].items).is_equal_to({"a": 1, "b": 2})

    def test_update(self) -> None:
        """Test updating an ObservableDict with another dictionary."""
        # Arrange
        observable_dict = ObservableDict[str, int]({"a": 1, "b": 2})
        changes: list[ObservableDictChange[str, int]] = []
        observable_dict.on_change(lambda change: changes.append(change))

        # Act
        observable_dict.update({"b": 42, "c": 3})

        # Assert
        assert_that(len(observable_dict)).is_equal_to(3)
        assert_that(dict(observable_dict.items())).is_equal_to({"a": 1, "b": 42, "c": 3})
        assert_that(changes).is_length(2)
        assert_that(changes[0].type).is_equal_to(ObservableCollectionChangeType.ADD)
        assert_that(changes[0].items).is_equal_to({"c": 3})
        assert_that(changes[1].type).is_equal_to(ObservableCollectionChangeType.UPDATE)
        assert_that(changes[1].items).is_equal_to({"b": 42})

    def test_keys(self) -> None:
        """Test getting the keys of an ObservableDict."""
        # Arrange
        observable_dict = ObservableDict[str, int]({"a": 1, "b": 2})
        changes: list[ObservableDictChange[str, int]] = []
        observable_dict.on_change(lambda change: changes.append(change))

        # Act
        keys = observable_dict.keys()

        # Assert
        assert_that(keys).is_equal_to(["a", "b"])
        assert_that(changes).is_empty()  # No notifications for keys

    def test_values(self) -> None:
        """Test getting the values of an ObservableDict."""
        # Arrange
        observable_dict = ObservableDict[str, int]({"a": 1, "b": 2})
        changes: list[ObservableDictChange[str, int]] = []
        observable_dict.on_change(lambda change: changes.append(change))

        # Act
        values = observable_dict.values()

        # Assert
        assert_that(values).is_equal_to([1, 2])
        assert_that(changes).is_empty()  # No notifications for values

    def test_items(self) -> None:
        """Test getting the items of an ObservableDict."""
        # Arrange
        observable_dict = ObservableDict[str, int]({"a": 1, "b": 2})
        changes: list[ObservableDictChange[str, int]] = []
        observable_dict.on_change(lambda change: changes.append(change))

        # Act
        items = observable_dict.items()

        # Assert
        assert_that(items).is_equal_to([("a", 1), ("b", 2)])
        assert_that(changes).is_empty()  # No notifications for items

    def test_copy(self) -> None:
        """Test copying an ObservableDict."""
        # Arrange
        observable_dict = ObservableDict[str, int]({"a": 1, "b": 2})
        changes: list[ObservableDictChange[str, int]] = []
        observable_dict.on_change(lambda change: changes.append(change))

        # Act
        copy = observable_dict.copy()

        # Assert
        assert_that(copy).is_equal_to({"a": 1, "b": 2})
        assert_that(changes).is_empty()  # No notifications for copy
