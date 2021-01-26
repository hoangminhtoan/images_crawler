# AutoCrawler
Baidu, Bing, Google, Naver multiprocess image crawler (High Quality & Speed & Customizable)

![](assets/animation.gif)

# How to use

1. Install Chrome

2. pip install -r requirements.txt

3. Write search keywords in keywords.txt

4. **Run "main.py"**

5. Files will be downloaded to 'download' directory.


# Arguments
usage:
```
python3 main.py [--skip true] [--threads 50] [--google true] [--naver true] [--bing true] [--baidu true] [--full true] [--face false] [--no_gui auto] [--limit 0]
```

```
--skip true        Skips keyword if downloaded directory already exists. This is needed when re-downloading.

--threads 116        Number of threads to download.

--google true      Download from google.com (boolean)

--naver true       Download from naver.com (boolean)

--bing true        Download from bing.com (boolean)

--baidu true        Download from baidu.com (boolean)

--full true       Download full resolution image instead of thumbnails (slow)

--face false       Face search mode

--no_gui auto      No GUI mode. (headless mode) Acceleration for full_resolution mode, but unstable on thumbnail mode.
                   Default: "auto" - false if full=false, true if full=true
                   (can be used for docker linux system)
                   
--limit 0          Maximum count of images to download per site. (0: infinite)
```


# Full Resolution Mode

You can download full resolution image of JPG, GIF, PNG files by specifying --full true

![](assets/full.gif)

# Data Imbalance Detection

Detects data imbalance based on number of files.

When crawling ends, the message show you what directory has under 50% of average files.

I recommend you to remove those directories and re-download.

# Customize

You can make your own crawler by changing collect_links.py

# Issues

As google site consistently changes, please make issues if it doesn't work.

# References
* [Auto Crawler](https://github.com/YoongiKim/AutoCrawler)
* [Image Downloader](https://github.com/sczhengyabin/Image-Downloader)

