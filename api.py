# api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from library import Library
from book import Book, EBook, AudioBook
import uvicorn


# Pydantic Models
class BookResponse(BaseModel):
    """API response model for book data"""
    title: str
    author: str
    isbn: str
    is_borrowed: bool = False
    book_type: str = "Book"

    # EBook specific fields
    file_format: Optional[str] = None

    # AudioBook specific fields
    duration: Optional[int] = None

    @classmethod
    def from_book(cls, book: Book) -> "BookResponse":
        """Convert Book object to BookResponse"""
        response = cls(
            title=book.title,
            author=book.author,
            isbn=book.isbn,
            is_borrowed=book.is_borrowed,
            book_type=book.__class__.__name__
        )

        # Add specific fields based on book type
        if isinstance(book, EBook):
            response.file_format = book.file_format
        elif isinstance(book, AudioBook):
            response.duration = book.duration

        return response


class AddBookRequest(BaseModel):
    """Request model for adding a book via ISBN"""
    isbn: str = Field(..., min_length=1, description="ISBN of the book to add", example="9780743273565")

    @field_validator("isbn")
    @classmethod
    def strip_and_check(cls, v: str):
        v = v.strip()
        if not v:
            # Boş veya sadece boşluklardan oluşuyorsa 422 için doğrulamada hata
            raise ValueError("ISBN cannot be empty")
        return v



class MessageResponse(BaseModel):
    """General message response"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    success: bool = False


# FastAPI app initialization
app = FastAPI(
    title="Library Management API",
    description="A simple library management system API built with FastAPI",
    version="1.0.0"
)

# Initialize library
library = Library("library.json")


@app.get("/", response_model=MessageResponse)
async def root():
    """Root endpoint - API information"""
    return MessageResponse(
        message="Welcome to Library Management API! Visit /docs for interactive documentation."
    )


@app.get("/books", response_model=List[BookResponse])
async def get_all_books():
    """
    Get all books in the library

    Returns a list of all books with their details including type-specific information.
    """
    books = library.list_books()
    return [BookResponse.from_book(book) for book in books]


@app.post("/books", response_model=BookResponse)

async def add_book(request: AddBookRequest):
    """
    Add a new book to the library using ISBN

    Fetches book information from Open Library API and adds it to the library.

    - **isbn**: ISBN of the book to add (e.g., "9780743273565")
    """

    if not request.isbn or not request.isbn.strip():
        raise HTTPException(status_code=422, detail="ISBN cannot be empty")

    try:
        # Add book using ISBN (fetches from Open Library API)
        success = library.add_book_from_isbn(request.isbn)

        if success:
            # Find the newly added book
            book = library.find_book(request.isbn)
            if book:
                return BookResponse.from_book(book)
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Book was added but could not be retrieved"
                )
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Book with ISBN {request.isbn} not found in Open Library"
            )

    except ValueError as e:
        # Handle specific library errors
        error_msg = str(e)
        if "already exists" in error_msg:
            raise HTTPException(status_code=409, detail=error_msg)
        elif "not found" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@app.delete("/books/{isbn}", response_model=MessageResponse)
async def delete_book(isbn: str):
    """
    Delete a book from the library by ISBN

    - **isbn**: ISBN of the book to delete
    """
    try:
        # Check if book exists first
        book = library.find_book(isbn)
        if not book:
            raise HTTPException(
                status_code=404,
                detail=f"Book with ISBN {isbn} not found in library"
            )

        # Check if book is borrowed
        if book.is_borrowed:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete '{book.title}' because it is currently borrowed"
            )

        # Remove the book
        library.remove_book(isbn)

        return MessageResponse(
            message=f"Book '{book.title}' with ISBN {isbn} has been successfully deleted"
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except ValueError as e:
        # Handle library-specific errors
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@app.get("/books/{isbn}", response_model=BookResponse)
async def get_book(isbn: str):
    """
    Get a specific book by ISBN

    - **isbn**: ISBN of the book to retrieve
    """
    book = library.find_book(isbn)
    if not book:
        raise HTTPException(
            status_code=404,
            detail=f"Book with ISBN {isbn} not found in library"
        )

    return BookResponse.from_book(book)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "total_books": len(library.books),
        "api_version": "1.0.0"
    }


# Error handlers
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return HTTPException(status_code=400, detail=str(exc))


if __name__ == "__main__":
    # Run the server directly with python api.py
    uvicorn.run(
        "api:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )