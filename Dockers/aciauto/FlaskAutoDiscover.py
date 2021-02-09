import requests, json, re, time, sys
from netmiko import ConnectHandler
from collections import Counter  # list comparision
import warnings

warnings.filterwarnings("ignore")
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += 'HIGH:!DH:!aNULL'
try:
    requests.packages.urllib3.contrib.pyopenssl.DEFAULT_SSL_CIPHER_LIST += 'HIGH:!DH:!aNULL'
except AttributeError:
    # no pyopenssl support used / needed / available
    pass


class APICAPI():
    def __init__(self, name, pwd, apicip, mac, socketio):
        self.name = name
        self.pwd = pwd
        self.apicip = "https://" + apicip
        self.sship = apicip
        self.token = ''
        self.socketio = socketio
        self.headers = {
            "Content-type": "application/json"
        }
        # self.mac = mac
        self.__initialMac(mac)  # 输入任何格式的mac都可以进行输出
        self.s = requests.session()
        self.getToken()  # get token first before any action

    def __dbprint(self, msg, DEBUG=0):
        self.socketio.emit('apic_result',
                           {'data': msg},
                           namespace='/test')

        if DEBUG:
            print(msg)

    def socketprint(self, msg):
        if self.webprint:
            self.socketio.emit('my_response',
                               {'data': msg, 'count': '9'},
                               namespace='/test')
        print(msg)

    def getToken(self):
        self.__dbprint("------------------------Applying Token--------------------------------")
        url = self.apicip + '/api/aaaLogin.json?gui-token-request=yes'
        data = {"aaaUser": {"attributes": {"name": self.name, "pwd": self.pwd}}}
        r = self.s.post(url, json=data, headers=self.headers, verify=False)
        # filter the token
        token = json.loads(r.text)['imdata'][0]['aaaLogin']['attributes'].get(
            'token')  # token直接存在session的cookies里面，不用管了
        urltoken = json.loads(r.text)['imdata'][0]['aaaLogin']['attributes'].get(
            'urlToken')  # 必须要把urltoken放进header里面才能运行
        # self.__dbprint(r.headers)
        # save token as global para
        self.headers["APIC-challenge"] = urltoken
        # self.urltoken = urltoken
        self.__dbprint("------------------------Token Done--------------------------------")

    def __EP_tracker(self):
        self.__dbprint("------------------------Start Detect--------------------------------")
        url = self.apicip + '/api/node/class/fvCEp.json?rsp-subtree=full&rsp-subtree-class=fvCEp,fvRsCEpToPathEp,fvIp,fvRsHyper,fvRsToNic,fvRsToVm&query-target-filter=eq(fvCEp.mac,"' + self.mac + '")'
        r = self.s.get(url, headers=self.headers, verify=False)
        # self.__dbprint(r.text)
        '''
        {"totalCount":"1","imdata":[{"fvCEp":{"attributes":{"annotation":"","childAction":"","contName":"","dn":"uni/tn-AGENCY-TRAINS/ap-Agency-TRAINS-Ap/epg-g1-agency-trains-116-Epg/cep-00:50:56:8A:3A:10","encap":"vlan-116","extMngdBy":"","id":"0","idepdn":"","ip":"0.0.0.0","lcC":"learned","lcOwn":"local","mac":"00:50:56:8A:3A:10","mcastAddr":"not-applicable","modTs":"2020-08-29T09:17:54.097+11:00","monPolDn":"uni/tn-common/monepg-default","name":"00:50:56:8A:3A:10","nameAlias":"","status":"","uid":"0","uuid":"","vmmSrc":""},"children":[{"fvRsCEpToPathEp":{"attributes":{"childAction":"","forceResolve":"yes","lcC":"learned","lcOwn":"local","modTs":"2020-08-29T09:17:54.097+11:00","rType":"mo","rn":"rscEpToPathEp-[topology/pod-1/protpaths-3172-3182/pathep-[VpcForG1G2-L2DCI-ACI-Sync02-PolGrp]]","state":"formed","stateQual":"none","status":"","tCl":"fabricAPathEp","tDn":"topology/pod-1/protpaths-3172-3182/pathep-[VpcForG1G2-L2DCI-ACI-Sync02-PolGrp]","tType":"mo"},"children":[{"fvReportingNode":{"attributes":{"childAction":"","createTs":"1970-01-01T11:00:00.000+11:00","id":"3172","lcC":"learned","lcOwn":"local","modTs":"2020-08-30T12:06:14.772+11:00","rn":"node-3172","status":""}}},{"fvReportingNode":{"attributes":{"childAction":"","createTs":"1970-01-01T11:00:00.000+11:00","id":"3182","lcC":"learned","lcOwn":"local","modTs":"2020-08-30T13:05:21.677+11:00","rn":"node-3182","status":""}}}]}}]}}]}
        '''
        try:  # 有的fvRsCEpToPathEp 并不是在[0]，需要循环找到第一个出现的位置
            for search in json.loads(r.text)['imdata'][0]["fvCEp"]["children"]:
                if search.get("fvRsCEpToPathEp"):
                    learnat = \
                        search["fvRsCEpToPathEp"]["attributes"].get(
                            "tDn").split(
                            '/')[
                            -1]  # 如果有多个结果，那么imdata的list会有多个元素
                    break
        except IndexError:
            self.__dbprint("The MAC {mac} is not in ACI!".format(mac=self.mac))
            return 1 # onapic2=1 继续搜索apic2

        except Exception as e:
            self.__dbprint(e)
            exit(0)
        if "pathep" not in learnat:  # 如果是有直接连接到单个leaf的接口，会被返回 "20]", 那么这里直接返回结果
            self.__dbprint("Direct Connect to ACI: {0}".format(search["fvRsCEpToPathEp"]["attributes"].get("tDn")))
            exit(0)
        self.learnat = re.search('\[(.*)\]$', learnat).groups()[0]
        datalist = json.loads(r.text)['imdata'][0]["fvCEp"]["attributes"].get('dn').split("/")
        # "uni/tn-AGENCY-TRAINS/ap-Agency-TRAINS-Ap/epg-g1-agency-trains-116-Epg/cep-00:50:56:8A:3A:10"
        tenant = datalist[1]
        self.tenant = re.search('tn-(.*)', tenant).groups()[0]
        app = datalist[2]
        self.app = re.search('ap-(.*)', app).groups()[0]
        epg = datalist[3]
        self.epg = re.search('g\d-(.*)', epg).groups()[0]

        self.__dbprint("The MAC is: {mac}".format(mac=self.mac))
        self.__dbprint("Learned from: {0}".format(self.learnat))
        self.__dbprint("Tenant: {0}".format(self.tenant))
        self.__dbprint("Application: {0}".format(self.app))
        self.__dbprint("EPG: {0}".format(self.epg))
        if len(json.loads(r.text)['imdata']) > 1:  # 如果返回多个EPG/VLAN有相同的MAC，那么输出提醒
            self.__dbprint("  (More EGP in this MAC, result might be not accurate)")
        else:
            self.__dbprint("\n")

        self.__dbprint("------------------------------------------------------------------------")
        return 0 # onapic2=0，不用继续搜索apic2

    def __nodePort(self):  # 获得node和端口信息
        self.__dbprint("------------------------Port Searching--------------------------------")
        url = self.apicip + '/api/node/mo/uni/infra/funcprof/accbundle-' + self.learnat + '.json?rsp-subtree-include=full-deployment&target-path=AccBaseGrpToEthIf'
        r = self.s.get(url, headers=self.headers, verify=False)
        nodes = json.loads(r.text)['imdata'][0]["infraAccBndlGrp"]["children"]  # 获得所有node raw data

        self.nodes = {}  # filter出所有的node到list,存node和interface信息：{'1023': ['eth1/1', 'eth1/45'], '2023': ['eth1/1', 'eth1/45']}
        for node in nodes:
            self.nodes[(node["pconsNodeDeployCtx"]["attributes"].get("nodeId"))] = []  # 接口信息暂时留空
        # self.__dbprint(nodeids) # 列出所有node

        for nodeid in self.nodes:  # 从每个node中filter出port
            porturl = self.apicip + '/api/node/mo/uni/infra/funcprof/accbundle-' + self.learnat + '.json?rsp-subtree-include=full-deployment&target-node=' + nodeid + '&target-path=AccBaseGrpToEthIf'
            r = self.s.get(porturl, headers=self.headers, verify=False)
            # self.__dbprint(r.text) # json返回
            for each in json.loads(r.text)['imdata'][0]['infraAccBndlGrp']['children']:  # 检查一下哪个brunch有port信息
                icount = each['pconsNodeDeployCtx']["attributes"].get('count')
                if int(icount) > 0:  # 有port信息的tree， attributes的count不为0
                    portlist = each['pconsNodeDeployCtx'][
                        'children']  # children 需要查看一下attribute的count，如果为0，那么就不是该children

                    portlist.pop()  # 最有一个没有用
                    self.__dbprint("ACI Node {0} interface:".format(nodeid))
                    for port in portlist:  # 获得node中的接口数据
                        rawport = port['pconsResourceCtx']['attributes'].get('ctxDn')
                        portnum = re.search('\[(.*)\]$', rawport).groups()[0]
                        self.nodes[nodeid].append(portnum)
                        self.__dbprint(portnum)

                        # before re output: topology/pod-1/node-3172/sys/phys-[eth1/41]
            self.__dbprint("------------------------------------------------------------------------")

    def __cdp(self):
        self.__dbprint("------------------------CDP Searching--------------------------------")
        # {'1023': ['eth1/1', 'eth1/45'], '2023': ['eth1/1', 'eth1/45']}
        cdpsysname = []
        for node in self.nodes:
            for interface in self.nodes[node]:
                url = self.apicip + '/api/node/mo/topology/pod-1/node-' + node + '/sys/cdp/inst/if-[' + interface + '].json?query-target=children&target-subtree-class=cdpAdjEp'
                # lldp --->   url: https://10.33.158.133/api/node/mo/topology/pod-1/node-2023/sys/lldp/inst/if-[eth1/1].json?query-target=children&target-subtree-class=lldpAdjEp
                r = self.s.get(url, headers=self.headers, verify=False)
                if not json.loads(r.text)['imdata']:  # 如果CDP信息为空，那么很可能host 直连ACI的
                    self.__dbprint("No CDP information, need to connect to ACI identifying")
                    self.__leaf_check()  # 找到不到CDP后，直接去leaf查看mac，验证是否为直连
                    exit(1)
                sysname = json.loads(r.text)['imdata'][0]['cdpAdjEp']['attributes'].get('sysName')
                if sysname not in cdpsysname:
                    cdpsysname.append(sysname)
                # self.__dbprint(r.text)
        self.__dbprint("The CDP neighbors are: {0}".format(cdpsysname))
        self.switches = cdpsysname  # 登录函数需要使用
        self.__dbprint("------------------------------------------------------------------------")
        return cdpsysname

    def __leaf_check(self):  # apic ssh 登录获得信息
        self.__dbprint("------------------------Accessing Leaf--------------------------------")
        cisco1 = {
            "device_type": "cisco_apic",
            "host": self.sship,
            "username": self.name,
            "password": self.pwd,
        }
        cmdlist = []
        for node in self.nodes:
            command = "fabric " + node + " show mac address-table | grep " + self.__mactrans()
            cmdlist.append(command)
            # cmd2 = "fabric 1026 show interface po12 | grep 'Members\|description'"
        # Will automatically 'disconnect()'
        with ConnectHandler(**cisco1) as net_connect:
            for cmd in cmdlist:
                output = net_connect.send_command(cmd).strip()
                self.__dbprint(output)

                ifnamelist = self.__apic_trans(output)  # 接口临时存储，用于查询接口信息
                node = re.search("fabric\s(\d+)\s", cmd).groups()[0]  # 把node从cmd里面取出来show interface
                for ifname in ifnamelist:  # 输出接口信息
                    self.__dbprint("--> Reading {ifname} information . . .".format(ifname=ifname))
                    ifcmd = "fabric " + node + " show interface " + ifname + " | grep 'Members\|description'"
                    output = net_connect.send_command(ifcmd).strip()
                    self.__dbprint(output)
                    self.__dbprint("--> Result:")
                    phif = re.search("channel:\s(.+)", output).groups()[0]  # 过滤出物理接口的名字，与ACI中的名字进行对比
                    phif = phif.replace(' ', '')  # 如果有空格，去掉空格
                    phiflist = phif.split(',')  # 'eth1/1, eth1/45' 如果多个接口，那么逗号分隔，如果一个，单独分隔，并且变为list

                    if Counter(phiflist) == Counter(self.nodes[node]):  # {'1023': ['eth1/1', 'eth1/45']} 列表比较，必须顺序也是一样的
                        self.__dbprint(
                            "Host {mac} is directly connect to Node-{node} Interface-{phif}".format(mac=self.mac,
                                                                                                    node=node,
                                                                                                    phif=str(
                                                                                                        phiflist)))
                    else:
                        self.__dbprint("Need more investigation. . . ")
                self.__dbprint("------------------------------------")

    def __apic_trans(self, data):
        ifnamelist = []
        for d in data.split("\n"):  # 接口临时存储，用于查询接口信息
            d = d.replace("\n", "")
            ifname = d.split(" ")[-1]
            if ifname not in ifnamelist:  # 把ssh得到的接口信息过滤后放到list，并且过滤掉重复接口
                ifnamelist.append(ifname)
        return ifnamelist

    def tonexus(self):
        self.__dbprint("------------------------Accessing N5K--------------------------------")
        # 读取switch的信息
        with open('N5KDB.json', 'r') as f:
            switchdb = json.loads(f.read())
        for switch in self.switches:
            try:
                ip = switchdb[switch]
            except:
                self.__dbprint("No such switch in DB!!")
                return None
            self.__dbprint("{0}:{1}".format(switch, ip))
            n5k = {
                "device_type": "cisco_nxos",
                "host": ip,
                "username": self.name,
                "password": self.pwd,
            }
            command = "show mac address-table | in " + self.__mactrans()
            cmd2 = "show run interface Eth151/1/5"
            # Will automatically 'disconnect()'
            with ConnectHandler(**n5k) as net_connect:
                output = net_connect.send_command(command)
                self.__dbprint(output)
            self.__dbprint("------------------------------------------------------------------------")

    def __mactrans(self):
        oldmac = self.mac.replace(':', '').lower()
        newmac = '.'.join(oldmac[i:i + 4] for i in range(0, 12, 4))  # range -- 0,4,8
        return newmac

    def __initialMac(self, mac):
        newmac = re.sub("[.:-]", "", mac).upper()
        self.mac = ':'.join(newmac[i:i + 2] for i in range(0, 12, 2))

    def test(self):
        # "VpcForG1G2-L2DCI-ACI-Sync02-PolGrp"
        url = self.apicip + '/api/node/mo/uni/infra/funcprof/accbundle-' + self.learnat + '.json?rsp-subtree-include=full-deployment&target-path=AccBaseGrpToEthIf'
        r = self.s.get(url, headers=self.headers, verify=False)
        self.__dbprint(r.text)

    def run(self):
        onapic2=self.__EP_tracker()
        if onapic2:
            swname="XXX"
            return swname,onapic2
        self.__nodePort()
        swname = self.__cdp()  # 从CDP的名字来检查对联是不是DC2的，如果连接的是LEF就是DC2，需要从走流程
        self.tonexus()
        return swname
