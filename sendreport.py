#!/usr/bin/env python
# -*- coding: UTF-8 -*-  \
import os
import sys
import datetime
import smtplib
import ConfigParser
from email.mime.text import MIMEText
from email.header import Header
global TOASTROAD
global FROMADDR
global FROMUSER
global FROMSMTP
global FROMPASS

def LoadConfig(EmailConfigPath =sys.argv[2]):
    config = ConfigParser.ConfigParser()
    config.read(EmailConfigPath)
    global FROMADDR, FROMUSER, FROMSMTP, FROMPASS, TOASTROADDR
    FROMADDR = config.get("Email_SENDER", "FROMADDR")
    FROMUSER = config.get("Email_LOGINUSER","FROMAUSR" )
    FROMSMTP = config.get("Email_SMTP", "FROMASMTP")
    FROMPASS = config.get("Email_LOGINPSSS", "FROMAPASS")
    TOASTROADDR = config.get("Email_Receiver","TOASTROADDR")

def GetTime():
    now = datetime.datetime.now()
    return now.strftime('%Y-%m-%d')

def LoadHTML(HTMLpath):
    with open(HTMLpath,"rb") as fp:
        return fp.read()

def ConstrucEmailReport(emailContext, sendformat = "html"):
    global FROMADDR, FROMUSER, FROMSMTP, FROMPASS, TOASTROADDR
    msg = MIMEText(emailContext, sendformat, 'utf-8')
    msg['From'] = '%s <%s>' %(FROMADDR ,FROMADDR)
    msg['to'] = TOASTROADDR
    msg['Subject'] = Header(u'AATEReport on %s' %GetTime(), 'utf8').encode()
    return msg.as_string()

def SendAATEReport2Team(sendaddr, toGroupList, context):
    global FROMADDR, FROMUSER, FROMSMTP, FROMPASS, TOASTROADDR
    try:
        SendServer = smtplib.SMTP(FROMSMTP,25)
        SendServer.set_debuglevel(1)
        SendServer.login(FROMUSER, FROMPASS)
        SendServer.sendmail(sendaddr, toGroupList,  context)
    except Exception , e:
        print "%s Send Email to team failed due to SMTP connection,check you can login smtp.163.com port:25" %sendaddr
        print e
    finally:
        SendServer.quit()


if __name__ == '__main__':
    LoadConfig()
    context = ConstrucEmailReport(LoadHTML(sys.argv[1]))
    SendAATEReport2Team(FROMADDR, TOASTROADDR.split(";"), context)
