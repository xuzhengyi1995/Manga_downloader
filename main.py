'''
BookWalker TW manga downloader - command line interface.

    python main.py login
    python main.py library
    python main.py download --select 1,3-5 -o D:\\Manga
'''
import argparse
import json
import logging
import sys
import time
from pathlib import Path

from browser import DEFAULT_COOKIE_PATH, create_driver, load_cookies, save_cookies
from downloader import Downloader
from website_actions import BookwalkerTW, is_bookwalker_url

logging.basicConfig(format='[%(levelname)s] %(asctime)s : %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)


def parse_res(value):
    try:
        width, height = (int(v) for v in value.lower().split('x'))
        return width, height
    except ValueError as err:
        raise argparse.ArgumentTypeError('use WIDTHxHEIGHT, e.g. 784x1200') from err


def parse_cut(value):
    if value == 'dynamic':
        return value
    try:
        parts = tuple(int(v) for v in value.split(','))
    except ValueError as err:
        raise argparse.ArgumentTypeError('use L,U,R,D or "dynamic"') from err
    if len(parts) != 4:
        raise argparse.ArgumentTypeError('use L,U,R,D or "dynamic"')
    return parts


def parse_selection(spec, count):
    '''"1,3-5" -> [0, 2, 3, 4] (indices into the library list).'''
    indices = []
    for part in spec.split(','):
        part = part.strip()
        if not part:
            continue
        lo, _, hi = part.partition('-')
        lo, hi = int(lo), int(hi or lo)
        for n in range(lo, hi + 1):
            if not 1 <= n <= count:
                raise SystemExit(f'Selection {n} is out of range 1-{count}')
            indices.append(n - 1)
    return list(dict.fromkeys(indices))


def open_session(args, actions, headless=True):
    driver = create_driver(headless=headless, res=args.res)
    if getattr(args, 'no_login', False):
        return driver
    try:
        try:
            load_cookies(driver, args.cookies)
        except (FileNotFoundError, ValueError) as err:
            raise SystemExit(str(err)) from None
        if not actions.is_logged_in(driver):
            raise SystemExit('Session expired or invalid. Run `python main.py login` again.')
    except BaseException:
        driver.quit()
        raise
    return driver


def cmd_login(args):
    actions = BookwalkerTW()
    driver = create_driver(headless=False, res=(1200, 900))
    try:
        driver.get(actions.login_url)
        print('Sign in to BookWalker TW in the opened Chrome window.')
        print('Waiting for login to complete (up to 10 minutes)...')
        deadline = time.time() + 600
        while time.time() < deadline:
            url = driver.current_url
            if (is_bookwalker_url(url, allow_subdomains=True)
                    and not actions.is_login_url(url)):
                break
            time.sleep(2)
        else:
            raise SystemExit('Timed out waiting for login.')
        time.sleep(3)
        if not actions.is_logged_in(driver):
            raise SystemExit('Login did not complete, cookies not saved.')
        save_cookies(driver, args.cookies)
        print(f'Logged in. Session saved to {args.cookies}')
    finally:
        driver.quit()


def cmd_logout(args):
    path = Path(args.cookies)
    if not path.is_file():
        print(f'No saved session at {path}.')
        return 0
    if not args.local_only:
        actions = BookwalkerTW()
        try:
            driver = create_driver(headless=True, res=(1200, 900))
            try:
                load_cookies(driver, path)
                actions.logout(driver)
            finally:
                driver.quit()
            # The logout responses rewrite the browser's own cookie jar, so success there
            # proves nothing. Replay the *saved* cookies in a fresh browser instead.
            driver = create_driver(headless=True, res=(1200, 900))
            try:
                load_cookies(driver, path)
                still_valid = actions.is_logged_in(driver)
            finally:
                driver.quit()
            if still_valid:
                print('Warning: BookWalker did NOT revoke the session server-side; the saved '
                      'cookies (and any copy of them) still log in. Use "sign out of all '
                      'devices" or change your password on the website to end the session.')
            else:
                print('Signed out on BookWalker TW. Verified: the saved cookies no longer log in.')
        except Exception as err:  # still delete the local file below
            print(f'Warning: server-side sign-out failed ({err}). '
                  'Sign out manually on the website to be sure.')
    try:
        path.unlink()
    except OSError as err:  # e.g. read-only Docker mount
        raise SystemExit(f'Could not delete {path} ({err}). Delete it manually on the host.')
    try:
        path.parent.rmdir()  # only removes the folder if it is now empty
    except OSError:
        pass
    print(f'Deleted {path}')
    return 0


def cmd_library(args):
    actions = BookwalkerTW()
    driver = open_session(args, actions)
    try:
        books = actions.list_library(driver)
    finally:
        driver.quit()
    if args.json:
        print(json.dumps([b.__dict__ for b in books], ensure_ascii=False, indent=2))
    else:
        for n, book in enumerate(books, 1):
            author = f'  ({book.author})' if book.author else ''
            print(f'{n:4d}  {book.id:>10}  {book.title}{author}')
        print(f'{len(books)} books.')


def cmd_download(args):
    actions = BookwalkerTW(flip_direction=args.flip_direction)
    driver = open_session(args, actions, headless=not args.no_headless)
    try:
        try:
            books = [actions.resolve_book(x) for x in args.books]
        except ValueError as err:
            raise SystemExit(str(err)) from None
        if args.all or args.select or args.search:
            library = actions.list_library(driver)
            if args.all:
                books += library
            if args.select:
                books += [library[i] for i in parse_selection(args.select, len(library))]
            if args.search:
                needle = args.search.casefold()
                books += [b for b in library if needle in b.title.casefold()]
        books = list({b.id: b for b in books}.values())
        if not books:
            raise SystemExit('No books selected. Give ids/URLs, --select, --search or --all.')
        if args.name and len(books) > 1:
            raise SystemExit('--name can only be used with a single book.')

        downloader = Downloader(
            driver, actions, args.output_dir, sleep_time=args.sleep,
            loading_wait_time=args.load_wait, cut_image=args.cut_image,
            file_name_prefix=args.prefix, number_of_digits=args.digits,
            start_page=args.start_page, end_page=args.end_page,
            save_page_source=args.save_page_source)
        failed = []
        for n, book in enumerate(books, 1):
            logging.info('[%d/%d] %s', n, len(books), book.title or book.id)
            if not downloader.download_book(book, folder_name=args.name):
                failed.append(book)
        if failed:
            logging.error('Failed: %s', ', '.join(b.title or b.id for b in failed))
            return 1
        return 0
    finally:
        driver.quit()


def build_parser():
    parser = argparse.ArgumentParser(description='BookWalker TW manga downloader')
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('--cookies', type=Path, default=DEFAULT_COOKIE_PATH,
                        help=f'session cookie file (default: {DEFAULT_COOKIE_PATH})')
    common.add_argument('--res', type=parse_res, default=(784, 1200),
                        help='viewer size WIDTHxHEIGHT (default: 784x1200)')
    sub = parser.add_subparsers(dest='command', required=True)

    p = sub.add_parser('login', parents=[common], help='sign in once in a visible browser and save the session')
    p.set_defaults(func=cmd_login)

    p = sub.add_parser('logout', parents=[common],
                       help='sign out on the server and delete the saved session file')
    p.add_argument('--local-only', action='store_true',
                   help='only delete the local cookie file, do not contact the server')
    p.set_defaults(func=cmd_logout)

    p = sub.add_parser('library', parents=[common], help='list books in your library')
    p.add_argument('--json', action='store_true', help='print as JSON')
    p.set_defaults(func=cmd_library)

    p = sub.add_parser('download', parents=[common], help='download books')
    p.add_argument('books', nargs='*', help='book ids or viewer URLs')
    p.add_argument('--all', action='store_true', help='download the whole library')
    p.add_argument('--select', help='library numbers from `library`, e.g. 1,3-5')
    p.add_argument('--search', help='download library books whose title contains TEXT')
    p.add_argument('-o', '--output-dir', type=Path, default=Path('downloads'),
                   help='base folder; each book goes into a sub-folder named after its title')
    p.add_argument('--name', help='folder name override (single book only)')
    p.add_argument('--start-page', type=int, help='first page to download (1-based)')
    p.add_argument('--end-page', type=int, help='last page to download (1-based)')
    p.add_argument('--cut-image', type=parse_cut, help='crop L,U,R,D pixels, or "dynamic"')
    p.add_argument('--prefix', default='', help='file name prefix, e.g. klk_v1')
    p.add_argument('--digits', type=int, default=3, help='digits in file names (default: 3)')
    p.add_argument('--sleep', type=float, default=1.0, help='seconds to wait per page (default: 1)')
    p.add_argument('--load-wait', type=float, default=10, help='seconds to wait for the viewer to load (default: 10)')
    p.add_argument('--flip-direction', choices=['auto', 'rtl', 'ltr'], default='auto',
                   help='reading direction for keyboard/click flipping (default: auto)')
    p.add_argument('--no-headless', action='store_true', help='show the browser window')
    p.add_argument('--no-login', action='store_true',
                   help='skip loading the session (for free /trial viewer URLs)')
    p.add_argument('--save-page-source', action='store_true',
                   help='on failure also save error.html (the page source; may contain '
                        'account details such as your email)')
    p.set_defaults(func=cmd_download)
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args) or 0


if __name__ == '__main__':
    sys.exit(main())
