#!/usr/bin/python3

import json
import requests
import sys
import warnings

warnings.filterwarnings("ignore")


class ExtrahopBackup():

    def __init__(self, HOST, API_KEY, BACKUP_NAME):
        self.HOST = HOST
        self.API_KEY = API_KEY
        self.BACKUP_NAME = BACKUP_NAME

    def createBackup(self):
        url = self.HOST + '/api/v1/customizations'
        headers = {
            'Authorization': 'ExtraHop apikey=%s' % self.API_KEY,
            'Content-Type': 'application/json'
        }
        data = {
            "name": self.BACKUP_NAME
        }
        r = requests.post(url, headers=headers, data=json.dumps(data), verify=False)
        if r.status_code == 201:
            print("Create Backup Success!")
            return True
        else:
            print('Unable to create backup')
            print(r.text)
            print(r.status_code)
            sys.exit()

    def getIdName(self):
        url = self.HOST + '/api/v1/customizations'
        headers = {
            'Authorization': 'ExtraHop apikey=%s' % self.API_KEY,
            'Content-Type': 'application/json'
        }
        r = requests.get(url, headers=headers, verify=False)
        if r.status_code == 200:
            backups = json.loads(r.text)
            for b in reversed(backups):
                if self.BACKUP_NAME in b['name']:
                    return b['id'], b['name']
                else:
                    continue
            print('Unable to retrieve ID for specified backup')
            sys.exit()
        else:
            print('Unable to retrieve backup IDs')
            print(r.text)
            print(r.status_code)
            sys.exit()

    def downloadBackup(self, backup_id):
        url = self.HOST + '/api/v1/customizations/' + str(backup_id) + '/download'
        headers = {
            'Authorization': 'ExtraHop apikey=%s' % self.API_KEY,
            'accept': 'application/exbk'
        }
        r = requests.post(url, headers=headers, verify=False)
        if r.status_code == 200:
            return r.content
        else:
            print('Unable to download backup')
            print(r.status_code)
            print(r.text)
            sys.exit()

    def writeBackup(self, backup):
        new_name = self.BACKUP_NAME.replace(':', '')
        filepath = "/home/tzhang/joshua/ExtrahopBackup/" + new_name + '.exbk'
        with open(filepath, "wb") as b:
            b.write(bytes(backup))
        print('Success! Backup file name:')
        print(filepath)

    def deleteBackup(self, backup_id):
        url = self.HOST + '/api/v1/customizations/' + str(backup_id)
        headers = {
            'Authorization': 'ExtraHop apikey=%s' % self.API_KEY,
            'accept': 'application/exbk'
        }
        r = requests.delete(url, headers=headers, verify=False)
        if r.status_code == 204:
            print("Finish delete Backup file")
            return r.content
        else:
            print('Unable to delete backup')
            print(r.status_code)
            print(r.text)
            sys.exit()

    def backuprun(self):
        self.createBackup()
        backup_id, self.BACKUP_NAME = self.getIdName()
        print("The Backup name is: {name}".format(name=self.BACKUP_NAME))
        print("The ID is: {id}".format(id=backup_id))
        backup = self.downloadBackup(backup_id)
        self.writeBackup(backup)
        self.deleteBackup(backup_id)


if __name__ == '__main__':
    API_KEY = 'L9JzDoLdRscLAGYCvdPxnlunzEmaYjDuNC5bNdoq9GY'
    hostnames = {
        'TfNSW_ECA': 'https://10.33.197.102#L9JzDoLdRscLAGYCvdPxnlunzEmaYjDuNC5bNdoq9GY',
        'TfNSW_EDA1': 'https://10.33.197.103#47SmP-Q0x9wUTrCOeHZeIWfmz9LzrDcfMIDaAWYbJjU',
        'TfNSW_EDA2': 'https://10.41.197.103#xfG4byIl2g8QSwF-Dho_Nscn4WjIMFlbAorxcvpkuiU'
    }
    # HOST = 'https://10.33.197.102'
    # BACKUP_NAME = 'TfNSW_ECA'

    for host in hostnames:
        bk = ExtrahopBackup(hostnames.get(host).split("#")[0], hostnames.get(host).split("#")[1], host)
        bk.backuprun()
        print('-------------------------------------------------------')
