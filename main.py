from book import Book, EBook, AudioBook
from library import Library
from member import Member
from member_manager import MemberManager
import sys
import time
import webbrowser
from pathlib import Path
from multiprocessing import Process
import uvicorn

# -----------------------------
# Top-level function for API
# -----------------------------
def run_server():
    """Run the FastAPI API server"""
    uvicorn.run("api:app", host="127.0.0.1", port=8000, log_level="warning")


# -----------------------------
# Web interface starter
# -----------------------------
def start_web_interface():
    print("\nStarting Library Management Web Interface...")
    print("=" * 50)

    try:
        web_file = Path("web_interface.html")
        if not web_file.exists():
            print("Error: web_interface.html file not found!")
            input("Press Enter to continue...")
            return

        print("Starting API server...")

        server_process = Process(target=run_server)
        server_process.start()

        print("Waiting for server to start...")
        time.sleep(3)

        web_url = f"file://{web_file.absolute()}"
        print(f"Opening web interface: {web_url}")
        webbrowser.open(web_url)

        print("\nWeb interface is now running!")
        print("API Server: http://127.0.0.1:8000")
        print("API Docs: http://127.0.0.1:8000/docs")
        print("Keep this terminal window open to keep the API server running.")
        print("Press Ctrl+C to stop the server and return to menu.")

        try:
            server_process.join()
        except KeyboardInterrupt:
            print("\nStopping server...")
            server_process.terminate()
            server_process.join()
            print("Server stopped successfully.")

    except ImportError as e:
        if "uvicorn" in str(e):
            print("Error: uvicorn not installed!")
            print("Install with: pip install uvicorn[standard]")
        else:
            print(f"Import Error: {e}")
        input("Press Enter to continue...")
    except Exception as e:
        print(f"Error starting web interface: {e}")
        input("Press Enter to continue...")


# -----------------------------
# CLI interface functions
# -----------------------------
def print_books(lib: Library):
    books = lib.list_books()
    if not books:
        print("No books in the library.")
    else:
        for b in books:
            print(b)
    input("Press Enter to continue...")


def print_members(mgr: MemberManager):
    members = mgr.list_members()
    if not members:
        print("No members in the system.")
    else:
        for m in members:
            print(m)
    input("Press Enter to continue...")


def add_book_flow(lib: Library):
    print("\nSelect Book Addition Method:")
    print("1) Add book automatically using ISBN (from Open Library API)")
    print("2) Add book manually (enter all details)")
    method = input("Enter (1-2): ").strip()

    if method == "1":
        isbn = input("Enter ISBN: ").strip()
        if not isbn:
            print("ISBN cannot be empty.")
            input("Press Enter to continue...")
            return
        try:
            print("Fetching book information from Open Library...")
            success = lib.add_book_from_isbn(isbn)
            if success:
                print("Book added successfully from API!")
                book = lib.find_book(isbn)
                if book:
                    print("Added:", book)
        except Exception as e:
            print("Error:", e)

    elif method == "2":
        print("\nSelect Book Type:")
        print("1) Printed Book")
        print("2) E-Book")
        print("3) Audiobook")
        btype = input("Enter (1-3): ").strip()

        title = input("Title: ").strip()
        author = input("Author: ").strip()
        isbn = input("ISBN: ").strip()

        try:
            if btype == "1":
                book = Book(title=title, author=author, isbn=isbn)
            elif btype == "2":
                file_format = input("File Format (e.g., PDF, EPUB): ").strip() or "PDF"
                book = EBook(title=title, author=author, isbn=isbn, file_format=file_format)
            elif btype == "3":
                duration = int(input("Duration (mins): ").strip() or "0")
                book = AudioBook(title=title, author=author, isbn=isbn, duration=duration)
            else:
                print("Invalid book type.")
                input("Press Enter to continue...")
                return

            lib.add_book(book)
            print("Book added manually.")
        except ValueError as e:
            print("Error:", e)
    else:
        print("Invalid method.")

    input("Press Enter to continue...")


def remove_book_flow(lib: Library):
    isbn = input("Enter ISBN to remove: ").strip()
    try:
        lib.remove_book(isbn)
        print("Book removed.")
    except ValueError as e:
        print("Error:", e)
    input("Press Enter to continue...")


