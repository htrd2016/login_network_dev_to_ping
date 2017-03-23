import paramiko
import os
import sys
import time
import pexpect

user = sys.argv[1]
password = sys.argv[2]
ip_ping_from = sys.argv[3]
serverip =  sys.argv[4]
zabbixserverip = sys.argv[5]
time_interval = int(sys.argv[6])
config_file = sys.argv[7]
ssh_or_telnet = sys.argv[8]
device_type = sys.argv[9]

def read_config(file_name):
    file_object = open(file_name)
    ret_arr = []
    try:
        lines = file_object.readlines()
        for line in lines:
            line = line.replace('\n','')
            if(len(line)>0 and line[0] == '#'):
                continue
            line_arr = line.split('|', 2)
            if(len(line_arr)<=1):
                continue
            ret_arr.append(line_arr)
    finally:
        file_object.close()

    return ret_arr

def print_conf(arr):
    for line in arr:
      print line

def send_to_server(zabbixserverip, hostname, key, data):
    print("zabbix_sender -z "+ zabbixserverip +" -s "+hostname+" -k "+key+" -o "+str(data))
    os.system("zabbix_sender -z "+ zabbixserverip +" -s "+hostname+" -k "+key+" -o "+str(data))

def get_ping_percent(ssh, ip_ping_from, des_ip, device_type):
    print("this is get ping source")
    if(device_type == "asa"):
      ssh.sendline("ping %s %s" % (ip_ping_from,des_ip))
    else:
      ssh.sendline("ping %s source %s" % (des_ip, ip_ping_from))
    ssh.expect('#')
    data = ssh.before
    #print data
    
    indexStart = data.find("Success rate is ")
    indexEnd = data.find(" percent");
    if (indexStart>0 and indexEnd>0):
#        print(indexStart)
#        print(indexEnd)
        indexStart+=16
        per = data[indexStart:indexEnd]
#        print(per.strip())
        return int(per.strip())
        #os.system("zabbix_sender -z " + zabbixserverip + " -s \""+hostname+"\" -k sender.ping.mc -o "+per.strip())

    print("error:%s" % data)
    return -1

if __name__ == '__main__':
    ret_arr = read_config(config_file)
    print print_conf(ret_arr)

    ssh_newkey = 'Are you sure you want to continue connecting'
    if(ssh_or_telnet != "ssh"):
       ssh = pexpect.spawn("telnet %s" % (serverip))
    else:
       ssh = pexpect.spawn("ssh %s@%s" % (user, serverip))
    try:
        if(ssh_or_telnet != "ssh"):
          ssh.expect(['Username: '])
          ssh.sendline(user)
        ssh.expect(['Password: ','password'])
        ssh.sendline(password)
        ssh.expect('>')
        ssh.sendline("enable")
        print ssh.before
        ssh.expect(['Password: '])
        ssh.sendline(password)
        ssh.expect('#')
    except pexpect.EOF: 
        print "EOF"
        ssh.close() 
    except pexpect.TIMEOUT: 
        print "TIMEOUT"
        ssh.close() 

    sucess = 1
    while True:
        for host in ret_arr:
            if(host is None):
               continue

            percent = get_ping_percent(ssh, ip_ping_from, host[0], device_type)
            print percent
            if (-1 == percent):
              sucess = 0
              break

            send_to_server(zabbixserverip, host[1], host[2], 100-percent)
        if(sucess == 0):
          time.sleep(100) 
          
        time.sleep(0.001*time_interval)
        
    ssh.close()
