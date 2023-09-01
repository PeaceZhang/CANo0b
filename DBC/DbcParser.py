import copy
import re

class DBC:
    def __init__(self, dbc):
        with open(dbc, "r", encoding="gbk") as f:
            self.original_data_str = f.read()
        f.close()
        with open(dbc, "r", encoding="gbk") as f:
            self.original_data_lines = f.readlines()
        f.close()
        self.BO = []
        msg = {}
        msg_start = False

        # print(self.original_data_str)

        for line in self.original_data_lines:
            line = line.strip()             # clean string
            if line.startswith("BU_:"):
                self.BU = line.removeprefix("BU_:").strip().split(" ")
            elif line.startswith("BO_ "):
                msg_start = True
                msg_original = line.removeprefix("BO_ ").split(" ")
                msg['msgid'] = msg_original[0]
                msg['name'] = msg_original[1].strip(":")
                msg['dlc'] = msg_original[2]
                # print(msg_original)
                msg['provider'] = msg_original[3]
                self.findsignalgroup(msg)
                msg['signallist'] = []
                # self.BO.append(msg)
                pass
            elif line.startswith("SG_ "):
                signal_original = line.removeprefix("SG_ ").split(" ")
                # print(signal_original)
                signal = {}
                signal['signame'] = signal_original[0]
                signal['startbit'] = signal_original[2][:signal_original[2].find("|")]
                signal['bitlen'] = signal_original[2][signal_original[2].find("|")+1: signal_original[2].find("@")]
                signal['byteorder'] = "motorola" if "0" == signal_original[2][signal_original[2].find("@")+1: len(signal_original[2])-1] else "intel"
                signal['valuetype'] = "unsigned" if "+" == signal_original[2][len(signal_original[2]) - 1:] else "signed"
                signal['factor'] = signal_original[3][1:signal_original[3].find(",")]
                signal['offset'] = signal_original[3][signal_original[3].find(",")+1:len(signal_original[3])-1]
                signal['minvalue'] = signal_original[4][1:signal_original[4].find("|")]
                signal['maxvalue'] = signal_original[4][signal_original[4].find("|")+1: len(signal_original[4])-1]
                signal['unit'] = signal_original[5]
                signal['group'] = ""
                for group in msg['signalgrouplist']:
                    if signal['signame'] in group['element']:
                        signal['group'] = group['groupname']
                self.findsignalinitvalue(signal, msg)
                self.findsignalvaluetable(signal, msg)
                self.finsignalsendtype(signal, msg)
                if 8 == len(signal_original):
                    signal['receiver'] = (signal_original[6].strip() + signal_original[7]).strip().split(",")
                else:
                    signal['receiver'] = signal_original[6].strip().split(",")
                if True == msg_start:
                    msg['signallist'].append(signal)
                    # print(msg['signallist'])
                    pass
            else:
                if True == msg_start:
                    # print("message finished")
                    # print(msg)
                    self.BO.append(msg.copy())
                    msg_start = False
    def findsignalgroup(self, msg):
        regular_expression = "SIG_GROUP_ " + msg['msgid'] + " .*;"
        ret = re.findall(regular_expression, self.original_data_str)
        grplist = []
        group_dic = {}
        msg['signalgrouplist'] = grplist
        for line in ret:
            linelist = line.rstrip(";").split(" ")
            group_dic['groupname'] = linelist[2]
            group_dic['element'] = linelist[5:]
            grplist.append(group_dic.copy())
    def findsignalvaluetable(self, signal, msg):
        regular_expression = "VAL_ " + msg['msgid'] + " " + signal['signame'] + " .*;"
        ret = re.findall(regular_expression, self.original_data_str)
        signal['valuetable'] = []
        if 1 == len(ret):
            signal['valuetable'] = ret[0].strip(";").strip().split(" ")[3:]
            for i in range(0, len(signal['valuetable'])):
                signal['valuetable'][i] = signal['valuetable'][i].strip('\"')
            # print(signal['valuetable'])
    def findsignalinitvalue(self, signal, msg):
        regular_expression = "BA_ " + "\"GenSigStartValue\" " + "SG_ " + msg['msgid'] + " " + signal['signame'] + " .*;"
        ret = re.findall(regular_expression, self.original_data_str)
        signal['initvalue'] = ""
        if 1 == len(ret):
            signal['initvalue'] = ret[0][-2:-1]
        # print(signal['initvalue'])

    def finsignalsendtype(self, signal, msg):
        regular_expression = "BA_ " + "\"GenSigSendType\" " + "SG_ " + msg['msgid'] + " " + signal['signame'] + " .*;"
        ret = re.findall(regular_expression, self.original_data_str)
        signal['sendtype'] = ""
        if 1 == len(ret):
            signal['sendtype'] = ret[0][-2:-1]
        # print(signal['sendtype'])
    def extractnode(self, node):
        temp_buf = copy.deepcopy(self.BO)
        nodeaccess_flag = False
        groupused_flag = False
        if node not in self.BU:
            print("node is invalid!")
        else:
            for msg in reversed(temp_buf):
                nodeaccess_flag = False
                if node == msg['provider']:
                    nodeaccess_flag = True
                else:
                    for signal in reversed(msg['signallist']):
                        if node in signal['receiver']:
                            nodeaccess_flag = True
                        else:
                            msg['signallist'].remove(signal)
                if False == nodeaccess_flag:
                    temp_buf.remove(msg)
            for msg in temp_buf:
                for group in reversed(msg['signalgrouplist']):
                    groupused_flag = False
                    for signal in msg['signallist']:
                        if signal['signame'] in group['element']:
                            groupused_flag = True
                    if False == groupused_flag:
                        msg['signalgrouplist'].remove(group)
        return temp_buf

if __name__ == '__main__':
    TEST_DBC = DBC("DataBase/test.dbc")
    ExtractMsg = TEST_DBC.extractnode("node")
    print(TEST_DBC.BU)
    print(ExtractMsg)