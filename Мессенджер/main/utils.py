from datetime import datetime
from errors import *
import json
import os
import sys
#sys.path.append('../')
from deco import mylog

import logging
from log.user_log_config import *
logger = logging.getLogger('user')


# Папка где лежит настоящий файл
FOLDER_PATH = os.path.dirname(os.path.abspath(__file__))
# путь до клиентского лога

USERS = os.path.join(FOLDER_PATH,r'Users\users.json')

#------------------------------------------------------------
def msg_to_bytes(data,coding):
      '''Перевод строки в json, потом в байты
      '''
      json_data=json.dumps(data)
      return json_data.encode(coding)

#------------------------------------------------------------	
	
def bytes_to_msg(byts,coding):
      '''Перевод байтов в json, потом в стр
      '''
      bytes_data=byts.decode(coding)
      return json.loads(bytes_data)

#------------------------------------------------------------
	
def get_msg(data, coding):
      '''Получает сообщение
      '''
      return bytes_to_msg(data,coding)
#------------------------------------------------------------
@mylog
def send_msg(adr,msg,coding):
      '''Отправляет сообщение
      '''
      if type(msg) is dict:
            adr.send(msg_to_bytes(msg,coding))
      else:
            raise NotDict(msg)

#------------------------------------------------------------
if __name__=='__main__':
      def find_user(name):
            '''
            Поиск name в списке юзеров. Если имя занято,
            возращается 1, в ином случае 0
            '''
            file=USERS
            with open(file,'r') as f:
                  try:
                        users=json.load(f)
                  except:
                        users=[]
                  if name in users:

                        return 1
                  else:
                        return 0
      #------------------------------------------------------------

      def user_append(name):
            '''Добавление нового пользователя в список в файле users
            '''
            file=USERS
            with open(file,'r') as f:
                  users=json.load(f)
            with open(file,'w') as f:
                  users.append(name)
                  json.dump(users,f)


      #------------------------------------------------------------

      def check_in(name,password):
            '''Регистрация нового пользователя.
            Если имя не занято, создается новый файл имя.json со словарем
            где ключами являются имя, пароль, статус, дата последнего входа.
            '''

            if find_user(name):
                  raise is_user(name)
            else:
                  file=r"Users\{}.json".format(name)
                  date=datetime.today().strftime('%d/%m/%Y')
                  user_append(name)
                  with open(file,'w')as f:
                        data={
                              'name':name,
                              'password':password,
                              'status':'online',
                              'date':date}
                        json.dump(data,f)
            logger.info(f'Новый пользователь {name}')

      #------------------------------------------------------------

      def log_in(name,password):
            '''Авторизация. Если имя есть в списке юзеров, открывается файл юзера и
            пароли сверяются.
            '''
            if find_user(name):
                  date=datetime.today().strftime('%d/%m/%Y')
                  file=r"Users\{}.json".format(name)
                  with open(file,'r')as f:
                        data=json.load(f)
                  if data['password']==password:
                        with open(file,'w') as f:
                              data['date']=date
                              json.dump(data,f)
                              logger.info(f'Пользователь {name} online')
                              return 1
                  else:
                        return 0
      #------------------------------------------------------------

      def user_off(name):
            '''При отключении пользователя от сервера меняет статус на
            offlane, записывает дату
            '''
            file=r"Users\{}.json".format(name)
            date=datetime.today().strftime('%d/%m/%Y')
            with open(file,'r')as f:
                  data=json.load(f)
            with open(file,'w')as f:
                  data['status']='offlane'
                  data['date']=date
                  json.dump(data,f)
      #------------------------------------------------------------

      def del_user(name):
            '''Удаляет пользователя из списка users и удаляет его файл
            '''
            if find_user(name):
                  #open_file=r'C:\Users\Ruslan\Documents\Клиент-серверное приложение\Vebinar_5\Users\users.json'
                  file=os.path.join(FOLDER_PATH, r'Users\{}.json'.format(name))
                  with open(USERS,'r') as f:
                        users=json.load(f)
                        users.remove(name)
                  with open(USERS,'w') as f:
                        json.dump(users,f)
                  os.remove(file)
                  return 1
            else:
                 return 0
      #------------------------------------------------------------


      if __name__=='__main__':
            log_in("admin",'admin')
            if find_user('admin'):
                  print("Yes")





      



