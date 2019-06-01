#Server
from socket import*
from utils import*
from errors import*
import sys

import logging
import log.server_log_config

logger = logging.getLogger('server')

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
      s.listen(1)

      print("Сервер запущен")
      while True:
            
            client,adrr=s.accept()
            

            msg=get_msg(client.recv(1024),'utf-8')
            print(msg)

            responce=presence_response(msg)
            send_msg(client,responce,'ascii')
            msg=get_msg(client.recv(1024),'utf-8')
            print(msg)
            client.close()
      
      

























