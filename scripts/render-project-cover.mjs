import fs from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {fileURLToPath} from 'node:url';
import {chromium} from 'playwright';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const fonts=process.env.SEED_FONT_DIR||path.join(os.homedir(),'Library/Fonts');
const data=async(file,type)=>`data:${type};base64,${(await fs.readFile(file)).toString('base64')}`;
let html=await fs.readFile(path.join(root,'scripts/sundai-cover.html'),'utf8');
for(const [tag,file,type] of [
 ['__FONT_REGULAR__',path.join(fonts,'Inter_24pt-Regular.ttf'),'font/ttf'],
 ['__FONT_BOLD__',path.join(fonts,'Inter_28pt-Bold.ttf'),'font/ttf'],
 ['__CAMPUS__',path.join(root,'stills/Sundai-campus.png'),'image/png'],
 ['__AMARU__',path.join(root,'assets/amaru-logo.svg'),'image/svg+xml']])html=html.replace(tag,await data(file,type));
const browser=await chromium.launch({channel:'chrome',headless:true});
try{
 const page=await browser.newPage({viewport:{width:2000,height:1125},deviceScaleFactor:1});
 await page.setContent(html,{waitUntil:'load'});await page.evaluate(()=>document.fonts.ready);
 await page.locator('img').evaluateAll(images=>Promise.all(images.map(i=>i.decode())));
 const qa=await page.evaluate(()=>({fonts:document.fonts.check('700 168px Inter'),overflow:document.documentElement.scrollWidth>innerWidth,images:[...document.images].every(i=>i.complete&&i.naturalWidth>0),width:innerWidth,height:innerHeight}));
 if(!qa.fonts||qa.overflow||!qa.images)throw new Error(JSON.stringify(qa));
 await page.screenshot({path:path.join(root,'stills/Sundai-project.png')});
 await page.screenshot({path:path.join(root,'stills/Sundai-project.jpg'),type:'jpeg',quality:94});
 await fs.writeFile(path.join(root,'qa/sundai-project-cover.json'),JSON.stringify({passed:true,...qa,source:'Existing Blender master rendered with blender/render_project_cover.py; Inter and approved Amaru SVG composed without changing geometry',files:['stills/Sundai-project.png','stills/Sundai-project.jpg']},null,2)+'\n');
 console.log(JSON.stringify({passed:true,...qa}));
}finally{await browser.close()}
