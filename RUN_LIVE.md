# Running AgriSight script 15 live (weather + PIB news + local LLM)

The live run needs internet access and a local Ollama model. Neither is available in the
analysis sandbox, so this run is done on your own PC. Total time: about 20–30 minutes,
mostly the one-time model download.

## 1. Install Ollama and a model (one time)

1. Download and install **Ollama for Windows** from https://ollama.com/download.
2. Open PowerShell and pull a model:
   ```powershell
   ollama pull llama3.1        # about 4.9 GB, recommended
   # or, on a laptop with less memory:
   ollama pull llama3.2        # about 2 GB; then set $env:AGRI_OLLAMA_MODEL="llama3.2"
   ```
3. Check that it is running: `ollama list` should show the model, and
   `curl http://127.0.0.1:11434` should reply "Ollama is running".

## 2. Confirm the code paths work on your machine (no internet needed)

From the project root, with the virtual environment active:
```powershell
python tests\test_live_paths.py
```
Expected: `4/4 scenarios passed`. This uses local stand-in services, so a failure here
means a setup problem, not a network problem.

## 3. The real live run

```powershell
python scripts\15_agrisight_four_agent_pipeline.py --live --llm
```
The last line reports the status of each component, for example:
```
Wrote 8 commodity forecasts; weather=ok; news=ok: 3 relevant of 20 items; LLM=local_model_used_numbers_verified; live=True
```

| Status you see | Meaning | What to do |
|---|---|---|
| `weather=ok` | Open-Meteo 7-day Chennai forecast retrieved | — |
| `news=ok: N relevant of M items` | PIB feed parsed; N matched agriculture/price keywords | N = 0 is valid if no relevant releases that day |
| `news=failed: HTTP Error 403` or `ParseError` | PIB blocked the request or changed its feed format | Note it; the rest of the brief is still valid |
| `LLM=local_model_used_numbers_verified` | Local model rewrote the brief; every price, forecast and weather number checked | — |
| `LLM=local_model_rejected_numbers_changed` | Model altered or invented a number; safe template used instead | Try `llama3.1` if you used a smaller model; the rejection itself is a valid result to report |
| `LLM=local_model_unavailable...` | Ollama not running | Start Ollama and rerun |

Every signal will still read `ABSTAIN_STALE_DATA`. This is the freshness gate working
correctly, because the statewide prices end on 20 April 2026. Live weather and news do not
refresh the prices.

## 4. Send back for the report

Please share these two files:
- `outputs\objective_completion_pipeline\agrisight_brief.md`
- `outputs\objective_completion_pipeline\agrisight_pipeline.json`

They will be used to replace the stand-in results in Section 4.12.2 of the report with the
real run, including the date, model name, number of news items and verification result.
