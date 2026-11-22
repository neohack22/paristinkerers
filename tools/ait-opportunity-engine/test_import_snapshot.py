import unittest
from import_snapshot import import_projects
class ImportTests(unittest.TestCase):
 def test_import_idempotent_and_score_unknown(self):
  s={'records':[{'source_operation':'demo_list','source_id':'demo01','title':'Test demo','rating':9}]}
  a,c=import_projects({'nodes':[]},s,{'demo_list'});b,c2=import_projects(a,s,{'demo_list'})
  self.assertEqual(c['new'],1);self.assertEqual(c2['unchanged'],1)
  self.assertIsNone(a['nodes'][0]['rating'])
 def test_rating_scale_when_valid(self):
  g,c=import_projects({'nodes':[]},{'records':[{'source_operation':'demo_list','source_id':'d','title':'D','rating':4,'rating_scale':5}]},{'demo_list'})
  self.assertEqual(g['nodes'][0]['rating'],4)
 def test_only_allowlisted(self):
  g,c=import_projects({'nodes':[]},{'records':[{'source_operation':'members_list','source_id':'d','title':'Person'}]},{'demo_list'})
  self.assertFalse(g['nodes'])
if __name__=='__main__':unittest.main()