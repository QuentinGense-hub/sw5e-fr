const MODULE_ID = "sw5e-fr";
const LANG = "fr";
const COMPENDIUM_DIR = "compendium";

function clone(value) {
  if (globalThis.foundry?.utils?.deepClone) return foundry.utils.deepClone(value);
  if (globalThis.structuredClone) return structuredClone(value);
  return JSON.parse(JSON.stringify(value));
}

function getBabele() {
  return globalThis.Babele?.get?.() ?? globalThis.game?.babele ?? null;
}

function translateJournalPages(pages, translations = {}) {
  if (!pages || !translations || typeof translations !== "object") return pages;

  const isArray = Array.isArray(pages);
  const sourcePages = isArray ? pages : Object.values(pages);
  if (!sourcePages.length) return pages;

  const translated = sourcePages.map(page => {
    const patch = translations[page._id] ?? translations[page.name];
    if (!patch) return page;

    const next = clone(page);
    const content = typeof patch.text === "string" ? patch.text : patch.content;
    const tooltip = patch.tooltip ?? patch.system?.tooltip ?? content;

    if (patch.name) next.name = patch.name;
    if (content) next.text = { ...(next.text ?? {}), content };
    if (tooltip) next.system = { ...(next.system ?? {}), tooltip };

    return next;
  });

  if (isArray) return translated;
  return translated.reduce((acc, page) => {
    acc[page._id ?? page.name] = page;
    return acc;
  }, {});
}

function translateTableResults(results, translations = {}) {
  if (!Array.isArray(results) || !translations || typeof translations !== "object") return results;

  return results.map(result => {
    const rangeKey = Array.isArray(result.range) ? `${result.range[0]}-${result.range[1]}` : undefined;
    const text = translations[result._id] ?? translations[rangeKey] ?? translations[result.text];
    if (!text) return result;

    const next = clone(result);
    next.text = text;
    return next;
  });
}

function translateAdvancements(advancements, translations = {}) {
  if (!Array.isArray(advancements) || !translations || typeof translations !== "object") return advancements;

  return advancements.map(advancement => {
    const patch = translations[advancement._id] ?? translations[advancement.title];
    if (!patch) return advancement;

    const next = clone(advancement);
    if (typeof patch === "string") next.title = patch;
    else {
      if (patch.title) next.title = patch.title;
      if (patch.hint) next.hint = patch.hint;
    }
    return next;
  });
}

Hooks.once("init", () => {
  const babele = getBabele();
  if (!babele) {
    console.warn(`${MODULE_ID} | Babele est introuvable. Les compendiums SW5E ne seront pas traduits.`);
    return;
  }

  babele.registerConverters?.({
    sw5eJournalPages: translateJournalPages,
    sw5eTableResults: translateTableResults,
    sw5eAdvancements: translateAdvancements
  });

  babele.register({
    module: MODULE_ID,
    lang: LANG,
    dir: COMPENDIUM_DIR
  });
});

Hooks.once("ready", () => {
  if (getBabele()) return;
  ui.notifications?.warn?.("SW5E FR : active le module Babele pour traduire les compendiums SW5E.");
});
