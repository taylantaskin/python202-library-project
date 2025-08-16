# library.py
import json
import httpx
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field
from book import Book  # EBook/AudioBook, Book.from_dict içinde handle ediliyor


@dataclass
class Library:
    """
    Manages a collection of books and stores them in a JSON file.
    """
    data_file: str = "library.json"
    books: List[Book] = field(default_factory=list)
    _data_path: Path = field(init=False)

    def __post_init__(self):
        """Initialize after dataclass creation."""
        self._data_path = Path(self.data_file)
        self.load_books()

    def load_books(self) -> None:
        """Load books from the JSON file into the library."""
        if not self._data_path.exists():
            self.books = []
            return
        try:
            raw = json.loads(self._data_path.read_text(encoding="utf-8"))
            if not isinstance(raw, list):
                raise ValueError("library.json format must be a list of books")
            self.books = [Book.from_dict(item) for item in raw]
        except Exception as e:
            print(f"[WARN] Couldn't load {self._data_path}: {e}. Starting with empty list.")
            self.books = []

    def save_books(self) -> None:
        """Save the current list of books to the JSON file."""
        data = [book.to_dict() for book in self.books]
        tmp = self._data_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self._data_path)

    def fetch_book_from_api(self, isbn: str) -> Optional[dict]:
        """
        Fetch book information from Open Library API.
        Returns book data as dict or None if not found.
        """
        try:
            # Open Library API endpoint
            url = f"https://openlibrary.org/isbn/{isbn}.json"

            # Configure client to follow redirects
            with httpx.Client(follow_redirects=True) as client:
                response = client.get(url, timeout=10.0)

                if response.status_code == 404:
                    return None

                response.raise_for_status()  # Raises exception for bad status codes
                book_data = response.json()

                # Extract title
                title = book_data.get("title", "Unknown Title")

                # Extract authors (Open Library can have complex author structure)
                authors = []
                if "authors" in book_data:
                    for author_ref in book_data["authors"]:
                        if isinstance(author_ref, dict) and "key" in author_ref:
                            # Fetch author name from author key
                            author_key = author_ref["key"]
                            author_url = f"https://openlibrary.org{author_key}.json"
                            try:
                                author_response = client.get(author_url, timeout=5.0)
                                if author_response.status_code == 200:
                                    author_data = author_response.json()
                                    author_name = author_data.get("name", "Unknown Author")
                                    authors.append(author_name)
                                else:
                                    authors.append("Unknown Author")
                            except Exception:
                                authors.append("Unknown Author")

                # If no authors found, use "Unknown Author"
                if not authors:
                    authors = ["Unknown Author"]

                return {
                    "title": title,
                    "author": ", ".join(authors),  # Join multiple authors
                    "isbn": isbn
                }

        except httpx.TimeoutException:
            print(f"[ERROR] Timeout while fetching book data for ISBN: {isbn}")
            return None
        except httpx.RequestError as e:
            print(f"[ERROR] Network error while fetching book data: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] Unexpected error while fetching book data: {e}")
            return None

    def add_book_from_isbn(self, isbn: str) -> bool:
        """
        Add a book to the library using only ISBN.
        Fetches book data from Open Library API.
        Returns True if successful, False otherwise.
        """
        # Check if book already exists
        if any(b.isbn == isbn for b in self.books):
            raise ValueError(f"A book with ISBN {isbn} already exists.")

        # Fetch book data from API
        book_data = self.fetch_book_from_api(isbn)

        if not book_data:
            raise ValueError(f"Book with ISBN {isbn} not found in Open Library.")

        # Create Book object from API data
        book = Book(
            title=book_data["title"],
            author=book_data["author"],
            isbn=book_data["isbn"]
        )

        # Add to library
        self.books.append(book)
        self.save_books()
        return True

    def add_book(self, book: Book) -> None:
        """Add a new book to the library and save the change."""
        if any(b.isbn == book.isbn for b in self.books):
            raise ValueError(f"A book with ISBN {book.isbn} already exists.")
        self.books.append(book)
        self.save_books()

    def remove_book(self, isbn: str) -> None:
        """Remove a book by ISBN and save the change."""
        for b in self.books:
            if b.isbn == isbn:
                self.books.remove(b)
                self.save_books()
                return
        raise ValueError(f"No book found with ISBN {isbn}.")

    def list_books(self) -> List[Book]:
        """Return all books (CLI'de yazdıracağız)."""
        return list(self.books)

    def find_book(self, isbn: str) -> Optional[Book]:
        """Find and return a book by its ISBN."""
        isbn = isbn.strip()
        for book in self.books:
            if book.isbn == isbn:
                return book
        return None