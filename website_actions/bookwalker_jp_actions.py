'''
Website actions for bookwalker.jp
'''
import base64

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
        return int(str(driver.find_element_by_id('pageSliderCounter').text).split('/')[1])

    def move_to_page(self, driver, page):
        driver.execute_script(
            'NFBR.a6G.Initializer.B0U.menu.a6l.moveToPage(%d)' % page)

    def wait_loading(self, driver):
        WebDriverWait(driver, 30).until_not(lambda x: self.check_is_loading(
            x.find_elements_by_css_selector(".loading")))

    def get_imgdata(self, driver, now_page):
        canvas = driver.find_element_by_css_selector(".currentScreen canvas")
        img_base64 = driver.execute_script(
            "return arguments[0].toDataURL('image/jpeg').substring(22);", canvas)
        return base64.b64decode(img_base64)

    def get_now_page(self, driver):
        return int(str(driver.find_element_by_id('pageSliderCounter').text).split('/')[0])
