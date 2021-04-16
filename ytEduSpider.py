from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium import webdriver
from browsermobproxy import Server
import time
from selenium.webdriver.chrome.options import Options


class ytEduCrawler:

    domain = "ksbao.com"
    start_url = "https://wide.ksbao.com/login"

    def __init__(self):
        self.server = Server(r'D:\Programs\browsermob-proxy-2.1.4-bin\browsermob-proxy-2.1.4\bin\browsermob-proxy.bat')
        self.server.start()
        self.proxy = self.server.create_proxy()
        chrome_options = Options()
        chrome_options.add_argument('--proxy-server={0}'.format(self.proxy.proxy))
        chrome_options.add_argument('--incognito')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--disable-gpu')
        self.chrome = webdriver.Chrome(chrome_options=chrome_options)

    def quit(self):
        self.server.stop()
        self.chrome.quit()

    def test(self):
        self.proxy.new_har("hupu.com")
        # self.proxy.new_har("hupu.com",options={'captureHeaders': True, 'captureContent': True})
        self.chrome.get("http://nba.hupu.com")
        # time.sleep(5)
        result = self.proxy.har
        for entry in result['log']['entries']:
            _url = entry['request']['url']
            print(_url)
        self.server.stop()


    def start_request(self, url=start_url,domain=domain):
        self.chrome.get(url)
        print("============================")
        # 首页登录
        self.chrome.get(url)
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
        self.proxy.new_har(domain)
        # 刷新页面，不用点击弹框关闭
        # self.chrome.refresh()
        # time.sleep(2)
        # 点击考点精讲
        self.chrome.find_element_by_class_name("rout-kdjj").click()
        time.sleep(2)
        self.chrome.refresh()
        time.sleep(2)
        # 左侧课程导航，点击
        EC.presence_of_element_located((By.CLASS_NAME, "content_left"))
        course_list = self.chrome.find_elements_by_xpath("//ul[@class='content_left']//li")
        course_url_list = []
        course_chapter_video_list = []
        for course_index in range(1, len(course_list)+1):
            time.sleep(2)
            course = self.chrome.find_element_by_xpath("//ul[@class='content_left']/li["+str(course_index)+"]")
            course_name = course.text
            course.click()
            EC.presence_of_element_located((By.CLASS_NAME, "content_rig"))
            time.sleep(2)
            chapter_list = self.chrome.find_elements_by_xpath("//ul[@class='content_rig']//li")
            # 点击播放视频
            for chapter_index in range(1, len(chapter_list)+1):
                time.sleep(2)
                current_course = self.chrome.find_element_by_xpath("//ul[@class='content_left']/li[" + str(course_index) + "]")
                current_course.click()
                time.sleep(2)
                chapter = self.chrome.find_element_by_xpath("//ul[@class='content_rig']/li["+str(chapter_index)+"]")
                chapter_name = chapter.text
                chapter.click()
                time.sleep(5)
                # video_list = self.chrome.find_elements_by_xpath("//li[@class='clearfix']")
                video_list = self.chrome.find_elements_by_xpath("//div[@class='listPart']//li[@class='clearfix']")
                if len(video_list) >= 2:
                    for video_index in range(2, len(video_list)+1):
                        video = self.chrome.find_element_by_xpath("//div[@class='listPart']//li[@class='clearfix']["+str(video_index)+"]")
                        video_name = video.text
                        course_chapter_video_list.append(course_name+"_"+chapter_name+"_"+video_name)
                        video.click()
                        time.sleep(5)
                self.chrome.back()
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

        request_logs = self.proxy.har
        for entry in request_logs['log']['entries']:
            m3u8_url = entry['request']['url']
            if "m3u8" in m3u8_url:
                print(m3u8_url)
                course_url_list.append(m3u8_url)
        with open("info.txt","w") as f:
            for name, _url in zip(course_chapter_video_list, course_url_list):
                # for _url in course_url_list:
                f.write(name + '\n')
                f.write(_url + '\n')
        originResp = self.chrome.page_source
        return originResp

if __name__=="__main__":
    spider = ytEduCrawler()
    spider.start_request()
    spider.quit()