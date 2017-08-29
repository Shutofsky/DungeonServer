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
baseAlarmLevel = 0

termLive = dict()
lockLive = dict()
currentBaseStatus = ''
indexStatus = dict()
indexStatusReverse = dict()


start_time = datetime.now()
def millis():
    dt = datetime.now() - start_time
    ms = (dt.days * 24 * 60 * 60 + dt.seconds) * 1000 + dt.microseconds / 1000.0
    return ms

def getDBData():
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    for row in req.execute("SELECT Id, Alive FROM lock_status"):
        if row[1] == 'YES':
            lockLive[row[0]] = millis()
        else:
            lockLive[row[0]] = 0
    for row in req.execute("SELECT Id, Alive FROM term_status"):
        if row[1] == 'YES':
            termLive[row[0]] = millis()
        else:
            termLive[row[0]] = 0
    for row in req.execute("SELECT * from dict ORDER BY Id"):
        indexStatus[row[1]] = row[0]
        indexStatusReverse[row[0]] = row[1]
    conn.close()

def compareBase():
    global currentBaseStatus
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

            conn.commit()
    conn.close()

def compareTerm():
    termHackCurrent = dict()
    termLockCurrent = dict()
    termOperCurrent = dict()
    termMenuListCurrent = dict()
    termIdLockCurrent = dict()
    termMsgHeadCurrent = dict()
    termMsgBodyCurrent = dict()
    termHackRequest = dict()
    termLockRequest = dict()
    termMenuListRequest = dict()
    termIdLockRequest = dict()
    termMsgHeadRequest = dict()
    termMsgBodyRequest = dict()

    currentTime = millis()

    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    for row in req.execute("SELECT * FROM term_status"):
        termHackCurrent[row[0]] = row[2]
        termLockCurrent[row[0]] = row[3]
        termOperCurrent[row[0]] = row[4]
        termMenuListCurrent[row[0]] = row[5]
        termIdLockCurrent[row[0]] = row[6]
        termMsgHeadCurrent[row[0]] = row[7]
        termMsgBodyCurrent[row[0]] = row[8]
    for row in req.execute("SELECT * FROM term_action"):
        termHackRequest[row[0]] = row[1]
        termLockRequest[row[0]] = row[2]
        termMenuListRequest[row[0]] = row[3]
        termIdLockRequest[row[0]] = row[4]
        termMsgHeadRequest[row[0]] = row[5]
        termMsgBodyRequest[row[0]] = row[6]
    for ipAddr in termHackRequest.keys():
        if termLive[ipAddr] + 2000 < currentTime:
            req.execute("UPDATE term_status SET Alive = 'NO' WHERE Id == ?", [ipAddr])
        if termHackCurrent[ipAddr] != termHackRequest[ipAddr] :
            print "Changing hack status of terminal " + ipAddr + " to " + termHackRequest[ipAddr]
            # Terminal hacked. Write to log, count alarm status
            client.publish('TERM', ipAddr + "/HACK/" + termHackRequest[ipAddr])
            req.execute("UPDATE term_status SET Operation = 'UPDATE', Hack_status = ? WHERE Id == ?", \
                    [termHackRequest[ipAddr], ipAddr])
        if termLockCurrent[ipAddr] != termLockRequest[ipAddr] :
            print "Changing lock status of terminal " + ipAddr + " to " + termLockRequest[ipAddr]
            # Termial locked or unlocked. Write to log, count alarm status
            client.publish('TERM', ipAddr + "/LOCK/" + termLockRequest[ipAddr])
            req.execute("UPDATE term_status SET Operation = 'UPDATE', Lock_status = ? WHERE Id == ?", \
                        [termLockRequest[ipAddr],ipAddr])
        if termMenuListCurrent[ipAddr] != termMenuListRequest[ipAddr] :
            print "Changing menulist of terminal " + ipAddr + " to " + termMenuListRequest[ipAddr]
            # Termial menu changed. MQTT
            client.publish('TERM', ipAddr + "/MENULIST/" + termMenuListRequest[ipAddr])
            req.execute("UPDATE term_status SET Menulist = ? WHERE Id == ?", [termMenuListRequest[ipAddr],ipAddr])
        if termMsgHeadCurrent[ipAddr] != termMsgHeadRequest[ipAddr] :
            print "Changing message head of terminal " + ipAddr + " to " + termMsgHeadRequest[ipAddr]
            # Termial message header changed. MQTT
            client.publish('TERM', ipAddr + "/MAILHEAD/" + termMsgHeadRequest[ipAddr])
            req.execute("UPDATE term_status SET Msg_head = ? WHERE Id == ?", [termMsgHeadRequest[ipAddr],ipAddr])
        if termMsgBodyCurrent[ipAddr] != termMsgBodyRequest[ipAddr] :
            print "Changing message body of terminal " + ipAddr + " to " + termMsgBodyRequest[ipAddr]
            # Termial message changed. MQTT
            client.publish('TERM', ipAddr + "/MAILBODY/" + termMsgBodyRequest[ipAddr])
            req.execute("UPDATE term_status SET Msg_body = ? WHERE Id == ?", [termMsgBodyRequest[ipAddr],ipAddr])
        conn.commit()
    conn.close()

