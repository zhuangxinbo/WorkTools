#!/usr/bin/python
# -*- coding: UTF-8 -*-  


import ConfigParser
from prettytable import PrettyTable
import multiprocessing
from Tkinter import * 
import paramiko 
import os




envsinfo={} 
#global_table = multiprocessing.Queue(1024)
global_subprocess =multiprocessing.Queue(256)
global_table =PrettyTable(["Cloudname",  "IP", "Uptime","Status", "Build", ])
master = Tk()
master.title("Astro team NG")
master.maxsize(1408+128, 500) # 窗口大小
t = Text(master,width=1408+128)
global env_count
env_count=0

"""just a workaround for pyinstaller on multiprocess
    see "https://github.com/pyinstaller/pyinstaller/wiki/Recipe-Multiprocessing"
"""

try:
    # Python 3.4+
    if sys.platform.startswith('win'):
        import multiprocessing.popen_spawn_win32 as forking
    else:
        import multiprocessing.popen_fork as forking
except ImportError:
    import multiprocessing.forking as forking

if sys.platform.startswith('win'):
    # First define a modified version of Popen.
    class _Popen(forking.Popen):
        def __init__(self, *args, **kw):
            if hasattr(sys, 'frozen'):
                # We have to set original _MEIPASS2 value from sys._MEIPASS
                # to get --onefile mode working.
                os.putenv('_MEIPASS2', sys._MEIPASS)
            try:
                super(_Popen, self).__init__(*args, **kw)
            finally:
                if hasattr(sys, 'frozen'):
                    # On some platforms (e.g. AIX) 'os.unsetenv()' is not
                    # available. In those cases we cannot delete the variable
                    # but only set it to the empty string. The bootloader
                    # can handle this case.
                    if hasattr(os, 'unsetenv'):
                        os.unsetenv('_MEIPASS2')
                    else:
                        os.putenv('_MEIPASS2', '')

    # Second override 'Popen' class with our modified version.
    forking.Popen = _Popen

""" class useed for connecting openstack controller.
"""

class openstackSSH():
    """setuptest
    """
    def __init__(self):
        self.cloudSSH = paramiko.SSHClient()
        

    """teardown
    """
    def __del__(self):
        self.cloudSSH.close()

    """return cilent
    """
    def get_cilent(self):
        return self.cloudSSH

    """connect to openstack controller
    """
    def connect2cloud(self, ip, password):
        ret = True
        try:
            self.cloudSSH.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.cloudSSH.connect(ip, 22, "root", password)
           # paramiko.util.log_to_file("filename.log")
        except Exception, e:
            print "e:",e
            print "failed:connect to cloud controller \n"
            ret = False 
        return ret

    """execute command on cloud controller.
    """
    def execution_command_on_cloud(self, cmd):
        stdin, stdout, stderr = self.cloudSSH.exec_command(cmd)
        return stdin, stdout, stderr


""" class useed for connecting NG.
"""
class NGSSH:
    """setuptest
    """

    def __init__(self):
        self.NGSSH = paramiko.SSHClient()
        self.os_password = "abc123"


    """teardown
    """
    def __del__(self):
        self.NGSSH.close()

    """return cilent
    """
    def get_cilent(self):
        return self.NGSSH

    """connect to openstack controller
    """
    def connect2cloud(self, ip, password):
        
        ret = False
        try:
            self.NGSSH.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.NGSSH.connect(ip, 22, "root", password)
            #paramiko.util.log_to_file("filename.log")
            ret = True
        except Exception, e:
            print ip
            print "e:",e
            print "failed:connect to cloud ng \n"
            
        return ret

    """execute command on cloud ng.
    """
    def execution_command_on_cloud(self, cmd):
        stdin, stdout, stderr = self.NGSSH.exec_command(cmd)
        return stdin, stdout, stderr

