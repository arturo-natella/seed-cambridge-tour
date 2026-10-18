import {chromium} from 'playwright';
import {writeFile} from 'node:fs/promises';
import assert from 'node:assert/strict';
const browser=await chromium.launch({channel:'chrome',headless:true});
const page=await browser.newPage();const report={errors:[],views:[]};page.on('pageerror',e=>report.errors.push(String(e)));
await page.goto('http://127.0.0.1:4173/#stop-3');await page.waitForFunction(()=>window.SEED?.ready);
async function settled(){await page.waitForFunction(()=>!SEED.state.flying&&!document.querySelector('#story').classList.contains('pending'));await page.waitForTimeout(700);}
for(const [name,width,height] of [['desktop',1920,1080],['laptop',1366,768],['phone',390,844]]){
 await page.setViewportSize({width,height});
 for(const view of ['hall','power','boreholes','surface']){
  if(view==='surface')await page.evaluate(()=>SEED.goTo(2,true));
  if(view==='hall')await page.evaluate(()=>SEED.goTo(3,true));
  if(view==='power')await page.locator('#trace-power').click();
  if(view==='boreholes'){if(width<851)await page.locator('#tab-overview').click();await page.locator('#show-boreholes').click();}
  await settled();
  await page.screenshot({path:`qa/clarity-${name}-${view}.png`});
  report.views.push(await page.evaluate(({name,view})=>({name,view,index:SEED.state.index,xray:SEED.state.xray,ground:SEED.state.ground,powerFocus:SEED.state.powerFocus,labels:[...document.querySelectorAll('.clarity-label')].filter(e=>!e.hidden).map(e=>({text:e.textContent,rect:e.getBoundingClientRect().toJSON()})),keyVisible:!document.querySelector('#scene-key').hidden&&getComputedStyle(document.querySelector('#scene-key')).display!=='none',groups:['boreholes','boreholeFocus','groundHeaders','boreholeSurface'].map(k=>({key:k,exists:!!SEED.groups[k],visible:SEED.groups[k]?.visible})),overflow:document.documentElement.scrollWidth>innerWidth}),{name,view}));
 }
}
for(const view of report.views){assert.equal(view.overflow,false,`${view.name}/${view.view}: page overflow`);if(['desktop','laptop'].includes(view.name)&&view.view==='power')assert.equal(view.labels.length,4,`${view.name}: all power route labels visible`);if(view.view==='boreholes')assert.equal(view.ground,true);}
assert.deepEqual(report.errors,[]);report.passed=true;
await writeFile('qa/rendering-clarity.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));await browser.close();
