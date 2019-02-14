# -*- coding:UTF-8 -*-
import time
import re
import MySQLdb
# import mysqli
from datetime import date, timedelta
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options

TB_LOGIN_URL = 'https://login.taobao.com/member/login.jhtml'
TB_LOGIN_URL = 'https://login.taobao.com/member/login.jhtml?sub=true&style=miniall&from=subway&full_redirect=true&newMini2=true&tpl_redirect_url=//subway.simba.taobao.com/entry/login.htm'
CHROME_DRIVER = '/usr/local/bin/chromedriver'

class SessionException(Exception):
    """
    会话异常类
    """
    def __init__(self, message):
        super().__init__(self)
        self.message = message

    def __str__(self):
        return self.message


class Crawler:

    def __init__(self):
        self.browser = None
        self.yesterday_date = None
        self.today_date = None

    def start(self, username, password):
        print("初始化日期")
        self.__init_date()
        print("初始化浏览器")
        self.__init_browser()
        print("切换至密码输入框")
        self.__switch_to_password_mode()
        time.sleep(0.5)
        print("输入用户名")
        self.__write_username(username)
        time.sleep(2.5)
        print("输入密码")
        self.__write_password(password)
        time.sleep(3.5)
        print("程序模拟解锁")
        if self.__lock_exist():
            self.__unlock()
        print("开始发起登录请求")
        self.__submit()
        time.sleep(4.5)
        # 登录成功，直接请求页面
        print("登录成功，跳转至目标页面")
        # self.__navigate_to_target_page()
        # time.sleep(6.5)
        # print("解析页面文本")
        # crawler_list = self.__parse_page_content();
        #
        # # 连接数据库并保存数据
        # print("保存数据到mysql数据库")
        # self.__save_list_to_db(crawler_list)

    def __switch_to_password_mode(self):
        """
        切换到密码模式
        :return:
        """
        if self.browser.find_element_by_id('J_QRCodeLogin').is_displayed():
            self.browser.find_element_by_id('J_Quick2Static').click()

    def __write_username(self, username):
        """
        输入账号
        :param username:
        :return:
        """
        username_input_element = self.browser.find_element_by_id('TPL_username_1')
        username_input_element.clear()
        username_input_element.send_keys(username)

    def __write_password(self, password):
        """
        输入密码
        :param password:
        :return:
        """
        password_input_element = self.browser.find_element_by_id("TPL_password_1")
        password_input_element.clear()
        password_input_element.send_keys(password)

    def __lock_exist(self):
        """
        判断是否存在滑动验证
        :return:
        """
        return self.__is_element_exist('#nc_1_wrapper') and self.browser.find_element_by_id(
            'nc_1_wrapper').is_displayed()

    def __unlock(self):
        """
        执行滑动解锁
        :return:
        """
        bar_element = self.browser.find_element_by_id('nc_1_n1z')
        ActionChains(self.browser).drag_and_drop_by_offset(bar_element, 800, 0).perform()
        time.sleep(1.5)
        self.browser.get_screenshot_as_file('error.png')
        if self.__is_element_exist('.errloading > span'):
            error_message_element = self.browser.find_element_by_css_selector('.errloading > span')
            error_message = error_message_element.text
            self.browser.execute_script('noCaptcha.reset(1)')
            raise SessionException('滑动验证失败, message = ' + error_message)

    def __submit(self):
        """
        提交登录
        :return:
        """
        self.browser.find_element_by_id('J_SubmitStatic').click()
        time.sleep(0.5)
        if self.__is_element_exist("#J_Message"):
            error_message_element = self.browser.find_element_by_css_selector('#J_Message > p')
            error_message = error_message_element.text
            raise SessionException('登录出错, message = ' + error_message)

    def __navigate_to_target_page(self):
        self.browser.get("https://subway.simba.taobao.com/#!/report/bpreport/index?start=" + self.yesterday_date +"&end=" + self.yesterday_date +"&tabId=2&page=1&rows=200");

    # 解析网页数据
    def __parse_page_content(self):
        table_container_div = self.browser.find_element_by_class_name("table-container")
        table_element = table_container_div.find_elements_by_tag_name("table")
        table_tr_list = table_element[1].find_elements_by_tag_name("tr")

        result_data = []

        for tr in table_tr_list:
            item_columns = tr.find_elements_by_tag_name("td")
            goods_column = item_columns[1]
            try:
                title_href = goods_column.find_element_by_class_name("title")
            except:
                continue

            # 商品名称 及链接
            goods_name = title_href.text
            goods_link_url = goods_column.find_element_by_link_text("进入宝贝").get_attribute("href")
            goods_item_id = re.search("detail\.tmall\.com/item\.htm\?id=([0-9a-zA-Z_]+)$", goods_link_url, ).group(1)

            # 成交金额
            turn_over_str = item_columns[5].text.replace("￥".decode("utf-8"), "").replace(",", "")
            if turn_over_str == '-':
                turn_over_str = '0'
            turn_over = float(turn_over_str)

            # 花费
            cost_money_str = item_columns[6].text.replace("￥".decode("utf-8"), "").replace(",", "")
            cost_money = float(cost_money_str)

            item_exist = False
            for item_info in result_data:
                if item_info["item_id"] == goods_item_id:
                    item_exist = True
                    item_info["turn_over"] = item_info["turn_over"] + turn_over
                    item_info["cost_money"] = item_info["cost_money"] + cost_money
                    break
            if not item_exist:
                result_data.append({"item_id": goods_item_id, "goods_name": goods_name, "link_url": goods_link_url,
                                    "turn_over": turn_over, "cost_money": cost_money})

        return result_data

    def __save_list_to_db(self, crawler_list):

        conn = MySQLdb.connect(
            host='',
            port=8888,
            user='',
            passwd='',
            db='',
            use_unicode=True,
            charset='utf8'
        )
        cur = conn.cursor()

        for crawler_item in crawler_list:
            # create_time = self.today_date + " 00:00:00"
            create_time = "2019-02-09" + " 00:00:00"
            crawler_date = self.yesterday_date + " 00:00:00"
            item_id = crawler_item["item_id"]
            goods_name = crawler_item["goods_name"]
            link_url = crawler_item["link_url"]
            turn_over = crawler_item["turn_over"]
            cost_money = crawler_item["cost_money"]
            mysql_script = "INSERT INTO taobao_zhitongche(crawler_date, item_id, goods_name, link_url, create_time, turn_over, cost_money) " \
                           "SELECT '%s', '%s', '%s', '%s', '%s', %s, %s FROM dual " \
                           "WHERE not exists (select * from taobao_zhitongche where crawler_date='%s' and item_id='%s')" % \
                           (crawler_date, item_id, goods_name, link_url, create_time, turn_over, cost_money, crawler_date, item_id)
            print(mysql_script)
            cur.execute(mysql_script)

        # 数据保存结束
        cur.close()
        conn.commit()
        conn.close()

        print("\n")

    def __init_date(self):
        date_offset = 0
        self.today_date = (date.today() + timedelta(days=-date_offset)).strftime("%Y-%m-%d")
        self.yesterday_date = (date.today() + timedelta(days=-date_offset-1)).strftime("%Y-%m-%d")

    def __init_browser(self):
        """
        初始化selenium浏览器
        :return:
        """
        options = Options()
        # options.add_argument("--headless")
        prefs = {"profile.managed_default_content_settings.images": 1}
        options.add_experimental_option("prefs", prefs)
        options.add_argument('--proxy-server=http://127.0.0.1:9000')
        options.add_argument('disable-infobars')
        options.add_argument('--no-sandbox')
        # options.add_argument('--user-data-dir=' + r'C:/Users/NALA/AppData/Local/Google/Chrome/User Data')


        self.browser = webdriver.Chrome(executable_path=CHROME_DRIVER, options=options)
        self.browser.implicitly_wait(3)
        self.browser.maximize_window()
        self.browser.get(TB_LOGIN_URL)

    def __is_element_exist(self, selector):
        """
        检查是否存在指定元素
        :param selector:
        :return:
        """
        try:
            self.browser.find_element_by_css_selector(selector)
            return True
        except NoSuchElementException:
            return False



#执行命令行
Crawler().start('', '')
