import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const content=await fetch('./assets/content.json').then(r=>{if(!r.ok)throw Error('Presentation text could not load');return r.json()});
const params=new URLSearchParams(location.search), reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
const scene=new THREE.Scene();scene.background=new THREE.Color('#e5e8de');scene.fog=new THREE.FogExp2('#e5e8de',.00055);
let renderer;
try{renderer=new THREE.WebGLRenderer({antialias:true,logarithmicDepthBuffer:true,preserveDrawingBuffer:true,powerPreference:'high-performance'});}catch(error){document.body.classList.add('no-webgl');$('#loadnote').innerHTML='This browser could not start 3D graphics. Enable hardware acceleration and reopen the tour.<a href="./stills/index.html">View the Blender stills instead ↗</a>';throw error;}
renderer.setPixelRatio(Math.min(devicePixelRatio,1.65));renderer.setSize(innerWidth,innerHeight);renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.05;$('#viewport').appendChild(renderer.domElement);
renderer.domElement.setAttribute('aria-label','Drag to orbit, scroll to zoom, click an object to read its explanation');renderer.domElement.setAttribute('tabindex','0');
const camera=new THREE.PerspectiveCamera(44,innerWidth/innerHeight,.1,3500);
// Blender is z-up, glTF is y-up. This is the only coordinate conversion.
const v=p=>new THREE.Vector3(p[0],p[2],-p[1]);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.07;controls.minDistance=1;controls.maxDistance=1200;controls.maxPolarAngle=Math.PI*.93;controls.target.copy(v([0,0,0]));
const hemi=new THREE.HemisphereLight('#e1edee','#858878',1.65);scene.add(hemi);
const sun=new THREE.DirectionalLight('#fff0df',2.6);sun.position.copy(v([-250,-300,380]));sun.castShadow=true;sun.shadow.mapSize.set(4096,4096);sun.shadow.camera.left=-360;sun.shadow.camera.right=360;sun.shadow.camera.top=330;sun.shadow.camera.bottom=-330;sun.shadow.camera.far=1000;sun.shadow.normalBias=.35;sun.shadow.bias=-.0007;scene.add(sun);
const fill=new THREE.DirectionalLight('#d8e4ef',.8);fill.position.copy(v([200,100,200]));scene.add(fill);
const state={index:0,card:0,object:null,xray:false,ground:false,flow:false,winter:false,labels:false,clean:false,powerFocus:false,exploring:false,ready:false,flying:false,hover:null};
let campus,groups={},pickables=[],materials=[],fanBatches=[],fanAngle=0,flight=null,storyTimer=null,pointerDown=null,lastTime=performance.now();
const fanMatrix=new THREE.Matrix4(),fanRotation=new THREE.Matrix4();
// Preserve the Blender pivots and blade geometry; share draw calls across fans.
function prepareFans(){
 campus.updateMatrixWorld(true);
 const campusInverse=campus.matrixWorld.clone().invert();
 for(const [prefix,key] of [['coolerRotor','coolers'],['chillerRotor','chillers']]){
  const roots=Object.entries(groups).filter(([name])=>new RegExp('^'+prefix+'\\d+$').test(name)).map(([,node])=>node);
  if(!roots.length)continue;
  const blades=roots.map(root=>root.children.find(child=>child.isMesh));
  const mesh=new THREE.InstancedMesh(blades[0].geometry,blades[0].material,roots.length);
  mesh.name=prefix+'Instances';mesh.userData.objectId=key;mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
  const pivots=roots.map(root=>new THREE.Matrix4().multiplyMatrices(campusInverse,root.matrixWorld));
  const offsets=roots.map((root,i)=>new THREE.Matrix4().multiplyMatrices(root.matrixWorld.clone().invert(),blades[i].matrixWorld));
  roots.forEach(root=>{root.removeFromParent();delete groups[root.name];});
  campus.add(mesh);groups[mesh.name]=mesh;fanBatches.push({mesh,pivots,offsets});
 }
 updateFans(0);
 for(const {mesh} of fanBatches){
  mesh.computeBoundingSphere();
  // Rotation leaves pivot positions unchanged; allow for every blade angle.
  mesh.boundingSphere.radius+=2;
 }
}
function updateFans(dt){
 fanAngle=(fanAngle-dt*Math.PI*(state.winter?.5:2))%(Math.PI*2);
 for(const {mesh,pivots,offsets} of fanBatches){
  for(let i=0;i<pivots.length;i++){
   fanRotation.makeRotationY(fanAngle+(i*.381966%1)*Math.PI*2);
   fanMatrix.copy(pivots[i]).multiply(fanRotation).multiply(offsets[i]);
   mesh.setMatrixAt(i,fanMatrix);
  }
  mesh.instanceMatrix.needsUpdate=true;
 }
}
const anchors={hall:[0,-28,5],roofSolar:[0,0,10],sealed:[-37,-5,1],compute:[-36.4,-10,1.5],network:[-39.3,-10,1.5],trench:[-38.25,-10,0],fire:[-37,-5,6.6],spine:[-37,23,2],electrical:[-7,12,2],bridges:[0,33,7],coolers:[0,48,9],chillers:[123,48,2],boreholes:[0,-142,-65],batteryHouse:[0,-47,5],solar:[-75,-160,3],substation:[175,0,5],generators:[210,110,3],fuel:[255,110,4],reserved:[210,158,0],house:[-160,2,5],greenhouse:[-155,-35,6],snowpad:[160,-95,0]};
Object.assign(anchors,{dewpoint:[-49.82,8,1.8],freshAir:[75,23.2,1.45],airlock:[102,-2,2.5],bypass:[-.85,35,8.9],freezeProtection:[0,39.35,7.72],drainTanks:[-88,23,1.85],coldInsulation:[0,-47.75,1.2]});
const alias={hallRoof:'hall',partitions:'sealed',spares:'compute',power:'electrical',powerLine:'substation',heatPipes:'spine',geology:'boreholes',groundCap:'boreholes',parking:'solar',solarField:'solar'};
const focusIds=[null,'house','solar','compute','spine','coolers','boreholes','greenhouse','substation','generators',null,null,null];
const cameraAt=i=>i===6?[[220,-340,110],[-5,-140,-65]]:content.bubbles[i].camera;
const titleAt=i=>i===0?'The idea':i===11?'What it costs':i===12?'The comparison':content.bubbles[i].name.replace(/^\d+\. /,'');
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const markup=s=>esc(s).replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>').replace(/\*([^*]+)\*/g,'<em>$1</em>');
function projectionOffset(){camera.aspect=innerWidth/innerHeight;if(innerWidth>850&&!document.body.classList.contains('render-only'))camera.setViewOffset(innerWidth,innerHeight,-innerWidth*.14,0,innerWidth,innerHeight);else camera.clearViewOffset();camera.updateProjectionMatrix();}
projectionOffset();
function visible(o){while(o){if(!o.visible)return false;o=o.parent;}return true;}
function objectKey(o){while(o){if(o.userData.objectId){const key=alias[o.userData.objectId]||o.userData.objectId;if(content.objects[key])return key;}o=o.parent;}return null;}
function applyVisuals(){
  const feature=content.bubbles[state.index].featured;
  for(const {mat,base,key,name,emissive} of materials){
    mat.color.copy(base);
    if(state.winter&&['grass','meadow','leaf','leafLight','leafGold','leafRust','roof','panel','gravel'].includes(name))mat.color.lerp(new THREE.Color('#eef1ed'),name==='panel'?.54:.91);
    const guideVisible=(state.xray&&['electrical','fire','trench','compute','network'].includes(key))||(state.ground&&['boreholes','batteryHouse'].includes(key));
    if(feature.length&&!feature.includes(key)&&!guideVisible)mat.color.multiplyScalar(.62);
    if(mat.emissive){mat.emissive.copy(emissive);if(key===state.hover)mat.emissive.set('#487140').multiplyScalar(.38);}
    if(state.winter&&name==='bypassYellow'&&mat.emissive)mat.emissive.set('#d85a30').multiplyScalar(.55);
  }
}
function setGroup(name,on){if(groups[name])groups[name].visible=on;}
function applyToggles(){
  for(const n of ['hall','hallRoof','roofSolar','partitions','airlockRoof','freshAirCase'])setGroup(n,!state.xray);
  setGroup('batteryHouseRoof',!state.ground);
  setGroup('groundCap',!state.ground);setGroup('solarField',!state.ground);setGroup('boreholes',state.ground);setGroup('boreholeFocus',state.ground);setGroup('groundHeaders',state.ground);setGroup('geology',state.ground);
  for(const n of ['terrain','landscape','context','parking','roads','paths','people','fence','solar'])setGroup(n,!state.ground);
  setGroup('boreholeSurface',!state.ground);
  setGroup('coldInsulation',state.ground);
  flowGroup.visible=state.flow;$('#flow-legend').hidden=!state.flow||state.xray||state.ground;
  const coolingView=state.index===5&&!state.xray&&!state.ground;
  $('#scene-key').hidden=!(state.xray||state.ground||coolingView);$('#interior-key').hidden=!state.xray||state.ground||state.powerFocus;$('#power-key').hidden=!state.powerFocus||state.ground;$('#borehole-key').hidden=!state.ground;$('#freeze-key').hidden=!coolingView;
  $('#trace-power').hidden=!state.xray||state.ground;document.body.classList.toggle('interior-view',state.xray&&!state.ground);document.body.classList.toggle('ground-view',state.ground);
  for(const k of ['xray','ground','flow','labels'])$('#toggle-'+k).setAttribute('aria-pressed',String(state[k]));
  $('#toggle-season').setAttribute('aria-pressed',String(state.winter));$('#season-label').textContent=state.winter?'Winter':'Summer';$('#toggle-season .tool-icon').textContent=state.winter?'❄':'☀';
  $('#season-note').textContent=state.winter?'Winter · outdoor air chills the ground':'Summer · the ground takes heat';
  $('#ground-loop-mode').textContent=state.winter?'Winter · outdoor air recharges the cold battery':'Summer · room heat moves into the rock';
  $('#borehole-arrow-warm').setAttribute('d',state.winter?'m61 43 7-10 7 10':'m61 33 7 10 7-10');
  $('#borehole-arrow-cool').setAttribute('d',state.winter?'m155 29 7 10 7-10':'m155 39 7-10 7 10');
  $('.borehole-diagram').setAttribute('aria-label',state.winter?'Winter recharge: cool fluid goes down, takes heat from the rock, and returns warmer to outdoor coolers. No air enters the boreholes. Diagram not to scale.':'Summer: warm fluid goes down, gives heat to the rock, and returns cooler. No air enters the boreholes. Diagram not to scale.');
  scene.background.set(state.winter?'#dce4e7':'#e5e8de');scene.fog.color.copy(scene.background);sun.color.set(state.winter?'#f1f5ff':'#fff0d7');
  $('#labels').hidden=!state.labels;applyVisuals();
  updateGeothermal();
}
function setToggle(key){state[key]=!state[key];if(key==='xray'&&!state.xray)state.powerFocus=false;applyToggles();}
function setCleanView(on){
  state.clean=on;document.body.classList.toggle('clean-view',on);$('#toggle-clean').setAttribute('aria-pressed',String(on));
  $('#toggle-labels').disabled=on;$('#toggle-labels').title=on?'Turn off Clean view to show labels':'';
  clearTimeout(hoverTimer);hoverTimer=null;pendingPointer=null;state.hover=null;$('#tooltip').hidden=true;renderer.domElement.style.cursor='grab';applyVisuals();
  if(on)closeList();
  else{const toggle=$('#toggle-clean');(toggle.getClientRects().length?toggle:$('.card-tabs [aria-selected="true"]')).focus();}
}
$('#toggle-clean').addEventListener('click',()=>setCleanView(!state.clean));
function showBoreholes(){state.powerFocus=false;goTo(6);}
function focusPower(){
  if(!state.ready)return;
  enterExplore();state.xray=true;state.ground=false;state.powerFocus=true;state.hover=null;applyToggles();renderObject('electrical');showCard(2);$('#story').classList.remove('tucked');
  camera.fov=48;camera.updateProjectionMatrix();$('#view-status').textContent='Battery cabinets → UPS + distribution → power busways → racks';
  animateTo([12,-52,45],[-28,3,2],1500,completeArrival);
}
$('#show-boreholes').addEventListener('click',showBoreholes);$('#trace-power').addEventListener('click',focusPower);
$('#explain-geothermal').addEventListener('click',()=>{if(state.index!==6)goTo(6);showCard(3);$('#story').classList.remove('tucked')});
const systemViews={
  bypass:{stop:5,pos:[18,14,19],target:[-.85,35,8.3]},
  freezeProtection:{stop:5,pos:[18,21,19],target:[0,39.35,7.72]},
  drainTanks:{stop:4,pos:[-61,1,20],target:[-88,23,2],xray:true},
  coldInsulation:{stop:6,pos:[38,-86,35],target:[0,-47.75,1.2],ground:true},
  dewpoint:{stop:3,pos:[-48.9,7.4,2.2],target:[-49.82,8,1.8],xray:true},
  freshAir:{stop:4,pos:[95,5,13],target:[75,23.2,1.5],xray:true},
  airlock:{stop:3,pos:[125,-18,15],target:[102,-2,2.5],xray:true}
};
function focusSystem(key){
  const view=systemViews[key];if(!view||!state.ready)return;
  goTo(view.stop,true);enterExplore();state.xray=!!view.xray;state.ground=!!view.ground;state.powerFocus=false;state.hover=null;applyToggles();renderObject(key);showCard(2);$('#story').classList.remove('tucked');
  camera.fov=48;camera.updateProjectionMatrix();$('#view-status').textContent=content.objects[key].name+' · illustrative layout';animateTo(view.pos,view.target,1200,completeArrival);
}
$('#story').addEventListener('click',e=>{const key=e.target.closest('[data-system-view]')?.dataset.systemView;if(key)focusSystem(key)});
$('#story').addEventListener('click',e=>{const action=e.target.closest('[data-view-action]')?.dataset.viewAction;if(action==='power')focusPower();if(action==='boreholes')showBoreholes();});
for(const k of ['xray','ground','flow','labels'])$('#toggle-'+k).addEventListener('click',()=>setToggle(k));$('#toggle-season').addEventListener('click',()=>setToggle('winter'));
const allCardNames=['overview','why','closer','energy','geothermal','freeze'];
const specialCard=()=>content.bubbles[state.index].referenceModels?'energy':state.index===6?'geothermal':[4,5,9].includes(state.index)?'freeze':null;
const cardNames=()=>['overview','why','closer',...(specialCard()?[specialCard()]:[])];
const cardCount=()=>cardNames().length;
function showCard(index,focus=false){
  const names=cardNames(),count=names.length;state.card=(index+count)%count;
  for(const name of allCardNames){
    const active=name===names[state.card],tab=$('#tab-'+name),panel=$('#panel-'+name);tab.hidden=!names.includes(name);tab.setAttribute('aria-selected',String(active));tab.tabIndex=active?0:-1;panel.hidden=!active;if(active)panel.scrollTop=0;if(active&&focus)tab.focus();
  }
  $('#story').classList.toggle('is-reading',state.card!==0);
  const specialTitles={energy:'How many eight-hour users fit?',geothermal:'The ground cools a sealed fluid loop',freeze:'How the cooling system handles winter'};
  const specialSources={energy:'8 active hours · fixed-campus estimate',geothermal:'Calc 09 · closed-loop design',freeze:'Handoff §5 · freeze protection'};
  $('#headline').textContent=state.card===3?specialTitles[names[3]]:state.card===2?content.objects[state.object].name:content.bubbles[state.index].headline;
  $('#source').textContent=state.card===3?specialSources[names[3]]:state.card===2?'SEED basis of design':content.bubbles[state.index].source;
  $('#card-count').textContent=`${state.card+1} / ${count}`;$('#story').scrollTop=0;
}
for(const name of allCardNames)$('#tab-'+name).addEventListener('click',()=>showCard(cardNames().indexOf(name)));
$('.card-tabs').addEventListener('keydown',e=>{let index=state.card;if(e.key==='ArrowRight')index++;else if(e.key==='ArrowLeft')index--;else if(e.key==='Home')index=0;else if(e.key==='End')index=cardCount()-1;else return;e.preventDefault();e.stopPropagation();showCard(index,true);});
$('#card-prev').addEventListener('click',()=>showCard(state.card-1));$('#card-next').addEventListener('click',()=>showCard(state.card+1));
$('#more').addEventListener('click',()=>showCard(1));
$('#show-energy').addEventListener('click',()=>showCard(3));
$('#show-system').addEventListener('click',()=>showCard(3));
function renderEnergy(){
  const e=content.modelEnergy;
  $('#panel-energy').innerHTML=`<p class="energy-intro"><b>Eight active coding hours. Top model throughout.</b> Repeated AI calls, tool use, retries and parallel agents are part of that work. Quota-blocked waiting is outside the eight hours.</p>
    <ol class="energy-chain" aria-label="How coding affects capacity"><li>Calls + context</li><li>Chip time</li><li>People who fit</li></ol>
    <div id="energy-result" class="energy-result"><p class="energy-mix">8 active coding hours per person daily</p><div class="energy-figures"><div><strong>${esc(e.perCampus)}</strong><span>users/day per datacenter</span></div><div><strong>${esc(e.fleet)}</strong><span>users/day across six sites</span></div></div><p><b>Illustrative one-cohort estimate:</b> users’ active periods overlap. About ${esc(e.served)} of the 400M reference target.</p><p><b>Power stays fixed:</b> about 83.3 MW per datacenter, including networking and storage support, and cooling.</p><small>Assumed intensity: 28 output + 333 new input tokens/s during active hours, taken from the developer study. Not measured Claude usage. Capacity is before reliability reserves and long-context bottlenecks.</small></div>
    <details class="design-details"><summary>What does eight active hours include?</summary>
      <p>Eight hours of active coding on the top model each day. A session can include many calls, code reads, tool results, retries and parallel agents. There is no fixed daily question or task allowance.</p>
      <p>Waiting because a usage allowance is exhausted is outside the eight active hours. A quota reset is not an electricity measurement and does not automatically turn the datacenter off.</p>
      <p><b>Eight hours tells us duration, not token demand.</b> The capacity estimate also needs an intensity assumption. Here we take the supplied developer study’s 28 output and 333 new input tokens/s peak rates and assume they persist during active hours. Representative session measurements must replace that assumption before a service commitment.</p>
      <p>One daily cohort is the baseline: its users’ active periods overlap. Balanced, non-overlapping cohorts could share the hardware at other times, but we do not automatically triple headcount because eight hours is one-third of a day.</p>
    </details>
    <details class="design-details"><summary>How model use turns into electricity</summary>
      <p>Each AI call asks chips to process the input and generate output. The heavy reference processes fewer tokens per chip per second, so the same workload occupies more chips or takes more time.</p>
      <p>Those chips draw electrical power while working. At a fixed hardware and power limit, using more chip time per person leaves capacity for fewer people. The computers’ electrical energy becomes heat that the cooling system carries away.</p>
      <p>The heavy reference stands in for the top model throughout all eight active hours. More intensive agent use consumes more chip time per person; it lowers headcount without enlarging the datacenter.</p>
    </details>
    <details class="design-details"><summary>Follow the capacity calculation</summary>
      <ol class="energy-calculation">
        <li><b>Keep the power fixed.</b> Six campuses share 500 MW, about 83.3 MW each. One rack plus support needs (210 + 14) kW × 1.10 = 246.4 kW of facility power.</li>
        <li><b>Fit whole rack pairs.</b> Round down 83,333 kW ÷ 246.4 kW: 338 active pairs per campus, using about 83.28 MW. Six sites hold 2,028 pairs and use 499.70 MW.</li>
        <li><b>Assume an active-user intensity.</b> With input processing assumed 10× faster than output generation: 28 + 333 ÷ 10 = <b>61.3 output-equivalent tokens/s per active user</b>.</li>
        <li><b>Estimate rack throughput.</b> Llama 3.1 405B provides about 617–646 adjusted tokens/s per GB300 GPU. Multiply by 72 GPUs and the assumed 2.5× Rubin gain per rack, transferred from an R1 result.</li>
        <li><b>Divide capacity by each user’s work.</b> 338 × 72 × 2.5 × 617–646 ÷ 61.3 ≈ <b>612,000–641,000 simultaneous users per datacenter</b>.</li>
        <li><b>Apply eight active hours.</b> One daily cohort supports roughly 610–640k users per site, each receiving eight active hours. Six sites support about 3.7–3.8 million daily users in this scenario.</li>
      </ol>
      <p>The range reflects benchmark endpoints, not all uncertainty. Sustained token intensity, hardware gain, efficient context reuse, PUE 1.10, memory bandwidth and response-time requirements need validation. No reliability reserve is included.</p>
      <p>Llama 3.1 405B does not establish Claude Opus throughput or best-model quality. It is the heavy hardware reference used to stand in for the top model.</p>
    </details>
    <details class="design-details"><summary>Why coding can process so much data</summary>
      <p>Your typed prompt is only part of the input. Code, conversation history and tool results can return on later calls. An agent may repeat this process many times; parallel agents add work at the same time.</p>
      <p><b>Scenario volumes:</b> 333 new input tokens/s × eight hours gives about 9.59 million new input tokens daily. At 28 output tokens/s, output is 806,400 tokens daily. Reasoning and agent output must be included, not just the final answer shown to the user.</p>
      <p>Those are assumed processed-token volumes, not measured personal usage, stored-file size or internet-download volume. The developer study also lists 860 million repeated-context reads per person daily, separately from new input.</p>
      <p>The baseline assumes effective context reuse. Cache hits still need attention, memory and bandwidth; cache misses need more input processing. These costs are not fully sized and can lower usable capacity. If aggregate input and output work doubles, the same modeled hardware supports about half as many users.</p>
    </details>
    <details class="design-details"><summary>Power, daily electricity and cost</summary>
      <p><b>Power is the rate; energy is power over time.</b> Running at 1 MW for one hour uses 1 MWh. One eight-hour cohort at the modeled full campus load uses about <b>666 MWh during loaded hours, plus idle and transition electricity</b>. The remaining 16 hours are not assumed to draw zero.</p>
      <p>Other users may fill the available time while one person waits for a quota reset. That requires an actual demand schedule. Actual daily and annual electricity use needs an operating-load schedule; the eight-hour requirement alone does not establish fleet utilization.</p>
      <p>The Blender design has 368 rack positions, which fit the lower 190 kW case. At the 210 kW midpoint, 338 active rack pairs fit each site. Cooling and backup still serve the same datacenter load.</p>
      <p><b>Compute-rack purchase:</b> 338 × $7.8M ≈ $2.64B per campus; six sites ≈ $15.82B. Buildings, networking, context memory, electricity and operations are additional. This is not a five-year project total, and the $30B constraint still needs a complete budget review.</p>
    </details>
    <details class="design-details"><summary>Which models inform the estimate?</summary>
      <p class="energy-note">The heavy reference supplies all capacity figures. The other models provide benchmark context, not a routing plan.</p>
      <div class="energy-models">${e.models.map(m=>`<article><div><span>${esc(m.tier)}</span><h3>${esc(m.name)}</h3></div><b>${esc(m.work)}<small>relative chip time*</small></b><p>${esc(m.description)}</p><small>${m.rate.map(n=>n.toLocaleString('en-US')).join('–')} adjusted output tokens/s per GB300 GPU.</small></article>`).join('')}</div>
      <p class="energy-note">*Same token load, fast reference = 1×. These ratios do not establish equal answer quality, response time or measured energy per token.</p>
    </details><p class="reference-source">${esc(e.source)} Estimates require workload and hardware validation.</p>`;
}
renderEnergy();
function renderGeothermal(){
  $('#panel-geothermal').innerHTML=`<p class="energy-intro"><b>Air stays in the building.</b> Fans move warm room air across a water coil. Heat passes into the fluid inside the coil, and pumps carry it through sealed pipes into the rock.</p>
    <div class="season-explainer" role="group" aria-label="Ground cooling season"><button id="geo-summer" aria-pressed="true">Summer · remove heat</button><button id="geo-winter" aria-pressed="false">Winter · recharge</button></div>
    <div id="geo-season" class="geo-season" aria-live="polite"></div>
    <details class="design-details"><summary>Follow the full path</summary><ol class="energy-calculation"><li><b>Collect the room heat.</b> Networking racks use rear-door water coils. Electrical rooms use fan coils. The room-air circuit is designed around 75°F (24°C) fluid.</li><li><b>Move it in fluid.</b> Pumps in the Cold Battery House circulate water mixed with DOWFROST antifreeze through the sealed pipe network.</li><li><b>Exchange heat with rock.</b> Each borehole holds a U-shaped pipe about 500 ft (150 m) deep. Heat crosses the pipe wall into the surrounding ground; the fluid stays inside the pipe and comes back up.</li><li><b>Use the cooling again.</b> Cooled fluid returns to the room-air circuit to absorb more heat. The computers’ main chip cooling circuit uses separate cold plates and outdoor dry coolers.</li></ol><p>The boreholes carry fluid. They do not carry air into the building or draw groundwater into the cooling system.</p></details>
    <details class="design-details"><summary>When the coolers and chillers help</summary><p>When outdoor air is below about 66°F (19°C), the dry coolers can make the room-air circuit’s 75°F (24°C) fluid directly. During warmer loaded hours, the ground takes the heat. Six backup chillers cover heat waves, maintenance or a field that performs worse than expected.</p><div class="assumption"><strong>We assume…</strong><p>The local rock can accept the modeled heat and winter recharging restores enough cooling. A test bore and a thermal response test are required before drilling the full field. Annual cooling savings and the seasonal heat balance must be recalculated for the eight-hour operating scenario; no revised savings percentage is claimed.</p></div></details>
    <details class="design-details"><summary>What keeps the winter fluid from freezing?</summary><p>The outdoor and buried fluid contains about 35% propylene glycol by weight, mixed using Dow’s DOWFROST. Recharging stops below 14°F (−10°C) outdoors, keeping normal running fluid in the high teens °F or warmer. It stays liquid down to about 2°F (−16°C).</p><p>Winter recharge is controlled separately from the warm hall circuit. Cold pipes in the Cold Battery House have vapor-sealed insulation. If the computers stop during a long cold outage, exposed coolers are isolated and drained into indoor tanks while backup-powered pumps keep the indoor and buried circuits circulating.</p><p>Ground circulation cannot keep exposed cooler coils warm against winter wind. The drain-down tanks, expansion allowance and final control setpoints still need engineering.</p></details>
    <button class="inline-action" data-system-view="coldInsulation">See the Cold Battery House and insulated pipes <span>↗</span></button>
    <p class="reference-source">Handoff §5, Cooling and Freeze protection · calc 09 · supplied basis of design. Diagram shows the principle; it is not to scale.</p>`;
  $('#geo-summer').addEventListener('click',()=>{if(state.winter)setToggle('winter')});$('#geo-winter').addEventListener('click',()=>{if(!state.winter)setToggle('winter')});updateGeothermal();
}
function updateGeothermal(){
  if(!$('#geo-season'))return;
  const winter=state.winter;
  $('#geo-summer').setAttribute('aria-pressed',String(!winter));$('#geo-winter').setAttribute('aria-pressed',String(winter));
  $('#geo-season').innerHTML=`<svg class="geo-diagram" viewBox="0 0 420 248" role="img" aria-label="${winter?'Winter: fluid carries heat from the rock to outdoor dry coolers. Outside air removes the heat at the cooler; no air enters the borehole.':'Summer: warm room air transfers heat through a coil into fluid. Fluid carries heat down a sealed U-pipe into rock, then returns cooler.'}"><rect x="8" y="6" width="404" height="91" rx="9" fill="#f7f9ef"/><text x="22" y="25" class="geo-small">${winter?'OUTSIDE · DRY COOLER':'INSIDE · ROOM-AIR COIL'}</text><path d="M52 47c-27 0-27 31 0 31h34" fill="none" stroke="#859778" stroke-width="3"/><path d="m79 73 9 5-9 5" fill="#859778"/><text x="98" y="59">${winter?'Outdoor air':'Room air'}</text><text x="98" y="78" class="geo-small">${winter?'removes heat':'stays inside'}</text><rect x="242" y="40" width="66" height="40" rx="3" fill="#cdd8bf" stroke="#607958"/><path d="M251 45v29m9-29v29m9-29v29m9-29v29m9-29v29m9-29v29" stroke="#879c75"/><path d="${winter?'M236 56h-35m8-6-9 6 9 6':'M199 56h35m-8-6 9 6-9 6'}" stroke="#b58049" fill="none" stroke-width="2"/><text x="204" y="77" class="geo-small">heat</text><path d="M257 80v115q0 24 24 24h6" stroke="#d85a30" fill="none" stroke-width="5"/><path d="M287 219h-1q9 0 9-24V80" stroke="#378add" fill="none" stroke-width="5"/><path d="${winter?'m250 165 7-11 7 11':'m250 154 7 11 7-11'}" fill="#d85a30"/><path d="${winter?'m288 154 7 11 7-11':'m288 165 7-11 7 11'}" fill="#378add"/><path d="M14 114h392" stroke="#a5b892" stroke-width="2"/><text x="22" y="136" class="geo-small">GROUND SURFACE</text><text x="22" y="168">${winter?'Rock gives up heat':'Rock takes the heat'}</text><text x="22" y="188" class="geo-small">Sealed U-pipe · 500 ft (150 m)</text><text x="22" y="208" class="geo-small">Fluid stays inside the pipe</text></svg>
    <p><b>${winter?'Winter recharges the cold battery.':'Summer sends room heat into the rock.'}</b> ${winter?'Outdoor dry coolers chill the circulating field fluid. That fluid removes stored heat from the rock, preparing it for summer. Cold air never goes down the boreholes.':'The fluid gives up heat through the pipe wall and returns cooler. The same room air keeps circulating indoors.'}</p>
    ${winter?'<small>The recharge path is separate from supplying the warm hall circuit. Recharge stops below 14°F (−10°C) outdoors.</small>':'<small>The ground handles the room-air cooling share. Most chip heat follows the warmer circuit to the outdoor dry coolers.</small>'}`;
}
function renderFreeze(){
  $('#panel-freeze').innerHTML=`<p class="energy-intro">The updated design combines <b>antifreeze, a warm-water bypass, cooler isolation and indoor drain-down tanks</b>. The protection changes when the computers stop producing heat.</p>
    <h3>Where the heat comes from</h3><p><b>The running computers are the heat source.</b> At modeled full load, about 75 MW of IT electricity per campus becomes heat. Pumps carry that heat outdoors in liquid; there is no hot-air duct from the hall to the dry coolers.</p>
    <ol class="energy-chain" aria-label="How computer heat reaches outdoor air"><li>Computers make heat</li><li>Liquid carries heat</li><li>Outdoor air takes heat</li></ol>
    <p>At the radiator, warm liquid stays inside metal tubes. Outside air passes over the tubes and fins, picks up heat and leaves warmer. Cooler liquid returns to collect more heat. Room-air heat first crosses an indoor water coil; that air stays inside.</p>
    <details class="design-details"><summary>Does computer heat make a cold snap harmless?</summary><p>Heat helps only where enough warm liquid is circulating. An idle cooler, an isolated pipe or a pump failure can leave an outdoor section cold even while the rest of the campus is producing heat.</p><p>A colder day increases heat loss. Whether a coil stays warm depends on its incoming liquid temperature, flow and exposure. This concept has not yet calculated the worst-case cold-snap heat balance, so the campus heat total is not proof that every pipe stays above freezing.</p><p>In cold weather, the controls prevent overcooling by slowing or stopping fans. The bypass keeps the hall supply warm enough, but it does not by itself protect every outdoor coil. Adequate antifreeze, monitored flow and a verified shutdown procedure remain necessary. The animated fans illustrate operation; real controls stage them according to load and temperature.</p></details>
    <div class="freeze-fluid"><b>Dow’s DOWFROST</b><p>About 35% propylene glycol by weight in the building, outdoor and borehole circuits. The separate rack circuits use PG25, a premixed 25% coolant.</p><small>Normal minimum: high teens °F (~−7°C). Stays liquid down to about 2°F (−16°C).</small></div>
    <h3>While the computers are running</h3><ol class="energy-calculation"><li>Slow the cooler fans, then stage coolers off as colder outside air removes heat more readily.</li><li>A motorized bypass blends warm return fluid around the coolers, keeping building supply at <b>70°F (21°C) or warmer</b>.</li><li>Each cooler has outlet freeze sensing and shut-off valves. Near the planned freeze limit, controls open the bypass and stop its fans.</li><li>Stop recharging the ground below <b>14°F (−10°C)</b> outdoors.</li></ol>
    <button class="inline-action" data-system-view="bypass">See the bypass and cooler valves <span>↗</span></button>
    <h3>If the computers stop during a long cold outage</h3><ol class="energy-calculation"><li><b>Close off the exposed coolers.</b> Winter wind can chill their coils even with the fans off.</li><li><b>Drain their fluid indoors.</b> Each cooler’s drain connects to the indoor drain-down tanks.</li><li><b>Keep indoor and buried fluid moving.</b> Backup power runs the pumps; the project estimates under 1 MW for that duty.</li><li><b>Check before restarting.</b> Any remaining slush must thaw. Expansion tanks accommodate fluid expansion; final volumes and restart controls need engineering.</li></ol>
    <button class="inline-action" data-system-view="drainTanks">See the drain-down tanks <span>↗</span></button>
    <details class="design-details"><summary>Freeze limits and remaining engineering</summary><p>About 35% propylene glycol by weight corresponds to about 36% DOWFROST product. The freeze alarm concept uses a 6°F margin above the ~2°F fluid freeze point: about 8°F (−13°C). The final setpoint still needs confirmation.</p><p>Burst protection and freeze protection are different. The source estimates burst protection to about −36°F (−38°C), interpolated from Dow’s tables. Residual fluid can still become slush; this is not a guarantee of flow or safe restart.</p><p>EVAPCO’s eco-Air instructions warn that opening drains and vents alone does not empty every tube; large dry coolers require air-assisted drainage. That equipment and sequence are not yet engineered in this concept.</p><div class="assumption"><strong>Still to confirm</strong><p>Fluid concentration, full drainability, tank capacities, pipe slopes, expansion volume, alarm settings and restart sequence. The illustrated tank and valve dimensions are placeholders. Heat tracing and wind screens remain optional.</p></div></details>
    <details class="design-details"><summary>Keeping indoor pipes dry</summary><p>The halls target a dew point of about 50°F (10°C). Cooling units keep rack supply at or above 77°F (25°C), and cold recharge pipes have vapor-sealed insulation. New wall sensors, a fresh-air drying unit and loading-dock airlocks show the condensation controls.</p><p>The fresh-air drying equipment still needs sizing. Its dehumidification duty must be verified separately from the 75°F (24°C) room-air cooling circuit.</p></details>
    <p class="reference-source">Updated handoff §5, Freeze protection and Condensation control · punch list 1j–1l. <a href="https://www.evapcoasia.com/sites/evapcoasia.com/files/2025-12/Bulletin%20EA24OM_eco-Air%20OM%28202512%29.pdf" target="_blank" rel="noopener">EVAPCO eco-Air operation manual, p.15</a>. Layout and tank sizes are illustrative; final engineering remains open.</p>`;
}
renderGeothermal();renderFreeze();
function designDetails(key){
  const d=content.design[key];if(!d)return '';
  return `<details class="design-details"><summary>${esc(d.title)}</summary><div class="design-copy">${d.html}${d.notes?`<details class="source-notes"><summary>Sources, alternatives and remaining checks</summary><div>${d.notes}</div></details>`:''}</div></details>`;
}
const powerPath=()=>`<div class="power-path"><span class="field-label">Follow the electrical connection</span><ol><li>Battery cabinets</li><li>UPS + distribution</li><li>Overhead power busways</li><li>Compute + network racks</li></ol><p>Batteries feed the UPS during an outage. The UPS and distribution feed the gold busways, with drops down to the racks. Pumps, CDUs and controls also stay on battery power until the generators take over.</p><small>Connection layout is illustrative; electrical engineering remains to be confirmed.</small><button class="inline-action" data-view-action="power">Trace it in the model <span>↗</span></button></div>`;
function equipmentContext(key){
  if(key==='sealed')return '<div class="system-note"><h3>Where the air goes</h3><p>Outside air passes over the outdoor coolers’ coils. Cooling fluid travels between those coils and the building. A small, dried fresh-air supply serves staff; ground-loop pipes never bring air into the halls.</p></div>';
  if(systemViews[key])return `<div class="system-note"><button class="inline-action" data-system-view="${key}">Locate this equipment in the model <span>↗</span></button>${['bypass','drainTanks','freezeProtection'].includes(key)?'<p class="context-note">Drain-down applies when the computers stop producing heat during a long cold outage. Tank capacity, drainability, expansion volume and restart controls still need engineering; any remaining slush must thaw before restarting.</p>':''}${key==='freshAir'?'<p class="context-note">The fresh-air drying unit’s capacity and dehumidification duty still need sizing; the 75°F (24°C) room-air circuit alone does not establish the 50°F (10°C) dew-point target.</p>':''}</div>`;
  if(['electrical','compute','network'].includes(key))return powerPath()+(key==='network'?'<p class="context-note">The networking racks have rear-door water coils: the equipment fans push warm air through those coils. There are no hot-aisle chimneys.</p>':'');
  if(['fire','trench'].includes(key))return '<div class="system-note"><h3>Which lines are which?</h3><p><b>Red, at the ceiling:</b> fire sprinklers. <b>Orange and blue, in the floor trenches:</b> warm coolant returning and cool coolant supplied to the racks. <b>Gold, overhead:</b> electrical power. The light gray overhead bars are cable trays.</p></div>';
  if(['boreholes','batteryHouse'].includes(key))return '<div class="system-note"><h3>Two different kinds of battery</h3><p>The <b>cold battery</b> stores cooling in the ground. The Cold Battery House contains pumps and pipes for that field. The <b>electrical UPS batteries</b> are inside the hall and carry electrical loads during an outage.</p><button class="inline-action" data-view-action="boreholes">Show the boreholes <span>↗</span></button></div>';
  return '';
}
function renderObject(key){
  const o=content.objects[key];if(!o)return;state.object=key;$('#object-select').value=key;$('#object-title').textContent=o.name;$('#panel-closer').scrollTop=0;if(state.card===2)$('#headline').textContent=o.name;
  $('#object-description').innerHTML=`<p>${markup(o.text)}</p><div class="key-number">${markup(o.number)}</div>${equipmentContext(key)}`;
  const d=content.design[o.why.replace(/^#/,'')];
  $('#object-design').innerHTML=`<h3>Why this choice</h3><div class="object-reason">${d.why}</div><h3>Full design details</h3>${designDetails(o.why.replace(/^#/,''))}<a class="source-link" target="_blank" rel="noopener" href="${content.mathURL+o.math}">Original calculation source ↗</a>`;
}
$('#object-select').addEventListener('change',e=>renderObject(e.target.value));
function renderCard(){
  const b=content.bubbles[state.index];$('#card-kicker').textContent=state.index===0?'SEED / THE IDEA':state.index>10?'SEED / '+(state.index===11?'THE BUDGET':'THE COMPARISON'):`${String(state.index).padStart(2,'0')} / ${titleAt(state.index)}`;
  $('#headline').textContent=b.headline;$('#bullets').replaceChildren(...b.bullets.map(t=>{const li=document.createElement('li');li.textContent=t;return li;}));
  $('#number').textContent=b.number;$('#number').classList.toggle('long',b.number.length>11);$('#unit').textContent=b.unit;
  $('#assumption').hidden=!b.assumption||Boolean(b.hideOverviewAssumption);$('#assumption p').textContent=b.assumption.replace(/^…/,'');$('#source').textContent=b.source;
  $('#reference-models').hidden=!b.referenceModels;$('#story').classList.toggle('has-references',!!b.referenceModels);
  $('#story').classList.toggle('has-four-cards',cardCount()===4);
  $('#show-system').hidden=!['geothermal','freeze'].includes(specialCard());$('#show-system').textContent=specialCard()==='geothermal'?'How ground cooling works →':'How we prevent freezing →';
  if(b.referenceModels){$('#reference-models p').textContent=b.referenceModels.map(m=>`${m.tier}: ${m.name}`).join(' · ');$('#reference-models small').textContent=b.referenceAssumption;$('#reference-models').title=b.referenceSource;}
  $('#view-guide').hidden=![3,4,6].includes(state.index);
  $('#view-guide').innerHTML=state.index===6?'<button class="inline-action" data-view-action="boreholes">Locate the borehole field <span>↗</span></button>':`<details><summary>Identify the power and cooling lines</summary><p><b>Gold above:</b> electrical power. <b>Light gray above:</b> cable trays. <b>Red at the ceiling:</b> sprinklers. <b>Orange + blue below:</b> warm-return and cool-supply pipes in the floor trenches.</p>${powerPath()}</details>`;
  $('#choice-why').textContent=b.why;
  $('#choice-details').innerHTML=(b.card?`<h3>What we chose</h3><p>${markup(b.card.what)}</p><h3>How it works</h3><p>${markup(b.card.how)}</p>`:'')+(b.assumption?`<div class="assumption"><strong>We assume…</strong><p>${esc(b.assumption.replace(/^…/,''))}</p></div>`:'')+(b.card?.math.length?`<details class="design-details"><summary>Numbers behind this choice</summary><ul class="math-notes">${b.card.math.map(m=>`<li>${markup(m)}</li>`).join('')}</ul></details>`:'');
  $('#choice-design').innerHTML=`<h3>Supporting design details</h3>${b.designKeys.map(designDetails).join('')}`;
  const related=b.objectKeys,other=Object.keys(content.objects).filter(k=>!related.includes(k));
  $('#object-select').innerHTML=`<optgroup label="At this stop">${related.map(k=>`<option value="${k}">${esc(content.objects[k].name)}</option>`).join('')}</optgroup><optgroup label="Elsewhere on campus">${other.map(k=>`<option value="${k}">${esc(content.objects[k].name)}</option>`).join('')}</optgroup>`;
  renderObject(related[0]);showCard(0);
  $('#back').disabled=state.index===0;$('#next span').textContent=state.index===0?'Begin tour':state.index===12?'Start again':'Next';
  $('#position-title').textContent=titleAt(state.index);$('#position-count').textContent=String(state.index+1).padStart(2,'0')+' / 13';
  $$('#progress button').forEach((el,i)=>{el.classList.toggle('active',i===state.index);el.classList.toggle('past',i<state.index);el.setAttribute('aria-current',String(i===state.index));});
  $$('#stop-list nav button').forEach((el,i)=>el.setAttribute('aria-current',String(i===state.index)));
}
function animateTo(pos,target,duration=1500,done){
  flight={start:performance.now(),duration:reduced?0:duration,from:camera.position.clone(),to:v(pos),targetFrom:controls.target.clone(),targetTo:v(target),done};state.flying=true;controls.enabled=false;
}
function completeArrival(){state.flying=false;controls.enabled=true;clearTimeout(storyTimer);storyTimer=setTimeout(()=>$('#story').classList.remove('pending'),reduced?0:500);}
function goTo(index,instant=false){
  if(!state.ready)return;
  clearTimeout(storyTimer);$('#story').classList.add('pending');$('#story').classList.remove('tucked');state.exploring=false;state.powerFocus=false;
  state.index=THREE.MathUtils.clamp(index,0,12);const b=content.bubbles[state.index];
  camera.fov=state.index===6?62:([0,2,10,11,12].includes(state.index)?52:44);camera.updateProjectionMatrix();
  state.xray=b.toggles.includes('X-ray');state.ground=b.toggles.includes('Ground cutaway');state.flow=/heat flow/i.test(b.toggles);state.hover=null;
  renderCard();applyToggles();$('#view-status').textContent='Proposed Cambridge campus';
  if(instant){flight=null;camera.position.copy(v(cameraAt(state.index)[0]));controls.target.copy(v(cameraAt(state.index)[1]));camera.lookAt(controls.target);controls.update();completeArrival();}
  else animateTo(...cameraAt(state.index),Math.max(1200,Math.min(2200,camera.position.distanceTo(v(cameraAt(state.index)[0]))*3)),completeArrival);
  history.replaceState(null,'','#stop-'+state.index);closeList();
}
function navigate(delta){
  if(!state.ready||state.flying)return;
  const next=state.index===12&&delta>0?0:THREE.MathUtils.clamp(state.index+delta,0,12);
  if(state.exploring){$('#story').classList.add('pending');animateTo(...cameraAt(state.index),700,()=>goTo(next));}
  else goTo(next);
}
$('#next').addEventListener('click',()=>navigate(1));$('#back').addEventListener('click',()=>navigate(-1));
$('.brand').addEventListener('click',e=>{e.preventDefault();goTo(0)});
$('#expand-story').addEventListener('click',()=>goTo(state.index));
function enterExplore(){if(!state.ready)return;state.exploring=true;if(!state.clean)$('#story').classList.add('tucked');$('#story').classList.remove('pending');$('#view-status').textContent='Exploring · Next continues the story';$('#leader').classList.add('hidden');}
controls.addEventListener('start',enterExplore);
for(let i=0;i<13;i++){
  const btn=document.createElement('button');btn.type='button';btn.title=titleAt(i);btn.setAttribute('aria-label',`Jump to ${titleAt(i)}`);btn.addEventListener('click',()=>goTo(i));$('#progress').append(btn);
  const link=document.createElement('button');link.innerHTML=`<span>${i===0?'○':i>10?'◇':String(i).padStart(2,'0')}</span>${esc(titleAt(i))}`;link.addEventListener('click',()=>goTo(i));$('#stop-list nav').append(link);
}
function closeList(){$('#stop-list').hidden=true;$('#index-toggle').setAttribute('aria-expanded','false');}
$('#index-toggle').addEventListener('click',()=>{const hidden=!$('#stop-list').hidden;$('#stop-list').hidden=hidden;$('#index-toggle').setAttribute('aria-expanded',String(!hidden));});$('.close-list').addEventListener('click',closeList);
let lastFocus;
function showDialog(dialog){lastFocus=document.activeElement;dialog.showModal();dialog.querySelector('button')?.focus();}
for(const d of $$('dialog')){d.querySelector('.dialog-close').addEventListener('click',()=>d.close());d.addEventListener('close',()=>lastFocus?.focus());d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close();}});}
function openObject(key){if(!content.objects[key])return;enterExplore();$('#story').classList.remove('tucked');renderObject(key);showCard(2);}
$('#help-toggle').addEventListener('click',()=>showDialog($('#help')));
$('#fullscreen').addEventListener('click',async()=>{try{if(document.fullscreenElement)await document.exitFullscreen();else await document.documentElement.requestFullscreen();}catch{}});
window.addEventListener('keydown',e=>{if(e.defaultPrevented||e.altKey||e.ctrlKey||e.metaKey||$$('dialog').some(d=>d.open)||e.target.closest('select,input,textarea')||(e.key===' '&&e.target.closest('button,summary,a')))return;if(['ArrowRight','ArrowDown','PageDown',' '].includes(e.key)){e.preventDefault();navigate(1)}else if(['ArrowLeft','ArrowUp','PageUp'].includes(e.key)){e.preventDefault();navigate(-1)}else if(e.key==='Home'){e.preventDefault();goTo(0)}else if(e.key==='End'){e.preventDefault();goTo(12)}else if(e.key==='Escape'){if(state.clean){e.preventDefault();setCleanView(false);return;}closeList();if(state.exploring)goTo(state.index);else showCard(0)}});
// All object picking uses the actual Blender meshes, including the revealed interior.
const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();
function pick(e){pointer.set(e.clientX/innerWidth*2-1,-e.clientY/innerHeight*2+1);raycaster.setFromCamera(pointer,camera);return raycaster.intersectObjects(pickables,false).find(hit=>visible(hit.object));}
renderer.domElement.addEventListener('pointerdown',e=>pointerDown={x:e.clientX,y:e.clientY});
renderer.domElement.addEventListener('pointerup',e=>{if(state.clean){pointerDown=null;return;}if(!pointerDown||Math.hypot(e.clientX-pointerDown.x,e.clientY-pointerDown.y)>5)return;const hit=pick(e),key=hit?objectKey(hit.object):null;if(key)openObject(key);pointerDown=null;});
let hoverTimer=null,pendingPointer=null;
renderer.domElement.addEventListener('pointermove',e=>{
 if(state.clean)return;
 pendingPointer={clientX:e.clientX,clientY:e.clientY,buttons:e.buttons};
 if(hoverTimer)return;
 hoverTimer=setTimeout(()=>{
  hoverTimer=null;const e=pendingPointer;if(!e||state.clean||state.flying||e.buttons)return;
  const hit=pick(e),key=hit?objectKey(hit.object):null;
  if(key!==state.hover){state.hover=key;applyVisuals();}renderer.domElement.style.cursor=key?'pointer':'grab';$('#tooltip').hidden=!key;
  if(key){$('#tooltip').textContent=content.objects[key].name;$('#tooltip').style.left=Math.min(e.clientX+15,innerWidth-300)+'px';$('#tooltip').style.top=(e.clientY+18)+'px';}
 },70);
});
renderer.domElement.addEventListener('pointerleave',()=>{clearTimeout(hoverTimer);hoverTimer=null;pendingPointer=null;$('#tooltip').hidden=true;state.hover=null;applyVisuals()});
// Low-cost moving arrowheads make direction readable without obscuring equipment.
const flowGroup=new THREE.Group();scene.add(flowGroup);const flowPaths=[];
function flow(points,color,ground=false,room=false,season=null){const curve=new THREE.CurvePath();points.map(v).forEach((p,i,a)=>{if(i)curve.add(new THREE.LineCurve3(a[i-1],p));});const length=curve.getLength();const beads=[];const material=new THREE.MeshBasicMaterial({color,depthTest:true});
 for(let i=0;i<Math.max(3,Math.ceil(length/15));i++){const mesh=new THREE.Mesh(new THREE.ConeGeometry(.45,1.5,6),material);flowGroup.add(mesh);beads.push(mesh);}flowPaths.push({curve,length,beads,ground,season:season||(room?'summer':null)});}
