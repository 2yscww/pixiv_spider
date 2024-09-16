import json
import time
import requests
import os
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException

# 预定义不允许的字符
INVALID_CHARS = r'[<>:"/\\|?*]'


# 当前文件的绝对路径
base_file = os.path.abspath(__file__)
# 获取文件的文件夹信息
base_dir = os.path.dirname(base_file)

class downloadImg:
    def __init__(self, save_dir, illust_name, illust_num, illust_url):
        self.save_dir = save_dir
        self.illust_name = illust_name
        self.illust_num = illust_num
        self.illust_url = illust_url

    def download_illust(self):

        _, illust_ex = os.path.splitext(self.illust_url)

        img_name = f"{self.illust_name}-{self.illust_num}{illust_ex}"

        save_path = os.path.join(self.save_dir, img_name)

        # 最大重试次数
        max_retries = 5

        # 重试次数
        retry_count = 0

        while retry_count < max_retries:
            try:
                img_response = session.get(self.illust_url)

                if img_response.status_code == 200:
                    with open(save_path, "wb") as img_file:
                        img_file.write(img_response.content)

                    print(f"{img_name} 下载完成")
                    return

                elif img_response == 429:
                    retry_count += 1

                    wait_time = 5 * retry_count  # 等待时间

                    print(
                        f"{img_name} 下载出错，状态码为 {img_response.status_code} 正在重试 {retry_count}/{max_retries} 等待 {wait_time} 秒"
                    )

                    time.sleep(wait_time)

                else:
                    print(f"{img_name} 下载出错，状态码为 {img_response.status_code}")
                    return
            except Exception as e:
                print(f"{img_name} 下载出错: {e}")


class createDir:
    def __init__(self, author_name=None, illust_name=None):
        self.author_name = self.clean_folder_name(author_name)
        self.illust_name = self.clean_folder_name(illust_name)
        self.result_dir_path = os.path.join(base_dir, "pixiv_result")
        self.author_dir_path = os.path.join(self.result_dir_path, self.author_name)
        self.illust_dir_path = None

    # 创建result文件夹
    def createResultDir(self):
        if os.path.exists(self.result_dir_path):
            print(f"{self.result_dir_path}已存在")
        else:
            os.makedirs(self.result_dir_path)

            print(f"{self.result_dir_path}已创建")

    # 创建作者文件夹
    def createAuthorDir(self):
        # 确保 result_dir_path 不为 None
        if not self.result_dir_path:
            print("请先创建 result 目录")
            return

        if os.path.exists(self.author_dir_path):
            print(f"{self.author_dir_path} 已存在")
        else:
            os.makedirs(self.author_dir_path)
            print(f"{self.author_dir_path} 已创建")

    #  创建作品文件夹
    def createIllustDir(self):


        # 确保 author_dir_path 不为 None
        if not self.author_dir_path:
            print("请先创建 author 目录")
            return

        self.illust_dir_path = os.path.join(self.author_dir_path, self.illust_name)

        if os.path.exists(self.illust_dir_path):
            print(f"{self.illust_dir_path} 已存在")
        else:
            os.makedirs(self.illust_dir_path)
            print(f"{self.illust_dir_path} 已创建")

    def return_save_path(self):
        return self.illust_dir_path
    
    def return_illust_name(self):
        return self.illust_name

    # 清理文件夹名称 去掉windows不允许的文件夹字符
    def clean_folder_name(self, folder_name):
        return re.sub(INVALID_CHARS, "_", folder_name)


class getOriginal:
    def __init__(self, illusts_id, session, driver):
        self.illusts_id = illusts_id
        self.session = session
        self.driver = driver
        self.image_num = None
        self.flag = False
        self.get_id = None
        self.author_text = None
        self.illust_text = None
        self.author_dir_flag = False
        self.save_dir = None
        self.illust_num = 1

    def confirmImgNum(self):
        for illustsID in self.illusts_id:
            url = f"https://www.pixiv.net/artworks/{illustsID}"

            self.driver.get(url)

            # 作者名称
            self.author_text = self.driver.find_element(
                By.XPATH,
                '//*[@id="root"]/div[2]/div/div[3]/div/div/div[1]/aside/section[1]/h2/div/div/a/div',
            ).text

            # 作品名称
            self.illust_text = self.driver.find_element(
                By.XPATH,
                '//*[@id="root"]/div[2]/div/div[3]/div/div/div[1]/main/section/div[1]/div/figcaption/div/div/h1',
            ).text

            new_dir = createDir(
                author_name=self.author_text, illust_name=self.illust_text
            )
            
            new_dir.createResultDir()
            
            self.illust_text = new_dir.return_illust_name()

            if self.author_dir_flag:
                print("")
            else:
                new_dir.createAuthorDir()
                self.author_dir_flag = True


            new_dir.createIllustDir()

            self.save_dir = new_dir.return_save_path()

            print("")

            print(self.illust_text)

            print("")

            try:
                self.driver.implicitly_wait(5)

                page_element = self.driver.find_element(
                    By.XPATH,
                    '//*[@id="root"]/div[2]/div/div[3]/div/div/div[1]/main/section/div[1]/div/figure/div/div[1]/div/div/div/div/div/span',
                )


            except NoSuchElementException:
                page_element = False

            except Exception as e:
                print(f"发生异常:{e}")

            if page_element:
                print("确认为多图")
                self.flag = True
            else:
                print("确认为单图")

            self.getOriginalUrl()


    def getOriginalUrl(self):

        # 确认为多图
        if self.flag:

            # 等待 "查看全部" 按钮加载，并点击它
            try:
                view_all_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            '//*[@id="root"]/div[2]/div/div[3]/div/div/div[1]/main/section/div[1]/div/div[4]/div/div[2]/button/div[2]',
                        )
                    )
                )
                view_all_button.click()

            except Exception as e:
                print(f"发生异常: {e}")


            # 应对懒加载，下拉页面

            self.driver.execute_script("window.scrollTo(0,10000);")

            time.sleep(1)

            self.driver.execute_script("window.scrollTo(0,10000);")

            time.sleep(1)

            self.driver.execute_script("window.scrollTo(0,10000);")

            try:
                a_tags = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "a.sc-1qpw8k9-3.ilIMcK")
                    )
                )

            except Exception as e:
                print(f"获取图片出现异常: {e}")


            self.illust_num = 1
            
            # 提取每个 <a> 标签的 href 属性
            for a_tag in a_tags:
                img_url = a_tag.get_attribute("href")
                
                download_img = downloadImg(self.save_dir,self.illust_text,self.illust_num,img_url)
                
                download_img.download_illust()
                
                self.illust_num += 1


        else:

            try:
                a_tags = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "a.sc-1qpw8k9-3.ilIMcK")
                    )
                )

            except Exception as e:
                print(f"获取图片出现异常: {e}")

            # 提取每个 <a> 标签的 href 属性
            for a_tag in a_tags:
                img_url = a_tag.get_attribute("href")
                
                download_img = downloadImg(self.save_dir,self.illust_text,self.illust_num,img_url)
                
                download_img.download_illust()

                self.illust_num += 1

        time.sleep(5)