def on_connect(client, userdata, flags, rc):
    client.subscribe("TERMASK/#")
    client.subscribe("LOCKASK/#")
    client.subscribe("RGBASK/#")

def on_message(client, userdata, msg):
    global dbName
    global baseAlarmLevel
    termHackCurrent = dict()
    termLockCurrent = dict()
    termOperCurrent = dict()
    termMenuListCurrent = dict()
    termMsgHeadCurrent = dict()
    termMsgBodyCurrent = dict()
    termAliveCurrent = dict()
    commList = str(msg.payload).split('/')
    conn = sqlite3.connect(dbName)
    req = conn.cursor()
    for row in req.execute("SELECT * FROM term_status"):
        termAliveCurrent[row[0]] = row[1]
        termHackCurrent[row[0]] = row[2]
        termLockCurrent[row[0]] = row[3]
        termOperCurrent[row[0]] = row[4]
        termMenuListCurrent[row[0]] = row[5]
        termMsgHeadCurrent[row[0]] = row[7]
        termMsgBodyCurrent[row[0]] = row[8]
#    print str(msg.payload)
    if msg.topic == 'TERMASK':
        # commList [0] - ipAddress терминала
        # commList [1] - команда
        # commList [2] - значение
        conn = sqlite3.connect(dbName)
        req = conn.cursor()
        if commList[0] in termLive.keys():
            if commList[1] == 'PONG': # Терминал прислал подтверждение, что жив
#                print termAliveCurrent[commList[0]]
                termLive[commList[0]] = millis()
                req.execute("UPDATE term_status SET Alive = 'YES' WHERE Id == ?", [commList[0]])
                if termAliveCurrent[commList[0]] == 'NO':
