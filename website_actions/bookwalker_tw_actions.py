'''
Website actions for bookwalker.com.tw
'''
import base64
import hashlib
import logging
import re
import time
from urllib.parse import urlsplit

from selenium.common.exceptions import JavascriptException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from website_actions.abstract_website_actions import Book, WebsiteActions, clean_text

BASE_URL = 'https://www.bookwalker.com.tw'
WWW_HOST = 'www.bookwalker.com.tw'
VIEWER_URL = BASE_URL + '/browserViewer/{id}/{mode}'
_VIEWER_PATH_RE = re.compile(r'/browserViewer/(\d+)(?:/(read|trial))?/?')
_BOOK_ID_RE = re.compile(r'\d{1,12}')
_PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'


def is_bookwalker_url(url, hosts=(WWW_HOST,), allow_subdomains=False):
    '''True only for https URLs whose parsed hostname is an allowed BookWalker TW host.
    Values returned by page JavaScript are page-controlled, so they are re-checked here.'''
    try:
        parts = urlsplit(str(url))
    except ValueError:
        return False
    host = (parts.hostname or '').lower()
    if parts.scheme != 'https' or not host:
        return False
    if allow_subdomains:
        return host == 'bookwalker.com.tw' or host.endswith('.bookwalker.com.tw')
    return host in hosts

# Finds the NFBR viewer object that exposes moveToPage() without relying on
# the obfuscated property names, which change whenever BookWalker rebuilds.
_FIND_VIEWER_JS = r'''
if (window.__mdlMover && typeof window.__mdlMover.moveToPage === 'function') return true;
const root = window.NFBR;
if (!root) return false;
const seen = new Set();
const queue = [[root, 0]];
while (queue.length) {
  const [obj, depth] = queue.shift();
  if (!obj || (typeof obj !== 'object' && typeof obj !== 'function') || seen.has(obj)) continue;
  seen.add(obj);
  if (typeof obj.moveToPage === 'function' && typeof obj !== 'function') {
    window.__mdlMover = obj;
    return true;
  }
  if (depth >= 6) continue;
  let keys;
  try { keys = Object.keys(obj); } catch (e) { continue; }
  for (const k of keys) {
    let v;
    try { v = obj[k]; } catch (e) { continue; }
    if (v && (typeof v === 'object' || typeof v === 'function') && !(v instanceof Node) && v !== window) {
      queue.push([v, depth + 1]);
    }
  }
}
return false;
'''

_COUNTER_JS = r'''
const el = document.getElementById('pageSliderCounter');
const txt = el ? (el.textContent || '').trim() : '';
const m = txt.match(/(\d+)\s*\/\s*(\d+)/);
if (m) return [parseInt(m[1]), parseInt(m[2])];
const slider = document.querySelector('#pageSlider input[type=range], input#pageSlider, .pageSlider input[type=range]');
if (slider) return [parseInt(slider.value) + 1, parseInt(slider.max) + 1];
return null;
'''

_CANVAS_HASH_JS = r'''
const c = document.querySelector('.currentScreen canvas');
if (!c || !c.width) return null;
const d = c.toDataURL('image/png');
let h = 0;
for (let i = 0; i < d.length; i += 97) { h = (h * 31 + d.charCodeAt(i)) | 0; }
return h + ':' + d.length;
'''

# Scrapes the bookshelf grid (ul.readerBookList > li cards). Cover <img> alts are
# a literal "書名" placeholder, so titles come from .readerBookName or the
# card menu's data-product_name. Returns {books: [[id, title, author]], pages: [url]}.
_LIBRARY_JS = r'''
const books = [];
const text = (root, sel) => { const e = root.querySelector(sel); return e ? e.textContent.trim() : ''; };
for (const card of document.querySelectorAll('ul.readerBookList > li')) {
  const a = card.querySelector('a[href*="/browserViewer/"]');
  const m = a && a.href.match(/\/browserViewer\/(\d+)/);
  if (!m) continue;
  const info = card.querySelector('[data-product_name]');
  const title = text(card, '.readerBookName') || (info && info.dataset.product_name) || '';
  const author = text(card, '.readerBookAuthor') || (info && info.dataset.author) || '';
  books.push([m[1], title, author]);
}
const pages = [...document.querySelectorAll('select.pageNumSelect option')]
  .map(o => o.value).filter(v => v && v.startsWith('http'));
return {books, pages};
'''


