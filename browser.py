'''
Chrome driver factory and login-session (cookie) handling.

The chromedriver binary is resolved automatically by Selenium Manager, which
downloads the Chrome-for-Testing driver matching the installed Chrome.
'''
import json
import logging
import os
from pathlib import Path

from selenium import webdriver

DEFAULT_COOKIE_PATH = Path(os.environ.get(
    'BW_COOKIES', Path.home() / '.manga_downloader' / 'bw_tw_cookies.json'))

_STEALTH_JS = '''
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
'''


def create_driver(headless=True, res=(784, 1200), profile_dir=None):
    '''Create a Chrome WebDriver with a viewport of exactly ``res`` pixels.'''
    options = webdriver.ChromeOptions()
    options.set_capability('unhandledPromptBehavior', 'accept')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument(f'--window-size={res[0]},{res[1]}')
    options.add_argument('--lang=zh-TW')
    if headless:
        options.add_argument('--headless=new')
    if hasattr(os, 'geteuid') and os.geteuid() == 0:  # e.g. inside Docker
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
    if profile_dir:
        options.add_argument(f'--user-data-dir={Path(profile_dir).resolve()}')

    driver = webdriver.Chrome(options=options)

    # Real UA of this Chrome, minus the "Headless" marker.
    version = driver.execute_cdp_cmd('Browser.getVersion', {})
    user_agent = version['userAgent'].replace('HeadlessChrome', 'Chrome')
    driver.execute_cdp_cmd('Network.enable', {})
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {'userAgent': user_agent})
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': _STEALTH_JS})
    driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
        'width': res[0], 'height': res[1], 'deviceScaleFactor': 1, 'mobile': False,
    })

    chrome_caps = driver.capabilities.get('chrome', {})
    logging.info('Chrome %s, chromedriver %s',
                 driver.capabilities.get('browserVersion'),
                 chrome_caps.get('chromedriverVersion', '?').split(' ')[0])
    return driver


def _is_bookwalker_cookie(cookie):
    domain = str(cookie.get('domain', '')).lstrip('.').lower()
    return domain == 'bookwalker.com.tw' or domain.endswith('.bookwalker.com.tw')


def _write_private(path, text):
    '''Write ``text`` to ``path`` readable only by the current user (0600 on POSIX;
    on Windows the file inherits the user-profile ACL).'''
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        os.chmod(path.parent, 0o700)
    except OSError:
        pass
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as fh:
        fh.write(text)
    os.chmod(path, 0o600)  # tighten a file that already existed with a wider mode


def save_cookies(driver, path=DEFAULT_COOKIE_PATH):
    '''Save the BookWalker TW cookies (incl. httpOnly) to a private JSON file.'''
    path = Path(path)
    cookies = [c for c in driver.execute_cdp_cmd('Network.getAllCookies', {})['cookies']
               if _is_bookwalker_cookie(c)]
    _write_private(path, json.dumps(cookies, ensure_ascii=False, indent=2))
    logging.info('Saved %d cookies to %s', len(cookies), path)


_SET_COOKIE_KEYS = ('name', 'value', 'domain', 'path', 'secure', 'httpOnly',
                    'sameSite', 'expires')


def load_cookies(driver, path=DEFAULT_COOKIE_PATH):
    '''Load BookWalker TW cookies saved by :func:`save_cookies` into the browser.'''
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(
            f'Cookie file {path} not found. Run `python main.py login` first.')
    try:
        cookies = json.loads(path.read_text(encoding='utf-8'))
    except (ValueError, UnicodeDecodeError) as err:
        raise ValueError(f'Cookie file {path} is not valid JSON; run `python main.py login`.') from err
    if not isinstance(cookies, list):
        raise ValueError(f'Cookie file {path} has an unexpected format; run `python main.py login`.')
    params = []
    for cookie in cookies:
        if not isinstance(cookie, dict) or not _is_bookwalker_cookie(cookie):
            continue
        param = {k: cookie[k] for k in _SET_COOKIE_KEYS if k in cookie}
        expires = param.get('expires', -1)
        if cookie.get('session') or not isinstance(expires, (int, float)) or expires < 0:
            param.pop('expires', None)
        params.append(param)
    driver.execute_cdp_cmd('Network.enable', {})
    driver.execute_cdp_cmd('Network.setCookies', {'cookies': params})
    logging.info('Loaded %d cookies from %s', len(params), path)
