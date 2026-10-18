"""Import the supplied design, then apply the user-approved tour baseline revision."""
import re, json, pathlib, hashlib, html
from html.parser import HTMLParser
root = pathlib.Path(__file__).resolve().parent.parent
source = (root.parent/'HANDOFF-2026-10-18-SEED-datacenter.md').read_text()
spec = source.split('## 7. ')[1].split('## 8. ')[0]
(root/'assets/spec-source.md').write_text('## 7. '+spec)
def table(marker):
    lines=spec.split(marker,1)[1].split('\n')
    rows=[]; started=False
    for line in lines:
        if line.startswith('|'):
            started=True
            cells=[c.strip() for c in line.strip('|').split('|')]
            if not cells[0].startswith('---'): rows.append(cells)
        elif started: break
    return rows
bubbles=[]
for row in table('| Card |'):
    name,head,bullets,big,assume,tag=row
    number,unit=re.match(r'\*\*(.+?)\*\*\s*(.*)',big).groups()
    bubbles.append(dict(name=name,headline=head,bullets=[b.strip() for b in bullets.split('•') if b.strip()],number=number,unit=unit,assumption=assume if assume!='—' else '',source=tag))
# Marker includes header; table() therefore sees separator before the data.
assert len(bubbles)==13,len(bubbles)
ids=['hall','roofSolar','sealed','compute','network','trench','fire','spine','electrical','bridges','coolers','chillers','boreholes','batteryHouse','solar','substation','generators','fuel','reserved','house','greenhouse','snowpad','dewpoint','freshAir','airlock','bypass','freezeProtection','drainTanks','coldInsulation']
objects={}
object_rows=table('| Object (element')
assert len(object_rows)==len(ids),f'Object mapping needs updating: {len(object_rows)} source rows, {len(ids)} ids'
for key,row in zip(ids,object_rows):
    name,text,number,math,why=row
    objects[key]=dict(name=re.sub(r' \([\d, ]+(?:X-ray|ground cutaway)?\)$','',name),text=text,number=number,math=math if math!='—' else '',why=why)
assert len(objects)==29
cams=table('| # | Stop |')
for i,row in enumerate(cams,1):
    nums=re.findall(r'\(([^)]+)\)',row[2])
    bubbles[i]['camera']=[[float(n.strip().replace('−','-')) for n in p.split(',')] for p in nums]
    bubbles[i]['toggles']=row[3]
for i in (0,11,12): bubbles[i]['camera']=[[-450,-450,250],[0,0,0]];bubbles[i]['toggles']='—'
anchors=['#users','#carbon','#solar','#racks','#chip-loop','#chip-loop','#room-air','#greenhouse','#grid','#backup','#users','#budget','#baseline']
featured=[[],['house'],['solar','roofSolar'],['sealed','compute','network','trench','fire','dewpoint','freshAir'],['spine','bridges','trench','drainTanks'],['coolers','bridges','bypass','freezeProtection'],['boreholes','batteryHouse','chillers','coldInsulation'],['greenhouse'],['substation'],['generators','fuel','reserved','electrical'],[],[],[]]
for i,b in enumerate(bubbles): b.update(anchor=anchors[i],featured=featured[i])
cardtext=spec.split('**Card text for each stop**',1)[1].split('**Left to the builder:**')[0]
for match in re.finditer(r'(?m)^(\d+)\. \*\*(.+?)\*\*\n([\s\S]*?)(?=^\d+\. \*\*|\Z)',cardtext):
    i=int(match[1]); body=match[3]; card={ 'title':match[2] }
    for label,key in [('What we chose','what'),('Why','why'),('How it works','how')]:
        card[key]=re.search(r'\*'+re.escape(label)+r':\* (.+)',body)[1]
    math=body.split('*Show the math:*',1)[1].strip()
    card['math']=[re.sub(r'^\s*-\s*','',s.strip()) for s in math.splitlines() if s.strip()]
    bubbles[i]['card']=card
labels=re.findall(r'^- "(.+)"$',spec.split('**Labels**',1)[1].split('**Virtual tour**')[0],re.M)
# User-requested reference models, grounded in handoff section 5 (Model tiers).
reference_models=[dict(tier='Fast',name='gpt-oss-120b'),dict(tier='Mid',name='DeepSeek-R1'),dict(tier='Top',name='Llama 3.1 405B')]
for i in (3,10,11,12):
    bubbles[i]['referenceModels']=reference_models
    bubbles[i]['referenceSource']='Handoff §5 · measured open-model speed tests (MLPerf v6.0, GB300)'
    bubbles[i]['referenceAssumption']='We assume Vera Rubin’s gain measured on DeepSeek-R1 applies to all three tiers.'
model_energy={}  # Populated by the user-approved top-model revision below.
# Bring the supplied basis of design into the tour. Keep its source notes and
# unresolved checks, but never copy scripts, inline styles or event handlers.
class Node:
    def __init__(self, tag='', attrs=()): self.tag=tag; self.attrs=dict(attrs); self.children=[]
    def text(self): return ''.join(c.text() if isinstance(c,Node) else c for c in self.children).strip()
    def find(self, predicate):
        return [n for c in self.children if isinstance(c,Node) for n in ([c] if predicate(c) else [])+c.find(predicate)]
