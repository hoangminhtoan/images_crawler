import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import ElementNotVisibleException, StaleElementReferenceException
import platform
import requests
import json
from concurrent import futures
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import os.path as osp
import re


class CollectLinks:
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
        if no_gui:
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

    def get_scroll(self):
        pos = self.browser.execute_script("return window.pageYOffset;")
        return pos

    def wait_and_click(self, xpath):
        #  Sometimes click fails unreasonably. So tries to click at all cost.
        try:
            w = WebDriverWait(self.browser, 15)
            elem = w.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            elem.click()
            self.highlight(elem)
        except Exception as e:
            print('Click time out - {}'.format(xpath))
            print('Refreshing browser...')
            self.browser.refresh()
            time.sleep(2)
            return self.wait_and_click(xpath)

        return elem

    def highlight(self, element):
        self.browser.execute_script("arguments[0].setAttribute('style', arguments[1]);", element, "background: yellow; border: 2px solid red;")

    @staticmethod
    def remove_duplicates(_list):
        return list(dict.fromkeys(_list))

    def bing(self, keyword, add_url=""):
        print('[Full Resolution Mode]')
        self.browser.get("https://www.bing.com/images/search?q={}".format(keyword))

        time.sleep(1)
        img_count = 0
        print('Scrolling down')

        links = []
        
        while True:
            image_elements = self.browser.find_elements_by_class_name("iusc")
            if len(image_elements) > img_count:
                img_count = len(image_elements)
                self.browser.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);")
            else:
                smb = self.browser.find_elements_by_class_name("btn_seemore")
                if len(smb) > 0 and smb[0].is_displayed():
                    smb[0].click()
                else:
                    break
            time.sleep(3)

        for image_element in image_elements:
            m_json_str = image_element.get_attribute("m")
            m_json = json.loads(m_json_str)
            links.append(m_json["murl"])

        links = self.remove_duplicates(links)

        print('Collect links done. Site: {}, Keyword: {}, Total: {}'.format('bing', keyword, len(links)))
        self.browser.close()

        return links

    def google(self, keyword, add_url=""):
        print('[Full Resolution Mode]')

        self.browser.get("https://www.google.com/search?q={}&tbm=isch{}".format(keyword, add_url))
        time.sleep(1)

        elem = self.browser.find_element_by_tag_name("body")

        print('Scraping links')

        self.wait_and_click('//div[@data-ri="0"]')
        time.sleep(1)

        links = []
        count = 1

        last_scroll = 0
        scroll_patience = 0

        while True:
            try:
                xpath = '//div[@id="islsp"]//div[@class="v4dQwb"]'
                div_box = self.browser.find_element(By.XPATH, xpath)
                self.highlight(div_box)

                xpath = '//img[@class="n3VNCb"]'
                img = div_box.find_element(By.XPATH, xpath)
                self.highlight(img)

                xpath = '//div[@class="k7O2sd"]'
                loading_bar = div_box.find_element(By.XPATH, xpath)

                # Wait for image to load. If not it will display base64 code.
                while str(loading_bar.get_attribute('style')) != 'display: none;':
                    time.sleep(0.1)

                src = img.get_attribute('src')

                if src is not None:
                    links.append(src)
                    print('%d: %s' % (count, src))
                    count += 1

            except StaleElementReferenceException:
                # print('[Expected Exception - StaleElementReferenceException]')
                pass
            except Exception as e:
                print('[Exception occurred while collecting links from google_full] {}'.format(e))

            scroll = self.get_scroll()
            if scroll == last_scroll:
                scroll_patience += 1
            else:
                scroll_patience = 0
                last_scroll = scroll

            if scroll_patience >= 30:
                break

            elem.send_keys(Keys.RIGHT)

        links = self.remove_duplicates(links)

        print('Collect links done. Site: {}, Keyword: {}, Total: {}'.format('google_full', keyword, len(links)))
        self.browser.close()

        return links
        

    def baidu(self, keyword, add_url=""):
        print('[Full Resolution Mode]')

        def decode_url(url):
            in_table = '0123456789abcdefghijklmnopqrstuvw'
            out_table = '7dgjmoru140852vsnkheb963wtqplifca'
            translate_table = str.maketrans(in_table, out_table)
            mapping = {'_z2C$q': ':', '_z&e3B': '.', 'AzdH3F': '/'}
            for k, v in mapping.items():
                url = url.replace(k, v)
            return url.translate(translate_table)

        base_url = "https://image.baidu.com/search/acjson?tn=resultjson_com&ipn=rj&ct=201326592"\
               "&lm=7&fp=result&ie=utf-8&oe=utf-8&st=-1&word={}".format(keyword)

        query_url = base_url 

        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        }
        res = requests.get(base_url + "&pn=0&rn=30", headers=headers)
        init_json = json.loads(res.text.replace(r"\'", ""), encoding='utf-8', strict=False)
        total_num = init_json['listNum']

        target_num = min(0, total_num)
        crawl_num = min(target_num * 2, total_num)

        crawled_urls = list()
        batch_size = 30

        with futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_list = list()

            def process_batch(batch_no, batch_size):
                image_urls = list()
                url = query_url + "&pn={}&rn={}".format(batch_no * batch_size, batch_size)
                try_time = 0
                while True:
                    try:
                        response = requests.get(url, headers=headers)
                        break
                    except Exception as e:
                        try_time += 1
                        if try_time > 3:
                            print(e)
                            return image_urls
                response.encoding = 'utf-8'
                res_json = json.loads(response.text.replace(r"\'", ""), encoding='utf-8', strict=False)
                for data in res_json['data']:
                    if 'objURL' in data.keys():
                        image_urls.append(decode_url(data['objURL']))
                    elif 'replaceUrl' in data.keys() and len(data['replaceUrl']) == 2:
                        image_urls.append(data['replaceUrl'][1]['ObjURL'])

                return image_urls

            for i in range(0, int((crawl_num + batch_size - 1) / batch_size)):
                future_list.append(executor.submit(process_batch, i, batch_size))
            for future in futures.as_completed(future_list):
                if future.exception() is None:
                    crawled_urls += future.result()
                else:
                    print(future.exception())

        links = crawled_urls[:min(len(crawled_urls), target_num)]
        links = self.remove_duplicates(links)
        
        return links

    def naver(self, keyword, add_url=""):
        print('[Full Resolution Mode]')

        self.browser.get("https://search.naver.com/search.naver?where=image&sm=tab_jum&query={}{}".format(keyword, add_url))
        time.sleep(1)

        elem = self.browser.find_element_by_tag_name("body")

        print('Scraping links')

        self.wait_and_click('//div[@class="photo_bx api_ani_send _photoBox"]')
        time.sleep(1)

        links = []
        count = 1

        last_scroll = 0
        scroll_patience = 0

        while True:
            try:
                xpath = '//div[@class="image _imageBox"]/img[@class="_image"]'
                imgs = self.browser.find_elements(By.XPATH, xpath)

                for img in imgs:
                    self.highlight(img)
                    src = img.get_attribute('src')

                    if src not in links and src is not None:
                        links.append(src)
                        print('%d: %s' % (count, src))
                        count += 1

            except StaleElementReferenceException:
                # print('[Expected Exception - StaleElementReferenceException]')
                pass
            except Exception as e:
                print('[Exception occurred while collecting links from naver_full] {}'.format(e))

            scroll = self.get_scroll()
            if scroll == last_scroll:
                scroll_patience += 1
            else:
                scroll_patience = 0
                last_scroll = scroll

            if scroll_patience >= 100:
                break

            elem.send_keys(Keys.RIGHT)
            elem.send_keys(Keys.PAGE_DOWN)

        links = self.remove_duplicates(links)

        print('Collect links done. Site: {}, Keyword: {}, Total: {}'.format('naver_full', keyword, len(links)))
        self.browser.close()

        return links

    def flickr(self, keyword, add_url=""):
        original_url = "https://www.flickr.com/search/?dimension_search_mode=min&height=640&width=640&text={}&advanced=1&page={}"
        self.browser.get(original_url.format(keyword, 1))
        time.sleep(1)
        
        links = []

        pages = range(1, 5000)

        for page in pages:
            concat_url = original_url.format(keyword, page)
            print("Now it is page {} for {}".format(page, keyword))
            self.browser.get(concat_url)
            for element in self.browser.find_elements_by_css_selector(".photo-list-photo-view"):
                img_url = 'https:'+ re.search(r'url\(\"(.*)\"\)', element.get_attribute("style")).group(1)
                # the url like: https://live.staticflickr.com/xxx/xxxxx_m.jpg
                # if you want to get a clearer(and larger) picture, remove the "_m" in the end of the url.
                links.append(img_url.replace('_m.jpg', '.jpg'))
            
            if len(links) > 2121:
                break

        links = self.remove_duplicates(links)
        print('Collect links done. Site: {}, Keyword: {}, Total: {}'.format('naver_full', keyword, len(links)))
        self.browser.close()

        return links

if __name__ == '__main__':
    crawler = CollectLinks()
    links = crawler.flickr("car")

    print(links)
