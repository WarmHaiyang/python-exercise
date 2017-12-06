import os
from concurrent.futures import ThreadPoolExecutor
from urllib import request
import re
import time
import urllib.parse
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import threading
'''
使用单独并发线程池爬取解析及单独并发线程池存储解析结果示例
爬取百度百科Android词条简介及该词条链接词条的简介信息，将结果输出到当前目录下output目录
'''
class CrawlThreadPool(object):
    '''
    启用最大并发线程数为5的线程池进行URL链接爬取及结果解析；
    最终通过crawl方法的complete_callback参数进行爬取解析结果回调
    '''
    def __init__(self):
        self.thread_pool = ThreadPoolExecutor(max_workers=10)

    def _get_base_all_href(self, url):
        print('获取所有漫画目录'+url)
        try:
            headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}
            req = request.Request(url, headers=headers)

            if 'info' in url.split("/"):
                content = self._get_page(url)
            else:
                content = request.urlopen(req).read().decode("utf-8","ignore")
            soup = BeautifulSoup(content, "html.parser")
            new_urls = set()
            if 'info' in url.split("/"):
                links_soup = soup.select('div.zj_list_con a')
            else:
                links_soup = soup.select('div.cartoon_online_border a')

            for link in links_soup:
                new_urls.add(urljoin(url, link["href"]))
            data = {"url":url,"new_urls":new_urls}
        except BaseException as e:
            print(str(e))
            data = None
        return data

    def _get_page(self, url):
        retry_count = 6
        while retry_count > 0:
            try:
                driver.get(url)
                page = driver.page_source
                return page
            except Exception as e:
                print(str(url)+"-----重试第"+str(6-retry_count)+"次")
                retry_count -= 1
                time.sleep(1)
        return None

    def _get_all_href(self, url):
        print('获取该一话中所有图片'+url)
        try:
            new_urls = set()
            page_content = self._get_page(url)
            
            soup = BeautifulSoup(page_content, "html.parser")
            links_soup = soup.select("select#page_select option")

            if 'view' in url.split("/"):
                head = soup.select("div.head_title a")[0].get_text()
                title = soup.select("div.head_title h2")[0].get_text()
            else:
                head = soup.select("h1.hotrmtexth1 a")[0]["title"]
                title = soup.select("span.redhotl")[0].get_text()

            for link in links_soup:
                new_urls.add(urljoin(url, link["value"]))
            data = {"url":url, "head":head, "title":title, "new_urls":new_urls}
        except BaseException as e:
            print(str(e))
            data = None
        return data

    def _gogo_content(self, url, liebiao):
        print('获取该图片的内容'+url)
        try:
            headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)","Referer":"http://manhua.dmzj.com"}
            req = request.Request(url, headers=headers)
            content = request.urlopen(req).read()
            liebiao.append(url[url.rindex("/")+1:])
            data = {"liebiao":liebiao,"content":content}
        except BaseException as e:
            print(str(e))
            data = None
        return data

    def gogo(self, url, liebiao, complete_callback):
        future = self.thread_pool.submit(self._gogo_content, url, liebiao)
        future.add_done_callback(complete_callback)

class OutPutThreadPool(object):
    '''
    启用最大并发线程数为5的线程池对上面爬取解析线程池结果进行并发处理存储；
    '''
    def __init__(self):
        self.thread_pool = ThreadPoolExecutor(max_workers=10)

    def _output_runnable(self, crawl_result):
        try:
            head = crawl_result['liebiao'][0]
            title = crawl_result['liebiao'][1]
            name  = urllib.parse.unquote(crawl_result['liebiao'][2])
            print(crawl_result['liebiao'])
            content = crawl_result['content']
            save_dir = 'manhua' + os.path.sep + head + os.path.sep + title
            print('开始保存文件 %s' % name)
            if os.path.exists(save_dir) is False:
                os.makedirs(save_dir)
            save_file = save_dir + os.path.sep + name
            if os.path.exists(save_file):
                print('文件 %s 已经存在!' % title)
                return
            with open(save_file, "wb") as file_input:
                file_input.write(content)
        except Exception as e:
            print('保存文件出错！.'+str(e))

    def save(self, crawl_result):
        self.thread_pool.submit(self._output_runnable, crawl_result)

class CrawlManager(object):
    '''
    爬虫管理类，负责管理爬取解析线程池及存储线程池
    '''
    def __init__(self):
        self.crawl_pool = CrawlThreadPool()
        self.output_pool = OutPutThreadPool()

    def _jiexi_url(self, crawl_url_future):
        try:
            data2 = crawl_url_future.result()
            self.output_pool.save(data2)
        except Exception as e:
            print('解析单页数据失败'+str(e))

    def _jiexi_base_url(self, url):
        try:
            res = self.crawl_pool._get_base_all_href(url)
            for u in res['new_urls']:
                resss = self.crawl_pool._get_all_href(u)
                for x in resss['new_urls']:
                    self.crawl_pool.gogo(x, [resss['head'], resss['title']], self._jiexi_url)
        except Exception as e:
            print('？？？？？'+str(e))

if __name__ == '__main__':
    # r_url = 'http://manhua.dmzj.com/shengdoushi-mingwangshenhua'
    r_url = 'https://www.dmzj.com/info/wenwuyuan.html'
    # input_url = str(input("请输入地址 按回车开始程序："))
    dcap = dict(DesiredCapabilities.PHANTOMJS)
    dcap["phantomjs.page.settings.userAgent"] = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36")
    dcap["phantomjs.page.settings.CacheControl"] = ("no-cache")
    # 设置user-agent请求头
    dcap["phantomjs.page.settings.loadImages"] = False  # 禁止加载图片
    driver = webdriver.PhantomJS('phantomjs-2.1.1-windows/bin/phantomjs', desired_capabilities=dcap)
    driver.set_page_load_timeout(26)  # 设置页面最长加载时间为26s
    # if input_url:
    #     r_url = input_url
    CrawlManager()._jiexi_base_url(r_url)
    driver.close()
    print('程序结束了，再见！')
    os._exit(0)