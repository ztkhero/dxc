import requests


def getFirmware(apikey, headers):
    url = "https://10.33.197.102/api/v1/extrahop"
    r = requests.get(url, headers=headers, verify=False)
    return r

def getUser(apikey, headers):
    url = "https://10.33.197.102/users/tzhang"
    r = requests.get(url, headers=headers, verify=False)
    return r

if __name__ == '__main__':
    apikey = "ExtraHop apikey=MJEUYSTKPjQIzBCSIO_YGJ9hIUdmkf2z6dmOCYRVPYc"
    headers = {
        "Accept": "application/json",
        "Authorization": apikey
    }

    r = getFirmware(apikey, headers)
    print(r.content)
