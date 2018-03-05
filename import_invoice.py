# encoding: utf-8
import logging
import re

import sys
import traceback

import xlrd


def read_excel_currency(v):
    if v is None or v == '':
        return ' '
    else:
        # return str(round(float(v), 2))
        return v

def get_invoices(input_path):
    try:
        wb = xlrd.open_workbook(input_path)
    except IOError:
        # print('配置文件读取失败')
        logging.error('config file load error')
        sys.exit(0)

    ws = wb.sheet_by_index(0)

    invoice_list = []
    for row in list(ws.get_rows())[1:]:
        try:
            invoice = dict(invoice_code=re.sub(re.compile('\.\d+'), '', str(row[0].value)),
                           invoice_num=re.sub(re.compile('\.\d+'), '', str(row[1].value)),
                           invoice_date=str(row[2].value).replace('.0', ''),
                           invoice_kjje_tax=read_excel_currency(row[3].value),
                           invoice_kjje=read_excel_currency(row[4].value),
                           invoice_check_code=str(row[5].value.replace('\n', '')),
                           excel_cell_data_error=''
                           )

        # except TypeError:
        #     # logging.error('excel数据文件数据类型有误！')
        #     logging.error(traceback.format_exc())
        #     # print(traceback.format_exc())
        #     sys.exit()
        # except ValueError:
        #     # logging.error('excel数据文件数据类型有误！')
        #     logging.error(traceback.format_exc())
        #     # print(traceback.format_exc())
        #     sys.exit()
        except Exception:
            invoice = dict(invoice_code=row[0].value,
                           invoice_num=row[1].value,
                           invoice_date=str(row[2].value).replace('.0', ''),
                           invoice_kjje_tax=row[3].value,
                           invoice_kjje=row[4].value,
                           invoice_check_code=row[5].value.replace('\n', ''),
                           excel_cell_data_error='excel 单元格数据格式错误'
                           )

        # invoice = dict(invoice_code=row[0].value,
        #                invoice_num=row[1].value,
        #                invoice_date=row[2],
        #                invoice_kjje_tax=row[3].value,
        #                invoice_kjje=row[4].value,
        #                invoice_check_code=row[5].value,
        #                )

        invoice_list.append(invoice)
    return invoice_list


if __name__ == '__main__':
    # print(get_invoices())
    pass