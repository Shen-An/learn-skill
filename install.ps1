<#
install.ps1 — 把本仓库里的 skill 同步到各 harness 的技能目录

用法（在仓库任意位置执行）：
    pwsh learn-skill/install.ps1                  # 同步全部 skill 到三个默认根目录
    pwsh learn-skill/install.ps1 -Only paper-reading
    pwsh learn-skill/install.ps1 -DryRun          # 只看会做什么，不写盘
    pwsh learn-skill/install.ps1 -Roots "$HOME\.agents\skills"
    pwsh learn-skill/install.ps1 -SkipGate        # 跳过回归门禁（不推荐）
    pwsh learn-skill/install.ps1 -KeepBackup      # 保留被替换掉的旧版目录

行为：
  1. 自动发现仓库里所有含 SKILL.md 的子目录（learning-wiki / paper-reading / …）
  2. 对每个 (skill × 根目录)：已是同版本则跳过；否则"旧版改名保全 → 拷新版 → 逐文件 SHA-256 比对 → 跑该 skill 的 evals/run_evals.py → 通过才删旧版，不通过自动回滚"
  3. 安装副本不含本地证据账本 feedback/ledger.jsonl（该文件按设计由运行时自建）；无论新装、升级还是"已同步"，都会清掉副本里的 __pycache__ 残留（清了多少个会打印出来）
  4. 退出码：全部成功 0；有任何失败 1
#>
[CmdletBinding()]
param(
    [string[]]$Roots,
    [string[]]$Only = @(),
    [switch]$SkipGate,
    [switch]$KeepBackup,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
$env:PYTHONDONTWRITEBYTECODE = '1'

$repo = $PSScriptRoot
if (-not (Test-Path -LiteralPath (Join-Path $repo 'README.md'))) {
    # 允许脚本被放在仓库子目录里：向上找
    $p = $repo
    while ($p -and -not (Test-Path -LiteralPath (Join-Path $p 'README.md'))) { $p = Split-Path -Parent $p }
    if ($p) { $repo = $p }
}

if (-not $Roots -or $Roots.Count -eq 0) {
    $Roots = @(
        (Join-Path $env:USERPROFILE '.agents\skills'),
        (Join-Path $env:USERPROFILE '.claude\skills'),
        (Join-Path $env:USERPROFILE '.codex\skills')
    )
}

function Get-BundleFiles {
    param([string]$Dir)
    if (-not (Test-Path -LiteralPath $Dir)) { return @() }
    Get-ChildItem -Recurse -File -Force -LiteralPath $Dir -ErrorAction SilentlyContinue | Where-Object {
        $rel = $_.FullName.Substring($Dir.Length + 1)
        ($rel -notmatch '\\__pycache__\\') -and ($rel -ne 'feedback\ledger.jsonl') -and ($_.Extension -ne '.pyc')
    }
}

function Get-SkillVersion {
    param([string]$Dir)
    $sk = Join-Path $Dir 'SKILL.md'
    if (-not (Test-Path -LiteralPath $sk)) { return '—' }
    $m = Select-String -LiteralPath $sk -Pattern '^\s*version:\s*"?([^"\r\n]+)' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($m) { return $m.Matches[0].Groups[1].Value.Trim() }
    return '—'
}

function Compare-Bundle {
    param([string]$Src, [string]$Dst)
    $sf = @(Get-BundleFiles $Src)
    $df = @(Get-BundleFiles $Dst)
    $srcRel = @($sf | ForEach-Object { $_.FullName.Substring($Src.Length + 1) })
    $dstRel = @($df | ForEach-Object { $_.FullName.Substring($Dst.Length + 1) })
    $missing = 0; $mismatch = 0
    foreach ($f in $sf) {
        $rel = $f.FullName.Substring($Src.Length + 1)
        $b = Join-Path $Dst $rel
        if (-not (Test-Path -LiteralPath $b)) { $missing++; continue }
        if ((Get-FileHash -LiteralPath $f.FullName).Hash -ne (Get-FileHash -LiteralPath $b).Hash) { $mismatch++ }
    }
    $extra = @($dstRel | Where-Object { $srcRel -notcontains $_ })
    [pscustomobject]@{ Missing = $missing; Mismatch = $mismatch; Extra = @($extra).Count; ExtraNames = $extra; Count = @($srcRel).Count }
}

function Remove-StrayPycache {
    param([string]$Dir)
    $n = 0
    Get-ChildItem -Recurse -Force -Directory -LiteralPath $Dir -Filter '__pycache__' -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-Item -Recurse -Force -LiteralPath $_.FullName -ErrorAction SilentlyContinue
        $n++
    }
    return $n
}

