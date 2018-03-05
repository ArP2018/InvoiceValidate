# encoding:utf-8
import json
import logging
import re
from collections import OrderedDict

import os
from bs4 import BeautifulSoup


def check_content(source_html):
    soup = BeautifulSoup(source_html, 'lxml')
    try:
        fpdm = soup.find('span', attrs={'id': re.compile('fpdm_(\w+)')}).get_text()
    except Exception:
        return False
    # 判断查验结果一致的发票内容有没有正常填充
    if len(fpdm):
        return True
    else:
        return False


def parse_source_code(source_html, invoice_id):
    logging.info('Start parsing data from htmlcode ...')
    soup = BeautifulSoup(source_html, 'lxml')

    fp_dict = OrderedDict()

    fp_dict['发票代码'] = soup.find('span', attrs={'id': re.compile('fpdm_(\w+)')}).get_text()
    fp_dict['发票号码'] = soup.find('span', attrs={'id': re.compile('fphm_(\w+)')}).get_text()
    fp_dict['开票日期'] = soup.find('span', attrs={'id': re.compile('kprq_(\w+)')}).get_text()
    fp_dict['校验码'] = soup.find('span', attrs={'id': re.compile('jym_(\w+)')}).get_text()
    fp_dict['机器编号'] = soup.find('span', attrs={'id': re.compile('[(sb)|(jq)]bh_(\w+)')}).get_text()

    fp_dict['购买方名称'] = soup.find('span', attrs={'id': re.compile('gfmc_(\w+)')}).get_text()
    fp_dict['购买方纳税人识别号'] = soup.find('span', attrs={'id': re.compile('gfsbh_(\w+)')}).get_text()
    fp_dict['购买方地址、电话'] = soup.find('span', attrs={'id': re.compile('gfdzdh_(\w+)')}).get_text()
    fp_dict['购买方开户行及账号'] = soup.find('span', attrs={'id': re.compile('gfyhzh_(\w+)')}).get_text()

    fpmx_dict = OrderedDict()
    fpmx_items = []

    mx_table = soup.find('button', id='showmx')
    if mx_table:
        mx_row = soup.find('div', attrs={'id': 'print_areamx'}).find('table', class_='fppy_table').find_all('tr')
    else:
        mx_row = soup.find('table', attrs={'class': 'fppy_table_box'}).find_all('tr')

    for idx, row in enumerate(mx_row[1:]):
        temp_item = OrderedDict()

        if row.find('td').get_text().strip() == '合计' or row.find('td').get_text().strip() == '小计':
            break

        line_item = row.find_all('td')
        item_cnt = len(line_item)

        temp_item['序号'] = str(idx + 1)
        temp_item['货物或应税劳务、服务名称'] = line_item[item_cnt - 8].get_text()
        temp_item['规格型号'] = line_item[item_cnt - 7].get_text()
        temp_item['单位'] = line_item[item_cnt - 6].get_text()
        temp_item['数量'] = line_item[item_cnt - 5].get_text()
        temp_item['单价'] = line_item[item_cnt - 4].get_text()
        temp_item['金额'] = line_item[item_cnt - 3].get_text()
        temp_item['税率'] = line_item[item_cnt - 2].get_text()
        temp_item['税额'] = line_item[item_cnt - 1].get_text()
        fpmx_items.append(temp_item)
    fpmx_dict['项目'] = fpmx_items
    fpmx_dict['合计金额'] = soup.find('span', id=re.compile('je_(\w+)')).get_text()
    fpmx_dict['合计税额'] = soup.find('span', id=re.compile('se_(\w+)')).get_text()
    fpmx_dict['合计税额'] = soup.find('span', id=re.compile('se_(\w+)')).get_text()
    fpmx_dict['价税合计（大写）'] = soup.find('span', id=re.compile('jshjdx_(\w+)')).get_text()
    fpmx_dict['价税合计（小写）'] = soup.find('span', id=re.compile('jshjxx_(\w+)')).get_text()

    fp_dict['明细'] = fpmx_dict

    fp_dict['销售方名称'] = soup.find('span', attrs={'id': re.compile('xfmc_(\w+)')}).get_text()
    fp_dict['销售方纳税人识别号'] = soup.find('span', attrs={'id': re.compile('xfsbh_(\w+)')}).get_text()
    fp_dict['销售方地址、电话'] = soup.find('span', attrs={'id': re.compile('xfdzdh_(\w+)')}).get_text()
    fp_dict['销售方开户行及账号'] = soup.find('span', attrs={'id': re.compile('xfyhzh_(\w+)')}).get_text()

    fp_dict['备注'] = soup.find('td', attrs={'id': re.compile('bz_(\w+)')}).get_text().replace('\n', '').strip()

    if 'display: none' in soup.find('div', attrs={'id': 'icon_zf'})['style']:
        fp_dict['发票状态'] = '正常'
    else:
        fp_dict['发票状态'] = '作废'

    json_text = json.dumps(fp_dict, ensure_ascii=False)
    logging.info('Parsed invoice data: %s' % json_text)

    logging.info('Start writing invoice data to json file ...')
    with open(os.path.join('temp', '%s.json' % invoice_id), 'w', encoding='utf-8') as f:
        f.write(json_text)
    logging.info('Finished')


if __name__ == '__main__':
    with open('bug.html', 'rb') as f:
        parse_source_code(f.read(), 'bug')
