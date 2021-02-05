import os
import os.path as osp
import shutil
import platform
import requests
from unidecode import unidecode

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class CollectLinks():
    def __init__(self, no_gui=False):
        executable = ''

        if platform.system() == 'Windows':
            print('Detected OS : Windows')
            executable = './chromedriver/chromedriver_win.exe'
        elif platform.system() == 'Linux':
            print('Detected OS : Linux')
            executable = './chromedriver/chromedriver_linux'
        elif platform.system() == 'Darwin':
            print('Detected OS : Mac')
            executable = './chromedriver/chromedriver_mac'
        else:
            raise OSError('Unknown OS Type')

        if not osp.exists(executable):
            raise FileNotFoundError('Chromedriver file should be placed at {}'.format(executable))

        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--headless')
        self.browser = webdriver.Chrome(executable, chrome_options=chrome_options)

        browser_version = 'Failed to detect version'
        chromedriver_version = 'Failed to detect version'
        major_version_different = False

        if 'browserVersion' in self.browser.capabilities:
            browser_version = str(self.browser.capabilities['browserVersion'])

        if 'chrome' in self.browser.capabilities:
            if 'chromedriverVersion' in self.browser.capabilities['chrome']:
                chromedriver_version = str(self.browser.capabilities['chrome']['chromedriverVersion']).split(' ')[0]

        if browser_version.split('.')[0] != chromedriver_version.split('.')[0]:
            major_version_different = True

        print('_________________________________')
        print('Current web-browser version:\t{}'.format(browser_version))
        print('Current chrome-driver version:\t{}'.format(chromedriver_version))
        if major_version_different:
            print('warning: Version different')
            print('Download correct version at "http://chromedriver.chromium.org/downloads" and place in "./chromedriver"')
        print('_________________________________')

    def remove_duplicates(self, _list):
        return list(dict.fromkeys(_list))

    def make_dir(self, dirname):
        current_path = os.getcwd()
        path = os.path.join(current_path, dirname)
        if not os.path.exists(path):
            os.makedirs(path)

    def save_object_to_file(self, object, file_path, is_base64=False):
        try:
            with open('{}'.format(file_path), 'wb') as file:
                if is_base64:
                    file.write(object)
                else:
                    shutil.copyfileobj(object.raw, file)
        except Exception as e:
            print('Save failed - {}'.format(e))

    def kiip(self, url, page_idx):
        if 'SB' in url:
            folder = "SB_4"
        elif 'WB' in url:
            folder = "WB_4"
        else:
            folder = "Topik"

        path = "./download/{}".format(folder)

        self.make_dir('{}'.format(path))
        for i in range(1, page_idx + 1):
            link = url.format(i)
            file_name = link.split('/')[-1]
            print("Crawling Image : {}".format(link))
            response = requests.get(link, stream=True)
            self.save_object_to_file(response, os.path.join(path, file_name))
            del response

if __name__ == '__main__':
    crawler = CollectLinks()

    # kii4
    #urls = ['https://kcenter.korean.go.kr/repository/ebook/culture/SB_step4/assets/page-images/page-532044-{:0>4d}.jpg',
                #'https://kcenter.korean.go.kr/repository/ebook/culture/WB_step4/assets/page-images/page-650022-{:0>4d}.jpg']
    #pages = [248, 160]

   

    
    # topik minji
    urls =['http://www.dmook.co.kr/fileRoot/kr/t/o/toko/DigitalAlbumRoot/200112142453/data/{}_0_0.jpg']

    pages = [595]

    for (url, page_idx) in zip(urls, pages):
        crawler.kiip(url, page_idx)
    

    