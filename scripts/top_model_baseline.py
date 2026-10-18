"""User-approved top-model baseline. Read source analysis; write tour assets only.

Unlike the original power-normalized conversion (130 versus 135 kW), convert
GB300 chips directly to 72-chip Rubin racks at the assumed 2.5x rack throughput.
All scenarios include the same 14 kW support allowance and 1.10 PUE.
"""
import hashlib
import html
import importlib.util
import json
import math
import re
import sys


def sizing(root):
    path = root.parent / 'analysis/case_sizing.py'
    spec = importlib.util.spec_from_file_location('seed_sizing_source', path)
    analysis = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(analysis)
    finally:
        sys.dont_write_bytecode = previous
    users, _, output, input_rate = analysis.CASES['C knowledge workers']
    assumptions = dict(users=users, promptsPerDay=20, agentTasksPerDay=5,
                       outputPerSecond=output, inputPerSecond=input_rate,
                       prefillGain=analysis.PREFILL_X, gpusPerRack=72,
                       rubinRackThroughputGain=2.5, computeRackKW=210,
                       supportRackKW=14, pue=1.10, capMW=500,
                       computeRackPriceMillion=7.8, fullLoadHoursPerYear=8760)
    def result(gb_gpus):
        racks = gb_gpus / (assumptions['gpusPerRack'] * assumptions['rubinRackThroughputGain'])
        it_mw = racks * (assumptions['computeRackKW'] + assumptions['supportRackKW']) / 1000
        site_mw = it_mw * assumptions['pue']
        return dict(gb300EquivalentGPUs=gb_gpus, racks=racks, gpus=racks*72,
                    itMW=it_mw, siteMW=site_mw, capPercent=site_mw/500*100,
                    servedPercent=min(100,500/site_mw*100),
                    servedUsers=min(users,users*500/site_mw),
                    annualTWhAtFullLoad=site_mw*8760/1e6,
                    computeRackPurchaseB=racks*7.8/1000)
    scenarios = {}
    for key, mix in [('fast','All fast'),('mixed20','Agent tasks 80% fast, 20% mid'),
                     ('mixed50','Agent tasks 50% fast, 50% mid'),
                     ('premium','Premium: chat 20% mid; tasks 30% mid, 10% top')]:
        scenarios[key] = [result(n*analysis.FLEET_GPUS) for n in analysis.mix_need(mix,'benchmark')]
    scenarios['heavy'] = [result(analysis.gpus_needed(users,output,input_rate,r,r*analysis.PREFILL_X))
                          for r in reversed(analysis.DECODE['Llama 3.1 405B'])]
    return dict(revision='top-model-01', assumptions=assumptions,
                outputEquivalentTokensPerSecond=users*(output+input_rate/analysis.PREFILL_X),
                scenarios=scenarios,
                wholeRacksWithin500MW=math.floor(500/1.10*1000/224),
                sourceHashes={str(p.relative_to(root.parent)):hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in [path,root.parent/'analysis/budget.py']},
                notes=[
                    'User requirement: top-quality model for every request; Llama 3.1 405B is a provisional heavy reference, not proof of best quality.',
                    'Preserves case C peak workload. No additional concurrency discount or unmeasured batching/cache multiplier.',
                    '2.5x throughput per Rubin rack, transferred from DeepSeek-R1, remains an assumption for every model.',
                    'Direct chip-to-rack conversion raises the old fast-model rack estimate by about 4%.',
                    '500 MW is treated conservatively as total facility power before any solar credit.',
                    'Annual energy assumes the calculated full load for all 8760 hours; it is not a demand forecast.',
                    'Rack prices are inherited planning estimates. Rack purchase is not a five-year project budget.',
                    'The old R1-specific context-memory capacity and price are not validated for the heavy model.'
                ])


