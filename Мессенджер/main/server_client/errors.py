import sys
sys.path.append('../')


class NotDict(Exception):
      def __init__(self, msg):
            self.msg=msg
      
      def __str__(self):
            return f"{self.msg} не является словарем"


class is_user(Exception):
      def __init__(self,name):
            self.name=name

      def __str__(self):
            return f'Имя {self.name} занято. Пожалуйста,выберите другое имя.'

if '__name__'=='__main__':
      pass
