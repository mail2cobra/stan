# -*- coding: utf-8 -*-

"""
info:www.runff.com 图片保存脚本；多线程版。
address:https://www.runff.com/html/live/s2340.html
author:stan wong
github:
update_time:2019/07/22
"""

# 需要登录，手工登录网页后查看cookie，导出另存到本地文件作为程序登录依据即可。
# 多线程爬取，将照片url爬取后保存到本地文件，读取本地文件的链接后多线程抓取照片到本地另存。

import os
import time
import random

from queue import Queue
from threading import Thread

import requests
from fake_useragent import UserAgent

from xmltodict import parse

# 抓取照片的URL存储文件, URL文件中的字段分隔符
global URL_FILE, URL_SPLIT
URL_FILE = "url.txt"
URL_SPLIT = "|"

# URL队列
global URL_LIST_QUEUE
URL_LIST_QUEUE = Queue()



# 页面爬取类，定义了基本的页面内容爬取逻辑。
class RunffSave(object):

    def __init__(self, race_URL):
        # 初始化heads参数
        self.ua = UserAgent()
        self.raceURL = race_URL
        self.headers = {
            'User-Agent': self.ua.random,
            'Referer': 'https://www.runff.com',
            'Content-Type': 'text/plain',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive'
        }

        # 初始化登录：采用现有cookie
        cookieFile = "d:\\" + self.raceURL + "\\cookie.txt"
        if not os.path.exists(cookieFile):
            print("错误：未找到cookie文件。")
            raise NameError('未找到cookie文件。')
        self.cookies = {}    # 初始化cookies字典变量
        f = open(cookieFile, "r")
        for line in f.read().split(';'):   # 按照字符：进行划分读取
            name, value = line.strip().split('=', 1)
            self.cookies[name] = value  # 为字典cookies添加内容

    # 保存指定比赛的照片的URL到文件。
    def saveRaceURL(self):
        saveCount = 0

        # 检查保存目录是否有效
        savePath = "d:\\" + str(self.raceURL) + "\\"
        if not os.path.exists(savePath):
            os.makedirs(savePath)

        file = open(savePath + URL_FILE, 'w')

        # 爬取相册地址
        url = "https://www.runff.com/html/live/" + self.raceURL + ".html"      # s2340
        print("开始检索指定比赛的照片：" + url)

        # POST数据
        params = {
            "isbxapimode": "true",
            "_xmltime": "1563775651845.0.8034272104939477"
        }

        _payload = '<?xml version="1.0" encoding="utf-8"?><BxMessage><AppId>BxAPI</AppId><Type>1</Type>' \
                   '  <Action>getPhotoList</Action>' \
                   '  <Data>' \
                   '      <fid>0</fid>' \
                   '      <number>照片直播</number>' \
                   '      <pageindex>{}</pageindex>' \
                   '      <time></time>' \
                   '      <sign>false</sign>' \
                   '      <pagesize>{}</pagesize>' \
                   '  </Data>' \
                   '  </BxMessage>'

        more = "true"
        pageIndex = 0
        pageSize = 200
        while more == "true":
            pageIndex = pageIndex + 1
            payload = _payload.format(pageIndex, pageSize).encode('utf-8')

            time.sleep(random.randint(1, 2))
            rs = requests.post(url, headers=self.headers, params=params, data=payload, cookies=self.cookies)

            if rs.status_code != 200:
                print("提示：第" + str(pageIndex) + "页数据检索异常：" + str(rs.status_code))
                return saveCount

            data = parse(rs.content.decode('utf-8'))  # 解析xml为有序字典
            data = data.get('BxMessage', {})
            data = data.get('Data', {})

            more = data.get('more')     # more flag
            data = data.get('list', [])

            for item in eval(data):
                # print(str(item))  # 单个dict对象
                file.write(str(item["id"]) + URL_SPLIT + str(item["mid"]) + URL_SPLIT + str(item["small"]) + URL_SPLIT + str(item["big"]))
                file.write("\n")

                saveCount = saveCount + 1
            print("提示：第" + str(pageIndex) + "页" + str(pageSize) + "条数据已经写入。")

        print("提示：共抓取了" + str(saveCount) + "条图片URL。")
        file.close()
        return saveCount


# 照片保存类，从 URL_FILE 读取待处理的照片链接保存到本地，多线程操作。
class ThreadSavePhoto():
    def __init__(self, race_ID):
        Thread.__init__(self)
        self.count = 0

        savePath = "d:\\" + str(race_ID) + "\\"

        if not os.path.exists(savePath + URL_FILE):
            print("错误：未找到url存储文件。")
            raise NameError('未找到url存储文件')

        # 读url文件到全局list,需要去除readline中的\n符号
        for line in open(savePath + URL_FILE, 'r'):
            URL_LIST_QUEUE.put(line[0: -1] + URL_SPLIT + str(race_ID))

    # 从本地url文件中读取记录并另存图片到本地。
    def writeDisk(self, row_Info):
        # 80454156|50616d33-4ad9-4676-ba21-91f31e087e67|/upload/photos/2019/2019dejjlyh/small/20190709182832_373_000038.jpg|/upload/photos/2019/2019dejjlyh/big/20190709182832_373_000038.jpg
        photoURL = row_Info.split(URL_SPLIT)[3]
        race_ID = row_Info.split(URL_SPLIT)[4]

        savePath = "d:\\" + str(race_ID) + "\\"
        filename = savePath + os.path.basename(photoURL)
        if os.path.exists(filename):
            print("提示：" + filename + " 已经存在。")
            return

        time.sleep(random.randint(1, 3))
        photoURL = "https://p.chinarun.com" + photoURL
        rs = requests.get(photoURL)
        with open(filename, 'wb') as f:
            f.write(rs.content)

        self.count = self.count + 1
        if self.count % 500 == 0:
            print("提示：已经保存了" + str(self.count) + "张照片。")

    def savePhoto(self):
        info = URL_LIST_QUEUE.get()
        self.writeDisk(info)

    def run(self):
        threadList = []
        max_thread = 50

        print("提示：开始后台保存照片，请等待。。。")

        while True:
            if URL_LIST_QUEUE.empty():
                break

            for th in threadList:
                if not th.is_alive():
                    threadList.remove(th)

            if len(threadList) == max_thread:
                continue

            th = Thread(target=self.savePhoto)
            threadList.append(th)
            # th.setDaemon(True)
            th.start()
            th.join()


def main():
    print("www.runff.com图片保存脚本")
    print("------------------------")

    menu = "1"
    while True:
        print("+输入比赛照片页的链接地址：")
        print("+输入0表示退出程序。")
        menu = input("  请输入：")
        if menu == "0":
            break

        raceID = menu
        rbs = RunffSave(raceID)
        saveCount = rbs.saveRaceURL()

        if saveCount <= 0:
            print("提示：未检索到指定比赛的照片信息。")
            continue

        print("+是否继续下载照片文件到本地？1是，0返回上一级菜单。")
        inputID = "0"
        inputID = input("  请输入：")
        if inputID == "0":
            break

        try:
            sp = ThreadSavePhoto(raceID)
        except Exception as e:
            print("错误：" + e)
            print("")
            continue

        sp.run()


def test():
    # rbs = RunffSave("s2340")
    # rbs.saveRaceURL()

    # 从现有url文件直接下载。
    try:
        sp = ThreadSavePhoto("s2340")
        sp.run()
    except Exception as e:
        print("错误：" + e)
        print("")


if __name__ == '__main__':
    test()
