param([string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot))
$bridge = Join-Path $ProjectRoot 'Saved\ClaudeBridge'
$ue = Join-Path $ProjectRoot 'Tools\ue.sh'
$gitBash = 'C:\Program Files\Git\bin\bash.exe'
$python = (Get-Command 'python.exe' -ErrorAction SilentlyContinue).Source
$pythonArgs = @()
if(-not $python){$python=(Get-Command 'py.exe' -ErrorAction SilentlyContinue).Source;$pythonArgs=@('-3')}
if(-not $python){throw 'Install Python 3 to stitch the panorama faces.'}
$stitcher = Join-Path $ProjectRoot 'Tools\stitch_pano.py'
$facesRoot = Join-Path $ProjectRoot 'Saved\Pano\faces'
$outRoot = Join-Path $ProjectRoot 'Saved\Final\Panoramas\SharedOutdoor_8K'
New-Item -ItemType Directory -Path $outRoot -Force | Out-Null
$spots = @(
  @{Name='Pool'; X=0; Y=0; Z=178.5},
  @{Name='Court'; X=5500; Y=0; Z=173.9},
  @{Name='PickleBall'; X=-5500; Y=0; Z=180.0},
  @{Name='JoggingTrack'; X=0; Y=6500; Z=165.5},
  @{Name='PartyLawn'; X=0; Y=-6500; Z=165.8},
  @{Name='Pavilion'; X=5500; Y=5500; Z=183.0},
  @{Name='Senior'; X=-5500; Y=5500; Z=181.8},
  @{Name='Path'; X=5500; Y=-5500; Z=176.6},
  @{Name='Lightings'; X=0; Y=-3000; Z=178.0}
)
function Run-Bridge([string]$Name,[string]$Code,[int]$Timeout=60) {
  $file = Join-Path $bridge ("job_render_shared_" + $Name + '.py')
  [IO.File]::WriteAllText($file,$Code,[Text.UTF8Encoding]::new($false))
  & $gitBash $ue $file $Timeout
  if ($LASTEXITCODE -ne 0) { throw "Bridge job failed: $Name" }
}
$i=0
foreach ($s in $spots) {
  $i++
  Write-Output ("START {0}/{1}: {2}" -f $i,$spots.Count,$s.Name)
  $unit='Amenity_Shared_Outdoor'
  $start="import pano_lumen as PL,importlib; importlib.reload(PL); PL.FACE_RES=4096; result=PL.render_spot_start('$unit','$($s.Name)',$($s.X),$($s.Y),bias=1.0,z=$($s.Z))"
  Run-Bridge ('start_' + $s.Name) $start 90 | Out-Null
  for($t=0;$t -lt 8;$t++) { Run-Bridge ('tick_' + $s.Name + '_' + $t) 'import pano_lumen as PL; result=PL.tick_batch()' 60 | Out-Null }
  $finish="import pano_lumen as PL; result=PL.render_spot_finish('$unit')"
  Run-Bridge ('finish_' + $s.Name) $finish 90 | Out-Null
  $base=Join-Path $outRoot ($s.Name + '_8K')
  & $python @pythonArgs $stitcher (Join-Path $facesRoot ("${unit}_$($s.Name)")) $base 8192
  if ($LASTEXITCODE -ne 0) { throw "Stitch failed: $($s.Name)" }
  Move-Item -LiteralPath ($base + '.jpg') -Destination ($base + '.jpg') -Force
  Write-Output ("DONE {0}: {1}.jpg" -f $s.Name,$base)
}