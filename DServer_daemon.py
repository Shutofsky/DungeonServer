# -*- coding: utf-8 -*-
from Tkinter import *
import paho.mqtt.client as mqtt
import socket, sqlite3, time
from datetime import datetime
from datetime import timedelta
#import image
import Image
import time

mqtt_broker_ip = '10.23.192.193'
mqtt_broker_port = 1883

dbName = 'DungeonStatus.db'

start_time = datetime.now()
def millis():
    dt = datetime.now() - start_time
    ms = (dt.days * 24 * 60 * 60 + dt.seconds) * 1000 + dt.microseconds / 1000.0
    return ms

def compareBase():
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    req.execute("SELECT * FROM base_status")
    S = req.fetchone()
    currentBaseStatus = str(S[0])
    req.execute("SELECT * FROM base_action")
    S = req.fetchone()
    requestBaseStatus = str(S[0])
    if requestBaseStatus != currentBaseStatus :
        print "Changing base status to " + requestBaseStatus
        # Write to MQTT devices - RGB, Terminalos, Locks
        req.execute("UPDATE base_status SET Current_status = ?", [requestBaseStatus])
        conn.commit()
    conn.close()

def compareLock():
    lockCurrent = dict()
    lockRequest = dict()
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    for row in req.execute("SELECT * FROM lock_status"):
        lockCurrent[row[0]] = row[2]
    for row in req.execute("SELECT * FROM lock_action"):
        lockRequest[row[0]] = row[1]
    for ipAddr in lockRequest.keys():
        if lockCurrent[ipAddr] != lockRequest[ipAddr] :
            print "Changing lock " + ipAddr + " status to " + lockRequest[ipAddr]
            # Write to MQTT lock
            req.execute("UPDATE lock_status SET Status = ? WHERE Id == ? ", [lockRequest[ipAddr], ipAddr])
            conn.commit()
    conn.close()

def compareTerm():
    termHackCurrent = dict()
    termLockCurrent = dict()
    termOperCurrent = dict()
    termResultCurrent = dict()
    termMenuListCurrent = dict()
    termIdLockCurrent = dict()
    termMsgHeadCurrent = dict()
    termMsgBodyCurrent = dict()
    termHackRequest = dict()
    termLockRequest = dict()
    termOperRequest = dict()
    termResultRequest = dict()
    termMenuListRequest = dict()
    termIdLockRequest = dict()
    termMsgHeadRequest = dict()
    termMsgBodyRequest = dict()
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    for row in req.execute("SELECT * FROM term_status"):
        termHackCurrent[row[0]] = row[2]
        termLockCurrent[row[0]] = row[3]
        termOperCurrent[row[0]] = row[4]
        termResultCurrent[row[0]] = row[5]
        termMenuListCurrent[row[0]] = row[6]
        termIdLockCurrent[row[0]] = row[7]
        termMsgHeadCurrent[row[0]] = row[8]
        termMsgBodyCurrent[row[0]] = row[9]
    for row in req.execute("SELECT * FROM term_action"):
        termHackRequest[row[0]] = row[1]
        termLockRequest[row[0]] = row[2]
        termOperRequest[row[0]] = row[3]
        termResultRequest[row[0]] = row[4]
        termMenuListRequest[row[0]] = row[5]
        termIdLockRequest[row[0]] = row[6]
        termMsgHeadRequest[row[0]] = row[7]
        termMsgBodyRequest[row[0]] = row[8]
    for ipAddr in termHackRequest.keys():
        if termHackCurrent[ipAddr] != termHackRequest[ipAddr] :
            print "Changing hack status of terminal " + ipAddr + " to " + termHackRequest[ipAddr]
            # Terminal hacked. Write to log, count alarm status
            req.execute("UPDATE term_status SET Operation = 'UPDATE', Hack_status = ? WHERE Id == ?", [termHackRequest[ipAddr],ipAddr])
        if termLockCurrent[ipAddr] != termLockRequest[ipAddr] :
            print "Changing lock status of terminal " + ipAddr + " to " + termLockRequest[ipAddr]
            # Termial locked or unlocked. Write to log, count alarm status
            req.execute("UPDATE term_status SET Operation = 'UPDATE', Lock_status = ? WHERE Id == ?", [termLockRequest[ipAddr],ipAddr])
        if termMenuListCurrent[ipAddr] != termMenuListRequest[ipAddr] :
            print "Changing menulist of terminal " + ipAddr + " to " + termMenuListRequest[ipAddr]
            # Termial menu changed. MQTT
            req.execute("UPDATE term_status SET Menulist = ? WHERE Id == ?", [termMenuListRequest[ipAddr],ipAddr])
        if termMsgHeadCurrent[ipAddr] != termMsgHeadRequest[ipAddr] :
            print "Changing message head of terminal " + ipAddr + " to " + termMsgHeadRequest[ipAddr]
            # Termial menu changed. MQTT
            req.execute("UPDATE term_status SET Msg_head = ? WHERE Id == ?", [termMsgHeadRequest[ipAddr],ipAddr])
        if termMsgBodyCurrent[ipAddr] != termMsgBodyRequest[ipAddr] :
            print "Changing message body of terminal " + ipAddr + " to " + termMsgBodyRequest[ipAddr]
            # Termial menu changed. MQTT
            req.execute("UPDATE term_status SET Msg_body = ? WHERE Id == ?", [termMsgBodyRequest[ipAddr],ipAddr])
        conn.commit()
    conn.close()

while True :
    compareBase()
    compareLock()
    compareTerm()
    time.sleep(0.5)