function Invoke-SkillGate {
    param([string]$Dir)
    if ($SkipGate) { return [pscustomobject]@{ Ok = $true; Text = '已跳过（-SkipGate）' } }
    $gate = Join-Path $Dir 'evals\run_evals.py'
    if (-not (Test-Path -LiteralPath $gate)) { return [pscustomobject]@{ Ok = $true; Text = '无门禁脚本' } }
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) { return [pscustomobject]@{ Ok = $false; Text = '找不到 python' } }
    Push-Location -LiteralPath $Dir
    try { $out = & python 'evals\run_evals.py' 2>&1; $code = $LASTEXITCODE } finally { Pop-Location }
    $lines = @($out)
    $last = @($lines | Where-Object { $_ -match '^\[' } | Select-Object -Last 1)
    if (-not $last -or $last.Count -eq 0) { $last = @($lines | Select-Object -Last 1) }
    [pscustomobject]@{ Ok = ($code -eq 0); Text = ('exit={0} :: {1}' -f $code, $last[0]) }
}

# ---- 发现 skill ----
$skills = @(Get-ChildItem -Directory -LiteralPath $repo | Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'SKILL.md') })
if ($Only.Count -gt 0) { $skills = @($skills | Where-Object { $Only -contains $_.Name }) }
if ($skills.Count -eq 0) { Write-Host '没找到任何 skill（子目录里含 SKILL.md 才算）' -ForegroundColor Red; exit 1 }

Write-Host ('仓库: {0}' -f $repo) -ForegroundColor Cyan
Write-Host ('skill: {0}' -f (($skills | ForEach-Object { $_.Name }) -join ', ')) -ForegroundColor Cyan
Write-Host ('根目录: {0}' -f ($Roots -join '  |  ')) -ForegroundColor Cyan
if ($DryRun) { Write-Host '模式: DRY RUN（只报告，不写盘）' -ForegroundColor Yellow }
Write-Host ''

$installed = 0; $updated = 0; $synced = 0; $failed = 0
$results = @()

