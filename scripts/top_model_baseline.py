"""Fixed case C workload, heavy model for every request, fixed campus capacity."""
import hashlib
import html
import importlib.util
import json
import math
import re
import sys


def sizing(root):
    path=root.parent/'analysis/case_sizing.py'
    spec=importlib.util.spec_from_file_location('seed_sizing_source',path)
    analysis=importlib.util.module_from_spec(spec)
    previous=sys.dont_write_bytecode
    sys.dont_write_bytecode=True
    try:
        spec.loader.exec_module(analysis)
    finally:
        sys.dont_write_bytecode=previous
    users,reads,output,input_rate=analysis.CASES['C knowledge workers']
    a=dict(targetUsers=users,promptsPerDay=20,agentTasksPerDay=5,campuses=6,
           fleetCapMW=500,campusCapMW=500/6,outputPerSecond=output,
           inputPerSecond=input_rate,referenceContextReadsPerUserDay=reads,
           prefillGain=analysis.PREFILL_X,gpusPerRack=72,rubinRackThroughputGain=2.5,
           computeRackKW=210,supportRackKW=14,pue=1.10,computeRackPriceMillion=7.8)
    pair_mw=(a['computeRackKW']+a['supportRackKW'])*a['pue']/1000
    racks=math.floor(a['campusCapMW']/pair_mw)
    rates=list(analysis.DECODE['Llama 3.1 405B'])
    work=output+input_rate/a['prefillGain']
    per_site=[racks*a['gpusPerRack']*a['rubinRackThroughputGain']*r/work for r in rates]
    fleet=[n*a['campuses'] for n in per_site]
    required_racks=[users*work/(72*2.5*r) for r in reversed(rates)]
    return dict(revision='fixed-workload-03',assumptions=a,
        hardware=dict(racksPerCampus=racks,racksFleet=racks*a['campuses'],
            gpusPerCampus=racks*72,gpusFleet=racks*72*a['campuses'],
            loadedCampusMW=racks*pair_mw,loadedFleetMW=racks*pair_mw*a['campuses'],
            computeRackPurchasePerCampusB=racks*7.8/1000,
            computeRackPurchaseFleetB=racks*a['campuses']*7.8/1000,
            adjustedHeavyTokensPerGPUSecond=rates),
        baseline=dict(workPerUserAtPeak=work,usersPerCampus=per_site,usersFleet=fleet,
            targetPercent=[n/users*100 for n in fleet],
            facilityMWForTarget=[n*pair_mw for n in required_racks],
            computeRacksForTarget=required_racks),
        sourceHashes={str(p.relative_to(root.parent)):hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in [path,root.parent/'analysis/budget.py']},
        notes=[
            'User correction: preserve 20 questions and five agent tasks per person daily. A task may make several AI calls. Case C peak rates remain 4.6 output and 40 new input tokens/s per source user.',
            'The heavy reference stands in for the top model on every question and task. No weaker-model routing is assumed.',
            'Peak rates are population-normalized sizing inputs, not continuous per-user generation rates. No eight-hour coding, daily-token integration, shift or quota-wait capacity multiplier is used.',
            'Reported headcount is the population whose assumed workload fits at the source peak rates, not the number of simultaneous chat sessions.',
            'Llama 3.1 405B is a provisional hardware proxy, not measured Opus performance or proof of equal answer quality. The 2.5x Rubin gain is transferred from R1.',
            'Capacity precedes reliability reserves, long-context attention, memory bandwidth, response-time guarantees and any additional storage power. The range covers benchmark endpoints only.',
            'Energy requires an operating-load schedule. Full-load MW is not an annual MWh forecast.',
            '338 rack pairs fit each campus; six independently capped campuses hold 2028 pairs.',
        ])


