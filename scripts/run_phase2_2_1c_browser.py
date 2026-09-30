#!/usr/bin/env python3
"""Serve the repository only on loopback while collecting real browser evidence."""
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    env = os.environ.copy()
    modules = env.get('CODEX_PRIMARY_RUNTIME_NODE_MODULES')
    if modules:
        env.setdefault('P221B_PLAYWRIGHT_MODULE', str(Path(modules) / 'playwright'))
    env.setdefault('P221B_CHROMIUM', '/tmp/chromium')
    server = subprocess.Popen([sys.executable, '-m', 'http.server', '8765', '--bind', '127.0.0.1'],
                              cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try:
                with urllib.request.urlopen('http://127.0.0.1:8765/data/phase2_2_1c/profiles.json', timeout=1):
                    break
            except OSError:
                if server.poll() is not None:
                    raise RuntimeError('Loopback server failed; do not collect evidence against another server')
                time.sleep(.1)
        else:
            raise RuntimeError('Loopback server did not become ready')
        return subprocess.call(['node', 'scripts/render_phase2_2_1c.cjs'], cwd=ROOT, env=env)
    finally:
        server.terminate()
        server.wait(timeout=5)


if __name__ == '__main__':
    sys.exit(main())