#                    client.publish('TERM', commList[0] + "/HACK/" + termHackCurrent[commList[0]])
#                    client.publish('TERM', commList[0] + "/LOCK/" + termLockCurrent[commList[0]])
#                    client.publish('TERM', commList[0] + "/MENULIST/" + termMenuListCurrent[commList[0]])
#                    client.publish('TERM', commList[0] + "/MAILHEAD/" + termMsgHeadCurrent[commList[0]])
#                    client.publish('TERM', commList[0] + "/MAILBODY/" + termMsgBodyCurrent[commList[0]])
                    client.publish('TERM', commList[0] + "/GETDB")
            elif commList[1] == 'Hack_status': # Терминал докладывает о своём статусе взломан или нет
                if commList[2] == 'YES' and termHackCurrent[commList[0]] == 'NO':
                    # Взломали, добавляем к статусу тревоги 10
                    baseAlarmLevel += 10
                    req.execute("UPDATE base_status SET Alarm_level = ? ", [baseAlarmLevel])
                req.execute("UPDATE term_status SET Operation = 'UPDATE', Hack_status = ? WHERE Id == ?", \
                            [commList[2], commList[0]])
                req.execute("UPDATE term_action SET Hack_status = ? WHERE Id == ?", \
                        [commList[2], commList[0]])
            elif commList[1] == 'Lock_status': # Терминал докладывает о своём статусе блокирован или нет
                if commList[2] == 'YES' and termLockCurrentCurrent[commList[0]] == 'NO':
                    # Заблокирвоался терминал, добавляем к статусу тревоги 15
                    baseAlarmLevel += 15
                    req.execute("UPDATE base_status SET Alarm_level = ? ", [baseAlarmLevel])
                req.execute("UPDATE term_status SET Operation = 'UPDATE', Lock_status = ? WHERE Id == ?", \
                            [commList[2], commList[0]])
                req.execute("UPDATE term_action SET Lock_status = ? WHERE Id == ?", \
                            [commList[2], commList[0]])
            elif commList[1] == 'Menulist':
                req.execute("UPDATE term_status SET Operation = 'UPDATE', Menulist = ? WHERE Id == ?", \
                            [commList[2], commList[0]])
                req.execute("UPDATE term_action SET Menulist = ? WHERE Id == ?", \
                            [commList[2], commList[0]])
            elif commList[1] == 'Msg_head':
                req.execute("UPDATE term_status SET Operation = 'UPDATE', Msg_head = ? WHERE Id == ?", \
                            [commList[2].decode('utf-8'), commList[0]])
                req.execute("UPDATE term_action SET Msg_head = ? WHERE Id == ?", \
                            [commList[2].decode('utf-8'), commList[0]])
            elif commList[1] == 'Msg_body':
                req.execute("UPDATE term_status SET Operation = 'UPDATE', Msg_body = ? WHERE Id == ?", \
                            [commList[2].decode('utf-8'), commList[0]])
                req.execute("UPDATE term_action SET Msg_body = ? WHERE Id == ?", \
                            [commList[2].decode('utf-8'), commList[0]])
            elif commList[1] == 'DOLEVELDOWN':
                tmpStatus = indexStatus[currentBaseStatus]
                if tmpStatus == 4 or tmpStatus == 5:
                    req.execute("UPDATE base_action SET Current_status = ?", [indexStatusReverse[tmpStatus - 1]])
                    client.publish('TERM', commList[0] + "/ISLEVEL/YES")
            elif commList[1] == 'DOLOCKOPEN':
                req.execute("SELECT Id_lock FROM term_status WHERE Id == ?", [commList[0]])
                S = req.fetchone()
                req.execute("UPDATE lock_action SET Status = 'OPEN' WHERE ID == ?", [S[0]])
                client.publish('TERM', commList[0] + "/ISLOCK/YES")
        conn.commit()
        conn.close()
    elif msg.topic == 'LOCKASK':
        conn = sqlite3.connect(dbName)
        req = conn.cursor()
        if commList[0] in lockLive.keys():
            if commList[1] == 'PONG':
                lockLive[commList[0]] = millis()
                req.execute("UPDATE lock_status SET Alive = 'YES' WHERE Id == ?",[commList[0]])
            if commList[1] == 'OPENED':
                req.execute("UPDATE lock_status SET Status = 'OPEN' WHERE Id == ? ", [commList[0]])
            if commList[1] == 'CLOSED':
                req.execute("UPDATE lock_status SET Status = 'CLOSED' WHERE Id == ? ", [commList[0]])
            if commList[1] == 'BLOCKED':
                req.execute("UPDATE lock_status SET Status = 'BLOCKED' WHERE Id == ? ", [commList[0]])
            if commList[1] == 'CODE':
                dt = datetime.now()
                if commList[3] == 'WRONG':
                    # Неверная попытка. Добавляем 3 к уровню тревоги.
                    baseAlarmLevel += 3
                else:
                    # Верная попытка, замок открыт. Добавляем 1 к уровню тревоги.
                    baseAlarmLevel += 1
                req.execute("UPDATE base_status SET Alarm_level = ? ", [baseAlarmLevel])
                req.execute("INSERT INTO lock_log VALUES(?, ?, ?, ?)", \
                            (commList[0], dt.strftime("%A, %d. %B %Y %H:%M:%S"), commList[3], commList[2]))
        conn.commit()
        conn.close()

getDBData()

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(mqtt_broker_ip, mqtt_broker_port, 5)
client.loop_start()
sendPing = 0

while True :
    sendPing = (sendPing + 1) % 2
    if sendPing:
        client.publish('TERM', "*/PING")
    compareBase()
    compareLock()
    compareTerm()
    time.sleep(0.5)
