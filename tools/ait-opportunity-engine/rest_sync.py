#!/usr/bin/env python3
"""Authenticated, allowlisted AI Tinkerers REST reader; no Codex in scheduled runs.

Usage:
  AIT_AGENT_KEY=... python rest_sync.py discover --out capabilities.json
  AIT_AGENT_KEY=... python rest_sync.py sync --config sync_config.json --state sync_state.json --out snapshot.json

No personal information, keys or raw response bodies appear in logs. Sync is read-only
and retains only fields explicitly mapped by the config. Never makes arbitrary calls
based on LLM-produced URLs. Paths must come from authenticated OpenAPI operationIds.
"""
import argparse, datetime as dt, hashlib, json, os, sys, tempfile, urllib.error, urllib.parse, urllib.request
from pathlib import Path
import yaml

HOST='https://aitinkerers.org'
BASE=HOST+'/api/agents/v1'
READ_SUFFIXES=('/search','/list','/get','/detail','/query','/validate')
MAX_RESPONSE=3_000_000

def save(path, data):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=path.parent,delete=False) as f:
        json.dump(data,f,ensure_ascii=False,indent=2); f.write('\n'); tmp=f.name
    os.replace(tmp,path)

def request(path, key, params=None, raw=False):
    if not path.startswith('/api/agents/v1/') or '://' in path:
        raise ValueError('Only documented AIT Agent API paths are permitted')
    url=HOST+path
    if params: url+='?'+urllib.parse.urlencode(params, doseq=True)
    req=urllib.request.Request(url,headers={'Authorization':'Bearer '+key,'Accept':'application/json, application/yaml, text/yaml','User-Agent':'AIT-Opportunity-Internal/1.0'},method='GET')
    with urllib.request.urlopen(req,timeout=25) as response:
        length=response.headers.get('Content-Length')
        if length and int(length)>MAX_RESPONSE: raise ValueError('response too large')
        body=response.read(MAX_RESPONSE+1)
        if len(body)>MAX_RESPONSE: raise ValueError('response too large')
        if raw: return body.decode('utf-8')
        return json.loads(body.decode('utf-8'))

def spec_and_key(key):
    if not key or not key.startswith('sk_'): raise RuntimeError('Set AIT_AGENT_KEY privately; never commit it')
    validation=request('/api/agents/v1/auth/validate',key)
    if validation.get('ok') is False: raise RuntimeError('API key validation failed')
    spec=yaml.safe_load(request('/api/agents/v1/openapi.yaml',key,raw=True))
    if not isinstance(spec,dict) or not isinstance(spec.get('paths'),dict): raise RuntimeError('Bad authenticated OpenAPI response')
    return validation,spec

def operations(spec):
    output={}
    for path,methods in spec.get('paths',{}).items():
        if not isinstance(methods,dict): continue
        for method,definition in methods.items():
            if method.lower()!='get' or not isinstance(definition,dict):continue
            name=definition.get('operationId')
            if name and path.startswith('/api/agents/v1/'):
                parameters=[]
                for p in definition.get('parameters',[]):
                    if '$ref' in p: continue
                    if p.get('in')=='query': parameters.append({'name':p.get('name'),'required':p.get('required',False)})
                output[name]={'method':'GET','path':path,'parameters':parameters}
    return output

def pick(obj,path):
    """Small explicit dotted-path projection: no arbitrary expression evaluation."""
    for part in path.split('.'):
        if not isinstance(obj,dict) or part not in obj:return None
        obj=obj[part]
    return obj

def sync(config,key,ops,old):
    results=[]; existing={r['record_key']:r for r in old.get('records',[]) if isinstance(r,dict) and 'record_key' in r}
    counts={'new':0,'changed':0,'unchanged':0,'skipped':0}
    for job in config.get('jobs',[]):
        name=job['operation_id']; endpoint=ops.get(name)
        if not endpoint: results.append({'operation':name,'status':'unavailable_or_not_readable'});continue
        # Exact user-configured parameters, checked against the authorized schema.
        allowed={x['name'] for x in endpoint['parameters']}
        supplied=job.get('params',{})
        if not set(supplied).issubset(allowed):
            results.append({'operation':name,'status':'invalid_query_parameters'});continue
        required={x['name'] for x in endpoint['parameters'] if x['required']}
        if not required.issubset(supplied):
            results.append({'operation':name,'status':'missing_required_query_parameters','required':sorted(required)});continue
        payload=request(endpoint['path'],key,supplied)
        collection=pick(payload,job['items_path'])
        if not isinstance(collection,list):
            results.append({'operation':name,'status':'items_path_not_array'});continue
        seen=0
        for item in collection[:job.get('max_items',100)]:
            if not isinstance(item,dict):counts['skipped']+=1;continue
            record={k:pick(item,path) for k,path in job.get('fields',{}).items()}
            source_id=record.get('source_id')
            if not source_id:counts['skipped']+=1;continue
            key_id=f'{name}:{source_id}'
            record={'record_key':key_id,'source_operation':name,'source_path':endpoint['path'],**record}
            digest=hashlib.sha256(json.dumps(record,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
            before=existing.get(key_id)
            if before and before.get('digest')==digest:counts['unchanged']+=1
            else:
                counts['changed' if before else 'new']+=1
                existing[key_id]={**record,'digest':digest,'observed_at':dt.datetime.now(dt.timezone.utc).isoformat()}
            seen+=1
        results.append({'operation':name,'status':'read','count':seen,'pagination':'single_page_only'})
    return {'schema':'ait_rest_snapshot/v1','updated_at':dt.datetime.now(dt.timezone.utc).isoformat(),'records':list(existing.values()),'results':results,'counts':counts}

def main(argv=None):
    p=argparse.ArgumentParser();p.add_argument('command',choices=['discover','sync']);p.add_argument('--out',required=True);p.add_argument('--config');p.add_argument('--state');a=p.parse_args(argv)
    key=os.getenv('AIT_AGENT_KEY','')
    try:
        validation,spec=spec_and_key(key);ops=operations(spec)
        if a.command=='discover':
            save(a.out,{'schema':'ait_api_capabilities/v1','read_operations':ops,'authenticated':True,'authorization_note':'Operation presence does not imply access to all records'})
            print(f'Authenticated OpenAPI: {len(ops)} GET operations discovered, written to {a.out}')
        else:
            if not a.config or not a.state: raise ValueError('sync requires --config and --state')
            config=json.loads(Path(a.config).read_text(encoding='utf8'))
            state=json.loads(Path(a.state).read_text(encoding='utf8')) if Path(a.state).exists() else {}
            output=sync(config,key,ops,state)
            # State & export identical: avoid duplicate raw storage.
            save(a.state,output)
            if Path(a.out).resolve()!=Path(a.state).resolve():save(a.out,output)
            print(json.dumps({'counts':output['counts'],'operations':output['results']},ensure_ascii=False))
    except (ValueError,RuntimeError,urllib.error.URLError,yaml.YAMLError,json.JSONDecodeError) as exc:
        print(json.dumps({'status':'failed','reason':type(exc).__name__,'message':str(exc) if isinstance(exc,(ValueError,RuntimeError)) else 'API or schema unavailable'},ensure_ascii=False),file=sys.stderr)
        return 2
    return 0
if __name__=='__main__':sys.exit(main())