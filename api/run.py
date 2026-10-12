"""Start the isolated local site and reuse the project's existing Ollama models."""
import os
import socket
import subprocess
import sys
import time
import signal
from pathlib import Path

import uvicorn
from api.model_provider import CONFIG

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[1]
HOST = os.environ.get('MOA_HOST', '127.0.0.1')

def listening(port):
    with socket.socket() as sock:
        sock.settimeout(1)
        return sock.connect_ex(('127.0.0.1',port)) == 0

if __name__ == '__main__':
    os.chdir(ROOT)
    runtime = ROOT/'.runtime'
    runtime.mkdir(exist_ok=True)
    pid_file = runtime / 'server.pid'
    if '--restart' in sys.argv and listening(8787):
        try:
            pid = int(pid_file.read_text().strip())
            args = subprocess.check_output(['ps', '-p', str(pid), '-o', 'args='], text=True).strip()
        except (OSError, ValueError, subprocess.CalledProcessError):
            raise SystemExit('실행 중인 모아의 PID를 확인하지 못했어요. 기존 서버를 종료한 뒤 다시 실행해 주세요.')
        if str(ROOT / '.venv/bin/python') not in args or '-m api.run' not in args:
            raise SystemExit('다른 프로세스는 종료하지 않았어요. 기존 모아 서버를 직접 종료해 주세요.')
        os.kill(pid, signal.SIGTERM)
        for _ in range(50):
            if not listening(8787): break
            time.sleep(0.1)
        else: raise SystemExit('기존 서버가 아직 종료되지 않았어요. 잠시 후 다시 실행해 주세요.')
    if CONFIG.provider == 'ollama' and CONFIG.ollama_url == 'http://127.0.0.1:11434' and not listening(11434):
        binary = WORKSPACE/'.tools/ollama/ollama'
        if not binary.is_file():
            raise SystemExit('먼저 MyLLM의 Ollama 실행 환경을 준비해 주세요.')
        env={**os.environ,'OLLAMA_MODELS':str(WORKSPACE/'.cache/ollama'),'OLLAMA_HOST':'127.0.0.1:11434'}
        with (runtime/'ollama.log').open('a') as log:
            subprocess.Popen([str(binary),'serve'],env=env,stdout=log,stderr=log,start_new_session=True)
    if listening(8787):
        print('모아가 이미 열려 있어요: http://127.0.0.1:8787 · 설정을 바꿨다면 Restart Moa.command를 실행해 주세요.')
    else:
        print('모아: http://127.0.0.1:8787 · 수신 주소: ' + HOST + ':8787 · 모델 연결: ' + CONFIG.provider + ' / ' + CONFIG.model)
        pid_file.write_text(str(os.getpid()))
        try:
            uvicorn.run('api.server:app',host=HOST,port=8787,log_level='warning')
        finally:
            if pid_file.is_file() and pid_file.read_text().strip() == str(os.getpid()): pid_file.unlink()
