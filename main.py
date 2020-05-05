'''
Main file
'''

from downloader import Downloader

settings = {
    'manga_url': 'MANGA_URL',
    'cookies': 'YOUR_COOKIES_HERE',
    'imgdir': 'IMGDIR',
    'res': (784, 1200),
    'sleep_time': 2,
    'loading_wait_time': 20,
    'cut_image': None
}

if __name__ == '__main__':
    downloader = Downloader(**settings)
    downloader.download()
