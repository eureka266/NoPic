#!/usr/bin/env python3
"""Start or reuse the local NoPic workbench and print a JSON launch receipt."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
WORKBENCH = ROOT / 'output/prototypes/cover-workbench'
WORKSPACE = WORKBENCH / 'workspace'
PID_FILE = WORKSPACE / 'workbench.pid'
LOG_FILE = WORKSPACE / 'workbench.log'


def process_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, PermissionError):
        return False
    return True


def read_pid() -> int | None:
    try:
        pid = int(PID_FILE.read_text().strip())
    except (FileNotFoundError, ValueError):
        return None
    return pid if process_is_alive(pid) else None


def workbench_http_ok(url: str) -> bool:
    try:
        with urlopen(url + '/api/state', timeout=1) as response:
            return response.status == 200
    except (OSError, URLError):
        return False


def port_is_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((host, port)) == 0


def wait_until_ready(url: str, process: subprocess.Popen[str]) -> None:
    deadline = time.monotonic() + 6
    while time.monotonic() < deadline:
        if workbench_http_ok(url):
            return
        if process.poll() is not None:
            raise RuntimeError(f'工作台启动失败，进程退出码为 {process.returncode}；请查看 {LOG_FILE}')
        time.sleep(0.1)
    raise RuntimeError(f'工作台启动超时；请查看 {LOG_FILE}')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=59054)
    args = parser.parse_args()

    if not WORKBENCH.is_dir() or not (WORKBENCH / 'server.py').is_file():
        raise RuntimeError(f'找不到工作台目录：{WORKBENCH}')
    WORKSPACE.mkdir(parents=True, exist_ok=True)

    url = f'http://127.0.0.1:{args.port}'
    pid = read_pid()
    if workbench_http_ok(url):
        receipt = {'url': url + '/', 'port': args.port, 'pid': pid, 'reused': True}
        print(json.dumps(receipt, ensure_ascii=False))
        return 0
    if port_is_open('127.0.0.1', args.port):
        raise RuntimeError(f'端口 {args.port} 已被其他服务占用，未覆盖现有进程')

    python = WORKBENCH / '.venv/bin/python'
    if not python.is_file():
        python = Path(sys.executable)
    log = LOG_FILE.open('a', encoding='utf-8')
    process = subprocess.Popen(
        [str(python), 'server.py', str(args.port)],
        cwd=WORKBENCH,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        text=True,
    )
    PID_FILE.write_text(str(process.pid) + '\n', encoding='utf-8')
    try:
        wait_until_ready(url, process)
    except Exception:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except OSError:
            pass
        raise
    receipt = {'url': url + '/', 'port': args.port, 'pid': process.pid, 'reused': False}
    print(json.dumps(receipt, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
