$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { $python = (Get-Command python).Source }
$steps = @(
  '00_download_koyambedu_history.py',
  '11_build_koyambedu_dataset.py',
  '12_koyambedu_research_analysis.py',
  '13_procurement_validation.py',
  '14_proposal_objective_evaluation.py',
  '15_agrisight_four_agent_pipeline.py'
)
foreach ($step in $steps) {
  Write-Host "Running $step"
  & $python (Join-Path $PSScriptRoot $step)
  if ($LASTEXITCODE -ne 0) { throw "$step failed with exit code $LASTEXITCODE" }
}
