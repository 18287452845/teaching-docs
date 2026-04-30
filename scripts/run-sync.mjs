import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const siteRoot = path.resolve(scriptDir, '..');
const syncScript = path.join(siteRoot, 'sync.py');
const extraArgs = process.argv.slice(2);

const candidates =
  process.platform === 'win32'
    ? [
        ['py', ['-3', syncScript, ...extraArgs]],
        ['python', [syncScript, ...extraArgs]],
      ]
    : [
        ['python3', [syncScript, ...extraArgs]],
        ['python', [syncScript, ...extraArgs]],
      ];

for (const [command, args] of candidates) {
  const result = spawnSync(command, args, {
    cwd: siteRoot,
    stdio: 'inherit',
  });

  if (result.error && result.error.code === 'ENOENT') {
    continue;
  }

  process.exit(result.status ?? 1);
}

console.error('Unable to find a Python runtime to run sync.py.');
process.exit(1);
