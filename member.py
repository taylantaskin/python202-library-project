# member.py
from dataclasses import dataclass, field, asdict
from typing import List

@dataclass
class Member:
    """
    Represents a library member.
    Attributes:
      name (str): Full name of the member.
      member_id (str): Unique identifier for the member.
      email (str): Contact email address.
      borrowed_books (list[str]): List of ISBNs of borrowed books.
    """
    name: str
    member_id: str
    email: str
    borrowed_books: List[str] = field(default_factory=list)

    def borrow_book(self, isbn: str):
        """Adds a book's ISBN to the borrowed list."""
        if isbn in self.borrowed_books:
            raise ValueError(f"Book with ISBN {isbn} is already borrowed by {self.name}.")
        self.borrowed_books.append(isbn)

    def return_book(self, isbn: str):
        """Removes a book's ISBN from the borrowed list."""
        if isbn not in self.borrowed_books:
            raise ValueError(f"Book with ISBN {isbn} is not borrowed by {self.name}.")
        self.borrowed_books.remove(isbn)

    def __str__(self) -> str:
        return f"{self.name} ({self.member_id}) - {self.email}"

    def to_dict(self) -> dict:
        """Serialize to plain dict for JSON persistence."""
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Member":
        """Safe constructor from dict (fills missing keys)."""
        data = dict(data)  # don't mutate caller's dict
        data.setdefault("borrowed_books", [])
        return Member(**data)
