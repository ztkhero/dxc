#!/usr/bin/python3

import requests, json
import warnings

warnings.filterwarnings("ignore")


def allAlerts(ip, headers):
    url_alert = "https://" + ip + "/api/v1/alerts"

    r = requests.get(url_alert, headers=headers, verify=False)

    # print(r.content.decode("utf-8"))
    result = json.loads(r.content.decode("utf-8"))

    for each in result:  # filter alters and print
        print("id: {id} - Name: {name}".format(id=each.get("id"), name=each.get("name")))

    '''
    {'id': 11, 'description': 'Alert triggered when ratio of web errors is greater than 5%.', 'mod_time': 1599782635081, 'notify_snmp': False, 'field_op': '/', 'stat_name': 'extrahop.application.http', 'disabled': True, 'operator': '>', 'operand': '0.05', 'field_name': 'rsp_error', 'name': 'Web Error Ratio - Red', 'cc': [], 'apply_all': False, 'severity': 1, 'author': 'ExtraHop', 'param': {'dset_param': 'median'}, 'interval_length': 30, 'param2': {'dset_param': 'median'}, 'units': 'none', 'field_name2': 'rsp', 'refire_interval': 300, 'type': 'threshold'}
    '''
    return result  # return all results without filter


def alert(ip, headers, id):
    url_alert = "https://" + ip + "/api/v1/alerts/" + id
    r = requests.get(url_alert, headers=headers, verify=False)
    result = json.loads(r.content.decode("utf-8"))
    print(r.content.decode("utf-8"))
    return result


if __name__ == '__main__':
    ip = "10.33.197.102"

    headers = {
        "accept": "application/json",
        "Authorization": "ExtraHop apikey=L9JzDoLdRscLAGYCvdPxnlunzEmaYjDuNC5bNdoq9GY"
    }

    alerts = allAlerts(ip, headers)
    alert(ip,headers,"15")