#Client

from socket import *
from utils import*
import sys
from datetime import datetime
from server_client.deco import mylog
import logging
import log.user_log_config
logger = logging.getLogger('user')

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
      print("Вы зарегистрированы?  y/n")
      answer=input()
      if answer.upper()=='Y':
            print("name: ")
            name=str(input())
            print("password")
            password=str(input())
            log_in(name,password)

      else:
            print("name: ")
            name=str(input())
            print("password")
            password=str(input())
            check_in(name,password)


      s=socket(AF_INET,SOCK_STREAM)
      
      try:
            host=sys.argv[1]
      except IndexError:
            host='localhost'
      try:
            port=int(sys.argv[2])

      except IndexError:
            port=8888

      s.connect((host,port))      
      
      send_msg(s,create_presence("online",name),'ascii')

      responce=get_msg(s.recv(1024),'ascii')
      print(responce)
      
      print(name)
      send_msg(s,create_presence("offlane",name),'ascii')
      user_off(name)
      s.close()






















