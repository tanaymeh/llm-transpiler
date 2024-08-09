import os
import json
from datetime import datetime, timedelta


class Book:
    def __init__(self, title, author, isbn):
        self.title = title
        self.author = author
        self.isbn = isbn
        self.is_checked_out = False
        self.due_date = None

    def check_out(self):
        self.is_checked_out = True
        self.due_date = datetime.now() + timedelta(days=14)  # Due in 14 days

    def return_book(self):
        self.is_checked_out = False
        self.due_date = None

    def __str__(self):
        return f"Title: {self.title}, Author: {self.author}, ISBN: {self.isbn}, Checked Out: {self.is_checked_out}, Due Date: {self.due_date}"


class Library:
    LIBRARY_FILE = "library.json"

    def __init__(self):
        self.books = []
        self.load_library()

    def add_book(self, book):
        self.books.append(book)

    def remove_book(self, isbn):
        self.books = [book for book in self.books if book.isbn != isbn]

    def find_book(self, isbn):
        for book in self.books:
            if book.isbn == isbn:
                return book
        return None

    def check_out_book(self, isbn):
        book = self.find_book(isbn)
        if book and not book.is_checked_out:
            book.check_out()
            print("Book checked out successfully.")
        else:
            print("Book not available for checkout.")

    def return_book(self, isbn):
        book = self.find_book(isbn)
        if book and book.is_checked_out:
            book.return_book()
            print("Book returned successfully.")
        else:
            print("Invalid return operation.")

    def display_overdue_books(self):
        today = datetime.now()
        overdue_books = [
            book for book in self.books if book.is_checked_out and book.due_date < today
        ]
        for book in overdue_books:
            days_overdue = (today - book.due_date).days
            print(f"{book} - Days Overdue: {days_overdue}")

    def save_library(self):
        try:
            with open(self.LIBRARY_FILE, "w") as file:
                json.dump(
                    [
                        {
                            "title": book.title,
                            "author": book.author,
                            "isbn": book.isbn,
                            "is_checked_out": book.is_checked_out,
                            "due_date": (
                                book.due_date.isoformat() if book.due_date else None
                            ),
                        }
                        for book in self.books
                    ],
                    file,
                )
            print("Library saved successfully.")
        except IOError as e:
            print(f"Error saving library: {e}")

    def load_library(self):
        if os.path.exists(self.LIBRARY_FILE):
            try:
                with open(self.LIBRARY_FILE, "r") as file:
                    books_data = json.load(file)
                    for data in books_data:
                        book = Book(data["title"], data["author"], data["isbn"])
                        if data["is_checked_out"]:
                            book.check_out()
                            book.due_date = datetime.fromisoformat(data["due_date"])
                        self.books.append(book)
                print("Library loaded successfully.")
            except IOError as e:
                print(f"Error loading library: {e}")


class LibraryManagementSystem:
    def __init__(self):
        self.library = Library()

    def main(self):
        while True:
            self.display_menu()
            choice = self.get_int_input("Enter your choice: ")
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
                self.display_overdue_books()
            elif choice == 7:
                self.library.save_library()
            elif choice == 8:
                print("Exiting...")
                break
            else:
                print("Invalid choice. Please try again.")

    def display_menu(self):
        print("\n--- Library Management System ---")
        print("1. Add a book")
        print("2. Remove a book")
        print("3. Find a book")
        print("4. Check out a book")
        print("5. Return a book")
        print("6. Display overdue books")
        print("7. Save library")
        print("8. Exit")

    def add_book(self):
        title = self.get_string_input("Enter book title: ")
        author = self.get_string_input("Enter book author: ")
        isbn = self.get_string_input("Enter book ISBN: ")
        self.library.add_book(Book(title, author, isbn))
        print("Book added successfully.")

    def remove_book(self):
        isbn = self.get_string_input("Enter ISBN of book to remove: ")
        self.library.remove_book(isbn)
        print("Book removed successfully.")

    def find_book(self):
        isbn = self.get_string_input("Enter ISBN of book to find: ")
        book = self.library.find_book(isbn)
        if book:
            print("Book found: " + str(book))
        else:
            print("Book not found.")

    def check_out_book(self):
        isbn = self.get_string_input("Enter ISBN of book to check out: ")
        self.library.check_out_book(isbn)

    def return_book(self):
        isbn = self.get_string_input("Enter ISBN of book to return: ")
        self.library.return_book(isbn)

    def display_overdue_books(self):
        self.library.display_overdue_books()

    def get_string_input(self, prompt):
        return input(prompt)

    def get_int_input(self, prompt):
        while True:
            try:
                return int(input(prompt))
            except ValueError:
                print("Invalid input. Please enter a number.")


if __name__ == "__main__":
    LibraryManagementSystem().main()
