from pydantic import BaseModel, EmailStr
from typing import List, NoReturn


# Task 1
class Book(BaseModel):
    title: str
    author: str
    year: int
    available: bool
    categories: List[str]  # Task 3


class User(BaseModel):
    name: str
    email: EmailStr
    membership_id: str


# Task 3
class Library(BaseModel):
    books: List[Book]
    users: List[User]

    def total_books(self) -> NoReturn:
        total = 0
        for book in self.books:
            if book.available == True:
                total += 1
        print(f"There are {total} books in the Library.")


class BookNotAvailable(Exception):
    def __init__(self, msg="This book is not available!") -> NoReturn:
        self.message = msg
        super().__init__(self.message)


# Task 2
def add_book(library: Library, book: Book) -> NoReturn:
    library.books.append(book)
    print(f"The book {book.author}-{book.title} is added to the Library!")


def find_book(library: Library, book: Book) -> str:
    if book in library.books:
        return f"The book {book.author}-{book.title} is on the Library's list."
    else:
        return f"The book {book.author}-{book.title} is not on the Library's list."


def is_book_borrow(book: Book) -> NoReturn:
    # Task 2
    #  if book.available == True:
    #     return f"The book {book.author}-{book.title} is available now!"
    # else:
    #     return f"The book {book.author}-{book.title} is borrowed!"
    # Task 4
    try:
        if book.available == False:
            raise BookNotAvailable
        else:
            print(f"The book {book.author}-{book.title} is available now!")
    except BookNotAvailable as exp:
        print(f"{book.author}-{book.title}. {exp}")


def return_book(book: Book) -> NoReturn:
    if book.available == False:
        book.available = True
        print(f"The book {book.author}-{book.title} has been returned!")
    else:
        print(
            f"The book {book.author}-{book.title} is not borrowed! It's available now!"
        )


# Test
if __name__ == "__main__":
    first_user = User(name="Akim", email="akim@ya.ru", membership_id="id1")
    print(first_user)
    Demian = Book(
        title="Demian",
        author="Herman Hesse",
        year=1919,
        available=True,
        categories=["World classic"],
    )
    Sunday = Book(
        title="Voskresenie",
        author="Lev Tolstoy",
        year=1899,
        available=True,
        categories=["Russian classic"],
    )
    FairyTales = Book(
        title="Fairy Tales",
        author="Aleksander Pushkin",
        year=1830,
        available=True,
        categories=["Russian fairy tales"],
    )
    My_labrirary = Library(books=[], users=[])
    add_book(My_labrirary, Demian)
    add_book(My_labrirary, Sunday)
    add_book(My_labrirary, FairyTales)
    print(My_labrirary.books)
    My_labrirary.total_books()
    return_book(Demian)
    Sunday.available = False
    is_book_borrow(Sunday)
    My_labrirary.total_books()
    return_book(Sunday)
    My_labrirary.total_books()
    is_book_borrow(Sunday)
    print(find_book(My_labrirary, FairyTales))
