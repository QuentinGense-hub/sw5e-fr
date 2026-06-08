const SW5E_CONDITION_LABELS = {
  corroded: "SW5E.ConCorroded",
  ignited: "SW5E.ConIgnited",
  shocked: "SW5E.ConShocked",
  slowed: "SW5E.ConSlowed",
  weakened: "SW5E.ConWeakened"
};

function valuesOfStatusEffects(statusEffects) {
  if (!statusEffects) return [];
  if (Array.isArray(statusEffects)) return statusEffects;
  if (statusEffects instanceof Map) return Array.from(statusEffects.values());
  return Object.values(statusEffects);
}

function applyConditionLabels() {
  const conditionTypes = CONFIG.DND5E?.conditionTypes ?? CONFIG.conditionTypes ?? {};

  for (const [id, label] of Object.entries(SW5E_CONDITION_LABELS)) {
    if (conditionTypes[id]) conditionTypes[id].label = label;
  }

  for (const effect of valuesOfStatusEffects(CONFIG.statusEffects)) {
    const id = effect.id ?? effect.name;
    const statusIds = effect.statuses instanceof Set ? effect.statuses : new Set();
    const label = SW5E_CONDITION_LABELS[id] ?? [...statusIds].map(statusId => SW5E_CONDITION_LABELS[statusId]).find(Boolean);
    if (!label) continue;

    effect.label = label;
    effect.name = label;
  }
}

Hooks.once("i18nInit", applyConditionLabels);
Hooks.once("ready", applyConditionLabels);
