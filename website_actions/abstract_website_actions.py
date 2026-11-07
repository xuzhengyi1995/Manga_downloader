'''
Abstract website actions, XU Zhengyi, 2020/05/05
'''
import unicodedata
from abc import ABC, abstractmethod
from dataclasses import dataclass


def clean_text(value) -> str:
    '''Make remote text safe for terminals/logs: drop control (Cc) and format (Cf)
    characters such as ESC, BEL, C1 CSI and bidi overrides, then collapse whitespace.'''
    text = ''.join(' ' if ch.isspace() else ch for ch in str(value or '')
                   if ch.isspace() or unicodedata.category(ch) not in ('Cc', 'Cf'))
    return ' '.join(text.split())


@dataclass
class Book:
    '''A book in the user's library.'''
    id: str
    title: str
    read_url: str
    author: str = ''


class WebsiteActions(ABC):
    '''
    Base class for all website actions.
    '''
    login_url: str = ''
    library_url: str = ''

    def get_class_name(self) -> str:
        return self.__class__.__name__

    @staticmethod
    @abstractmethod
    def check_url(manga_url) -> bool:
        '''Give a manga url and check if the website is this class.'''

    @abstractmethod
    def is_logged_in(self, driver) -> bool:
        '''Return True if the browser session is logged in.'''

    @abstractmethod
    def list_library(self, driver) -> list[Book]:
        '''Return the books the logged-in user can read.'''

    @abstractmethod
    def resolve_book(self, id_or_url) -> Book:
        '''Turn a book id or viewer URL into a Book.'''

    def before_download(self, driver):
        '''Run after the viewer loaded, e.g. to close hint windows.'''

    @abstractmethod
    def get_book_title(self, driver) -> str:
        '''Title of the book currently open in the viewer.'''

    @abstractmethod
    def get_sum_page_count(self, driver) -> int:
        '''Total page count of the book.'''

    @abstractmethod
    def get_now_page(self, driver) -> int:
        '''Current page, 1-based.'''

    @abstractmethod
    def move_to_page(self, driver, page) -> bool:
        '''Move to the given 0-based page. Return True if the page changed.'''

    @abstractmethod
    def wait_loading(self, driver):
        '''Wait until the current page is rendered.'''

    @abstractmethod
    def get_imgdata(self, driver, now_page) -> bytes:
        '''Image bytes of the current page.'''
