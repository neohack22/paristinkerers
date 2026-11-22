import unittest,copy,sys
sys.path.insert(0,__import__('os').path.dirname(__file__))
from engine import generate
class EngineTests(unittest.TestCase):
 def base(self):
  return {'nodes':[{'id':'project:one','type':'Project','name':'One','chapter':'Paris','rating':9,'rating_scale':10,'source':{'id':'a'}},{'id':'project:two','type':'Project','name':'Two','chapter':'Paris','rating':4,'rating_scale':10,'event_format':'meetup','source':{'id':'b'}},{'id':'theme:rag','type':'Theme','name':'RAG'},{'id':'technology:db','type':'Technology','name':'TestDB'}], 'relationships':[{'from':'project:one','to':'theme:rag','type':'HAS_THEME'},{'from':'project:two','to':'theme:rag','type':'HAS_THEME'},{'from':'project:one','to':'technology:db','type':'USES'}]}
 def test_workshop_and_progression(self):
  x=generate(self.base());t=[o['type'] for o in x['opportunities']];self.assertIn('workshop',t);self.assertIn('hackathon',t);self.assertIn('themed_meetup',t)
 def test_aggregate_and_no_duplicate(self):
  x=generate(self.base());self.assertEqual(len([o for o in x['opportunities'] if o['type']=='themed_meetup']),1);self.assertEqual(len(set(o['id'] for o in x['opportunities'])),len(x['opportunities']))
 def test_unknown_score_not_low(self):
  b=self.base();b['nodes'][0]['rating']=None;x=generate(b);self.assertFalse(any(o['type']=='workshop' for o in x['opportunities']))
 def test_dinner_requires_verified_role(self):
  b=self.base();self.assertNotIn('dinner',[o['type'] for o in generate(b)['opportunities']]);b['nodes'][0]['speaker_technical_company_role_confirmed']=True;self.assertIn('dinner',[o['type'] for o in generate(b)['opportunities']])
if __name__=='__main__':unittest.main()