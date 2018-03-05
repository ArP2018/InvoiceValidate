# encoding: utf-8
import sys
import logging
import time
import traceback
import urllib.request
from selenium import webdriver
from queue import Queue
from ml_captha import crack_captha, send_error, CjyConectionError
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from sourceparser import parse_source_code, check_content
from udf_exceptions import BadRefreshException, CapthaNotRefreshException, CjyApiError, CjyDecodeException, \
    CjyRecognizeException

URL = 'https://inv-veri.chinatax.gov.cn/'


class InvoiceVerify(object):
    def __init__(self):
        self.browser = webdriver.Ie()
        self.browser.maximize_window()
        self.browser.execute_script("document.body.style.zoom='100%';")
        # 初始化html_code 用来保存正常发票的页面源码
        self.html_code = ''
        self.checked_captha_url = ''

        self.shibie_count = 0
        self.normal_fp = 0
        self.progress_count = 0

    def open_homepage(self):
        self.browser.get(URL)

        if 'overridelink' in self.browser.page_source:
            close_js = 'document.getElementById("overridelink").click();'
            self.browser.execute_script(close_js)

        try:
            WebDriverWait(self.browser, 30).until(lambda _driver: _driver.find_element_by_id('fpdm').is_displayed())
        except TimeoutException:
            print('page load failed')
            logging.info('page load failed')
            sys.exit(0)

    # 记录单张发票查验结果，写到临时文件
    def log_finished_invoice(self, invoice, validate_result):
        with open('finished_invoice_temp', 'a', encoding='utf-8') as finished_file:
            finished_file.write(
                '%s|%s|%s|%s|%s|%s|%s\n' % (invoice['invoice_code'],
                                            invoice['invoice_num'],
                                            invoice['invoice_date'],
                                            invoice['invoice_kjje_tax'],
                                            invoice['invoice_kjje'],
                                            invoice['invoice_check_code'],
                                            validate_result)
            )

    def download_captha(self):
        '''
        下载验证码
        :return:
        '''
        captha_url = self.browser.find_element(By.ID, 'yzm_img').get_attribute('src')
        try:
            urllib.request.urlretrieve(captha_url, 'temp/captha.png')
            return self.browser.find_element_by_id('yzminfo').find_element(By.TAG_NAME, 'font').text
        except IOError:
            self.download_captha()
        except NoSuchElementException:
            return None

    def input_invoice_info(self, invoice):
        # 发票代码
        fpdm_element = self.browser.find_element_by_id('fpdm')
        fpdm_element.clear()
        fpdm_element.send_keys(str(invoice['invoice_code']))

        # 发票号码
        fphm_element = self.browser.find_element_by_id('fphm')
        fphm_element.clear()
        fphm_element.send_keys(str(invoice['invoice_num']))

        # 开票日期
        kprq_element = self.browser.find_element_by_id('kprq')
        kprq_element.clear()
        kprq_element.send_keys(invoice['invoice_date'])

        # 开具金额（不含税）/校验码
        kjje_element = self.browser.find_element_by_id('kjje')
        kjje_element.clear()
        context = self.browser.find_element_by_id('context').text
        if '校验码' in context:
            kjje_element.send_keys(invoice['invoice_check_code'][-6:])
        elif '开具金额' in context:
            kjje_element.send_keys(str(invoice['invoice_kjje']))

    def validate_basic_info(self):
        # 输入信息有误的情况，界面会显示错误信息
        fpdmjy = self.browser.find_element_by_id('fpdmjy').text.strip()
        if fpdmjy:
            return fpdmjy

        fphmjy = self.browser.find_element_by_id('fphmjy').text.strip()
        if fphmjy:
            return fphmjy

        kprqjy = self.browser.find_element_by_id('kprqjy').text.strip()
        if kprqjy:
            return kprqjy

        kjjejy = self.browser.find_element_by_id('kjjejy').text.strip()
        if kjjejy:
            return kjjejy

        return None

    def display_captha(self):
        '''
        判断验证码是否刷新出来，如果没有则点击刷新
        :return:
        '''
        while True:
            # 验证码显示正常，且验证码属于按颜色识别的类型，返回
            if 'images/code.png' not in self.browser.find_element(By.ID, 'yzm_img').get_attribute('src'):
                return

            self.browser.find_element_by_id('imgarea').find_element_by_tag_name('a').click()
            # 下面这个不好使
            # self.browser.execute_script('document.getElementById("imgarea").getElementsByTagName("a")[0].click()')
            # time.sleep(0.8)
            self.is_popup_displayed()

    def is_popup_displayed(self):
        '''
        判断是否弹出刷新频繁的提示框，如果出现，关闭后睡眠60s，没有则正常返回
        :return:
        '''
        time.sleep(0.5)
        try:
            # print('判断是否弹出刷新频繁的提示框')
            self.browser.find_element_by_id('popup_ok')
            # print(self.browser.find_element_by_id('popup_message').text)
            # logging.info(self.browser.find_element_by_id('popup_message').text)
            logging.info('popup message')
            self.browser.execute_script('document.getElementById("popup_ok").click();')
            # logging.error('刷新验证码过于频繁！')
            # time.sleep(60)

            # 抛出异常
            raise BadRefreshException
        except NoSuchElementException:
            return

    def refresh_captha(self, pre_url):
        '''
        刷新验证码，重新获得的url与传入的url不一致则认为刷新成功
        :param pre_url: 验证码刷新前的url
        :return:
        '''
        s_time = time.time()
        while True:
            e_time = time.time()

            if e_time - s_time >= 600:
                raise CapthaNotRefreshException

            self.is_popup_displayed()
            self.browser.find_element_by_id('imgarea').find_element_by_tag_name('a').click()
            # self.browser.execute_script('document.getElementById("imgarea").getElementsByTagName("a")[0].click()')
            # time.sleep(0.8)
            logging.info('refresh captha ...')
            # print('refresh captha ...')

            now_url = self.browser.find_element(By.ID, 'yzm_img').get_attribute('src')

            if pre_url == now_url:
                continue
            else:
                return

    # 处理点击查验按钮后的各种情况
    def verify_check_result_displayed(self):
        '''
        判断点击查验按钮这一操作是否正常执行，如果页面没有任何返回结果，则返回0
        :return:
        0：页面没有返回任何结果
        1: 弹出提示框（验证码失败或者超过次数）
        2: 查验结果不一致  'cyjg'
        3: 查验结果一致  'fpcc_zp'
        '''
        result_map = {
            'popup_container': 1,
            'cyjg': 2,
            'cycs': 3
        }
        expected_result = 0
        try:
            # print('检查查验结果')
            WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.XPATH,
                                                "//*[@id='popup_container' or @id='cyjg' or @id='cycs']")
                                               ))
        except TimeoutException:
            # print('查验结果为空')
            return expected_result

        for k in result_map.keys():
            try:
                el = self.browser.find_element_by_id(k)
                if el.is_displayed():
                    expected_result = result_map.get(k)
                    break
            except NoSuchElementException:
                pass

        return expected_result

    def input_captha_and_check(self, text):
        '''
        输入识别结果并点击查验按钮
        :param text: 验证码识别结果
        :return:
        '''
        yzm_element = self.browser.find_element_by_id('yzm')
        yzm_element.clear()
        yzm_element.send_keys(text)

        # 输入验证结果后需要判断查验按钮是否可以点击
        if self.browser.find_element_by_id('checkfp').is_displayed():
            self.browser.execute_script('document.getElementById("checkfp").click();')
            time.sleep(0.5)
            return
        else:
            self.input_captha_and_check(text)

    # 关闭消息提示框
    # 关闭发票查验结果窗口
    # 关闭货物明细清单
    def close_html_element(self, element_id):
        # print('准备执行关闭%s操作' % element_id)
        self.browser.execute_script('document.getElementById("%s").click();' % element_id)
        # print('关闭%s操作执行完毕' % element_id)
        time.sleep(0.5)
        try:
            # print('close popup window: %s' % element_id)
            logging.info('close popup window: %s' % element_id)
            WebDriverWait(self.browser, 3).until(EC.invisibility_of_element_located((By.ID, element_id)))
        except TimeoutException:
            # print('close operation failed: %s' % element_id)
            logging.error('close operation failed: %s' % element_id)
            self.close_html_element(element_id)

    # 打开货物明细清单
    def open_hwmx_list(self):
        self.browser.execute_script('document.getElementById("showmx").click();')
        time.sleep(0.5)

        try:
            WebDriverWait(self.browser, 5).until(EC.visibility_of_element_located((By.ID, 'hwmxqd')))
            return
        except TimeoutException:
            self.open_hwmx_list()

    def check_invoice(self, text):
        '''
        处理点击查验按钮后的返回结果
        :param text: 验证码识别结果
        :return:
        作废： 发票作废
        一致： 检查结果一致
        cyjg: 发票不一致
        False: 验证码错误
        -1: 查验结果界面发票内容未加载成功
        '''
        if text:
            self.input_captha_and_check(text)
        else:
            return False

        displayed = self.verify_check_result_displayed()

        # print(displayed)
        # 点击查验按钮页面没反应
        if displayed == 0:
            return '查验失败'
        # 点击查验按钮页面弹出消息提示框
        # 1. 超过当日查验次数
        # 2. 验证码识别错误
        elif displayed == 1:
            popup_message = self.browser.find_element_by_id('popup_message').text
            # logging.debug(popup_message)
            # print(popup_message)
            logging.info('beyond check times limit')
            self.close_html_element('popup_ok')

            # 超过每日查验次数限制
            if '限制' in popup_message or '当日' in popup_message:
                return popup_message
            # 验证码识别错误后刷新并重新识别
            else:
                return False
        # 验证不一致的结果
        elif displayed == 2:
            cyjg = self.browser.find_element_by_id('cyjg').text
            self.close_html_element('closebt')
            return cyjg
        # 一致的情况
        # 1. 作废
        # 2. 正常
        elif displayed == 3:
            self.html_code = self.browser.page_source

            # 先判断是否有货物明细清单
            if '查看货物明细清单' in self.browser.page_source:
                self.open_hwmx_list()
                self.html_code = self.browser.page_source
                self.close_html_element('mxclose')

            is_zf_displayed = self.browser.find_element_by_id('icon_zf').is_displayed()
            self.close_html_element('closebt')

            # 检查发票内容是否已经成功加载
            if not check_content(self.html_code):
                self.html_code = ''
                return -1

            if is_zf_displayed:
                return '作废'
            else:
                return '一致'

    def start_validate(self, inv_list):
        '''
        爬取批量发票过程
        :param inv_list: 发票信息列表
        :return:
        '''
        self.open_homepage()

        # 初始化发票队列
        inv_queue = Queue()
        for inv in inv_list:
            inv_queue.put(inv)

        fp_total_count = inv_queue.qsize()

        while True:
            if inv_queue.empty():
                break

            invoice = inv_queue.get()

            self.progress_count += 1
            print('Validation progress (undergoing/total): %s/%s' % (self.progress_count, fp_total_count))
            print('Processing...')
            try:
                if invoice['excel_cell_data_error']:
                    self.log_finished_invoice(invoice, invoice['excel_cell_data_error'])
                    print('Finished')
                    continue

                # 数据源里的发票信息不全
                if invoice['invoice_code'] == '' or \
                        invoice['invoice_num'] == '' or \
                        invoice['invoice_date'] == '' or \
                        (invoice['invoice_check_code'] == '' and invoice['invoice_kjje'] == ''):
                    self.log_finished_invoice(invoice, '发票信息不全，查验失败')
                    print('Finished')
                    continue

                self.is_popup_displayed()

                logging.info(invoice)
                # 输入发票基本信息
                self.input_invoice_info(invoice)

                # 浏览器判断输入有误的情况
                if self.validate_basic_info():
                    self.log_finished_invoice(invoice, self.validate_basic_info())
                    print('Finished')
                    continue

                self.normal_fp += 1
                # 等待验证码刷新
                self.display_captha()

                # 判断验证码是否已经刷新。有时候成功验证后，验证码可能因为网络原因不能及时刷新
                if self.checked_captha_url == self.browser.find_element_by_id('yzm_img').get_attribute('src'):
                    self.refresh_captha(self.checked_captha_url)

                # 下载验证码并进行识别
                color = self.download_captha()
                crack_result = crack_captha(color)
                self.shibie_count += 1
                # 记录查验结果
                check_result = self.check_invoice(crack_result['pic_str'])
                while check_result is False:
                    send_error(crack_result['pic_id'])
                    captha_url = self.browser.find_element_by_id('yzm_img').get_attribute('src')
                    self.refresh_captha(captha_url)
                    self.display_captha()
                    color = self.download_captha()
                    crack_result = crack_captha(color)
                    self.shibie_count += 1
                    check_result = self.check_invoice(crack_result['pic_str'])

                if check_result == -1:
                    inv_queue.put(invoice)
                    continue

                self.log_finished_invoice(invoice, check_result)
                if self.html_code:
                    parse_source_code(self.html_code, '%s%s' % (invoice['invoice_code'], invoice['invoice_num']))
                    self.html_code = ''

                # 每张发票验证完后保存一个验证码url，用以下一次验证的时候检查时候已经刷新
                self.checked_captha_url = self.browser.find_element_by_id('yzm_img').get_attribute('src')

                print('Finished')

            except (BadRefreshException, NoSuchElementException, CjyDecodeException, CjyRecognizeException):
                inv_queue.put(invoice)
                logging.error(traceback.format_exc())

                self.progress_count -= 1
                print('error occurred when validating')
                print('rollback and validate next invoice')
                logging.info('begin to close browser ... ')
                self.browser.quit()

                self.browser = webdriver.Ie()
                self.browser.maximize_window()
                self.browser.execute_script("document.body.style.zoom='100%';")
                self.open_homepage()
                logging.info('new browser is opened ... ')

            except CjyConectionError:
                logging.error('failed when calling chaojiying api')
                break

            except CjyApiError:
                break

            except CapthaNotRefreshException:
                logging.error('captha cannot refresh')
                break

            # 遇到不能预测的错误时，退出验证过程，将剩余发票查验状态标记为未查看
            except Exception:
                self.log_finished_invoice(invoice, '程序出错')

                while inv_queue.qsize():
                    self.log_finished_invoice(inv_queue.get(), '因程序出错退出未查看')

                logging.error(traceback.format_exc())
                break

        self.browser.quit()


if __name__ == '__main__':
    pass
