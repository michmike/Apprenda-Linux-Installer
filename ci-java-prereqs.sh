#!/bin/bash 
## runs artifact/stable copy of the prereq checker
## args: artifact version (defaulted to 5.0.Latest)
#####################

artifact_version=${1:-'5.0.Latest'}

#we'll already be in the bootstrap repo...
cd "./${artifact_version}"
python prereqChecker.py -v force
prereq_ret=$?

#remove all compiled python files
#... running from the share may eventually cause problems :-( 
rm -f ./*.pyc

#ensure state of some services
chkconfig iptables off; 
service iptables stop;

chkconfig cgconfig on; 
service cgconfig start;

exit $prereq_ret;
