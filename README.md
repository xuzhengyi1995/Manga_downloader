# NEW METHOD FOR BW TO TRY!

Download it in the [release](https://github.com/xuzhengyi1995/Manga_downloader/releases/tag/BW-downloader-chrome-v0.1) or here: [Windows x64 release build v0.1](https://github.com/xuzhengyi1995/Manga_downloader/releases/download/BW-downloader-chrome-v0.1/BW-downloader-chrome-bin.zip)

**If you are finding something to download BW, please try this method for BW, it's really a good thing to try, you will like it!**

**For coma, please see below.**

Now have a new method, with a customized `chromium` browser, it can download BW original image with it's original size very easily. It can download both manga and novel, and may be used to every website that use canvas to render the page (now only tested on BW).

It is only a dev version, may have bugs and may crash, but you can download the customized browser and try it now.

**Do not use it for other website, only use it as a BW downloader, it is not as safe as normal chrome browser!**

Clone this repo or only download the [BW-downloader-chrome-bin.zip](https://github.com/xuzhengyi1995/Manga_downloader/raw/master/BW-downloader-chrome-bin.zip)

1.  Unzip the file `BW-downloader-chrome-bin.zip`.
2.  Open a `powsershell` or `cmd`, `cd` to the unzipped browser dir.
3.  Open the browser with command line `.\chrome.exe --user-data-dir=c:\bw-downloader-profile --no-sandbox`
4.  Adjust your browser window size, make it smaller and can only display one manga page, example below
    ![image](https://user-images.githubusercontent.com/29002064/139255318-95531cd9-c442-4a61-acb4-cef3d71b7190.png)


5.  You can now go to BW website, log in and open the manga you want to download, remember to reset the manga's read status before you open it.
6.  Press `F12`, make it a separate window (see the image below) and run the script below (just go to `console` and copy-past the code, press enter) to move the page automatically, if your network is good, you can change the `3000` to a smaller number, 3000 means 3000ms -> 3s, every 3s it will move to the next page.

    You can also manually click the mouse left button / use a keyboard arrow key / use a keyboard simulation software to move the page, you can choose the way you like, just make sure the page is moving.
    ```js
    window.i=0;setInterval(()=>{NFBR.a6G.Initializer.Z4p.menu.options.a6l.moveToPage(window.i);console.log(window.i);window.i++;},3000)
    ```
    
    If this not work and show 'Uncaught TypeError: Cannot read properties of undefined (reading 'menu') at <anonymous>:1:54', it means BW has updated the js, you can try to find it in the console, just try `NFBR.a6G.Initializer.*.menu` is not `undefined` and the * is the new object name; Or you can just file a bug.

    ![image](https://user-images.githubusercontent.com/29002064/138590508-e7555a2d-1528-4e59-8a50-e08e407bc1be.png)


7.  Now you can check your `C:\bw_export_data`, you can find a random uuid folder with all the manga images in it.
    ![image](https://user-images.githubusercontent.com/29002064/139255390-03b9191a-e90b-4572-9cde-b7e50ca9787c.png)

If you want to download multiple manga at the same time, just open as many manga as you want, and do the step 5 to 6.

This method is very easy to use, stable and no need to find any resolution or cookies, and it can download the real original image with no barcode.

Maybe will add a new browser ui to it and can click to download in the future.

May not download the cover page now.

Only built on windows, no program now for other platform.

If you find some problem, please file a bug, thank you!

# Manga_Downloader

A Manga download framework using `selenium`.

**Now support the websites below:**

1.  [Bookwalker.jp](https://bookwalker.jp)
2.  [Bookwalker.com.tw](https://www.bookwalker.com.tw)
3.  [Cmoa.jp](https://www.cmoa.jp/)

**Program will check the website of given URL automaticity**

**If the website you given is unsupported, the program will raise an error.**

**Now support multi manga download with only login one time**

**现在支持批量下载**

**you should prepare the information below:**

1.  Manga URL
2.  Cookies
3.  Image dir (Where to put the image, folder name)
4.  Some website you should see the size of image and set it at `res`. [Cmoa.jp](https://www.cmoa.jp/) doesn't need this.

# How to Use

## All settings

All the settings are in `main.py`.

```python
settings = {
    # Manga urls, should be the same website
    'manga_url': [
        'URL_1',
        'URL_2'
    ],
    # Your cookies
    'cookies': 'YOUR_COOKIES_HERE',
    # Folder names to store the Manga, the same order with manga_url
    'imgdir': [
        'IMGDIR_FOR_URL_1',
        'IMGDIR_FOR_URL_2'
    ],
    # Resolution, (Width, Height), For cmoa.jp this doesn't matter.
    'res': (1393, 2048),
    # Sleep time for each page (Second), normally no need to change.
    'sleep_time': 2,
    # Time wait for page loading (Second), if your network is good, you can reduce this parameter.
    'loading_wait_time': 20,
    # Cut image, (left, upper, right, lower) in pixel, None means do not cut the image. This often used to cut the edge.
    # Like (0, 0, 0, 3) means cut 3 pixel from bottom of the image.
    'cut_image': None,
    # File name prefix, if you want your file name like 'klk_v1_001.jpg', write 'klk_v1' here.
    'file_name_prefix': '',
    # File name digits count, if you want your file name like '001.jpg', write 3 here.
    'number_of_digits': 3,
    # Start page, if you want to download from page 3, set this to 3, None means from 0
    'start_page': None,
    # End page, if you want to download until page 10, set this to 10, None means until finished
    'end_page': None,
}
```

## Install environment & How to Get URL/Cookies

**This program now work for Chrome, if you use another browser, please check [this page](https://selenium-python.readthedocs.io/installation.html)**

0.  Install python packages _selenium_ and _pillow_ and get the _Google chrome Drivers_.

    1.  For _selenium_ ad _pillow_:

    ```shell
    pip install selenium
    pip install Pillow
    # This undetected_chromedriver is prevent us from been detected by BW
    pip install undetected_chromedriver
    ```

    2.  For Google chrome Drivers:

        1.  Please check your Chrome version, 'Help'->'About Google Chrome'.

        2.  Download Chrome Driver fit to your Chrome version [here](https://sites.google.com/a/chromium.org/chromedriver/downloads).

        3.  Put it into any folder and add the folder into the PATH.

    3.  For more info, I suggest you to check it [here](https://selenium-python.readthedocs.io/installation.html)


1.  Change the `IMGDIR` in the main.py to indicate where to put the manga.

2.  Add your cookies in the program.

    **Remember to use F12 to see the cookies!**

    **Because some http only cookies can not be seen by javascript!**

    **Remember to go to the links below to get the cookies!**

    1.  For [Bookwalker.jp] cookies, go [here](https://member.bookwalker.jp/app/03/my/profile).
    2.  For [Bookwalker.com.jp] cookies, go [here](https://www.bookwalker.com.tw/member).
    3.  For [www.cmoa.jp] cookies, go [here](https://www.cmoa.jp/) and you **must** get cookies by plug-in [EditThisCookie](http://www.editthiscookie.com/), download it for chrome [here](https://chrome.google.com/webstore/detail/edit-this-cookie/fngmhnnpilhplaeedifhccceomclgfbg).

    -   For `EditThisCookie`, this can be used in any website above, but for `cmoa` you **must** use this method

        1.  Go to user preferences (chrome-extension://fngmhnnpilhplaeedifhccceomclgfbg/options_pages/user_preferences.html) of `EditThisCookie`
        2.  Set the cookie export format to `Semicolon separated name=value pairs`
        3.  Go to [cmoa](https://www.cmoa.jp/), click the `EditThisCookie` and click `export` button
        4.  Copy the cookies in the file (**After the `// Example: http://www.tutorialspoint.com/javascript/javascript_cookies.htm`**) into the program

    -   For the traditional way

        > 1.  Open the page.
        > 2.  Press F12.
        > 3.  Click on the _Network_.
        > 4.  Refresh the page.
        > 5.  Find the first _profile_ request, click it.
        > 6.  On the right, there will be a _Request Headers_, go there.
        > 7.  Find the _cookie:...._, copy the string after the _cookie:_, paste to the _main.py_, _YOUR_COOKIES_HERE_

3.  Change the _manga_url_ in the _main.py_.

    1.  For [Bookwalker.jp]

        First go to [購入済み書籍一覧](https://bookwalker.jp/holdBooks/), you can find all your mangas here.

        This time the URL is the URL of **'この本を読む'** button for your manga.

        Right click this button, and click **'Copy link address'**.

        The URL is start with **member.bookwalker.jp**, not the **viewer.bookwalker.jp**. Here we use the manga [【期間限定　無料お試し版】あつまれ！ふしぎ研究部　１](https://member.bookwalker.jp/app/03/webstore/cooperation?r=BROWSER_VIEWER/640c0ddd-896c-4881-945f-ad5ce9a070a6/https%3A%2F%2Fbookwalker.jp%2FholdBooks%2F).

        This is the URL of the **あつまれ！ふしぎ研究部　１**: <https://member.bookwalker.jp/app/03/webstore/cooperation?r=BROWSER_VIEWER/640c0ddd-896c-4881-945f-ad5ce9a070a6/https%3A%2F%2Fbookwalker.jp%2FholdBooks%2F>

    2.  For [Bookwalker.com.tw]

        Please go to [线上阅读](https://www.bookwalker.com.tw/member/available_book_list).

        The manga URL like this：<https://www.bookwalker.com.tw/browserViewer/56994/read>

    3.  For [Cmoa.jp]

        Open the Manga and just copy the URL on the browser.

        The manga URL like this : <https://www.cmoa.jp/bib/speedreader/speed.html?cid=0000156072_jp_0001&u0=0&u1=0&rurl=https%3A%2F%2Fwww.cmoa.jp%2Fmypage%2Fmypage_top%2F%3Ftitle%3D156072>

    Just copy this URL to the `MANGA_URL` in _main.py_.

4.  After edit the program, run `python main.py` to run it.

# Notice

1.  The `SLEEP_TIME` by default is 2 seconds, you can adjust it with your own network situation, if the downloading has repeated images, you can change it to 5 or more. If you think it's too slow, try change it to 1 or even 0.5.

2.  `LOADING_WAIT_TIME = 20`, this is the time to wait until the manga viewer page loaded, if your network is not good, you can set it to 30 or 50 seconds.

3.  Resolution, you can change it as you want, but check the original image resolution first.

    ```python
    RES = (784, 1200)
    ```

    If the original image has a higher resolution, you can change it like this (The resolution is just a example).

    ```python
    RES = (1568, 2400)
    ```

    **For [Cmoa.jp] no need this, the resolution is fixed by [Cmoa.jp].**

4.  Some time we should log out and log in, this website is very strict and take so many method to prevent abuse.

5.  Now you can cut the image by setting `CUT_IMAGE` to (left, upper, right, lower).

    For example you want to cut 3px from the bottom of image, you can set it to:

    ```python
    CUT_IMAGE = (0, 0, 0, 3)
    ```

    This function use `Pillow`, if you want to use it, you should install it by using the command:

    ```shell
    pip install Pillow
    ```

    By default it is `None`, means do not cut the image.

6.  You can now change the file name prefix and number of digits by changing `file_name_prefix` and `number_of_digits`.

    For example, if you are downloading Kill La Kill Manga Volume 1, and you want the file name like:

    <pre>
        KLK_V1
        │--KLK_V1_001.jpg
        │--KLK_V1_002.jpg
        │--KLK_V1_003.jpg
    </pre>

    Then you can set the parameters like below:

    ```python
    settings = {
        ...,
        'file_name_prefix': 'KLK_V1',
        # File name digits count, if you want your file name like '001.jpg', write 3 here.
        'number_of_digits': 3
    }
    ```

# Develop

0.  Concept

    To download Manga, normally we do like this:

    <pre>
    +------------+     +-----------+      +------------+      +-------------------+      +--------------+
    |            |     |           |      |            |      |                   | OVER |              |
    |   Login    +-----+ Load page +----->+ Save image +----->+ Move to next page +----->+   Finished   |
    |            |     |           |      |            |      |                   |      |              |
    +------------+     +-----------+      +-----+------+      +---------+---------+      +--------------+
                                                ^                       |
                                                |                       |
                                                |      More page        |
                                                +-----------------------+
    </pre>

    So we can create a framework to reuse the code, for new website, normally we only need to write some of the method.

1.  Structure of file

    <pre>
    |--main.py
    │--downloader.py
    │--README.MD
    └─website_actions
        │--abstract_website_actions.py
        │--bookwalker_jp_actions.py
        │--bookwalker_tw_actions.py
        │--cmoa_jp_actions.py
        │--__init__.py
    </pre>

2.  Introduction to abstract `WebsiteActions` class.

    For each website, the class should have the following methods/attributes, here we use bookwalker.jp as example:

    ```python
    class BookwalkerJP(WebsiteActions):
        '''
        bookwalker.jp
        '''

        # login_url is the page that we load first and put the cookies.
        login_url = 'https://member.bookwalker.jp/app/03/login'

        @staticmethod
        def check_url(manga_url):
            '''
            This method return a bool, check if the given manga url is belong to this class.
            '''
            return manga_url.find('bookwalker.jp') != -1

        def get_sum_page_count(self, driver):
            '''
            This method return an integer, get total page number.
            '''
            return int(str(driver.find_element_by_id('pageSliderCounter').text).split('/')[1])

        def move_to_page(self, driver, page):
            '''
            This method return nothing, move to given page number.
            '''
            driver.execute_script(
                'NFBR.a6G.Initializer.B0U.menu.a6l.moveToPage(%d)' % page)

        def wait_loading(self, driver):
            '''
            This method return nothing, wait manga loading.
            '''
            WebDriverWait(driver, 30).until_not(lambda x: self.check_is_loading(
                x.find_elements_by_css_selector(".loading")))

        def get_imgdata(self, driver, now_page):
            '''
            This method return String/something can be written to file or convert to BytesIO, get image data.
            '''
            canvas = driver.find_element_by_css_selector(".currentScreen canvas")
            img_base64 = driver.execute_script(
                "return arguments[0].toDataURL('image/jpeg').substring(22);", canvas)
            return base64.b64decode(img_base64)

        def get_now_page(self, driver):
            '''
            This method return an integer, the page number on the current page
            '''
            return int(str(driver.find_element_by_id('pageSliderCounter').text).split('/')[0])
    ```

      We also have a `before_download` method, this method run before we start download, because some website need to close some pop-up component before we start downloading.

    ```python
    def before_download(self, driver):
        '''
        This method return nothing, Run before download.
        '''
        driver.execute_script('parent.closeTips()')
    ```
