#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";

const MODULE_PREFIX = "sw5e";

function parseArgs(argv) {
  const args = {
    source: "../upstream-sw5e-module",
    out: "./translation-workbench",
    only: null
  };

  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--source") args.source = argv[++i];
    else if (arg === "--out") args.out = argv[++i];
    else if (arg === "--only") args.only = new Set(argv[++i].split(",").map(pack => pack.trim()).filter(Boolean));
    else if (arg === "--help" || arg === "-h") {
      printHelp();
      process.exit(0);
    }
  }

  return args;
}

function printHelp() {
  console.log(`Usage:
node sw5e-fr/tools/export-babele-templates.mjs --source upstream-sw5e-module --out sw5e-fr/translation-workbench

Options:
  --source <dir>  Dossier du dépôt sw5e-module cloné.
  --out <dir>     Dossier de sortie des templates Babele.
  --only <packs>  Liste de packs séparés par des virgules, ex: conditions,classes.
`);
}

async function readJson(file) {
  return JSON.parse(await fs.readFile(file, "utf8"));
}

async function* walk(dir) {
  for (const entry of await fs.readdir(dir, { withFileTypes: true })) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) yield* walk(fullPath);
    else if (entry.isFile() && entry.name.endsWith(".json")) yield fullPath;
  }
}

function cleanEntry(entry) {
  return Object.fromEntries(Object.entries(entry).filter(([, value]) => {
    if (value === undefined || value === null) return false;
    if (typeof value === "string" && value.trim() === "") return false;
    if (typeof value === "object" && !Array.isArray(value) && !Object.keys(value).length) return false;
    return true;
  }));
}

function extractItemOrActor(doc) {
  return cleanEntry({
    name: doc.name,
    description: doc.system?.description?.value,
    chat: doc.system?.description?.chat,
    atFlavorText: doc.system?.atFlavorText?.value,
    invocations: doc.system?.invocations?.value,
    biography: doc.system?.details?.biography?.value,
    advancements: extractAdvancements(doc)
  });
}

function extractAdvancements(doc) {
  const advancements = {};

  for (const advancement of doc.system?.advancement ?? []) {
    if (!advancement.title && !advancement.hint) continue;
    advancements[advancement._id ?? advancement.title] = cleanEntry({
      title: advancement.title,
      hint: advancement.hint
    });
  }

  return advancements;
}

function extractJournal(doc) {
  const pages = {};

  for (const page of doc.pages ?? []) {
    const key = page._id ?? page.name;
    pages[key] = cleanEntry({
      name: page.name,
      text: page.text?.content,
      tooltip: page.system?.tooltip
    });
  }

  return cleanEntry({
    name: doc.name,
    pages
  });
}

function extractTable(doc) {
  const results = {};

  for (const result of doc.results ?? []) {
    const rangeKey = Array.isArray(result.range) ? `${result.range[0]}-${result.range[1]}` : undefined;
    results[result._id ?? rangeKey ?? result.text] = result.text;
  }

  return cleanEntry({
    name: doc.name,
    description: doc.description,
    results
  });
}

function mappingForPack(pack) {
  if (pack.type === "JournalEntry") {
    return {
      name: "name",
      pages: {
        path: "pages",
        converter: "sw5eJournalPages"
      }
    };
  }

  if (pack.type === "RollTable") {
    return {
      name: "name",
      description: "description",
      results: {
        path: "results",
        converter: "sw5eTableResults"
      }
    };
  }

  return {
    name: "name",
    description: "system.description.value",
    chat: "system.description.chat",
    atFlavorText: "system.atFlavorText.value",
    invocations: "system.invocations.value",
    biography: "system.details.biography.value",
    advancements: {
      path: "system.advancement",
      converter: "sw5eAdvancements"
    }
  };
}

function extractDocument(pack, doc) {
  if (pack.type === "JournalEntry") return extractJournal(doc);
  if (pack.type === "RollTable") return extractTable(doc);
  return extractItemOrActor(doc);
}

async function buildPackTemplate(sourceRoot, pack) {
  const sourceDir = path.join(sourceRoot, "packs", "_source", pack.name);
  const entries = {};

  try {
    await fs.access(sourceDir);
  } catch {
    return null;
  }

  for await (const file of walk(sourceDir)) {
    const doc = await readJson(file);
    const key = doc.name ?? doc._id ?? path.basename(file, ".json");
    entries[key] = extractDocument(pack, doc);
  }

  return {
    label: pack.label,
    mapping: mappingForPack(pack),
    entries
  };
}

async function main() {
  const args = parseArgs(process.argv);
  const sourceRoot = path.resolve(args.source);
  const outRoot = path.resolve(args.out);
  const manifest = await readJson(path.join(sourceRoot, "module.json"));
  const packs = manifest.packs.filter(pack => !args.only || args.only.has(pack.name));

  await fs.mkdir(outRoot, { recursive: true });

  for (const pack of packs) {
    const template = await buildPackTemplate(sourceRoot, pack);
    if (!template) continue;

    const outFile = path.join(outRoot, `${MODULE_PREFIX}.${pack.name}.json`);
    await fs.writeFile(outFile, `${JSON.stringify(template, null, 2)}\n`, "utf8");
    console.log(`Wrote ${path.relative(process.cwd(), outFile)}`);
  }
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
