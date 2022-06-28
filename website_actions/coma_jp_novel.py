'''
Website actions for coma.jp novels
'''
import base64
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

try:
    from abstract_website_actions import WebsiteActions
except:
    from website_actions.abstract_website_actions import WebsiteActions


class CmoaJPNovels(WebsiteActions):
    '''
    coma.jp novels
    '''
    login_url = 'https://www.cmoa.jp/'

    def next_page(self, driver):
        driver.execute_script('moveNextPageSpeech()')

    def prev_page(self, driver):
        driver.execute_script('movePrevPageSpeech()')

    def is_finished(self, driver):
        return driver.execute_script('return ZHL0PP.Z060JL()')

    @staticmethod
    def check_url(manga_url):
        return manga_url.find('cmoa.jp/bib/reader') != -1

    def get_sum_page_count(self, driver):
        self.now_page = 0
        sum_page = 0
        while not self.is_finished(driver):
            sum_page += 1
            self.next_page(driver)
            time.sleep(0.5)

        for _ in range(sum_page):
            self.prev_page(driver)
            time.sleep(0.5)

        return sum_page

    def move_to_page(self, driver, page):
        if page == self.now_page:
            return

        f_to_use = self.next_page
        if page < self.now_page:
            f_to_use = self.prev_page

        for _ in range(abs(page - self.now_page)):
            f_to_use(driver)

        self.now_page = page

    def wait_loading(self, driver):
        WebDriverWait(driver, 600).until_not(
            lambda x: x.find_element(By.ID, 'ctmble_menu_notification_overlay_span').is_displayed())

    def get_imgdata(self, driver, now_page):
        return driver.get_screenshot_as_png()

    def get_now_page(self, driver):
        return self.now_page + 1

    def before_download(self, driver):
        WebDriverWait(driver, 600).until_not(
            lambda x: x.find_element(By.ID, 'preMessage'))
        driver.switch_to.frame(driver.find_element(By.ID, 'binb'))
        WebDriverWait(driver, 600).until_not(
            lambda x: x.find_element(By.ID, 'msg_outer_div').is_displayed())
