#Client
COD='utf-8'

import time
import sys
import logging
import log.user_log_config
import threading

from metaclasses import ClientVerifier
from socket import *
from utils import*
from datetime import datetime
from deco import mylog
from ClientDB.ClientDB import ClientDB

folder=os.path.dirname(os.path.abspath(__file__))
path=os.path.join(folder,'ClientDB')

logger = logging.getLogger('user')


class Client(metaclass=ClientVerifier):
      def __init__(self,clientDatabase):
            self.clientDatabase=clientDatabase

      def read_messages(self,client):
            while True:
                  try:
                        message=get_msg(client.recv(1024),COD)
                        print(f"{message['From']} {message['Text']}")
                  except:
                        print('read_messages')

      def create_message(self, message_to, text, account_name='Guest'):
            return {'Time':time.time(), 'To':message_to,'From':account_name,'Text':text}

      @mylog
      def create_presence(self, status,user='Guest'):
            data=datetime.today().strftime('%d/%m/%Y')
            message={
                  'status':status,
                  'data':data,
                  'user':user
                  }
            logger.info(f"{self.create_presence.__name__}-{message}")
            return message

            

if __name__=='__main__':
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
            account_name='client1'
            print('Укажите получателя')

      #Создание клиентской БД
      clientDatabase=ClientDB(account_name,path)
      #Создание клиента
      client=Client(clientDatabase)
      
      #################################sock=client.connect()
      sock=socket(AF_INET,SOCK_STREAM)
      sock.connect((host,port))
      
      #Первое подключение
      send_msg(sock,client.create_presence("online",account_name),COD)
      responce=get_msg(sock.recv(1024),COD)
      #Запрос списка контактов
      send_msg(sock,client.create_presence('get_contacts',account_name),COD)
      responceContactsList=get_msg(sock.recv(1024),COD)
      contactsList=responceContactsList['alert']
      print('contacts ',contactsList)
      #Добавление контактов в БД
      for contact in contactsList:
            client.clientDatabase.add_contact(contact)
 

      t=threading.Thread(target=client.read_messages, args=(sock,))
      t.start()
      if responce['responce'] == 200:
            user_name=input("Введите получателя: ")
            while True:
                  input_message=input('Сообщение ')
                  if input_message=='exit':
                        break
                  elif input_message=='add':
                        contact=input('Введите контакт для добавления ')
                        client.clientDatabase.add_contact(contact)
                  elif input_message=='del':
                        contact=input('Введите контакт для удаления ')
                        client.clientDatabase.del_contact(contact)
                  else:
                        message=client.create_message(user_name,input_message,account_name)
                        send_msg(sock,message,COD)

           


      





















