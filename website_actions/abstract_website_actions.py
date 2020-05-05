'''
Abstract website actions, XU Zhengyi, 2020/05/05
'''

from abc import ABCMeta, abstractmethod


class WebsiteActions:
    '''
    Base class for all website actions.
    '''
    __metaclass__ = ABCMeta

    def __init__(self):
        self.class_name = self.__class__.__name__

    def get_class_name(self)->str:
        '''
        Get class name.
        '''
        return self.class_name

    @staticmethod
    @abstractmethod
    def check_url(manga_url)->bool:
        '''
        Give a manga url and check if the website is this class.
        '''
        return False

    @property
    @abstractmethod
    def login_url(self)->str:
        '''
        Login url property.
        '''
        pass

    @abstractmethod
    def get_sum_page_count(self, driver)->int:
        '''
        Get sum page count on for the manga.
        '''
        pass

    @abstractmethod
    def move_to_page(self, driver, page)->bool:
        '''
        Move to given page.
        '''
        pass

    @abstractmethod
    def wait_loading(self, driver):
        '''
        Wait page loading.
        '''
        pass

    def before_download(self, driver):
        '''
        Run after page loaded, can be used to close some hint windows.
        '''
        pass

    @abstractmethod
    def get_imgdata(self, driver, now_page):
        '''
        Get imgdata on the page. Return
        '''
        pass

    @abstractmethod
    def get_now_page(self, driver)->int:
        '''
        Get now page.
        '''
        pass
