param(
    [Parameter(Mandatory = $true)]
    [string]$GrootRoot,

    [ValidateSet("base", "sparse_demo_temporal")]
    [string]$Variant = "base",

    [double]$TemporalWeight = 0.05,
    [double]$VelocityWeight = 0.02,
    [string]$Python = "python",

    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$FinetuneArgs
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path $GrootRoot
$Candidates = @(
    (Join-Path $Root "gr00t\experiment\launch_finetune.py"),
    (Join-Path $Root "gr00t1.7\experiment\launch_finetune.py")
)
$LaunchScript = $Candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $LaunchScript) {
    throw "Could not locate the GR00T N1.7 launch_finetune.py under $Root"
}

$VariantArgs = @("--sparse-demo-algorithm-variant", $Variant)
if ($Variant -eq "sparse_demo_temporal") {
    $VariantArgs += @(
        "--sparse-demo-temporal-consistency-weight", [string]$TemporalWeight,
        "--sparse-demo-velocity-smoothness-weight", [string]$VelocityWeight
    )
} else {
    $VariantArgs += @(
        "--sparse-demo-temporal-consistency-weight", "0.0",
        "--sparse-demo-velocity-smoothness-weight", "0.0"
    )
}

& $Python $LaunchScript @FinetuneArgs @VariantArgs
exit $LASTEXITCODE