flow([[-35.57,-18,-.1],[-35.57,20,-.1],[-36.62,20,2.7],[-36.62,21,2.3],[-36.62,26,2.3],[-36.62,26,2.8],[-1.3,26,2.8],[-1.3,26,1.8],[-1.3,30,1.8],[-1.3,30,7.2],[-1.3,38,7.2]],'#d85a30');
flow([[-.4,38,7.2],[-.4,30,7.2],[-.4,30,1.8],[-.4,27,1.8],[-.4,27,2.8],[-36.18,27,2.8],[-36.18,27,2.3],[-36.18,21,2.3],[-36.18,20,2.7],[-35.13,20,-.1],[-35.13,-18,-.1]],'#378add');
flow([[-38.47,0,-.1],[-38.47,20,-.1],[-39.52,20,2.7],[-39.52,21,2.3],[-39.52,28,2.3],[-39.52,28,2.8],[-102,28,2.8],[-110,28,2.8],[-110,28,-.7],[-110,-47,-.7],[-3,-47,-.7],[-3,-47,1.2],[-.6,-47,1.2],[-.6,-47,-1],[-.6,-61,-1],[.13,-61,-1],[.13,-220,-1],[.13,-220,-149.8],[0,-220,-150]],'#d85a30',true,true);
flow([[0,-220,-150],[-.13,-220,-149.8],[-.13,-220,-1],[-.13,-62,-1],[-.13,-62,-1.8],[.6,-62,-1.8],[.6,-48.5,-1.8],[.6,-48.5,1.2],[3,-48.5,1.2],[3,-48.5,-2],[-111.5,-48.5,-2],[-111.5,29,-2],[-111.5,29,2.8],[-102,29,2.8],[-39.08,29,2.8],[-39.08,29,2.3],[-39.08,21,2.3],[-39.08,20,2.7],[-38.03,20,-.1],[-38.03,0,-.1]],'#378add',true,true);
// Winter recharge goes between the outdoor room-loop coolers and the field.
// Do not reverse the hall path and suggest cold recharge fluid enters its coils.
flow([[1.25,38,7.2],[1.25,30,7.2],[1.25,30,1.8],[1.25,29,1.8],[1.25,29,2.8],[-102,29,2.8],[-111.5,29,2.8],[-111.5,29,-2],[-111.5,-48.5,-2],[3,-48.5,-2],[3,-48.5,1.2],[.6,-48.5,1.2],[.6,-48.5,-1.8],[.6,-62,-1.8],[-.13,-62,-1.8],[-.13,-62,-1],[-.13,-220,-1],[-.13,-220,-149.8],[0,-220,-150]],'#378add',true,false,'winter');
flow([[0,-220,-150],[.13,-220,-149.8],[.13,-220,-1],[.13,-61,-1],[-.6,-61,-1],[-.6,-47,-1],[-.6,-47,1.2],[-3,-47,1.2],[-3,-47,-.7],[-110,-47,-.7],[-110,28,-.7],[-110,28,2.8],[-102,28,2.8],[.5,28,2.8],[.5,28,1.8],[.5,30,1.8],[.5,30,7.2],[.5,38,7.2]],'#d85a30',true,false,'winter');
flow([[-1.3,35,7.2],[-1.3,35,8.3],[-.4,35,8.3],[-.4,35,7.2]],'#d85a30',false,false,'winter');
flow([[-85,26,2.8],[-116,26,2.8],[-116,-34,.6],[-125,-34,.6]],'#d85a30');
flow([[112,34,.6],[112,29,.6],[100,29,.6],[100,29,2.8]],'#378add');
const labelIds=['compute','spine','bridges','network','coolers','boreholes','solar','generators','trench','bypass','dewpoint','substation','house'];
if(labelIds.length!==content.labels.length)throw Error('Model label mapping needs to match the current design');
const labelNodes=content.labels.map((label,i)=>{const el=document.createElement('button');el.className='label';el.textContent=label;el.addEventListener('click',()=>openObject(labelIds[i]));$('#labels').append(el);return{el,key:labelIds[i]};});
const claritySpecs=[
  {key:'boreholes',point:[0,-142.5,1],text:'Boreholes below this meadow · Show',mode:'surface',action:showBoreholes},
  {key:'boreholes',point:[0,-220,-80],text:'Highlighted U-loop · 150 m deep',mode:'ground',action:()=>openObject('boreholes')},
  {key:'batteryHouse',point:[0,-47,7],text:'Cold Battery House · pumps + pipes',mode:'ground',action:()=>openObject('batteryHouse')},
  {key:'battery',point:[-21,-10,2.5],text:'Battery cabinets',mode:'power',action:()=>openObject('electrical')},
  {key:'electrical',point:[-7,12,2],text:'UPS + distribution',mode:'interior',action:()=>openObject('electrical')},
  {key:'power',point:[-36.4,12,4.8],text:'Power busway · gold',mode:'interior',action:()=>openObject('electrical')},
  {key:'rackdrop',point:[-36.65,-7.8,3.375],text:'Power drops to each rack',mode:'power',action:()=>openObject('electrical')},
  {key:'fire',point:[-37,-5,6.6],text:'Fire sprinklers · red',mode:'interior',action:()=>openObject('fire')},
  {key:'compute',point:[-36.4,-10,2.3],text:'Compute racks',mode:'interior',action:()=>openObject('compute')},
  {key:'trench',point:[-38.25,-10,.1],text:'Cooling in floor trench',mode:'interior',action:()=>openObject('trench')},
  {key:'network',point:[-39.3,-3,2.3],text:'Network rack + rear-door coil',mode:'interior',action:()=>openObject('network')}
];
const clarityNodes=claritySpecs.map(spec=>{const el=document.createElement('button');el.className='clarity-label clarity-'+spec.key;el.textContent=spec.text;el.hidden=true;el.addEventListener('click',spec.action);$('#clarity-labels').append(el);return{...spec,el};});
function project(point){const p=v(point).project(camera);return{x:(p.x+1)*innerWidth/2,y:(1-p.y)*innerHeight/2,z:p.z};}
function clarityOverlays(){
  const obstacles=[$('#story'),$('.tools'),$('#scene-key')].filter(el=>!el.hidden&&getComputedStyle(el).display!=='none').map(el=>el.getBoundingClientRect());
  const occupied=[];const mode=state.ground?'ground':state.xray?'interior':'surface';
  for(const {el,point,key,mode:labelMode} of clarityNodes){
    const p=project(point);let blocked=(state.powerFocus&&['fire','compute','trench','network'].includes(key))||(labelMode!==mode&&!(labelMode==='power'&&state.powerFocus))||state.flying||p.z>1||p.z<0||p.x<105||p.x>innerWidth-105||p.y<112||p.y>innerHeight-140;
    if(!blocked){
      el.hidden=false;const width=el.offsetWidth,height=el.offsetHeight;let placement=null;
      for(const offset of [0,-28,28,-56,56]){
        const rect={left:p.x+offset-width/2,right:p.x+offset+width/2,top:p.y-height-14,bottom:p.y};
        if(rect.left<16||rect.right>innerWidth-16)continue;
        if(!obstacles.concat(occupied).some(r=>rect.left<r.right+12&&rect.right>r.left-12&&rect.top<r.bottom+12&&rect.bottom>r.top-12)){placement={rect,offset};break;}
      }
      blocked=!placement;
      if(placement){el.style.left=(p.x+placement.offset)+'px';el.style.top=(p.y-14)+'px';el.style.setProperty('--anchor-x',-placement.offset+'px');occupied.push(placement.rect);}
    }
    el.hidden=blocked;
  }
  return occupied;
}
function overlays(){
 if(state.clean)return;
 const key=focusIds[state.index];const leader=$('#leader');leader.classList.toggle('hidden',!key||state.exploring||state.flying||$('#story').classList.contains('pending'));
 if(key){const p=project(anchors[key]),r=$('#story').getBoundingClientRect();if(p.z>1||p.x<r.right+10||p.y<95||p.y>innerHeight-110)leader.classList.add('hidden');else{const yy=Math.min(r.bottom-40,Math.max(r.top+80,p.y));$('#leader path').setAttribute('d',`M${r.right},${yy} L${r.right+24},${yy} L${p.x},${p.y}`);$('#leader circle').setAttribute('cx',p.x);$('#leader circle').setAttribute('cy',p.y);}}
 const clarityOccupied=clarityOverlays();
 if(state.labels){const occupied=clarityOccupied.map(r=>({x:(r.left+r.right)/2,y:(r.top+r.bottom)/2}));for(const {el,key} of labelNodes){const p=project(anchors[key]);const blocked=(key==='boreholes'&&!state.ground)||(['compute','network','trench'].includes(key)&&!state.xray)||p.z>1||p.x<20||p.x>innerWidth-20||p.y<100||p.y>innerHeight-110||occupied.some(q=>Math.abs(q.x-p.x)<190&&Math.abs(q.y-p.y)<48);el.hidden=blocked;if(!blocked){el.style.left=p.x+'px';el.style.top=p.y+'px';occupied.push(p)}}}
 const d=camera.position.clone().sub(controls.target);$('#compass svg').style.transform=`rotate(${Math.atan2(d.x,d.z)}rad)`;
}
function tick(time){requestAnimationFrame(tick);const dt=Math.min(.05,(time-lastTime)/1000);lastTime=time;
 if(flight){const f=flight,t=f.duration===0?1:Math.min(1,(time-f.start)/f.duration),s=t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;camera.position.lerpVectors(f.from,f.to,s);controls.target.lerpVectors(f.targetFrom,f.targetTo,s);camera.lookAt(controls.target);if(t===1){flight=null;f.done?.();}}
 else controls.update();
 if(!reduced&&fanBatches.length)updateFans(dt);
 if(state.flow)for(const f of flowPaths){f.beads.forEach((b,i)=>{b.visible=(!f.ground||state.ground)&&(!f.season||f.season===(state.winter?'winter':'summer'));if(!b.visible)return;const t=(((reduced?0:time)*.00006+i/f.beads.length)%1+1)%1;b.position.copy(f.curve.getPoint(t));const tangent=f.curve.getTangent(t);b.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),tangent);});}
 overlays();renderer.render(scene,camera);
}
requestAnimationFrame(tick);
window.addEventListener('resize',()=>{renderer.setSize(innerWidth,innerHeight);projectionOffset()});
try{
 const gltf=await new GLTFLoader().loadAsync('./assets/campus.glb',e=>{if(e.total)$('#loadbar').style.width=(10+e.loaded/e.total*85)+'%'});campus=gltf.scene;scene.add(campus);
 campus.traverse(o=>{if(o.name&&o.type==='Object3D')groups[o.name]=o;});
 // glTF empty nodes may load as Group or Object3D, so retain any named parent.
 for(const o of campus.children)groups[o.name]=o;
 prepareFans();
 campus.traverse(o=>{if(!o.isMesh)return;o.castShadow=true;o.receiveShadow=true;pickables.push(o);const mats=Array.isArray(o.material)?o.material:[o.material];const cloned=mats.map(m=>{const mat=m.clone();const key=objectKey(o);materials.push({mat,base:mat.color.clone(),key,name:m.name,emissive:mat.emissive?.clone()||new THREE.Color()});if(m.name==='groundPipe'){mat.transparent=true;mat.opacity=.22;mat.depthWrite=false;}if(m.name==='glass'){mat.transparent=true;mat.opacity=.24;mat.depthWrite=false;mat.side=THREE.DoubleSide;}return mat;});o.material=Array.isArray(o.material)?cloned:cloned[0];});
 state.ready=true;$('#loadbar').style.width='100%';$('#loading').style.opacity='0';setTimeout(()=>$('#loading').remove(),550);
 if(params.has('render'))document.body.classList.add('render-only');projectionOffset();
 const initial=parseInt(params.get('stop')??location.hash.replace('#stop-',''),10);goTo(Number.isFinite(initial)?initial:0,true);
 // Read-only state and explicit controls are used by the QA harness and saved still views.
 window.SEED={state,content,groups,goTo,setToggle,openObject,showBoreholes,focusPower,focusSystem,camera,controls,renderer,scene,anchors,project,ready:true,
  inspect:()=>({meshes:pickables.length,drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles,groups:Object.keys(groups),fans:fanBatches.map(({mesh})=>({name:mesh.name,count:mesh.count})),assumption:content.bubbles[state.index].assumption}),
  view:(pos,target)=>{flight=null;camera.position.copy(v(pos));controls.target.copy(v(target));controls.update()},
  objectScreen:key=>project(anchors[key])};
}catch(error){console.error(error);$('#loadnote').innerHTML='The campus model could not load. Start the static server from the tour folder, then refresh.<a href="./stills/index.html">View the stills ↗</a>';$('#loading').style.opacity='1';}