def apply(content, root):
    calc = sizing(root)
    content['planningRevision'] = calc['revision']
    (root/'assets/top-model-sizing.json').write_text(json.dumps(calc,ensure_ascii=False,indent=2)+'\n')
    heavy = calc['scenarios']['heavy']
    fast = calc['scenarios']['fast']
    def span(values, digits=0):
        return '–'.join(f'{v:,.{digits}f}' for v in values)
    def field(rows, key, divisor=1, digits=0):
        return span([r[key]/divisor for r in rows],digits)
    figures = dict(powerGW=field(heavy,'siteMW',1000,1),
                   racks=span([round(r['racks']/100)*100 for r in heavy]),
                   chipsMillion=field(heavy,'gpus',1e6,1),
                   annualTWh=field(heavy,'annualTWhAtFullLoad'),
                   purchaseB=field(heavy,'computeRackPurchaseB'),
                   servedMillion=span([r['servedUsers']/1e6 for r in reversed(heavy)]))
    comparison = [
        ['Compute racks for all 400M',span([round(r['racks']/10)*10 for r in fast]),figures['racks']],
        ['AI chips',span([round(r['gpus']/1000)*1000 for r in fast]),figures['chipsMillion']+' million'],
        ['Total facility power at full load',field(fast,'siteMW')+' MW',figures['powerGW']+' GW'],
        ['Electricity at that load all year',field(fast,'annualTWhAtFullLoad',1,1)+' TWh',figures['annualTWh']+' TWh'],
        ['Compute-rack purchase only','$'+field(fast,'computeRackPurchaseB',1,1)+'B','$'+figures['purchaseB']+'B'],
        ['Users’ workload within 500 MW','400 million',figures['servedMillion']+' million']
    ]
    labels = dict(heavy='Top model for everyone · baseline',fast='Fast models · comparison',
                  mixed20='20% of agent tasks on mid tier · comparison',
                  mixed50='50% of agent tasks on mid tier · comparison',
                  premium='Premium mix · comparison')
    mixes = dict(heavy='Every question and agent task uses the Llama 3.1 405B heavy reference.',
                 fast='Every question and agent task uses the gpt-oss-120b fast reference.',
                 mixed20='Chat stays fast; agent tasks use 80% fast and 20% mid.',
                 mixed50='Chat stays fast; agent tasks use 50% fast and 50% mid.',
                 premium='Chat: 80% fast, 20% mid. Tasks: 60% fast, 30% mid, 10% heavy.')
    scenarios=[]
    for key in ['heavy','fast','mixed20','mixed50','premium']:
        rows=calc['scenarios'][key]
        served=sorted(r['servedPercent'] for r in rows)
        scenarios.append(dict(id=key,label=labels[key],mix=mixes[key],
            low=round(rows[0]['capPercent']),high=round(rows[1]['capPercent']),
            served='100%' if served[0]==100 else span(served,1)+'%',
            power=field(rows,'siteMW',1000,1)+' GW' if rows[0]['siteMW']>=1000 else field(rows,'siteMW')+' MW',
            users=span([r['servedUsers']/1e6 for r in reversed(rows)])+' million' if served[0]<100 else '400 million',
            meaning=('The baseline exceeds the 500 MW limit by about 15 times. Keeping that limit supports about '+figures['servedMillion']+' million users’ assumed workload, not all 400 million.' if key=='heavy' else
                     'Comparison only. This changes model use and does not meet the top-model-for-every-request requirement.')))
    content['modelEnergy']=dict(source='Top-model revision · case C inputs and benchmark references · rack assumptions from the supplied budget',
        defaultScenario='heavy', demand=calc['assumptions'],figures=figures,comparison=comparison,scenarios=scenarios,
        models=[dict(name=name,tier=tier,rate=[round(r) for r in rates],work=work,description=description) for name,tier,rates,work,description in [
            ('Llama 3.1 405B','Baseline',[617,646],'~29–34×','Provisional heavy reference. Largest in this study does not establish best answer quality.'),
            ('gpt-oss-120b','Fast',[18760,21000],'1×','Previous fast-model approach, retained only for comparison.'),
            ('DeepSeek-R1','Mid',[8230,10023],'~2–3×','Mid-tier comparison and source of the assumed Rubin hardware gain.')]])
    b=content['bubbles']
    reference_assumption='Llama 3.1 405B is a heavy-model proxy; its quality is not a validated match for the best model. Rubin’s 2.5× per-rack gain is assumed.'
    refs=[dict(tier='Baseline proxy',name='Llama 3.1 405B'),dict(tier='Comparisons',name='gpt-oss-120b / DeepSeek-R1')]
    for i in [0,3,8,10,11,12]:
        b[i].update(referenceModels=refs,referenceSource='User-approved top-model baseline · 18 October 2026',referenceAssumption=reference_assumption)
    b[0].update(headline='SEED: the top model, within a power limit',
        bullets=['500 MW and $30B across six campuses','Goal: 400 million people, all using the top model','Current heavy-model estimate: 26–27 million within the cap'],
        number='400 million',unit='people targeted · capacity still falls short',
        assumption='The same workload: 20 questions + 5 agent tasks per person daily. The heavy reference stands in for the top model.',
        source='Challenge targets · revised sizing estimate',
        why='SEED means Sustainable, Energy-Efficient Datacenters. The new requirement is the top model for every request. We keep the 400-million-user goal and show the capacity gap explicitly.')
    b[1].update(number='52,000–55,000',unit='users’ workload per MW · heavy-reference estimate',
        assumption='The same peak workload and hardware assumptions as the top-model baseline.',source='Revised sizing · users per MW')
    b[1]['card']['math']=['Users per MW: ~26.2–27.4 million users’ workload ÷ 500 MW ≈ 52,000–55,000.',
        'The previous carbon-per-user figure divided by 400 million. Embodied carbon and water per user must be recalculated for the actual fleet and workload served.']
    b[3]['bullets'][0]='368 rack positions shown; ~338 fit per site at the midpoint power assumption'
    b[3].update(number='210 kW',unit='per compute rack + 14 kW for networking and storage',
                assumption='210 kW is the midpoint of the reported 190–230 kW range; the 368-rack drawing uses the lower end.')
    b[3]['card']['math'][0]='The drawing has 368 compute racks × 72 GPUs = 26,496 GPUs. At 210 + 14 kW and 1.10 PUE, a full drawn site would use ~90.7 MW; its ~83.3 MW allowance fits about 338 active rack pairs. At 190 + 14 kW, the drawing uses ~82.6 MW.'
    b[3]['card']['math'].append('Serving all 400 million on the heavy reference requires about 29,600–31,000 compute racks across a much larger fleet. This campus is one part of the original 500 MW concept.')
    b[8].update(headline='500 MW stays our power limit',
        bullets=['Six campus allowances of about 83 MW each','All 400 million on the heavy reference need ~7.3–7.6 GW','Clean-power contracts do not increase the allowed capacity'],
        number='500 MW',unit='fleet limit · heavy-model demand is about 15× higher',
        assumption='Sizing includes networking, storage support and cooling, before a solar credit.',source='Revised sizing · total facility power')
    b[8]['card']['math']=['500 MW × 8,760 h = 4.38 TWh if the capped fleet runs at full power all year.',
        'Serving the full heavy-model workload needs ~7.3–7.6 GW at the midpoint rack draw. Holding that full load all year would use ~64–67 TWh; this is not an annual demand forecast.']
    b[9]['card']['math'][0]='Fuel for the existing full campus: 48 h × ~82 MW × ~0.28 L/kWh ≈ 1.1 million litres. A larger fleet requires a new backup-power and fuel plan.'
    b[10].update(headline='The top model changes our capacity',
        bullets=['Every question and agent task uses the heavy reference','The 400-million-user goal needs ~7.3–7.6 GW','At 500 MW, about 6.6–6.9% of the assumed workload fits'],
        number='26–27 million',unit='users’ workload within 500 MW · planning estimate',
        assumption='The same peak usage, cached context, 210 + 14 kW per rack pair and 1.10 PUE.',
        source='Top-model baseline · revised sizing',
        why='Top-model access is the requirement. Capacity must follow the work that fits within the power limit, rather than a fast-model result.')
    b[10]['card']=dict(title='Capacity with the top model',what='A 500 MW fleet serving every request on the top model, provisionally sized using Llama 3.1 405B.',
        why=b[10]['why'],how='Batch requests, reuse available context and schedule jobs on the same model. These techniques already inform the sizing basis; no extra saving is assumed.',
        math=['400 million × (4.6 + 40 ÷ 10) = 3.44 billion output-equivalent tokens per second at the modeled peak.',
              'Divide by the adjusted heavy-reference speed (~617–646 tokens/s per GB300 GPU), then by 72 GPUs and the assumed 2.5× Rubin rack gain: ~29,600–31,000 compute racks.',
              'Racks × (210 + 14) kW × 1.10 = ~7.3–7.6 GW of total facility power.',
              '400 million × 500 MW ÷ required facility MW = ~26–27 million users’ equivalent workload within the cap. Response-time and quality targets still require testing.'])
    b[11].update(headline='The full workload exceeds the budget',
        bullets=['~29,600–31,000 compute racks for all 400 million','Compute racks alone exceed the entire $30B budget','Buildings, support systems and electricity cost extra'],
        number='$231–242B',unit='compute-rack purchase only · not a five-year total',
        assumption='$7.8M per compute rack, the existing analyst-based midpoint; no vendor quote.',
        source='Revised rack count × inherited price assumption',
        why='Everyone using the heavy reference needs roughly 30 times the fast-model hardware. The previous $15.8–17.2B five-year estimate no longer applies.')
    b[12].update(headline='Efficiency helps; the gap remains',
        bullets=['Same computer work: ~24% less total power at PUE 1.10 vs 1.44','Within 500 MW: ~31% more power available to computers','The full top-model workload still needs a much larger fleet'],
        number='~24%',unit='less total power for the same computer load',
        assumption='PUE 1.10 is a design allowance; 1.44 is the supplied large-datacenter comparison.',
        source='PUE comparison · revised planning baseline',
        why='Efficient cooling still matters when every request uses the top model. It improves useful capacity, but does not remove the compute demand or establish a new project payback.')
    b[12]['designKeys']=['efficiency','budget']
    content['objects']['compute']['number']='368 positions drawn; ~338 active per campus at the midpoint power assumption'
    content['objects']['compute']['text']+=' The drawing uses the lower rack-power case; the midpoint sizing includes a separate 14 kW support rack per compute rack.'
    content['labels'][0]='Sealed data halls: 368 rack positions drawn; ~338 fit at midpoint power'

    def section(key,title,why,paragraphs,numbers=()):
        old=content['design'].get(key,{})
        notes=old.get('notes','')
        # Preserve source links and explicit engineering checks, not obsolete budget prose.
        refs=' · '.join(re.findall(r'<a\b[^>]*>.*?</a>',notes))
        copy=''.join('<p>'+p+'</p>' for p in paragraphs)
        if numbers: copy+='<div class="nums"><dl>'+''.join('<div><dt>'+html.escape(k)+'</dt><dd>'+html.escape(v)+'</dd></div>' for k,v in numbers)+'</dl></div>'
        content['design'][key]=dict(title=title,why='<p>'+why+'</p>',html=copy,
            notes='<span><strong>Planning basis</strong>User-approved top-model revision. Original source links support individual inputs; their older scenario totals are superseded here.</span><span><strong>Sources</strong>'+refs+'</span>')
    section('scope','Six-campus concept; full top-model demand is larger',b[0]['why'],[
        'The challenge sets 400 million knowledge workers, six sites, a 500 MW power limit and $30B over five years. The user now requires the top model for every request.',
        'We preserve 20 chat questions and five agent tasks per person per day, along with the original peak rates. Agent tasks can make multiple model calls. The fleet is shared; no additional concurrency discount is applied.',
        'The Blender model remains the original Cambridge campus concept. Its cooling and backup equipment describe that campus, not an engineered 7.3–7.6 GW expansion.',
        'Cambridge land, grid access, a suitable parcel and rock conditions remain unresolved. The site is illustrative.'],
        [('User target','400 million'),('Within 500 MW, heavy reference','~26–27 million users’ workload'),('Full workload facility power','~7.3–7.6 GW')])
    section('models','Top model for every request',b[10]['why'],[
        '<b>Service requirement:</b> every chat question and agent task may use the top-quality model. Llama 3.1 405B is the provisional heavy reference from the study, not proof of best answer quality or the exact cost of a proprietary model.',
        'The other references, gpt-oss-120b and DeepSeek-R1, are comparison cases only. Switching to them changes the requirement.',
        'The calculation retains cached context and benchmark throughput. Batching, prompt reuse and scheduling must be measured together; they are not additional assumed multipliers.',
        'Validate representative long documents, reasoning and agent jobs, output quality, response time, concurrent load, cache hits and misses, and whole-system energy before committing to capacity.'],
        [('Peak equivalent output','3.44 billion tokens/s'),('Heavy-reference speed, adjusted','~617–646 tokens/s/GB300 GPU'),('Rubin throughput gain, assumed','2.5× per 72-GPU rack')])
    section('computers','Rack count follows the top-model workload',b[3]['why'],[
        'The 72-GPU Vera Rubin rack remains the hardware reference. New sizing converts required GB300 GPUs directly to racks at an assumed 2.5× per-rack throughput gain. The source measured that gain on DeepSeek-R1; applying it to Llama is an assumption.',
        'Power uses 210 kW per compute rack, plus 14 kW for networking and storage support, then a 1.10 total-facility-to-IT power ratio. Extra context storage may change that allowance.',
        'The drawing has 368 populated compute positions per campus and about 26,500 GPUs, based on the 190 kW lower-power case. At the 210 kW midpoint, about 338 rack pairs fit each ~83.3 MW campus allowance. The six-site fleet fits about 2,029 whole rack pairs at 500 MW, before reliability reserves.',
        'The previous 876–980-rack first purchase is no longer the plan. Its fast-model comparison is now ~910–1,020 racks after the direct conversion correction.'],
        [('Heavy workload: compute racks','~29,600–31,000'),('Heavy workload: Rubin GPUs','~2.1–2.2 million'),('Within 500 MW at midpoint','~2,029 rack pairs')])
    section('memory','Reuse context; validate the heavy model’s memory needs',
        'Caching can avoid processing the same input again, while new answers still require compute. Its capacity and bandwidth must match the chosen model.',[
        'The calculation assumes available context can be reused. Long contexts, cache misses and moving cached data through the storage system can reduce throughput.',
        'The old ~2.3 EB, ~5.7 GB/user and $1.5–1.8B flash estimates were based on DeepSeek-R1 and an assumed FP8 cache. They are not validated storage figures for Llama 3.1 405B or a future top model.',
        'Recalculate cache bytes per token, active sessions, retention and eviction, memory-tier bandwidth, support power and cost for the selected model. The new rack-price subtotal excludes this redesign.'])
    section('budget','The full top-model workload exceeds $30B',b[11]['why'],[
        '<b>$231–242B is compute-rack purchase only.</b> It comes from ~29,600–31,000 racks × the inherited $7.8M midpoint estimate. It is not a total build cost or five-year budget.',
        'Separate networking, context memory, land, buildings, grid connections, backup, cooling, electricity and operations still need a revised budget. A 7.3–7.6 GW fleet is an extrapolation, not a designed expansion.',
        'The old $15.8–17.2B total, $13–14B left over, ~$90M annual electricity saving and ~2.5-year payback belonged to the fast-model scenario. None is a claim about the new baseline.',
        'The existing 500 MW concept can support about 26–27 million users’ assumed heavy-model workload. Its updated cost and reliability margins also require review.'],
        [('Full workload compute-rack purchase','$231–242B'),('Five-year budget constraint','$30B'),('New five-year total','Not yet established')])
    section('efficiency','Cooling efficiency still improves useful capacity',b[12]['why'],[
        'For the same computer and networking load, 1 − 1.10 ÷ 1.44 = 23.6% less total facility power. This compares the SEED design allowance with the supplied large-datacenter PUE reference.',
        'Under a fixed 500 MW limit, 500 ÷ 1.10 ≈ 455 MW reaches IT equipment versus 500 ÷ 1.44 ≈ 347 MW: about 31% more IT power available.',
        'These are power ratios, not evidence that the full top-model workload fits. New dollar savings, water totals, cooling layouts and payback require a design and operating schedule for the actual fleet.'])
    # Other stops keep their campus-specific thermal design. Remove first-tranche
    # budget quantities that otherwise imply the superseded fast-model purchase.
    backup=content['design']['backup']
    start=backup['html'].find('<div class="nums">')
    if start!=-1:
        backup['html']=backup['html'][:start]+'<p>The shown full-campus concept stores about 1.1 million litres for 48 hours. A larger fleet requires a new backup-power, fuel and cost calculation.</p></div>'
    content['design']['power']['html']+='<p><b>Top-model revision:</b> 500 MW remains the limit. Full heavy-model demand is ~7.3–7.6 GW before solar. The existing campus solar and grid design have not been scaled to that demand.</p>'
    for field in ['html','why']:
        content['design']['power'][field]=content['design']['power'][field].replace('fits 31% more chips','makes 31% more IT power available').replace('More chips under the cap than at PUE 1.44','More IT power under the cap than at PUE 1.44')
    content['design']['hall']['html']=content['design']['hall']['html'].replace('0.08–0.17 kg/user-yr','Recalculate for the new workload and fleet')
    content['design']['efficiency']['notes']='<span><strong>Source</strong>Supplied budget: PUE 1.10 design allowance versus Uptime Institute 2025 large-site PUE 1.44.</span>'
    return calc
