import {cp, mkdir, readdir, rm} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';

const root = fileURLToPath(new URL('../', import.meta.url));
const output = path.join(root, 'dist');
await rm(output, {recursive: true, force: true});
await mkdir(output, {recursive: true});
// Publish only the static runtime and still gallery. The Blender master,
// authoring scripts, test reports and local project settings stay out of dist.
for (const item of ['index.html', 'src', 'vendor', 'stills']) {
  await cp(path.join(root, item), path.join(output, item), {
    recursive: true,
    filter: source => path.basename(source) !== '.DS_Store',
  });
}
await mkdir(path.join(output, 'assets'));
for (const item of ['campus.glb', 'content.json', 'top-model-sizing.json', 'amaru-logo.svg']) {
  await cp(path.join(root, 'assets', item), path.join(output, 'assets', item));
}
console.log(`Built static tour in dist/ (${(await readdir(output)).join(', ')}).`);
