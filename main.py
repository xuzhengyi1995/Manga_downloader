'''
Main file
'''

from downloader import Downloader

settings = {
    # Manga url
    'manga_url': 'MANGA_URL',
    # Your cookies
    'cookies': 'YOUR_COOKIES_HERE',
    # Folder name to store the Manga
    'imgdir': 'IMGDIR',
    # Resolution, (Width, Height), For coma this doesn't matter.
    'res': (784, 1200),
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
    'number_of_digits': 3
}

if __name__ == '__main__':
    downloader = Downloader(**settings)
    downloader.download()
