# test_library.py
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch
from library import Library
from book import Book


@pytest.fixture
def temp_library(tmp_path):
    """Create a temporary library for testing."""
    test_file = tmp_path / "test_library.json"
    return Library(data_file=str(test_file))


@pytest.fixture
def sample_book():
    """Create a sample book for testing."""
    return Book(title="Test Book", author="Test Author", isbn="1234567890")


class TestLibrary:
    """Test cases for Library class."""

    def test_library_initialization(self, temp_library):
        """Test library initializes with empty book list."""
        assert isinstance(temp_library.books, list)
        assert len(temp_library.books) == 0

    def test_add_book_manual(self, temp_library, sample_book):
        """Test adding a book manually."""
        temp_library.add_book(sample_book)
        assert len(temp_library.books) == 1
        assert temp_library.books[0].isbn == "1234567890"

    def test_add_duplicate_book(self, temp_library, sample_book):
        """Test adding duplicate book raises ValueError."""
        temp_library.add_book(sample_book)

        with pytest.raises(ValueError, match="already exists"):
            temp_library.add_book(sample_book)

    def test_remove_book(self, temp_library, sample_book):
        """Test removing a book."""
        temp_library.add_book(sample_book)
        temp_library.remove_book("1234567890")
        assert len(temp_library.books) == 0

    def test_remove_nonexistent_book(self, temp_library):
        """Test removing non-existent book raises ValueError."""
        with pytest.raises(ValueError, match="No book found"):
            temp_library.remove_book("9999999999")

    def test_find_book(self, temp_library, sample_book):
        """Test finding a book by ISBN."""
        temp_library.add_book(sample_book)
        found_book = temp_library.find_book("1234567890")
        assert found_book is not None
        assert found_book.title == "Test Book"

    def test_find_nonexistent_book(self, temp_library):
        """Test finding non-existent book returns None."""
        found_book = temp_library.find_book("9999999999")
        assert found_book is None

    def test_list_books(self, temp_library, sample_book):
        """Test listing books returns a copy."""
        temp_library.add_book(sample_book)
        books_list = temp_library.list_books()

        # Should return a list with one book
        assert len(books_list) == 1

        # Should be a copy, not the original list
        assert books_list is not temp_library.books

    def test_save_and_load_books(self, tmp_path):
        """Test saving and loading books from JSON file."""
        test_file = tmp_path / "test_save_load.json"
        library1 = Library(data_file=str(test_file))

        # Add a book and save
        book = Book(title="Save Test", author="Load Test", isbn="1111111111")
        library1.add_book(book)

        # Create new library instance and check if book is loaded
        library2 = Library(data_file=str(test_file))
        assert len(library2.books) == 1
        assert library2.books[0].title == "Save Test"


class TestAPIIntegration:
    """Test cases for API integration."""

    @patch('httpx.Client')
    def test_fetch_book_from_api_success(self, mock_client_class, temp_library):
        """Test successful API call."""
        # Mock the HTTP client
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # Mock the main book response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "title": "The Great Gatsby",
            "authors": [{"key": "/authors/OL123456A"}]
        }

        # Mock the author response
        mock_author_response = Mock()
        mock_author_response.status_code = 200
        mock_author_response.json.return_value = {
            "name": "F. Scott Fitzgerald"
        }

        # Setup mock to return different responses for different URLs
        def mock_get(url, timeout=None):
            if "isbn" in url:
                return mock_response
            elif "authors" in url:
                return mock_author_response
            return Mock()

        mock_client.get.side_effect = mock_get

        # Test the method
        result = temp_library.fetch_book_from_api("9780743273565")

        assert result is not None
        assert result["title"] == "The Great Gatsby"
        assert result["author"] == "F. Scott Fitzgerald"
        assert result["isbn"] == "9780743273565"

    @patch('httpx.Client')
    def test_fetch_book_from_api_not_found(self, mock_client_class, temp_library):
        """Test API call when book is not found."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        mock_response = Mock()
        mock_response.status_code = 404
        mock_client.get.return_value = mock_response

        result = temp_library.fetch_book_from_api("9999999999")
        assert result is None

    @patch('httpx.Client')
    def test_fetch_book_from_api_network_error(self, mock_client_class, temp_library):
        """Test API call with network error."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        import httpx
        mock_client.get.side_effect = httpx.RequestError("Network error")

        result = temp_library.fetch_book_from_api("1234567890")
        assert result is None

    @patch('httpx.Client')
    def test_add_book_from_isbn_success(self, mock_client_class, temp_library):
        """Test adding book from ISBN successfully."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "title": "Test API Book",
            "authors": [{"key": "/authors/OL123456A"}]
        }

        mock_author_response = Mock()
        mock_author_response.status_code = 200
        mock_author_response.json.return_value = {"name": "API Test Author"}

        def mock_get(url, timeout=None):
            if "isbn" in url:
                return mock_response
            elif "authors" in url:
                return mock_author_response
            return Mock()

        mock_client.get.side_effect = mock_get

        # Test adding book from ISBN
        result = temp_library.add_book_from_isbn("1234567890")

        assert result is True
        assert len(temp_library.books) == 1
        assert temp_library.books[0].title == "Test API Book"
        assert temp_library.books[0].author == "API Test Author"

    def test_add_book_from_isbn_duplicate(self, temp_library, sample_book):
        """Test adding book from ISBN when ISBN already exists."""
        temp_library.add_book(sample_book)

        with pytest.raises(ValueError, match="already exists"):
            temp_library.add_book_from_isbn("1234567890")

    @patch('httpx.Client')
    def test_add_book_from_isbn_not_found(self, mock_client_class, temp_library):
        """Test adding book from ISBN when book is not found in API."""
        mock_client = Mock()
        mock_client_class.return_value.__enter__.return_value = mock_client

        mock_response = Mock()
        mock_response.status_code = 404
        mock_client.get.return_value = mock_response

        with pytest.raises(ValueError, match="not found in Open Library"):
            temp_library.add_book_from_isbn("9999999999")

# Run tests with: python -m pytest test_library.py -v