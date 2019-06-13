#Server
COD='utf-8'
import select
from socket import*
from utils import*
#from errors import*
import sys
from deco import mylog
import logging
import log.server_log_config
logger = logging.getLogger('server')


def read_requests(r_clients,all_clients):
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

def write_responses(messages):
      for message in messages:
            to=message['To']
            sock=names[to]
            text=message
            send_msg(sock,text,COD)







@mylog
def presence_response(presence):
      if presence['status']=='online':
            logger.info(f"{presence_response.__name__}-{presence}")
            return {'responce':200}
      else:
            logger.info(f"{presence_response.__name__}-{presence}")
            return {'responce':400}      
      
      
if __name__=='__main__':
      s=socket(AF_INET, SOCK_STREAM)

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
      
      s.bind((host, port))
      s.listen(15)
      s.settimeout(0.5)
      clients=[]
      names={}


      print("Сервер запущен")
      while True:
            try:
                  client,adrr=s.accept()
                  msg=get_msg(client.recv(1024),COD)
                  client_name=msg['user']
                  print(client_name)
                  responce=presence_response(msg)
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
            requests=read_requests(r,clients)
            write_responses(requests)
                  #client.close()
      


























