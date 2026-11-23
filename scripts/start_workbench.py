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
from install_brand_pack import validate_manifest, pack_fingerprint


ROOT = Path(__file__).resolve().parents[1]
WORKBENCH = ROOT / 'output/prototypes/cover-workbench'


def discover_project_root() -> Path:
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            cwd=Path.cwd(), capture_output=True, text=True, check=True,
        )
        return Path(result.stdout.strip()).resolve()
    except (OSError, subprocess.CalledProcessError):
        return Path.cwd().resolve()


def active_brand_pack(project_root: Path) -> Path | None:
    config = project_root / '.nopic/active-brand-pack.json'
    if not config.is_file():
        return None
    try:
        data = json.loads(config.read_text(encoding='utf-8'))
        pack_root = Path(data['pack_root']).expanduser().resolve()
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise RuntimeError(f'无法读取激活的品牌包配置：{config} ({error})') from error
    if not (pack_root / 'manifest.json').is_file():
        raise RuntimeError(f'激活的品牌包不存在或缺少 manifest.json：{pack_root}')
    return pack_root


def process_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, PermissionError):
        return False
    return True


def workbench_http_ok(url: str) -> bool:
    try:
        with urlopen(url + '/api/state', timeout=1) as response:
            return response.status == 200
    except (OSError, URLError):
        return False


def workbench_state(url: str) -> dict | None:
    try:
        with urlopen(url + '/api/state', timeout=1) as response:
            if response.status != 200:
                return None
            return json.loads(response.read())
    except (OSError, URLError, json.JSONDecodeError):
        return None


def port_is_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((host, port)) == 0


def wait_until_ready(url: str, process: subprocess.Popen[str], log_file: Path) -> None:
    deadline = time.monotonic() + 6
    while time.monotonic() < deadline:
        if workbench_http_ok(url):
            return
        if process.poll() is not None:
            raise RuntimeError(f'工作台启动失败，进程退出码为 {process.returncode}；请查看 {LOG_FILE}')
        time.sleep(0.1)
    raise RuntimeError(f'工作台启动超时；请查看 {log_file}')


def stop_process(pid: int) -> None:
    try:
        os.killpg(pid, signal.SIGTERM)
    except OSError:
        return
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline and process_is_alive(pid):
        time.sleep(0.1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=59054)
    parser.add_argument('--project-root')
    args = parser.parse_args()

    project = Path(args.project_root).expanduser().resolve() if args.project_root else discover_project_root()
    pack = active_brand_pack(project)
    workspace = project / '.nopic/workspace'
    pid_file = workspace / 'workbench.pid'
    log_file = workspace / 'workbench.log'

    if not WORKBENCH.is_dir() or not (WORKBENCH / 'server.py').is_file():
        raise RuntimeError(f'找不到工作台目录：{WORKBENCH}')
    workspace.mkdir(parents=True, exist_ok=True)

    url = f'http://127.0.0.1:{args.port}'
    pid = None
    try:
        pid = int(pid_file.read_text().strip())
        if not process_is_alive(pid):
            pid = None
    except (FileNotFoundError, ValueError):
        pass
    existing = workbench_state(url)
    expected_pack = None
    if pack:
        manifest = validate_manifest(pack)
        expected_pack = (manifest.get('id'), manifest.get('version'), str(pack.resolve()), pack_fingerprint(pack, manifest))
    actual_pack = ((existing or {}).get('brand_pack') or {})
    actual_identity = (actual_pack.get('id'), actual_pack.get('version'), actual_pack.get('root'), actual_pack.get('content_fingerprint')) if actual_pack.get('id') else None
    pack_matches = actual_identity == expected_pack
    project_matches = bool(existing and Path(existing.get('workspace', '')).resolve() == workspace.resolve())
    if existing and pack_matches and project_matches:
        receipt = {'url': url + '/', 'port': args.port, 'pid': pid, 'reused': True,
                   'project_root': str(project), 'brand_pack': str(pack) if pack else None}
        print(json.dumps(receipt, ensure_ascii=False))
        return 0
    if existing and pid and project_matches:
        stop_process(pid)
    if port_is_open('127.0.0.1', args.port):
        raise RuntimeError(f'端口 {args.port} 已被其他服务占用，未覆盖现有进程')

    python = WORKBENCH / '.venv/bin/python'
    if not python.is_file():
        python = Path(sys.executable)
    log = log_file.open('a', encoding='utf-8')
    command = [str(python), 'server.py', str(args.port), '--project-root', str(project)]
    if pack:
        command.extend(['--brand-pack', str(pack)])
    process = subprocess.Popen(
        command,
        cwd=WORKBENCH,
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        text=True,
    )
    pid_file.write_text(str(process.pid) + '\n', encoding='utf-8')
    try:
        wait_until_ready(url, process, log_file)
    except Exception:
        try:
            stop_process(process.pid)
        except OSError:
            pass
        raise
    receipt = {'url': url + '/', 'port': args.port, 'pid': process.pid, 'reused': False,
               'project_root': str(project), 'brand_pack': str(pack) if pack else None}
    print(json.dumps(receipt, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(1)
