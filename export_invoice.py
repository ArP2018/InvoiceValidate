# encoding: utf-8

'''
created_by: Yin Yalin
created_date: 2017-11-22
purpose: 处理爬取下来的发票json文件
'''
import json
import logging
import time
import pandas as pd


def trans_currency(v):
    if v.strip() == '' or v is None:
        return ''
    else:
        return float(v)


def convert_to_list(file_path):
    '''
    按照
    Entity name 开票抬头
    Invoice Date 开票日期
    Invoice # 发票号码
    Vendor Name 供应商名称
    Amount(Tax inc.) 含税金额
    Tax Rate 税率
    Tax amount 税额
    的顺序返回一个list
    :param file_path:
    :return:
    '''
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        inv_dict = json.loads(text)

        # amount_tax = float(inv_dict['明细']['价税合计（小写）'][1:])
        # tax = float(inv_dict['明细']['合计税额'][1:])
        # tax_rate = str(int(round(tax / (amount_tax - tax) * 100, 0))) + '%'
        return [inv_dict['发票代码'],
                inv_dict['发票号码'],
                inv_dict['开票日期'],
                inv_dict['购买方名称'],
                inv_dict['购买方纳税人识别号'],
                inv_dict['购买方开户行及账号'],
                inv_dict['购买方地址、电话'],
                inv_dict['销售方名称'],
                inv_dict['销售方名称'],
                inv_dict['销售方地址、电话'],
                inv_dict['销售方开户行及账号'],
                inv_dict['明细']['合计金额'],
                inv_dict['明细']['合计税额'],
                inv_dict['明细']['价税合计（小写）'],
                inv_dict['明细']['价税合计（大写）'],
                inv_dict['备注'],
                inv_dict['校验码'],
                inv_dict['发票状态']]

    except IOError:
        logging.debug('output file path  %s does not exist')
        return False


def convert_to_detail_list(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        inv_dict = json.loads(text)

        inv_detail_list = []
        gmfmc = inv_dict['购买方名称']
        kprq = inv_dict['开票日期']
        fpdm = inv_dict['发票代码']
        fphm = inv_dict['发票号码']
        xsfmc = inv_dict['销售方名称']

        for idx, item in enumerate(inv_dict['明细']['项目']):
            temp_item = []
            temp_item.append(fpdm)
            temp_item.append(fphm)
            temp_item.append(idx + 1)
            temp_item.append('')
            temp_item.append(item['货物或应税劳务、服务名称'])
            temp_item.append(item['规格型号'])
            temp_item.append(item['单位'])
            temp_item.append(item['数量'])
            temp_item.append(item['单价'])
            temp_item.append(item['金额'])
            temp_item.append(item['税率'])
            temp_item.append(item['税额'])

            inv_detail_list.append(temp_item)

        return inv_detail_list

    except IOError:
        logging.debug('output file path  %s does not exist')
        return False


def write_to_excel(output_path):
    finished_inv_list = []
    with open('finished_invoice_temp', 'r', encoding='utf-8') as f:
        for line in f.readlines():
            finished_inv_list.append(line.replace('\n', '').split('|'))

    df = pd.DataFrame(finished_inv_list)

    # sheet2_data = [['', '购买方名称', '', '', '销售方名称', '', '税额/(含税金额-税额)', '']]
    # sheet3_data = [['', '购买方名称', '', '', '销售方名称', '', '税额/(含税金额-税额)', '']]
    sheet2_data = []
    sheet3_data = []
    cnt = 1
    for inv in finished_inv_list:
        path = 'temp/%s%s.json' % (inv[0], inv[1])
        # print path
        temp_list = convert_to_list(path)
        if temp_list:
            list_sheet2 = [cnt]
            list_sheet2.extend(temp_list)
            cnt += 1
            sheet2_data.append(list_sheet2)

        detail_list = convert_to_detail_list(path)

        if detail_list:
            sheet3_data.extend(detail_list)
    df_sheet2 = pd.DataFrame(sheet2_data, )
    df_sheet3 = pd.DataFrame(sheet3_data)

    writer = pd.ExcelWriter(output_path)
    df.to_excel(writer, index=False,
                sheet_name='check_result-%s' % time.strftime("%Y%m%d %H%M%S", time.localtime()),
                # columns=(
                #     'invoice_code', 'invoice_num', 'invoice_date', 'invoice_kjje_tax', 'invoice_kjje',
                #     'invoice_check_code', 'state'
                # ),
                header=('发票代码', '发票号码', '开票日期', '含税开票金额', '不含税开票金额', '校验码', '查验结果'))

    if not df_sheet2.empty:
        df_sheet2.to_excel(writer, index=False,
                           sheet_name='invoice list-%s' % time.strftime("%Y%m%d %H%M%S", time.localtime()),
                           header=['NO.序号', '发票代码', '发票号码', '开票日期', '购方名称', '购方税号', '购方开户行账户',
                                   '购方地址电话', '销方名称', '销方税号', '销方地址电话', '销方开户行账户', '合计金额',
                                   '合计税额', '价税合计', '价税合计_中文', '备注', '校验码', '发票状态'
                                   ])
    if not df_sheet3.empty:
        df_sheet3.to_excel(writer, index=False,
                           sheet_name='invoice details-%s' % time.strftime("%Y%m%d %H%M%S", time.localtime()),
                           header=['发票代码', '发票号码', '序号', '商品编码', '货物或应税劳务名称', '规格型号',
                                   '单位', '数量', '单价', '金额', '税率', '税额'])
    writer.save()


if __name__ == '__main__':
    for i in range(120):
        write_to_excel('testing/target_%s.xlsx'%str(i))