class getAuthorProfile:
    def __init__(self, driver, authorID):
        self.driver = driver
        self.authorID = authorID

    def get_profile(self):
        url = f"https://www.pixiv.net/ajax/user/{self.authorID}/profile/all"

        # 获取登录后的cookies
        cookies = self.driver.get_cookies()
        session = requests.Session()

        # 获取Selenium中的User-Agent
        user_agent = self.driver.execute_script("return navigator.userAgent;")

        # 设置User-Agent和其他必要的头信息
        headers = {
            "User-Agent": user_agent,
            "Referer": "https://www.pixiv.net/tags/%E7%BA%B1%E9%9B%BE",
        }
        session.headers.update(headers)

        for cookie in cookies:
            session.cookies.set(cookie["name"], cookie["value"])

        # 发送请求获取JSON数据

        response = session.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            illusts = data.get("body", {}).get("illusts")

            illusts_id = list(illusts.keys())

            print("作品信息获取成功")

        else:
            print(f"作品信息请求失败，状态码: {response.status_code}")

        return illusts_id, session

class autoLogin:
    def __init__(self, driver, email, password):
        self.driver = driver
        self.email = email
        self.password = password

    def auto_login(self):
        self.driver.get("https://accounts.pixiv.net/login")

        self.driver.implicitly_wait(10)

        self.driver.find_element(
            By.XPATH,
            '//*[@id="app-mount-point"]/div/div/div[4]/div[1]/div[2]/div/div/div/form/fieldset[1]/label/input',
        ).send_keys(self.email)

        self.driver.find_element(
            By.XPATH,
            '//*[@id="app-mount-point"]/div/div/div[4]/div[1]/div[2]/div/div/div/form/fieldset[2]/label/input',
        ).send_keys(self.password)

        self.driver.find_element(
            By.XPATH,
            '//*[@id="app-mount-point"]/div/div/div[4]/div[1]/div[2]/div/div/div/form/button',
        ).click()

        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        '//*[@id="root"]/div[2]/div/div[2]/div[1]/div[1]/div/div[3]/div[1]/div[5]/div/button/div',
                    )
                )  # 找到用户的头像
            )

            print("登录成功")
        except TimeoutException:
            print("登录超时，可能登录失败")

        return self.driver

class initializeConfig:
    def __init__(self, user_agent):
        self.user_agent = user_agent

    def setup_WebDriver(self):
        chrome_options = Options()
        chrome_options.add_argument(
            "--allow-running-insecure-content"
        )  # 允许https中加载http

        chrome_options.add_argument("--ignore-certificate-errors")  # 忽略 SSL 证书错误

        chrome_options.add_experimental_option(
            "excludeSwitches", ["enable-automation"]
        )  # 设置绕过selenium 检测
        chrome_options.add_argument("--ignore-ssl-errors")  # 忽略SSL错误
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-dev-shm-usage")  # 禁用共享内存

        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-setuid-sandbox")

        chrome_options.add_argument(f"user-agent={self.user_agent}")  # 设置UA

        return webdriver.Chrome(options=chrome_options)


if __name__ == "__main__":
    # 记录程序开始时间
    start_time = time.time()

    email = "SET YOUR EMAIL"
    password = "SET YOUR PASSWD"

    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"

    authorID = "39750820"  # 测试作者2

    init_config = initializeConfig(user_agent)

    driver = init_config.setup_WebDriver()

    login = autoLogin(driver, email, password)
    
    login.auto_login()

    profile = getAuthorProfile(driver, authorID)

    author_illusts, session = profile.get_profile()

    original = getOriginal(author_illusts, session, driver)

    original.confirmImgNum()

    # 记录程序结束时间
    end_time = time.time()

    # 计算程序运行时间
    elapsed_time = end_time - start_time

    # 打印程序运行时间
    print(f"程序运行时间: {elapsed_time:.2f} 秒")
