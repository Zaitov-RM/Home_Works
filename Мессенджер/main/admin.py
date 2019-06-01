import json
from datetime import datetime
import sys
import os
import re
import server_client.utils


#--------------------------------------------------------------------
FOLDER_PATH = os.path.dirname(os.path.abspath(__file__))
USERS = os.path.join(FOLDER_PATH,r'server_client\Users\users.json')
print(USERS)


def verify_user():
      '''Проверяет активность пользователя по дате. Если нет активности,
      удаляет пользователя.
      '''
      date_now=datetime.today().strftime('%d/%m/%Y')
      file=USERS

      with open(file,'r') as f:
            users=json.load(f)
      for user in users:
            file=os.path.join(FOLDER_PATH,r'\Users\{}.json'.format(user))
            with open(file,'r') as f:
                  date=json.load(f)['date']
            if not sub_dates(date_now,date):
                  del_user(user)
#--------------------------------------------------------------------
                        
def str_date_to_int(date):
      '''Преобразует строкувую дату в числовую
'''
      dd=int(date[0:2])
      mm=int(date[3:5])
      yy=int(date[6:10])
      return dd,mm,yy
#--------------------------------------------------------------------

def sub_dates(date_now,last_date):
      '''Находит разность дат
      '''
      DD,MM,YY=str_date_to_int(date_now)
      dd,mm,yy=str_date_to_int(last_date)
      if (YY-yy)==0:#Если заходил в этом году
            if (MM-mm)==0:#Если заходил в этом месяце
                  if (DD-dd)==0:#Если заходил сегодня
                        return 1
                  else:
                        return 0
            else:
                  return 0
      else:
            return 0
#--------------------------------------------------------------------


  
#if __name__=='__main__':
#      date=datetime.today().strftime('%d/%m/%Y')      
#      verify_user()

