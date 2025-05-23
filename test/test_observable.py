from assertpy import assert_that

from observant import Observable


class TestObservable:
    """Unit tests for the Observable class."""

    def test_get(self) -> None:
        """Test getting the value from an Observable."""
        # Arrange
        observable = Observable[int](42)

        # Act
        value = observable.get()

        # Assert
        assert_that(value).is_equal_to(42)

    def test_set(self) -> None:
        """Test setting the value of an Observable."""
        # Arrange
        observable = Observable[int](42)

        # Act
        observable.set(99)

        # Assert
        assert_that(observable.get()).is_equal_to(99)

    def test_set_with_callback(self) -> None:
        """Test that callbacks are called when the value is set."""
        # Arrange
        observable = Observable[int](42)
        callback_values: list[int] = []
        observable.on_change(lambda value: callback_values.append(value))

        # Act
        observable.set(99)

        # Assert
        assert_that(callback_values).is_length(1)
        assert_that(callback_values[0]).is_equal_to(99)

    def test_set_with_multiple_callbacks(self) -> None:
        """Test that multiple callbacks are called when the value is set."""
        # Arrange
        observable = Observable[int](42)
        callback_values1: list[int] = []
        callback_values2: list[int] = []
        observable.on_change(lambda value: callback_values1.append(value))
        observable.on_change(lambda value: callback_values2.append(value))

        # Act
        observable.set(99)

        # Assert
        assert_that(callback_values1).is_length(1)
        assert_that(callback_values1[0]).is_equal_to(99)
        assert_that(callback_values2).is_length(1)
        assert_that(callback_values2[0]).is_equal_to(99)

    def test_on_change(self) -> None:
        """Test registering a callback with on_change."""
        # Arrange
        observable = Observable[int](42)
        callback_values: list[int] = []

        # Act
        observable.on_change(lambda value: callback_values.append(value))
        observable.set(99)

        # Assert
        assert_that(callback_values).is_length(1)
        assert_that(callback_values[0]).is_equal_to(99)

    def test_with_string_value(self) -> None:
        """Test Observable with a string value."""
        # Arrange
        observable = Observable[str]("hello")
        callback_values: list[str] = []
        observable.on_change(lambda value: callback_values.append(value))

        # Act
        observable.set("world")

        # Assert
        assert_that(observable.get()).is_equal_to("world")
        assert_that(callback_values).is_length(1)
        assert_that(callback_values[0]).is_equal_to("world")

    def test_with_complex_value(self) -> None:
        """Test Observable with a complex value (list)."""
        # Arrange
        observable = Observable[list[int]]([1, 2, 3])
        callback_values: list[list[int]] = []
        observable.on_change(lambda value: callback_values.append(value))

        # Act
        observable.set([4, 5, 6])

        # Assert
        assert_that(observable.get()).is_equal_to([4, 5, 6])
        assert_that(callback_values).is_length(1)
        assert_that(callback_values[0]).is_equal_to([4, 5, 6])

    def test_set_with_notify_false(self) -> None:
        """Test setting the value with notify=False doesn't trigger callbacks."""
        # Arrange
        observable = Observable[int](42)
        callback_values: list[int] = []
        observable.on_change(lambda value: callback_values.append(value))

        # Act
        observable.set(99, notify=False)

        # Assert
        assert_that(observable.get()).is_equal_to(99)  # Value should be updated
        assert_that(callback_values).is_empty()  # But no callbacks should be triggered

        # Verify callbacks still work with default notify=True
        observable.set(100)
        assert_that(callback_values).is_length(1)
        assert_that(callback_values[0]).is_equal_to(100)

    def test_bool_conversion(self) -> None:
        """Test boolean conversion of Observable."""
        # Arrange & Act
        truthy_observable = Observable[int](42)
        falsy_observable = Observable[int](0)

        # Assert
        assert_that(bool(truthy_observable)).is_true()
        assert_that(bool(falsy_observable)).is_false()

        # Test in if statement
        if truthy_observable:
            result_truthy = True
        else:
            result_truthy = False

        if falsy_observable:
            result_falsy = True
        else:
            result_falsy = False

        assert_that(result_truthy).is_true()
        assert_that(result_falsy).is_false()

    def test_str_conversion(self) -> None:
        """Test string conversion of Observable."""
        # Arrange
        observable = Observable[int](42)

        # Act
        string_value = str(observable)

        # Assert
        assert_that(string_value).is_equal_to("42")

    def test_repr_conversion(self) -> None:
        """Test repr conversion of Observable."""
        # Arrange
        int_observable = Observable[int](42)
        str_observable = Observable[str]("hello")

        # Act
        int_repr = repr(int_observable)
        str_repr = repr(str_observable)

        # Assert
        assert_that(int_repr).is_equal_to("Observable(42)")
        assert_that(str_repr).is_equal_to("Observable('hello')")
