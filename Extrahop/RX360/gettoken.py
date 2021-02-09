import requests
import base64
import json

# The hostname of the Reveal(x) 360 API. This hostname is displayed in Reveal(x)
# 360 on the API Access page under API Endpoint. The hostname does not
# include the /oauth/token.
HOST = "https://transportnsw.api.cloud.extrahop.com/oauth2/token"
# The ID of the REST API credentials.
ID = "6r8eqrcku1d6geucnblvlc8fab"
# The secret of the REST API credentials.
SECRET = "Cisc0123"

proxies = {
    'http': "147.200.0.44:8080",
    'https': "147.200.0.44:8080",
}


def getToken():
    """
    Method that generates and retrieves a temporary API access token for Reveal(x) 360 authentication.
        Returns:
            str: A temporary API access token
    """
    auth = base64.b64encode(bytes(ID + ":" + SECRET, "utf-8")).decode("utf-8")
    print(auth)
    headers = {
        "Authorization": "Basic " + auth,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    r = requests.post(
        HOST,
        headers=headers,
        data="grant_type=client_credentials", proxies=proxies
    )
    print(r.json())
    return r.json()["access_token"]


if __name__ == '__main__':
    token = getToken()
    print(token)
