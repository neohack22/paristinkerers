import unittest
from rest_sync import operations,sync,pick
from unittest.mock import patch
class RestSyncTests(unittest.TestCase):
 def setUp(self):
  self.spec={'paths':{'/api/agents/v1/demo/list':{'get':{'operationId':'demo_list','parameters':[{'name':'meetup_token','in':'query','required':True}]},'post':{'operationId':'demo_create'}}}}
 def test_get_only(self):
  self.assertEqual(list(operations(self.spec)),['demo_list'])
 def test_picks(self):
  self.assertEqual(pick({'data':{'items':[1]}},'data.items'),[1])
 def test_incremental_idempotent(self):
  config={'jobs':[{'operation_id':'demo_list','params':{'meetup_token':'mu_demo'},'items_path':'data.items','fields':{'source_id':'token','title':'title'}}]}
  with patch('rest_sync.request',return_value={'data':{'items':[{'token':'demo1','title':'A'}]}}):
   a=sync(config,'fake-key',operations(self.spec),{})
   b=sync(config,'fake-key',operations(self.spec),a)
  self.assertEqual(a['counts']['new'],1);self.assertEqual(b['counts']['unchanged'],1)
 def test_missing_required_no_request(self):
  config={'jobs':[{'operation_id':'demo_list','params':{},'items_path':'data.items','fields':{'source_id':'token'}}]}
  with patch('rest_sync.request') as mock:
   a=sync(config,'fake-key',operations(self.spec),{})
   mock.assert_not_called()
  self.assertEqual(a['results'][0]['status'],'missing_required_query_parameters')
if __name__=='__main__': unittest.main()