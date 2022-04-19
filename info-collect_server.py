(''')
Info collection V1
Author: huasu@juniper.net
A.Purpose of this script

This script is to simplfy the info collection while opening ticket with Nera.

B. Instructions
b1: Below configuration need to commit on device
set system services netconf ssh  

b2: python and pyez module need to be installed on server.
* Install python3 on server
* pip3 install junos-eznc  <<<install pyez
https://www.juniper.net/documentation/us/en/software/junos-pyez/junos-pyez-developer/topics/task/junos-pyez-server-installing.html

b3: run the script
server$ python3 info-collect_server.py 

example:
[huasu@pinkie ~]$ python info-collect_server.py 
device name: lab-mx960-3D-02
username: nera
password: 


C: Other requirements:

a. User should key in the crendetial with  startshell privilidge.

b. This script would roughly take 120 seconds to finish, be patient please.

c. Three files will be generated on network devices and local server at /var/tmp respectively, named rsi.txt, master_re_var_log.tgz and backup_re_var_log.tgz. 

d. For singtel RE device, two files will be generated on network devices and local server at /var/tmp respectively, named rsi.txt, master_re_var_log.tgz 

d. Above files in part c will be overwritten while excecute the script next time, so that disk space won't grow infinitely.


(''')


from jnpr.junos import Device

from lxml import etree
from jnpr.junos.utils.fs import FS
from getpass import getpass
import sys

device_name = input("device name: ")
user = input("username: ")
junos_password = getpass("password: ",stream=None)

dev = Device(host=device_name,user=user,password=junos_password,gather_facts=False) 
#dev = Device(host='lab-mx480-3d-02',user='user',password=junos_password,gather_facts=False) #replace with your ip and credential

dev.open()

#rsi = dev.rpc.get_support_information({'format':'text'}, dev_timeout=300)

#f = open('/var/tmp/rsi.txt', 'w')
#f.write(etree.tostring(rsi))
#f.close()


fs = FS(dev)
#fs.tgz("/var/tmp/rsi.txt","/var/tmp/rsi.txt.tgz")
fs.tgz("/var/log/", "/var/tmp/master_re_var_log.tgz")

# Need to use starshell to archieve file copy and compress in backup RE
from jnpr.junos.utils.start_shell import StartShell 
ss = StartShell(dev)
ss.open()

ss.run('cli -c "request support information | save /var/tmp/rsi.txt"')
ss.run('cli -c "request routing-engine login backup"')
ss.run("file archive compress source /var/log destination /var/tmp/backup_re_var_log",">")
ss.run("file copy /var/tmp/backup_re_var_log.tgz re0:/var/tmp",">")
ss.run("file copy /var/tmp/backup_re_var_log.tgz re1:/var/tmp",">")
ss.run("exit",">")
fl = ss.run('ls -l /var/tmp/*re_var_log.tgz')
md5 = ss.run('md5 /var/tmp/*re_var_log.tgz')
print (fl) #list out all tgz files under /var/tmp
print (md5) #list out all tgz files with md5 under /var/tmp
ss.close()


from jnpr.junos.utils.scp import SCP


with SCP(dev, progress=True) as scp:
	scp.get ('/var/tmp/rsi.txt', local_path='/var/tmp')
	scp.get ('/var/tmp/master_re_var_log.tgz', local_path='/var/tmp')
	scp.get ('/var/tmp/backup_re_var_log.tgz', local_path='/var/tmp')

dev.close()