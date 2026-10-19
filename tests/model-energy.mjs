import {chromium} from 'playwright';
import fs from 'node:fs';
import assert from 'node:assert/strict';

// Independent acceptance from the raw heavy benchmark and preserved case C rates.
const calculated=JSON.parse(fs.readFileSync('assets/top-model-sizing.json','utf8'));
const close=(a,b,label)=>assert.ok(Math.abs(a-b)<1e-6,label);
const rackMW=(210+14)*1.10/1000;
const racks=Math.floor((500/6)/rackMW);
assert.equal(racks,338);
assert.equal(calculated.hardware.racksPerCampus,racks);
assert.equal(calculated.hardware.racksFleet,2028);
assert.equal(calculated.hardware.gpusPerCampus,24336);
close(calculated.hardware.loadedCampusMW,83.2832,'Support and cooling counted exactly once');
close(calculated.hardware.loadedFleetMW,499.6992,'Six sites remain below 500 MW');
close(calculated.hardware.computeRackPurchaseFleetB,15.8184,'Fixed fleet compute-rack purchase');
assert.equal(calculated.assumptions.targetUsers,400e6);
assert.equal(calculated.assumptions.promptsPerDay,20);
assert.equal(calculated.assumptions.agentTasksPerDay,5);
assert.equal(calculated.assumptions.outputPerSecond,4.6);
assert.equal(calculated.assumptions.inputPerSecond,40);
assert.equal(calculated.assumptions.activeHoursPerUserDay,undefined,'No active-hour substitution');
assert.equal(calculated.baseline.workPerUserAtPeak,8.6);
for(const [i,raw] of [259,271].entries()){
 const effective=raw*(1+9400/(680*10));
 const throughput=racks*72*2.5*effective;
 const users=throughput/(4.6+40/10);
 close(calculated.baseline.usersPerCampus[i],users,'Raw benchmark divided by unchanged source workload');
 close(calculated.baseline.usersFleet[i],users*6,'Six separately capped campuses');
 close(calculated.baseline.targetPercent[i],users*6/400e6*100,'Fraction of target population');
 close(calculated.baseline.facilityMWForTarget[1-i],400e6*(4.6+40/10)/(72*2.5*effective)*rackMW,'Target extrapolation uses the same workload and power basis');
}
const content=JSON.parse(fs.readFileSync('assets/content.json','utf8'));
assert.equal(content.planningRevision,'fixed-workload-03');
assert.equal(content.modelEnergy.perCampus,'4.37–4.57M');
assert.equal(content.modelEnergy.fleet,'26.19–27.40M');
assert.equal(content.bubbles[0].hideOverviewAssumption,true);
assert.equal(content.bubbles[10].number,'~4.37–4.57M');
assert.equal(content.bubbles[11].number,'$2.64B');
assert.ok(content.bubbles[7].unit.includes('varies with load'));
assert.ok(!JSON.stringify(content.bubbles).includes('610–640'));
assert.ok(content.design.memory.html.includes('Cache size, bandwidth and added support power remain unvalidated'));
const energyStops=[0,3,8,10,11,12];
const report={passed:false,checks:[],screenshots:[],errors:[],network:[],viewports:[],reference:'Unchanged 20 questions and five tasks daily; raw heavy benchmark, 4.6/40 peak rates, independently capped campuses and overview-block removal'};
const browser=await chromium.launch({channel:'chrome',headless:true});
const context=await browser.newContext({viewport:{width:1920,height:1080},reducedMotion:'reduce'});
const page=await context.newPage();
page.on('pageerror',error=>report.errors.push(String(error)));
page.on('response',response=>{if(response.status()>=400)report.network.push({url:response.url(),status:response.status()});});
const check=(name,pass)=>{assert.ok(pass,name);report.checks.push(name);};
const settled=()=>page.waitForFunction(()=>window.SEED?.ready&&!SEED.state.flying&&!document.querySelector('#story').classList.contains('pending')&&Number(getComputedStyle(document.querySelector('#story')).opacity)>.99);
const atStop=async stop=>{await page.evaluate(stop=>SEED.goTo(stop,true),stop);await settled();};
const noOverflow=async name=>{
 const metrics=await page.evaluate(()=>{
  const panel=document.querySelector('#panel-energy'),story=document.querySelector('#story');
  return {viewport:innerWidth,document:document.documentElement.scrollWidth,story:[story.clientWidth,story.scrollWidth],panel:[panel.clientWidth,panel.scrollWidth]};
 });
 check(name,metrics.document<=metrics.viewport+1&&metrics.story[1]<=metrics.story[0]+1&&metrics.panel[1]<=metrics.panel[0]+1);
 return metrics;
};
const capture=async name=>{const file=`qa/model-energy-${name}.png`;await page.screenshot({path:file});report.screenshots.push(file);};
try{
 await page.goto('http://127.0.0.1:4173/#stop-3');await settled();
 check('Removed coding scenarios are not available',await page.locator('#energy-scenario').count()===0);
 for(const viewport of [{name:'desktop',width:1920,height:1080},{name:'laptop',width:1366,height:768},{name:'phone',width:390,height:844}]){
  await page.setViewportSize({width:viewport.width,height:viewport.height});
  for(let stop=0;stop<13;stop++){
   await atStop(stop);
   check(`${viewport.name} stop ${stop}: energy tab only at model-reference stops`,await page.locator('#tab-energy').isVisible()===energyStops.includes(stop));
  }
  for(const stop of energyStops){
   await atStop(stop);
   const overview=await page.locator('#panel-overview').innerText(),headline=await page.locator('#headline').innerText(),source=await page.locator('#source').innerText(),url=page.url();
   // Follow the visible overview shortcut once, then use the fourth tab.
   if(stop===3)await page.locator('#show-energy').click();else await page.locator('#tab-energy').click();
   check(`${viewport.name} stop ${stop}: energy opens in main card`,await page.locator('#panel-energy').isVisible()&&await page.locator('#tab-energy').getAttribute('aria-selected')==='true'&&page.url()===url);
   const result=page.locator('#energy-result');
   const figures=await result.locator('.energy-figures strong').allTextContents();
   check(`${viewport.name} stop ${stop}: corrected capacity`,figures[0]==='4.37–4.57M'&&figures[1]==='26.19–27.40M');
   const resultText=await result.innerText();
   check(`${viewport.name} stop ${stop}: fixed power and target share`,resultText.includes('83.3 MW')&&resultText.includes('6.55–6.85%'));
   check(`${viewport.name} stop ${stop}: same workload is explicit`,resultText.includes('20 questions + 5 agent tasks per person daily'));
   check(`${viewport.name} stop ${stop}: capacity is not simultaneous conversations`,resultText.includes('not a count of simultaneous conversations'));
   await noOverflow(`${viewport.name} stop ${stop}: no horizontal overflow`);
   await page.locator('#panel-energy').evaluate(element=>element.scrollTop=0);
   await capture(`${viewport.name}-stop${stop}`);
   // Arrow, Home and End keys move within the card tablist, not the tour.
   await page.locator('#tab-energy').focus();await page.keyboard.press('ArrowRight');
   check(`${viewport.name} stop ${stop}: tab keyboard wraps to overview`,await page.locator('#panel-overview').isVisible()&&page.url()===url);
   check(`${viewport.name} stop ${stop}: overview is preserved`,await page.locator('#headline').innerText()===headline&&await page.locator('#source').innerText()===source&&await page.locator('#panel-overview').innerText()===overview);
   await page.keyboard.press('ArrowLeft');check(`${viewport.name} stop ${stop}: keyboard wraps back to energy`,await page.locator('#panel-energy').isVisible()&&page.url()===url);
   await page.keyboard.press('Home');await page.keyboard.press('End');
   check(`${viewport.name} stop ${stop}: tab Home/End remain local`,await page.locator('#panel-energy').isVisible()&&await page.locator('#tab-energy').evaluate(element=>element===document.activeElement)&&page.url()===url);
   // Tour navigation is still available while the energy explanation is open.
   await page.locator('#next').click();await settled();
   check(`${viewport.name} stop ${stop}: Next continues tour and restores overview`,await page.evaluate(stop=>SEED.state.index===(stop===12?0:stop+1)&&SEED.state.card===0,stop)&&await page.locator('#panel-overview').isVisible());
  }
  await atStop(3);await page.locator('#tab-energy').click();
  for(const detail of await page.locator('#panel-energy > details').all()){
   await detail.locator(':scope > summary').click();
   check(`${viewport.name}: expanded explanation is readable`,await detail.evaluate(element=>element.open));
   await noOverflow(`${viewport.name}: expanded explanation stays within card`);
  }
  await page.locator('#panel-energy .energy-calculation').scrollIntoViewIfNeeded();await capture(`${viewport.name}-calculation`);
  const text=await page.locator('#panel-energy').innerText();
  check(`${viewport.name}: formula and power-versus-energy boundary are included`,text.includes('8.6 output-equivalent tokens/s per user at peak')&&text.includes('1 MW for one hour uses 1 MWh')&&text.includes('Actual daily and annual electricity use needs an operating-load schedule'));
  check(`${viewport.name}: full campus capacity is distinct from demand`,text.includes('83.28 MW')&&text.includes('338 active pairs')&&text.includes('Llama 3.1 405B does not establish Claude Opus throughput'));
  await page.locator('#panel-energy').evaluate(element=>element.scrollTop=element.scrollHeight);
  await capture(`${viewport.name}-capacity`);
  await page.locator('#panel-energy > details').evaluateAll(elements=>elements.forEach(element=>element.open=false));
  report.viewports.push({name:viewport.name,...await noOverflow(`${viewport.name}: final card layout has no horizontal overflow`)});
 }
 for(const width of [1920,1366,390]){
  await page.setViewportSize({width,height:width===390?844:1080});await atStop(0);
  check(`${width}: requested workload assumption block removed from main card`,!await page.locator('#assumption').isVisible());
  await page.locator('#tab-why').click();
  check(`${width}: workload basis remains in supporting explanation`,(await page.locator('#choice-details').innerText()).includes('20 questions + 5 agent tasks'));
  await atStop(3);check(`${width}: equipment-specific assumption remains`,await page.locator('#assumption').isVisible());
 }
 await atStop(11);await page.setViewportSize({width:1920,height:1080});
 const budgetTitle=await page.locator('#headline').innerText();
 await page.locator('#toggle-clean').click();check('Clean view still hides revised cards',await page.locator('#story').evaluate(el=>getComputedStyle(el).visibility==='hidden'||getComputedStyle(el).display==='none'));
 await page.keyboard.press('Escape');check('Escape restores the revised budget card',await page.locator('#headline').innerText()===budgetTitle&&await page.locator('#story').isVisible());
 check('No new tabs or external navigation',context.pages().length===1&&page.url().startsWith('http://127.0.0.1:4173/'));
 check('No browser errors',report.errors.length===0);check('No failed local assets',report.network.length===0);report.passed=true;
}catch(error){report.failure=String(error);console.error(error);await capture('failure');}
finally{fs.writeFileSync('qa/model-energy-report.json',JSON.stringify(report,null,2));await browser.close();console.log(JSON.stringify({passed:report.passed,checks:report.checks.length,failure:report.failure,screenshots:report.screenshots.length}));if(!report.passed)process.exitCode=1;}
