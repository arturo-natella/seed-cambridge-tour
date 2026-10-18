import {spawnSync} from 'node:child_process';import path from 'node:path';import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');const blender=process.env.BLENDER_BIN||'/Applications/Blender.app/Contents/MacOS/Blender';
const requested=process.argv.slice(2);const shots=requested.length?requested:['S1','S2','S3-detail','S3','S4','Power-detail','Freeze-detail','Cooler-detail','Drain-detail','FreshAir-detail'];
for(const shot of shots){const result=spawnSync(blender,['--background','--python-exit-code','1',path.join(root,'blender/SEED-Cambridge.blend'),'--python',path.join(root,'blender/render_stills.py'),'--',shot],{cwd:root,stdio:'inherit'});if(result.status!==0)process.exit(result.status??1);}
