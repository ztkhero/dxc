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
        "metric_category": "http_server",
        "metric_specs": [
            {
                "name": "rsp"
            }
        ],
        "object_type": "device_group",
        "object_ids": [
            24
        ],
        "cycle": "auto"
        # "from":1603198800001,
        # "until":1603889940000

    }
    url="https://10.33.197.102/api/v1/metrics"
    r = requests.post(url, headers=headers, data=json.dumps(data), verify=False)
    print(r.text)