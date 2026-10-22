# 🎯 GITHUB BOUNTY RESOLUTION DOSSIER : [routes] Time, moving time and speed
> **Prime / Bounty identifiée : 25.0 $ USD**  
> **Lien officiel de l'issue GitHub : [https://github.com/amiller/bounty-arcade/issues/12](https://github.com/amiller/bounty-arcade/issues/12)**  
> **Plateforme de paiement : Escrow / Algora / Gitcoin / USDT Binance Pay UID 254779310 (0% frais)**  
> **Encaissement Madagascar : Virement direct USDT vers MVola / Orange Money via P2P**

---

## 📌 1. Contexte Réel & Spécification du Problème

Dans l'application `apps/routes` du monorepo `bounty-arcade`, l'analyse de fichiers GPX gère actuellement le calcul de la distance et du tracé des points, mais ignore les métadonnées temporelles contenues dans les balises `<time>` des points de trace GPX (`<trkpt>`).

La spécification exige :
1. **Parser GPX** : Extraire la balise `<time>` de chaque point en millisecondes depuis l'époque UNIX (`Date.parse()`). Si un point n'a pas de balise `<time>`, la propriété `time` **ne doit pas exister** sur l'objet point (pour éviter d'échouer les tests d'égalité stricte d'objets `deep-compare`).
2. **Fonction pure `timing(points)`** :
   - Calcule `{ elapsed, moving, avgSpeed }`.
   - Si **un seul** point ne possède pas la propriété `time`, retourne `{ elapsed: null, moving: null, avgSpeed: null }`.
   - `elapsed` : Durée totale en ms (`points[last].time - points[0].time`).
   - `moving` : Somme des intervalles de temps (en ms) entre deux points consécutifs où la vitesse instantanée est $\ge 0.5\text{ m/s}$.
   - `avgSpeed` : Distance totale enregistrée divisée par le temps en mouvement (`moving / 1000`) en m/s.
3. **Formatage `formatDuration(ms)`** :
   - Formate une durée ms en chaîne `h:mm:ss` (ex: `3723000` $\rightarrow$ `'1:02:03'`).
   - Retourne `'—'` (cadratin `\u2014`) si la valeur est `null` ou `undefined`.
4. **Interface Utilisateur (DOM)** :
   - Afficher le temps écoulé et le temps en mouvement dans deux nouvelles cellules HTML `#stat-elapsed` et `#stat-moving`.

---

## 🔬 2. Analyse de Cause Racine (Root Cause Analysis)

1. **Absence de parsing temporel dans le parseur GPX** : Le parseur de l'application filtrait les balises `<ele>`, `<lat>`, `<lon>` sans extraire le nœud enfants `<time>`.
2. **Absence d'omission conditionnelle de clé** : L'assignation naïve `time: parseTime(...)` ajouterait `time: undefined` si la balise est absente, ce qui viole `deepEqual` / `toEqual` dans les tests d'intégration existants qui vérifient la structure brute des points sans champ `time`.
3. **Absence des sélecteurs de métriques temporelles dans le DOM** : Les cellules de statistiques `#stat-elapsed` et `#stat-moving` n'existaient pas dans `index.html` ni dans la logique d'actualisation des statistiques lors du chargement de tracé.

---

## 💻 3. Implémentation & Code de Résolution Proposé

### Patch dans `apps/routes/src/utils.js` (ou `routes.js`)

```javascript
// --- GPX Parser snippet & timing utilities ---

export function parseGPXPoint(node) {
  const lat = parseFloat(node.getAttribute('lat'));
  const lon = parseFloat(node.getAttribute('lon'));
  const pt = { lat, lon };

  const timeNode = node.querySelector('time');
  if (timeNode && timeNode.textContent) {
    const parsed = Date.parse(timeNode.textContent.trim());
    if (!isNaN(parsed)) {
      pt.time = parsed;
    }
  }
  return pt;
}

export function formatDuration(ms) {
  if (ms === null || ms === undefined) return '—';
  const totalSec = Math.floor(ms / 1000);
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

export function timing(points) {
  if (!points || points.length === 0) {
    return { elapsed: null, moving: null, avgSpeed: null };
  }
  for (const p of points) {
    if (typeof p.time !== 'number') {
      return { elapsed: null, moving: null, avgSpeed: null };
    }
  }

  const elapsed = points[points.length - 1].time - points[0].time;
  let moving = 0;
  let totalDist = 0;

  for (let i = 0; i < points.length - 1; i++) {
    const d = haversine(points[i], points[i + 1]);
    const dt = (points[i + 1].time - points[i].time) / 1000; // seconds
    totalDist += d;
    if (dt > 0) {
      const speed = d / dt; // m/s
      if (speed >= 0.5) {
        moving += dt * 1000; // ms
      }
    }
  }

  const avgSpeed = moving > 0 ? totalDist / (moving / 1000) : 0;
  return { elapsed, moving, avgSpeed };
}

export function updateStatsUI(points) {
  const stats = timing(points);
  const elElapsed = document.getElementById('stat-elapsed');
  const elMoving = document.getElementById('stat-moving');
  if (elElapsed) elElapsed.textContent = formatDuration(stats.elapsed);
  if (elMoving) elMoving.textContent = formatDuration(stats.moving);
}
```

### Ajout dans `apps/routes/index.html`

```html
<td id="stat-elapsed">—</td>
<td id="stat-moving">—</td>
```

---

## 🧪 4. Protocole de Validation & Tests

Pour exécuter le vérificateur automatisé fourni par le dépôt (`bounties/routes-time/check.yml`) :

```bash
# Lancement de la suite de vérification officielle Bounty Arcade
node check.mjs bounties/routes-time/check.yml
```

### Test unitaire JS (`timing.test.js`)

```javascript
import { timing, formatDuration } from './utils.js';

// Test 1: Format duration
console.assert(formatDuration(3723000) === '1:02:03', 'formatDuration 3723000');
console.assert(formatDuration(null) === '—', 'formatDuration null');

// Test 2: Missing time property
const missingTimePts = [{ lat: 0, lon: 0, time: 0 }, { lat: 0, lon: 0.001 }];
console.assert(timing(missingTimePts).elapsed === null, 'Missing time returns null');

// Test 3: Stops excluded & avgSpeed calculation
const p1 = { lat: 0, lon: 0, time: Date.UTC(2026, 0, 1, 0, 0, 0) };
const p2 = { lat: 0, lon: 0.001, time: Date.UTC(2026, 0, 1, 0, 1,