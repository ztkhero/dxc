import requests
from bs4 import BeautifulSoup
import urllib3
import time

urllib3.disable_warnings()


def get_token(url, headers, s):  # token for ECA is necessary, others use cookie

    r = s.get(url, timeout=30, headers=headers, verify=False)
    soup = BeautifulSoup(r.content, "html.parser")
    sfind = soup.find_all('form', id='loginForm')[0]
    token = sfind.find_all('input', attrs={'name': 'csrfmiddlewaretoken'})[0].get('value')
    return token


def access_cookie(url, headers, ip, token, s):
    data = {
        "csrfmiddlewaretoken": token,
        "next": "/admin/",
        "username": username,
        "password": password

    }
    headers_access = headers.copy()
    headers_access["Content-Length"] = "133"
    headers_access["Content-Type"] = "application/x-www-form-urlencoded"
    headers_access["Origin"] = "https://" + ip
    headers_access["Referer"] = "https://" + ip + "/admin/login/?next=/admin/"
    headers_access["Sec-Fetch-Site"] = "same-origin"
    r = s.post(url, headers=headers_access, data=data, verify=False)
    return r


if __name__ == '__main__':
    ip = "10.33.197.102"
    url = 'https://' + ip + '/admin/login/?next=/admin/'
    username = "tzhang"
    password = "vOkls2"
    s = requests.session()
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en,zh-CN;q=0.9,zh;q=0.8",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Host": ip,
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36"
    }

    token = get_token(url, headers, s)
    print(token)

    url_login = 'https://' + ip + '/admin/login/'
    access_cookie(url_login, headers, ip, token, s)

    time.sleep(2)
    ips = ["10.33.197.103"]
    headers["Host"] = ips[0]
    r = s.get("https://" + ips[0] + "/admin/", headers=headers, verify=False)
    print(r.content)
