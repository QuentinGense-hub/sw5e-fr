param(
    [string]$source = "../upstream-sw5e-module",
    [string]$out = "translation-workbench",
    [string]$only = $null
)

$MODULE_PREFIX = "sw5e"

function Clean-Entry($entry) {
    $result = @{}
    foreach ($kvp in $entry.GetEnumerator()) {
        $value = $kvp.Value
        if ($null -eq $value) { continue }
        if ($value -is [string] -and $value.Trim() -eq "") { continue }
        if ($value -is [hashtable] -and $value.Keys.Count -eq 0) { continue }
        $result[$kvp.Key] = $value
    }
    return $result
}

function Extract-Advancements($doc) {
    $advancements = @{}
    $advList = $doc.system.advancement
    if (-not $advList -or $advList.Count -eq 0) { return $null }

    foreach ($adv in $advList) {
        if (-not $adv.title -and -not $adv.hint) { continue }
        $key = $adv._id
        if (-not $key) { $key = $adv.title }
        # Simple title-only advancements (like "Features" -> "Features")
        if ($adv.title -and -not $adv.hint) {
            $advancements[$adv.title] = $adv.title
        } elseif ($adv.title -and $adv.hint) {
            $advancements[$key] = Clean-Entry @{
                "title" = $adv.title
                "hint" = $adv.hint
            }
        }
    }

    if (@($advancements.Keys).Count -eq 0) { return $null }
    return $advancements
}

function Extract-ItemOrActor($doc) {
    $result = @{}
    $result["name"] = $doc.name
    if ($doc.system.description.value -and $doc.system.description.value.Trim() -ne "") { $result["description"] = $doc.system.description.value }
    if ($doc.system.description.chat -and $doc.system.description.chat.Trim() -ne "") { $result["chat"] = $doc.system.description.chat }
    if ($doc.system.atFlavorText.value -and $doc.system.atFlavorText.value.Trim() -ne "") { $result["atFlavorText"] = $doc.system.atFlavorText.value }
    if ($doc.system.invocations.value -and $doc.system.invocations.value.Trim() -ne "") { $result["invocations"] = $doc.system.invocations.value }
    if ($doc.system.details.biography.value -and $doc.system.details.biography.value.Trim() -ne "") { $result["biography"] = $doc.system.details.biography.value }
    $adv = Extract-Advancements $doc
    if ($adv) { $result["advancements"] = $adv }
    return Clean-Entry $result
}

function Extract-Journal($doc) {
    $pages = @{}
    if ($doc.pages) {
        foreach ($page in $doc.pages) {
            $key = $page._id
            $pageEntry = @{}
            $pageEntry["name"] = $page.name
            if ($page.text.content -and $page.text.content.Trim() -ne "") { $pageEntry["text"] = $page.text.content }
            if ($page.system.tooltip -and $page.system.tooltip.Trim() -ne "") { $pageEntry["tooltip"] = $page.system.tooltip }
            $cleaned = Clean-Entry $pageEntry
            if ($cleaned.Keys.Count -gt 0) {
                $pages[$key] = $cleaned
            }
        }
    }
    $result = @{}
    $result["name"] = $doc.name
    if ($pages.Keys.Count -gt 0) { $result["pages"] = $pages }
    return Clean-Entry $result
}

function Extract-Table($doc) {
    $results = @{}
    if ($doc.results) {
        foreach ($result in $doc.results) {
            $key = $result._id
            $results[$key] = $result.text
        }
    }
    $entry = @{}
    $entry["name"] = $doc.name
    if ($doc.description -and $doc.description.Trim() -ne "") { $entry["description"] = $doc.description }
    if ($results.Keys.Count -gt 0) { $entry["results"] = $results }
    return Clean-Entry $entry
}

function Mapping-For-Pack($pack) {
    if ($pack.type -eq "JournalEntry") {
        return @{
            "name" = "name"
            "pages" = @{
                "path" = "pages"
                "converter" = "sw5eJournalPages"
            }
        }
    }
    if ($pack.type -eq "RollTable") {
        return @{
            "name" = "name"
            "description" = "description"
            "results" = @{
                "path" = "results"
                "converter" = "sw5eTableResults"
            }
        }
    }
    return @{
        "name" = "name"
        "description" = "system.description.value"
        "chat" = "system.description.chat"
        "atFlavorText" = "system.atFlavorText.value"
        "invocations" = "system.invocations.value"
        "biography" = "system.details.biography.value"
        "advancements" = @{
            "path" = "system.advancement"
            "converter" = "sw5eAdvancements"
        }
    }
}

function Extract-Document($pack, $doc) {
    if ($pack.type -eq "JournalEntry") { return Extract-Journal $doc }
    if ($pack.type -eq "RollTable") { return Extract-Table $doc }
    return Extract-ItemOrActor $doc
}

function Build-Pack-Template($sourceRoot, $pack) {
    $sourceDir = Join-Path -Path $sourceRoot -ChildPath "packs/_source/$($pack.name)"
    if (-not (Test-Path -LiteralPath $sourceDir)) {
        return $null
    }

    $entries = @{}
    $files = Get-ChildItem -Path $sourceDir -Filter "*.json" -Recurse -File
    foreach ($file in $files) {
        $content = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8
        $doc = $content | ConvertFrom-Json
        $key = $doc.name
        if (-not $key) { $key = $doc._id }
        if (-not $key) { $key = $file.BaseName }
        $entries[$key] = Extract-Document $pack $doc
    }

    return @{
        "label" = $pack.label
        "mapping" = Mapping-For-Pack $pack
        "entries" = $entries
    }
}

function Main {
    $sourceRoot = Resolve-Path $source
    New-Item -ItemType Directory -Force -Path $out | Out-Null
    $outRoot = Resolve-Path $out

    $manifestPath = Join-Path -Path $sourceRoot -ChildPath "module.json"
    $manifestRaw = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8
    $manifest = $manifestRaw | ConvertFrom-Json

    $packs = @($manifest.packs)
    if ($only) {
        $onlySet = $only.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
        $packs = $packs | Where-Object { $_.name -in $onlySet }
    }

    $total = $packs.Count
    $i = 0
    foreach ($pack in $packs) {
        $i++
        Write-Progress -Activity "Generating Babele templates" -Status "$($pack.name) ($i/$total)" -PercentComplete (($i-1)/$total*100)
        $template = Build-Pack-Template $sourceRoot $pack
        if (-not $template) {
            Write-Host "  Skipped $($pack.name) (no _source dir)"
            continue
        }
        $outFile = Join-Path -Path $outRoot -ChildPath "$MODULE_PREFIX.$($pack.name).json"
        $json = $template | ConvertTo-Json -Depth 100
        [System.IO.File]::WriteAllText($outFile, "$json`n", [System.Text.UTF8Encoding]::new($false))
        Write-Host "  Wrote $outFile"
    }
    Write-Progress -Activity "Generating Babele templates" -Completed
}

Main
