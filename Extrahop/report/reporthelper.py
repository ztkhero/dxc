import requests
from datetime import datetime
import json
import warnings

warnings.filterwarnings("ignore")


class Report():

    def __init__(self, APIKEY, ip, dgnames, timeframe, APIpara, DEBUG=0):  # dgnames 为list
        self.APIKEY = APIKEY
        self.ip = ip
        self.dgnames = dgnames
        self.timeframe = timeframe
        self.APIpara = APIpara
        self.DEBUG = DEBUG
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': 'ExtraHop apikey=%s' % self.APIKEY
        }

    def dbprint(self, msg):
        if self.DEBUG:
            print(msg)

    def __getDeviceGroupId(self):
        ids = {}
        for name in self.dgnames:
            url = "https://" + self.ip + "/api/v1/devicegroups?name=" + name
            r = requests.get(url, headers=self.headers, verify=False)
            rspdata = json.loads(r.text)
            for each in rspdata:
                ids[each['name']] = each['id']
        return ids
        # {'4Trak - App Server': 10, '4Trak - Database Servers (MySQL)': 11, '4Trak - Web Server': 9}

    def __dateToStamp(self):
        fromtime = datetime.strptime(self.timeframe["start"], '%d/%m/%Y %H:%M')
        untiltime = datetime.strptime(self.timeframe["end"], '%d/%m/%Y %H:%M')
        stampframe = {'from': datetime.timestamp(fromtime) * 1000 + 1, 'until': datetime.timestamp(untiltime) * 1000}
        return stampframe
        # {'from': 1603630800001.0, 'until': 1603632600000.0}

    def __getMetric(self):
        stampframe = self.__dateToStamp()
        xidlist = []
        data = {
            "from": stampframe['from'],
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
            "until": stampframe['until']

        }

        url = "https://" + self.ip + "/api/v1/metrics"  # 如果有多时间点的数值的话，会产生xid
        for api in self.APIpara:  # 设置多个值的时候，循环获取内容
            data["metric_category"] = api['category']
            data["metric_specs"][0]["name"] = api['name']
            r = requests.post(url, headers=self.headers, data=json.dumps(data), verify=False)
            if "xid" in r.text:
                xidlist.append(json.loads(r.text))
            else:
                self.dbprint(r.text)  # 如果没有xid，就返回metric。暂时没有遇到没有xid的值。
            # {"xid":349289,"num_results":2} 这个xid再次获取的时候，会得到每30s的一个value，可以呈现到chart里面，也可以自行累加
        self.dbprint(xidlist)
        return xidlist
        # [{'xid': 349439, 'num_results': 2}, {'xid': 349441, 'num_results': 2}]

    def __XidMetric(self):
        xidlist = self.__getMetric()
        for xid in xidlist:
            url = "https://" + self.ip + "/api/v1/metrics/next/" + str(xid["xid"])
            r = requests.get(url, headers=self.headers, verify=False)
            self.dbprint(r.text)
            statsmetrics = json.loads(r.text)["stats"]
            databytes = 0
            for metric in statsmetrics:
                databytes += int(metric['values'][0])
            print(databytes)

            dataB = self.__bytesTransfer(databytes)  # {'value': 1.234, 'unit': 'KB'}
            self.dbprint(dataB)

    def __bytesTransfer(self, databytes):
        if 1000 < databytes < 1000000:
            self.dbprint("{0} KB".format(databytes / 1000))
            return {'value': databytes / 1000, 'unit': 'KB'}
        elif 1000000 < databytes < 1000000000:
            self.dbprint("{0} MB".format(databytes / 1000000))
            return {'value': databytes / 1000000, 'unit': 'MB'}
        elif 1000000000 < databytes < 1000000000000:
            self.dbprint("{0} GB".format(databytes / 1000000000))
            return {'value': databytes / 1000000000, 'unit': 'GB'}
        elif databytes > 1000000000000:
            self.dbprint("{0} TB".format(databytes / 1000000000000))
            return {'value': databytes / 1000000000000, 'unit': 'TB'}
        else:
            self.dbprint("{0} Bytes".format(databytes))
            return {'value': databytes, 'unit': 'Bytes'}

    def run(self):
        ids = self.__getDeviceGroupId()
        self.dbprint(ids)
        self.dbprint(self.__dateToStamp())
        self.__XidMetric()


if __name__ == '__main__':
    DEBUG = 1
    APIKEY = "L9JzDoLdRscLAGYCvdPxnlunzEmaYjDuNC5bNdoq9GY"
    serverIP = "10.33.197.102"
    dgnames = ["4Trak - App Server"]
    timeframe = {
        "start": "12/10/2020  00:00",
        "end": "25/10/2020  23:59"
    }
    APIpara = [{"category": "net", "name": "bytes_out"}, {"category": "net", "name": "bytes_in"}]
    # 首次API请求经常返回错误数值，建议增加一个无用的数值进行首次请求，解决该bug
    myreport = Report(APIKEY, serverIP, dgnames, timeframe, APIpara, DEBUG)
    myreport.run()
