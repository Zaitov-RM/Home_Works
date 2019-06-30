from sqlalchemy import create_engine,Table,Column,ForeignKey,\
     Integer,String,Text,DateTime,MetaData
from sqlalchemy.orm import mapper, sessionmaker
import datetime
import os

defaultPath=os.path.dirname(os.path.abspath(__file__))
print(defaultPath)

class ClientDB:
      class AllUsers:
            #Нужно получить всех существующих юзеров с сервера
            def __init__(self,userName):
                  self.id=None
                  self.userName=userName
                  
      class MessageHistory:
            #История переписки
            def __init__(self,msgFrom,msgTo,msg):
                  self.id=None
                  self.msgFrom=msgFrom
                  self.msgTo=msgTo
                  self.msg=msg
                  self.dateTime=datetime.datetime.now()
      class Contacts:
            #Список контактов
            def __init__(self,contact):
                  self.id=None
                  self.contact=contact

      def __init__(self,userName,path=defaultPath):
            #создаем движок
            self.engine=create_engine(f'sqlite:///{path}/client_{userName}DB.db3',echo=False,
                                      pool_recycle=7200,connect_args={'check_same_thread': False})
            #Создаем объект метеадата
            self.metadata=MetaData()

            #Создаем таблицы
            allUsersTable=Table('AllUsers',self.metadata,
                                Column('id',Integer,primary_key=True),
                                Column('userName',String)
                                )
            
            messageHistoryTable=Table('MessageHistory',self.metadata,
                                      Column('id',Integer,primary_key=True),
                                      Column('msgFrom', ForeignKey('AllUsers.userName')),
                                      Column('msgTo',ForeignKey('AllUsers.userName')),
                                      Column('msg',Text),
                                      Column('dateTime',DateTime)
                                      )
            contactsTable=Table('Contacts',self.metadata,
                                Column('id',Integer,primary_key=True),
                                Column('contact',ForeignKey('AllUsers.userName'))
                                )
            #Создаем таблицы
            self.metadata.create_all(self.engine)

            #Связываем объект с таблицей
            mapper(self.AllUsers,allUsersTable)
            mapper(self.MessageHistory,messageHistoryTable)
            mapper(self.Contacts,contactsTable)

            #Создаем объект сессия
            Session=sessionmaker(bind=self.engine)
            self.session=Session()

            #Очищаем список контактов
            self.session.query(self.Contacts).delete()
            self.session.commit()

      #Методы главного класса
      #----------------------
      #Добавление контакта
      def add_contact(self,contact):
            if not self.session.query(self.Contacts).count():
                  newContact=self.Contacts(contact)
                  self.session.add(newContact)
                  self.session.commit()

      #Удаление контакта
      def del_contact(self,delContact):
            self.session.query(self.Contacts).filter_by(contact=delContact).delete()

      #Добавление существующих польователей
      def add_users(self,usersList):
            self.session.query(self.AllUsers).delete()
            for user in usersList:
                  userToAllUsers=self.AllUsers(user)
                  self.session.add(userToAllUsers)
                  self.session.commit()

      #Сохранение сообщения
      def save_message(self, msgFrom,msgTo,msg):
            message=self.MessageHistory(msgFrom,msgTo,msg)
            self.session.add(message)
            self.session.commit()

      #
      def get_message(self,msg_From=None,msg_To=None):
            if msg_From:
                  query=self.session.query(self.MessageHistory).filter_by(msgFrom=msg_From)
            if msg_To:
                  query=self.session.query(self.MessageHistory).filter_by(msgTo=msg_To)
            return [(history.msgFrom,history.msgTo,history.msg,history.dateTime) for history in query.all()]
                  
      #Возвращение имеющихся контактов
      def get_contacts(self):
            return [contact[0] for contact in self.session.query(self.Contacts.contact).all()]

      #Возвращение имеющихся пользователей
      def get_users(self):
            return [user[0] for user in self.session.query(self.AllUsers.userName).all()]


if __name__=='__main__':
      testDB=ClientDB('user2')
      testDB.add_users(['user2','user3'])
      testDB.add_contact('user4')
      print(testDB.get_users())
      print(testDB.get_contacts())
      testDB.save_message('user1','user4','Hi, user4')
      testDB.save_message('user4','user1','Hi,user1')
      for i in range(len(testDB.get_message('user1'))):
            print(testDB.get_message('user1')[i])
      print(testDB.get_message(msg_To='user1'))
      

















                  
            
                                             
