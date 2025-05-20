import datetime
import os
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Book:
    title: str
    author: str
    isbn: str
    is_checked_out: bool = False
    due_date: Optional[datetime.date] = None

    def check_out(self) -> None:
        self.is_checked_out = True
        self.due_date = datetime.date.today() + datetime.timedelta(days=14)

    def return_book(self) -> None:
        self.is_checked_out = False
        self.due_date = None

    def __str__(self) -> str:
        return (
            f"Title: {self.title}, Author: {self.author}, ISBN: {self.isbn}, "
            f"Checked Out: {self.is_checked_out}, Due Date: {self.due_date}"
        )


class Library:
    LIBRARY_FILE = "library.txt"

    def __init__(self) -> None:
        self.books: List[Book] = []
        self.load_library()

    def add_book(self, book: Book) -> None:
        self.books.append(book)

    def remove_book(self, isbn: str) -> None:
        self.books = [book for book in self.books if book.isbn != isbn]

    def find_book(self, isbn: str) -> Optional[Book]:
        return next((book for book in self.books if book.isbn == isbn), None)

    def check_out_book(self, isbn: str) -> None:
        book = self.find_book(isbn)
        if book and not book.is_checked_out:
            book.check_out()
            print("Book checked out successfully.")
        else:
            print("Book not available for checkout.")

    def return_book(self, isbn: str) -> None:
        book = self.find_book(isbn)
        if book and book.is_checked_out:
            book.return_book()
            print("Book returned successfully.")
        else:
            print("Invalid return operation.")

    def display_overdue_books(self) -> None:
        today = datetime.date.today()
        for book in self.books:
            if book.is_checked_out and book.due_date and book.due_date < today:
                overdue_days = (today - book.due_date).days
                print(f"{book} - Days Overdue: {overdue_days}")

    def save_library(self) -> None:
        try:
            with open(self.LIBRARY_FILE, "w") as file:
                for book in self.books:
                    file.write(
                        f"{book.title},{book.author},{book.isbn},"
                        f"{book.is_checked_out},{book.due_date}\n"
                    )
            print("Library saved successfully.")
        except IOError as e:
            print(f"Error saving library: {e}")

    def load_library(self) -> None:
        if not os.path.exists(self.LIBRARY_FILE):
            return

        try:
            with open(self.LIBRARY_FILE, "r") as file:
                for line in file:
                    parts = line.strip().split(",")
                    if len(parts) < 4:
                        continue
                    book = Book(parts[0], parts[1], parts[2])
                    if parts[3] == "True":
                        book.check_out()
                        if len(parts) > 4 and parts[4] != "None":
                            book.due_date = datetime.date.fromisoformat(parts[4])
                    self.books.append(book)
            print("Library loaded successfully.")
        except IOError as e:
            print(f"Error loading library: {e}")


def get_string_input(prompt: str) -> str:
    return input(prompt)


def get_int_input(prompt: str) -> int:
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Invalid input. Please enter a number.")


def display_menu() -> None:
    print("\n--- Library Management System ---")
    print("1. Add a book")
    print("2. Remove a book")
    print("3. Find a book")
    print("4. Check out a book")
    print("5. Return a book")
    print("6. Display overdue books")
    print("7. Save library")
    print("8. Exit")


def main() -> None:
    library = Library()
    while True:
        display_menu()
        choice = get_int_input("Enter your choice: ")
        if choice == 1:
            title = get_string_input("Enter book title: ")
            author = get_string_input("Enter book author: ")
            isbn = get_string_input("Enter book ISBN: ")
            library.add_book(Book(title, author, isbn))
            print("Book added successfully.")
        elif choice == 2:
            isbn = get_string_input("Enter ISBN of book to remove: ")
            library.remove_book(isbn)
            print("Book removed successfully.")
        elif choice == 3:
            isbn = get_string_input("Enter ISBN of book to find: ")
            book = library.find_book(isbn)
            print("Book found: " + str(book) if book else "Book not found.")
        elif choice == 4:
            isbn = get_string_input("Enter ISBN of book to check out: ")
            library.check_out_book(isbn)
        elif choice == 5:
            isbn = get_string_input("Enter ISBN of book to return: ")
            library.return_book(isbn)
        elif choice == 6:
            library.display_overdue_books()
        elif choice == 7:
            library.save_library()
        elif choice == 8:
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()
