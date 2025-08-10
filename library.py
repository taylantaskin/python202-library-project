# library.py
import json
from pathlib import Path
from typing import List, Optional
from book import Book  # EBook/AudioBook, Book.from_dict içinde handle ediliyor

class Library:
    """
    Manages a collection of books and stores them in a JSON file.
    """
    def __init__(self, data_file: str = "library.json"):
        self.data_file = Path(data_file)
        self.books: List[Book] = []
        self.load_books()

    def load_books(self) -> None:
        """Load books from the JSON file into the library."""
        if not self.data_file.exists():
            self.books = []
            return
        try:
            raw = json.loads(self.data_file.read_text(encoding="utf-8"))
            if not isinstance(raw, list):
                raise ValueError("library.json format must be a list of books")
            self.books = [Book.from_dict(item) for item in raw]
        except Exception as e:
            print(f"[WARN] Couldn't load {self.data_file}: {e}. Starting with empty list.")
            self.books = []

    def save_books(self) -> None:
        """Save the current list of books to the JSON file."""
        data = [book.to_dict() for book in self.books]
        tmp = self.data_file.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.data_file)

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
