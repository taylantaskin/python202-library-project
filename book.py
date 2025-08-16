# book.py
from dataclasses import dataclass, asdict

@dataclass
class Book:
    title: str
    author: str
    isbn: str
    is_borrowed: bool = False

    def borrow_book(self):
        if self.is_borrowed == True:
            raise ValueError(f"'{self.title}' is already borrowed.")
        self.is_borrowed = True

    def return_book(self):
        if self.is_borrowed == False:
            raise ValueError(f"'{self.title}' was not borrowed.")
        self.is_borrowed = False

    def display_info(self) -> str:
        return f"'{self.title}' by {self.author} (ISBN: {self.isbn})"

    def __str__(self) -> str:
        return self.display_info()

    def to_dict(self) -> dict:
        data = asdict(self)
        data["_cls"] = self.__class__.__name__  # tür bilgisini kaydet
        return data

    @staticmethod
    def from_dict(data: dict) -> "Book":
        cls = data.pop("_cls", "Book")
        if cls == "EBook":
            return EBook(**data)
        if cls == "AudioBook":
            return AudioBook(**data)
        return Book(**data)


@dataclass
class EBook(Book):
    file_format: str = "PDF"

    def display_info(self) -> str:
        return f"{super().display_info()} [Format: {self.file_format}]"


@dataclass
class AudioBook(Book):
    duration: int = 0  # dakika

    def display_info(self) -> str:
        return f"{super().display_info()} [Duration: {self.duration} mins]"
