# test_member.py
import pytest
import json
import tempfile
from pathlib import Path
from member import Member
from member_manager import MemberManager
from book import Book, EBook, AudioBook
from library import Library


class TestMember:
    def test_member_creation(self):
        member = Member("John Doe", "M001", "john@example.com")
        assert member.name == "John Doe"
        assert member.member_id == "M001"
        assert member.email == "john@example.com"
        assert len(member.borrowed_books) == 0
        assert isinstance(member.borrowed_books, list)

    def test_member_creation_with_borrowed_books(self):
        borrowed_books = ["978-0451524935", "978-0547928227"]
        member = Member("Jane Doe", "M002", "jane@example.com", borrowed_books=borrowed_books)
        assert len(member.borrowed_books) == 2
        assert "978-0451524935" in member.borrowed_books
        assert "978-0547928227" in member.borrowed_books

    def test_member_borrow_book(self):
        member = Member("John Doe", "M001", "john@example.com")
        isbn = "978-0451524935"

        member.borrow_book(isbn)
        assert len(member.borrowed_books) == 1
        assert isbn in member.borrowed_books

    def test_member_borrow_multiple_books(self):
        member = Member("John Doe", "M001", "john@example.com")
        isbn1 = "978-0451524935"
        isbn2 = "978-0547928227"

        member.borrow_book(isbn1)
        member.borrow_book(isbn2)

        assert len(member.borrowed_books) == 2
        assert isbn1 in member.borrowed_books
        assert isbn2 in member.borrowed_books

    def test_member_borrow_same_book_twice(self):
        member = Member("John Doe", "M001", "john@example.com")
        isbn = "978-0451524935"

        member.borrow_book(isbn)

        # Should raise error when borrowing the same book again
        with pytest.raises(ValueError, match="already borrowed"):
            member.borrow_book(isbn)

        # Should still have only one copy
        assert len(member.borrowed_books) == 1

    def test_member_return_book(self):
        member = Member("John Doe", "M001", "john@example.com")
        isbn = "978-0451524935"

        # First borrow the book
        member.borrow_book(isbn)
        assert isbn in member.borrowed_books

        # Then return it
        member.return_book(isbn)
        assert isbn not in member.borrowed_books
        assert len(member.borrowed_books) == 0

    def test_member_return_book_from_multiple(self):
        member = Member("John Doe", "M001", "john@example.com")
        isbn1 = "978-0451524935"
        isbn2 = "978-0547928227"
        isbn3 = "978-0312944926"

        # Borrow multiple books
        member.borrow_book(isbn1)
        member.borrow_book(isbn2)
        member.borrow_book(isbn3)
        assert len(member.borrowed_books) == 3

        # Return one book
        member.return_book(isbn2)
        assert len(member.borrowed_books) == 2
        assert isbn1 in member.borrowed_books
        assert isbn2 not in member.borrowed_books
        assert isbn3 in member.borrowed_books

    def test_member_return_non_borrowed_book(self):
        member = Member("John Doe", "M001", "john@example.com")
        isbn = "978-0451524935"

        # Try to return a book that wasn't borrowed
        with pytest.raises(ValueError, match="not borrowed"):
            member.return_book(isbn)

    def test_member_str_method(self):
        member = Member("John Doe", "M001", "john@example.com")
        member_str = str(member)
        assert "John Doe" in member_str
        assert "M001" in member_str
        assert "john@example.com" in member_str

    def test_member_to_dict(self):
        member = Member("John Doe", "M001", "john@example.com", borrowed_books=["978-0451524935"])
        member_dict = member.to_dict()

        assert member_dict["name"] == "John Doe"
        assert member_dict["member_id"] == "M001"
        assert member_dict["email"] == "john@example.com"
        assert member_dict["borrowed_books"] == ["978-0451524935"]

    def test_member_from_dict(self):
        data = {
            "name": "John Doe",
            "member_id": "M001",
            "email": "john@example.com",
            "borrowed_books": ["978-0451524935"]
        }
        member = Member.from_dict(data)

        assert member.name == "John Doe"
        assert member.member_id == "M001"
        assert member.email == "john@example.com"
        assert member.borrowed_books == ["978-0451524935"]

    def test_member_from_dict_missing_borrowed_books(self):
        # Test with missing borrowed_books field
        data = {
            "name": "John Doe",
            "member_id": "M001",
            "email": "john@example.com"
        }
        member = Member.from_dict(data)

        assert member.name == "John Doe"
        assert member.borrowed_books == []  # Should default to empty list


