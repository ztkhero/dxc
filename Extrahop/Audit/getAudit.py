#!/usr/bin/python3
# -*- coding=utf-8 -*-
import json
import requests
import time
import warnings
from openpyxl import Workbook
import pymysql
import datetime

warnings.filterwarnings("ignore")


def auditData(apikey, eip, limit, offset, title, excel):
    headers = {
        "Accept": "application/json",
        "Authorization": apikey
    }
    url = eip + "/api/v1/auditlog?limit=" + limit + "&offset=" + offset
    r = requests.get(url, headers=headers, verify=False)
    data = json.loads(r.text)
    if excel:  # 写入excel
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = title
        sheet["A1"] = "Time"
        sheet["B1"] = "User"
        sheet["C1"] = "API Key"
        sheet["D1"] = "Operation"
        sheet["E1"] = "Details"
        sheet["F1"] = "Component"
        column = 2
    else:  # 写入sqldb
        pass
    for each in data:  # 解析json数据
        id = each.get("id")  # for sql
        atime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(float(each.get('occur_time')) / 1000))
        user = each["body"].get("user")
        api_key = each["body"].get("apikey_redacted")
        operation = each["body"].get("operation")
        details = each["body"].get("details")
        component = each["body"].get("facility")
        timestamp = float(each.get('occur_time')) / 1000  # for sql
        # print(each)
        # print("Time:{0} User:{1} API Key:{2} Operation:{3} Details:{4} Component:{5}".format(atime, user, api_key,
        #                                                                                      operation, details,
        #                                                                                      component))
        if excel:
            sheetWrite(sheet, str(column), atime, user, api_key, operation, details, component)
            column += 1
        else:
            sqlWrite(id, atime, user, api_key, operation, details, component, timestamp)
    if excel:
        workbook.save(filename="Extrahop_Audit_Log.xlsx")
        print("Data to Excel Success!")



def sheetWrite(sheet, column, atime, user, api_key, operation, details, component):
    sheet["A" + column] = atime
    sheet["B" + column] = user
    sheet["C" + column] = api_key
    sheet["D" + column] = operation
    sheet["E" + column] = details
    sheet["F" + column] = component

    # print(workbook.sheetnames)
    # print(sheet.title)


def sqlWrite(id, atime, user, api_key, operation, details, component, timestamp):
    try:
        db = pymysql.connect(host='10.33.80.200', port=8306, user='extrahop', passwd='Cisc0123', db='Extrahop')
    except Exception as e:
        print(e)
        exit(0)
    cursor = db.cursor()
    try:
        # Create a new record
        sql = "INSERT INTO `Audit` (`id`, `time`,`user`, `apikey`,`operation`, `details`,`component`, `timestamp`) VALUES (%s, %s,%s, %s,%s, %s,%s, %s)"
        cursor.execute(sql, (id, atime, user, api_key, operation, details, component, timestamp))
        db.commit()
    except Exception as e:
        print(e)
        db.rollback()
    db.close()


if __name__ == '__main__':
    print("master1")
    apikey = "ExtraHop apikey=ECvZVWm-9C8H0yS9xqX_hVvMOiOYsk4bvUhvOiYu824"

    eip = "https://10.33.197.102"
    limit = "1000"
    offset = "0"
    title = "ECA_Audit"
    excel = 0  # 0=sql 1=excel
    auditData(apikey, eip, limit, offset, title, excel)
