# encoding: utf-8
import logging
import logging.handlers
import traceback

handler = logging.handlers.RotatingFileHandler('log.txt', 'a', maxBytes=10*1012*1024, backupCount=5, encoding='utf8')

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
                    # filename='log.txt',
                    handlers=[handler]
                    )

import re
import sys
import os
import time
from export_invoice import write_to_excel
from import_invoice import get_invoices
from invoice_verify_ie import InvoiceVerify

start_time = time.time()

try:
    with open('config', 'r', encoding='utf-8') as f:
        config_info = f.read()
        try:
            input_path = re.search(re.compile('SOURCE_EXCEL_PATH *\=( *\S+)'), config_info).group(1).strip()
            output_path = re.search(re.compile('TARGET_EXCEL_PATH *\=( *\S+)'), config_info).group(1).strip()
        except AttributeError:
            logging.error('config file content error')
            print('config info error')
            sys.exit(0)

except IOError:
    logging.error('config file read error, not exist')
    print('config file not exist')
    sys.exit(0)

# 获取发票基本信息列表
invoice_list = get_invoices(input_path)

# 验证并爬取列表里的发票
invfy = InvoiceVerify()
invfy.start_validate(invoice_list)

if os.path.exists('finished_invoice_temp'):
    # 将发票写入自定义的模板
    try:
        write_to_excel(output_path)
        os.remove('finished_invoice_temp')

        for j in os.listdir('temp'):
            if '.json' in j:
                os.remove('temp/%s' % j)
    except Exception:
        logging.error('failed when writing result to excel ... ')
        logging.error(traceback.format_exc())

    # 清除临时数据


end_time = time.time()

logging.info('time spent: %s s' % (end_time - start_time))
logging.info('invoice_count: %s' % invfy.normal_fp)
# logging.info('average time: %s s per invoice' % (end_time - start_time)/invfy.normal_fp)
try:
    logging.info('captha accuracy: %s%s' % (round(invfy.normal_fp / invfy.shibie_count * 100, 2), '%'))
except ZeroDivisionError:
    logging.info('captha accuracy:')

time.sleep(5)