""" Tools
"""
class EnvCollect:
    """collect basic infomation of Env
    """
      
    def __init__(self,NGinfo):
        
        self.envconfig = "./EnvConfig.conf"
        self.envsinfo = NGinfo
        self.ssh = openstackSSH()
        self.ngssh = NGSSH()


    """create ssh session through name
    """
    def create_ssh_session(self, envname="cloudwilson"):
        ip, password ,domain= self.envsinfo.get(envname)
        return self.ssh.connect2cloud(ip, password)
    
    """create ssh session through name
    """
    def create_ng_ssh_session(self, ip, password):
        return self.ngssh.connect2cloud(ip, password)
        
        
    def excution_cmd_on_ng(self,cmd):
        try:
            stin, stout, sterr = self.ngssh.execution_command_on_cloud(cmd)
            out = stout.readlines()
            # print out
            return out
        except:
            #print "stdin",stin
            #print "stderr",sterr
            self.ngssh.__del__
            return None
        
    """execute command on controller
    """
    def excution_cmd_on_controller(self,cmd):
        try:
            stin, stout, sterr = self.ssh.execution_command_on_cloud(cmd)
            out = stout.readlines()
            # print out
            return out
        except:
            print "stdin",stin.readlines()
            print "stderr",sterr.readlines()
            self.ssh.__del__
            return None
        
    """keystone authorization
    """
    def keystone_auth(self, cmd,envname="cloudwilson"):
        #self.create_ssh_session(envname)
        stdout =self.excution_cmd_on_controller("source keystonerc_%s;%s" % (envname,cmd))
        return stdout
    
    """check onde status in VM layer.If Instances has deleting status ,return false
    """        
    def _nova_check(self,novastatus):
        if len(novastatus) ==4:         # no nova deployed ,cinderstatus equal 4
            return False
        for onenode in novastatus:
                if (onenode.find("deleting") != -1 ) or (onenode.find("Error") != -1 ):
                    return False
        return True
    
    """check onde status in VM layer
    """
    def nova_check(self,env="cloudwilson"):
        stout = self.keystone_auth("nova list",env)
        if self._nova_check(stout):
            return True
        else:
            return False
    
    
    """check volumes deployed status.if cinder-list has "deleting",return false
    """        
    def _cinder_check(self,cinderstatus):
        if len(cinderstatus) ==4:        # no cinder deployed ,cinderstatus equal 4
            return False
        for onenode in cinderstatus:
                if (onenode.find("deleting") != -1 ) :
                    return False
        return True
    
    """check onde status in VM layer
    """
    def cinder_check(self,env="cloudwilson"):
        stout= self.keystone_auth("cinder list",env)
        if self._cinder_check(stout):
            return True
        else:
            return False
        
    
    """
        check NG use CAM?
    """    
    def _is_cam(self,envname): 
        if len(self.keystone_auth("nova list |grep CAM",envname)) ==0:
            return False
        else:
            return True
        

    """Get MN-0 IP
    """
    def _get_mn_0_ip(self, envname="cloudwilson"):
        NGdomain = self.envsinfo[envname][2]   
        if NGdomain == "NG2" or NGdomain == "cloud15":       # IN airfram NG2, we can get ip through 'nova list' 
            if self._is_cam(envname):
                IP = self.keystone_auth("nova list|grep 'MN-0'|egrep -o 'oam_external_net=.* ' |awk -F = '{print $2}' ",envname)
            else:
                # no use CAM
                IP = self.keystone_auth("nova list|grep 'MN-0'|egrep -o 'external_om_net=.* ' |awk -F = '{print $2}' ",envname)
        elif NGdomain == "cloud11" : # In cloud11, we can get ip through nova flaoting-ip-list by MN-0 id
            if self._is_cam(envname):
                IP = self.keystone_auth("nova list|grep 'MN-0'|egrep -o 'oam_external_net=.* ' |awk -F = '{print $2}' ",envname) 
            else:   
                mn_0_id = self.keystone_auth("nova list |grep MN-0 |awk -F \| '{print $2}'",envname)
                mn_0_id = mn_0_id[0].strip()
                IP = self.keystone_auth("nova floating-ip-list  |grep %s |awk -F \| '{print $2}'" % mn_0_id,envname)
        # print IP
        if len(IP) == 0:
            return None
        else:    
            return IP[0].strip()


    """ check NG connection
    """

    
    """Check VGP status
    """    
    def _check_VGP_plantform(self, envname="cloudwilson", ip=None):
        if ip is not None:
            node_vgp_status = self.excution_cmd_on_ng("cmmcli -g")
            if node_vgp_status != None:
                for node in node_vgp_status:
                    if node.find("rejected") != -1:
                        print ("%s:some nodes status is unaccept.Please connect to NG to check issue." %envname)
                        return False
                return True
            else:
                return False
            
    """Check NG version
    """      
    def _get_NG_version(self,envname="cloudwilson"):
        ng_version = self.excution_cmd_on_ng("nginfo --vv")
        # print ng_version
        # print "\n".join(ng_version)
        return "\n".join(ng_version)
    
    """
    """
    def _add_row_to_table(self, envname="cloudwilson"):
        self.table.add_row([envname, self._get_mn_0_ip(envname), "successful", self._get_NG_version(envname)])
    
    """display table
    """ 
    def ng_output_table(self):
        print (self.table)
    
    """check one NG infos via name
    """    
    def main_directly(self,envname):

        print "collecting %s ..." % envname
        self.create_ssh_session(envname)
        cinder_status = self.cinder_check(envname)
        nova_status = self.nova_check(envname)
        if cinder_status == True and nova_status == True:
            NGIP = self._get_mn_0_ip(envname)
            print "NGIP=%s"%NGIP
            if NGIP is None:
                self.table.add_row([envname, "NA", "Can't get NGIP", "NA"])
            else:
                if self._check_VGP_plantform(envname, NGIP):
                    # print "%s deploy successfully" % envname
                    self.table.add_row([envname, NGIP, "successful", self._get_NG_version(envname)])
                else:
                    # print "deploy failed due to VGP plantform issue,check cmmcli -g command"
                    self.table.add_row([envname, NGIP, "VGP issue", self._get_NG_version(envname)])
        
        elif (cinder_status == False and nova_status ==False):
            self.table.add_row([envname, "NA", "NG removed", "NA"])        
        else :
            self.table.add_row([envname, "NA", "under deploying", "NA"])
 
    
    """check running time
    """
    def _check_running_time(self):
        running_time = self.excution_cmd_on_ng("uptime | awk -F , '{print $1}' |cut -b 14-")
        return running_time[0]

        
        
    """check one NG infos via name
    """    
    def main_(self,envname,q,processQ):
        # test=["cloudkohottaret"]
        # for envname in self.envsinfo.keys():
        #print "collecting %s ..." % envname
        
        #print processQ

        paramiko.util.log_to_file("paramiko.log")
        self.create_ssh_session(envname)

        cinder_status = self.cinder_check(envname)
        nova_status = self.nova_check(envname)
        if cinder_status == True and nova_status == True:
            NGIP = self._get_mn_0_ip(envname)
            if NGIP is None:
                q.put([envname, "NA", "NA","Can't get NGIP", "NA"])
            else:
                if self.create_ng_ssh_session(NGIP,"rootme") == FALSE:
                    q.put([envname, NGIP , "NA", "Can't connect MN-0 ", "NA"])
                else:
                    if self._check_VGP_plantform(envname,NGIP) == True:
                        # print "%s deploy successfully" % envname
                        q.put([envname, NGIP, self._check_running_time(), "successful", self._get_NG_version(envname)])
                    else:
                        # print "deploy failed due to VGP plantform issue,check cmmcli -g command"
                        q.put([envname, NGIP, self._check_running_time(),"VGP issue", self._get_NG_version(envname)]) 
        elif (cinder_status == False and nova_status ==False):
            q.put([envname, "NA", "NA", "NG removed", "NA"])        
        else :
            q.put([envname, "NA", "NA", "under deploying", "NA"])
        processQ.put(envname)
 
    
    def no_sub(self):
        for envname in self.envsinfo.keys():
            self.main_directly(envname)
        self.ng_output_table()    
    


        