def search_book_flow(lib: Library):
    isbn = input("Enter ISBN to search: ").strip()
    b = lib.find_book(isbn)
    if b:
        print(b)
    else:
        print("Not found.")
    input("Press Enter to continue...")


def add_member_flow(mgr: MemberManager):
    name = input("Member Name: ").strip()
    member_id = input("Member ID: ").strip()
    email = input("Email: ").strip()
    member = Member(name=name, member_id=member_id, email=email)
    try:
        mgr.add_member(member)
        print("Member added.")
    except ValueError as e:
        print("Error:", e)
    input("Press Enter to continue...")


def borrow_book_flow(lib: Library, mgr: MemberManager):
    member_id = input("Enter Member ID: ").strip()
    isbn = input("Enter ISBN of the book to borrow: ").strip()
    member = mgr.find_member(member_id)
    book = lib.find_book(isbn)

    if not member:
        print("Member not found.")
        input("Press Enter to continue...")
        return
    if not book:
        print("Book not found.")
        input("Press Enter to continue...")
        return

    try:
        book.borrow_book()
        member.borrow_book(isbn)
        lib.save_books()
        mgr.save_members()
        print("Book borrowed successfully.")
    except ValueError as e:
        print("Error:", e)
    input("Press Enter to continue...")


def return_book_flow(lib: Library, mgr: MemberManager):
    member_id = input("Enter Member ID: ").strip()
    isbn = input("Enter ISBN of the book to return: ").strip()
    member = mgr.find_member(member_id)
    book = lib.find_book(isbn)

    if not member:
        print("Member not found.")
        input("Press Enter to continue...")
        return
    if not book:
        print("Book not found.")
        input("Press Enter to continue...")
        return

    try:
        book.return_book()
        member.return_book(isbn)
        lib.save_books()
        mgr.save_members()
        print("Book returned successfully.")
    except ValueError as e:
        print("Error:", e)
    input("Press Enter to continue...")


# -----------------------------
# Interface selection
# -----------------------------
def select_interface():
    while True:
        print("\n" + "=" * 60)
        print("LIBRARY MANAGEMENT SYSTEM")
        print("=" * 60)
        print("Choose your interface:")
        print("1) Command Line Interface (CLI)")
        print("2) Web Interface (Browser)")
        print("3) Exit")

        choice = input("Select interface (1-3): ").strip()

        if choice == "1":
            return "cli"
        elif choice == "2":
            return "web"
        elif choice == "3":
            print("Goodbye!")
            return "exit"
        else:
            print("Invalid choice. Enter 1, 2, or 3.")
            input("Press Enter to try again...")


# -----------------------------
# CLI runner
# -----------------------------
def run_cli_interface():
    lib = Library("library.json")
    member_manager = MemberManager("members.json")

    MENU = """
Library Management CLI
1) Add a Book
2) Remove a Book
3) List All Books
4) Search for a Book
5) Add a Member
6) List Members
7) Borrow a Book
8) Return a Book
9) Back to Interface Selection
0) Exit
Choice: """

    while True:
        choice = input(MENU).strip()

        if choice == "1":
            add_book_flow(lib)
        elif choice == "2":
            remove_book_flow(lib)
        elif choice == "3":
            print_books(lib)
        elif choice == "4":
            search_book_flow(lib)
        elif choice == "5":
            add_member_flow(member_manager)
        elif choice == "6":
            print_members(member_manager)
        elif choice == "7":
            borrow_book_flow(lib, member_manager)
        elif choice == "8":
            return_book_flow(lib, member_manager)
        elif choice == "9":
            return
        elif choice == "0":
            print("Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice. Enter a number between 0 and 9.")
            input("Press Enter to try again...")


# -----------------------------
# Main entry point
# -----------------------------
def main():
    while True:
        interface_choice = select_interface()

        if interface_choice == "cli":
            run_cli_interface()
        elif interface_choice == "web":
            start_web_interface()
        elif interface_choice == "exit":
            break


if __name__ == "__main__":
    main()
