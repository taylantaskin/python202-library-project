# test_api.py
import pytest
import json
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from api import app
from library import Library
from book import Book

# Test client
client = TestClient(app)


class TestLibraryAPI:
    @pytest.fixture(autouse=True)
    def setup_and_cleanup(self):
        """Setup and cleanup for each test"""
        # Setup: Create a clean test library
        test_file = "test_api_library.json"
        if Path(test_file).exists():
            Path(test_file).unlink()

        # Override the library instance in the API module
        import api
        api.library = Library(test_file)

        yield

        # Cleanup: Remove test file
        if Path(test_file).exists():
            Path(test_file).unlink()

    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "Welcome to Library Management API" in data["message"]
        assert data["success"] == True

    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "total_books" in data
        assert "api_version" in data

    def test_get_empty_books_list(self):
        """Test getting empty books list"""
        response = client.get("/books")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_books_with_data(self):
        """Test getting books when library has books"""
        # Add a book directly to the library
        import api
        book = Book("Test Book", "Test Author", "1234567890")
        api.library.add_book(book)

        response = client.get("/books")
        assert response.status_code == 200

        books = response.json()
        assert len(books) == 1
        assert books[0]["title"] == "Test Book"
        assert books[0]["author"] == "Test Author"
        assert books[0]["isbn"] == "1234567890"
        assert books[0]["book_type"] == "Book"

    @patch('library.httpx.Client')
    def test_add_book_success(self, mock_client):
        """Test successfully adding a book via ISBN"""
        # Mock API responses
        mock_book_response = Mock()
        mock_book_response.status_code = 200
        mock_book_response.json.return_value = {
            'title': 'The Great Gatsby',
            'authors': [{'key': '/authors/OL123A'}]
        }
        mock_book_response.raise_for_status.return_value = None

        mock_author_response = Mock()
        mock_author_response.status_code = 200
        mock_author_response.json.return_value = {
            'name': 'F. Scott Fitzgerald'
        }

        mock_client_instance = mock_client.return_value.__enter__.return_value
        mock_client_instance.get.side_effect = [mock_book_response, mock_author_response]

        # Test the API
        response = client.post("/books", json={"isbn": "9780743273565"})
        assert response.status_code == 200

        book_data = response.json()
        assert book_data["title"] == "The Great Gatsby"
        assert book_data["author"] == "F. Scott Fitzgerald"
        assert book_data["isbn"] == "9780743273565"

    def test_add_book_invalid_isbn(self):
        """Test adding book with invalid ISBN"""
        with patch('library.Library.add_book_from_isbn') as mock_add:
            mock_add.side_effect = ValueError("Book with ISBN 9999999999 not found in Open Library.")

            response = client.post("/books", json={"isbn": "9999999999"})
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_add_duplicate_book(self):
        """Test adding duplicate book"""
        with patch('library.Library.add_book_from_isbn') as mock_add:
            mock_add.side_effect = ValueError("A book with ISBN 1234567890 already exists.")

            response = client.post("/books", json={"isbn": "1234567890"})
            assert response.status_code == 409
            assert "already exists" in response.json()["detail"]

    def test_get_specific_book(self):
        """Test getting a specific book by ISBN"""
        # Add a book directly
        import api
        book = Book("Specific Book", "Specific Author", "1111111111")
        api.library.add_book(book)

        response = client.get("/books/1111111111")
        assert response.status_code == 200

        book_data = response.json()
        assert book_data["title"] == "Specific Book"
        assert book_data["isbn"] == "1111111111"

    def test_get_nonexistent_book(self):
        """Test getting a book that doesn't exist"""
        response = client.get("/books/9999999999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_delete_book_success(self):
        """Test successfully deleting a book"""
        # Add a book first
        import api
        book = Book("Book To Delete", "Delete Author", "2222222222")
        api.library.add_book(book)

        response = client.delete("/books/2222222222")
        assert response.status_code == 200

        result = response.json()
        assert result["success"] == True
        assert "successfully deleted" in result["message"]

        # Verify book is deleted
        get_response = client.get("/books/2222222222")
        assert get_response.status_code == 404

    def test_delete_nonexistent_book(self):
        """Test deleting a book that doesn't exist"""
        response = client.delete("/books/9999999999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_delete_borrowed_book(self):
        """Test deleting a borrowed book (should fail)"""
        # Add and borrow a book
        import api
        book = Book("Borrowed Book", "Borrowed Author", "3333333333")
        book.borrow_book()  # Mark as borrowed
        api.library.add_book(book)

        response = client.delete("/books/3333333333")
        assert response.status_code == 400
        assert "currently borrowed" in response.json()["detail"]

    def test_api_documentation(self):
        """Test that API documentation is accessible"""
        response = client.get("/docs")
        assert response.status_code == 200

        # Test OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == 200
        openapi_schema = response.json()
        assert "openapi" in openapi_schema
        assert "info" in openapi_schema

    def test_invalid_request_body(self):
        """Test posting with invalid request body"""
        response = client.post("/books", json={"invalid": "data"})
        assert response.status_code == 422  # Validation error

    def test_empty_isbn(self):
        """Test posting with empty ISBN"""
        response = client.post("/books", json={"isbn": ""})
        assert response.status_code == 422  # Validation error

# Run with: pytest test_api.py -v