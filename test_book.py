# test_book.py
import pytest
from book import Book, EBook, AudioBook


class TestBook:
    def test_book_creation(self):
        book = Book("1984", "George Orwell", "978-0451524935")
        assert book.title == "1984"
        assert book.author == "George Orwell"
        assert book.isbn == "978-0451524935"
        assert not book.is_borrowed

    def test_book_borrow_and_return(self):
        book = Book("1984", "George Orwell", "978-0451524935")
        
        # Test borrowing
        book.borrow_book()
        assert book.is_borrowed
        
        # Test double borrow (should raise error)
        with pytest.raises(ValueError):
            book.borrow_book()
        
        # Test returning
        book.return_book()
        assert not book.is_borrowed
        
        # Test double return (should raise error)
        with pytest.raises(ValueError):
            book.return_book()

    def test_book_display_info(self):
        book = Book("1984", "George Orwell", "978-0451524935")
        display = book.display_info()
        assert "'1984'" in display
        assert "George Orwell" in display
        assert "978-0451524935" in display

    def test_book_str_method(self):
        book = Book("1984", "George Orwell", "978-0451524935")
        book_str = str(book)
        assert "'1984'" in book_str
        assert "George Orwell" in book_str

    def test_book_serialization(self):
        book = Book("Test Book", "Test Author", "123456789")
        book_dict = book.to_dict()
        assert book_dict["_cls"] == "Book"
        assert book_dict["title"] == "Test Book"
        assert book_dict["author"] == "Test Author"
        assert book_dict["isbn"] == "123456789"
        
        # Test deserialization
        restored_book = Book.from_dict(book_dict)
        assert restored_book.title == book.title
        assert restored_book.author == book.author
        assert restored_book.isbn == book.isbn

    def test_book_from_dict_missing_fields(self):
        # Test with minimal data
        data = {"title": "Test", "author": "Author", "isbn": "123"}
        book = Book.from_dict(data)
        assert book.title == "Test"
        assert not book.is_borrowed  # Should default to False


class TestEBook:
    def test_ebook_creation(self):
        ebook = EBook("Digital Fortress", "Dan Brown", "978-0312944926", file_format="EPUB")
        assert ebook.title == "Digital Fortress"
        assert ebook.author == "Dan Brown"
        assert ebook.isbn == "978-0312944926"
        assert ebook.file_format == "EPUB"
        assert not ebook.is_borrowed

    def test_ebook_default_format(self):
        ebook = EBook("Test Book", "Test Author", "123456789")
        assert ebook.file_format == "PDF"  # Default format

    def test_ebook_display_info(self):
        ebook = EBook("Digital Fortress", "Dan Brown", "978-0312944926", file_format="EPUB")
        display = ebook.display_info()
        assert "Digital Fortress" in display
        assert "Dan Brown" in display
        assert "EPUB" in display
        assert "Format:" in display

    def test_ebook_serialization(self):
        ebook = EBook("Test EBook", "Test Author", "123456789", file_format="MOBI")
        ebook_dict = ebook.to_dict()
        assert ebook_dict["_cls"] == "EBook"
        assert ebook_dict["file_format"] == "MOBI"
        
        # Test deserialization
        restored_ebook = Book.from_dict(ebook_dict)
        assert isinstance(restored_ebook, EBook)
        assert restored_ebook.file_format == "MOBI"

    def test_ebook_borrow_functionality(self):
        ebook = EBook("Test EBook", "Test Author", "123456789")
        ebook.borrow_book()
        assert ebook.is_borrowed


class TestAudioBook:
    def test_audiobook_creation(self):
        audiobook = AudioBook("The Hobbit", "J.R.R. Tolkien", "978-0547928227", duration=720)
        assert audiobook.title == "The Hobbit"
        assert audiobook.author == "J.R.R. Tolkien"
        assert audiobook.isbn == "978-0547928227"
        assert audiobook.duration == 720
        assert not audiobook.is_borrowed

    def test_audiobook_default_duration(self):
        audiobook = AudioBook("Test Book", "Test Author", "123456789")
        assert audiobook.duration == 0  # Default duration

    def test_audiobook_display_info(self):
        audiobook = AudioBook("The Hobbit", "J.R.R. Tolkien", "978-0547928227", duration=720)
        display = audiobook.display_info()
        assert "The Hobbit" in display
        assert "J.R.R. Tolkien" in display
        assert "720 mins" in display
        assert "Duration:" in display

    def test_audiobook_serialization(self):
        audiobook = AudioBook("Test AudioBook", "Test Author", "123456789", duration=480)
        audiobook_dict = audiobook.to_dict()
        assert audiobook_dict["_cls"] == "AudioBook"
        assert audiobook_dict["duration"] == 480
        
        # Test deserialization
        restored_audiobook = Book.from_dict(audiobook_dict)
        assert isinstance(restored_audiobook, AudioBook)
        assert restored_audiobook.duration == 480

    def test_audiobook_borrow_functionality(self):
        audiobook = AudioBook("Test AudioBook", "Test Author", "123456789", duration=300)
        audiobook.borrow_book()
        assert audiobook.is_borrowed


class TestBookPolymorphism:
    def test_different_book_types_in_list(self):
        books = [
            Book("Regular Book", "Author 1", "111"),
            EBook("Digital Book", "Author 2", "222", file_format="EPUB"),
            AudioBook("Audio Book", "Author 3", "333", duration=180)
        ]
        
        # Test that all books can be treated polymorphically
        for book in books:
            assert hasattr(book, 'borrow_book')
            assert hasattr(book, 'return_book')
            assert hasattr(book, 'display_info')
            
        # Test specific display info for each type
        assert "Format:" in books[1].display_info()  # EBook
        assert "Duration:" in books[2].display_info()  # AudioBook

    def test_serialization_deserialization_all_types(self):
        original_books = [
            Book("Regular Book", "Author 1", "111"),
            EBook("Digital Book", "Author 2", "222", file_format="EPUB"),
            AudioBook("Audio Book", "Author 3", "333", duration=180)
        ]
        
        # Serialize all books
        serialized = [book.to_dict() for book in original_books]
        
        # Deserialize all books
        restored_books = [Book.from_dict(data) for data in serialized]
        
        # Verify types are preserved
        assert isinstance(restored_books[0], Book)
        assert not isinstance(restored_books[0], (EBook, AudioBook))
        assert isinstance(restored_books[1], EBook)
        assert isinstance(restored_books[2], AudioBook)
        
        # Verify data integrity
        assert restored_books[1].file_format == "EPUB"
        assert restored_books[2].duration == 180


if __name__ == "__main__":
    pytest.main([__file__, "-v"])