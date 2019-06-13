#Client
COD='utf-8'

import time
import sys
import logging
import log.user_log_config
import threading

from socket import *
from utils import*
from datetime import datetime
from deco import mylog


logger = logging.getLogger('user')

def read_messages(client):
      while True:
            try:
                  message=get_msg(client.recv(1024),COD)
                  print(f"{message['From']} {message['Text']}")
            except:
                  print('read_messages')

def create_message(message_to, text, account_name='Guest'):
      return {'Time':time.time(), 'To':message_to,'From':account_name,'Text':text}


@mylog
def create_presence(status,user='Guest'):
      data=datetime.today().strftime('%d/%m/%Y')
      message={
            'status':status,
            'data':data,
            'user':user
            }
      logger.info(f"{create_presence.__name__}-{message}")
      return message
            

if __name__=='__main__':
      s=socket(AF_INET,SOCK_STREAM)
      
      try:
            host=sys.argv[1]
      except IndexError:
            host='localhost'
      try:
            port=int(sys.argv[2])

      except IndexError:
            port=8888
      try:
            mode = sys.argv[3]
      except IndexError:
            mode = 'r'
      try:
            account_name = sys.argv[4]
            print(account_name)
      except IndexError:
            print('Укажите получателя')

      s.connect((host,port))
      send_msg(s,create_presence("online",account_name),COD)
      responce=get_msg(s.recv(1024),COD)
      #print(type(responce))

      t=threading.Thread(target=read_messages, args=(s,))
      t.start()
      if responce['responce'] == 200:
            user_name=input("Введите получателя: ")
            while True:
                  input_message=input()
                  if input_message=='exit':
                        break
                  else:
                        message=create_message(user_name,input_message,account_name)
                        send_msg(s,message,COD)

            s.disconnect























