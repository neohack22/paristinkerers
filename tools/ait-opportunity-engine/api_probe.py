#!/usr/bin/env python3
"""Permission check only: never stores credentials or member data.
Usage: AIT_AGENT_KEY=... python api_probe.py
No keys are accepted as command arguments.
"""
import os, json, urllib.request, urllib.error, sys
from pathlib import Path
BASE='https://aitinkerers.org/api/agents/v1'
def main():
 key=os.getenv('AIT_AGENT_KEY')
 if not key:
  print(json.dumps({'status':'missing_agent_key','developer_page':'https://aitinkerers.org/developers/api-keys','next':'Configure AIT_AGENT_KEY in a private environment; never share it in chat or commit it.'}));return 2
 if not key.startswith('sk_'):
  print(json.dumps({'status':'invalid_key_format'}));return 2
 req=urllib.request.Request(BASE+'/auth/validate',headers={'Authorization':'Bearer '+key,'Accept':'application/json'})
 try:
  with urllib.request.urlopen(req,timeout=15) as resp: body=json.load(resp)
  print(json.dumps({'status':'validated','effective_permissions':body},ensure_ascii=False))
  return 0
 except (urllib.error.URLError,ValueError) as e:
  print(json.dumps({'status':'validation_failed','error_type':type(e).__name__}));return 1
if __name__=='__main__':sys.exit(main())