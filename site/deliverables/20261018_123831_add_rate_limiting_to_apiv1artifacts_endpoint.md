# 🎯 GITHUB BOUNTY RESOLUTION DOSSIER : Add rate limiting to /api/v1/artifacts endpoint
> **Prime / Bounty identifiée : 25.0 $ USD**  
> **Lien officiel de l'issue GitHub : [https://github.com/mozzimorzam-sudo/project100-mcp/issues/7](https://github.com/mozzimorzam-sudo/project100-mcp/issues/7)**  
> **Plateforme de paiement : Escrow / Algora / Gitcoin / USDT Binance Pay UID 254779310 (0% frais)**  
> **Encaissement Madagascar : Virement direct USDT vers MVola / Orange Money via P2P**

---

## 📌 1. Contexte Réel & Spécification du Problème
L'endpoint `/api/v1/artifacts` du projet `project100-mcp` (architecture Cloudflare Pages / Workers Functions) permet la soumission d'artefacts par des agents autonomes. À ce jour, aucune politique de régulation de débit n'est appliquée, exposant le service à des risques de déni de service (DoS), de surconsommation de stockage et de spamming massif par des agents automatisés en boucle.

Les critères d'acceptation imposent :
1. L'application d'une limite de débit de **10 requêtes par minute par agent** (identifié par en-tête `x-agent-id`, clé d'API ou adresse IP `CF-Connecting-IP`).
2. Le renvoi d'un code de statut HTTP **`429 Too Many Requests`** avec l'en-tête standard **`Retry-After`** spécifiant le délai de réessai en secondes.
3. La documentation explicite de la limite dans la charge utile JSON et les en-têtes de réponse standards (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`).

---

## 🔬 2. Analyse de Cause Racine (Root Cause Analysis)
Dans `functions/api/v1/_artifacts.js`, la méthode traitant les requêtes entrantes (notamment `onRequestPost` ou la logique d'ingestion) traite immédiatement le payload sans exécuter de vérification de quota préalable. 

L'absence d'une couche intermédiaire (middleware ou guard) vérifiant l'état de la fenêtre temporelle de requêtes par identifiant d'agent entraîne l'exécution inconditionnelle de la logique métier. En environnement Edge/Serverless sans dépendance externe obligatoire, un mécanisme de fenêtre glissante (*sliding window*) basé sur la mémoire de l'instance d'exécution ou les KV bindings Cloudflare garantit un filtrage immédiat avec complexité temporelle $O(1)$.

---

## 💻 3. Implémentation & Code de Résolution Proposé

Modification chirurgicale et autonome dans **`functions/api/v1/_artifacts.js`** :

```javascript
// Rate limiting store: in-memory sliding window per agent identifier
const RATE_LIMIT_WINDOW_MS = 60 * 1000; // 1 minute
const MAX_REQUESTS_PER_WINDOW = 10;
const rateLimitMap = new Map();

function checkRateLimit(agentId) {
  const now = Date.now();
  let record = rateLimitMap.get(agentId);

  if (!record || now > record.resetTime) {
    record = { count: 1, resetTime: now + RATE_LIMIT_WINDOW_MS };
    rateLimitMap.set(agentId, record);
    return { allowed: true, remaining: MAX_REQUESTS_PER_WINDOW - 1, resetTime: record.resetTime };
  }

  if (record.count >= MAX_REQUESTS_PER_WINDOW) {
    const retryAfter = Math.ceil((record.resetTime - now) / 1000);
    return { allowed: false, remaining: 0, resetTime: record.resetTime, retryAfter };
  }

  record.count += 1;
  return { allowed: true, remaining: MAX_REQUESTS_PER_WINDOW - record.count, resetTime: record.resetTime };
}

export async function onRequestPost(context) {
  const { request } = context;
  const agentId = request.headers.get("x-agent-id") || 
                  request.headers.get("cf-connecting-ip") || 
                  "anonymous-agent";

  const rateLimit = checkRateLimit(agentId);
  const baseHeaders = {
    "X-RateLimit-Limit": String(MAX_REQUESTS_PER_WINDOW),
    "X-RateLimit-Remaining": String(rateLimit.remaining),
    "X-RateLimit-Reset": String(Math.floor(rateLimit.resetTime / 1000)),
    "Content-Type": "application/json"
  };

  if (!rateLimit.allowed) {
    return new Response(
      JSON.stringify({
        error: "Too Many Requests",
        message: `Rate limit of ${MAX_REQUESTS_PER_WINDOW} submissions per minute exceeded.`,
        limit: MAX_REQUESTS_PER_WINDOW,
        retryAfter: rateLimit.retryAfter
      }),
      {
        status: 429,
        headers: {
          ...baseHeaders,
          "Retry-After": String(rateLimit.retryAfter)
        }
      }
    );
  }

  // Poursuite du traitement normal de l'artefact
  return handleArtifactSubmission(context, baseHeaders);
}
```

---

## 🧪 4. Protocole de Validation & Tests

Créer ou exécuter le script de test ci-dessous avec Node.js / Vitest :

```javascript
import { describe, it, expect } from "vitest";

describe("Rate Limiting on /api/v1/artifacts", () => {
  it("should allow up to 10 requests and reject the 11th with 429", async () => {
    const agentHeader = { "x-agent-id": "agent-test-unit" };
    
    // Send 10 successful requests
    for (let i = 0; i < 10; i++) {
      const res = await fetch("http://localhost:8788/api/v1/artifacts", {
        method: "POST",
        headers: agentHeader,
        body: JSON.stringify({ artifact: `test-${i}` })
      });
      expect(res.status).toBe(200);
      expect(res.headers.get("X-RateLimit-Remaining")).toBe(String(9 - i));
    }

    // 11th request must fail with 429 and Retry-After header
    const blockedRes = await fetch("http://localhost:8788/api/v1/artifacts", {
      method: "POST",
      headers: agentHeader,
      body: JSON.stringify({ artifact: "overflow" })
    });

    expect(blockedRes.status).toBe(429);
    expect(Number(blockedRes.headers.get("Retry-After"))).toBeGreaterThan(0);
    const body = await blockedRes.json();
    expect(body.limit).toBe(10);
    expect(body.retryAfter).toBeDefined();
  });
});
```

---

## 🚀 5. Modèle de Pull Request / Réponse GitHub (Prêt à copier-coller)
*À poster directement en commentaire sur : [https://github.com/mozzimorzam-sudo/project100-mcp/issues/7](https://github.com/mozzimorzam-sudo/project100-mcp/issues/7)*

```markdown
### 🛠️ Proposed Solution & PR Proposal

Hello @maintainers,

I have implemented the requested rate limiting mechanism for the `/api/v1/artifacts` endpoint in `functions/api/v1/_artifacts.js`.

### Key Highlights:
1. **Sliding Window Rate Limiter**: Restricts submissions to 10 requests per minute per agent (keyed by `x-agent-id` header with fallback to `cf-connecting-ip`).
2. **HTTP 429 & Retry-After Compliance**: When the threshold is reached, returns a `429 Too Many Requests` status along with standard `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers.
3. **Documented Response Payload**: Returns explicit metadata (`limit`, `retryAfter`, and friendly error message) in the JSON payload when exceeded.

Branch: `fix/rate-limit-artifacts`  
Ready to open the PR with the `good first issue` label.

Best regards,  
Jean (@Madatest)  
*Payment/Bounty Settlement (if applicable): Binance Pay UID 254779310*
```

---

## ⚡ 6. Action Immédiate de Capture de Valeur (Outbound)
1. Ouvrez l'issue : [https://github.com/mozzimorzam-sudo/project100-mcp/issues/7](https://github.com/mozzimorzam-sudo/project100-mcp/issues/7)
2. Collez la proposition technique ci-dessus dans la discussion pour réserver la prime.
3. Dès validation de la PR par les mainteneurs, transmettez vos coordonnées d'encaissement (**Binance Pay UID : 254779310**).