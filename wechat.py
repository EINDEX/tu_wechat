
import codecs
import csv
import re
from datetime import date, datetime, timedelta
from functools import lru_cache
from urllib import parse

import fire
import requests

import uncurl

fieldnames = ['time', 'read_num', 'like_num', 'copyright_type',
              'tou', 'title', 'content_url']


class Mession:
    def __init__(self, curl_commend, start, end, only_tu=True):
        context = uncurl.parse_context(curl_commend)
        self.params = dict(parse.parse_qsl(parse.urlsplit(context.url).query))
        self.headers = context.headers
        self.cookies = context.cookies
        self.start = start
        self.end = end + timedelta(days=1)
        self.only_tu = only_tu

    def get_data(self, begin: int):
        self.params['begin'] = str(begin)
        res = requests.get(
            'https://mp.weixin.qq.com/cgi-bin/newmasssendpage',
            headers=self.headers,
            params=self.params,
            cookies=self.cookies
        )

        if res.ok:
            return res.json()

        raise Exception()

    def get_data_start_to_end(self, start: datetime, end: datetime):
        err_num = 5
        i = 0
        res = []
        send_time = end
        while start < send_time:
            print(start, send_time)
            if err_num < 0:
                raise Exception()
            try:
                print(f'get data {i}')
                data = self.get_data(i)
                for sent in data['sent_list']:
                    tou = True
                    send_time = datetime.fromtimestamp(
                        sent['sent_info']['time'])
                    if send_time < start:
                        break
                    elif send_time > end:
                        continue
                    for appmsg in sent['appmsg_info']:
                        if tou:
                            appmsg['tou'] = 1
                            tou = False
                        else:
                            appmsg['tou'] = 0
                        appmsg['time'] = str(send_time)
                        res.append(appmsg)
                i += 7
            except Exception as e:
                print(e)
                err_num -= 1
        return res

    def filter_den(self, url, times=3):
        if times <= 0:
            return False
        try:
            headers = {
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7,la;q=0.6',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
                'Accept': '*/*',
                'Connection': 'keep-alive',
            }
            res = requests.get(url, headers=headers)
            if res.ok:
                if re.findall('兔纸', res.text):
                    return True
            return False
        except Exception:
            return self.filter_den(url, times-1)

    def write_data(self, res, file_name="wechat.csv"):
        with open(file_name, 'wb') as csvfile:
            csvfile.write(codecs.BOM_UTF8)
        with open(file_name, 'a') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames)
            writer.writeheader()
            writer.writerows(res)

    def do(self):
        r = self.get_data_start_to_end(self.start, self.end)

        res = []
        for i in r:
            if self.only_tu:
                print(f"check {i['title']}")
                if not self.filter_den(i['content_url']):
                    continue
            for k in list(i.keys()):
                if k not in fieldnames:
                    i.pop(k)
            res.append(i)
        self.write_data(
            res,
            f"wechat_{str(self.start.date())}_{str(self.end.date())}{'_tu' if self.only_tu else ''}.csv"
        )


class Wechat:
    def date(self, start: str, end: str, only_tu=True):
        with open('request.curl', 'r') as f:
            curl_commend = f.read()

        start = datetime.strptime(start, "%Y-%m-%d")
        end = datetime.strptime(end, "%Y-%m-%d")

        m = Mession(curl_commend, start, end, only_tu)
        m.do()

    def date_to_today(self, start: str, only_tu=True):
        self.data(start, str(date.today()), only_tu)


if __name__ == "__main__":
    fire.Fire(Wechat)
