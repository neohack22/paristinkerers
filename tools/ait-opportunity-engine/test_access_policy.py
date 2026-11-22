import unittest
from unittest.mock import patch
from access_policy import canonical_chapter,validate_job
from rest_sync import sync

class ScopeTests(unittest.TestCase):
 def setUp(self):
  self.ops={'demos':{'path':'/api/agents/v1/demos','parameters':[{'name':'meetup_token','required':True}]}}
  self.policy={'api_chapters':{'paris':{'enabled':True,'allowed_filters':{'meetup_token':['mu_paris']}},'san-francisco':{'enabled':False,'max_items_per_job':10,'allowed_filters':{'meetup_token':['mu_sf']}}},'max_items_per_job':100}
  self.job={'operation_id':'demos','chapter':'paris','chapter_filter_param':'meetup_token','params':{'meetup_token':'mu_paris'},'chapter_field':'chapter','items_path':'data.items','fields':{'source_id':'token','title':'title','chapter':'chapter'},'max_items':20}
 def test_aliases(self):
  self.assertEqual(canonical_chapter('BKO'),'bamako')
  self.assertEqual(canonical_chapter('CKY'),'conakry')
  self.assertEqual(canonical_chapter('Casa'),'casablanca')
  self.assertEqual(canonical_chapter('SF'),'san-francisco')
  self.assertIsNone(canonical_chapter('Eindhoven'))
 def test_unapproved_event_blocked_without_network(self):
  j=dict(self.job,params={'meetup_token':'mu_other'})
  with patch('rest_sync.request') as req:
   out=sync({'jobs':[j],'access_policy':self.policy},'fake',self.ops,{})
   req.assert_not_called()
  self.assertEqual(out['results'][0]['status'],'blocked_by_scope')
 def test_public_city_blocked_without_network(self):
  with patch('rest_sync.request') as req:
   out=sync({'jobs':[dict(self.job,chapter='Eindhoven')],'access_policy':self.policy},'fake',self.ops,{})
   req.assert_not_called()
  self.assertEqual(out['results'][0]['reason'],'chapter_not_in_api_scope')
 def test_san_francisco_disabled(self):
  j=dict(self.job,chapter='sf',params={'meetup_token':'mu_sf'},max_items=5)
  self.assertFalse(validate_job(j,self.ops['demos'],self.policy).allowed)
 def test_response_cross_chapter_rejected(self):
  with patch('rest_sync.request',return_value={'data':{'items':[{'token':'a','title':'A','chapter':'lima'},{'token':'b','title':'B','chapter':'paris'}]}}):
   out=sync({'jobs':[self.job],'access_policy':self.policy},'fake',self.ops,{})
  self.assertEqual(len(out['records']),1)
  self.assertEqual(out['records'][0]['source_id'],'b')
 def test_old_unapproved_records_purged(self):
  with patch('rest_sync.request',return_value={'data':{'items':[]}}):
   out=sync({'jobs':[self.job],'access_policy':self.policy},'fake',self.ops,{'records':[{'record_key':'a','chapter':'eindhoven'},{'record_key':'b','chapter':'paris'}]})
  self.assertEqual(len(out['records']),1)
 def test_missing_config_fail_closed(self):
  with patch('rest_sync.request') as req:
   out=sync({'jobs':[self.job]},'fake',self.ops,{})
   req.assert_not_called()
  self.assertEqual(out['results'][0]['status'],'blocked_by_scope')
if __name__=='__main__':unittest.main()