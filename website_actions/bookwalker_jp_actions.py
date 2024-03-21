'''
Website actions for bookwalker.jp
'''
import base64

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

try:
    from abstract_website_actions import WebsiteActions
except:
    from website_actions.abstract_website_actions import WebsiteActions


class BookwalkerJP(WebsiteActions):
    '''
    bookwalker.jp
    '''
    login_url = 'https://member.bookwalker.jp/app/03/login'
    js = ''

    def check_is_loading(self, list_ele):
        '''
        Check is loading.
        '''
        is_loading = False
        for i in list_ele:
            if i.is_displayed() is True:
                is_loading = True
                break
        return is_loading

    @staticmethod
    def check_url(manga_url):
        return manga_url.find('bookwalker.jp') != -1

    def get_sum_page_count(self, driver):
        return int(str(driver.find_element(By.ID, 'pageSliderCounter').get_attribute('textContent')).split('/')[1])

    def move_to_page(self, driver, page):
        driver.execute_script(
            f'NFBR.a6G.Initializer.{self.js}.menu.options.a6l.moveToPage(%d)' % page)

    def wait_loading(self, driver):
        WebDriverWait(driver, 600).until_not(lambda x: self.check_is_loading(
            x.find_elements(By.CSS_SELECTOR, ".loading")))

    def get_imgdata(self, driver, now_page):
        canvas = driver.find_element(By.CSS_SELECTOR, ".currentScreen canvas")
        img_base64 = driver.execute_script(
            "return arguments[0].toDataURL('image/png', 1.0).substring(21);", canvas)
        return base64.b64decode(img_base64)

    def get_now_page(self, driver):
        return int(str(driver.find_element(By.ID, 'pageSliderCounter').get_attribute('textContent')).split('/')[0])
    
    def before_download(self, driver):
        for key in driver.execute_script('return Object.keys(NFBR.a6G.Initializer)'):
            if 'menu' in driver.execute_script(f'return Object.keys(NFBR.a6G.Initializer.{key})'):
                self.js = key
                break
