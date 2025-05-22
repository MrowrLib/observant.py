from dataclasses import dataclass

from assertpy import assert_that

from observant import ObservableProxy


@dataclass
class Library:
    title: str
    books: list[str]


class TestObservableProxyList:
    """Unit tests for list operations in ObservableProxy class."""

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

    def test_list_sync_updates_model_immediately(self) -> None:
        """Test sync=True causes ObservableList to write through to the model."""
        # Arrange
        lib = Library(title="Classic", books=["Odyssey"])
        proxy = ObservableProxy(lib, sync=True)

        # Act
        proxy.observable_list(str, "books").append("Iliad")

        # Assert
        assert_that(lib.books).contains("Odyssey", "Iliad")

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
