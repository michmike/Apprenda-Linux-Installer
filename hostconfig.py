import sys
import subprocess
import functools
import socket
import os
import shutil
import time
import fileinput
import logging


FNULL = open(os.devnull, 'w')
logger = logging.getLogger(__name__)

class LinuxHostConfig(object):
    def __init__(self, family):
        self.family = family
        self.requiredLibs = []
        self.configRules = []


    def checkRequiredConfigs(self):
        return [cfg for cfg in self.configRules if not cfg.check()]

    def checkRequiredLibs(self):
        return [lib for lib in self.requiredLibs if self.isLibInstalled(lib) ]

    def hasRequiredConfigs(self):
        return len(self.checkRequiredConfigs()) == 0

    def hasRequiredLibs(self):
        return len(self.checkRequiredLibs()) == 0

    def isValid(self):
        return len(self.checkRequiredConfigs())== 0 and len(self.checkRequiredLibs())==0

    def applyRequiredLibs(self):
        for lib in self.checkRequiredLibs():
            self.installLib(lib)


    def applyRequiredConfigs(self):
        for cfg in self.checkRequiredConfigs():
            cfg.fix()
    
    def applyRequired(self):
        self.applyRequiredLibs()
        self.applyRequiredConfigs()
        
    def isLibInstalled(self,libName):
        return False;

    def installLib(self,libName):
        pass




class RedHatDerivedConfig(LinuxHostConfig):
     pkgMgr = "yum"
     def __init__(self):
         super(RedHatDerivedConfig,self).__init__(LinuxFamily.RedHat)

     def installLib(self,libName):
         cmd = "{0} install -y {1}".format(RedHatDerivedConfig.pkgMgr,libName)
         exitCode = subprocess.check_call(cmd,shell=True,stdout=FNULL, stderr=subprocess.STDOUT)


     def isLibInstalled(self,libName):
         libCmd = "rpm -qa | grep {0}".format(libName)
         logger.debug("Checking if %s is installed :\n %s\n",libName,libCmd)
         exitCode = subprocess.call(libCmd,shell=True,stdout=FNULL, stderr=subprocess.STDOUT)
         return exitCode!=0


class DebianDerivedConfig(LinuxHostConfig):
    pkgMgr = "apt-get"
    def __init__(self):
        super(DebianDerivedConfig,self).__init__(LinuxFamily.RedHat)

    def _installLib(self,libName):
        cmd = "{0} install {1}".format(DebianDerivedConfig.pkgMgr,libName)
        exitCode = subprocess.call([DebianDerivedConfig.pkgMgr,"install","-y",libName],stdout=FNULL, stderr=subprocess.STDOUT)
        return exitCode!=0
    
    def isLibInstalled(self,libName):
         libCmd = "dpkg -l | grep {0}".format(libName)
         #print "Checking if {0} is installed :\n {1}\n".format(libName,libCmd)
         exitCode = subprocess.call(libCmd,shell=True,stdout=FNULL, stderr=subprocess.STDOUT)
         return exitCode!=0

class LinuxFamily:
    RedHat = "RedHat"
    Debian =  "Debian"


class ConfigRule(object):
    def __init__(self,name,message,checkAction=None,fixAction=None):
        self.name = name
        self.message = message
        if checkAction is not None:
            self.checkAction = checkAction
        else:
            self.checkAction = self._doNothing

        if fixAction is not None:
            self.fixAction = fixAction
        else:
            self.fixAction = self._doNothing

    def check(self):
        return self.checkAction()

    def fix(self):
        return self.fixAction()

    def _doNothing(self):
        logger.debug(self.message)
        logger.debug("\nDoing nothing as requested for rule {0} \n",self.name)
        pass

class ShellRunnerConfigRule(ConfigRule):
    def __init__(self,name,message,checkCmd,fixCmd):
        ConfigRule.__init__(self,name,message,functools.partial(self.runShellCmd,checkCmd),functools.partial(self.runShellCmd,fixCmd))

    def runShellCmd(self,shellCmd):
        logger.debug("\nRunning command %s",shellCmd)
        return shellCmd.check()

class ShellCmd(object):
    def __init__(self,cmd,output=None,exitCode=0):
        self.cmd = cmd
        self.output = output
        self.exitCode = exitCode

    def check(self):
        if self.output is None:
            # we only care about the exit code
            exCode  = subprocess.call(self.cmd,shell=True,stdout=FNULL, stderr=subprocess.STDOUT)
            return  exCode==self.exitCode
        else:
            # it would be nice to call subprocess.check_output however that's not available until py 2.7.. shoot
            process = subprocess.Popen(self.cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE,shell=True)
            procOut,exitCode = process.communicate()
            return procOut.rstrip() == self.output.rstrip()


def checkHostname():
    hostname = socket.gethostname()
    try:
        host = socket.gethostbyname(hostname)
        logger.debug("Successfully resolved %s to ip %s",hostname,host)
        return True
    except:
        logger.debug("Failed to resolve hostname %s",hostname)
        return False

def fixHostname():
    hostname = socket.gethostname()
    shutil.copyfile("/etc/hosts","/etc/hosts.bak."+str(time.time()))
    for line in fileinput.input("/etc/hosts",inplace=1):
        if "127.0.0.1" in line and hostname not in line:
            # Fileinput redirects stdout to the file
            print line.rstrip() + " " + hostname + "\n"

def buildRedhatConfig():
    hostConfig =  RedHatDerivedConfig()
    hostConfig.requiredLibs = ["cifs-utils", "unzip", "libcgroup","openssh-clients"]
    hostConfig.configRules = [
        ShellRunnerConfigRule(
            "iptables",
            "Ensure that iptables or other firewall is disabled and not running",
            ShellCmd(cmd="service iptables status",exitCode=3),
            ShellCmd(cmd="service iptables stop; /sbin/chkconfig iptables off")
        ),
        ConfigRule(
            "hostname resolvable",
            "Check if the hostname is resolvable to itself",
            checkHostname,
            fixHostname
        ),
        ShellRunnerConfigRule(
            "cgroups enabled",
            "Check that cgconfig is enabled and running",
            ShellCmd(cmd="service cgconfig status",output="Running"),
            ShellCmd("service cgconfig restart; /sbin/chkconfig cgconfig on")
        )
    ]
    return hostConfig

def buildDebianConfig():
    hostConfig =  DebianDerivedConfig()
    hostConfig.requiredLibs = ["cifs-utils", "unzip","cgroup-bin","libcgroup1","openssh-client"]
    hostConfig.configRules = [
        ShellRunnerConfigRule(
            "iptables",
            "Ensure that iptables or other firewall is disabled and not running",
            ShellCmd(cmd="ufw status",output="Status: inactive"),
            ShellCmd(cmd="ufw disable")
        ),
        ConfigRule(
            "hostname resolvable",
            "Check if the hostname is resolvable to itself",
            checkHostname,
            fixHostname
        ),
        ShellRunnerConfigRule(
            "cgroups enabled",
            "Check that cgconfig is enabled and running",
            ShellCmd(cmd="service cgconfig status",output="cgconfig start/running"),
            ShellCmd("service cgconfig restart; /sbin/chkconfig cgconfig on")
        )
    ]
    return hostConfig

supportedConfigs = {}
supportedConfigs[LinuxFamily.RedHat] = buildRedhatConfig()
#supportedConfigs[LinuxFamily.Debian] = buildDebianConfig()

def getConfig(family,version=None):
    # This should somehow support overriding version configuration, skip for now
    return supportedConfigs[family]














