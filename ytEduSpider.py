import functools
import re
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver
from browsermobproxy import Server
import time
from selenium.webdriver.chrome.options import Options
import os
import pdfkit
from PyPDF2 import PdfFileReader, PdfFileWriter


class ytEduCrawler:
    domain = "ksbao.com"
    start_url = "https://wide.ksbao.com/login"

    # 下载视频需要server参数，默认为None表示非下载视频的情况
    def __init__(self, domain=domain, server=None ):
        chrome_options = Options()
        chrome_options.add_argument('--incognito')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--disable-gpu')
        self.server = server
        if server is not None:
            server.start()
            self.proxy = server.create_proxy()
            chrome_options.add_argument('--proxy-server={0}'.format(self.proxy.proxy))
            self.proxy.new_har(domain)
        self.chrome = webdriver.Chrome(chrome_options=chrome_options)

    def quit(self):
        if self.server is not None:
            self.server.stop()
        self.chrome.quit()
        time.sleep(3)

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
    def seek_chapter_start(self, start_index, end_index):
        # 点击考点精讲
        self.chrome.find_element_by_class_name("rout-kdjj").click()
        time.sleep(2)
        self.chrome.refresh()
        time.sleep(2)
        # 左侧课程导航目录
        EC.presence_of_element_located((By.CLASS_NAME, "content_left"))
        menu_list = self.chrome.find_elements_by_xpath("//ul[@class='content_left']//li")
        current_index_count = 0
        for menu_index in range(1, len(menu_list) + 1):
            time.sleep(2)
            menu = self.chrome.find_element_by_xpath("//ul[@class='content_left']/li[" + str(menu_index) + "]")
            # 点击左侧课程目录
            menu.click()
            EC.presence_of_element_located((By.CLASS_NAME, "content_rig"))
            time.sleep(2)
            chapter_length = len(self.chrome.find_elements_by_xpath("//ul[@class='content_rig']//li"))
            chapter_index = 0
            for i in range(1, chapter_length + 1):
                current_chapter_size_desc = self.chrome.find_element_by_xpath(
                    "//ul[@class='content_rig']/li[" + str(i) + "]/span").text
                current_chapter_size = int(re.sub("\D", "", current_chapter_size_desc))
                video_index = start_index - current_index_count
                current_index_count += current_chapter_size
                chapter_index += 1
                if current_index_count >= start_index or current_index_count >= end_index:
                    break
            if current_index_count >= start_index or current_index_count >= end_index:
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
            os.system("start N_m3u8DL-CLI " + _url + " --saveName " + '"' + name + '"')
            time.sleep(7)

    # 控制浏览器依次点击视频，并记录视频名称，左开右闭，start_index: 视频编号，从1开始,end_index不包括
    def visit_and_get_name_list(self, start_index, end_index):
        menu_chapter_video_list = []
        menu_start, chapter_start, video_start = self.seek_chapter_start(start_index, end_index)
        menu_list = self.chrome.find_elements_by_xpath("//ul[@class='content_left']//li")
        for menu_index in range(menu_start, len(menu_list) + 1):
            time.sleep(2)
            menu = self.chrome.find_element_by_xpath("//ul[@class='content_left']/li[" + str(menu_index) + "]")
            menu_name = menu.text
            # 点击左侧导航目录
            menu.click()
            EC.presence_of_element_located((By.CLASS_NAME, "content_rig"))
            time.sleep(2)
            chapter_list = self.chrome.find_elements_by_xpath("//ul[@class='content_rig']//li")
            for chapter_index in range(chapter_start, len(chapter_list) + 1):
                time.sleep(2)
                # 点击左侧具体课程目录
                current_menu = self.chrome.find_element_by_xpath(
                    "//ul[@class='content_left']/li[" + str(menu_index) + "]")
                current_menu.click()
                time.sleep(2)
                # 点击右侧章节，直接播放当前章节第一个video
                chapter = self.chrome.find_element_by_xpath("//ul[@class='content_rig']/li[" + str(chapter_index) + "]")
                chapter_name = chapter.text
                chapter.click()
                time.sleep(5)
                video_list = self.chrome.find_elements_by_xpath("//div[@class='listPart']//li[@class='clearfix']")
                for video_index in range(video_start, len(video_list) + 1):
                    video = self.chrome.find_element_by_xpath(
                        "//div[@class='listPart']//li[@class='clearfix'][" + str(video_index) + "]")
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
        return menu_chapter_video_list[start_index - end_index:end_index]

    # 左开右闭，start_index: 视频编号，从1开始,end_index不包括
    def get_videos(self, start_index, end_index):
        # 访问指定数量视频的页面
        name_list = self.visit_and_get_name_list(start_index, end_index)
        # 获取视频url地址
        course_url_list = self.get_m3u8_url_list(start_index, end_index)
        self.vedio_download(name_list, course_url_list)

    def get_knowledges(self):
        # 点击考点精讲
        self.chrome.find_element_by_class_name("rout-kdjj").click()
        time.sleep(2)
        # self.chrome.refresh()
        # time.sleep(2)
        # 左侧课程导航目录
        EC.presence_of_element_located((By.CLASS_NAME, "content_left"))
        filepath = "knowledge/"
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        menu_list = self.chrome.find_elements_by_xpath("//ul[@class='content_left']//li")
        for menu_index in range(1, len(menu_list) + 1):
            time.sleep(2)
            menu = self.chrome.find_element_by_xpath("//ul[@class='content_left']/li[" + str(menu_index) + "]")
            menu_name = menu.text
            # 点击左侧导航目录
            menu.click()
            EC.presence_of_element_located((By.CLASS_NAME, "content_rig"))
            time.sleep(2)
            chapter_list = self.chrome.find_elements_by_xpath("//ul[@class='content_rig']//li")
            # todo modify
            # for chapter_index in range(1, len(chapter_list) + 1):
            for chapter_index in range(1, 2):
                time.sleep(2)
                content = ""
                # 点击左侧具体课程目录
                current_menu = self.chrome.find_element_by_xpath(
                    "//ul[@class='content_left']/li[" + str(menu_index) + "]")
                current_menu.click()
                time.sleep(2)
                # 点击右侧章节，直接播放当前章节第一个video
                chapter = self.chrome.find_element_by_xpath("//ul[@class='content_rig']/li[" + str(chapter_index) + "]")
                chapter_name = chapter.text
                chapter.click()
                time.sleep(5)
                video_list = self.chrome.find_elements_by_xpath("//div[@class='listPart']//li[@class='clearfix']")
                chapter_mark = True
                for video_index in range(1, len(video_list) + 1):
                    video = self.chrome.find_element_by_xpath("//div[@class='listPart']//li[@class='clearfix'][" + str(video_index) + "]")
                    if len(video_list) > 1:
                        video.click()
                        time.sleep(5)
                    video_name = video.text
                    self.chrome.find_element_by_xpath("//div[@class='tabDiv']/span[2]").click()
                    time.sleep(1)
                    knowledge_text_div_ele = None
                    try:
                        knowledge_text_div_ele = self.chrome.find_element_by_class_name("knowledgeText")
                    except Exception as e:
                        print(e)
                    if knowledge_text_div_ele is not None:
                        knowledge_text = knowledge_text_div_ele.get_attribute('innerHTML')
                        if chapter_mark:
                            content += parse_html(title=menu_name + ":" + chapter_name, title2=video_name, content=knowledge_text, font_size="26px")
                            chapter_mark = False
                        else:
                            content += parse_html(title2=video_name, content=knowledge_text, font_size="26px")
                    self.chrome.find_element_by_xpath("//div[@class='tabDiv']/span[1]").click()
                    time.sleep(1)
                filename = str(menu_index) + "_" + str(chapter_index) + ".pdf"
                save_pdf(content, filepath + filename)
                self.chrome.back()
        merge_pdf(filepath, 'knowledge.pdf')

    def get_exercises(self):
        self.chrome.find_element_by_class_name("routine").click()
        time.sleep(2)
        # chapter_info_pdf = []
        menu_list = self.chrome.find_elements_by_xpath("//ul[@class='chapter_contentleft']//li")
        filepath = "exercise/"
        if not os.path.exists(filepath):
            os.makedirs(filepath)
        #   从第2个开始，第一个是在线考试，非题库
        for menu_index in range(2, len(menu_list) + 1):
            current_menu = self.chrome.find_element_by_xpath("//ul[@class='chapter_contentleft']/li[" + str(menu_index) + "]")
            current_menu.click()
            time.sleep(1)
            current_menu_li = self.chrome.find_element_by_xpath("//ul[@class='chapter_contentleft']/li[" + str(menu_index) + "]/div[2]")
            print("题目:" + current_menu_li.text)
            menu_name = current_menu_li.text
            current_menu_li.click()
            time.sleep(1)
            chapter_list = self.chrome.find_elements_by_xpath("//div[@class='chapter_contentright']//li")
            # todo modify
            # for chapter_index in range(1, len(chapter_list)+1):
            for chapter_index in range(1, 2):
                current_chapter = self.chrome.find_element_by_xpath("//div[@class='chapter_contentright']//li[" + str(chapter_index) + "]//span[@class='pct']")
                chapter_name = current_chapter.text
                print("章节:" + current_chapter.text)
                test_count_text = self.chrome.find_elements_by_class_name("testCount")[chapter_index-1].text
                test_count = int(re.search("/([0-9]+)", test_count_text).group(1))
                count = 1
                if test_count % 50:
                    count = test_count // 50 + 1
                else:
                    count = test_count // 50
                current_chapter.click()
                time.sleep(2)
                # 点击背题模式
                self.chrome.find_element_by_xpath("//div[@class='moulde_p']//li[2]").click()
                time.sleep(1)
                content = ""
                chapter_mark = True
                while count:
                    exercise_list = self.chrome.find_elements_by_xpath("//div[@class='answerCard']//li")
                    for exercise in exercise_list:
                        exercise.click()
                        time.sleep(2)
                        answer_div = self.chrome.find_element_by_id("exambt").get_attribute('innerHTML')
                        # todo bug fix
                        # [\d\D]*表示包括\n的任意多个字符，.*表示不包括换行的任意多个字符,?表示非贪婪模式
                        answer_div1 = re.sub('<div><div class="buttonLeft">[\d\D]*?<div class="buttonRight">[\d\D]*?</div></div>', "", answer_div)
                        if chapter_mark:
                            content += parse_html(title=menu_name + ":" + chapter_name, content=answer_div1)
                            chapter_mark = False
                        else:
                            content += parse_html(content=answer_div)
                    count -= 1
                    if count >= 1:
                        self.chrome.find_element_by_class_name("moveNextUI").click()
                        time.sleep(1)
                filename = str(menu_index) + "_" + str(chapter_index) + ".pdf"
                save_pdf(content, filepath + filename)
                self.chrome.back()
                time.sleep(1)
        merge_pdf(filepath, 'exercise.pdf')

    def start_request(self, url=start_url):
        try:
            # 首页登录
            self.login(url)
            # self.get_videos(start_index=1, end_index=3)
            self.get_knowledges()
            # self.get_exercises()
        finally:
            self.quit()


