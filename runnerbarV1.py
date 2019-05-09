# -*- coding: utf-8 -*-

"""
info:www.runnerbar.com 图片保存脚本；单线程版。
author:stan wong
github:
update_time:2019/05/03
"""

import json
import os
import random
import time
from datetime import datetime

import requests
from fake_useragent import UserAgent

from tools import is_equal_date


class RunnerBarSave(object):

    def __init__(self, race_date: datetime = datetime.today().date()):
        self.ua = UserAgent()
        self.raceDate = race_date
        self.activityList = "http://www.runnerbar.com/yd_runnerbar/activityList"
        self.headers = {
            'User-Agent': self.ua.random,
            'Referer': self.activityList,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Connection': 'keep-alive'
            # 'Connection': 'close'
        }

    # 输出符合条件的比赛名称，返回对应的比赛ID列表。
    def get_raceList(self):
        print("开始检索指定比赛日(" + datetime.strftime(self.raceDate, "%Y-%m-%d") + ")的比赛信息。。。")

        url = "http://m.yundong.runnerbar.com/yd_mobile/wx_manager/getPortalActivity"

        headers = {
            'User-Agent': self.ua.random,
            'Referer': self.activityList,
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': 'application/json, text/javascript, */*; q=0.01'
        }

        # 返回值
        result = list()

        size = 20
        # 默认检索前5页数据，每页20条数据
        for i in range(0, 100, size):
            # POST数据
            datas = {
                'index': i,
                'size': size
            }

            # time.sleep(random.randint(1, 3))
            rs = requests.post(url, headers=headers, data=datas)

            if rs.status_code != 200:
                print("    第" + str(i / 20) + "页检索异常:" + str(rs.status_code))
                continue
            else:
                data = rs.json()
                status = data["status"]

                if status == 0:
                    ds = data["result"]
                    pl = ds["portalList"]

                    value = {}
                    for item in pl:
                        start_time = datetime.fromtimestamp(float(item["start_time"]) / 1000)

                        if not is_equal_date(start_time.date(), self.raceDate):
                            continue

                        # 比赛日期符合条件
                        value.clear()
                        value.setdefault("id", item["id"])
                        value.setdefault("title", item["title"])
                        value.setdefault("city", item["city"])
                        value.setdefault("activity_photo_count", item["activity_photo_count"])
                        result.append(value.copy())
                else:
                    print("    第" + str(i / 20) + "页检索异常。")

        return result

    # 格式化输出指定的比赛相册信息。
    def get_raceInfo(self, item):
        print(str(item["id"]).ljust(10) + str(item["title"]).ljust(40) + str(item["city"]).ljust(10) + "  照片数" + str(item["activity_photo_count"]).ljust(10))

    # 保存指定参数号码的照片。
    def saveRaceNumPhoto(self, race_ID, race_num):
        print("开始检索指定参数号码的照片：" + str(race_num))

        saveCount = 0

        # 检查保存目录是否有效
        savePath = "d:\\" + str(race_ID) + "\\"
        if not os.path.exists(savePath):
            os.makedirs(savePath)

        # 爬取相册地址
        url = "http://www.runnerbar.com/yd_runnerbar/album/getGameNumPhotoList.json"

        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'User-Agent': self.ua.random,
            'Referer': 'http://www.runnerbar.com/yd_runnerbar/album/pc?activity_id=' + str(race_ID)
        }

        # POST数据
        datas = {
            'uid': 3333,
            'activity_id': race_ID,
            'game_number': race_num,
            'index': 0,
            'size': 1000
        }

        time.sleep(random.randint(1, 2))
        rs = requests.post(url, headers=headers, data=datas)
        if rs.status_code != 200:
            print("提示：数据检索异常：" + str(rs.status_code))
            return

        data = json.loads(rs.text)
        data = data["photoList"]

        for item in data:
            photoURL = item["url_hq"]
            filename = savePath + os.path.basename(photoURL)
            if os.path.exists(filename):
                print("提示：" + filename + " 已经存在。")
                continue

            try:
                rs = requests.get(photoURL)
                with open(filename, 'wb') as f:
                    f.write(rs.content)

                saveCount = saveCount + 1
                print("提示：" + filename + "已经保存。")
            except Exception:
                print("提示：保存 " + photoURL + " 时发生错误。")

        if int(saveCount) % 10 == 0:
            print("提示：已经保存了" + str(saveCount) + "张图片，保存位置[" + savePath + "]。")

        print("提示：共保存了" + str(saveCount) + "张图片，保存位置[" + savePath + "]。")

    # 保存指定比赛的照片。
    def saveRaceListPhoto(self, race_ID, race_List):
        print("开始检索指定相册ID的照片：" + str(race_ID))

        # http://www.runnerbar.com/yd_runnerbar/album/pc?type=1&activity_id=20722
        # http://m.yundong.runnerbar.com/yd_mobile/share/album.json?callback=jQuery31005949012655658235_1557026252548&activity_id=20722&page=1&pageSize=25&_=1557026252549

        # 确定相册照片数量
        photoCount = 0
        for item in race_List:
            if item["id"] == race_ID:
                photoCount = item["activity_photo_count"]
        if photoCount == 0:
            print("提示：检索照片时发生异常，请核查相册ID输入。")
            return

        saveCount = 0

        # 检查保存目录是否有效
        savePath = "d:\\" + str(race_ID) + "\\"
        if not os.path.exists(savePath):
            os.makedirs(savePath)

        # 爬取相册地址
        url = "http://m.yundong.runnerbar.com/yd_mobile/share/album.json"

        # 原链接中使用 callback 参数回调jsonp数据，为了便于处理，去掉该参数，直接返回json数据。
        headers = {
            # 'callback': 'XXX',
            'User-Agent': self.ua.random,
            'Referer': 'http://www.runnerbar.com/yd_runnerbar/album/pc?activity_id=' + str(race_ID)
        }

        pageSize = 25
        for i in range(1, int(photoCount/pageSize+1)):
            # GET数据
            datas = {
                'activity_id': race_ID,
                'page': i,
                'pageSize': pageSize
            }

            time.sleep(random.randint(1, 2))
            rs = requests.post(url, headers=headers, data=datas)
            if rs.status_code != 200:
                print("提示：第" + str(i) + "页数据检索异常：" + str(rs.status_code))
                continue

            data = json.loads(rs.text)
            data = data["album"]
            data = data["searchResultList"]

            for item in data:
                photoURL = item["url_hq"]

                # 去除 ?quality=h 后缀h
                filename = savePath + os.path.basename(photoURL)[0:-10]
                if os.path.exists(filename):
                    print("提示：" + filename + " 已经存在。")
                    continue

                try:
                    rs = requests.get(photoURL)
                    with open(filename, 'wb') as f:
                        f.write(rs.content)

                    saveCount = saveCount + 1
                    print("提示：" + filename + "已经保存。")
                except Exception:
                    print("提示：保存 " + photoURL + " 时发生错误。")

            if int(saveCount) % 1000 == 0:
                print("提示：已经保存了" + str(saveCount) + "张图片，保存位置[" + savePath + "]。")

            # test
            # if saveCount > 55:
            #     break

        print("提示：共保存了" + str(saveCount) + "张图片，保存位置[" + savePath + "]。")


if __name__ == '__main__':
    print("www.runnerbar.com图片保存脚本")
    print("----------------------------")

    menu = "1"
    while True:
        print("+输入比赛日期(yyyy-mm-dd)并回车确认以检索相册地址；")
        print("+输入1并回车确认，则默认当前日期为比赛日期；")
        print("+输入0表示退出程序。")
        menu = input("  请输入：")
        raceDate = datetime.today()
        if menu == "0":
            break
        if menu == "1":
            raceDate = datetime.today().date()
        else:
            try:
                raceDate = datetime.strptime(menu, "%Y-%m-%d")
            except Exception:
                print("提示：输入的日期格式不对，请重新输入。")
                print("")
                continue

        rbs = RunnerBarSave(raceDate)
        raceList = rbs.get_raceList()

        if len(raceList) <= 0:
            print("提示：未检索到指定日期的比赛相册信息。")
            continue

        print("检索到的比赛相册信息如下：")
        for item in raceList:
            rbs.get_raceInfo(item)

        raceID = 0
        raceNum = 0
        while True:
            print("++请输入要保存的比赛相册ID，并回车确认：")
            print("++如果要按参数号码过滤检索，请在比赛相册ID后分隔输入参数号码（20722-1617），并回车确认：")
            print("++输入0表示返回上一级菜单。")
            inputID = input("  请输入：")
            if inputID == "0":
                break
            else:
                raceInput = inputID.split("-")

                try:
                    raceID = int(raceInput[0])
                except Exception:
                    print("提示：比赛相册ID输入的数字格式不对，请重新输入。")
                    print("")
                    continue

                if len(raceInput) > 1:
                    try:
                        raceNum = int(inputID.split("-")[1])
                    except Exception:
                        print("提示：参数号码输入的数字格式不对，请重新输入。")
                        print("")
                        continue
                    rbs.saveRaceNumPhoto(raceID, raceNum)
                else:
                    rbs.saveRaceListPhoto(raceID, raceList)