class TestMemberManager:
    def test_member_manager_creation_new_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            manager = MemberManager(tmp.name)
            assert len(manager.members) == 0
            assert manager.data_file == Path(tmp.name)

    def test_member_manager_creation_nonexistent_file(self):
        # Test with a file that doesn't exist
        non_existent_path = "/tmp/test_nonexistent_members.json"
        manager = MemberManager(non_existent_path)
        assert len(manager.members) == 0

    def test_add_member(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            manager = MemberManager(tmp.name)
            member = Member("John Doe", "M001", "john@example.com")

            manager.add_member(member)
            assert len(manager.members) == 1
            assert manager.members[0].name == "John Doe"
            assert manager.members[0].member_id == "M001"

    def test_add_multiple_members(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            manager = MemberManager(tmp.name)
            member1 = Member("John Doe", "M001", "john@example.com")
            member2 = Member("Jane Smith", "M002", "jane@example.com")

            manager.add_member(member1)
            manager.add_member(member2)

            assert len(manager.members) == 2
            member_ids = [m.member_id for m in manager.members]
            assert "M001" in member_ids
            assert "M002" in member_ids

    def test_add_duplicate_member(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            manager = MemberManager(tmp.name)
            member1 = Member("John Doe", "M001", "john@example.com")
            member2 = Member("Jane Doe", "M001", "jane@example.com")  # Same ID

            manager.add_member(member1)
            with pytest.raises(ValueError, match="already exists"):
                manager.add_member(member2)

            # Verify only first member was added
            assert len(manager.members) == 1
            assert manager.members[0].name == "John Doe"

    def test_find_member(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            manager = MemberManager(tmp.name)
            member = Member("John Doe", "M001", "john@example.com")

            manager.add_member(member)
            found_member = manager.find_member("M001")
            assert found_member is not None
            assert found_member.name == "John Doe"
            assert found_member.member_id == "M001"

    def test_find_nonexistent_member(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            manager = MemberManager(tmp.name)
            not_found = manager.find_member("M999")
            assert not_found is None

    def test_find_member_among_multiple(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            manager = MemberManager(tmp.name)
            member1 = Member("John Doe", "M001", "john@example.com")
            member2 = Member("Jane Smith", "M002", "jane@example.com")
            member3 = Member("Bob Johnson", "M003", "bob@example.com")

            manager.add_member(member1)
            manager.add_member(member2)
            manager.add_member(member3)

            found_member = manager.find_member("M002")
            assert found_member is not None
            assert found_member.name == "Jane Smith"

    def test_remove_member(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            manager = MemberManager(tmp.name)
            member = Member("John Doe", "M001", "john@example.com")

            manager.add_member(member)
            assert len(manager.members) == 1

            manager.remove_member("M001")
            assert len(manager.members) == 0

    def test_remove_nonexistent_member(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            manager = MemberManager(tmp.name)
            with pytest.raises(ValueError, match="No member found"):
                manager.remove_member("M999")

    def test_remove_member_from_multiple(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            manager = MemberManager(tmp.name)
            member1 = Member("John Doe", "M001", "john@example.com")
            member2 = Member("Jane Smith", "M002", "jane@example.com")
            member3 = Member("Bob Johnson", "M003", "bob@example.com")

            manager.add_member(member1)
            manager.add_member(member2)
            manager.add_member(member3)
            assert len(manager.members) == 3

            manager.remove_member("M002")
            assert len(manager.members) == 2

            # Verify correct member was removed
            member_ids = [m.member_id for m in manager.members]
            assert "M001" in member_ids
            assert "M002" not in member_ids
            assert "M003" in member_ids

    def test_list_members_empty(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            manager = MemberManager(tmp.name)
            members = manager.list_members()
            assert members == []
            assert isinstance(members, list)

    def test_list_members_with_content(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            manager = MemberManager(tmp.name)
            member1 = Member("John Doe", "M001", "john@example.com")
            member2 = Member("Jane Smith", "M002", "jane@example.com")

            manager.add_member(member1)
            manager.add_member(member2)

            members = manager.list_members()
            assert len(members) == 2
            assert isinstance(members, list)
            # Verify it returns a copy, not the original list
            assert members is not manager.members

    def test_member_manager_persistence(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            # Create manager and add member
            manager1 = MemberManager(tmp.name)
            member = Member("John Doe", "M001", "john@example.com")
            member.borrow_book("978-0451524935")  # Add borrowed book
            manager1.add_member(member)

            # Create new manager instance with same file
            manager2 = MemberManager(tmp.name)
            assert len(manager2.members) == 1

            loaded_member = manager2.find_member("M001")
            assert loaded_member is not None
            assert loaded_member.name == "John Doe"
            assert loaded_member.email == "john@example.com"
            assert "978-0451524935" in loaded_member.borrowed_books

    def test_member_manager_load_invalid_json(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode='w') as tmp:
            # Write invalid JSON
            tmp.write("invalid json content")
            tmp.flush()

            # Should handle error gracefully
            manager = MemberManager(tmp.name)
            assert len(manager.members) == 0

    def test_member_manager_load_non_list_json(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode='w') as tmp:
            # Write valid JSON but not a list
            json.dump({"not": "a list"}, tmp)
            tmp.flush()

            # Should handle error gracefully
            manager = MemberManager(tmp.name)
            assert len(manager.members) == 0

    def test_member_manager_save_atomic_write(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            manager = MemberManager(tmp.name)
            member = Member("John Doe", "M001", "john@example.com")
            manager.add_member(member)

            # Verify temporary file handling
            tmp_file = Path(tmp.name + ".tmp")
            assert not tmp_file.exists()  # Temp file should be cleaned up

            # Main file should exist and be readable
            main_file = Path(tmp.name)
            assert main_file.exists()

            data = json.loads(main_file.read_text())
            assert isinstance(data, list)
            assert len(data) == 1

    def test_member_serialization_deserialization(self):
        original_member = Member("John Doe", "M001", "john@example.com",
                                 borrowed_books=["978-0451524935", "978-0547928227"])

        # Serialize
        member_dict = original_member.to_dict()
        assert member_dict["name"] == "John Doe"
        assert member_dict["member_id"] == "M001"
        assert member_dict["email"] == "john@example.com"
        assert len(member_dict["borrowed_books"]) == 2

        # Deserialize
        restored_member = Member.from_dict(member_dict)
        assert restored_member.name == original_member.name
        assert restored_member.member_id == original_member.member_id
        assert restored_member.email == original_member.email
        assert restored_member.borrowed_books == original_member.borrowed_books


# Integration Tests
class TestIntegration:
    def test_full_borrow_return_workflow(self):
        """Test complete borrow and return workflow with real Library and MemberManager"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as lib_tmp, \
                tempfile.NamedTemporaryFile(suffix=".json", delete=False) as mem_tmp:
            library = Library(lib_tmp.name)
            member_manager = MemberManager(mem_tmp.name)

            # Add book and member
            book = Book("1984", "George Orwell", "978-0451524935")
            member = Member("John Doe", "M001", "john@example.com")

            library.add_book(book)
            member_manager.add_member(member)

            # Verify initial state
            assert len(library.books) == 1
            assert len(member_manager.members) == 1
            assert not book.is_borrowed
            assert len(member.borrowed_books) == 0

            # Borrow workflow (similar to main.py logic)
            found_book = library.find_book("978-0451524935")
            found_member = member_manager.find_member("M001")

            assert found_book is not None
            assert found_member is not None

            found_book.borrow_book()
            found_member.borrow_book("978-0451524935")

            library.save_books()
            member_manager.save_members()

            # Verify borrow state
            assert found_book.is_borrowed
            assert "978-0451524935" in found_member.borrowed_books

            # Return workflow
            found_book.return_book()
            found_member.return_book("978-0451524935")

            library.save_books()
            member_manager.save_members()

            # Verify return state
            assert not found_book.is_borrowed
            assert "978-0451524935" not in found_member.borrowed_books

    def test_workflow_persistence_across_sessions(self):
        """Test that borrow/return state persists when app restarts"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as lib_tmp, \
                tempfile.NamedTemporaryFile(suffix=".json", delete=False) as mem_tmp:
            # Session 1: Add data and borrow book
            library1 = Library(lib_tmp.name)
            member_manager1 = MemberManager(mem_tmp.name)

            book = Book("1984", "George Orwell", "978-0451524935")
            member = Member("John Doe", "M001", "john@example.com")

            library1.add_book(book)
            member_manager1.add_member(member)

            # Borrow book
            found_book1 = library1.find_book("978-0451524935")
            found_member1 = member_manager1.find_member("M001")
            found_book1.borrow_book()
            found_member1.borrow_book("978-0451524935")
            library1.save_books()
            member_manager1.save_members()

            # Session 2: Load and verify state
            library2 = Library(lib_tmp.name)
            member_manager2 = MemberManager(mem_tmp.name)

            found_book2 = library2.find_book("978-0451524935")
            found_member2 = member_manager2.find_member("M001")

            assert found_book2 is not None
            assert found_member2 is not None
            assert found_book2.is_borrowed
            assert "978-0451524935" in found_member2.borrowed_books

    def test_multiple_members_multiple_books(self):
        """Test system with multiple members borrowing different books"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as lib_tmp, \
                tempfile.NamedTemporaryFile(suffix=".json", delete=False) as mem_tmp:
            library = Library(lib_tmp.name)
            member_manager = MemberManager(mem_tmp.name)

            # Add multiple books
            book1 = Book("1984", "George Orwell", "978-0451524935")
            book2 = Book("The Hobbit", "J.R.R. Tolkien", "978-0547928227")
            ebook = EBook("Digital Book", "Digital Author", "978-1234567890", file_format="EPUB")

            library.add_book(book1)
            library.add_book(book2)
            library.add_book(ebook)

            # Add multiple members
            member1 = Member("John Doe", "M001", "john@example.com")
            member2 = Member("Jane Smith", "M002", "jane@example.com")

            member_manager.add_member(member1)
            member_manager.add_member(member2)

            # Member 1 borrows book1
            book1.borrow_book()
            member1.borrow_book("978-0451524935")

            # Member 2 borrows book2 and ebook
            book2.borrow_book()
            ebook.borrow_book()
            member2.borrow_book("978-0547928227")
            member2.borrow_book("978-1234567890")

            # Verify states
            assert book1.is_borrowed
            assert book2.is_borrowed
            assert ebook.is_borrowed
            assert len(member1.borrowed_books) == 1
            assert len(member2.borrowed_books) == 2
            assert "978-0451524935" in member1.borrowed_books
            assert "978-0547928227" in member2.borrowed_books
            assert "978-1234567890" in member2.borrowed_books

    def test_error_scenarios(self):
        """Test various error scenarios"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as lib_tmp, \
                tempfile.NamedTemporaryFile(suffix=".json", delete=False) as mem_tmp:
            library = Library(lib_tmp.name)
            member_manager = MemberManager(mem_tmp.name)

            book = Book("1984", "George Orwell", "978-0451524935")
            member = Member("John Doe", "M001", "john@example.com")

            library.add_book(book)
            member_manager.add_member(member)

            # Test borrowing already borrowed book
            book.borrow_book()
            with pytest.raises(ValueError):
                book.borrow_book()

            # Test member borrowing same book twice
            member.borrow_book("978-0451524935")
            with pytest.raises(ValueError):
                member.borrow_book("978-0451524935")

            # Test returning non-borrowed book (reset state first)
            book.return_book()
            member.return_book("978-0451524935")

            with pytest.raises(ValueError):
                book.return_book()

            with pytest.raises(ValueError):
                member.return_book("978-0451524935")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])