#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monetization Module for AUTO-INCOME AI.
Evaluates monetization feasibility from Madagascar, pricing models,
net margin calculations, and payment rails (Payoneer, Crypto USDT, ComeUp, Gumroad, Ko-fi).
"""

from typing import Dict, Any, List


class MonetizationAdvisor:
    """Evaluates payment infrastructure, fees, and actionable cash-out for Madagascar."""

    CHANNELS: Dict[str, Dict[str, Any]] = {
        "binance_pay": {
            "name": "Binance Pay Direct (UID : 254779310)",
            "supports_madagascar": True,
            "readiness_score": 20.0,  # Max 20 points (0% frais, instantané)
            "fee_percent": 0.0,
            "min_payout_usd": 0.01,
            "payout_delay_days": 0,
            "binance_uid": "254779310",
            "seller_email": "compte.amidy001@gmail.com",
            "local_cashout": "Conversion P2P directe vers MVola (038 75 318 15) à Madagascar en 5 minutes",
            "required_setup": "Binance UID actif : 254779310 (Réception instantanée 0 frais)"
        },
        "mvola_direct": {
            "name": "MVola Direct Madagascar (038 75 318 15)",
            "supports_madagascar": True,
            "readiness_score": 20.0,
            "fee_percent": 0.0,
            "min_payout_usd": 1.0,
            "payout_delay_days": 0,
            "phone_number": "0387531815",
            "local_cashout": "Réception directe sur votre compte MVola 038 75 318 15",
            "required_setup": "Compte Telma MVola 038 75 318 15 (Jean)"
        },
        "crypto_usdt": {
            "name": "Crypto USDT (Binance P2P / Mobile Money)",
            "supports_madagascar": True,
            "readiness_score": 20.0,  # Max 20 points
            "fee_percent": 0.5,
            "min_payout_usd": 5.0,
            "payout_delay_days": 0,
            "local_cashout": "Vente directe P2P vers MVola ou Orange Money à Madagascar en 5 minutes",
            "required_setup": "Compte Binance ou TrustWallet avec adresse USDT TRC20"
        },
        "comeup": {
            "name": "ComeUp (ex-5euros) Microservices",
            "supports_madagascar": True,
            "readiness_score": 19.0,
            "fee_percent": 20.0,
            "min_payout_usd": 10.0,
            "payout_delay_days": 5,
            "local_cashout": "Virement bancaire direct vers Payoneer ou compte bancaire à Madagascar",
            "required_setup": "Profil vendeur ComeUp validé avec pièce d'identité"
        },
        "kofi": {
            "name": "Ko-fi Shop & Tips",
            "supports_madagascar": True,
            "readiness_score": 18.0,
            "fee_percent": 5.0,
            "min_payout_usd": 1.0,
            "payout_delay_days": 1,
            "local_cashout": "Liaison PayPal ou Stripe Express via Payoneer vers Madagascar",
            "required_setup": "Compte Ko-fi gratuit avec page de produit digital"
        },
        "payoneer": {
            "name": "Payoneer Global Payment",
            "supports_madagascar": True,
            "readiness_score": 18.0,
            "fee_percent": 2.0,
            "min_payout_usd": 20.0,
            "payout_delay_days": 2,
            "local_cashout": "Carte Mastercard internationale ou virement bancaire BNI/BOA/BMOI à Madagascar",
            "required_setup": "Compte Payoneer avec coordonnées bancaires virtuelles US/EU"
        },
        "gumroad": {
            "name": "Gumroad Digital Products",
            "supports_madagascar": True,
            "readiness_score": 16.0,
            "fee_percent": 10.0,
            "min_payout_usd": 10.0,
            "payout_delay_days": 7,
            "local_cashout": "Paiement direct hebdomadaire via compte bancaire ou Payoneer vers Madagascar",
            "required_setup": "Compte Gumroad gratuit avec produit téléchargeable publié"
        }
    }

    STRATEGY_DEFAULTS: Dict[str, Dict[str, Any]] = {
        "digital_product": {
            "target_client": "Professionnels indépendants, créateurs et étudiants internationaux",
            "acquisition_channel": "GitHub Pages, réseaux sociaux professionnels, forums thématiques",
            "delivery_process": "Téléchargement immédiat sécurisé après confirmation de paiement",
            "recommended_channel": "binance_pay",
            "backup_channel": "crypto_usdt",
            "benchmark_price_usd": 12.0
        },
        "microservice_gig": {
            "target_client": "Agences web, e-commerçants francophones et PME européennes",
            "acquisition_channel": "ComeUp, Fiverr, prospection B2B éthique",
            "delivery_process": "Livraison du livrable sous 24h avec révision incluse",
            "recommended_channel": "comeup",
            "backup_channel": "binance_pay",
            "benchmark_price_usd": 25.0
        },
        "seo_content": {
            "target_client": "Éditeurs de sites de niche et entreprises de marketing de contenu",
            "acquisition_channel": "Plateformes de rédaction ou vente directe aux éditeurs",
            "delivery_process": "Envoi du fichier Markdown optimisé avec métadonnées",
            "recommended_channel": "comeup",
            "backup_channel": "binance_pay",
            "benchmark_price_usd": 15.0
        },
        "b2b_prospects": {
            "target_client": "Startups et agences commerciales recherchant des leads B2B ciblés",
            "acquisition_channel": "Offre directe aux agences de prospection ou freelances",
            "delivery_process": "Fichier CSV / Excel nettoyé contenant données publiques conformes",
            "recommended_channel": "comeup",
            "backup_channel": "binance_pay",
            "benchmark_price_usd": 30.0
        },
        "micro_tool": {
            "target_client": "Développeurs, marketeurs et utilisateurs recherchant un outil simple",
            "acquisition_channel": "Hébergement gratuit sur GitHub Pages, diffusion sur forums tech",
            "delivery_process": "Application web 100% autonome accessible sans inscription",
            "recommended_channel": "binance_pay",
            "backup_channel": "kofi",
            "benchmark_price_usd": 0.0  # Gratuit avec dons / versions pro
        }
    }

    @classmethod
    def evaluate_opportunity_monetization(cls, category: str, custom_price: float = None) -> Dict[str, Any]:
        """Analyzes pricing, platform fee, target client, and cash-out route for Madagascar."""
        strategy = cls.STRATEGY_DEFAULTS.get(category, cls.STRATEGY_DEFAULTS["digital_product"])
        channel_key = strategy["recommended_channel"]
        channel_info = cls.CHANNELS.get(channel_key, cls.CHANNELS["crypto_usdt"])

        price = custom_price if custom_price is not None else strategy["benchmark_price_usd"]
        fee_amount = round(price * (channel_info["fee_percent"] / 100.0), 2)
        net_revenue = round(price - fee_amount, 2)

        return {
            "category": category,
            "target_client": strategy["target_client"],
            "acquisition_channel": strategy["acquisition_channel"],
            "delivery_process": strategy["delivery_process"],
            "recommended_channel": channel_key,
            "channel_name": channel_info["name"],
            "price_usd": price,
            "fee_usd": fee_amount,
            "net_revenue_usd": net_revenue,
            "madagascar_readiness_score": channel_info["readiness_score"],
            "local_cashout": channel_info["local_cashout"],
            "required_setup": channel_info["required_setup"],
            "payout_delay_days": channel_info["payout_delay_days"]
        }

    @classmethod
    def get_channel_readiness_score(cls, channel_key: str) -> float:
        """Returns readiness score (0-20 points) for scoring engine."""
        return cls.CHANNELS.get(channel_key, {}).get("readiness_score", 15.0)

    @classmethod
    def generate_monetization_checklist(cls, deliverable: Dict[str, Any]) -> List[str]:
        """Produces actionable, zero-cost steps for the user to start receiving income."""
        channel = deliverable.get("monetization_channel", "crypto_usdt")
        ch_data = cls.CHANNELS.get(channel, cls.CHANNELS["crypto_usdt"])

        if channel == "binance_pay":
            return [
                "1. Votre compte Binance Pay est déjà configuré : UID 254779310 (compte.amidy001@gmail.com).",
                f"2. Vos clients peuvent envoyer directement {deliverable.get('price_usd', 0.0)} $ sans aucuns frais sur votre Binance UID.",
                f"3. Encaissement immédiat à Madagascar : {ch_data['local_cashout']}.",
                "4. Les fonds reçus sont instantanément disponibles dans votre portefeuille Funding Binance."
            ]

        return [
            f"1. Canal de vente : {ch_data['name']} (Email vendeur : compte.amidy001@gmail.com).",
            f"2. Déposez ou publiez l'actif généré : '{deliverable.get('title')}' au prix suggéré de {deliverable.get('price_usd', 0.0)} $.",
            f"3. Mode d'encaissement à Madagascar : {ch_data['local_cashout']}.",
            "4. Règle du coût zéro : aucune commission n'est prélevée avant une vente confirmée."
        ]
