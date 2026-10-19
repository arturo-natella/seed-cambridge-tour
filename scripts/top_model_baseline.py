"""Eight active coding hours per person, heavy reference, fixed campus capacity."""
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
    _,reads,output,input_rate=analysis.CASES['B agent devs']
    users=400_000_000
    a=dict(targetUsers=users,activeHoursPerUserDay=8,campuses=6,
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
    return dict(revision='coding-capacity-05',assumptions=a,
        hardware=dict(racksPerCampus=racks,racksFleet=racks*a['campuses'],
            gpusPerCampus=racks*72,gpusFleet=racks*72*a['campuses'],
            loadedCampusMW=racks*pair_mw,loadedFleetMW=racks*pair_mw*a['campuses'],
            computeRackPurchasePerCampusB=racks*7.8/1000,
            computeRackPurchaseFleetB=racks*a['campuses']*7.8/1000,
            adjustedHeavyTokensPerGPUSecond=rates),
        baseline=dict(workPerActiveUserSecond=work,usersPerCampus=per_site,usersFleet=fleet,
            simultaneousUsersPerCampus=per_site,baselineDailyCohorts=1,
            outputTokensPerUserDay=output*8*3600,newInputTokensPerUserDay=input_rate*8*3600,
            loadedHoursPerDay=8,loadedEnergyMWhPerCampusDay=racks*pair_mw*8,
            targetPercent=[n/users*100 for n in fleet],
            facilityMWForTarget=[n*pair_mw for n in required_racks],
            computeRacksForTarget=required_racks),
        sourceHashes={str(p.relative_to(root.parent)):hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in [path,root.parent/'analysis/budget.py']},
        notes=[
            'User requirement: eight active coding hours per person per day, with the top model throughout. No fixed question or task count limits this workload.',
            'Token-rate assumption: the supplied case B developer peak rates, 28 output and 333 new input tokens/s, are treated as sustained aggregate rates during active hours. This is a planning assumption, not measured Claude or user usage.',
            'Multiple calls, tool results, retries and parallel agents count toward the aggregate token rates. Quota-blocked waiting is outside the eight active hours.',
            'The baseline assumes one daily cohort with overlapping active periods, so daily users equal simultaneous capacity. No automatic one-third concurrency factor or quota-wait multiplier is applied.',
            'Llama 3.1 405B is a provisional heavy hardware proxy, not measured Opus performance or proof of equal answer quality. The 2.5x Rubin gain is transferred from R1.',
            'Capacity precedes reliability reserves, long-context attention, memory bandwidth, response-time guarantees and any additional storage power. The range covers benchmark endpoints only.',
            'Loaded energy covers the eight modeled active hours only; add idle and transition electricity. Annual energy requires an operating-load schedule.',
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
        source='User requirement: eight active coding hours daily on the top model. Assumed intensity: case B developer rates, 28 output + 333 new input tokens/s during active use. Not measured Claude usage.',
        models=[dict(name='Llama 3.1 405B',tier='Hardware proxy',rate=[round(n) for n in h['adjustedHeavyTokensPerGPUSecond']],work='~29–34×',description='Used for all capacity figures. Not a measurement of Claude Opus or a claim about which model is best.'),
                dict(name='gpt-oss-120b',tier='Benchmark context',rate=[18760,21000],work='1×',description='Retained to explain relative chip time; no requests are routed to this model in the plan.'),
                dict(name='DeepSeek-R1',tier='Hardware-gain reference',rate=[8230,10023],work='~2–3×',description='Source of the assumed Rubin throughput gain. Its cache sizing does not establish the heavy model’s memory needs.')])
    b=content['bubbles']
    refs=[dict(tier='Service requirement',name='Strongest model throughout'),dict(tier='Hardware proxy',name='Llama 3.1 405B')]
    proxy='Llama is the heavy hardware proxy. The 28 output + 333 new input tokens/s during active hours are a study-based assumption, not measured Claude usage.'
    for i in [0,3,8,10,11,12]:
        b[i].update(referenceModels=refs,referenceSource='Eight-hour coding requirement · 18 October 2026',referenceAssumption=proxy)
    b[0].update(headline='Eight hours of coding. The same power limit.',
        bullets=['Eight active coding hours per person daily, using the top model','Same six datacenters: 500 MW total, about 83 MW each',f'Illustrative capacity: ~{per_site} users per datacenter in one daily cohort'],
        number='8 active hours',unit='per person, per day · quota-blocked waiting is excluded',
        assumption='Planning intensity: 28 output + 333 new input tokens/s during active hours, from the supplied developer study. One overlapping daily cohort; not measured Claude usage.',
        hideOverviewAssumption=True,
        source='Eight-hour requirement · study-based capacity estimate',
        why='SEED means Sustainable, Energy-Efficient Datacenters. We keep each datacenter’s power fixed and estimate how many people can receive eight active hours of coding on the top model. The 400-million-person ambition remains a reference target.')
    b[0]['referenceAssumption']='Workload intensity and hardware assumptions are explained inside AI & energy.'
    b[1].update(number='7,400–7,700',unit='active users per MW · illustrative coding case',
        assumption='Study developer rates during active hours; heavy-model proxy; before reliability reserves and context bottlenecks.',source='Eight-hour coding · users per MW')
    b[1]['card']['math']=[f'~{per_site} active users ÷ ~83.3 MW ≈ 7,400–7,700 active users per MW.',
        'One daily cohort gives each user eight active hours. More cohorts require balanced scheduling; no automatic threefold capacity credit is taken.']
    b[3]['bullets'][0]='368 rack positions drawn; 338 active rack pairs fit the midpoint power allowance'
    b[3].update(number='210 kW',unit='per compute rack + 14 kW for networking and storage',
        assumption='210 kW is the midpoint of the reported 190–230 kW range. The drawing uses the lower end; operating capacity uses 338 pairs.')
    b[3]['card']['math'][0]='At the midpoint: 338 × (210 + 14) kW × 1.10 ≈ 83.28 MW per campus; 338 × 72 = 24,336 active GPUs. The 368 drawn positions would use ~90.7 MW at this midpoint, so they cannot all run at that draw within the allowance.'
    b[3]['card']['math'].append('More calls, longer outputs and input reprocessing use more chip time. With fixed hardware and power, fewer users’ workload fits.')
    b[7]['bullets'][1]='At full IT load, ~75 MW becomes heat; the greenhouse needs well under 1 MW'
    b[7].update(unit='warm return-water design point · availability varies with load',
        assumption='~300 W/m² peak greenhouse demand, roughly estimated. Recoverable heat follows IT load; off-peak backup heat is not sized.')
    b[7]['card']['how']='Warm return water is designed around 124°F (51°C). Its usable heat output depends on the computers’ load; eight active coding hours do not establish round-the-clock heat availability.'
    b[7]['card']['math']=['At modeled full load, the campus IT demand is ~75 MW and becomes heat. The 60 × 30 m greenhouse needs roughly 1,800 m² × 300 W/m² = 0.54 MW at peak. Heat recovered by this particular circuit and off-peak backup must still be engineered.']
    content['objects']['greenhouse'].update(text='Warm return water can heat it on the way to the coolers. Available heat follows IT load; off-peak backup heat remains to be sized.',number='~0.54 MW peak heating estimate')
    content['design']['house']['html']='<p><strong>Revised operating assumption:</strong> Recoverable heat follows IT load. The workload scenario does not establish a continuous 75 MW heat supply or guaranteed return temperature. Off-peak backup heating remains to be sized.</p>'+content['design']['house']['html']
    content['design']['house']['html']=content['design']['house']['html'].replace('Waste heat available','Total IT heat at full load')
    b[8].update(headline='The datacenter keeps its power limit',
        bullets=['About 83.3 MW per datacenter; 500 MW across six sites','More AI work per person reduces capacity, not the power limit','User sessions can pause while other users keep the machines busy'],
        number='83.3 MW',unit='power allowance per datacenter · unchanged',
        assumption='338 active rack pairs per site, 210 + 14 kW each, PUE 1.10; before a solar credit.',source='Fixed-campus design · operating scenario')
    b[8]['card']['math']=['338 × 224 kW × 1.10 = 83.2832 MW at modeled full load. Six sites total 499.6992 MW.',
        'One eight-hour loaded cohort: 83.28 MW × 8 h ≈ 666 MWh per campus, plus idle and transition electricity.',
        'Quota waiting does not turn off the campus. Actual daily and annual energy require a schedule of the total datacenter load, including the remaining hours.']
    b[9]['card']['math'][0]='Fuel for the existing full campus: 48 h × ~82 MW × ~0.28 L/kWh ≈ 1.1 million litres. Fewer users do not shrink the backup requirement for a fully loaded campus.'
    b[10].update(headline='Eight-hour users within a fixed datacenter',
        bullets=['Eight active coding hours per person; top model for every call',f'Six sites support ~{fleet} people in the one-cohort planning case','Calls, retries and parallel agents all consume the same fixed computing capacity'],
        number='~'+per_site,unit='users per datacenter per day · illustrative one-cohort case',
        assumption='28 output + 333 new input tokens/s sustained during active hours is assumed. Efficient context reuse; no reliability or latency reserve included.',
        source='Eight-hour coding · provisional capacity',
        why='Eight hours defines the daily duration, not the number of AI calls or tokens. We use a separately labeled intensity assumption to estimate how many people fit within the same power allowance.')
    b[10]['card']=dict(title='Eight active hours on the top model',what=b[10]['bullets'][0],why=b[10]['why'],
        how='Use the top model throughout the eight active hours, including repeated calls, tool results, retries and parallel agents. Waiting for a quota reset is outside those active hours. The baseline assumes one daily cohort whose active periods overlap.',
        math=['338 rack pairs × (210 + 14) kW × 1.10 = 83.28 MW per campus.',
              'Assumed work per active user: 28 output + 333 new input ÷ 10 = 61.3 output-equivalent tokens/s.',
              '338 × 72 GPUs × assumed 2.5× Rubin gain × ~617–646 adjusted tokens/s ÷ 61.3 ≈ 612,000–641,000 simultaneous users per campus.',
              'One daily cohort supports roughly 610–640k users per site, each with eight active hours; about 3.7–3.8 million across six sites.',
              'This assumed intensity produces 806,400 output and 9,590,400 new input tokens per person over eight hours. These are scenario volumes, not measured personal usage.'])
    b[11].update(headline='Budget the fixed campuses',
        bullets=['338 compute racks per datacenter; 2,028 across six sites','Six-site compute-rack purchase: about $15.82B','Buildings, memory, support systems and operations cost extra'],
        number='$2.64B',unit='compute-rack purchase per datacenter only',
        assumption='$7.8M per compute rack, inherited planning midpoint; no vendor quote or new five-year total.',
        source='Fixed rack count × inherited price assumption',
        why='Intensive coding on the top model reduces the number of people served within the fixed power limit. It does not require purchasing a hypothetical fleet for all 400 million in this fixed-campus plan. The $30B five-year constraint still needs a complete cost review.')
    b[12].update(headline='Efficiency creates room for more work',
        bullets=['Same IT load: ~24% less total power at PUE 1.10 vs 1.44','At a fixed power limit: ~31% more power available to IT','Heavier coding still lowers the people served per datacenter'],
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
            notes='<span><strong>Planning basis</strong>Eight active coding hours on the top model are the user requirement. Token intensity, hardware transfer, cache behavior and scheduling are planning assumptions; this is not measured Claude performance.</span><span><strong>Original input references</strong>'+refs+'</span>')
    section('scope','Eight active coding hours within fixed campuses',b[0]['why'],[
        'The physical limits stay at six sites and 500 MW, with a $30B five-year constraint still needing complete budget validation. The 400-million-person goal is a reference target.',
        'Each person receives eight active coding hours daily using the top model. There is no fixed daily question or task allowance. Quota-blocked waiting is excluded from active time.',
        'Duration alone does not establish computing demand. For this estimate, the supplied developer study’s 28 output and 333 new input tokens/s peak rates are explicitly treated as sustained during active hours. Actual session telemetry is still needed.',
        'The baseline assumes one daily cohort whose active periods overlap. Balanced shifts could serve additional daily users, but no automatic one-third concurrency discount is assumed.'],
        [('Per-campus power allowance','~83.3 MW'),('Daily active use','8 hours per person'),('One-cohort capacity per campus','~'+per_site+' users, illustrative')])
    section('models','The top model throughout the coding session',b[10]['why'],[
        'Use the strongest model throughout each person’s eight active coding hours, across repeated calls, agent tasks, retries and reasoning. No weaker-model routing is assumed.',
        'Llama 3.1 405B is a provisional hardware proxy. Its benchmark does not measure proprietary Claude throughput, answer quality, subscription quota or joules per token.',
        'The 28 output and 333 new input tokens/s intensity is taken from the supplied developer study and assumed throughout active hours. Parallel agents must be counted in aggregate, not as free extra activity.',
        'Measure input, cache creation, cache reads, reasoning output, session overlap and response-time targets before making a service-capacity commitment.'])
    section('computers','338 active rack pairs per datacenter',b[3]['why'],[
        'The design still has 368 drawn rack positions. At the 210 kW midpoint plus 14 kW support and PUE 1.10, 338 active pairs fit each 83.3 MW allowance. At the lower 190 kW compute draw, all 368 positions fit.',
        'Six independently capped campuses therefore operate 2,028 pairs. We cannot pool the small leftover power between sites to activate a 2,029th pair.',
        'The capacity calculation uses 72 GPUs per rack and an assumed 2.5× rack throughput gain over the GB300 heavy-reference benchmark. Applying the R1 hardware gain to Llama and this workload needs validation.',
        'No capacity reserve is included. Additional context storage, attention work, memory bandwidth, maintenance and latency requirements can lower the usable headcount.'],
        [('Active GPUs per campus','24,336'),('Modeled loaded power','83.28 MW per campus'),('Six-site active rack pairs','2,028')])
    section('memory','Code and context can be processed repeatedly',
        'An active coding session can consume much more data than the text a person types. Repeated calls and parallel agents count toward total computing demand.',[
        'At the assumed 333 new input tokens/s for eight active hours, the scenario processes about 9.59 million new input tokens per person daily. At 28 output tokens/s it generates 806,400 tokens. These are modeled volumes, not measured personal usage or stored-file sizes.',
        'Repeated context is separate. The supplied developer profile lists 860 million context reads per person daily, which are not the same as new input or downloaded files.',
        'The baseline assumes effective context reuse. Cache hits still need attention, memory and bandwidth; cache misses need extra input processing and can reduce usable capacity.',
        'Cache size, bandwidth and added support power remain unvalidated for the chosen heavy model.'])
    section('budget','Purchase the fixed campus hardware',b[11]['why'],[
        '338 compute racks × $7.8M ≈ $2.64B per datacenter; six sites cost about $15.82B for compute-rack purchase only.',
        'Networking, context memory, buildings, land, cooling, grid access, backup, electricity and operations are additional. The $30B five-year constraint has not been revalidated.',
        'Total cost, electricity savings and payback require a complete operating-load schedule and current equipment estimates.'])
    section('efficiency','Use the available electricity more effectively',b[12]['why'],[
        'For the same IT load, 1 − 1.10 ÷ 1.44 = 23.6% less facility power. At a fixed 500 MW, 500 ÷ 1.10 versus 500 ÷ 1.44 gives about 31% more power for IT.',
        'One eight-hour fully loaded cohort uses about 666 MWh per campus during those hours, plus idle and transition electricity. The other 16 hours are not assumed to use zero electricity.',
        'More balanced cohorts can share the same hardware across the day, but do not increase simultaneous capacity. Cooling, backup and boreholes still serve the same datacenter load.'])
    backup=content['design']['backup']
    start=backup['html'].find('<div class="nums">')
    if start!=-1:
        backup['html']=backup['html'][:start]+'<p>The full-campus concept stores about 1.1 million litres for 48 hours. Fewer users at the same loaded power do not reduce this backup requirement.</p></div>'
    content['design']['power']['html']+='<p><b>Eight-hour coding requirement:</b> Each person receives eight active hours daily on the top model. About 83.3 MW per site and 500 MW across six sites remain fixed. Token intensity and overlapping usage determine how many people fit; quota waiting is not an extra capacity credit.</p>'

    for field in ['html','why']:
        content['design']['power'][field]=content['design']['power'][field].replace('fits 31% more chips','makes 31% more IT power available').replace('More chips under the cap than at PUE 1.44','More IT power under the cap than at PUE 1.44')
    content['design']['hall']['html']=content['design']['hall']['html'].replace('0.08–0.17 kg/user-yr','Recalculate for the actual workload, schedule and fleet')
    content['design']['efficiency']['notes']='<span><strong>Source</strong>Supplied budget: PUE 1.10 design allowance versus large-site PUE 1.44. Daily and annual electricity require a load schedule; peak power is not an energy forecast.</span>'
    update_operating_copy(content)
    return calc


def update_operating_copy(content):
    """Keep every visible detail aligned with the revised operating schedule.

    Fixed geometry and source weather statistics are retained. Prior annual
    energy/carbon/payback results are not forecasts for eight-hour users.
    """
    b, objects, design = content['bubbles'], content['objects'], content['design']

    def replace(key, old, new, fields=('html', 'why')):
        hits = 0
        for field in fields:
            if old in design[key][field]:
                design[key][field] = design[key][field].replace(old, new)
                hits += 1
        assert hits, f'Expected source copy missing: {key}: {old}'

    def number(key, label, new_label, value):
        pattern = r'<div><dt>' + re.escape(label) + r'</dt><dd>.*?</dd></div>'
        replacement = '<div><dt>' + html.escape(new_label) + '</dt><dd>' + html.escape(value) + '</dd></div>'
        design[key]['html'], count = re.subn(pattern, lambda _: replacement, design[key]['html'])
        assert count == 1, f'Expected number missing: {key}: {label}'

    b[1]['bullets'][1] = 'Carbon and water per user still need a full operating schedule'
    b[1]['card']['how'] = 'The campus is run from here. We compare active users per megawatt under the same workload. Carbon and water per user require a complete annual load and resource-use estimate.'

    b[2].update(number='0.8–1.0 MW', unit='estimated solar output averaged across a year',
        assumption='Inherited solar-yield estimate. The share of annual electricity use and grid savings depend on the operating schedule.')
    b[2]['card']['why'] = b[2]['why'] = 'Solar can reduce grid purchases when generation coincides with site demand. The same 500 MW limit applies; annual savings depend on when the campus runs and how exports are handled.'
    b[2]['card']['how'] = 'The supplied Massachusetts yield assumptions give about 0.8–1.0 MW averaged across the year. That is roughly 1% of the campus’s full-load power, not a calculated share of its revised annual electricity use.'
    b[2]['card']['math'][0] = '3.3 MW of roof and canopy panels × ~14% + 2–3 MW of meadow inverter capacity × 17% ≈ 0.8–1.0 MW annual-average generation, or roughly 7–9 GWh/year. Grid purchases avoided depend on the hourly generation and campus-load schedules.'
    objects['solar']['text'] = 'More panels over the meadow and parking. With the roof, estimated output averages 0.8–1.0 MW across the year. Annual grid savings depend on when that generation meets campus demand.'

    b[5].update(unit='weather-file hours suitable for direct chip cooling',
        assumption='Original weather study, not operating hours. The warmer-weather case needs ~20 hours of assistance; annual energy must be rerun with the new load schedule.')
    b[5]['bullets'][2] = 'Warm-water chips need little chiller assistance in the weather study'
    b[5]['card']['what'] = '102 dry coolers on short legs on a 6 m steel deck, fed by three pipe bridges. Sealed coils reject heat without evaporative cooling towers; rare hot conditions need assistance or a power limit.'
    b[5]['why'] = b[5]['card']['why'] = 'Warm-water chips let outdoor air carry away heat in nearly all hours of the source weather file. Weather availability does not establish how many hours the datacenter actually runs.'
    b[5]['card']['math'][1] = 'Annual fan, pump and chiller electricity must be recalculated from the revised hourly IT load and weather. The eight-hour requirement alone does not determine annual cooling energy.'
    objects['coolers']['text'] = objects['coolers']['text'].replace('the chips never need chillers in a typical year', 'rare hot conditions can require assistance or a rack power limit')
    objects['coolers']['number'] = '8,759 / 8,760 source weather hours suitable for direct chip cooling'
    replace('chip-loop', 'outdoor air alone can cool the chips in 8,759 of 8,760 hours in Cambridge, with no chillers and no water evaporated. Fixed cold water would need chillers and use about 2.7× the energy.', 'the original weather model finds direct chip cooling feasible in 8,759 of 8,760 hours in Cambridge, with no evaporative water use. These are weather-file hours, not a forecast of operating hours. Annual cooling electricity and comparison with fixed cold water must be rerun using the revised hourly load.')
    number('chip-loop', 'Water at 70–77°F (21–25°C)', 'Original weather model: water at 70–77°F (21–25°C)', '63% of weather-file hours')
    number('chip-loop', 'Fans + pumps a year, per site', 'Annual fan and pump electricity', 'Requires revised hourly load and weather simulation')
    number('chip-loop', 'Fixed 90°F (32°C) + chillers instead', 'Annual comparison with fixed 90°F water', 'Not yet recalculated for this operating schedule')
    number('chip-loop', 'Hot summer, +3.6°F (+2°C)', 'Original +3.6°F (+2°C) weather scenario', '20 weather hours need assistance')
    replace('chip-loop', 'a site&#x27;s towers would evaporate ~3,600 m³ of water a day, by Lawrence Berkeley National Laboratory&#x27;s 2016 planning figure of 1.8 L per kWh.', 'the source study used Lawrence Berkeley National Laboratory&#x27;s 2016 planning intensity of 1.8 L per kWh. Daily water savings require the revised load schedule; no daily volume is claimed here.', fields=('notes',))

    b[6].update(number='~1,000', unit='boreholes in the existing concept · field sizing to validate',
        assumption='Original thermal design retained. Test the rock and rerun the hourly heat balance for the eight-hour operating scenario before claiming annual savings.')
    b[6]['why'] = b[6]['card']['why'] = 'When outdoor air cannot cool the room circuit enough, the concept transfers heat into rock with circulation pumps. Chillers cover shortfalls. Annual energy savings depend on the hourly heat load, weather and winter recharge.'
    b[6]['card']['math'] = [
        'At full modeled load: 338 support racks × 14 kW = 4.73 MW. Adding the assumed electrical losses of 1–3% of ~75 MW gives roughly 5.5–7 MW of room-air heat.',
        'The original weather file has about 2,290 hours above 66°F (19°C). These are potential ground-cooling hours; actual operation depends on whether the datacenter needs cooling then.',
        'The existing field shows 1,024 boreholes, based on the original ~1,000-hole concept. Its seasonal heat balance and winter recharge must be revalidated for the revised hourly load.',
        'Annual energy savings and peak chiller relief have not been recalculated for the eight-hour operating scenario. The ground loop and six backup chillers remain in the physical design.'
    ]
    objects['boreholes']['number'] = '1,024 loops drawn · seasonal heat balance to validate'
    objects['batteryHouse']['number'] = 'Pumps serve the ground loop as cooling demand requires'
    replace('room-air', 'Outdoor air can&#x27;t make 75°F (24°C) water for about 2,290 hours a year. The ground does it with less power than chillers every year and keeps SEED passive. The chillers are insurance if the rock, the share of heat in the air, or the summer is worse than modeled. Arturo chose this over a chillers-only design: it doesn&#x27;t pay back on electricity alone, but it uses less power over time.', 'The original weather file has about 2,290 hours when outdoor air cannot make 75°F (24°C) water directly. Ground cooling is intended to reduce compressor use during loaded warm hours. The chillers cover shortfalls. The field’s seasonal heat balance, winter recharge, annual savings and payback require a new hourly simulation for this operating schedule.')
    number('room-air', 'Energy saved vs. chillers', 'Annual energy saved vs. chillers', 'Not yet recalculated for the eight-hour scenario')
    number('room-air', 'Peak saved', 'Peak relief for chillers', 'Requires updated full-load thermal validation')
    number('room-air', 'Boreholes needed / drilled', 'Boreholes in existing concept / drawing', '~1,000 / 1,024; final sizing to validate')
    number('room-air', 'Drilling cost', 'Original drilling allowance', '$11–16M; not a current quote or revised project total')
    number('room-air', 'Chiller cost, a floor', 'Original chiller allowance', '~$2.3–3.8M floor; current quote needed')

    replace('power', 'and the cooling model suggests 1.03–1.07.', 'the capacity calculation uses PUE 1.10 throughout. Actual annual PUE needs the revised load and cooling simulation.')
    number('power', 'Energy at 500 MW, a year', 'Energy for eight loaded hours, per campus', '~666 MWh, plus idle and transition electricity')
    number('power', 'Share of Massachusetts sales', 'Annual electricity and share of state demand', 'Requires a complete operating-load schedule')
    number('power', 'Budgeted price', 'Inherited electricity-price assumption', '10–18.2¢/kWh; current contract needed')

    b[9]['why'] = b[9]['card']['why'] = 'The concept uses batteries and generators with renewable diesel. Its estimated 50–80% lifecycle fuel-carbon reduction is a comparison with fossil diesel, not a reduction in the whole campus footprint. Annual backup emissions depend on testing, outages and fuel sourcing.'
    b[9]['card']['math'][0] = 'Full-load fuel allowance: 48 h × 83.28 MW × ~0.28 L/kWh ≈ 1.12 million litres. Fewer users do not reduce backup demand at the same campus power; generator efficiency and reserve still need validation.'
    b[9]['card']['math'][2] = 'Annual grid and backup emissions require an operating-load schedule, generator test and outage hours, and fuel-specific emissions factors. No revised annual footprint or percentage contribution is claimed.'
    replace('backup', 'Generators only run for tests and rare outages, so their fuel is under 1% of a site&#x27;s footprint.', 'Annual backup emissions depend on generator testing, outages and fuel sourcing. Their share of the campus footprint must be recalculated alongside grid electricity for the revised operating schedule.')
    objects['reserved']['number'] = 'Future option · not included in the compute-rack purchase'
    number('hall', 'Embodied carbon', 'Embodied carbon per user', 'Requires building inventory, service life and the revised user count')
    number('hall', 'Stone wool&#x27;s extra carbon repaid', 'Carbon payback for the wall choice', 'Not established for the revised operating schedule')

    # Equipment popups share these records with every Closer look card.
    objects['sealed']['text'] = 'The sealed hall limits uncontrolled outside air. A small filtered and dried fresh-air supply serves staff. Most computer heat passes into liquid cooling circuits.'
    objects['drainTanks']['text'] = 'Indoor tanks receive the exposed coolers’ fluid during a long winter outage. Antifreeze concentration, complete drainability, expansion space and restart controls still need engineering; slush formation is not a blanket guarantee against pipe damage.'
    replace('fluid', 'Even if the pumps stopped in a deep freeze, it would turn to slush rather than split the pipes, by Dow&#x27;s tables.', 'Dow&#x27;s tables inform the proposed burst protection, but concentration, expansion space, full drainability and restart controls still require engineering. Slush formation alone does not guarantee that every coil or pipe is protected.')
    content['labels'][1] = 'Warm-water chip cooling: up to 113°F (45°C); rare hot conditions need assistance'
    content['labels'][2] = 'DOWFROST loops: normal running fluid stays in the high teens °F or warmer'
    content['labels'][4] = 'Cooling ridge: 102 dry coolers, no evaporative water use'
    content['labels'][7] = 'Backup concept: batteries + renewable-diesel generators, ~83 MW, 48 hours of fuel'

    # Clarify the existing panel specification: the wool is an enclosed core.
    design['hall']['title'] = 'A low steel hall with enclosed stone-wool panels'
    objects['hall']['text'] = 'A one-story steel hall with stone-wool insulation enclosed between interior and exterior steel panel faces. The finished room faces metal, with no exposed insulation intended. Edge closures, joints and penetrations still need detailed engineering.'
    panel_explainer = ('<div><h4>Is stone wool exposed to the room?</h4>'
        '<p><strong>Interior steel face → enclosed stone-wool core → exterior steel face.</strong> '
        'The specified insulated metal panel has steel on both sides. People in the finished hall face metal; the stone wool is insulation inside the wall.</p>'
        '<p>The design intent is no exposed insulation in occupied rooms or air paths. Cut edges need closures, and joints and service penetrations need the appropriate seals and fire-stopping for the approved wall assembly. These details are not resolved in the 3D model.</p>'
        '<p>Cutting or disturbing mineral wool can release dust and fibres that irritate the throat, skin and eyes. Installation and repair require the selected product’s handling instructions, dust controls and appropriate protective equipment. An enclosed finished panel does not remove the need for those work practices.</p></div>')
    design['hall']['html'] = panel_explainer + design['hall']['html']
    design['hall']['notes'] += ('<span><strong>Material handling</strong>'
        '<a href="https://www.rockwool.com/siteassets/rw-uk/downloads/msds/msds-rockwool-insulation-web.pdf" target="_blank" rel="noopener">ROCKWOOL safe-use instructions</a> '
        '(general stone-wool handling guidance, December 2022; not a declaration that ROCKWOOL supplies this panel). '
        'Obtain the selected panel manufacturer’s safety and installation documents.</span>')
    b[1]['designKeys'].append('hall')
    b[3]['card']['how'] += ' The hall walls use stone wool enclosed between steel panel faces; bare insulation is not intended to face the room.'
