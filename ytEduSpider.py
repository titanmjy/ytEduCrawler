import re
import subprocess

from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver
from browsermobproxy import Server
import time
from selenium.webdriver.chrome.options import Options
import os


class ytEduCrawler:
    domain = "ksbao.com"
    start_url = "https://wide.ksbao.com/login"

    def __init__(self, domain=domain):
        # 本地代理server
        self.server = Server(r'D:\Programs\browsermob-proxy-2.1.4-bin\browsermob-proxy-2.1.4\bin\browsermob-proxy.bat')
        self.server.start()
        self.proxy = self.server.create_proxy()
        chrome_options = Options()
        chrome_options.add_argument('--proxy-server={0}'.format(self.proxy.proxy))
        chrome_options.add_argument('--incognito')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--disable-gpu')
        self.chrome = webdriver.Chrome(chrome_options=chrome_options)
        self.proxy.new_har(domain)

    def quit(self):
        self.server.stop()
        self.chrome.quit()

    def login(self, login_url):
        self.chrome.get(login_url)
        wait = WebDriverWait(self.chrome, 10)
        wait.until(EC.presence_of_element_located((By.XPATH, '/html/body')))
        input_name = self.chrome.find_element_by_id("txtName")
        input_passwd = self.chrome.find_element_by_id("pswPassword")
        # input_name.send_keys("13770273837")
        input_name.send_keys("13584783806")
        input_passwd.send_keys("123456")
        self.chrome.find_element_by_id("login").click()
        time.sleep(5)
        # 关闭弹框
        # wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'close_btn')))
        # self.chrome.find_element_by_class_name("close_btn").click()
        # 刷新页面，不用点击弹框关闭
        # self.chrome.refresh()
        # time.sleep(2)

    # 点击menu，找到chapter的index
    def seek_chapter_start(self, start_index):
        # 点击考点精讲
        self.chrome.find_element_by_class_name("rout-kdjj").click()
        time.sleep(2)
        self.chrome.refresh()
        time.sleep(2)
        # 左侧课程导航目录
        EC.presence_of_element_located((By.CLASS_NAME, "content_left"))
        menu_list = self.chrome.find_elements_by_xpath("//ul[@class='content_left']//li")
        current_index_count = 0
        for menu_index in range(1, len(menu_list)+1):
            time.sleep(2)
            menu = self.chrome.find_element_by_xpath("//ul[@class='content_left']/li[" + str(menu_index) + "]")
            # 点击左侧课程目录
            menu.click()
            EC.presence_of_element_located((By.CLASS_NAME, "content_rig"))
            time.sleep(2)
            chapter_length = len(self.chrome.find_elements_by_xpath("//ul[@class='content_rig']//li"))
            chapter_index = 0
            for i in range(1, chapter_length+1):
                current_chapter_size_desc = self.chrome.find_element_by_xpath("//ul[@class='content_rig']/li["+str(i)+"]/span").text
                current_chapter_size = int(re.sub("\D","",current_chapter_size_desc))
                video_index = start_index - current_index_count
                current_index_count += current_chapter_size
                chapter_index += 1
                if current_index_count >= start_index:
                    break
            if current_index_count >= start_index:
                break
        # 返回menu chapter video 三级断点续传index
        return menu_index, chapter_index, video_index

    # 根据请求记录获取m3u8的url地址列表，左开右闭，start_index: 视频编号，从1开始,end_index不包括
    def get_m3u8_url_list(self, start_index, end_index):
        course_url_list = []
        request_logs = self.proxy.har
        for entry in request_logs['log']['entries']:
            m3u8_url = entry['request']['url']
            if "m3u8" in m3u8_url:
                # print(m3u8_url)
                course_url_list.append(m3u8_url)
        return course_url_list[start_index - end_index:end_index]

    def vedio_download(self, name_list, url_list):
        for name, _url in zip(name_list, url_list):
            print(name + ":" + _url)
            os.system("start N_m3u8DL-CLI " + _url + " --saveName " + '"'+ name +'"')
            time.sleep(7)

    # 控制浏览器依次点击视频，并记录视频名称，左开右闭，start_index: 视频编号，从1开始,end_index不包括
    def visit_and_get_name_list(self, start_index, end_index):
        menu_chapter_video_list = []
        menu_start, chapter_start, video_start = self.seek_chapter_start(start_index)
        menu_list = self.chrome.find_elements_by_xpath("//ul[@class='content_left']//li")
        for menu_index in range(menu_start, len(menu_list)+1):
            time.sleep(2)
            menu = self.chrome.find_element_by_xpath("//ul[@class='content_left']/li[" + str(menu_index) + "]")
            menu_name = menu.text
            # 点击左侧课程目录
            menu.click()
            EC.presence_of_element_located((By.CLASS_NAME, "content_rig"))
            time.sleep(2)
            chapter_list = self.chrome.find_elements_by_xpath("//ul[@class='content_rig']//li")
            for chapter_index in range(chapter_start, len(chapter_list) + 1):
                time.sleep(2)
                # 点击左侧具体课程目录
                current_menu = self.chrome.find_element_by_xpath("//ul[@class='content_left']/li[" + str(menu_index) + "]")
                current_menu.click()
                time.sleep(2)
                # 点击右侧章节，直接播放当前章节第一个video
                chapter = self.chrome.find_element_by_xpath("//ul[@class='content_rig']/li[" + str(chapter_index) + "]")
                chapter_name = chapter.text
                chapter.click()
                time.sleep(5)
                video_list = self.chrome.find_elements_by_xpath("//div[@class='listPart']//li[@class='clearfix']")
                for video_index in range(video_start, len(video_list) + 1):
                    video = self.chrome.find_element_by_xpath("//div[@class='listPart']//li[@class='clearfix'][" + str(video_index) + "]")
                    video_name = video.text
                    menu_chapter_video_list.append(menu_name + "_" + chapter_name + "_" + video_name)
                    if len(video_list) > 1:
                        video.click()
                        time.sleep(5)
                    if len(menu_chapter_video_list) >= (end_index - start_index):
                        break
                self.chrome.back()
                if len(menu_chapter_video_list) >= (end_index - start_index):
                    break
            if len(menu_chapter_video_list) >= (end_index - start_index):
                break
            #         # 视频列表
            #         EC.presence_of_element_located((By.TAG_NAME, "video"))
            #         time.sleep(5)
            #         video_list = self.chrome.find_elements_by_class_name("summary")
            #         for video in video_list:
            #             video.click()
            #             time.sleep(10)
            #             self.chrome.back()
            #             # result = self.proxy.har
            #             # print(result['log']['entries'])
            #             # for entry in result['log']['entries']:
            #             #     _url = entry['request']['url']
            #             #     print(_url)
            #         # 考点详情
            #         # "//pre"
            #         # 考点精讲
            #         # //div[@class='testBtn subBtnColor']
            #         # 点击背题模式，选择目标div
            #         # //div[@class='exambt']
            #         self.chrome.back()
        return menu_chapter_video_list[start_index - end_index:end_index]

    # 左开右闭，start_index: 视频编号，从1开始,end_index不包括
    def start_request(self, start_index, end_index, url=start_url):
        print("============================")
        # 首页登录
        self.login(url)
        # 访问指定数量视频的页面
        name_list = self.visit_and_get_name_list(start_index, end_index)
        # 获取视频地址
        course_url_list = self.get_m3u8_url_list(start_index, end_index)
        # for i,j in zip(name_list, course_url_list):
        #     print(i+" : "+j)
        self.vedio_download(name_list, course_url_list)


if __name__ == "__main__":
    try:
        spider = ytEduCrawler()
        spider.start_request(start_index=22, end_index=33)
    finally:
        spider.quit()
