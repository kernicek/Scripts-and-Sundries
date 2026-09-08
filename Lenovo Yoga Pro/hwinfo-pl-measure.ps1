# Lenovo Yoga Pro 9 14IRP8 — read Intel PL1/PL2 from HWiNFO shared memory.
#
# Setup:  HWiNFO64 running, Settings -> "Shared Memory Support" ticked
#         (free version disables it again after 12 h).
#
# Usage:  .\hwinfo-pl-measure.ps1 -Label 'batterysaving-AC-idle'
#         .\hwinfo-pl-measure.ps1 -Label 'batterysaving-AC-load' -Load -Seconds 90
#
# Set the Lenovo thermal mode with Fn+Q before each run — the Windows power-mode
# slider does NOT change the power limits on this chassis.
# Appends to pl-samples.csv next to this script.

param(
  [string]$Label = 'unlabelled',
  [switch]$Load,
  [int]$Seconds = 90,
  [int]$IntervalMs = 2500,
  [int]$Threads = 0
)
$ErrorActionPreference = 'Stop'
$csv = Join-Path $PSScriptRoot 'pl-samples.csv'

$code = @'
using System;
using System.IO.MemoryMappedFiles;
using System.Text;
using System.Collections.Generic;

public class Hwi {
    public static Dictionary<string, double> Read() {
        var d = new Dictionary<string, double>();
        var mmf = MemoryMappedFile.OpenExisting("Global\\HWiNFO_SENS_SM2", MemoryMappedFileRights.Read);
        using (var acc = mmf.CreateViewAccessor(0, 0, MemoryMappedFileAccess.Read)) {
            uint off = acc.ReadUInt32(32), size = acc.ReadUInt32(36), num = acc.ReadUInt32(40);
            for (uint i = 0; i < num; i++) {
                long b = off + (long)i * size;
                byte[] lbl = new byte[128];
                acc.ReadArray(b + 12, lbl, 0, 128);
                string label = Encoding.Default.GetString(lbl);
                int z = label.IndexOf('\0'); if (z >= 0) label = label.Substring(0, z);
                double val = acc.ReadDouble(b + 12 + 128 + 128 + 16);
                if (!d.ContainsKey(label)) d[label] = val;
            }
        }
        return d;
    }
}
'@
if (-not ('Hwi' -as [type])) { Add-Type -TypeDefinition $code -Language CSharp }

function Get-Snap {
    $s = [Hwi]::Read()
    function V($k) { if ($s.ContainsKey($k)) { [math]::Round($s[$k], 1) } else { 'n/a' } }
    [pscustomobject]@{
        Label      = $Label
        PL1_Static = V 'PL1 Power Limit (Static)'
        PL1_Dyn    = V 'PL1 Power Limit (Dynamic)'
        PL2_Static = V 'PL2 Power Limit (Static)'
        PL2_Dyn    = V 'PL2 Power Limit (Dynamic)'
        PkgPower   = V 'CPU Package Power'
        IAPower    = V 'IA Cores Power'
        PkgTemp    = V 'CPU Package'
        CoreMax    = V 'Core Max'
        CpuUsage   = V 'Total CPU Usage'
        ThermThrot = V 'Package/Ring Thermal Throttling'
        ChargeRate = V 'Charge Rate'
    }
}

function Invoke-Sampling([int]$Secs) {
    $rows = @()
    if ($Secs -le 0) { return @(Get-Snap) }
    $end = (Get-Date).AddSeconds($Secs)
    while ((Get-Date) -lt $end) { $rows += Get-Snap; Start-Sleep -Milliseconds $IntervalMs }
    $rows
}

$procs = @()
try {
    if ($Load) {
        if ($Threads -le 0) { $Threads = [Environment]::ProcessorCount }
        Write-Output "Load: $Threads threads for $Seconds s"
        for ($i = 0; $i -lt $Threads; $i++) {
            $procs += Start-Process powershell.exe -PassThru -WindowStyle Hidden -ArgumentList @(
                '-NoProfile','-Command',
                "`$e=(Get-Date).AddSeconds($($Seconds + 10)); `$x=0.0; while((Get-Date) -lt `$e){ `$x=[math]::Sqrt(`$x+1.234567) }"
            )
        }
        Start-Sleep -Seconds 3
        $rows = Invoke-Sampling ($Seconds - 5)
    } else {
        $rows = Invoke-Sampling 0
    }
}
finally {
    foreach ($p in $procs) { try { Stop-Process -Id $p.Id -Force -ErrorAction Stop } catch {} }
}

$rows | Format-Table -AutoSize | Out-String -Width 250 | Write-Output

if ($rows.Count -gt 1) {
    "--- $($rows.Count) samples ---"
    "PL1_Dyn seen : " + (($rows.PL1_Dyn | Sort-Object -Unique) -join ', ')
    "PL2_Dyn seen : " + (($rows.PL2_Dyn | Sort-Object -Unique) -join ', ')
    $pk = $rows.PkgPower | Where-Object { $_ -ne 'n/a' }
    if ($pk) { "PkgPower min/avg/max : {0} / {1} / {2} W" -f ($pk | Measure-Object -Minimum).Minimum, [math]::Round(($pk | Measure-Object -Average).Average,1), ($pk | Measure-Object -Maximum).Maximum }
    $tp = $rows.CoreMax | Where-Object { $_ -ne 'n/a' }
    if ($tp) { "CoreMax  min/avg/max : {0} / {1} / {2} C" -f ($tp | Measure-Object -Minimum).Minimum, [math]::Round(($tp | Measure-Object -Average).Average,1), ($tp | Measure-Object -Maximum).Maximum }
}

$rows | Export-Csv -Path $csv -NoTypeInformation -Append -Encoding utf8
"appended to $csv"
