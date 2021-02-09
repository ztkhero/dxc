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
    data = {
        "from": 1603630800001.0,
        "metric_category": "net",
        "metric_specs": [
            {
                "name": "bytes_out"
            }
        ],
        "object_type": "device_group",
        "object_ids": [
            10
        ],
        "cycle": "auto",
        "until": 1603632600000.0

    }
    url = "https://10.33.197.102/api/v1/metrics"
    r = requests.post(url, headers=headers, data=json.dumps(data), verify=False)
    print(r.text)

    xid = json.loads(r.text)["xid"]
    url1 = "https://10.33.197.102/api/v1/metrics/next/" + str(xid)
    r = requests.get(url1, headers=headers, verify=False)
    print(r.text)
    statsmetrics = json.loads(r.text)["stats"]
    bytesout = 0
    for each in statsmetrics:
        bytesout += int(each['values'][0])
    if 1000 < bytesout < 1000000:
        print("{0} KB".format(bytesout / 1000))
    elif 1000000 < bytesout < 1000000000:
        print("{0} MB".format(bytesout / 1000000))
    elif 1000000000 < bytesout < 1000000000000:
        print("{0} GB".format(bytesout / 1000000000))
    elif bytesout > 1000000000000:
        print("{0} TB".format(bytesout / 1000000000000))
    else:
        print("{0} Bytes".format(bytesout))
