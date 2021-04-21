'''
Website actions for www.cmoa.jp
'''
import base64
from io import BytesIO

import PIL.Image as pil_image
from selenium.webdriver.support.ui import WebDriverWait

try:
    from abstract_website_actions import WebsiteActions
except:
    from website_actions.abstract_website_actions import WebsiteActions


class CmoaJP(WebsiteActions):
    '''
    cmoa.jp
    '''
    login_url = 'https://www.cmoa.jp/'

    @staticmethod
    def get_file_content_chrome(driver, uri):
        result = driver.execute_async_script("""
        var uri = arguments[0];
        var callback = arguments[1];
        var toBase64 = function(buffer){for(var r,n=new Uint8Array(buffer),t=n.length,a=new Uint8Array(4*Math.ceil(t/3)),i=new Uint8Array(64),o=0,c=0;64>c;++c)i[c]="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/".charCodeAt(c);for(c=0;t-t%3>c;c+=3,o+=4)r=n[c]<<16|n[c+1]<<8|n[c+2],a[o]=i[r>>18],a[o+1]=i[r>>12&63],a[o+2]=i[r>>6&63],a[o+3]=i[63&r];return t%3===1?(r=n[t-1],a[o]=i[r>>2],a[o+1]=i[r<<4&63],a[o+2]=61,a[o+3]=61):t%3===2&&(r=(n[t-2]<<8)+n[t-1],a[o]=i[r>>10],a[o+1]=i[r>>4&63],a[o+2]=i[r<<2&63],a[o+3]=61),new TextDecoder("ascii").decode(a)};
        var xhr = new XMLHttpRequest();
        xhr.responseType = 'arraybuffer';
        xhr.onload = function(){ callback(toBase64(xhr.response)) };
        xhr.onerror = function(){ callback(xhr.status) };
        xhr.open('GET', uri);
        xhr.send();
        """, uri)
        if type(result) == int:
            raise Exception("Request failed with status %s" % result)
        return base64.b64decode(result)

    @staticmethod
    def check_url(manga_url):
        return manga_url.find('cmoa.jp/bib/speedreader') != -1

    def get_sum_page_count(self, driver):
        return int(str(driver.execute_script("return document.getElementById('menu_slidercaption').innerHTML")).split('/')[1])

    def move_to_page(self, driver, page):
        driver.execute_script(
            'SpeedBinb.getInstance("content").moveTo(%d)' % page)

    def wait_loading(self, driver):
        WebDriverWait(driver, 600).until_not(
            lambda x: x.find_element_by_id("start_wait"))

    def get_imgdata(self, driver, now_page):
        image_elements = driver.find_element_by_id(
            'content-p%d' % now_page).find_elements_by_css_selector('img')

        imgs_arr = []
        imgs_height = [0]
        mmset = 4
        for i in image_elements:
            blob_url = i.get_attribute('src')
            image_data = self.get_file_content_chrome(driver, blob_url)
            part_img = pil_image.open(BytesIO(image_data))
            imgs_arr.append(part_img)
            width, height = part_img.size
            imgs_height.append(height + imgs_height[-1] - mmset)

        last_img_height = imgs_height.pop() + mmset

        final_img = pil_image.new('RGB', (width, last_img_height))

        for i in range(len(imgs_arr)):
            final_img.paste(imgs_arr[i], (0, imgs_height[i]))

        final_data = BytesIO()
        final_img.save(final_data, format='PNG')
        return final_data.getbuffer()

    def get_now_page(self, driver):
        return int(str(driver.execute_script("return document.getElementById('menu_slidercaption').innerHTML")).split('/')[0])

    def before_download(self, driver):
        driver.execute_script('parent.closeTips()')