def work(msg,q,envsinfo,processQ):
    processWork = EnvCollect(envsinfo)
    processWork.main_(msg,q,processQ)


def info_by_name(envname, configHD):
    ip = configHD.get(envname, "controlIP")
    password = configHD.get(envname, "controlPASS")
    domain = configHD.get(envname, "env_domain")
    return ip, password, domain

def load_env_config(NGinfo):
    global env_count

    config = ConfigParser.ConfigParser()
    config.read("./EnvConfig.conf")
    envs = config.get("teamEnv", "envs")
    for env in envs.split(";"):
        NGinfo[env] = info_by_name(env, config)
        env_count = env_count +1
        #self._add_row_to_table(env)

    
def gui_process(Q,envcounter,NGinfoQ):
    t.pack()
    update_process(Q,envcounter,NGinfoQ)
    master.mainloop()    
    
def go(NGinfo):
    global env_count
    manager = multiprocessing.Manager()
    queue = manager.Queue()      
    processQ =manager.Queue() 

               
    pool = multiprocessing.Pool(processes =multiprocessing.cpu_count())
    pool.apply_async(gui_process, (processQ,env_count,queue))

    for envname in NGinfo.keys():
        pool.apply_async(work, (envname,queue,NGinfo,processQ))
    pool.close()
    pool.join()     
    
  
def update_process(Q,env_count,NGinfoQ):
    print env_count
    if not Q.empty():
        env = Q.get(True)
        #print "collectiong %s...\n" % env
        t.insert(CURRENT, "collecting %s's information completed\n" % env)
        t.update()
        env_count = env_count -1
        if env_count == 0:
            while True:
                if not NGinfoQ.empty():
                    row = NGinfoQ.get(True)
                    global_table.add_row(row)
                else:
                    break
            t.insert(INSERT, global_table)
            t.update_idletasks()
            print global_table
            
        master.after(5000,update_process,Q,env_count,NGinfoQ) #callback,5s
    else:
        master.after(5000,update_process,Q,env_count,NGinfoQ)
     


   
if __name__ == '__main__':
    multiprocessing.freeze_support()    #just for windows.
    load_env_config(envsinfo)  
    go(envsinfo) 
    
