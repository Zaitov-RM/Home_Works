#Server
COD='utf-8'
import select
import sys
import logging
import log.server_log_config
import os

from metaclasses import ServerVerifier
from socket import*
from utils import*
from descript import Port
#from errors import*
from deco import mylog
from ServerDB.ServerDB import ServerDB

logger = logging.getLogger('server')

folder=os.path.dirname(os.path.abspath(__file__))
path=os.path.join(folder,'ServerDB\serverDB.db3')


class Server(metaclass=ServerVerifier):
      port=Port()
      def __init__(self,host,port,serverDB,af_inet=AF_INET,sock_stream=SOCK_STREAM):
            self.host=host
            self.port=port
            self.serverDB=serverDB
            self.AF_INET=af_inet
            self.SOCK_STREAM=sock_stream

      def connect(self):
            sock=socket(self.AF_INET,self.SOCK_STREAM)
            sock.bind((self.host,self.port))
            sock.settimeout(0.5)
  
            self.sock=sock
            self.sock.listen(5)
            return self.sock

      def read_requests(self,r_clients,all_clients):
            messages=[]
            for sock in r_clients:
                  try:
                        message=get_msg(sock.recv(1024),COD)
                        messages.append(message)
                  except:
                        print(f"Клиент {sock.fileno()} {sock.getpeername} отключился")
                        #sock.close()
                        all_clients.remove(sock)
            return messages

      def write_responses(self,messages):
            for message in messages:
                  to=message['To']
                  sock=names[to]
                  text=message
                  send_msg(sock,text,COD)


      @mylog
      def presence_response(self,presence):
            if presence['status']=='get_contacts':
                  return {'responce':202,
                          'alert':self.serverDB.get_contacts('client1')}
            elif presence['status']=='online':
                  logger.info(f"{self.presence_response.__name__}-{presence}")
                  return {'responce':200}
            else:
                  logger.info(f"{self.presence_response.__name__}-{presence}")
                  return {'responce':400}      
      
      
if __name__=='__main__':
      try:
            host=sys.argv[1]
      except IndexError as ie:
            logger.info(f'{ie}')
            host=''
      try:
            port=int(sys.argv[2])
      except IndexError as ie:
            logger.info(f'{ie}')
            port=8888

      serverDB=ServerDB(path)
      server=Server(host,port,serverDB)
      s=server.connect()

      clients=[]
      names={}
    

      print("Сервер запущен")
      while True:
            try:
                  client,adrr=s.accept()
                  #Первое подключение
                  #Запрос от клиента
                  msg=get_msg(client.recv(1024),COD)
                  client_name=msg['user']
                  print(client_name)
                  #Подготовка и отправка ответа клиенту
                  responce=server.presence_response(msg)
                  send_msg(client,responce,COD)
                  #Запрос на список контактов
                  #Отправить список контактов
                  msg=get_msg(client.recv(1024),COD)
                  print('msg ',msg)
                  responce=server.presence_response(msg)
                  print('responce ',responce)
                  send_msg(client,responce,COD)

            except OSError as e:
                  pass
            else:
                  print(f"Получен запрос на соединение от {adrr}")
                  clients.append(client)
                  names[client_name] = client
            finally:
                  wait=0
                  r=[]
                  w=[]
            try:
                  r,w,e=select.select(clients, clients,[], wait)
            except:
                  pass
            requests=server.read_requests(r,clients)
            server.write_responses(requests)
                  #client.close()
      


























