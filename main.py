import os
import requests
import shutil
from multiprocessing import Pool
import argparse
from collect_links import CollectLinks
import imghdr
import base64

from unidecode import unidecode # remove notation in vietnamese keywords


class Sites:
    GOOGLE = 1
    NAVER = 2
    BING = 3
    BAIDU = 4

    @staticmethod
    def get_text(code):
        if code == Sites.GOOGLE:
            return 'google'
        elif code == Sites.NAVER:
            return 'naver'
        elif code == Sites.BING:
            return 'bing'
        elif code == Sites.BAIDU:
            return 'baidu'

    @staticmethod
    def get_face_url(code):
        if code == Sites.GOOGLE:
            return "&tbs=itp:face"
        if code == Sites.NAVER:
            return "&face=1"


class AutoCrawler:
    def __init__(self, skip_already_exist=True, n_threads=4, 
                do_google=True, do_naver=True, 
                do_bing=True, do_baidu=True,
                download_path='download',
                full_resolution=True, face=False, no_gui=False, limit=0):
        """
        :param skip_already_exist: Skips keyword already downloaded before. This is needed when re-downloading.
        :param n_threads: Number of threads to download.
        :param do_google: Download from google.com (boolean)
        :param do_naver: Download from naver.com (boolean)
        :param download_path: Download folder path
        :param full_resolution: Download full resolution image instead of thumbnails (slow)
        :param face: Face search mode
        :param no_gui: No GUI mode. Acceleration for full_resolution mode.
        :param limit: Maximum count of images to download. (0: infinite)
        """

        self.skip = skip_already_exist
        self.n_threads = n_threads
        self.do_google = do_google
        self.do_naver = do_naver
        self.do_bing = do_bing 
        self.do_baidu = do_baidu
        self.download_path = download_path
        self.full_resolution = full_resolution
        self.face = face
        self.no_gui = no_gui
        self.limit = limit

        os.makedirs('./{}'.format(self.download_path), exist_ok=True)

    @staticmethod
    def all_dirs(path):
        paths = []
        for dir in os.listdir(path):
            if os.path.isdir(path + '/' + dir):
                paths.append(path + '/' + dir)

        return paths

    @staticmethod
    def all_files(path):
        paths = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if os.path.isfile(path + '/' + file):
                    paths.append(path + '/' + file)

        return paths

    @staticmethod
    def get_extension_from_link(link, default='jpg'):
        splits = str(link).split('.')
        if len(splits) == 0:
            return default
        ext = splits[-1].lower()
        if ext == 'jpg' or ext == 'jpeg':
            return 'jpg'
        elif ext == 'gif':
            return 'gif'
        elif ext == 'png':
            return 'png'
        else:
            return default

    @staticmethod
    def validate_image(path):
        ext = imghdr.what(path)
        if ext == 'jpeg':
            ext = 'jpg'
        return ext  # returns None if not valid

    @staticmethod
    def make_dir(dirname):
        current_path = os.getcwd()
        path = os.path.join(current_path, dirname)
        if not os.path.exists(path):
            os.makedirs(path)

    @staticmethod
    def get_keywords(keywords_file='keywords.txt'):
        # read search keywords from file
        with open(keywords_file, 'r', encoding='utf-8-sig') as f:
            text = f.read()
            lines = text.split('\n')
            lines = filter(lambda x: x != '' and x is not None, lines)
            keywords = sorted(set(lines))

        print('{} keywords found: {}'.format(len(keywords), keywords))

        # re-save sorted keywords
        with open(keywords_file, 'w+', encoding='utf-8') as f:
            for keyword in keywords:
                f.write('{}\n'.format(keyword))

        return keywords

    @staticmethod
    def save_object_to_file(object, file_path, is_base64=False):
        try:
            with open('{}'.format(file_path), 'wb') as file:
                if is_base64:
                    file.write(object)
                else:
                    shutil.copyfileobj(object.raw, file)
        except Exception as e:
            print('Save failed - {}'.format(e))

    @staticmethod
    def base64_to_object(src):
        header, encoded = str(src).split(',', 1)
        data = base64.decodebytes(bytes(encoded, encoding='utf-8'))
        return data

    def download_images(self, keyword, links, site_name, max_count=0):
        keyword = unidecode(keyword)
        keyword = keyword.replace(' ', '_')
        self.make_dir('{}/{}'.format(self.download_path, keyword.replace('"', '')))
        total = len(links)
        success_count = 0

        if max_count == 0:
            max_count = total

        for index, link in enumerate(links):
            if success_count >= max_count:
                break

            try:
                print('Downloading {} from {}: {} / {}'.format(keyword, site_name, success_count + 1, max_count))

                if str(link).startswith('data:image/jpeg;base64'):
                    response = self.base64_to_object(link)
                    ext = 'jpg'
                    is_base64 = True
                elif str(link).startswith('data:image/png;base64'):
                    response = self.base64_to_object(link)
                    ext = 'png'
                    is_base64 = True
                else:
                    response = requests.get(link, stream=True)
                    ext = self.get_extension_from_link(link)
                    is_base64 = False
                
                tmp = keyword.replace(' ', '_').strip()
                no_ext_path = '{}/{}/{}_{}_{}'.format(self.download_path.replace('"', ''), tmp, tmp, site_name, str(index).zfill(4))
                path = no_ext_path + '.' + ext
                self.save_object_to_file(response, path, is_base64=is_base64)

                success_count += 1
                del response

                ext2 = self.validate_image(path)
                if ext2 is None:
                    print('Unreadable file - {}'.format(link))
                    os.remove(path)
                    success_count -= 1
                else:
                    if ext != ext2:
                        path2 = no_ext_path + '.' + ext2
                        os.rename(path, path2)
                        print('Renamed extension {} -> {}'.format(ext, ext2))

            except Exception as e:
                print('Download failed - ', e)
                continue

    def download_from_site(self, keyword, site_code):
        site_name = Sites.get_text(site_code)
        add_url = Sites.get_face_url(site_code) if self.face else ""

        try:
            collect = CollectLinks(no_gui=self.no_gui)  # initialize chrome driver
        except Exception as e:
            print('Error occurred while initializing chromedriver - {}'.format(e))
            return

        try:
            print('Collecting links... {} from {}'.format(keyword, site_name))

            if site_code == Sites.GOOGLE:
                links = collect.google(keyword, add_url)

            elif site_code == Sites.NAVER:
                links = collect.naver(keyword, add_url)

            elif site_code == Sites.BING:
                links = collect.bing(keyword, add_url)

            elif site_code == Sites.BAIDU:
                links = collect.baidu(keyword, add_url)

            else:
                print('Invalid Site Code')
                links = []

            print('Downloading images from collected links... {} from {}'.format(keyword, site_name))
            self.download_images(keyword, links, site_name, max_count=self.limit)

            print('Done {} : {}'.format(site_name, keyword))

        except Exception as e:
            print('Exception {}:{} - {}'.format(site_name, keyword, e))

    def download(self, args):
        self.download_from_site(keyword=args[0], site_code=args[1])

    def do_crawling(self):
        keywords = self.get_keywords()

        tasks = []

        for keyword in keywords:
            new_keyword = unidecode(keyword)
            new_keyword = new_keyword.replace(' ', '_')
            dir_name = '{}/{}'.format(self.download_path, new_keyword)
            if os.path.exists(os.path.join(os.getcwd(), dir_name)) and self.skip:
                print('Skipping already existing directory {}'.format(dir_name))
                continue

            if self.do_google:
               tasks.append([keyword, Sites.GOOGLE])

            if self.do_naver:
                tasks.append([keyword, Sites.NAVER])

            if self.do_bing:
                tasks.append([keyword, Sites.BING])
            
            if self.do_baidu:
                tasks.append([keyword, Sites.BAIDU])

        pool = Pool(self.n_threads)
        pool.map_async(self.download, tasks)
        pool.close()
        pool.join()
        print('Task ended. Pool join.')

        self.imbalance_check()

        print('End Program')

    def imbalance_check(self):
        print('Data imbalance checking...')

        dict_num_files = {}

        for dir in self.all_dirs(self.download_path):
            n_files = len(self.all_files(dir))
            dict_num_files[dir] = n_files

        avg = 0
        for dir, n_files in dict_num_files.items():
            avg += n_files / len(dict_num_files)
            print('dir: {}, file_count: {}'.format(dir, n_files))

        dict_too_small = {}

        for dir, n_files in dict_num_files.items():
            if n_files < avg * 0.5:
                dict_too_small[dir] = n_files

        if len(dict_too_small) >= 1:
            print('Data imbalance detected.')
            print('Below keywords have smaller than 50% of average file count.')
            print('I recommend you to remove these directories and re-download for that keyword.')
            print('_________________________________')
            print('Too small file count directories:')
            for dir, n_files in dict_too_small.items():
                print('dir: {}, file_count: {}'.format(dir, n_files))

            print("Remove directories above? (y/n)")
            answer = input()

            if answer == 'y':
                # removing directories too small files
                print("Removing too small file count directories...")
                for dir, n_files in dict_too_small.items():
                    shutil.rmtree(dir)
                    print('Removed {}'.format(dir))

                print('Now re-run this program to re-download removed files. (with skip_already_exist=True)')
        else:
            print('Data imbalance not detected.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip', type=str, default='true',
                        help='Skips keyword already downloaded before. This is needed when re-downloading.')
    parser.add_argument('--threads', type=int, default=16, help='Number of threads to download.')
    parser.add_argument('--google', type=str, default='true', help='Download from google.com (boolean)')
    parser.add_argument('--naver', type=str, default='true', help='Download from naver.com (boolean)')
    parser.add_argument('--bing', type=str, default='true', help='Download from bing.com (boolean)')
    parser.add_argument('--baidu', type=str, default='true', help='Download from baidu.com (boolean)')
    parser.add_argument('--full', type=str, default='true', help='Download full resolution image instead of thumbnails (slow)')
    parser.add_argument('--face', type=str, default='false', help='Face search mode')
    parser.add_argument('--no_gui', type=str, default='auto', help='No GUI mode. Acceleration for full_resolution mode. '
                                                                   'But unstable on thumbnail mode. '
                                                                    'Default: "auto" - false if full=false, true if full=true')
    parser.add_argument('--limit', type=int, default=0, help='Maximum count of images to download per site. (0: infinite)')
    args = parser.parse_args()

    _skip = False if str(args.skip).lower() == 'false' else True
    _threads = args.threads
    _google = False if str(args.google).lower() == 'false' else True
    _naver = False if str(args.naver).lower() == 'false' else True
    _bing = False if str(args.bing).lower() == 'false' else True
    _baidu = False if str(args.baidu).lower() == 'false' else True
    _full = False if str(args.full).lower() == 'false' else True
    _face = False if str(args.face).lower() == 'false' else True
    _limit = int(args.limit)

    no_gui_input = str(args.no_gui).lower()
    if no_gui_input == 'auto':
        _no_gui = _full
    elif no_gui_input == 'true':
        _no_gui = True
    else:
        _no_gui = False

    print('Options - skip:{}, threads:{}, baidu:{}, bing:{}, google:{}, naver:{}, full_resolution:{}, face:{}, no_gui:{}, limit:{}'
          .format(_skip, _threads, _baidu, _bing, _google, _naver, _full, _face, _no_gui, _limit))

    crawler = AutoCrawler(skip_already_exist=_skip, n_threads=_threads,
                          do_google=_google, do_naver=_naver, do_bing=_bing, do_baidu=_baidu, full_resolution=_full,
                          face=_face, no_gui=_no_gui, limit=_limit)
    crawler.do_crawling()