class Document(HTMLParser):
    def __init__(self): super().__init__(); self.root=Node(); self.stack=[self.root]
    def handle_starttag(self, tag, attrs):
        n=Node(tag,attrs); self.stack[-1].children.append(n)
        if tag not in ('br','hr','img','meta','link','input'): self.stack.append(n)
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==tag: self.stack=self.stack[:i]; break
    def handle_data(self, text): self.stack[-1].children.append(text)
allowed={'div','p','h4','strong','em','a','span','dl','dt','dd','ul','ol','li','table','thead','tbody','tr','th','td','br','sup','sub'}
def clean(n):
    if isinstance(n,str): return html.escape(n)
    if n.tag in ('script','style'): return ''
    children=''.join(clean(c) for c in n.children)
    if n.tag not in allowed: return children
    attrs=''
    if n.tag=='a' and n.attrs.get('href','').startswith('https://'):
        attrs=' href="'+html.escape(n.attrs['href'],quote=True)+'" target="_blank" rel="noopener"'
    classes=set(n.attrs.get('class','').split()) & {'nums','tablewrap','todo','changed','flag','n','total'}
    if classes: attrs+=' class="'+' '.join(sorted(classes))+'"'
    return '<'+n.tag+attrs+'>'+children+('' if n.tag=='br' else '</'+n.tag+'>')
design_source=(root.parent/'appendix/seed-basis-of-design.html').read_text()
doc=Document();doc.feed(design_source);design={}
for section in doc.root.find(lambda n:n.tag=='section' and 'dec' in n.attrs.get('class','').split()):
    key=section.attrs['id']; bodies=section.find(lambda n:'dec-body' in n.attrs.get('class','').split())
    if not bodies: continue
    body=bodies[0]; why=next((n for n in body.children if isinstance(n,Node) and any(c.tag=='h4' and c.text()=='Why' for c in n.children if isinstance(c,Node))),None)
    footer=section.find(lambda n:n.tag=='footer')
    design[key]=dict(title=section.find(lambda n:n.tag=='h3')[0].text(),html=clean(body),why=''.join(clean(c) for c in why.children if not isinstance(c,Node) or c.tag!='h4') if why else '',notes=''.join(clean(c) for c in footer[0].children) if footer else '')
design_keys=[['scope'],['house'],['power'],['computers','sealed','memory','fire'],['chip-loop','fluid','hall'],['chip-loop','fluid'],['room-air','fluid'],['house'],['power'],['backup','fluid'],['models','computers'],['budget'],['budget']]
object_keys=[['hall','house','solar','substation'],['house','greenhouse'],['solar','roofSolar'],['compute','network','sealed','trench','fire','electrical','dewpoint','freshAir','airlock'],['spine','bridges','trench','drainTanks'],['coolers','bypass','freezeProtection','bridges','chillers'],['boreholes','batteryHouse','coldInsulation','chillers'],['greenhouse'],['substation'],['generators','fuel','reserved','electrical'],['compute','network'],['compute','solar','generators'],['coolers','boreholes','solar','generators']]
closing_why={0:'One detailed design is repeated across six campuses to meet the challenge’s 500 MW limit.',11:'Fast models handle most work, so the plan can serve the modeled demand without buying enough racks to fill the entire power cap.',12:'The extra equipment costs more to build, but lower electricity use is estimated to save about $90M a year.'}
for i,b in enumerate(bubbles):
    b.update(designKeys=design_keys[i],objectKeys=object_keys[i],why=b['card']['why'] if 'card' in b else closing_why[i])
assert all(k in design for b in bubbles for k in b['designKeys'])
assert all(o['why'].lstrip('#') in design for o in objects.values())
content=dict(bubbles=bubbles,objects=objects,labels=labels,design=design,modelEnergy=model_energy,mathURL='https://claude.ai/artifact/8ofePKB934K361bVkuPRN4',whyURL='https://claude.ai/artifact/65FXnUpGEvJaqCACavodDt',sourceSHA256=hashlib.sha256(source.encode()).hexdigest(),designSHA256=hashlib.sha256(design_source.encode()).hexdigest())
# Apply the later user instruction without modifying the original source documents.
import importlib.util
revision_spec=importlib.util.spec_from_file_location('top_model_baseline',root/'scripts/top_model_baseline.py')
revision=importlib.util.module_from_spec(revision_spec)
revision_spec.loader.exec_module(revision)
revision.apply(content,root)
(root/'assets/content.json').write_text(json.dumps(content,ensure_ascii=False,indent=2)+'\n')
print(f'Imported {len(bubbles)} bubbles, {len(objects)} explainers, {sum("card" in b for b in bubbles)} detail cards, {len(labels)} labels.')
