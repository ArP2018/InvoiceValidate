# encoding: utf-8
import json
import logging
import re

from PIL import Image
import sys

from chaojiying import Chaojiying_Client
from cjy_code_mapping import err_type_map, err_code_map
from udf_exceptions import CjyConectionError, CjyApiError, CjyDecodeException, CjyRecognizeException

captha_path = 'temp\captha.png'

try:
    with open('config', 'r') as f:
        config_info = f.read()
        cjy_name = re.search(re.compile('USERNAME *\=( *\S+)'), config_info).group(1).strip()
        cjy_password = re.search(re.compile('PASSWORD *\=( *\S+)'), config_info).group(1).strip()
except IOError:
    logging.warning(u'error when opening config file')
    sys.exit(0)

cjy = Chaojiying_Client(cjy_name, cjy_password, '96001')


def get_merged_img(img_path, color):
    to_img = Image.new('RGB', (90, 55), (255, 255, 255))

    im_code = Image.open(img_path)
    if color == u'蓝色':
        im_color = Image.open('temp/blue.png')
    elif color == u'红色':
        im_color = Image.open('temp/red.png')
    # elif color == u'黄色':
    else:
        im_color = Image.open('temp/yellow.png')

    to_img.paste(im_code, (0, 0))
    to_img.paste(im_color, (0, 36))

    to_img.save(img_path)

    return img_path


# 发送错误报告
def send_error(pic_uid):
    cjy.ReportError(pic_uid)


def crack_captha(color):
    try:
        if color:
            merged_img = get_merged_img(captha_path, color)
            im = open(merged_img, 'rb').read()
            logging.info(u'ready to call chaojiying api')
            crack_result_msg = cjy.PostPic(im, 6004)
        else:
            im = open(captha_path, 'rb').read()
            logging.info(u'ready to call chaojiying api')
            crack_result_msg = cjy.PostPic(im, 5000)

    except ConnectionError:
        logging.error(u'chaojiying api connection error')
        raise CjyConectionError
    except json.decoder.JSONDecodeError:
        logging.error('chaojiying api decode error')
        raise CjyDecodeException

    err_code = crack_result_msg['err_no']
    # os.remove(captha_path)

    if err_code == 0:
        logging.info(u'captha recognize complete')
        logging.info(json.dumps(crack_result_msg, ensure_ascii=False))
        return {'pic_str': crack_result_msg['pic_str'], 'pic_id': crack_result_msg['pic_id']}

    # 识别过程报错, 发送错误给超级鹰
    elif err_code in err_type_map['repeat']:
        logging.info(u'chaojiying error, error code: %s' % str(err_code))
        logging.info('error info: %s' % err_code_map[err_code])
        # cjy.ReportError(crack_result_msg['pic_id'])
        raise CjyRecognizeException
    else:
        logging.info(u'chaojiying error, error code: %s' % str(err_code))
        logging.info('error info: %s' % err_code_map[err_code])
        # cjy.ReportError(crack_result_msg['pic_id'])
        raise CjyRecognizeException


if __name__ == '__main__':
    # print(crack_captha(color='黄色'))
    pass
