import {chromium} from 'playwright';
import fs from 'node:fs';
import assert from 'node:assert/strict';

// Acceptance values for the user-approved whole-facility baseline. Independently
// cross-check the raw benchmark and unit conversion, rather than reading UI data.
const expected={
 heavy:{low:1459,high:1526,served:'6.6–6.9%',power:'7.3–7.6 GW',users:'26–27M'},
 fast:{low:45,high:50,served:'100%',power:'224–251 MW',users:'400M'},
 mixed20:{low:52,high:60,served:'100%',power:'262–301 MW',users:'400M'},
 mixed50:{low:64,high:75,served:'100%',power:'319–375 MW',users:'400M'},
 premium:{low:167,high:182,served:'55.0–59.7%',power:'837–909 MW',users:'220–239M'}
};
const calculated=JSON.parse(fs.readFileSync('assets/top-model-sizing.json','utf8'));
const rawHeavy=[271,259];
for(let i=0;i<2;i++){
 const effective=rawHeavy[i]*(1+9400/(680*10));
 const rackOutput=effective*72*2.5;
 const peakWork=400e6*(4.6+40/10);
 const requiredRacks=peakWork/rackOutput;
 const watts=requiredRacks*224000*1.1;
 const actual=calculated.scenarios.heavy[i];
 assert.ok(Math.abs(actual.racks-requiredRacks)<1e-6,'Heavy rack count agrees with raw MLPerf workload adjustment');
 assert.ok(Math.abs(actual.siteMW-watts/1e6)<1e-6,'Support and facility overhead counted exactly once');
 assert.ok(Math.abs(actual.annualTWhAtFullLoad-watts*8760/1e12)<1e-6,'Annual energy converts watts and hours correctly');
 assert.ok(Math.abs(actual.computeRackPurchaseB-requiredRacks*7.8/1000)<1e-6,'Rack purchase excludes a fabricated total budget');
 assert.ok(Math.abs(actual.servedUsers-400e6*500e6/watts)<1e-6,'Served users and power demand use the same capacity basis');
}
assert.equal(calculated.wholeRacksWithin500MW,2029);
const content=JSON.parse(fs.readFileSync('assets/content.json','utf8'));
assert.equal(content.modelEnergy.defaultScenario,'heavy');
assert.equal(content.bubbles[0].unit,'people targeted · capacity still falls short');
assert.equal(content.bubbles[1].number,'52,000–55,000');
assert.equal(content.bubbles[10].number,'26–27 million');
assert.equal(content.bubbles[11].number,'$231–242B');
assert.ok(content.bubbles[11].unit.includes('not a five-year total'));
assert.ok(!JSON.stringify(content.bubbles).includes('All 400 million served, inside the budget'));
assert.ok(content.design.memory.html.includes('not validated storage figures'));
const energyStops=[0,3,8,10,11,12];
const report={passed:false,checks:[],screenshots:[],errors:[],network:[],viewports:[],reference:'Raw heavy-reference benchmark, explicit workload and whole-facility power identities; user-approved top-model baseline'};
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
 check('Top-model scenario is selected on first load',await page.locator('#energy-scenario').inputValue()==='heavy');
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
   check(`${viewport.name} stop ${stop}: scenario selector has five choices`,await page.locator('#energy-scenario option').count()===5);
   const resultTexts=[];
   for(const [id,reference] of Object.entries(expected)){
    await page.locator('#energy-scenario').selectOption(id);
    const result=page.locator('#energy-result');
    const figures=await result.locator('.energy-figures strong').allTextContents();
    check(`${viewport.name} stop ${stop} ${id}: capacity and served demand match analysis`,figures[0]===reference.power&&figures[1]===reference.users&&(await result.innerText()).includes(reference.served));
    check(`${viewport.name} stop ${stop} ${id}: selection preserves stop and card`,page.url()===url&&await page.evaluate(stop=>SEED.state.index===stop&&SEED.state.card===3,stop));
    check(`${viewport.name} stop ${stop} ${id}: changed capacity figures are visible in the reading area`,await result.locator('.energy-figures').evaluate(element=>{
     const figures=element.getBoundingClientRect(),panel=document.querySelector('#panel-energy').getBoundingClientRect();
     return figures.top>=panel.top-1&&figures.bottom<=panel.bottom+1;
    }));
    check(`${viewport.name} stop ${stop} ${id}: total power includes support and cooling`,(await result.innerText()).includes('networking and storage support, and cooling')&&!(await result.innerText()).includes('Networking is additional'));
    const bar=await result.locator('.energy-meter').evaluate(element=>({width:element.clientWidth,fill:element.querySelector('span').getBoundingClientRect().width,range:element.querySelector('i').getBoundingClientRect().width,over:element.classList.contains('over-cap')}));
    check(`${viewport.name} stop ${stop} ${id}: meter remains bounded and identifies overload`,bar.fill<=bar.width+.5&&bar.fill+bar.range<=bar.width+.5&&bar.over===(reference.high>100));
    resultTexts.push(await result.innerText());
    await noOverflow(`${viewport.name} stop ${stop} ${id}: no horizontal overflow`);
   }
   check(`${viewport.name} stop ${stop}: all scenario choices produce distinct explanations`,new Set(resultTexts).size===5);
   await page.locator('#energy-scenario').selectOption('heavy');
   await page.locator('#panel-energy').evaluate(element=>element.scrollTop=0);
   await capture(`${viewport.name}-stop${stop}`);
   // Arrow, Home and End keys move within the card tablist, not the tour.
   await page.locator('#tab-energy').focus();await page.keyboard.press('ArrowRight');
   check(`${viewport.name} stop ${stop}: tab keyboard wraps to overview`,await page.locator('#panel-overview').isVisible()&&page.url()===url);
   check(`${viewport.name} stop ${stop}: overview is preserved`,await page.locator('#headline').innerText()===headline&&await page.locator('#source').innerText()===source&&await page.locator('#panel-overview').innerText()===overview);
   await page.keyboard.press('ArrowLeft');check(`${viewport.name} stop ${stop}: keyboard wraps back to energy`,await page.locator('#panel-energy').isVisible()&&page.url()===url);
   await page.keyboard.press('Home');await page.keyboard.press('End');
   check(`${viewport.name} stop ${stop}: tab Home/End remain local`,await page.locator('#panel-energy').isVisible()&&await page.locator('#tab-energy').evaluate(element=>element===document.activeElement)&&page.url()===url);
   await page.locator('#energy-scenario').selectOption('fast');await page.locator('#energy-scenario').focus();
   // Native macOS headless menus do not commit ArrowDown; typeahead exercises
   // a real keyboard selection without depending on the operating-system popup.
   await page.keyboard.press('2');await page.keyboard.press('Enter');
   check(`${viewport.name} stop ${stop}: native selector keyboard changes scenario without navigating`,await page.locator('#energy-scenario').inputValue()==='mixed20'&&page.url()===url&&(await page.locator('.energy-figures strong').first().innerText())==='262–301 MW');
   // Tour navigation is still available while the energy explanation is open.
   await page.locator('#next').click();await settled();
   check(`${viewport.name} stop ${stop}: Next continues tour and restores overview`,await page.evaluate(stop=>SEED.state.index===(stop===12?0:stop+1)&&SEED.state.card===0,stop)&&await page.locator('#panel-overview').isVisible());
  }
  await atStop(3);await page.locator('#tab-energy').click();await page.locator('#energy-scenario').selectOption('fast');
  for(const detail of await page.locator('#panel-energy > details').all()){
   await detail.locator(':scope > summary').click();
   check(`${viewport.name}: expanded explanation is readable`,await detail.evaluate(element=>element.open));
   await noOverflow(`${viewport.name}: expanded explanation stays within card`);
  }
  await page.locator('#panel-energy .energy-calculation').scrollIntoViewIfNeeded();await capture(`${viewport.name}-calculation`);
  const text=await page.locator('#panel-energy').innerText();
  check(`${viewport.name}: formula and power-versus-energy boundary are included`,text.includes('3.44 billion output-equivalent tokens/second')&&text.includes('1 MW for one hour uses 1 MWh')&&text.includes('Annual electricity use also needs a workload schedule'));
  check(`${viewport.name}: full campus capacity is distinct from demand`,text.includes('~83 MW')&&text.includes('75 MW for computers and networking')&&text.includes('Actual demand depends on workload and utilization'));
  await page.locator('#panel-energy').evaluate(element=>element.scrollTop=element.scrollHeight);
  await capture(`${viewport.name}-capacity`);
  await page.locator('#panel-energy > details').evaluateAll(elements=>elements.forEach(element=>element.open=false));
  report.viewports.push({name:viewport.name,...await noOverflow(`${viewport.name}: final card layout has no horizontal overflow`)});
 }
 await atStop(11);await page.setViewportSize({width:1920,height:1080});
 const budgetTitle=await page.locator('#headline').innerText();
 await page.locator('#toggle-clean').click();check('Clean view still hides revised cards',await page.locator('#story').evaluate(el=>getComputedStyle(el).visibility==='hidden'||getComputedStyle(el).display==='none'));
 await page.keyboard.press('Escape');check('Escape restores the revised budget card',await page.locator('#headline').innerText()===budgetTitle&&await page.locator('#story').isVisible());
 check('No new tabs or external navigation',context.pages().length===1&&page.url().startsWith('http://127.0.0.1:4173/'));
 check('No browser errors',report.errors.length===0);check('No failed local assets',report.network.length===0);report.passed=true;
}catch(error){report.failure=String(error);console.error(error);await capture('failure');}
finally{fs.writeFileSync('qa/model-energy-report.json',JSON.stringify(report,null,2));await browser.close();console.log(JSON.stringify({passed:report.passed,checks:report.checks.length,failure:report.failure,screenshots:report.screenshots.length}));if(!report.passed)process.exitCode=1;}
