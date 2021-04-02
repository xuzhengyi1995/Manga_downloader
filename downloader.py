'''
Main downloader, XU Zhengyi, 2020/05/05
'''
import base64
import logging
import os
import random
import time
from io import BytesIO

import PIL.Image as pil_image
import undetected_chromedriver as uc
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from website_actions import *
from website_actions.abstract_website_actions import WebsiteActions

logging.basicConfig(format='[%(levelname)s](%(name)s) %(asctime)s : %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)


def get_cookie_dict(cookies):
    cookies = cookies.split('; ')
    cookies_dict = {}
    for i in cookies:
        kv = i.split('=')
        cookies_dict[kv[0]] = kv[1]
    return cookies_dict


def add_cookies(driver, cookies):
    for i in cookies:
        driver.add_cookie({'name': i, 'value': cookies[i]})


class Downloader:
    '''
    Main download class
    '''

    def __init__(
            self, manga_url, cookies, imgdir, res, sleep_time=2, loading_wait_time=20,
            cut_image=None, file_name_prefix='', number_of_digits=3, start_page=None,
            end_page=None
    ):
        self.manga_url = manga_url
        self.cookies = get_cookie_dict(cookies)
        self.imgdir = imgdir
        self.res = res
        self.sleep_time = sleep_time
        self.loading_wait_time = loading_wait_time
        self.cut_image = cut_image
        self.file_name_model = '/'
        if len(file_name_prefix) != 0:
            self.file_name_model += file_name_prefix + '_'

        self.file_name_model += '%%0%dd.png' % number_of_digits
        self.start_page = start_page - 1 if start_page and start_page > 0 else 0
        self.end_page = end_page

        self.init_function()

    def check_implementation(self, this_manga_url):
        is_implemented_website = False
        for temp_actions_class in WebsiteActions.__subclasses__():
            if temp_actions_class.check_url(this_manga_url):
                is_implemented_website = True
                self.actions_class = temp_actions_class()
                logging.info('Find action class, use %s class.',
                             self.actions_class.get_class_name())
                break

        if not is_implemented_website:
            logging.error('This website has not been added...')
            raise NotImplementedError

    def get_driver(self):
        option = webdriver.ChromeOptions()
        option.set_capability('unhandledPromptBehavior', 'accept')
        option.add_argument('high-dpi-support=1')
        option.add_argument('device-scale-factor=1')
        option.add_argument('force-device-scale-factor=1')
        option.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36")
        option.add_argument('window-size=%d,%d' % self.res)
        option.add_argument('headless')
        # self.driver = webdriver.Chrome(chrome_options=option)
        self.driver = uc.Chrome(options=option)
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
              Object.defineProperty(navigator, 'webdriver', {
                get: () => false
              })
              window.navigator.chrome = undefined;
              Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
              });
              Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
              });
              const originalQuery = window.navigator.permissions.query;
              window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
              );
            """
        })

    def init_function(self):
        if self.cut_image is not None:
            self.left, self.upper, self.right, self.lower = self.cut_image
        self.get_driver()
        random.seed()

    def login(self):
        logging.info('Login...')
        driver = self.driver
        driver.get(self.actions_class.login_url)
        driver.delete_all_cookies()
        add_cookies(driver, self.cookies)
        logging.info('Login finished...')

    def prepare_download(self, this_image_dir, this_manga_url):
        if not os.path.isdir(this_image_dir):
            os.mkdir(this_image_dir)
        logging.info('Loading Book page...')
        driver = self.driver
        driver.set_window_size(self.res[0], self.res[1])
        driver.get(this_manga_url)
        logging.info('Book page Loaded...')
        logging.info('Preparing for downloading...')
        time.sleep(self.loading_wait_time)

    def download_book(self, this_image_dir):
        driver = self.driver
        logging.info('Run before downloading...')
        self.actions_class.before_download(driver)
        logging.info('Start download...')
        try:
            page_count = self.actions_class.get_sum_page_count(driver)
            logging.info('Has %d pages.', page_count)
            end_page = page_count
            if self.end_page and self.end_page <= page_count:
                end_page = self.end_page
            self.actions_class.move_to_page(driver, self.start_page)

            time.sleep(self.sleep_time)

            for i in range(self.start_page, end_page):
                self.actions_class.wait_loading(driver)
                image_data = self.actions_class.get_imgdata(driver, i + 1)
                with open(this_image_dir + self.file_name_model % i, 'wb') as img_file:
                    if self.cut_image is None:
                        img_file.write(image_data)
                    else:
                        org_img = pil_image.open(BytesIO(image_data))
                        width, height = org_img.size
                        org_img.crop(
                            (self.left, self.upper, width - self.right, height - self.lower)).save(img_file, format='PNG')

                logging.info('Page %d Downloaded', i + 1)
                if i == page_count - 1:
                    logging.info('Finished.')
                    return

                self.actions_class.move_to_page(driver, i + 1)

                WebDriverWait(driver, 300).until_not(
                    lambda x: self.actions_class.get_now_page(x) == i + 1)

                time.sleep(self.sleep_time + random.random() * 2)
        except Exception as err:
            with open("error.html", "w", encoding="utf-8") as err_source:
                err_source.write(driver.page_source)
            driver.save_screenshot('./error.png')
            logging.error('Something wrong or download finished,Please check the error.png to see the web page.\r\nNormally, you should logout and login, then renew the cookies to solve this problem.')
            logging.error(err)
            return

    def download(self):
        total_manga = len(self.manga_url)
        total_dir = len(self.imgdir)
        if total_manga != total_dir:
            logging.error('Total manga urls given not equal to imgdir.')
            return

        for i in range(total_manga):
            t_manga_url = self.manga_url[i]
            t_img_dir = self.imgdir[i]
            self.check_implementation(t_manga_url)
            if i == 0:
                self.login()
            logging.info("Starting download manga %d, imgdir: %s",
                         i + 1, t_img_dir)
            self.prepare_download(t_img_dir, t_manga_url)
            self.download_book(t_img_dir)
            logging.info("Finished download manga %d, imgdir: %s",
                         i + 1, t_img_dir)
            time.sleep(2)
        self.driver.close()
        self.driver.quit()
