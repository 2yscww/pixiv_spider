import time
import random
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
                    if os.path.exists(save_path):
                        print(f"{img_name} 已存在")
                        return

                    with open(save_path, "wb") as img_file:
                        img_file.write(img_response.content)

                    print(f"{img_name} 下载完成")
                    return

                elif img_response.status_code == 429:
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

            try:
                # 作品名称
                self.illust_text = self.driver.find_element(
                    By.XPATH,
                    '//*[@id="root"]/div[2]/div/div[3]/div/div/div[1]/main/section/div[1]/div/figcaption/div/div/h1',
                ).text

            except NoSuchElementException:
                self.illust_text = "无题"

            if self.illust_text == "无题":
                try:
                    illust_date_element = WebDriverWait(self.driver, 10).until(
                        EC.visibility_of_element_located((
                            By.XPATH,
                            '//*[@id="root"]/div[2]/div/div[3]/div/div/div[1]/main/section/div[1]/div/figcaption/div/div/div[3]/time',
                        ))
                    )


                    illust_date = illust_date_element.text

                    match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", illust_date)
                    if match:
                        year, month, day = match.groups()
                        # 格式化成 'YYYY-MM-DD' 的格式
                        date_str = f"{year}-{int(month):02d}-{int(day):02d}"

                        self.illust_text = f"无题-{date_str}"
                except Exception as e:
                    print(f"无题作品发生了异常: {e}")


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
                print(f"页面多图标签发生异常: {e}")

            if page_element:
                print("确认为多图")
                
                self.flag = True
                self.get_id = illustsID
                
                image_info = page_element.text # 页面多图标签的文字
                self.image_num = int(image_info.split('/')[-1])  # 以斜杠为分割符
            else:
                print("确认为单图")
                self.get_id = illustsID
                self.image_num = 1
                
            self.getOriginalUrl()

    def getOriginalUrl(self):
            
            url = f'https://www.pixiv.net/ajax/illust/{self.get_id}'
            
            response = self.session.get(url)
            if response.status_code == 200:

                self.illust_num = 1
                
                data = response.json()
                original_url = data.get("body",{}).get("urls",{}).get("original")
                    
                url_prefix , url_suffix = original_url.split('_p')
                    
                base_name , ex_name = os.path.splitext(url_suffix)
                    
                for i in range(self.image_num):
                    img_url = f'{url_prefix}_p{i}{ex_name}'
                    
                    download_img = downloadImg(
                    self.save_dir, self.illust_text, self.illust_num, img_url
                    )

                    download_img.download_illust()

                    self.illust_num += 1
                
                    
            else:
                print(f"原图url请求失败，状态码: {response.status_code}")


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
            # 'Referer': 'https://www.pixiv.net/',
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
        
        input_field = self.driver.find_elements(
            By.CSS_SELECTOR,
            'input.sc-bn9ph6-6.cYyjQe',
        )
        
        input_email = input_field[0]
        
        input_password = input_field[1]
        
        for char in self.email:
            time.sleep(random.uniform(0.1, 0.5))
            input_email.send_keys(char)

        for passwd_char in self.password:
            time.sleep(random.uniform(0.1, 0.5))
            input_password.send_keys(passwd_char)

        time.sleep(random.uniform(1, 3))

        self.driver.find_element(By.XPATH,'//*[@id="app-mount-point"]/div/div/div[4]/div[1]/form/button[1]').click()

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
        # self.proxy = proxy
        self.user_agent = user_agent

    def setup_WebDriver(self):
        chrome_options = Options()
        # chrome_options.add_argument(f"--proxy-server={self.proxy}")

        chrome_options.add_argument(
            "--allow-running-insecure-content"
        )  # 允许https中加载http

        chrome_options.add_argument("--ignore-certificate-errors")  # 忽略 SSL 证书错误

        chrome_options.add_experimental_option(
            "excludeSwitches", ["enable-automation"]
        )  # 设置绕过selenium 检测

        chrome_options.add_argument("--ignore-ssl-errors")  # 忽略SSL错误
        # chrome_options.add_argument('--allow-insecure-localhost')  # 允许访问不安全的 localhost（自签名证书）
        # chrome_options.add_argument("--headless")  无头模式，即不显示浏览器
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


    authorID = input("输入作者的PID: ")

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

