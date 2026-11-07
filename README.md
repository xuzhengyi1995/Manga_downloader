# Manga_Downloader (BookWalker TW)

A command-line downloader for books you own on [BOOK☆WALKER 台灣漫讀](https://www.bookwalker.com.tw), built on Selenium.

- Log in once in a real browser window. Later runs reuse the saved session headlessly.
- List your bookshelf and pick books by number, by title search, or download everything.
- Pages flip automatically. The tool finds the viewer's page API by itself, so it keeps working when BookWalker re-obfuscates its scripts, and falls back to the keyboard and to mouse clicks.
- Each book is saved to `<output-dir>/<book title>/000.png, 001.png, ...`. Interrupted downloads resume where they stopped.

Only download books you have purchased, for personal use.

## Requirements

- Python 3.12+
- Google Chrome (any current version). You do **not** need to install chromedriver: Selenium Manager downloads the driver that matches your Chrome automatically.

```shell
conda activate bw            # or any venv
pip install -r requirements.txt
```

## Usage

### 1. Log in (once)

```shell
python main.py login
```

A Chrome window opens on the BookWalker TW login page. Sign in normally. When the login finishes, the session cookies are saved to `~/.manga_downloader/bw_tw_cookies.json`. You can change the location with `--cookies PATH` or the `BW_COOKIES` environment variable.

That file is equivalent to your password, so do not share it or commit it. It only contains BookWalker TW cookies. On Linux and macOS it is created owner-only (`0600`, in a `0700` folder); on Windows it inherits your user-profile permissions. When the session expires, the tool asks you to run `login` again.

To remove the session when you are done:

```shell
python main.py logout               # sign out on BookWalker, verify, then delete the file
python main.py logout --local-only  # only delete the local file
```

`logout` checks the result by loading the saved cookies again in a fresh browser. If they still log in, it tells you that BookWalker did not revoke the session. In that case, sign out of all devices or change your password on the website.

### 2. List your books

```shell
python main.py library          # numbered list: No.  id  title
python main.py library --json
```

### 3. Download

```shell
# By number from `library`
python main.py download --select 1,3-5 -o D:\Manga

# By title search, the whole library, or explicit ids / viewer URLs
python main.py download --search 葬送的芙莉蓮 -o D:\Manga
python main.py download --all -o D:\Manga
python main.py download 123456 https://www.bookwalker.com.tw/browserViewer/654321/read -o D:\Manga

# Free trial pages need no login (handy to test your setup)
python main.py download https://www.bookwalker.com.tw/browserViewer/38352/trial --no-login -o D:\Manga
```

| Option | Default | Description |
| --- | --- | --- |
| `-o, --output-dir` | `downloads` | Base folder. Each book gets a sub-folder named after its title. |
| `--name` | book title | Folder name override (single book only). |
| `--start-page`, `--end-page` | whole book | Page range, 1-based. |
| `--res WxH` | `784x1200` | Viewer size, which is also the image size. Raise it for higher-resolution books, e.g. `1568x2400`. |
| `--cut-image L,U,R,D` / `dynamic` | none | Crop pixels from each edge, or auto-trim white borders based on page 1. |
| `--prefix`, `--digits` | `''`, `3` | File names such as `klk_v1_001.png`. |
| `--sleep` | `1` | Extra seconds per page. Increase this if you get repeated pages. |
| `--load-wait` | `10` | Seconds to wait for the viewer to start. |
| `--flip-direction` | `auto` | `rtl` / `ltr`. Only used by the keyboard and click fallbacks. |
| `--no-headless` | off | Show the browser while downloading. |
| `--cookies PATH` | `~/.manga_downloader/bw_tw_cookies.json` | Session file. |
| `--save-page-source` | off | On failure, also save `error.html` (the page source). |

If a download fails, `error.png` (a screenshot) is written into that book's folder. Add `--save-page-source` to also get `error.html`. It is off by default because logged-in BookWalker pages can contain your email address and member ID. Don't share it.

Only `https://www.bookwalker.com.tw/browserViewer/<id>/read` or `/trial` URLs (or a plain id) are accepted. Titles and authors from the site are stripped of control characters before they reach your terminal.

The viewer may reopen at your last-read page. With the page API this does not matter. If the tool only has the keyboard or click fallback, reset the read position first.

## Docker

Log in on the host first (Docker has no visible browser). Then run:

```shell
docker compose build
docker compose run --rm mangadw download --select 1 -o /downloads
```

The compose file mounts `~/.manga_downloader` (the session) and `./downloads`. A `.dockerignore` keeps `downloads/`, error dumps, cookie files and `.git` out of the image. Still, don't push the image to a registry.

## Security notes

- While a run is active, Chrome is controlled through chromedriver on a random `127.0.0.1` port with no authentication. Run the tool on a machine where you are the only user, or in Docker.
- Inside Docker the container runs as root, so Chrome starts with `--no-sandbox`.
- A security audit of this tool (Cloudflare `security-audit` skill, quick profile) is saved outside the repo, under `~/security-audit-skill/Manga_downloader/`.

## Develop

```
main.py                         CLI (login / library / download)
browser.py                      Chrome driver factory, cookie save/load via CDP
downloader.py                   Page loop: wait → capture → crop → save → flip
website_actions/
  abstract_website_actions.py   WebsiteActions ABC + Book dataclass
  bookwalker_tw_actions.py      BookWalker TW viewer and bookshelf logic
```

Page flipping in `bookwalker_tw_actions.py` tries three strategies in this order and keeps the first one that works:

1. The viewer's `moveToPage()`, found by walking `window.NFBR` instead of using hardcoded names.
2. Arrow keys.
3. Clicking the page edge.

A flip only counts once the page counter (`#pageSliderCounter`) or the canvas content has changed.
