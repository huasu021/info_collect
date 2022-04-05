(''')
Info collection V1
Author: huasu@juniper.net
A.Purpose of this script

This script is to simply info collection while open ticket with Nera.

B. Instructions
b1: Below configuration need to commit on device
set system scripts op file info_collect.py
set system scripts language python

b2: Copy this script to RE0 and RE1 at /var/db/script/op directory respectively.

b3: This python on-box script need to be modified before use:
a1. replace router's IP, username and password in this line with correct one e.g dev = Device(host='172.16.99.37',user='huasu',password='juniper123')

C: Other requirements:

a. User in part a1 should have startshell privilidge, otherwise /var/log file on backup RE would not be able to generate. 

b. This script would roughly take 90 seconds to finish, be patient please.

c. Three tgz files will be generated at /var/tmp/ in master RE, named rsi.txt.tgz, master_re_var_log.tgz and backup_re_var_log.tgz. 

d. Above files in part c will be overwritten while excecute the script next time, so that disk space won't grow infinitely.

e. Junos version need to be above 16.1
(''')


from jnpr.junos import Device
from lxml import etree
from jnpr.junos.utils.fs import FS
dev = Device(host='172.16.99.37',user='lab',password='lab123',gather_facts=False) #replace with your ip and credential
dev.open()

rsi = dev.rpc.get_support_information({'format':'text'}, dev_timeout=300)

f = open('/var/tmp/rsi.txt', 'w')
f.write(etree.tostring(rsi))
f.close()


fs = FS(dev)
fs.tgz("/var/tmp/rsi.txt","/var/tmp/rsi.txt.tgz")
fs.tgz("/var/log/", "/var/tmp/master_re_var_log.tgz")

from jnpr.junos.utils.start_shell import StartShell 
ss = StartShell(dev)
ss.open()
#ss.run('cli','>')
#ss.run('request routing-engine login backup')

ss.run('cli -c "request routing-engine login backup"')
ss.run("file archive compress source /var/log destination /var/tmp/backup_re_var_log",">")
ss.run("file copy /var/tmp/backup_re_var_log.tgz re0:/var/tmp",">")
ss.run("file copy /var/tmp/backup_re_var_log.tgz re1:/var/tmp",">")
ss.run("exit",">")
fl = ss.run('ls -l /var/tmp/*.tgz')
md5 = ss.run('md5 /var/tmp/*.tgz')
print fl
print md5
ss.close()
dev.close()