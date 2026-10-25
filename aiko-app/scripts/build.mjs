import { spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, rmSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const projectRoot = fileURLToPath(new URL('..', import.meta.url));
const tempBase = join(projectRoot, 'node_modules', '.cache');
mkdirSync(tempBase, { recursive: true });

// Keep esbuild's short-lived files away from Windows' shared Temp directory,
// where scanners and other apps can lock files during cleanup.
const buildTemp = mkdtempSync(join(tempBase, 'aiko-build-'));
const env = {
  ...process.env,
  TEMP: buildTemp,
  TMP: buildTemp,
  TMPDIR: buildTemp,
};

const commands = [
  [resolve(projectRoot, 'node_modules/typescript/bin/tsc'), []],
  [resolve(projectRoot, 'node_modules/vite/bin/vite.js'), ['build']],
];

let exitCode = 0;
try {
  for (const [script, args] of commands) {
    const result = spawnSync(process.execPath, [script, ...args], {
      cwd: projectRoot,
      env,
      stdio: 'inherit',
    });

    if (result.error) throw result.error;
    if (result.status !== 0) {
      exitCode = result.status ?? 1;
      break;
    }
  }
} catch (error) {
  console.error('[build] Failed to start the production build:', error);
  exitCode = 1;
} finally {
  try {
    rmSync(buildTemp, { recursive: true, force: true });
  } catch (error) {
    console.warn('[build] Could not remove the isolated temporary folder:', error);
  }
}

process.exitCode = exitCode;
