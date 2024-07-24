import os
from datetime import datetime, timedelta

class Book:
    def __init__(self, title, author, isbn):
        self.title = title
        self.author = author
        self.isbn = isbn
        self.is_checked_out = False
        self.due_date = None

    def get_title(self):
        return self.title

    def get_author(self):
        return self.author

    def get_isbn(self):
        return self.isbn

    def is_checked_out(self):
        return self.is_checked_out

    def get_due_date(self):
        return self.due_date

    def check_out(self):
        self.is_checked_out = True
        self.due_date = datetime.now() + timedelta(days=14)

    def return_book(self):
        self.is_checked_out = False
        self.due_date = None

    def __str__(self):
        return f"Title: {self.title}, Author: {self.author}, ISBN: {self.isbn}, Checked Out: {self.is_checked_out}, Due Date: {self.due_date}"

class Library:
    LIBRARY_FILE = "library.txt"

    def __init__(self):
        self.books = []
        self.load_library()

    def add_book(self, book):
        self.books.append(book)

    def remove_book(self, isbn):
        self.books = [book for book in self.books if book.get_isbn() != isbn]

    def find_book(self, isbn):
        for book in self.books:
            if book.get_isbn() == isbn:
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
        for book in self.books:
            if book.is_checked_out and book.get_due_date() < today:
                days_overdue = (today - book.get_due_date()).days
                print(f"{book} - Days Overdue: {days_overdue}")

    def save_library(self):
        try:
            with open(self.LIBRARY_FILE, 'w') as writer:
                for book in self.books:
                    writer.write(f"{book.get_title()},{book.get_author()},{book.get_isbn()},{book.is_checked_out},{book.get_due_date()}\n")
            print("Library saved successfully.")
        except IOError as e:
            print(f"Error saving library: {e}")

    def load_library(self):
        if not os.path.exists(self.LIBRARY_FILE):
            return
        try:
            with open(self.LIBRARY_FILE, 'r') as reader:
                for line in reader:
                    parts = line.strip().split(',')
                    book = Book(parts[0], parts[1], parts[2])
                    if parts[3] == 'True':
                        book.check_out()
                        book.due_date = datetime.strptime(parts[4], '%Y-%m-%d %H:%M:%S.%f')
                    self.books.append(book)
            print("Library loaded successfully.")
        except IOError as e:
            print(f"Error loading library: {e}")

class LibraryManagementSystem:
    library = Library()

    @staticmethod
    def main():
        while True:
            LibraryManagementSystem.display_menu()
            choice = LibraryManagementSystem.get_int_input("Enter your choice: ")
            if choice == 1:
                LibraryManagementSystem.add_book()
            elif choice == 2:
                LibraryManagementSystem.remove_book()
            elif choice == 3:
                LibraryManagementSystem.find_book()
            elif choice == 4:
                LibraryManagementSystem.check_out_book()
            elif choice == 5:
                LibraryManagementSystem.return_book()
            elif choice == 6:
                LibraryManagementSystem.display_overdue_books()
            elif choice == 7:
                LibraryManagementSystem.library.save_library()
            elif choice == 8:
                print("Exiting...")
                return
            else:
                print("Invalid choice. Please try again.")

    @staticmethod
    def display_menu():
        print("\n--- Library Management System ---")
        print("1. Add a book")
        print("2. Remove a book")
        print("3. Find a book")
        print("4. Check out a book")
        print("5. Return a book")
        print("6. Display overdue books")
        print("7. Save library")
        print("8. Exit")

    @staticmethod
    def add_book():
        title = LibraryManagementSystem.get_string_input("Enter book title: ")
        author = LibraryManagementSystem.get_string_input("Enter book author: ")
        isbn = LibraryManagementSystem.get_string_input("Enter book ISBN: ")
        LibraryManagementSystem.library.add_book(Book(title, author, isbn))
        print("Book added successfully.")

    @staticmethod
    def remove_book():
        isbn = LibraryManagementSystem.get_string_input("Enter ISBN of book to remove: ")
        LibraryManagementSystem.library.remove_book(isbn)
        print("Book removed successfully.")

    @staticmethod
    def find_book():
        isbn = LibraryManagementSystem.get_string_input("Enter ISBN of book to find: ")
        book = LibraryManagementSystem.library.find_book(isbn)
        if book:
            print("Book found:", book)
        else:
            print("Book not found.")

    @staticmethod
    def check_out_book():
        isbn = LibraryManagementSystem.get_string_input("Enter ISBN of book to check out: ")
        LibraryManagementSystem.library.check_out_book(isbn)

    @staticmethod
    def return_book():
        isbn = LibraryManagementSystem.get_string_input("Enter ISBN of book to return: ")
        LibraryManagementSystem.library.return_book(isbn)

    @staticmethod
    def display_overdue_books():
        LibraryManagementSystem.library.display_overdue_books()

    @staticmethod
    def get_string_input(prompt):
        return input(prompt)

    @staticmethod
    def get_int_input(prompt):
        while True:
            try:
                return int(input(prompt))
            except ValueError:
                print("Invalid input. Please enter a number.")

if __name__ == "__main__":
    LibraryManagementSystem.main()