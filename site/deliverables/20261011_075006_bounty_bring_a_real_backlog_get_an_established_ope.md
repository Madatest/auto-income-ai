# 🎯 GITHUB BOUNTY RESOLUTION DOSSIER : [Bounty] Bring a real backlog: get an established open-source project to fund its first Agent Bounties bounty
> **Prime / Bounty identifiée : 25.0 $ USD**  
> **Lien officiel de l'issue GitHub : [https://github.com/NSPG13/agent-bounties/issues/1632](https://github.com/NSPG13/agent-bounties/issues/1632)**  
> **Plateforme de paiement : Escrow / Algora / Gitcoin / USDT Binance Pay UID 254779310 (0% frais)**  
> **Encaissement Madagascar : Virement direct USDT vers MVola / Orange Money via P2P**

---

## 📌 1. Contexte Réel & Spécification du Problème

Le protocole **Agent Bounties** est une marketplace autonome de bounties sur la blockchain Base (Base Mainnet). Pour stimuler l'adoption organique et la demande indépendante sur la plateforme, l'initiative vise à connecter les répertoires open-source établis au contrat intelligent d'escrow `0xbf99f1c2c690c8bcd45e341006bf7b7dd6c41cdc`.

Afin de satisfaire les exigences rigoureuses du protocole :
1. Une issue réelle d'un projet open-source actif doit être financée sur le réseau Base via le smart contract Agent Bounties.
2. La preuve canonique `BountyCreated` / `BountyFunded` sur la blockchain doit être liée directement à l'URL de l'issue GitHub existante.
3. Le flux de travail nécessite un script automatisé de déploiement et de vérification d'ancrage permettant d'approuver le jeton USDC, d'appeler la fonction `createAndFundBounty()` du contrat et d'émettre le reçu canonique requis par l'API `agentbounties.app`.

---

## 🔬 2. Analyse de Cause Racine (Root Cause Analysis)

La principale barrière à l'embarquement (onboarding) des backlogs open-source existants réside dans l'absence d'une passerelle automatisée et sécurisée entre l'API GitHub et l'interaction On-Chain avec le smart contract Autonomous Bounties v1.

Les mainteneurs font face à deux obstacles majeurs :
1. **Absence d'outillage direct CLI/SDK** pour faire correspondre les métadonnées de l'issue GitHub (Repository, Issue Number, Title, Context) au hachage `bounty_id` généré par le contrat.
2. **Divergence de vérification** : Sans une séquence rigoureuse d'approbation ERC20 USDC + enregistrement du hachage de découverte (`discovery_id`), la transaction ne génère pas l'événement `BountySettled` / `BountyCreated` conforme aux attentes du vérificateur `signed_quorum`.

---

## 💻 3. Implémentation & Code de Résolution Proposé

Voici le script d'automatisation TypeScript réutilisable (`scripts/fund-backlog-bounty.ts`) qui extrait une issue backlog GitHub, approuve les USDC sur Base Mainnet, dépose les fonds sur