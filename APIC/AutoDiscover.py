import requests, json, re, time, sys
from netmiko import ConnectHandler
import warnings

warnings.filterwarnings("ignore")


class APICAPI():
    def __init__(self, name, pwd, apicip, mac):
        self.name = name
        self.pwd = pwd
        self.apicip = "https://" + apicip
        self.sship = apicip
        self.token = ''
        self.headers = {
            "Content-type": "application/json"
        }
        self.mac = mac
        self.s = requests.session()
        self.getToken()  # get token first before any action

    def getToken(self):
        print("------------------------Applying Token--------------------------------")
        url = self.apicip + '/api/aaaLogin.json?gui-token-request=yes'
        data = {"aaaUser": {"attributes": {"name": self.name, "pwd": self.pwd}}}
        r = self.s.post(url, json=data, headers=self.headers, verify=False)
        # filter the token
        token = json.loads(r.text)['imdata'][0]['aaaLogin']['attributes'].get(
            'token')  # token直接存在session的cookies里面，不用管了
        urltoken = json.loads(r.text)['imdata'][0]['aaaLogin']['attributes'].get(
            'urlToken')  # 必须要把urltoken放进header里面才能运行
        # print(r.headers)
        # save token as global para
        self.headers["APIC-challenge"] = urltoken
        # self.urltoken = urltoken
        print("------------------------Token Done--------------------------------")

    def EP_tracker(self):
        print("------------------------Start Detect--------------------------------")
        url = self.apicip + '/api/node/class/fvCEp.json?rsp-subtree=full&rsp-subtree-class=fvCEp,fvRsCEpToPathEp,fvIp,fvRsHyper,fvRsToNic,fvRsToVm&query-target-filter=eq(fvCEp.mac,"' + self.mac + '")'
        r = self.s.get(url, headers=self.headers, verify=False)
        # print(r.text)
        '''
        {"totalCount":"1","imdata":[{"fvCEp":{"attributes":{"annotation":"","childAction":"","contName":"","dn":"uni/tn-AGENCY-TRAINS/ap-Agency-TRAINS-Ap/epg-g1-agency-trains-116-Epg/cep-00:50:56:8A:3A:10","encap":"vlan-116","extMngdBy":"","id":"0","idepdn":"","ip":"0.0.0.0","lcC":"learned","lcOwn":"local","mac":"00:50:56:8A:3A:10","mcastAddr":"not-applicable","modTs":"2020-08-29T09:17:54.097+11:00","monPolDn":"uni/tn-common/monepg-default","name":"00:50:56:8A:3A:10","nameAlias":"","status":"","uid":"0","uuid":"","vmmSrc":""},"children":[{"fvRsCEpToPathEp":{"attributes":{"childAction":"","forceResolve":"yes","lcC":"learned","lcOwn":"local","modTs":"2020-08-29T09:17:54.097+11:00","rType":"mo","rn":"rscEpToPathEp-[topology/pod-1/protpaths-3172-3182/pathep-[VpcForG1G2-L2DCI-ACI-Sync02-PolGrp]]","state":"formed","stateQual":"none","status":"","tCl":"fabricAPathEp","tDn":"topology/pod-1/protpaths-3172-3182/pathep-[VpcForG1G2-L2DCI-ACI-Sync02-PolGrp]","tType":"mo"},"children":[{"fvReportingNode":{"attributes":{"childAction":"","createTs":"1970-01-01T11:00:00.000+11:00","id":"3172","lcC":"learned","lcOwn":"local","modTs":"2020-08-30T12:06:14.772+11:00","rn":"node-3172","status":""}}},{"fvReportingNode":{"attributes":{"childAction":"","createTs":"1970-01-01T11:00:00.000+11:00","id":"3182","lcC":"learned","lcOwn":"local","modTs":"2020-08-30T13:05:21.677+11:00","rn":"node-3182","status":""}}}]}}]}}]}
        '''
        learnat = \
            json.loads(r.text)['imdata'][0]["fvCEp"]["children"][0]["fvRsCEpToPathEp"]["attributes"].get("tDn").split(
                '/')[
                -1]  # 如果有多个结果，那么imdata的list会有多个元素

        self.learnat = re.search('\[(.*)\]$', learnat).groups()[0]
        datalist = json.loads(r.text)['imdata'][0]["fvCEp"]["attributes"].get('dn').split("/")
        # "uni/tn-AGENCY-TRAINS/ap-Agency-TRAINS-Ap/epg-g1-agency-trains-116-Epg/cep-00:50:56:8A:3A:10"
        tenant = datalist[1]
        self.tenant = re.search('tn-(.*)', tenant).groups()[0]
        app = datalist[2]
        self.app = re.search('ap-(.*)', app).groups()[0]
        epg = datalist[3]
        self.epg = re.search('g\d-(.*)', epg).groups()[0]

        print("The MAC is: {mac}".format(mac=self.mac))
        print("Learned from: {0}".format(self.learnat))
        print("Tenant: {0}".format(self.tenant))
        print("Application: {0}".format(self.app))
        print("EPG: {0} ".format(self.epg), end="")
        if len(json.loads(r.text)['imdata']) > 1:  # 如果返回多个EPG/VLAN有相同的MAC，那么输出提醒
            print("  (More EGP in this MAC, result might be not accurate)")
        else:
            print("\n")

        print("------------------------------------------------------------------------")

    def nodePort(self):  # 获得node和端口信息
        print("------------------------Port Searching--------------------------------")
        url = self.apicip + '/api/node/mo/uni/infra/funcprof/accbundle-' + self.learnat + '.json?rsp-subtree-include=full-deployment&target-path=AccBaseGrpToEthIf'
        r = self.s.get(url, headers=self.headers, verify=False)
        nodes = json.loads(r.text)['imdata'][0]["infraAccBndlGrp"]["children"]  # 获得所有node raw data

        self.nodes = {}  # filter出所有的node到list,存node和interface信息：{'1023': ['eth1/1', 'eth1/45'], '2023': ['eth1/1', 'eth1/45']}
        for node in nodes:
            self.nodes[(node["pconsNodeDeployCtx"]["attributes"].get("nodeId"))] = []  # 接口信息暂时留空
        # print(nodeids) # 列出所有node

        for nodeid in self.nodes:  # 从每个node中filter出port
            porturl = self.apicip + '/api/node/mo/uni/infra/funcprof/accbundle-' + self.learnat + '.json?rsp-subtree-include=full-deployment&target-node=' + nodeid + '&target-path=AccBaseGrpToEthIf'
            r = self.s.get(porturl, headers=self.headers, verify=False)
            # print(r.text) # json返回
            for each in json.loads(r.text)['imdata'][0]['infraAccBndlGrp']['children']:  # 检查一下哪个brunch有port信息
                icount = each['pconsNodeDeployCtx']["attributes"].get('count')
                if int(icount) > 0:  # 有port信息的tree， attributes的count不为0
                    portlist = each['pconsNodeDeployCtx'][
                        'children']  # children 需要查看一下attribute的count，如果为0，那么就不是该children

                    portlist.pop()  # 最有一个没有用
                    print("ACI Node {0} interface:".format(nodeid))
                    for port in portlist:  # 获得node中的接口数据
                        rawport = port['pconsResourceCtx']['attributes'].get('ctxDn')
                        portnum = re.search('\[(.*)\]$', rawport).groups()[0]
                        self.nodes[nodeid].append(portnum)
                        print(portnum)

                        # before re output: topology/pod-1/node-3172/sys/phys-[eth1/41]
            print("------------------------------------------------------------------------")

    def cdp(self):
        print("------------------------CDP Searching--------------------------------")
        # {'1023': ['eth1/1', 'eth1/45'], '2023': ['eth1/1', 'eth1/45']}
        cdpsysname = []
        for node in self.nodes:
            for interface in self.nodes[node]:
                url = self.apicip + '/api/node/mo/topology/pod-1/node-' + node + '/sys/cdp/inst/if-[' + interface + '].json?query-target=children&target-subtree-class=cdpAdjEp'
                # lldp --->   url: https://10.33.158.133/api/node/mo/topology/pod-1/node-2023/sys/lldp/inst/if-[eth1/1].json?query-target=children&target-subtree-class=lldpAdjEp
                r = self.s.get(url, headers=self.headers, verify=False)
                if not json.loads(r.text)['imdata']:  # 如果CDP信息为空，那么很可能host 直连ACI的
                    print("No CDP information, need to connect to ACI identifying")
                    self.__leaf_check()  # 找到不到CDP后，直接去leaf查看mac，验证是否为直连
                    exit(1)
                sysname = json.loads(r.text)['imdata'][0]['cdpAdjEp']['attributes'].get('sysName')
                if sysname not in cdpsysname:
                    cdpsysname.append(sysname)
                # print(r.text)
        print("The CDP neighbors are: {0}".format(cdpsysname))
        self.switches = cdpsysname  # 登录函数需要使用
        print("------------------------------------------------------------------------")
        return cdpsysname

    def __leaf_check(self):  # apic ssh 登录获得信息
        print("------------------------Accessing Leaf--------------------------------")
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
                print(output)

                ifnamelist = self.__apic_trans(output)  # 接口临时存储，用于查询接口信息
                node = re.search("fabric\s(\d+)\s", cmd).groups()[0]  # 把node从cmd里面取出来show interface
                for ifname in ifnamelist:  # 输出接口信息
                    print("--> Reading {ifname} information . . .".format(ifname=ifname))
                    ifcmd = "fabric " + node + " show interface " + ifname + " | grep 'Members\|description'"
                    output = net_connect.send_command(ifcmd).strip()
                    print(output)
                    print("--> Result:")
                    phif = re.search("channel:\s(.+)", output).groups()[0]  # 过滤出物理接口的名字，与ACI中的名字进行对比
                    if phif in self.nodes[
                        node]:  # {'1023': ['eth1/1', 'eth1/45']}
                        print("Host {mac} is directly connect to Node-{node} Interface-{phif}".format(mac=self.mac,
                                                                                                      node=node,
                                                                                                      phif=phif))
                    else:
                        print("Need more investigation. . . ")
                print("------------------------------------")

    def __apic_trans(self, data):
        ifnamelist = []
        for d in data.split("\n"):  # 接口临时存储，用于查询接口信息
            d = d.replace("\n", "")
            ifname = d.split(" ")[-1]
            if ifname not in ifnamelist:  # 把ssh得到的接口信息过滤后放到list，并且过滤掉重复接口
                ifnamelist.append(ifname)
        return ifnamelist

    def tonexus(self):
        print("------------------------Accessing N5K--------------------------------")
        # 读取switch的信息
        with open('N5KDB.json', 'r') as f:
            switchdb = json.loads(f.read())
        for switch in self.switches:
            try:
                ip = switchdb[switch]
            except:
                print("No such switch in DB!!")
                return None
            print("{0}:{1}".format(switch, ip))
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
                print(output)
            print("------------------------------------------------------------------------")

    def __mactrans(self):
        oldmac = self.mac.replace(':', '').lower()
        newmac = '.'.join(oldmac[i:i + 4] for i in range(0, 12, 4))  # range -- 0,4,8
        return newmac

    def test(self):
        # "VpcForG1G2-L2DCI-ACI-Sync02-PolGrp"
        url = self.apicip + '/api/node/mo/uni/infra/funcprof/accbundle-' + self.learnat + '.json?rsp-subtree-include=full-deployment&target-path=AccBaseGrpToEthIf'
        r = self.s.get(url, headers=self.headers, verify=False)
        print(r.text)


if __name__ == '__main__':
    # note: 00:50:56:99:7B:0C 10.34.208.53 objective 直连？ 如何查看leaf的mac address table
    name = 'tzhang'
    pwd = 'vOkls2'
    apicip1 = "10.33.158.133"
    apicip2 = "10.41.158.133"

    try:
        mac = sys.argv[1]
    except:
        mac = "00:50:56:99:49:C6"

    dxcapic = APICAPI(name, pwd, apicip1, mac)
    dxcapic.EP_tracker()
    dxcapic.nodePort()
    swname = dxcapic.cdp()  # 从CDP的名字来检查对联是不是DC2的，如果连接的是LEF就是DC2，需要从走流程
    dxcapic.tonexus()
    if "LEF" in str(swname):
        print("Transfering APCI2 . . . . .")
        time.sleep(2)
        dxcapic = APICAPI(name, pwd, apicip2, mac)
        dxcapic.EP_tracker()
        dxcapic.nodePort()
        dxcapic.cdp()
        dxcapic.tonexus()
