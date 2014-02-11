#!/bin/bash 
## ensures the bootstrap repo is mounted and persisted
#####################

CI_MOUNT_USER='apprendabuild'
CI_MOUNT_PASS='@ppd3v12'


if [ -e './ci-functions' ]; then 
 . ./ci-functions

else
 echo 'error: could not find ci-functions';
 exit 1;
fi;


#####################

safe_mount_share "${CI_BOOTS_SHARE}" "${CI_BOOTS_PATH}" 
func_ret=$?
if [ $func_ret -ne 0 ]; then 
 echo '===!!=== ERROR: ci-init-bootstrap: safe_mount_share() failed ===!!===';
 exit 1;
fi;


safe_persist_mount "${CI_BOOTS_SHARE}" "${CI_BOOTS_PATH}" 
func_ret=$?
if [ $func_ret -ne 0 ]; then 
 echo '===!!=== ERROR: ci-init-bootstrap: safe_persist_mount() failed ===!!===';
 exit 1;
fi;

echo 'ci-init-bootstrap successful';
exit 0

