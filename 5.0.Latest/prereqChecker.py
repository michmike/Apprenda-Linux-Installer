import sys
import subprocess
import functools
import socket
import os
import hostconfig
from hostconfig import *
import argparse

def getInput(message, default):
    returnVal = ''
    while True:
        if default is None:
            val = raw_input(' -> ' + message + ': ')
        else:
            val = raw_input(' -> ' + message + ' [' + default + ']: ')

        if len(val) > 0:
            returnVal = val
            break
        else:
            if default is None:
                print ' ** You must provide a value for ' + message
            else:
                returnVal = default
                break

    return returnVal

def confirm(message):
    confirm = getInput(message, "n" )
    if confirm.lower() == "y":
        return True
    else:
        return False

class PrereqValidator(object):
    def __init__(self, hostConfig,infoOut = sys.stdout, errOut = sys.stderr):
        # The host configuration to validate
        self.hostConfig = hostConfig
        # The stream to write to for informational messages and interactions
        self.out = infoOut
        # The stream to write to for errors
        self.err = errOut
        
    def hasPrivileges(self):
        return os.geteuid() == 0   
    
    def hasRequiredConfigs(self):
        return self.hostConfig.hasRequiredConfigs()

    def hasRequiredLibs(self):
        return self.hostConfig.hasRequiredLibs()

    def isValid(self):
        return self.hasPrivileges() and self.hostConfig.isValid()        
     
    def printSuccess(self):
        self.out.write("\n--------------------------------------------------------------------\n")
        self.out.write("All libraries and configuration settings applied. Install Apprenda !\n")
        self.out.write("--------------------------------------------------------------------\n")
     
    def printFailure(self):
        self.err.write("\n--------------------------------------------------------------------\n")
        self.err.write("Prerequisite checking failed !!!  Re-run or correct manually before trying to install Apprenda\n")
        self.err.write("--------------------------------------------------------------------\n")
     
    def printStatus(self): 
        self.printRequiredPrivs()
        self.printRequiredLibs()
        self.printRequiredConfigs()
        
    def printRequiredPrivs(self):    
        if not self.hasPrivileges():
            self.err.write("\nThe prerequisite installation needs to be run with root privileges\n")
        
    def tagRequiredPrivs(self):
        self.err.write('<Error errorCode="LINUX_BADPRIVILEGE">\
            The prerequisite installation needs to be run with root privileges</Error>')

    def printRequiredConfigs(self):
        reqConfs =  self.hostConfig.checkRequiredConfigs()
        if reqConfs:
            self.out.write("\nInvalid system configurations:\n")
            for cfg in reqConfs:
                self.out.write("* {1}\n".format(cfg.name,cfg.message))   
     
    def tagRequiredConfigs(self):
        reqConfs = self.hostConfig.checkRequiredConfigs()
        for cfg in reqConfs:
            self.out.write('<Error errorCode="LINUX_INVALIDSYSTEMCONFIG"> {1}</Error>\n'.format(cfg.name, cfg.message))

    def printRequiredLibs(self):
        reqLibs = self.hostConfig.checkRequiredLibs()
        if reqLibs:
            self.out.write("\nRequired libraries:\n")
            for lib in reqLibs:
                self.out.write("* " + lib + "\n")          

    def tagRequiredLibs(self):
        reqLibs = self.hostConfig.checkRequiredLibs()
        for lib in reqLibs:
            self.out.write('<Error errorCode="LINUX_LIBNOTINSTALLED">Required library: '+lib+' not installed</Error>\n')


if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Checks and installs Apprenda installation prerequisites',add_help=True)
    parser.add_argument('mode',  help="Interaction mode", choices=["checkonly","interactive","bulk","force"])
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='output information to STDOUT about the install process')
    #parser.add_argument('--distro', help='Linux distro family ', choices=["RedHat","Debian"],default="RedHat")
    parser.add_argument('--version', help='Distro version')

    args = parser.parse_args()
    interactive = args.mode.lower() == 'interactive'
    bulk = args.mode.lower() == 'bulk'
    checkOnly = args.mode.lower() == 'checkonly'
    force = args.mode.lower() == 'force'
    distro = LinuxFamily.RedHat #args.distro

    validator = PrereqValidator(hostconfig.getConfig(distro))
    # ----------- Run it !!! --------------------------------
    if checkOnly:
        print "Checking system configuration, no changes are applied\n"

        if  not validator.isValid():
            validator.printStatus()
            validator.printFailure()
            sys.exit(1)
        else:
            validator.printSuccess()
            sys.exit(0)
    else:
        if not validator.hasPrivileges():
            validator.printRequiresPrivs()
            sys.exit(1)

        if force:
            validator.printStatus()
            validator.hostConfig.applyRequired()
                            
        elif interactive:
            for lib in validator.hostConfig.checkRequiredLibs():
                if confirm("Library {0} missing from installation. Install ? ".format(lib)):
                    validator.hostConfig.installLib(lib)

            for config in validator.hostConfig.checkRequiredConfigs():
                if confirm("{1} - Failed. Fix ?".format(config.name,config.message)):
                    config.fix()

        elif bulk:
            if validator.hostConfig.checkRequiredLibs():
                validator.printRequiredLibs()

                if confirm("Would you like to fix all missing libraries?"):
                    validator.hostConfig.applyRequiredLibs()

            if validator.hostConfig.checkRequiredConfigs():
                validator.printRequiredConfigs()

                if confirm("Would you like to fix all invalid configurations?"):
                    validator.hostConfig.applyRequiredConfigs()

        else:
            sys.exit("Either interactive or bulk fixing needs to be picked")

        if validator.isValid():
            validator.printSuccess()
            sys.exit(0)
        else:
            validator.printStatus()
            validator.printFailure()
            sys.exit(1)
