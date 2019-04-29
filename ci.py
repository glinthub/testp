#!/usr/bin/python

import time
import threading
import socket
import os
import commands
import datetime

import paramiko

class TestStateConst:
    Idle = 0
    Running = 1
    Passed = 2
    Failed = 3
    Canceled = 4

def stateToStr(state):
    if state == TestStateConst.Idle:
        return "idle"
    if state == TestStateConst.Running:
        return "running"
    if state == TestStateConst.Passed:
        return "passed"
    if state == TestStateConst.Failed:
        return "failed"
    if state == TestStateConst.Canceled:
        return "canceled"
    return "unknown"

class TestServer:
    def __init__(self, ipaddr, username, password):
        self.ipaddr = ipaddr
        self.username = username
        self.password = password

class TestDockerContainer(TestServer):
    def __init__(self, image, name, username, password):
        self.image = image
        self.name = name
        self.username = username
        self.password = password
        self.ipaddr = ""

    def start(self):
        cmd = "docker run -it -d --rm --name " + self.name + " " + self.image
        print cmd
        os.system(cmd)
        self.getIpAddr()
        self.startSshServer()

    def startSshServer(self):
        cmd = "docker exec " + self.name + " service ssh start"
        print cmd
        os.system(cmd)

    def getIpAddr(self):
        cmd = "docker exec " + self.name + " ifconfig eth0 | grep netmask | awk {'print $2;'}"
        print cmd
        self.ipaddr = commands.getoutput(cmd)
        print self.ipaddr

    def stop(self):
        cmd = "docker stop " + self.name
        print cmd
        os.system(cmd)

class TestRunner(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        pass
    def open(self):
        pass
    def close(self):
        pass
    def sendcmd(self, cmd):
        pass
    def recvline(self):
        pass

class TestRunnerSsh(TestRunner):
    def __init__(self,server):
        super(TestRunnerSsh, self).__init__()
        self.recvbuf = ""
        self.client = paramiko.SSHClient()
        self.lines = []
        self.state = TestStateConst.Idle
        self.server = server
    def connect(self):
        client = self.client
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(self.server.ipaddr, username=self.server.username, password=self.server.password)
    def openshell(self):
        self.ch = self.client.invoke_shell()
        self.ch.settimeout(1)
    def open(self):
        self.connect()
        self.openshell()
        time.sleep(1)
    def close(self):
        self.ch.close()
        self.client.close()
    def sendcmd(self, cmd):
        self.ch.send(cmd+"\n")
    def recvline(self):
        buf = self.recvbuf
        while True:
            pos = buf.find("\n")
            if pos is not -1:
                for line in buf.split("\n"):
                    if len(line) is not 0:
                        self.recvbuf = buf[pos+1:]
                        self.lines.append(line)
                        return line
            else:
                recv = self.ch.recv(100)
                buf += recv
    def run(self):
        pass

class TestFile:
    def __init__(self, localpath):
        self.localpath = localpath
    def deploy(self, server, remotepath):
        t = paramiko.transport.Transport(server.ipaddr) #establish connection
        t.connect(username=server.username, password=server.password)
        f = paramiko.sftp_client.SFTPClient.from_transport(t)
        try:
            f.remove(remotepath)
        except IOError:
            pass
        f.put(self.localpath, remotepath)
        f.chmod(remotepath, 0755)
        f.close()
        t.close()

class TestCase(object):
    def __init__(self):
        self.name = str(self.__class__.__name__)
        self.desc = "description not available yet"
        self.state = TestStateConst.Idle
    def execute(self):
        pass
    def verify(self):
        pass
    def genReport(self, outputfile):
        pass

class TestSuite:
    def __init__(self, name):
        self.name = name
        self.testcases = []
        self.testfiles = []
        self.testservers = []
        self.testrunners = []
    def testfile_add(self, tf):
        self.testfiles.append(tf)
    def setup(self):
        for tf in self.testfiles:
            tf.deploy()
    def testcase_add(self, tc):
        self.testcases.append(tc)
    def execute(self):
        for tc in self.testcases:
            tc.execute()
    def genReport(self):
        filename = self.name.replace(" ", "_") + ".html"
        f = open(filename, "w+")
        f.writelines('<html>')
        f.write('<head>')
        f.write('<style type="text/css">')
        f.write('div.testcase {text-align: left;color: blue;}')
        f.write('</style>')
        f.write('</head>')
        f.write('<body>')
        f.write("<center><h1>" + self.name + " Report</h1></center>")
        f.write("<center>(Auto-generated at " + str(datetime.datetime.now()) + ")</center>")
        f.write("<hr>\n")

        #Cases
        f.write("<h2>1. Test Cases</h2>\n")
        subSection = 1
        for tc in self.testcases:
            f.write("<h3>1." + str(subSection) + " " + tc.name + "</h3>\n")
            f.write("<p>"+tc.desc+"</p>\n")
            stateColor = "orange"
            if tc.state == TestStateConst.Passed:
                stateColor = "green"
            if tc.state == TestStateConst.Failed:
                stateColor = "red"
            f.write("<font color=" + stateColor + ">\n" + stateToStr(tc.state) + "</font>")
            tc.genReport(f)
            subSection += 1

        #Logs
        f.write("<h2>2. Test Logs</h2>\n")
        subSection = 1
        for tr in self.testrunners:
            f.write("<h3>2." + str(subSection) + " Test Log " + str(tr.__class__.__name__) + "</h3>\n")
            f.write("<pre>")
            for line in tr.lines:
                f.write(line + "\n")
            f.write("</pre>\n")
            subSection += 1

        f.write("</body>")
        f.write("</html>")
        f.close()

        filename = "'" + filename + "'"
        cmd = "md5sum " + filename
        print cmd
        md5 = commands.getoutput(cmd).split()[0]
        print "md5: " + md5
        offset = 0
        mdx = ""
        while offset <= len(md5) - 1:
            b = md5[offset:offset+1]
            n = int(b, 16)
            mdx += hex((n*3+offset) % 16)[2:3]
            offset += 1
        print "mdx: " + mdx

        cmd = "sed -i 's|</body></html>|Document fingerprint: " + mdx+ "\\0|g' " + filename
        print cmd
        os.system(cmd)

