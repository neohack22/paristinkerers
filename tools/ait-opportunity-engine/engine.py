#!/usr/bin/env python3
"""AI Tinkerers organizer opportunity engine. Local, read-only inputs, no outreach.

Usage:
  python engine.py --input ait_project_graph_pilot_v1.json --output opportunities.json
  python engine.py --input graph.json --output opportunities.json --demo-score-threshold 8

Privacy: only data the organizer is authorized to process. No API scraping or contact extraction.
"""
import argparse, json, re, unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

def key(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(s).lower()) if not unicodedata.combining(c))

def eid(prefix, value):
    return f'{prefix}:'+re.sub(r'[^a-z0-9]+','-',key(value)).strip('-')

def generate(data, threshold=8):
    nodes={n['id']: n for n in data.get('nodes', [])}
    projects=[n for n in nodes.values() if n.get('type')=='Project']
    edges=data.get('relationships', [])
    byproject=defaultdict(lambda:defaultdict(set))
    for e in edges:
        a,b=e.get('from'),e.get('to'); rel=e.get('type','')
        if a in nodes and b in nodes and nodes[a].get('type')=='Project': byproject[a][rel].add(b)
    opportunities={}; topic_groups=defaultdict(list)
    def add(oid, kind, title, projects_ids, why, rank, status='candidate', sponsor=None, evidence=None):
        cur=opportunities.get(oid)
        if cur:
            cur['project_ids']=sorted(set(cur['project_ids']+list(projects_ids)))
            cur['evidence']=sorted(set(cur['evidence']+list(evidence or [])))
            cur['priority']=max(cur['priority'],rank)
        else:
            opportunities[oid]={'id':oid,'type':kind,'title':title,'project_ids':sorted(set(projects_ids)),'why':why,'priority':rank,'status':status,'sponsor':sponsor,'evidence':sorted(set(evidence or [])),'outreach_sent':False,'event_confirmed':False}
    for p in projects:
        pid=p['id']; links=byproject[pid]
        themes=sorted(links.get('HAS_THEME',set()))
        techs=sorted(links.get('USES',set()))
        # Robust against differently named relation types, but never infer use from mere similarity.
        if not themes: themes=[eid('theme',t) for t in p.get('themes',[])]
        if not techs: techs=[eid('technology',t) for t in p.get('technologies',[])]
        source=p.get('source',{}); evidence=[source.get('url') or f"gmail:{source['id']}" if source.get('id') else 'unknown']
        score=p.get('rating'); scale=p.get('rating_scale',10)
        good=score is not None and scale and (score/scale)>=threshold/10
        chapter=p.get('chapter','unknown')
        for t in themes: topic_groups[(chapter,t)].append(pid)
        if good:
            add(eid('opp:workshop',pid),'workshop',f"Workshop à partir de {p.get('name','projet')}",[pid],"Note suffisante; aptitude de l'intervenant à confirmer",90,evidence=evidence)
        elif score is not None:
            is_builder='builder' in key(p.get('event_format','')) or 'hackathon' in key(p.get('event_format',''))
            kind='themed_meetup' if is_builder else 'hackathon'
            add(eid('opp:progression',pid),kind,f"Faire progresser : {p.get('name','projet')}",[pid],"Note en dessous du seuil de workshop, format suivant selon événement source",55,evidence=evidence)
        # Each project is eligible to contribute to general meetup; theme grouping upgrades at 2.
        add(eid('opp:general_meetup',chapter),'general_meetup',f"Meetup généraliste — {chapter}",[pid],"Projets à présenter, sélection à confirmer",35,evidence=evidence)
        # A dinner needs a verified technical founder/enterprise technical profile; never infer.
        if p.get('speaker_technical_company_role_confirmed') is True:
            for t in themes:
                add(eid('opp:dinner',f'{chapter}:{t}'),'dinner',f"Dîner technique — {nodes.get(t,{}).get('name',t)}",[pid],"Intervenant technique en entreprise ou technical founder vérifié",45,evidence=evidence)
        # Project technology => supplier prospecting only; sponsor must be verified separately.
        for tech in techs:
            tn=nodes.get(tech,{})
            add(eid('opp:sponsor',f'{chapter}:{tech}'),'event_sponsorship',f"Sponsoring via {tn.get('name',tech)} — {chapter}",[pid],"Technologie explicitement utilisée ; fournisseur et engagement à qualifier",60,evidence=evidence)
        # Rival-substitution is only from a verified relation, not automatically guessed.
        for tech in techs:
            for e in edges:
                if e.get('from')==tech and e.get('type')=='COMPETES_WITH' and e.get('status')=='confirmed':
                    alt=e.get('to');
                    add(eid('opp:competition',f'{chapter}:{alt}'),'hackathon',f"Challenge de migration vers {nodes.get(alt,{}).get('name',alt)}",[pid],"Concurrent vérifié ; substitution et effort technique à vérifier",50,evidence=evidence)
    for (chapter,theme),ps in topic_groups.items():
        if len(set(ps))>=2:
            n=nodes.get(theme,{})
            add(eid('opp:themed',f'{chapter}:{theme}'),'themed_meetup',f"Meetup thématique — {n.get('name',theme)} ({chapter})",ps,"Au moins deux projets distincts sur la thématique ; programmation à confirmer",70)
    out=sorted(opportunities.values(),key=lambda x:(-x['priority'],-len(x['project_ids']),x['id']))
    return {'schema':'ait_opportunity_engine/v1','generated_at':datetime.now(timezone.utc).isoformat(),'input_projects':len(projects),'input_relationships':len(edges),'score_threshold_fraction':threshold/10,'opportunities':out,'caveats':['Aucun score inventé : inconnu n’est pas faible.','Aucun contact ni événement exécuté.','Opportunités sans sponsor confirmé tant que le fournisseur et la relation ne sont pas vérifiés.','Analyse interne uniquement ; diffusion sponsor soumise aux permissions.']}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--output',required=True);ap.add_argument('--demo-score-threshold',type=float,default=8);a=ap.parse_args()
    data=json.loads(Path(a.input).read_text(encoding='utf8'))
    out=generate(data,a.demo_score_threshold)
    Path(a.output).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
    print(f"{out['input_projects']} projects -> {len(out['opportunities'])} opportunity records")
if __name__=='__main__': main()