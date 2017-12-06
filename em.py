import os
from concurrent.futures import ThreadPoolExecutor
from urllib import request
import re
import time
from urllib.parse import urljoin
from bs4 import BeautifulSoup
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
        print('获取页面所有小说'+url)
        try:
            headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}
            req = request.Request(url, headers=headers)
            content = request.urlopen(req).read().decode("GBK","ignore")
            soup = BeautifulSoup(content, "html.parser")
            new_urls = set()
            links_soup = soup.select('td.even > a')
            for link in links_soup:
                new_urls.add("/".join(urljoin(url, link["href"]).split('/')[:-1])+str("/index.html"))
            data = {"url":url,"new_urls":new_urls}
        except BaseException as e:
            print(str(e))
            data = None
        return data

    def _get_all_href(self, url):
        print('获取该页面所有章节链接'+url)
        try:
            headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}
            req = request.Request(url, headers=headers)
            content = request.urlopen(req).read().decode("GBK","ignore")
            soup = BeautifulSoup(content, "html.parser")
            new_urls = set()
            links_soup = soup.find("table", class_="t")
            for link in links_soup.find_all('a'):
                if str(link["href"]).find("最新章节") < 0:
                    new_urls.add(urljoin(url, link["href"]))
            data = {"url":url,"new_urls":new_urls}
        except BaseException as e:
            print(str(e))
            data = None
        return data

    def _gogo_content(self, url):
        print('获取该页面所有内容'+url)
        try:
            headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}
            req = request.Request(url, headers=headers)
            content = request.urlopen(req).read().decode("GBK","ignore")
            soup = BeautifulSoup(content, "html5lib")
            contents = []
            content_soup = soup.find("div",id="content").get_text()
            title  = soup.find("h1").get_text()
            code   = url.split('/')[-1][:-5]
            head   = soup.find("span", class_="lft").find_all("a")
            data = {"url":url, "head":head[1].get_text(), "title":code+title, "content":content_soup}
        except BaseException as e:
            print(str(e))
            data = None
        return data

    def gogo(self, url, complete_callback):
        future = self.thread_pool.submit(self._gogo_content, url)
        future.add_done_callback(complete_callback)

class OutPutThreadPool(object):
    '''
    启用最大并发线程数为5的线程池对上面爬取解析线程池结果进行并发处理存储；
    '''
    def __init__(self):
        self.thread_pool = ThreadPoolExecutor(max_workers=10)

    def _output_runnable(self, crawl_result):
        try:
            url = crawl_result['url']
            head = crawl_result['head']
            title = crawl_result['title']
            content = crawl_result['content'].replace(u'\xa0 ', u' ')
            save_dir = 'output' + os.path.sep + head
            print('开始保存文件 %s as %s.txt.' % (url, title))
            if os.path.exists(save_dir) is False:
                os.makedirs(save_dir)
            save_file = save_dir + os.path.sep + title + '.txt'
            save_file = re.sub(r"\?", "", save_file);
            if os.path.exists(save_file):
                print('文件 %s 已经存在!' % title)
                return
            with open(save_file, "w", encoding='utf-8') as file_input:
                file_input.write(content)
        except Exception as e:
            print('保存文件出错！.'+str(e))
        return

    def save(self, crawl_result):
        self.thread_pool.submit(self._output_runnable, crawl_result)


class CrawlManager(object):
    '''
    爬虫管理类，负责管理爬取解析线程池及存储线程池
    '''
    def __init__(self):
        self.crawl_pool = CrawlThreadPool()
        self.output_pool = OutPutThreadPool()

    def _crawl_future_callback(self, crawl_url_future):
        try:
            data = crawl_url_future.result()
            for new_url in data['new_urls']:
                self.start_runner(new_url)
            self.output_pool.save(data)
        except Exception as e:
            print('运行 _crawl_future_callback 出错了！. '+str(e))

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
                    self.crawl_pool.gogo(x, self._jiexi_url)
            while True:
                pass
        except Exception as e:
            print('？？？？？'+str(e))

    def start_runner1(self, url):
        self.crawl_pool.gogo(url, self._jiexi_url)

if __name__ == '__main__':
    root_url = 'http://www.5858xs.com/xiaoshuosort1/0/1.html'
    data21=  CrawlManager()._jiexi_base_url(root_url)
    # root_url = 'http://baike.baidu.com/item/Android'
    # CrawlManager().start_runner1(root_url)