"""Verify script 15's --live/--llm code paths against local stand-in services (no internet needed).

Usage (from the project root, after scripts 02-07 have produced data/processed and outputs/models):
    python tests/test_live_paths.py
Each scenario runs in its own temporary run directory, so real outputs are never touched.
"""
import json, os, shutil, subprocess, sys, tempfile, threading, time
from http.server import HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from fixture_server import H  # noqa: E402

PORT = 8765
F = f'http://127.0.0.1:{PORT}'
SCRIPT = ROOT / 'scripts' / '15_agrisight_four_agent_pipeline.py'

SCENARIOS = [
    ('S1 live + faithful local model', ['--live', '--llm'],
     {'AGRI_WEATHER_URL': f'{F}/forecast', 'AGRI_PIB_RSS': f'{F}/rss', 'AGRI_OLLAMA_URL': f'{F}/faithful/api/generate'},
     lambda j: j['weather_status'] == 'ok' and j['news_status'].startswith('ok: 2') and j['llm_status'] == 'local_model_used_numbers_verified'),
    ('S2 local model changes a price', ['--live', '--llm'],
     {'AGRI_WEATHER_URL': f'{F}/forecast', 'AGRI_PIB_RSS': f'{F}/rss', 'AGRI_OLLAMA_URL': f'{F}/hallucinate/api/generate'},
     lambda j: j['llm_status'].startswith('local_model_rejected_numbers_changed') and '2950' in j['llm_check']['unexpected']),
    ('S3 non-local LLM endpoint', ['--llm'], {'AGRI_OLLAMA_URL': 'https://api.example.com/api/generate'},
     lambda j: j['llm_status'].startswith('refused_non_local_endpoint')),
    ('S4 all services down', ['--live', '--llm'],
     {'AGRI_WEATHER_URL': 'http://127.0.0.1:9/f', 'AGRI_PIB_RSS': 'http://127.0.0.1:9/r', 'AGRI_OLLAMA_URL': 'http://127.0.0.1:9/api/generate'},
     lambda j: j['weather_status'].startswith('failed') and j['news_status'].startswith('failed') and len(j['forecasts']) == 8),
]


def main():
    srv = HTTPServer(('127.0.0.1', PORT), H); threading.Thread(target=srv.serve_forever, daemon=True).start(); time.sleep(.3)
    models = ROOT / 'outputs' / 'models'
    if not (models / 'ml_results.pkl').exists():
        sys.exit('outputs/models/ml_results.pkl not found: run scripts 02-07 first.')
    failures = 0
    for name, args, env, check in SCENARIOS:
        run_dir = Path(tempfile.mkdtemp(prefix='agrisight_'))
        shutil.copytree(models, run_dir / 'models')
        e = {**os.environ, 'AGRISIGHT_RUN_DIR': str(run_dir), **env}
        p = subprocess.run([sys.executable, str(SCRIPT), *args], env=e, capture_output=True, text=True, cwd=ROOT)
        try:
            j = json.loads((run_dir / 'objective_completion_pipeline' / 'agrisight_pipeline.json').read_text(encoding='utf-8'))
            ok = p.returncode == 0 and check(j)
        except Exception as exc:
            ok, j = False, {'error': str(exc), 'stderr': p.stderr[-400:]}
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}  ->  weather={j.get('weather_status')}; news={j.get('news_status')}; llm={str(j.get('llm_status'))[:70]}")
        shutil.rmtree(run_dir, ignore_errors=True)
    srv.shutdown()
    print(f'\n{len(SCENARIOS) - failures}/{len(SCENARIOS)} scenarios passed')
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
