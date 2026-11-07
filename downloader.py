'''
Main downloader, XU Zhengyi, 2020/05/05
'''
import logging
import random
import re
import time
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps

_ILLEGAL_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f\x7f-\x9f]')
_WINDOWS_RESERVED = re.compile(r'(CON|PRN|AUX|NUL|COM[0-9¹²³]|LPT[0-9¹²³])(\..*)?', re.I)
_PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'


def _clean_component(name):
    name = _ILLEGAL_CHARS.sub('_', str(name or ''))[:150].strip().rstrip('. ')
    if _WINDOWS_RESERVED.fullmatch(name):
        name = '_' + name
    return name


def sanitize_folder_name(name, fallback='book'):
    '''A single safe path component. The fallback (the book id) is sanitized too,
    because ids come from page-controlled JavaScript.'''
    return _clean_component(name) or _clean_component(fallback) or 'book'


class Downloader:
    '''
    Downloads every page of a book currently opened in the given driver.
    '''

    def __init__(self, driver, actions, output_dir, sleep_time=1.0, loading_wait_time=20,
                 cut_image=None, file_name_prefix='', number_of_digits=3,
                 start_page=None, end_page=None, save_page_source=False):
        self.driver = driver
        self.actions = actions
        self.output_dir = Path(output_dir)
        self.sleep_time = sleep_time
        self.loading_wait_time = loading_wait_time
        self.cut_image = cut_image
        prefix = _clean_component(file_name_prefix)
        prefix = f'{prefix}_'.replace('%', '%%') if prefix else ''
        self.file_name_model = prefix + '%%0%dd.png' % max(1, min(int(number_of_digits), 9))
        self.start_page = start_page - 1 if start_page and start_page > 0 else 0
        self.end_page = end_page
        self.save_page_source = save_page_source
        self.image_box = None

    def _save(self, path, image_data):
        if not image_data.startswith(_PNG_SIGNATURE):
            raise RuntimeError('Page data is not a PNG image')
        if self.cut_image is None:
            path.write_bytes(image_data)
            return
        # Only the PNG decoder may parse page-supplied bytes.
        with Image.open(BytesIO(image_data), formats=['PNG']) as img:
            if self.cut_image == 'dynamic':
                if self.image_box is None:
                    self.image_box = ImageOps.invert(img.convert('RGB')).getbbox()
                img.crop(self.image_box).save(path, format='PNG')
            else:
                left, upper, right, lower = self.cut_image
                width, height = img.size
                img.crop((left, upper, width - right, height - lower)).save(path, format='PNG')

    def download_book(self, book, folder_name=None):
        '''Open ``book`` in the viewer and save all pages. Return True on success.'''
        driver, actions = self.driver, self.actions
        self.image_box = None
        title = book.title
        book_dir = self.output_dir / sanitize_folder_name(folder_name or title, book.id)
        try:
            logging.info('Loading %s', book.read_url)
            driver.get(book.read_url)
            time.sleep(self.loading_wait_time)
            actions.before_download(driver)

            title = book.title or actions.get_book_title(driver)
            book_dir = self.output_dir / sanitize_folder_name(folder_name or title, book.id)
            book_dir.mkdir(parents=True, exist_ok=True)
            logging.info('Saving "%s" to %s', title, book_dir)

            page_count = actions.get_sum_page_count(driver)
            end_page = min(self.end_page, page_count) if self.end_page else page_count
            logging.info('Book has %d pages, downloading %d-%d',
                         page_count, self.start_page + 1, end_page)
            self._goto(self.start_page)

            last_hash = None
            for i in range(self.start_page, end_page):
                path = book_dir / (self.file_name_model % i)
                if path.exists():
                    logging.info('Page %d exists, skipped', i + 1)
                else:
                    actions.wait_loading(driver)
                    time.sleep(self.sleep_time)
                    image_data = actions.get_imgdata(driver, i + 1)
                    digest = actions.image_hash(image_data)
                    if digest == last_hash:
                        logging.warning('Page %d looks identical to the previous page', i + 1)
                    last_hash = digest
                    self._save(path, image_data)
                    logging.info('Page %d/%d downloaded', i + 1, page_count)

                if i + 1 >= end_page:
                    break
                if not actions.move_to_page(driver, i + 1):
                    if actions.get_now_page(driver) >= page_count:
                        logging.info('Reached the last page.')
                        break
                    raise RuntimeError(f'Could not flip to page {i + 2}')
                time.sleep(random.random())
            logging.info('Finished "%s".', title)
            return True
        except Exception as err:  # keep diagnostics for any viewer failure
            err = str(err).strip() or type(err).__name__
            saved = []
            try:
                book_dir.mkdir(parents=True, exist_ok=True)
                driver.save_screenshot(str(book_dir / 'error.png'))
                saved.append('error.png')
                # The logged-in page source can contain account details (email, member id,
                # CSRF token), so it is only written when explicitly requested.
                if self.save_page_source:
                    (book_dir / 'error.html').write_text(driver.page_source, encoding='utf-8')
                    saved.append('error.html')
            except Exception as diag_err:  # a dead driver must not hide the real error
                logging.warning('Could not save diagnostics: %s', diag_err)
            logging.error('Download failed: %s. %s'
                          'If you were logged out, run `python main.py login`.', err,
                          f'See {", ".join(saved)} in {book_dir}. ' if saved else '')
            return False

    def _goto(self, page):
        '''Go to a 0-based page, stepping one page at a time if the API is unavailable.'''
        # The viewer may reopen at the last-read page, so always seek explicitly.
        if self.actions.move_to_page(self.driver, page):
            return
        if self.actions.get_now_page(self.driver) > page + 1:
            raise RuntimeError(
                f'Viewer opened at page {self.actions.get_now_page(self.driver)} and cannot '
                f'jump back to page {page + 1}. Reset the read position in the viewer and retry.')
        while self.actions.get_now_page(self.driver) < page + 1:
            current = self.actions.get_now_page(self.driver)
            if not self.actions.move_to_page(self.driver, current):
                raise RuntimeError(f'Could not reach start page {page + 1}')
