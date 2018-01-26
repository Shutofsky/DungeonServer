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


def on_connect(client, userdata, flags, rc):
    client.subscribe("TERMASK/#")    # Подписка на канал TERMASK
    client.subscribe("LOCKASK/#")    # Подписка на канал LOCKASK
    client.subscribe("RGBASK/#")     # Подписка на канал LOCKASK

def on_message(client, userdata, msg):
    commList = str(msg.payload).split('/')  # Разделяем тело сообщения на элементы списка по знаку /
    # commList[0] - IP-адрес устройства, и т.д.
    if msg.topic == 'TERMASK':              # Сообщение пришло в канал TERMASK
	# Здесь должна быть обработка сообщений для канала TERMASK
    elif msg.topic == 'LOCKASK':
	# Здесь должна быть обработка сообщений для канала LOCKASK
    elif msg.topic == 'RGBASK':
	# Здесь должна быть обработка сообщений для канала RGBASK



client = mqtt.Client()   	# Создаём объект типа MQTT Client
client.on_connect = on_connect	# Привязываем функцию для исполнения при успешном соединении с сервером
client.on_message = on_message	# Привязываем функцию для исполнения при приходе сообщения в любом из подписанных каналов


try:  # Продбуем соединиться с сервером
    client.connect(mqtt_broker_ip, mqtt_broker_port, 5)	# Соединяемся с сервtром. Адрес, порт, таймаут попытки.
except BaseException:
    # Соединение не удалось!
    mqttFlag = 0
else:
    # Соединение успешно.
    mqttFlag = 1
    client.loop_start() # Клиентский цикл запустили - реконнект при разрыве связи и работа обработчика сообщений



while True :
    client.publish('TERM', "*/PING") # Запрос PING для всех терминалов (канал TERM)
    client.publish('LOCK', "*/PING") # Запрос PING для всех замков (канал LOCK)
    client.publish('RGB', "*/PING")  # Запрос PING для всех светильников (канал RGB)
    time.sleep(1) # Пауза одна секунда
