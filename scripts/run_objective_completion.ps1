$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = 'C:\Users\Freeware Sys\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$env:AGRISIGHT_RUN_DIR = Join-Path $projectRoot 'outputs\objective_completion_run_20261016'
$steps = @(
  '04_feature_engineering.py',
  '05_sarima_baseline.py',
  '06_prophet_model.py',
  '07_ml_models.py',
  '08_shap_analysis.py',
  '15_agrisight_four_agent_pipeline.py'
)
foreach ($step in $steps) {
  Write-Host "Running $step"
  & $python (Join-Path $PSScriptRoot $step)
  if ($LASTEXITCODE -ne 0) { throw "$step failed with exit code $LASTEXITCODE" }
}
Write-Host "Running matched objective evaluation"
& $python (Join-Path $PSScriptRoot '14_proposal_objective_evaluation.py')
if ($LASTEXITCODE -ne 0) { throw "Objective evaluation failed with exit code $LASTEXITCODE" }
Write-Host "Artifacts written under $env:AGRISIGHT_RUN_DIR and outputs\proposal_objective_evaluation"
