#!/usr/bin/python

import time
import threading

from ci import *

class VgmTesterRunner(TestSshRunner):
    def __init__(self, datasize):
        super(VgmTesterRunner, self).__init__("192.168.2.222", "xl4", " ")
        self.datasize = datasize
    def run(self):
        self.state = TestStateConst.Running
        self.open()
        self.sendcmd('echo 5 > /tmp/xl4_log.conf')
        self.sendcmd('pkill vgm')
        self.sendcmd("LD_LIBRARY_PATH=/tmp /tmp/vgm -size " + "%d"%self.datasize)
        while True:
            if self.state is not TestStateConst.Running:
                self.close()
                break
            try:
                s = self.recvline()
            except socket.timeout:
                continue
            print s
            self.lines.append(s)
            if s.find("test_case_GW passed") != -1:
                self.state = TestStateConst.Passed

class PmaRunner(TestSshRunner):
    def __init__(self):
        super(PmaRunner, self).__init__("172.17.0.2", "root", "1")
        self.vgmAddr = "192.168.2.222"
    def run(self):
        self.state = TestStateConst.Running
        self.open()
        self.sendcmd('echo 5 > /tmp/xl4_log.conf')
        self.sendcmd('pkill pma')
        self.sendcmd("LD_LIBRARY_PATH=/tmp /tmp/pma -ip " + self.vgmAddr)
        while True:
            if self.state is not TestStateConst.Running:
                self.close()
                break
            try:
                s = self.recvline()
            except socket.timeout:
                continue
            self.lines.append(s)

pma = PmaRunner()
vgm = VgmTesterRunner(10000000)

class TestCaseRunNormal(TestCase):
    def __init__(self):
        self.buf = ""
    def start(self):
        self.state = TestStateConst.Passed
        vgm.start()
        pma.start()
        print "all tasks started"
        while True:
            if pma.state != TestStateConst.Running:
                break
            if vgm.state != TestStateConst.Running:
                pma.state = TestStateConst.Canceled
            time.sleep(1)
        print "all tasks stoped"
        self.state = vgm.state
        print str(self.__class__) + stateToStr(self.state)

class TestCaseNoDoipNack(TestCase):
    def __init__(self):
        pass
    def start(self):
        self.state = TestStateConst.Passed
        for line in pma.lines:
            if line.find("bytes: 02 fd 80 02") != -1 or \
            line.find("bytes: 02 fd 80 03") != -1:
                self.state = TestStateConst.Failed
        print str(self.__class__) + stateToStr(self.state)

class TestCaseBlockSize16k(TestCase):
    def __init__(self):
        pass
    def start(self):
        self.state = TestStateConst.Passed
        print str(self.__class__) + stateToStr(self.state)

class TestCaseDisconnect(TestCase):
    def __init__(self):
        pass
    def start(self):
        self.state = TestStateConst.Passed
        print str(self.__class__) + stateToStr(self.state)

class TestCaseRetryConnect(TestCase):
    def __init__(self):
        self.pma = PmaRunner()
    def start(self):
        self.state = TestStateConst.Passed
        vgm.stop()
        self.pma.start()
        print "pma started"
        duration = 8
        time.sleep(duration)
        self.pma.state = TestStateConst.Canceled
        print "pma stoped"
        retryCnt = 0
        secBegin = 0
        secEnd = 0
        for line in self.pma.lines:
            if line.find(self.failPatten) != -1:
                retryCnt += 1
                minute = int(line.split(":")[1])
                second = int(line.split(":")[2].split(".")[0])
                sec = minute*60+second
                if secBegin == 0:
                    secBegin = sec
                secEnd = sec
        duration = secEnd - secBegin
        print "%d times of retry seen"%retryCnt
        if retryCnt < 2:
            self.state = TestStateConst.Failed
        elif retryCnt < duration - 1 or retryCnt > duration + 1:
            print "expect %d"%duration + ", actual %d"%retryCnt
            self.state = TestStateConst.Failed
        print str(self.__class__) + stateToStr(self.state)

class TestCaseConnectionRefused(TestCaseRetryConnect):
    def __init__(self):
        super(TestCaseConnectionRefused, self).__init__()
        self.failPatten = "Connection refused"

class TestCaseUnreachable(TestCaseRetryConnect):
    def __init__(self):
        super(TestCaseUnreachable, self).__init__()
        self.failPatten = "connect timeout"
        self.pma.vgmAddr = "1.1.1.1"

testfile_lib = TestFile("/src/doip_visteon/libdoip.so", "/tmp/libdoip.so", "172.17.0.2", "root", "1")
testfile_pma = TestFile("/src/doip_visteon/apps/pma/pma", "/tmp/pma", "172.17.0.2", "root", "1")
testfile_vgm = TestFile("/src/doip_visteon/apps/vgm-tester/vgm", "/tmp/vgm", "192.168.2.222", "xl4", " ")

ts = TestSuite()
ts.testfile_add(testfile_lib)
ts.testfile_add(testfile_pma)
ts.testfile_add(testfile_vgm)
ts.setup()
ts.testcase_add(TestCaseRunNormal())
ts.testcase_add(TestCaseNoDoipNack())
ts.testcase_add(TestCaseBlockSize16k())
ts.testcase_add(TestCaseDisconnect())
ts.testcase_add(TestCaseConnectionRefused())
ts.testcase_add(TestCaseUnreachable())
ts.start()

