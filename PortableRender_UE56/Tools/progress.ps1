# Live progress for the Neelam -> Unreal job. Ctrl-C to stop.
$P = "C:\Users\Admin\Documents\Unreal Projects\Room_render"
$total = @{ "2bhk" = 1241; "3bhk" = 762 }   # visible objects per blend
while ($true) {
    Clear-Host
    Write-Host ("Neelam -> Unreal   " + (Get-Date -Format T)) -ForegroundColor Cyan
    foreach ($n in "2bhk", "3bhk") {
        $log = "$P\SourceArt\${n}_export.log"
        $out = "$P\SourceArt\" + $n.ToUpper()
        if (-not (Test-Path $log)) { Write-Host "$n export : waiting"; continue }
        $txt = Get-Content $log -Raw
        $done = ([regex]::Matches($txt, "Extracting primitive")).Count
        $pct = [math]::Min(100, [math]::Round(100 * $done / $total[$n]))
        if ($txt -match "@@DONE") { $state = "DONE" } elseif ($txt -match "RuntimeError|MemoryError|EXCEPTION_ACCESS") { $state = "check log" } else { $state = "exporting" }
        $mb = 0; if (Test-Path $out) { $mb = [math]::Round(((Get-ChildItem $out -Recurse -File | Measure-Object Length -Sum).Sum) / 1MB) }
        Write-Host ("{0} export : {1,-10} meshes {2}/{3} ({4}%)  on disk {5} MB" -f $n, $state, $done, $total[$n], $pct, $mb)
    }
    foreach ($n in "2bhk", "3bhk") {
        $bl = "$P\SourceArt\${n}_bake.log"
        if (Test-Path $bl) {
            $m = Select-String -Path $bl -Pattern "@@BAKED (\d+)/(\d+)" | Select-Object -Last 1
            $d = if (Select-String -Path $bl -Pattern "@@DONE" -Quiet) { "DONE" } else { "baking" }
            if ($m) { Write-Host ("{0} bake   : {1,-10} materials {2}/{3}" -f $n, $d, $m.Matches[0].Groups[1].Value, $m.Matches[0].Groups[2].Value) }
        }
    }
    $hb ="$P\Saved\ClaudeBridge\heartbeat.json"
    if ((Test-Path $hb) -and ((Get-Date) - (Get-Item $hb).LastWriteTime).TotalSeconds -lt 15) { Write-Host "Unreal bridge: CONNECTED" -ForegroundColor Green }
    else { Write-Host "Unreal bridge: not running - paste the py line into Output Log (Cmd)" -ForegroundColor Yellow }
    $last = Get-ChildItem "$P\Saved\ClaudeBridge\outbox" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime | Select-Object -Last 1
    if ($last) { Write-Host ("Last Unreal job: " + $last.Name + " @ " + $last.LastWriteTime.ToString("T")) }
    Start-Sleep 3
}
