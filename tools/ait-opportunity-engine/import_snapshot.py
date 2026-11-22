#!/usr/bin/env python3
"""Conservative AIT REST snapshot -> local pilot graph projection.
Does NOT write canonical CRM registry; never invents ratings, persons or used tools.
Only imports jobs explicitly configured as entity_type=Project with a source_id.
"""
import argparse,copy,json,re,unicodedata
from pathlib import Path
from access_policy import canonical_chapter, is_api_chapter

def slug(t):
 t=''.join(c for c in unicodedata.normalize('NFKD',str(t).lower()) if not unicodedata.combining(c))
 return re.sub(r'[^a-z0-9]+','-',t).strip('-')

def import_projects(graph,snapshot,allowed_ops=None,access_policy=None):
    g=copy.deepcopy(graph)
    nodes={x['id']:x for x in g.get('nodes',[])}
    aliases={f"{canonical_chapter(x.get('chapter'))}:{x.get('source_token')}":x['id'] for x in g.get('nodes',[]) if x.get('source_token') and canonical_chapter(x.get('chapter'))}
    counts={'new':0,'updated':0,'unchanged':0,'rejected':0}
    for record in snapshot.get('records',[]):
        if (not isinstance(record,dict) or not record.get('source_id')
            or (allowed_ops and record.get('source_operation') not in allowed_ops)
            or not access_policy or not is_api_chapter(record.get('chapter'),access_policy)):
            counts['rejected']+=1;continue
        label=record.get('title')
        if not isinstance(label,str) or not label.strip():counts['rejected']+=1;continue
        token=str(record['source_id'])
        chapter=canonical_chapter(record['chapter'])
        alias_key=f'{chapter}:{token}'
        pid=aliases.get(alias_key) or 'project:ait-api:'+slug(chapter+'-'+token)
        if not slug(token):counts['rejected']+=1;continue
        old=nodes.get(pid)
        candidate=copy.deepcopy(old) if old else {'id':pid,'type':'Project'}
        if candidate.get('type')!='Project':counts['rejected']+=1;continue
        candidate['name']=label
        candidate['source_token']=token
        candidate['chapter']=chapter
        candidate['source']={'kind':'ait_agent_api','operation':record.get('source_operation'),'path':record.get('source_path'),'observed_at':record.get('observed_at')}
        # Import ratings ONLY when documented explicitly as a rating / score in the API configuration.
        rating=record.get('rating');scale=record.get('rating_scale')
        if isinstance(rating,(float,int)) and not isinstance(rating,bool) and isinstance(scale,(float,int)) and not isinstance(scale,bool) and 0<=rating<=scale and scale>0:
            candidate['rating']=rating;candidate['rating_scale']=scale;candidate['rating_status']='api_reported'
        elif not old:
            candidate['rating']=None;candidate['rating_status']='unknown'
        for field in ('chapter','event_format','event_external_id','status'):
            if record.get(field) is not None:candidate[field]=record[field]
        if old==candidate:counts['unchanged']+=1
        else:
            counts['updated' if old else 'new']+=1
            nodes[pid]=candidate
    g['nodes']=list(nodes.values());g['status']='projection_from_authorized_sources_not_canonical_crm'
    return g,counts

def main():
 p=argparse.ArgumentParser();p.add_argument('--graph',required=True);p.add_argument('--snapshot',required=True);p.add_argument('--out',required=True);p.add_argument('--policy',required=True);p.add_argument('--allowed-operation',action='append',default=[]);a=p.parse_args()
 graph=json.loads(Path(a.graph).read_text(encoding='utf8'));snapshot=json.loads(Path(a.snapshot).read_text(encoding='utf8'))
 if not a.allowed_operation: raise SystemExit('Specify at least one --allowed-operation from authenticated capability discovery')
 policy=json.loads(Path(a.policy).read_text(encoding='utf8'))
 out,counts=import_projects(graph,snapshot,set(a.allowed_operation),policy)
 Path(a.out).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(counts))
if __name__=='__main__':main()