foreach ($root in $Roots) {
    foreach ($skill in $skills) {
        $src = $skill.FullName
        $dst = Join-Path $root $skill.Name
        $newVer = Get-SkillVersion $src
        $lines = @()

        if (-not (Test-Path -LiteralPath $root)) {
            $lines += ('    根目录不存在，将新建: {0}' -f $root)
            if (-not $DryRun) { New-Item -ItemType Directory -Path $root -Force | Out-Null }
        }

        $exists = Test-Path -LiteralPath $dst
        $cmp0 = if ($exists) { Compare-Bundle -Src $src -Dst $dst } else { $null }
        $sameAlready = $exists -and $cmp0.Missing -eq 0 -and $cmp0.Mismatch -eq 0 -and $cmp0.Extra -eq 0

        if ($sameAlready) {
            # 内容已一致也要清残留：门禁跑过之后安装副本里可能留下 __pycache__
            $swept = Remove-StrayPycache -Dir $dst
            $gate = Invoke-SkillGate -Dir $dst
            $suffix = if ($swept -gt 0) { '  已清理 pycache {0} 个' -f $swept } else { '' }
            $tag = '已同步'; $color = 'DarkGray'
            if (-not $gate.Ok) { $tag = '已同步但门禁未过'; $color = 'Red'; $failed++ } else { $synced++ }
            Write-Host ('[{0}] {1}  v{2}  {3} 文件  {4}{5}' -f $tag, $dst, $newVer, $cmp0.Count, $gate.Text, $suffix) -ForegroundColor $color
            $results += [pscustomobject]@{ Skill = $skill.Name; Path = $dst; Action = $tag; Version = $newVer; Files = $cmp0.Count; Ok = $gate.Ok }
            foreach ($l in $lines) { Write-Host $l -ForegroundColor Yellow }
            continue
        }

        $action = if ($exists) { '升级' } else { '新装' }
        if ($DryRun) {
            $detail = if ($exists) { ('缺失 {0} / 不一致 {1} / 多余 {2}' -f $cmp0.Missing, $cmp0.Mismatch, $cmp0.Extra) } else { '目标不存在' }
            Write-Host ('[将{0}] {1}  v{2}  （{3}）' -f $action, $dst, $newVer, $detail) -ForegroundColor Yellow
            $results += [pscustomobject]@{ Skill = $skill.Name; Path = $dst; Action = '将' + $action; Version = $newVer; Files = 0; Ok = $true }
            continue
        }

        $oldVer = if ($exists) { Get-SkillVersion $dst } else { '（无旧版）' }
        $oldFp = if ($exists) { (Get-FileHash -LiteralPath (Join-Path $dst 'SKILL.md')).Hash.Substring(0, 16) } else { '—' }
        $tmp = $dst + '.old-tmp'
        if (Test-Path -LiteralPath $tmp) { Remove-Item -Recurse -Force -LiteralPath $tmp }

        try {
            if ($exists) { Move-Item -LiteralPath $dst -Destination $tmp -Force }
            New-Item -ItemType Directory -Path $dst -Force | Out-Null
            Copy-Item -Path (Join-Path $src '*') -Destination $dst -Recurse -Force
            Remove-Item -LiteralPath (Join-Path $dst 'feedback\ledger.jsonl') -Force -ErrorAction SilentlyContinue
            Remove-StrayPycache -Dir $dst | Out-Null

            $cmp = Compare-Bundle -Src $src -Dst $dst
            $gate = Invoke-SkillGate -Dir $dst
            $ok = ($cmp.Missing -eq 0 -and $cmp.Mismatch -eq 0 -and $cmp.Extra -eq 0 -and $gate.Ok)

            if ($ok) {
                if (Test-Path -LiteralPath $tmp) {
                    if ($KeepBackup) {
                        $bakName = '{0}.bak-{1}-{2}' -f $skill.Name, ($oldVer -replace '[^\w\.\-]', ''), (Get-Date -Format 'yyyyMMdd-HHmmss')
                        Move-Item -LiteralPath $tmp -Destination (Join-Path $root $bakName) -Force
                        $lines += ('    旧版保留为: {0}' -f $bakName)
                    } else {
                        Remove-Item -Recurse -Force -LiteralPath $tmp
                    }
                }
                if ($action -eq '升级') { $updated++ } else { $installed++ }
                Write-Host ('[{0}] {1}  v{2}（旧版 v{3} fp={4}）  {5} 文件  {6}' -f $action, $dst, $newVer, $oldVer, $oldFp, $cmp.Count, $gate.Text) -ForegroundColor Green
                $results += [pscustomobject]@{ Skill = $skill.Name; Path = $dst; Action = $action; Version = $newVer; Files = $cmp.Count; Ok = $true }
            } else {
                Remove-Item -Recurse -Force -LiteralPath $dst -ErrorAction SilentlyContinue
                if (Test-Path -LiteralPath $tmp) { Move-Item -LiteralPath $tmp -Destination $dst -Force }
                Write-Host ('[失败已回滚] {0}  比对 缺失={1} 不一致={2} 多余={3}  门禁 {4}' -f $dst, $cmp.Missing, $cmp.Mismatch, $cmp.Extra, $gate.Text) -ForegroundColor Red
                $failed++
                $results += [pscustomobject]@{ Skill = $skill.Name; Path = $dst; Action = '失败已回滚'; Version = $oldVer; Files = $cmp.Count; Ok = $false }
            }
        } catch {
            Remove-Item -Recurse -Force -LiteralPath $dst -ErrorAction SilentlyContinue
            if (Test-Path -LiteralPath $tmp) { Move-Item -LiteralPath $tmp -Destination $dst -Force }
            Write-Host ('[异常已回滚] {0}: {1}' -f $dst, $_.Exception.Message) -ForegroundColor Red
            $failed++
        }
        foreach ($l in $lines) { Write-Host $l -ForegroundColor Yellow }
    }
}

Write-Host ''
Write-Host ('汇总: 新装 {0} / 升级 {1} / 已同步 {2} / 失败 {3}' -f $installed, $updated, $synced, $failed) -ForegroundColor Cyan
if ($DryRun) { Write-Host '（DRY RUN：未写入任何文件）' -ForegroundColor Yellow }

# 附：当前各根目录的 skill 与版本
if (-not $DryRun) {
    Write-Host ''
    Write-Host '当前状态:' -ForegroundColor Cyan
    foreach ($root in $Roots) {
        if (-not (Test-Path -LiteralPath $root)) { Write-Host ('  [不存在] {0}' -f $root); continue }
        foreach ($skill in $skills) {
            $dst = Join-Path $root $skill.Name
            if (Test-Path -LiteralPath $dst) {
                $cmp = Compare-Bundle -Src $skill.FullName -Dst $dst
                $flag = if ($cmp.Missing -eq 0 -and $cmp.Mismatch -eq 0 -and $cmp.Extra -eq 0) { '一致' } else { '不一致' }
                Write-Host ('  {0,-64} v{1,-8} {2,3} 文件  {3}' -f $dst, (Get-SkillVersion $dst), $cmp.Count, $flag)
            }
        }
    }
}

exit $(if ($failed -gt 0) { 1 } else { 0 })
