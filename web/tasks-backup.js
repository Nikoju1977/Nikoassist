/* NikoAssist Web — restaurer un export sans modifier les tâches déjà présentes.
   Aucune requête réseau ; validation stricte avant affichage ou sauvegarde. */
(function(root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.NikoAssistTaskBackup = api;
})(typeof window === 'object' ? window : typeof globalThis === 'object' ? globalThis : this, function() {
  'use strict';
  const FORMAT = 'nikoassist-tasks-v1';
  const MAX_TASKS = 200;
  const MAX_BYTES = 256 * 1024;

  function title(value) {
    return typeof value === 'string' ? value.replace(/\s+/g, ' ').trim() : '';
  }
  function parse(text) {
    if (typeof text !== 'string' || text.length > MAX_BYTES) throw new Error('Fichier JSON trop volumineux.');
    let payload;
    try { payload = JSON.parse(text); }
    catch (_) { throw new Error('Le fichier ne contient pas un JSON valide.'); }
    if (!payload || typeof payload !== 'object' || Array.isArray(payload) ||
        payload.format !== FORMAT || !Array.isArray(payload.tasks) || payload.tasks.length > MAX_TASKS) {
      throw new Error('Ce fichier ne correspond pas à un export de tâches NikoAssist.');
    }
    return payload.tasks.map((item, index) => {
      const name = title(item?.text);
      if (!name || name.length > 160 || typeof item?.done !== 'boolean') {
        throw new Error('Tâche invalide à la ligne ' + (index + 1) + '.');
      }
      // Les identifiants importés ne sont jamais réutilisés.
      return {text: name, done: item.done};
    });
  }

  function previewMerge(existing, imported) {
    if (!Array.isArray(existing) || !Array.isArray(imported)) throw new TypeError('Listes de tâches invalides.');
    const keys = new Set(existing.map(t => title(t?.text).toLocaleLowerCase('fr')).filter(Boolean));
    const toAdd = [];
    let duplicates = 0, limited = 0;
    for (const item of imported) {
      const key = title(item.text).toLocaleLowerCase('fr');
      if (keys.has(key)) { duplicates++; continue; }
      keys.add(key);
      if (existing.length + toAdd.length >= MAX_TASKS) { limited++; continue; }
      toAdd.push({text: title(item.text), done: item.done});
    }
    return {toAdd, duplicates, limited};
  }
  return Object.freeze({FORMAT, MAX_TASKS, MAX_BYTES, parse, previewMerge});
});
