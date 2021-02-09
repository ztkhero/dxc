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
    url="https://10.33.197.102/extrahop/reports/export_dashboard?width=1400&paginate=single&name=4Trak%20-%20App%20Server%20Overview%202021-02-01%2009.26.00%20to%2009.56.00%20AEDT.pdf&id=downloaded-4133669427033039000&title=4Trak%20-%20App%20Server%20Overview&producer=ExtraHop%208.2.3.2203&creator=tzhang&stem=https%3A%2F%2F10.33.197.102&path=%2FDashboard%2FsYQcY%2Fprint&search=&hash_search=from%3D1612131960%26interval_type%3DDT%26theme%3Ddark%26until%3D1612133760"
    r = requests.get(url, headers=headers, verify=False)
    print(r.content)
