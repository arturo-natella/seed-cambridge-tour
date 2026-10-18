import {spawnSync} from 'node:child_process';import path from 'node:path';import {fileURLToPath} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const blender=process.env.BLENDER_BIN||'/Applications/Blender.app/Contents/MacOS/Blender';
const result=spawnSync(blender,['--background','--python-exit-code','1','--python',path.join(root,'blender/build_scene.py')],{cwd:root,stdio:'inherit'});process.exit(result.status??1);
