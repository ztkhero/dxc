from netmiko import ConnectHandler
from influxdb import InfluxDBClient
import datetime, random
import re, time


class sshConnect():

    def __init__(self, deviceType, hostDict, userName, passWord, dataBase):
        self.deviceType = deviceType
        self.hostDict = hostDict
        self.userName = userName
        self.passWord = passWord
        self.dataBase = dataBase

    def ssh(self, host):  # 连接host并输出raw data
        device1 = {
            "device_type": self.deviceType,
            "host": host,
            "username": self.userName,
            "password": self.passWord,
        }
        # command = "top -bn1 | grep --color=never nt"
        # command = "top -Hbn1 | grep --color=never -w 'fwk[0-9][0-9]_[0-9]'"
        command = "top -Hbn1 | egrep --color=never -w 'fwk[[:digit:]]{1,2}_[[:digit:]]{1,2}'"

        with ConnectHandler(**device1) as net_connect:
            net_connect.find_prompt()
            # print(net_connect.find_prompt())
            output = net_connect.send_command(command)
        return output

    def filter(self, host):  # 对raw data 进行清洗
        raw = self.ssh(host)
        contents = raw.split("\n")  # raw data有数行，需要每行清洗
        metrics = []  # 收集清洗后的数据
        '''
        [['67', '0.8', 'fwk20_1'], ['61', '0.8', 'fwk20_3']] 数据最后呈现为这样
        '''
        for content in contents:
            metric = []
            try:
                ft = re.search('(\d+(\.\d+)?\s+\d+\.\d+)\s+\d+:\d+(\.\d+)?\s+(.*[^\s])', content).groups()
            except:
                continue
            # ft=('0.0  0.0', '.0', ' fwk20_3')
            cpu_mem_raw = ft[0]  # cpu/mem
            cpu_mem = re.split(r'\s+', cpu_mem_raw)
            # cpu_mem=['5.0', '0.0'] cpu and mem
            metric.append(cpu_mem[0])
            metric.append(cpu_mem[1])
            metric.append(ft[3])
            metrics.append(metric)
        return metrics

    def writedb(self, host, hostname):
        datalist = self.filter(host)
        '''
        [['67', '0.8', 'fwk20_1'], ['61', '0.8', 'fwk20_3']
        '''
        client = InfluxDBClient('10.33.80.200', 8086, 'tzhang', 'Cisc0123', self.dataBase)

        current_time = datetime.datetime.utcnow().isoformat("T")  # 不带时区的时间

        for subdata in datalist:
            body = [{
                "measurement": hostname,  # 表的名字
                "time": current_time,  # 时间，必须有
                "tags": {  # tag是用来索引的，不同设备用不同的tag组;基于tag过滤
                    "device_ip": host,
                    "virtual_firewall": subdata[2]
                },
                "fields": {  # 对应tag所拥有的值，不可以作为索引
                    "cpu_usage": float(subdata[0]),
                    "mem_usage": float(subdata[1]),
                },
            }]  # 例如需要10.1.1.1路由器的指标，那么tag可以用ip或者type来索引到。 但是tag与field在数据库呈现是一样的key:value

            client.write_points(body)  # 写入数据

    def run(self):
        for hostname in self.hostDict:  # 可以提交多个设备和IP
            self.writedb(self.hostDict.get(hostname), hostname)


if __name__ == '__main__':
    deviceType = "checkpoint_gaia"
    # hostList = ["10.33.80.200"]
    # userName = "tzhang"
    # passWord = "C0nnect1"
    hostDict = {"G1CTLFW1": "10.33.146.51", "G1DMZFW1": "10.33.146.41", "G1DMZFW2": "10.33.146.42",
                "G2DMZFW1": "10.41.146.43"}
    userName = "admin"
    passWord = "vpn123"
    dataBase = 'transport'
    # dataBase = 'test1'

    cp = sshConnect(deviceType, hostDict, userName, passWord, dataBase)
    cp.run()
