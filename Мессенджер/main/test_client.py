import unittest
from Client import create_presence
from datetime import datetime
from utils import*
from errors import*

class TestClient(unittest.TestCase):
      def test_message(self):
            data=datetime.today().strftime('%d/%m/%Y')
            self.assertEqual(create_presence('online','user'),\
                             {'status':'online','data':data,'user':'user'})
'''
class TestCheckIn(unittest.TestCase):
      def test_find_user(self):
            self.assertEqual(find_user('admin'),1)

class TestErrors(unittest.TestCase):
      def test_isuser(self):
            with self.assertRaises(is_user):
                  check_in('user','pass')
'''

unittest.main()
if __name__=='main':
      unittest.main()

            