# string format {{}}显示大括号，占位符替换最内层的{}
def parse_html(title="", title2="", content="", font_size="16px"):
    html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <style type="text/css">
                div{{font-size:{font_size}}}
            </style>
        </head>
        <body>
            <h2>{title}</h2>
            <h3>{title2}</h3>
            <div>
                {content}
            </div>
        </body>
        </html>
        """
    html = html_template.format(title=title, title2=title2, content=content,font_size=font_size)
    return html


def save_pdf(html, filename):
    options = {
        'page-size': 'Letter',
        'margin-top': '0.75in',
        'margin-right': '0.75in',
        'margin-bottom': '0.75in',
        'margin-left': '0.75in',
        'encoding': "UTF-8",
        'custom-header': [
            ('Accept-Encoding', 'gzip')
        ],
        'cookie': [
            ('cookie-name1', 'cookie-value1'),
            ('cookie-name2', 'cookie-value2'),
        ],
        'outline-depth': 10,
    }
    pdfkit.from_string(html, filename, options=options)


def file_compare(file1, file2):
    file1_menu = int(re.search("([0-9]+)_([0-9]+)", file1).group(1))
    file1_chapter = int(re.search("([0-9]+)_([0-9]+)", file1).group(2))
    file2_menu = int(re.search("([0-9]+)_([0-9]+)", file2).group(1))
    file2_chapter = int(re.search("([0-9]+)_([0-9]+)", file2).group(2))
    if file1_menu > file2_menu:
        return 1
    elif file1_menu == file2_menu:
        if file1_chapter > file2_chapter:
            return 1
        elif file1_chapter == file2_chapter:
            return 0
        else:
            return -1
    else:
        return -1


# todo 页码
def merge_pdf(filepath, outfn):
    """
    合并pdf
    :param infnList: 要合并的PDF文件路径
    :param outfn: 保存的PDF文件名
    :return: None
    """
    pdf_output = PdfFileWriter()
    key = functools.cmp_to_key(file_compare)
    pdf_list = os.listdir(filepath)
    pdf_list.sort(key=key)
    infn_list = [filepath + x for x in pdf_list]
    for pdf in infn_list:
        pdf_input = PdfFileReader(open(pdf, 'rb'))
        # 获取当前pdf共用多少页
        page_count = pdf_input.getNumPages()
        for i in range(page_count):
            pdf_output.addPage(pdf_input.getPage(i))
    # 合并
    pdf_output.write(open(outfn, 'wb'))

if __name__ == "__main__":
    server = Server(r'D:\Programs\browsermob-proxy-2.1.4-bin\browsermob-proxy-2.1.4\bin\browsermob-proxy.bat')
    spider = ytEduCrawler()
    spider.start_request()