def apply(content, root):
    calc=sizing(root)
    content['planningRevision']=calc['revision']
    (root/'assets/top-model-sizing.json').write_text(json.dumps(calc,ensure_ascii=False,indent=2)+'\n')
    a,h=calc['assumptions'],calc['hardware']
    def span(values,divisor=1,digits=0):
        return '–'.join(f'{n/divisor:,.{digits}f}' for n in values)
    def people(values):
        return span(values,1e6,2)+'M' if min(values)>=1e6 else span([round(n/10000)*10 for n in values])+'k'
    base=calc['baseline']
    per_site=people(base['usersPerCampus'])
    fleet=span(base['usersFleet'],1e6,1)+' million'
    content['modelEnergy']=dict(demand=a,hardware=h,baseline=base,
        perCampus=per_site,fleet=people(base['usersFleet']),served=span(base['targetPercent'],1,2)+'%',
        targetPowerGW=span(base['facilityMWForTarget'],1000,1),
        source='Same daily workload: 20 questions + 5 agent tasks. Case C peak rates: 4.6 output + 40 new input tokens/s per user. Heavy reference for the top model.',
        models=[dict(name='Llama 3.1 405B',tier='Hardware proxy',rate=[round(n) for n in h['adjustedHeavyTokensPerGPUSecond']],work='~29–34×',description='Used for all capacity figures. Not a measurement of Claude Opus or a claim about which model is best.'),
                dict(name='gpt-oss-120b',tier='Benchmark context',rate=[18760,21000],work='1×',description='Retained to explain relative chip time; no requests are routed to this model in the plan.'),
                dict(name='DeepSeek-R1',tier='Hardware-gain reference',rate=[8230,10023],work='~2–3×',description='Source of the assumed Rubin throughput gain. Its cache sizing does not establish the heavy model’s memory needs.')])
    b=content['bubbles']
    refs=[dict(tier='Service requirement',name='Strongest model throughout'),dict(tier='Hardware proxy',name='Llama 3.1 405B')]
    proxy='The heavy reference stands in for the top model. Peak sizing uses 4.6 output + 40 new input tokens/s per user; hardware transfer and cache behavior still need validation.'
    for i in [0,3,8,10,11,12]:
        b[i].update(referenceModels=refs,referenceSource='Fixed-workload correction · 18 October 2026',referenceAssumption=proxy)
    b[0].update(headline='The top model. The same power limit.',
        bullets=['20 questions and five agent tasks per person daily','The heavy reference stands in for the top model on every call',f'Fixed six-site design: ~{per_site} users’ workload per datacenter'],
        number='400 million',unit='people targeted · fixed-campus capacity is lower',
        assumption='20 questions + 5 agent tasks per person daily. Peak rates: 4.6 output and 40 new input tokens/s per user. The heavy reference stands in for the top model.',
        hideOverviewAssumption=True,
        source='Same workload · heavy-model capacity estimate',
        why='SEED means Sustainable, Energy-Efficient Datacenters. We keep each datacenter’s power fixed and calculate how much of the original 400-million-person workload fits when every call uses the heavy reference.')
    b[1].update(number='52,000–55,000',unit='users’ assumed workload per MW · illustrative',
        assumption='Same daily workload and heavy-model proxy; source peak rates, before reliability reserves and context bottlenecks.',source='Fixed workload · users per MW')
    b[1]['card']['math']=[f'~{per_site} users’ workload ÷ ~83.3 MW ≈ 52,000–55,000 users per MW.',
        'This is a population capacity estimate at the assumed peak rates, not a count of simultaneous conversations. Carbon and water per user need a validated operating schedule.']
    b[3]['bullets'][0]='368 rack positions drawn; 338 active rack pairs fit the midpoint power allowance'
    b[3].update(number='210 kW',unit='per compute rack + 14 kW for networking and storage',
        assumption='210 kW is the midpoint of the reported 190–230 kW range. The drawing uses the lower end; operating capacity uses 338 pairs.')
    b[3]['card']['math'][0]='At the midpoint: 338 × (210 + 14) kW × 1.10 ≈ 83.28 MW per campus; 338 × 72 = 24,336 active GPUs. The 368 drawn positions would use ~90.7 MW at this midpoint, so they cannot all run at that draw within the allowance.'
    b[3]['card']['math'].append('More calls, longer outputs and input reprocessing use more chip time. With fixed hardware and power, fewer users’ workload fits.')
    b[7]['bullets'][1]='At full IT load, ~75 MW becomes heat; the greenhouse needs well under 1 MW'
    b[7].update(unit='warm return-water design point · availability varies with load',
        assumption='~300 W/m² peak greenhouse demand, roughly estimated. Recoverable heat follows IT load; off-peak backup heat is not sized.')
    b[7]['card']['how']='Warm return water is designed around 124°F (51°C). Its usable heat output depends on the computers’ load; the workload assumption does not establish round-the-clock heat availability.'
    b[7]['card']['math']=['At modeled full load, the campus IT demand is ~75 MW and becomes heat. The 60 × 30 m greenhouse needs roughly 1,800 m² × 300 W/m² = 0.54 MW at peak. Heat recovered by this particular circuit and off-peak backup must still be engineered.']
    content['objects']['greenhouse'].update(text='Warm return water can heat it on the way to the coolers. Available heat follows IT load; off-peak backup heat remains to be sized.',number='~0.54 MW peak heating estimate')
    content['design']['house']['html']='<p><strong>Revised operating assumption:</strong> Recoverable heat follows IT load. The workload scenario does not establish a continuous 75 MW heat supply or guaranteed return temperature. Off-peak backup heating remains to be sized.</p>'+content['design']['house']['html']
    content['design']['house']['html']=content['design']['house']['html'].replace('Waste heat available','Total IT heat at full load')
    b[8].update(headline='The datacenter keeps its power limit',
        bullets=['About 83.3 MW per datacenter; 500 MW across six sites','More AI work per person reduces capacity, not the power limit','User sessions can pause while other users keep the machines busy'],
        number='83.3 MW',unit='power allowance per datacenter · unchanged',
        assumption='338 active rack pairs per site, 210 + 14 kW each, PUE 1.10; before a solar credit.',source='Fixed-campus design · operating scenario')
    b[8]['card']['math']=['338 × 224 kW × 1.10 = 83.2832 MW at modeled full load. Six sites total 499.6992 MW.',
        'At 83.28 MW, one hour at full load uses 83.28 MWh. Actual daily and annual energy depend on the load over time.',
        'Peak token rates size the hardware. They are not assumed to run continuously for eight or 24 hours, and no shift or quota-wait multiplier is added.']
    b[9]['card']['math'][0]='Fuel for the existing full campus: 48 h × ~82 MW × ~0.28 L/kWh ≈ 1.1 million litres. Fewer users do not shrink the backup requirement for a fully loaded campus.'
    b[10].update(headline='How many people fit in one datacenter?',
        bullets=['Same workload: 20 questions and five agent tasks per person daily',f'Six sites support ~{fleet} users’ assumed workload','The heavy reference handles every call; the 500 MW limit stays fixed'],
        number='~'+per_site,unit='users’ assumed workload per datacenter',
        assumption='4.6 output + 40 new input tokens/s per source user at peak; efficient context reuse; no reliability or latency reserve included.',
        source='Same workload · heavy-model capacity',
        why='The hardware supports the population whose assumed peak workload fits. The daily task count is unchanged; the heavy model uses more chip time, so fewer users fit within the fixed power limit.')
    b[10]['card']=dict(title='The same workload within a fixed campus',what=b[10]['bullets'][0],why=b[10]['why'],
        how='Each agent task may make several calls. The source workload already includes questions and agent tasks in its 4.6 output and 40 new input tokens/s peak rates. Do not multiply those rates by the task count again.',
        math=['338 rack pairs × (210 + 14) kW × 1.10 = 83.28 MW per campus.',
              'Peak work per source user: 4.6 output + 40 new input ÷ 10 = 8.6 output-equivalent tokens/s.',
              '338 × 72 GPUs × assumed 2.5× Rubin gain × ~617–646 adjusted tokens/s ÷ 8.6 ≈ 4.37–4.57 million users’ workload per campus.',
              'Six equal sites support ~26.2–27.4 million users’ workload, about 6.55–6.85% of the 400M target.',
              'Peak rates do not establish daily token totals, eight active hours or simultaneous session counts. No shift or quota-wait multiplier is included.'])
    b[11].update(headline='Budget the fixed campuses',
        bullets=['338 compute racks per datacenter; 2,028 across six sites','Six-site compute-rack purchase: about $15.82B','Buildings, memory, support systems and operations cost extra'],
        number='$2.64B',unit='compute-rack purchase per datacenter only',
        assumption='$7.8M per compute rack, inherited planning midpoint; no vendor quote or new five-year total.',
        source='Fixed rack count × inherited price assumption',
        why='Using the heavy reference reduces the number of people served for the same workload. It does not require purchasing a hypothetical fleet for all 400 million in this fixed-campus plan. The $30B five-year constraint still needs a complete cost review.')
    b[12].update(headline='Efficiency creates room for more work',
        bullets=['Same IT load: ~24% less total power at PUE 1.10 vs 1.44','At a fixed power limit: ~31% more power available to IT','The heavy model still lowers the people served for the same workload'],
        number='~24%',unit='less total power for the same computer load',
        assumption='PUE 1.10 is a design allowance; 1.44 is the supplied comparison. Workload and scheduling determine headcount.',
        source='PUE comparison · fixed-campus capacity',
        why='Efficient cooling supports more useful computation within the same electrical limit. This is a power comparison, not a new dollar-saving or payback claim.')
    b[12]['designKeys']=['efficiency','budget']
    content['objects']['compute']['number']='368 positions drawn; 338 active rack pairs per campus at midpoint power'
    content['objects']['compute']['text']+=' Operational sizing uses 338 compute racks plus their support allowance. More AI work per person reduces how many users these racks can serve.'
    content['labels'][0]='368 rack positions drawn; 338 active pairs within the midpoint power cap'

    def section(key,title,why,paragraphs,numbers=()):
        notes=content['design'].get(key,{}).get('notes','')
        refs=' · '.join(re.findall(r'<a\b[^>]*>.*?</a>',notes))
        copy=''.join('<p>'+p+'</p>' for p in paragraphs)
        if numbers:copy+='<div class="nums"><dl>'+''.join('<div><dt>'+html.escape(k)+'</dt><dd>'+html.escape(v)+'</dd></div>' for k,v in numbers)+'</dl></div>'
        content['design'][key]=dict(title=title,why='<p>'+why+'</p>',html=copy,
            notes='<span><strong>Planning basis</strong>20 questions and five agent tasks per person daily, with the heavy reference for the top model. Source peak rates, hardware transfer and cache behavior determine the estimate; this is not measured Claude performance.</span><span><strong>Original input references</strong>'+refs+'</span>')
    section('scope','The same daily workload within fixed campuses',b[0]['why'],[
        'The challenge targets 400 million people, six sites, 500 MW and $30B over five years. We keep the physical limits and report how much of that population’s assumed workload fits.',
        'Each person has 20 questions and five agent tasks daily. A task may make several AI calls. The heavy reference stands in for the top model on every call.',
        'The supplied case C peak rates remain 4.6 output and 40 new input tokens/s per source user. They are peak sizing inputs, not continuous daily generation rates.',
        'No active-hour schedule, daily-cohort multiplier or extra concurrency discount is assumed. Land, grid access and rock testing remain unresolved.'],
        [('Per-campus power allowance','~83.3 MW'),('Daily workload','20 questions + 5 agent tasks per person'),('Capacity per campus','~'+per_site+' users’ workload, illustrative')])
    section('models','The heavy reference for every question and task',b[10]['why'],[
        'The same daily workload is retained. Every question and every call within an agent task uses the heavy reference; there is no weaker-model routing.',
        'Llama 3.1 405B is the provisional hardware proxy for the top model. Its benchmark does not measure proprietary Claude throughput, answer quality, subscription quota or joules per token.',
        '4.6 output and 40 new input tokens/s per source user are the original case C peak rates. They already aggregate the daily workload; multiplying again by 20 questions or five tasks would double-count work.',
        'Actual input, cache creation, cache reads, reasoning output, session overlap and response-time targets still need measurement before a service-capacity commitment.'])
    section('computers','338 active rack pairs per datacenter',b[3]['why'],[
        'The design still has 368 drawn rack positions. At the 210 kW midpoint plus 14 kW support and PUE 1.10, 338 active pairs fit each 83.3 MW allowance. At the lower 190 kW compute draw, all 368 positions fit.',
        'Six independently capped campuses therefore operate 2,028 pairs. We cannot pool the small leftover power between sites to activate a 2,029th pair.',
        'The capacity calculation uses 72 GPUs per rack and an assumed 2.5× rack throughput gain over the GB300 heavy-reference benchmark. Applying the R1 hardware gain to Llama and this workload needs validation.',
        'No capacity reserve is included. Additional context storage, attention work, memory bandwidth, maintenance and latency requirements can lower the usable headcount.'],
        [('Active GPUs per campus','24,336'),('Modeled loaded power','83.28 MW per campus'),('Six-site active rack pairs','2,028')])
    section('memory','An agent task can involve many AI calls',
        'The daily task count is not a count of model calls. Context, tool results and repeated processing also consume computing resources.',[
        'The daily workload is 20 questions plus five agent tasks per person. Each task can involve several AI calls; code, conversation history and tool results can be processed again on later calls.',
        'The case C source lists 104 million context reads per person per day, separately from the 40 new input tokens/s peak rate. Repeated reads are not the same as new input, stored data or network downloads.',
        'The baseline assumes effective context reuse. Cache hits still require attention, memory and bandwidth; misses require additional input processing.',
        'Cache size, bandwidth and added support power remain unvalidated. The old R1-specific 2.3 EB and flash-cost estimates do not size the chosen heavy model. Peak rates alone do not establish daily token totals.'])
    section('budget','Purchase the fixed campus hardware',b[11]['why'],[
        '338 compute racks × $7.8M ≈ $2.64B per datacenter; six sites cost about $15.82B for compute-rack purchase only. This is not the earlier similarly numbered whole-project budget.',
        'Networking, context memory, buildings, land, cooling, grid access, backup, electricity and operations are additional. The $30B five-year constraint has not been revalidated.',
        'The previous $231–242B extrapolation purchased compute racks to chase the whole population under this same workload. It is not the fixed-campus purchase plan.',
        'The old total-cost, leftover-budget, savings and payback headlines are superseded. Measure usage and finish the engineering estimate before making a financial commitment.'])
    section('efficiency','Use the available electricity more effectively',b[12]['why'],[
        'For the same IT load, 1 − 1.10 ÷ 1.44 = 23.6% less facility power. At a fixed 500 MW, 500 ÷ 1.10 versus 500 ÷ 1.44 gives about 31% more power for IT.',
        'Power is a rate; energy is power over time. One hour at the modeled 83.28 MW campus load uses 83.28 MWh. Actual daily and annual energy require an operating-load schedule, including idle demand.',
        'The daily question and task counts stay fixed. The heavy model changes the chip time needed, while cooling, backup and boreholes still serve the same datacenter load.'])
    backup=content['design']['backup']
    start=backup['html'].find('<div class="nums">')
    if start!=-1:
        backup['html']=backup['html'][:start]+'<p>The full-campus concept stores about 1.1 million litres for 48 hours. Fewer users at the same loaded power do not reduce this backup requirement.</p></div>'
    content['design']['power']['html']+='<p><b>Fixed-workload correction:</b> 20 questions and five agent tasks per person daily, with the heavy reference for the top model. About 83.3 MW per site and 500 MW across six sites remain fixed. The resulting capacity is ~4.37–4.57M users’ workload per site at the source peak rates.</p>'

    for field in ['html','why']:
        content['design']['power'][field]=content['design']['power'][field].replace('fits 31% more chips','makes 31% more IT power available').replace('More chips under the cap than at PUE 1.44','More IT power under the cap than at PUE 1.44')
    content['design']['hall']['html']=content['design']['hall']['html'].replace('0.08–0.17 kg/user-yr','Recalculate for the actual workload, schedule and fleet')
    content['design']['efficiency']['notes']='<span><strong>Source</strong>Supplied budget: PUE 1.10 design allowance versus large-site PUE 1.44. Daily and annual electricity require a load schedule; peak power is not an energy forecast.</span>'
    return calc
