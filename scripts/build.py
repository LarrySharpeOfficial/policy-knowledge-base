#!/usr/bin/env python3
import hashlib,html,json,os,re,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; CONTENT=ROOT/'content'/'policies'; DIST=ROOT/'dist'
REQUIRED=('schema_version','id','slug','title','problem','proposal','implementation','benefits','tradeoffs','jurisdictions','topics','attribution','editorial_status','publication_status','sources')
SLUG=re.compile(r'^[a-z0-9-]+$'); META=re.compile(r'<!-- policy-meta\s*(\{.*?\})\s*policy-meta -->',re.S)
def load_policy(path):
 text=path.read_text(encoding='utf-8'); match=META.search(text)
 if not match: raise ValueError(f'{path.name}: missing policy-meta block')
 data=json.loads(match.group(1)); data['body_markdown']=text[match.end():].strip(); missing=[k for k in REQUIRED if k not in data]
 if missing: raise ValueError(f'{path.name}: missing {", ".join(missing)}')
 if data['schema_version']!='1.0.0' or not SLUG.fullmatch(data['slug']): raise ValueError(f'{path.name}: invalid schema or slug')
 if data['attribution']!='Larry Sharpe' or data['editorial_status'] not in {'draft_unapproved','approved'} or data['publication_status'] not in {'local_only','publishable','published'}: raise ValueError(f'{path.name}: invalid governance metadata')
 if not data['sources']: raise ValueError(f'{path.name}: source required')
 for source in data['sources']:
  for key in ('title','url','video_id','published_date','timestamp_url','quote'):
   if not source.get(key): raise ValueError(f'{path.name}: source missing {key}')
 return data
def markdown_to_html(text):
 out=[]; paragraph=[]
 def flush():
  if paragraph: out.append('<p>'+html.escape(' '.join(paragraph))+'</p>'); paragraph.clear()
 for raw in text.splitlines():
  line=raw.strip()
  if not line: flush()
  elif line.startswith('# '): flush(); out.append('<h1>'+html.escape(line[2:])+'</h1>')
  elif line.startswith('## '): flush(); out.append('<h2>'+html.escape(line[3:])+'</h2>')
  else: paragraph.append(line)
 flush(); return '\n'.join(out)
def policy_page(p):
 sources=''.join('<li><a href="'+html.escape(s['timestamp_url'],quote=True)+'">'+html.escape(s['title'])+' at '+str(s['excerpt_start_seconds'])+' seconds</a><blockquote>'+html.escape(s['quote'])+'</blockquote><p class="meta">'+html.escape(s['transcript_type'])+'</p></li>' for s in p['sources'])
 return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(p['title'])+'</title><link rel="stylesheet" href="../assets/style.css"></head><body><a class="skip" href="#main">Skip to content</a><header><p><a href="../index.html">Back to all policies</a></p><p class="eyebrow">Public alpha · '+html.escape(p['editorial_status'].replace('_',' '))+'</p></header><main id="main">'+markdown_to_html(p['body_markdown'])+'<h2>Proposal</h2><p>'+html.escape(p['proposal'])+'</p><h2>Source excerpts</h2><ol>'+sources+'</ol></main><footer>Attribution: Larry Sharpe · Public alpha</footer></body></html>'
def build():
 policies=[load_policy(p) for p in sorted(CONTENT.glob('*.md'))]; ids=[p['id'] for p in policies]; slugs=[p['slug'] for p in policies]
 if len(ids)!=len(set(ids)): raise ValueError('duplicate policy id')
 if len(slugs)!=len(set(slugs)): raise ValueError('duplicate policy slug')
 snapshot={'snapshot_version':'0.1.0','schema_version':'1.0.0','policies':policies}; payload=(json.dumps(snapshot,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode(); checksum=hashlib.sha256(payload).hexdigest()
 if DIST.exists(): shutil.rmtree(DIST)
 (DIST/'assets').mkdir(parents=True); (DIST/'policies').mkdir()
 (DIST/'policy-snapshot-v0.1.0.json').write_bytes(payload); shutil.copy2(ROOT/'schema'/'policy.schema.json',DIST/'policy.schema.json'); shutil.copy2(ROOT/'static'/'style.css',DIST/'assets'/'style.css'); shutil.copy2(ROOT/'static'/'app.js',DIST/'assets'/'app.js')
 links=''.join('<li><a href="policies/'+html.escape(p['slug'])+'.html">'+html.escape(p['title'])+'</a></li>' for p in policies); index=(ROOT/'templates'/'index.html').read_text(encoding='utf-8').replace('{{POLICY_LINKS}}',links); (DIST/'index.html').write_text(index,encoding='utf-8',newline='\n')
 for p in policies: (DIST/'policies'/(p['slug']+'.html')).write_text(policy_page(p),encoding='utf-8',newline='\n')
 sitemap='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>https://larrysharpeofficial.github.io/policy-knowledge-base/policies/'+p['slug']+'.html</loc></url>' for p in policies)+'</urlset>\n'; (DIST/'sitemap.xml').write_text(sitemap,encoding='utf-8',newline='\n')
 llms='# Larry Sharpe Policy Knowledge Base\n\nPublic alpha. Canonical snapshot: /policy-knowledge-base/policy-snapshot-v0.1.0.json\n\n'+'\n'.join('- ['+p['title']+'](/policy-knowledge-base/policies/'+p['slug']+'.html): '+p['proposal'] for p in policies)+'\n'; (DIST/'llms.txt').write_text(llms,encoding='utf-8',newline='\n')
 manifest={'snapshot_version':'0.1.0','schema_version':'1.0.0','sha256':checksum,'source_commit':os.environ.get('SOURCE_COMMIT','uncommitted-local-prototype'),'policy_count':len(policies)}; (DIST/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n'); (DIST/'policy-snapshot-v0.1.0.sha256').write_text(checksum+'  policy-snapshot-v0.1.0.json\n',encoding='ascii',newline='\n')
 print(json.dumps({'built':len(policies),'snapshot':'0.1.0','sha256':checksum,'dist':str(DIST)})); return manifest
if __name__=='__main__': build()
