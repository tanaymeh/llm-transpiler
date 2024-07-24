import java.io.*;
import java.util.*;
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;

class Book {
    private String title;
    private String author;
    private String isbn;
    private boolean isCheckedOut;
    private LocalDate dueDate;

    public Book(String title, String author, String isbn) {
        this.title = title;
        this.author = author;
        this.isbn = isbn;
        this.isCheckedOut = false;
        this.dueDate = null;
    }

    // Getters and setters
    public String getTitle() { return title; }
    public String getAuthor() { return author; }
    public String getIsbn() { return isbn; }
    public boolean isCheckedOut() { return isCheckedOut; }
    public LocalDate getDueDate() { return dueDate; }

    public void checkOut() {
        isCheckedOut = true;
        dueDate = LocalDate.now().plusDays(14); // Due in 14 days
    }

    public void returnBook() {
        isCheckedOut = false;
        dueDate = null;
    }

    @Override
    public String toString() {
        return String.format("Title: %s, Author: %s, ISBN: %s, Checked Out: %s, Due Date: %s",
                title, author, isbn, isCheckedOut, dueDate);
    }
}

class Library {
    private List<Book> books;
    private static final String LIBRARY_FILE = "library.txt";

    public Library() {
        books = new ArrayList<>();
        loadLibrary();
    }

    public void addBook(Book book) {
        books.add(book);
    }

    public void removeBook(String isbn) {
        books.removeIf(book -> book.getIsbn().equals(isbn));
    }

    public Book findBook(String isbn) {
        return books.stream()
                .filter(book -> book.getIsbn().equals(isbn))
                .findFirst()
                .orElse(null);
    }

    public void checkOutBook(String isbn) {
        Book book = findBook(isbn);
        if (book != null && !book.isCheckedOut()) {
            book.checkOut();
            System.out.println("Book checked out successfully.");
        } else {
            System.out.println("Book not available for checkout.");
        }
    }

    public void returnBook(String isbn) {
        Book book = findBook(isbn);
        if (book != null && book.isCheckedOut()) {
            book.returnBook();
            System.out.println("Book returned successfully.");
        } else {
            System.out.println("Invalid return operation.");
        }
    }

    public void displayOverdueBooks() {
        LocalDate today = LocalDate.now();
        books.stream()
                .filter(Book::isCheckedOut)
                .filter(book -> book.getDueDate().isBefore(today))
                .forEach(book -> System.out.println(book + " - Days Overdue: " +
                        ChronoUnit.DAYS.between(book.getDueDate(), today)));
    }

    public void saveLibrary() {
        try (PrintWriter writer = new PrintWriter(new FileWriter(LIBRARY_FILE))) {
            for (Book book : books) {
                writer.println(String.format("%s,%s,%s,%b,%s",
                        book.getTitle(), book.getAuthor(), book.getIsbn(),
                        book.isCheckedOut(), book.getDueDate()));
            }
            System.out.println("Library saved successfully.");
        } catch (IOException e) {
            System.err.println("Error saving library: " + e.getMessage());
        }
    }

    private void loadLibrary() {
        try (BufferedReader reader = new BufferedReader(new FileReader(LIBRARY_FILE))) {
            String line;
            while ((line = reader.readLine()) != null) {
                String[] parts = line.split(",");
                Book book = new Book(parts[0], parts[1], parts[2]);
                if (Boolean.parseBoolean(parts[3])) {
                    book.checkOut();
                    book.getDueDate().parse(parts[4]);
                }
                books.add(book);
            }
            System.out.println("Library loaded successfully.");
        } catch (IOException e) {
            System.err.println("Error loading library: " + e.getMessage());
        }
    }
}

public class LibraryManagementSystem {
    private static Library library = new Library();
    private static Scanner scanner = new Scanner(System.in);

    public static void main(String[] args) {
        while (true) {
            displayMenu();
            int choice = getIntInput("Enter your choice: ");
            switch (choice) {
                case 1: addBook(); break;
                case 2: removeBook(); break;
                case 3: findBook(); break;
                case 4: checkOutBook(); break;
                case 5: returnBook(); break;
                case 6: displayOverdueBooks(); break;
                case 7: library.saveLibrary(); break;
                case 8: System.out.println("Exiting..."); return;
                default: System.out.println("Invalid choice. Please try again.");
            }
        }
    }

    private static void displayMenu() {
        System.out.println("\n--- Library Management System ---");
        System.out.println("1. Add a book");
        System.out.println("2. Remove a book");
        System.out.println("3. Find a book");
        System.out.println("4. Check out a book");
        System.out.println("5. Return a book");
        System.out.println("6. Display overdue books");
        System.out.println("7. Save library");
        System.out.println("8. Exit");
    }

    private static void addBook() {
        String title = getStringInput("Enter book title: ");
        String author = getStringInput("Enter book author: ");
        String isbn = getStringInput("Enter book ISBN: ");
        library.addBook(new Book(title, author, isbn));
        System.out.println("Book added successfully.");
    }

    private static void removeBook() {
        String isbn = getStringInput("Enter ISBN of book to remove: ");
        library.removeBook(isbn);
        System.out.println("Book removed successfully.");
    }

    private static void findBook() {
        String isbn = getStringInput("Enter ISBN of book to find: ");
        Book book = library.findBook(isbn);
        if (book != null) {
            System.out.println("Book found: " + book);
        } else {
            System.out.println("Book not found.");
        }
    }

    private static void checkOutBook() {
        String isbn = getStringInput("Enter ISBN of book to check out: ");
        library.checkOutBook(isbn);
    }

    private static void returnBook() {
        String isbn = getStringInput("Enter ISBN of book to return: ");
        library.returnBook(isbn);
    }

    private static void displayOverdueBooks() {
        library.displayOverdueBooks();
    }

    private static String getStringInput(String prompt) {
        System.out.print(prompt);
        return scanner.nextLine();
    }

    private static int getIntInput(String prompt) {
        while (true) {
            try {
                System.out.print(prompt);
                return Integer.parseInt(scanner.nextLine());
            } catch (NumberFormatException e) {
                System.out.println("Invalid input. Please enter a number.");
            }
        }
    }
}