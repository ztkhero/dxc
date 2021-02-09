import requests
import warnings
import json

warnings.filterwarnings("ignore")

if __name__ == '__main__':
    APIKEY = "L9JzDoLdRscLAGYCvdPxnlunzEmaYjDuNC5bNdoq9GY"
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'ExtraHop apikey=%s' % APIKEY
    }
    devicename = "4Trak"
    url = "https://10.33.197.102/api/v1/devicegroups?name=" + devicename
    r = requests.get(url, headers=headers, verify=False)
    rspdata=json.loads(r.text)
    for each in rspdata:
        print(each['name'])
        print("id: {0}".format(each['id']))
