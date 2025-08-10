# test_library.py
import pytest
import json
import tempfile
from pathlib import Path
from book import Book, EBook, AudioBook
from library import Library


class TestLibrary:
    def test_library_creation_new_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            library = Library(tmp.name)
            assert len(library.books) == 0
            assert library.data_file == Path(tmp.name)

    def test_library_creation_nonexistent_file(self):
        # Test with a file that doesn't exist
        non_existent_path = "/tmp/test_nonexistent_library.json"
        library = Library(non_existent_path)
        assert len(library.books) == 0

    def test_add_book(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            library = Library(tmp.name)
            book = Book("Test Book", "Test Author", "123456789")
            
            library.add_book(book)
            assert len(library.books) == 1
            assert library.books[0].title == "Test Book"
            assert library.books[0].author == "Test Author"
            assert library.books[0].isbn == "123456789"

    def test_add_different_book_types(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            library = Library(tmp.name)
            
            regular_book = Book("Regular Book", "Author 1", "111")
            ebook = EBook("Digital Book", "Author 2", "222", file_format="EPUB")
            audiobook = AudioBook("Audio Book", "Author 3", "333", duration=180)
            
            library.add_book(regular_book)
            library.add_book(ebook)
            library.add_book(audiobook)
            
            assert len(library.books) == 3
            assert isinstance(library.books[1], EBook)
            assert isinstance(library.books[2], AudioBook)

    def test_add_duplicate_book(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            library = Library(tmp.name)
            book1 = Book("Test Book", "Test Author", "123456789")
            book2 = Book("Another Book", "Another Author", "123456789")  # Same ISBN
            
            library.add_book(book1)
            with pytest.raises(ValueError, match="already exists"):
                library.add_book(book2)
            
            # Verify only first book was added
            assert len(library.books) == 1
            assert library.books[0].title == "Test Book"

    def test_remove_book(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            library = Library(tmp.name)
            book = Book("Test Book", "Test Author", "123456789")
            
            library.add_book(book)
            assert len(library.books) == 1
            
            library.remove_book("123456789")
            assert len(library.books) == 0

    def test_remove_nonexistent_book(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            library = Library(tmp.name)
            with pytest.raises(ValueError, match="No book found"):
                library.remove_book("nonexistent")

    def test_remove_book_multiple_books(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            library = Library(tmp.name)
            book1 = Book("Book 1", "Author 1", "111")
            book2 = Book("Book 2", "Author 2", "222")
            book3 = Book("Book 3", "Author 3", "333")
            
            library.add_book(book1)
            library.add_book(book2)
            library.add_book(book3)
            assert len(library.books) == 3
            
            library.remove_book("222")
            assert len(library.books) == 2
            
            # Verify correct book was removed
            isbns = [book.isbn for book in library.books]
            assert "111" in isbns
            assert "222" not in isbns
            assert "333" in isbns

    def test_find_book(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            library = Library(tmp.name)
            book = Book("Test Book", "Test Author", "123456789")
            
            library.add_book(book)
            found_book = library.find_book("123456789")
            assert found_book is not None
            assert found_book.title == "Test Book"
            assert found_book.author == "Test Author"

    def test_find_nonexistent_book(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            library = Library(tmp.name)
            not_found = library.find_book("nonexistent")
            assert not_found is None

    def test_find_book_with_whitespace(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            library = Library(tmp.name)
            book = Book("Test Book", "Test Author", "123456789")
            library.add_book(book)
            
            # Test finding with whitespace
            found_book = library.find_book("  123456789  ")
            assert found_book is not None
            assert found_book.title == "Test Book"

    def test_list_books_empty(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            library = Library(tmp.name)
            books = library.list_books()
            assert books == []
            assert isinstance(books, list)

    def test_list_books_with_content(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            library = Library(tmp.name)
            book1 = Book("Book 1", "Author 1", "111")
            book2 = Book("Book 2", "Author 2", "222")
            
            library.add_book(book1)
            library.add_book(book2)
            
            books = library.list_books()
            assert len(books) == 2
            assert isinstance(books, list)
            # Verify it returns a copy, not the original list
            assert books is not library.books

    def test_persistence_save_and_load(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            # Create library and add book
            library1 = Library(tmp.name)
            book = Book("Test Book", "Test Author", "123456789")
            library1.add_book(book)
            
            # Create new library instance with same file
            library2 = Library(tmp.name)
            assert len(library2.books) == 1
            assert library2.books[0].title == "Test Book"
            assert library2.books[0].author == "Test Author"
            assert library2.books[0].isbn == "123456789"

    def test_persistence_different_book_types(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            # Create library and add different book types
            library1 = Library(tmp.name)
            regular_book = Book("Regular Book", "Author 1", "111")
            ebook = EBook("Digital Book", "Author 2", "222", file_format="EPUB")
            audiobook = AudioBook("Audio Book", "Author 3", "333", duration=180)
            
            library1.add_book(regular_book)
            library1.add_book(ebook)
            library1.add_book(audiobook)
            
            # Create new library instance and verify types are preserved
            library2 = Library(tmp.name)
            assert len(library2.books) == 3
            
            # Verify types
            book_by_isbn = {book.isbn: book for book in library2.books}
            assert isinstance(book_by_isbn["111"], Book)
            assert not isinstance(book_by_isbn["111"], (EBook, AudioBook))
            assert isinstance(book_by_isbn["222"], EBook)
            assert isinstance(book_by_isbn["333"], AudioBook)
            
            # Verify specific attributes
            assert book_by_isbn["222"].file_format == "EPUB"
            assert book_by_isbn["333"].duration == 180

    def test_persistence_with_borrowed_books(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            # Create library and borrow a book
            library1 = Library(tmp.name)
            book = Book("Test Book", "Test Author", "123456789")
            library1.add_book(book)
            
            # Borrow the book and save
            found_book = library1.find_book("123456789")
            found_book.borrow_book()
            library1.save_books()
            
            # Create new library instance and verify borrow state is preserved
            library2 = Library(tmp.name)
            loaded_book = library2.find_book("123456789")
            assert loaded_book is not None
            assert loaded_book.is_borrowed

    def test_load_books_invalid_json(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode='w') as tmp:
            # Write invalid JSON
            tmp.write("invalid json content")
            tmp.flush()
            
            # Should handle error gracefully
            library = Library(tmp.name)
            assert len(library.books) == 0

    def test_load_books_non_list_json(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode='w') as tmp:
            # Write valid JSON but not a list
            json.dump({"not": "a list"}, tmp)
            tmp.flush()
            
            # Should handle error gracefully
            library = Library(tmp.name)
            assert len(library.books) == 0

    def test_save_books_atomic_write(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            library = Library(tmp.name)
            book = Book("Test Book", "Test Author", "123456789")
            library.add_book(book)
            
            # Verify temporary file is created and then replaced
            assert tmp.name.endswith(".json")
            tmp_file = Path(tmp.name + ".tmp")
            
            # After save_books, temp file should not exist
            assert not tmp_file.exists()
            
            # But the main file should exist and be readable
            main_file = Path(tmp.name)
            assert main_file.exists()
            
            data = json.loads(main_file.read_text())
            assert isinstance(data, list)
            assert len(data) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])