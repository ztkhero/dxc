#!/usr/bin/python3

import http.client
import json
import csv
import datetime
import ssl
import sys

HOST = '10.33.197.103'
APIKEY = 'pNTVfnv44PnNd6nhXld7LNCg354edFhM-64N3ZQNNDU'
FILENAME = 'devices.csv'
LIMIT = 100
SAVEL2 = False
ADVANCED_ONLY = True
CRITICAL_ONLY = False

headers = {}
headers['Accept'] = 'application/json'
headers['Authorization'] = 'ExtraHop apikey=' + APIKEY


def getDevices(offset):
    conn = http.client.HTTPSConnection(HOST, context=ssl._create_unverified_context())
    conn.request('GET', '/api/v1/devices?limit=%d&offset=%d&search_type=any' % (LIMIT, offset), headers=headers)
    resp = conn.getresponse()
    if resp.status == 200:
        devices = json.loads(resp.read())
        conn.close()
        return devices
    else:
        print("Error retrieving Device list")
        print(resp.status, resp.reason)
        resp.read()
        dTable = None
        conn.close()
        sys.exit()


continue_search = True
offset = 0
dTable = []
while (continue_search):
    new_devices = getDevices(offset)
    offset += LIMIT
    dTable += new_devices
    if (len(new_devices) > 0):
        continue_search = True
    else:
        continue_search = False

if (dTable != None):
    print(" - Saving %d devices in CSV file" % len(dTable))
    with open(FILENAME, 'w') as csvfile:
        csvwriter = csv.writer(csvfile, dialect='excel')
        csvwriter.writerow(list(dTable[0].keys()))
        w = 0
        s = 0
        for d in dTable:
            if ADVANCED_ONLY == False or (ADVANCED_ONLY == True and d['analysis'] == 'advanced'):
                if CRITICAL_ONLY == False or (CRITICAL_ONLY == True and d['critical'] == True):
                    if d['is_l3'] | SAVEL2:
                        w += 1
                        d['mod_time'] = datetime.datetime.fromtimestamp(d['mod_time'] / 1000.0)
                        d['user_mod_time'] = datetime.datetime.fromtimestamp(d['user_mod_time'] / 1000.0)
                        d['discover_time'] = datetime.datetime.fromtimestamp(d['discover_time'] / 1000.0)
                        csvwriter.writerow(list(d.values()))
                    else:
                        s += 1
                else:
                    s += 1
            else:
                s += 1
        print(" - Wrote %d devices, skipped %d devices " % (w, s))
