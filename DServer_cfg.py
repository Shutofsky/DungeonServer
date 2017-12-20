# -*- coding: utf-8 -*-
from tkinter import *
import paho.mqtt.client as mqtt
import socket, sqlite3, time
from datetime import datetime
from datetime import timedelta
#import image
#import Image
import time

dbName = 'DungeonStatus.db'
termWindow = []
menuFrame = []
menuLabel = []
menuBody = []
bodyFrame = []
bodyHead = []
bodyText = []
bodyScroll = []

i = 0
conn = sqlite3.connect(dbName)
req = conn.cursor()
for row in req.execute("SELECT * from term_status ORDER BY Id"):
    termWindow.append(Tk())
    termWindow[i].geometry('600x400')
    headTitle = u'Терминал ' + row[0]
    termWindow[i].title(headTitle)
    menuFrame.append(Frame(termWindow[i]))
    menuLabel.append(Label(menuFrame[i], text=u'Пункты меню'))
    menuBody.append(Entry(menuFrame[i], text = row[5]))
    menuFrame[i].grid(row=0, column=0)
    bodyFrame.append(Frame(termWindow[i]))
    bodyHead.append(Entry(bodyFrame[i], text=row[7]))
    bodyText.append(Text(bodyFrame[i], width=62, height=5, wrap=WORD, font='arial 8'))
    bodyText[i].insert(END, row[8])
    bodyScroll.append(Scrollbar(bodyFrame[i], command=bodyText[i].yview))
    bodyFrame[i].grid(row=1, column=0)
#    termLive[row[0]] = row[1]
#    termHack[row[0]] = row[2]
#    termLock[row[0]] = row[3]
#    termOper[row[0]] = row[4]
#    termMenu[row[0]] = row[5]
#    termMsgHead[row[0]] = row[7]
#    termMsgBody[row[0]] = row[8]
    i += 1

numTerms = i
conn.close()

i = 0
while i < numTerms:
    termWindow[i].mainloop()
    i += 1