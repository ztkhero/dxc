import requests
import warnings
import json
warnings.filterwarnings("ignore")

APIKEY = "L9JzDoLdRscLAGYCvdPxnlunzEmaYjDuNC5bNdoq9GY"
headers = {
    'Accept': 'application/json',
    'Authorization': 'ExtraHop apikey=%s' % APIKEY
}

url = "https://10.33.197.102/api/v1"

def getPack():
    getspurl = url + '/supportpacks'
    r = requests.get(getspurl, headers=headers, verify=False)
    return json.loads(r.text)

if __name__ == '__main__':
    packlist=getPack()
    print(packlist)
    for each in packlist:
        print(each)

