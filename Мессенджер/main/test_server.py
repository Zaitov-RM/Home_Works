import unittest
from Server import presence_response
from datetime import datetime
from utils import*
from errors import*


class TestPresenceResponse(unittest.TestCase):
      def test_presence_response(self):
            self.assertEqual(presence_response({'status':'online','data':'data','user':'user'}),\
                             {'responce':200})

class TestGetMsg(unittest.TestCase):
      def test_get_msg(self):
            data=msg_to_bytes({'admin':'admin'},'ascii')                 
            self.assertEqual(get_msg(data,'ascii'),{'admin':'admin'})

class TestErrors(unittest.TestCase):
      def test_isuser(self):
            with self.assertRaises(NotDict):
                  send_msg("adr","test",'ascii')



if __name__=='main':
      unittest.main()

            