class BookwalkerTW(WebsiteActions):
    '''
    bookwalker.com.tw
    '''
    login_url = BASE_URL + '/login'
    member_url = BASE_URL + '/member'
    library_url = BASE_URL + '/bookcase/available_book_list'

    def __init__(self, flip_direction='auto', page_timeout=60):
        self.flip_direction = flip_direction
        self.page_timeout = page_timeout
        self.strategy = None

    # ----- session / library -------------------------------------------------

    @staticmethod
    def check_url(manga_url):
        return is_bookwalker_url(manga_url, allow_subdomains=True)

    @staticmethod
    def is_login_url(url):
        return 'loginConfirm' in url or '/login' in url.split('?')[0]

    def is_logged_in(self, driver):
        # Logged-out visits to /member redirect to member.bookwalker.com.tw/loginConfirm.
        driver.get(self.member_url)
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script('return document.readyState') == 'complete')
        return not self.is_login_url(driver.current_url)

    def logout(self, driver):
        '''Invalidate the session on the server (www link + member POST form).'''
        driver.get(BASE_URL + '/logout')
        time.sleep(2)
        driver.get('https://member.bookwalker.com.tw/')
        time.sleep(2)
        driver.execute_script(
            "const f = document.getElementById('logout-form'); if (f) f.submit();")
        time.sleep(3)
        return not self.is_logged_in(driver)

    def _scrape_library_page(self, driver, url):
        driver.get(url)
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script('return document.readyState') == 'complete')
        WebDriverWait(driver, 15).until(
            lambda d: d.find_elements(By.CSS_SELECTOR, 'ul.readerBookList, .pageNumBox'))
        return driver.execute_script(_LIBRARY_JS)

    def _is_library_page_url(self, url):
        return (is_bookwalker_url(url)
                and urlsplit(url).path.startswith('/bookcase/available_book_list'))

    def list_library(self, driver):
        # Everything returned by _LIBRARY_JS is page-controlled (it runs in the page's
        # JS world), so ids, titles and pagination URLs are re-validated in Python.
        books, seen = [], set()
        first = self._scrape_library_page(driver, self.library_url)
        raw_pages = first.get('pages') or []
        pages = [u for u in raw_pages if isinstance(u, str) and self._is_library_page_url(u)]
        if len(pages) != len(raw_pages):
            logging.warning('Ignored %d pagination link(s) outside %s',
                            len(raw_pages) - len(pages), self.library_url)
        pages = list(dict.fromkeys(pages)) or [self.library_url]
        for n, url in enumerate(pages, 1):
            result = first if n == 1 else self._scrape_library_page(driver, url)
            new = 0
            for entry in result.get('books') or []:
                try:
                    book_id, title, author = (str(x) for x in entry)
                except (TypeError, ValueError):
                    continue
                if not _BOOK_ID_RE.fullmatch(book_id) or book_id in seen:
                    continue
                seen.add(book_id)
                new += 1
                books.append(Book(book_id, clean_text(title),
                                  VIEWER_URL.format(id=book_id, mode='read'), clean_text(author)))
            logging.info('Library page %d/%d: %d books', n, len(pages), new)
        return books

    def resolve_book(self, id_or_url):
        '''Accept a numeric id or a https://www.bookwalker.com.tw/browserViewer/<id>[/read|/trial]
        URL; the URL is rebuilt from its parts so only the BookWalker viewer is ever opened.'''
        id_or_url = str(id_or_url).strip()
        if _BOOK_ID_RE.fullmatch(id_or_url):
            return Book(id_or_url, '', VIEWER_URL.format(id=id_or_url, mode='read'))
        if is_bookwalker_url(id_or_url):
            match = _VIEWER_PATH_RE.fullmatch(urlsplit(id_or_url).path)
            if match and _BOOK_ID_RE.fullmatch(match.group(1)):
                return Book(match.group(1), '',
                            VIEWER_URL.format(id=match.group(1), mode=match.group(2) or 'read'))
        raise ValueError(f'Not a BookWalker TW book id or viewer URL: {clean_text(id_or_url)}')

    # ----- viewer ------------------------------------------------------------

    def before_download(self, driver):
        self.strategy = None
        if self.is_login_url(driver.current_url):
            raise RuntimeError('Viewer redirected to the login page (not logged in)')
        try:
            WebDriverWait(driver, self.page_timeout).until(
                lambda d: d.execute_script(_COUNTER_JS) is not None
                or d.find_elements(By.CSS_SELECTOR, '.currentScreen canvas'))
        except WebDriverException as err:
            raise RuntimeError(
                f'Viewer did not load (ended at {clean_text(driver.current_url)})') from err
        try:
            found = WebDriverWait(driver, 15).until(
                lambda d: d.execute_script(_FIND_VIEWER_JS))
        except WebDriverException:
            found = False
        logging.info('Viewer moveToPage API %s', 'found' if found else
                     'not found, will use keyboard/click flipping')
        if self.flip_direction == 'auto':
            self.flip_direction = self._detect_direction(driver)
            logging.info('Reading direction: %s', self.flip_direction)

    def _detect_direction(self, driver):
        try:
            rtl = driver.execute_script(r'''
                const m = window.__mdlMover;
                for (const o of [m, m && m.options, window.NFBR]) {
                  if (!o) continue;
                  for (const k of Object.keys(o)) {
                    const v = o[k];
                    if (typeof v === 'string' && /^(rtl|ltr)$/i.test(v)) return v.toLowerCase();
                  }
                }
                const d = document.documentElement.getAttribute('dir') || '';
                return /^(rtl|ltr)$/i.test(d) ? d.toLowerCase() : null;''')
        except JavascriptException:
            rtl = None
        return rtl if rtl in ('rtl', 'ltr') else 'rtl'

    def get_book_title(self, driver):
        title = driver.execute_script(r'''
            const el = document.querySelector('#pagetitle, .titleText, #bookTitle');
            return (el && el.textContent.trim()) || document.title || '';''')
        title = clean_text(title)
        return re.sub(r'\s*[|\-–]\s*BOOK☆WALKER.*$', '', title, flags=re.I).strip()

    def _counter(self, driver):
        return driver.execute_script(_COUNTER_JS)

    def get_sum_page_count(self, driver):
        counter = self._counter(driver)
        if counter:
            return counter[1]
        raise RuntimeError('Could not read the page count (#pageSliderCounter missing)')

    def get_now_page(self, driver):
        counter = self._counter(driver)
        return counter[0] if counter else 0

    def _state(self, driver):
        return (self.get_now_page(driver), driver.execute_script(_CANVAS_HASH_JS))

    def _wait_changed(self, driver, before, timeout):
        try:
            WebDriverWait(driver, timeout, poll_frequency=0.25).until(
                lambda d: self._state(d) != before)
            return True
        except WebDriverException:
            return False

    def _flip_api(self, driver, page):
        return driver.execute_script(
            'if (!window.__mdlMover) return false; window.__mdlMover.moveToPage(arguments[0]); return true;',
            page)

    def _flip_key(self, driver, page):
        key = Keys.ARROW_LEFT if self.flip_direction == 'rtl' else Keys.ARROW_RIGHT
        ActionChains(driver).send_keys(key).perform()
        return True

    def _flip_click(self, driver, page):
        width = driver.execute_script('return window.innerWidth')
        height = driver.execute_script('return window.innerHeight')
        x = int(width * 0.08) if self.flip_direction == 'rtl' else int(width * 0.92)
        ActionChains(driver).move_to_location(x, height // 2).click().perform()
        return True

    def move_to_page(self, driver, page):
        '''Move to the given 0-based page; return True if the page changed.'''
        before = self._state(driver)
        if before[0] == page + 1:
            return True
        sequential = before[0] == page  # next page relative to the current one
        strategies = [('api', self._flip_api)]
        if sequential:
            strategies += [('keyboard', self._flip_key), ('click', self._flip_click)]
        if self.strategy:
            strategies.sort(key=lambda s: s[0] != self.strategy)
        for name, flip in strategies:
            try:
                if not flip(driver, page):
                    continue
            except WebDriverException as err:
                logging.debug('Flip via %s failed: %s', name, err)
                continue
            if self._wait_changed(driver, before, 8 if self.strategy != name else self.page_timeout):
                if self.strategy != name:
                    logging.info('Page flip strategy: %s', name)
                    self.strategy = name
                return True
        return False

    def wait_loading(self, driver):
        def loaded(d):
            for el in d.find_elements(By.CSS_SELECTOR, '.loading'):
                try:
                    if el.is_displayed():
                        return False
                except WebDriverException:
                    pass
            return bool(d.execute_script(_CANVAS_HASH_JS))
        WebDriverWait(driver, 600, poll_frequency=0.25).until(loaded)

    def get_imgdata(self, driver, now_page):
        data_url = driver.execute_script(
            "return document.querySelector('.currentScreen canvas').toDataURL('image/png');")
        if not isinstance(data_url, str) or not data_url.startswith('data:image/png;base64,'):
            raise RuntimeError('Canvas did not return a PNG data URL')
        data = base64.b64decode(data_url.split(',', 1)[1], validate=True)
        # toDataURL can be overridden by page script; only accept real PNG bytes.
        if not data.startswith(_PNG_SIGNATURE):
            raise RuntimeError('Canvas data is not a PNG image')
        return data

    @staticmethod
    def image_hash(data):
        return hashlib.sha1(data).hexdigest()
