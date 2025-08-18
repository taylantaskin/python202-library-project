# test_library_simple.py
import pytest
import os
from pathlib import Path
from unittest.mock import patch, Mock
from library import Library
from book import Book


class TestLibrary:
    @pytest.fixture
    def temp_library(self):
        """Creates a temporary library for testing"""
        test_file = "test_temp_library.json"
        lib = Library(data_file=test_file)
        yield lib
        # Cleanup
        if Path(test_file).exists():
            Path(test_file).unlink()

    def test_library_init(self, temp_library):
        """Test library initialization"""
        assert isinstance(temp_library.books, list)
        assert temp_library.data_file == "test_temp_library.json"

    def test_add_and_find_book(self, temp_library):
        """Test adding and finding a book"""
        book = Book("Test Book", "Test Author", "1234567890")
        temp_library.add_book(book)

        # Find book
        found = temp_library.find_book("1234567890")
        assert found is not None
        assert found.title == "Test Book"
        assert found.author == "Test Author"

    def test_duplicate_book_error(self, temp_library):
        """Test duplicate ISBN error"""
        book1 = Book("Book 1", "Author 1", "1234567890")
        book2 = Book("Book 2", "Author 2", "1234567890")

        temp_library.add_book(book1)

        with pytest.raises(ValueError, match="already exists"):
            temp_library.add_book(book2)

    def test_remove_book(self, temp_library):
        """Test removing a book"""
        book = Book("Test Book", "Test Author", "1234567890")
        temp_library.add_book(book)

        temp_library.remove_book("1234567890")

        found = temp_library.find_book("1234567890")
        assert found is None

    def test_remove_nonexistent_book(self, temp_library):
        """Test removing a non-existent book"""
        with pytest.raises(ValueError, match="No book found"):
            temp_library.remove_book("9999999999")

    @patch('httpx.Client')
    def test_add_book_from_isbn_success(self, mock_client, temp_library):
        """Test adding a book from ISBN via API (success case)"""
        # Mock book response
        mock_book_response = Mock()
        mock_book_response.status_code = 200
        mock_book_response.json.return_value = {
            'title': 'Test API Book',
            'authors': [{'key': '/authors/OL123A'}]
        }
        mock_book_response.raise_for_status.return_value = None

        # Mock author response
        mock_author_response = Mock()
        mock_author_response.status_code = 200
        mock_author_response.json.return_value = {
            'name': 'Test Author'
        }

        # Configure mock client
        mock_client_instance = mock_client.return_value.__enter__.return_value
        mock_client_instance.get.side_effect = [mock_book_response, mock_author_response]

        # Test the method
        result = temp_library.add_book_from_isbn("9780123456789")

        assert result == True
        assert len(temp_library.books) == 1

        added_book = temp_library.books[0]
        assert added_book.title == "Test API Book"
        assert added_book.author == "Test Author"
        assert added_book.isbn == "9780123456789"

    @patch('httpx.Client')
    def test_add_book_from_isbn_not_found(self, mock_client, temp_library):
        """Test book not found in API"""
        mock_response = Mock()
        mock_response.status_code = 404

        mock_client_instance = mock_client.return_value.__enter__.return_value
        mock_client_instance.get.return_value = mock_response

        with pytest.raises(ValueError, match="not found in Open Library"):
            temp_library.add_book_from_isbn("9999999999999")

    def test_list_books(self, temp_library):
        """Test listing books"""
        book1 = Book("Book 1", "Author 1", "1111111111")
        book2 = Book("Book 2", "Author 2", "2222222222")

        temp_library.add_book(book1)
        temp_library.add_book(book2)

        books = temp_library.list_books()
        assert len(books) == 2

        titles = [b.title for b in books]
        assert "Book 1" in titles
        assert "Book 2" in titles

    def test_save_and_load_persistence(self, temp_library):
        """Test data persistence"""
        # Add a book
        book = Book("Persistent Book", "Persistent Author", "1234567890")
        temp_library.add_book(book)

        # Create a new Library instance (loads from the same file)
        new_library = Library(data_file=temp_library.data_file)

        # Verify data was loaded
        assert len(new_library.books) == 1
        assert new_library.books[0].title == "Persistent Book"
        assert new_library.books[0].author == "Persistent Author"
        assert new_library.books[0].isbn == "1234567890"

# Run with: pytest test_book.py -v
