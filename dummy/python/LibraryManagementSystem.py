import datetime
from datetime import timedelta
import sys


class Book:
    def __init__(self, title, author, isbn, checked_out=False, due_date=None):
        self.title = title
        self.author = author
        self.isbn = isbn
        self.checked_out = checked_out
        self.due_date = due_date  # datetime.date or None

    def check_out(self):
        self.checked_out = True
        self.due_date = datetime.date.today() + timedelta(days=14)

    def return_book(self):
        self.checked_out = False
        self.due_date = None

    def __str__(self):
        due = self.due_date.isoformat() if self.due_date else "N/A"
        return (
            f"Title: {self.title}, Author: {self.author}, ISBN: {self.isbn}, "
            f"Checked Out: {self.checked_out}, Due Date: {due}"
        )


class Library:
    LIBRARY_FILE = "library.txt"

    def __init__(self):
        self.books = []
        self.load()

    def add_book(self, book):
        self.books.append(book)

    def remove_book(self, isbn):
        self.books = [b for b in self.books if b.isbn != isbn]

    def find_book(self, isbn):
        for book in self.books:
            if book.isbn == isbn:
                return book
        return None

    def check_out_book(self, isbn):
        book = self.find_book(isbn)
        if book and not book.checked_out:
            book.check_out()
            print("Book checked out successfully.")
        else:
            print("Book not available for checkout.")

    def return_book(self, isbn):
        book = self.find_book(isbn)
        if book and book.checked_out:
            book.return_book()
            print("Book returned successfully.")
        else:
            print("Invalid return operation.")

    def display_overdue_books(self):
        today = datetime.date.today()
        for book in self.books:
            if book.checked_out and book.due_date < today:
                days_overdue = (today - book.due_date).days
                print(f"{book} - Days Overdue: {days_overdue}")

    def save(self):
        try:
            with open(self.LIBRARY_FILE, 'w') as f:
                for book in self.books:
                    due_str = book.due_date.isoformat() if book.due_date else ""
                    f.write(
                        f"{book.title},{book.author},{book.isbn},"
                        f"{book.checked_out},{due_str}\n"
                    )
            print("Library saved successfully.")
        except Exception as e:
            print(f"Error saving: {e}")

    def load(self):
        try:
            with open(self.LIBRARY_FILE, 'r') as f:
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) != 5:
                        continue  # Skip invalid lines
                    title, author, isbn, checked_out_str, due_str = parts
                    checked_out = checked_out_str.lower() == 'true'
                    due_date = datetime.date.fromisoformat(due_str) if due_str else None
                    book = Book(title, author, isbn, checked_out, due_date)
                    self.books.append(book)
            print("Library loaded successfully.")
        except FileNotFoundError:
            print("No saved library found. Starting with empty list.")
        except Exception as e:
            print(f"Error loading: {e}")


class LibraryManagementSystem:
    def __init__(self):
        self.library = Library()
        self.scanner = sys.stdin

    def run(self):
        while True:
            self.display_menu()
            choice = self.get_int("Enter choice: ")
            if choice == 1:
                self.add_book()
            elif choice == 2:
                self.remove_book()
            elif choice == 3:
                self.find_book()
            elif choice == 4:
                self.check_out_book()
            elif choice == 5:
                self.return_book()
            elif choice == 6:
                self.library.display_overdue_books()
            elif choice == 7:
                self.library.save()
            elif choice == 8:
                print("Exiting...")
                break
            else:
                print("Invalid choice.")

    def display_menu(self):
        print("\n--- Library Management System ---")
        print("1. Add a book\n2. Remove a book\n3. Find a book\n4. Check out a book")
        print("5. Return a book\n6. Display overdue books\n7. Save library\n8. Exit")

    def add_book(self):
        title = self.get_string("Enter title: ")
        author = self.get_string("Enter author: ")
        isbn = self.get_string("Enter ISBN: ")
        self.library.add_book(Book(title, author, isbn))
        print("Book added.")

    def remove_book(self):
        isbn = self.get_string("Enter ISBN: ")
        self.library.remove_book(isbn)
        print("Book removed.")

    def find_book(self):
        isbn = self.get_string("Enter ISBN: ")
        book = self.library.find_book(isbn)
        print(f"Found: {book}" if book else "Not found.")

    def check_out_book(self):
        isbn = self.get_string("Enter ISBN: ")
        self.library.check_out_book(isbn)

    def return_book(self):
        isbn = self.get_string("Enter ISBN: ")
        self.library.return_book(isbn)

    def get_string(self, prompt):
        print(prompt, end='')
        return input().strip()

    def get_int(self, prompt):
        while True:
            try:
                return int(input(prompt))
            except ValueError:
                print("Enter a number!")


if __name__ == "__main__":
    sys.exit(LibraryManagementSystem().run())
