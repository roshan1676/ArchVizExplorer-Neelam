$projectRoot = Split-Path -Parent $PSScriptRoot
$bridge = Join-Path $projectRoot 'Saved\ClaudeBridge'
New-Item -ItemType Directory -Path (Join-Path $bridge 'inbox'), (Join-Path $bridge 'outbox'), (Join-Path $bridge 'done') -Force | Out-Null
$lines = @(
    '#!/bin/bash',
    'PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"',
    'B="$PROJECT_ROOT/Saved/ClaudeBridge"',
    'mkdir -p "$B/inbox" "$B/outbox"',
    'T=${2:-60}; ID="cmd_$(date +%s%N)"',
    'if [ "$1" = "-" ] || [ -z "$1" ]; then cat > "$B/inbox/$ID.tmp"; else cp "$1" "$B/inbox/$ID.tmp"; fi',
    'mv "$B/inbox/$ID.tmp" "$B/inbox/$ID.py"',
    'for i in $(seq 1 $((T*4))); do',
    '  if [ -f "$B/outbox/$ID.json" ]; then cat "$B/outbox/$ID.json"; exit 0; fi',
    '  sleep 0.25',
    'done',
    'echo "TIMEOUT: Unreal Editor bridge did not return $ID" >&2',
    'rm -f "$B/inbox/$ID.py"',
    'exit 1'
)
[IO.File]::WriteAllText((Join-Path $bridge 'ue.sh'), ($lines -join "`n"), [Text.UTF8Encoding]::new($false))
Write-Output "Render bridge ready in $bridge"
