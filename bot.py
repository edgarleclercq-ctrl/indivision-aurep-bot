"""
Bot Telegram de révision AUREP CCP - L'indivision et le partage
3 modes : Fiches flash / QCM interactif / Simulateur liquidatif
"""

import os
import json
import random
import asyncio
import logging
from datetime import time
from anthropic import Anthropic

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# CONFIG — à renseigner dans les variables d'environnement
# ─────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
YOUR_CHAT_ID = os.environ.get("YOUR_CHAT_ID", "")   # ton chat_id Telegram personnel

client = Anthropic(api_key=ANTHROPIC_API_KEY)

# ─────────────────────────────────────────────
# BASE DE CONNAISSANCE — synthèse du cours AUREP
# ─────────────────────────────────────────────
COURS_AUREP = """
Tu es un professeur expert en droit patrimonial français, spécialisé dans la préparation 
au certificat CCP AUREP. Tu maîtrises parfaitement le cours "L'indivision et le partage" 
(aspects civils et fiscaux) de Cécilia Broto.

=== STRUCTURE DU COURS ===

PARTIE I — INDIVISION LÉGALE
1. Naissance : recherchée (concubins, partenaires, époux SDB, famille) ou subie (post-communautaire, post-successorale)
2. Gestion :
   - Actes conservatoires : un seul indivisaire suffit (art 815-2 CC) — éviter tout péril
   - Actes d'administration : majorité des 2/3 en valeur (art 815-3 CC) — baux d'habitation, mandat de gestion
   - Actes de disposition : UNANIMITÉ (art 815-3 CC) — vente, hypothèque, baux commerciaux/ruraux
   - Exception vente judiciaire : 2/3 peuvent demander autorisation au juge (art 815-5-1 CC)
3. Droits des indivisaires :
   - Droit au partage (art 815 CC) — imprescriptible, principe fondamental
   - Droit d'usage commun ou privatif (art 815-9 CC)
   - Indemnité d'occupation si usage privatif — même sans occupation effective (Cass 2017)
     Valorisation : valeur locative avec abattement 15-30% — prescription 5 ans
   - Droit aux revenus (art 815-10 CC) — répartition annuelle
   - Droit de céder ses droits indivis (art 815-14 CC) — droit de préemption des coïndivisaires
4. Fin de l'indivision :
   - Sursis judiciaire : 2 ans max (art 820 CC)
   - Maintien judiciaire : 5 ans renouvelables (art 821 CC) — conjoint survivant ou descendants mineurs
   - Attribution éliminatoire (art 824 CC)
   - Attribution préférentielle (art 831 CC) — DE DROIT pour le conjoint survivant
     Conjoint : de droit / Partenaire : si prévu par testament / Concubin : NON

PARTIE II — INDIVISION CONVENTIONNELLE
- Conditions : consentement unanime, écrit obligatoire (nullité sinon), désignation des biens + quotes-parts
- Durée déterminée : max 5 ans renouvelable (art 1873-3 CC)
- Durée indéterminée : partage possible à tout moment sauf mauvaise foi
- Gérant : pouvoirs = époux en régime légal / pas d'hypothèque / pas de bail rural
- Coût notarié : émolument proportionnel + taxe fixe 125€ + CSI 0,1%

PARTIE III — LIQUIDATION CIVILE

MÉTHODE LIQUIDATIVE (à appliquer dans l'ordre) :
1. Qualifier la dépense (conservation / amélioration / somptuaire / entretien)
2. Qualifier la créance (contre l'indivision art 815-13 CC ou entre indivisaires)
3. Vérifier la prescription (5 ans art 2224 CC — SUSPENDUE entre époux/partenaires art 2236 CC — PAS de suspension pour concubins)
4. Neutralisation par contribution aux charges (résidence principale/secondaire uniquement)
5. Calculer

QUALIFICATION DES CRÉANCES :
→ Dépenses d'acquisition = créance ENTRE indivisaires (pas contre l'indivision — Cass 26 mai 2021)
   Époux : profit subsistant (art 1469 CC) / Partenaires : profit subsistant (art 515-7 CC) / Concubins : NOMINAL (art 1895 CC)

→ Dépenses nécessaires à la conservation (art 815-13 CC) = créance CONTRE l'indivision
   Calcul : PLUS FORTE des 2 sommes entre dépense faite ET profit subsistant
   Inclut : remboursement mensualités prêt, taxe foncière, taxe habitation (Cass 2019), charges copropriété, assurance
   Remboursement anticipé = dépense nécessaire (avis Cass 5 juillet 2023)
   RÈGLE DE TROIS pour le prêt : (mensualités payées / financement global) × valeur actuelle

→ Dépenses d'amélioration (art 815-13 CC) = créance CONTRE l'indivision
   Calcul : PROFIT SUBSISTANT uniquement (plus-value apportée)
   NB : industrie personnelle (bricolage) = AUCUNE créance sur ce fondement

→ Dépenses somptuaires = PAS d'indemnisation
→ Dépenses d'entretien = indemnisation SAUF si l'indivisaire occupe privativement

OCCUPATION PRIVATIVE :
→ Due même sans occupation effective
→ Non due si : convention contraire, décision judiciaire gratuite, héritier saisi, locataire en place
→ Indemnité accroît à la MASSE indivise (pas aux coïndivisaires directement)
→ Prescription 5 ans

PARTIE III — LIQUIDATION FISCALE

PARTAGE DROIT COMMUN (art 747 CGI) :
- Partage pur et simple : droit de partage 2,5% sur actif NET (actif brut - passif)
- Partage avec soulte : droit de partage 2,5% sur actif net - soultes + DMTO (droits de vente ~5,80%) sur les soultes

PARTAGE RÉGIME DE FAVEUR (art 748 CGI) — CONDITIONS :
1. Origine : succession, communauté conjugale, biens époux/partenaires, donation-partage
2. Qualité : membres originaires, conjoint, ascendants, descendants, AUTu

→ Succession : 2,5% sur actif net SANS déduction des soultes (pas de DMTO sur soultes)
→ Divorce / rupture PACS : 1,1% sur actif net SANS déduction des soultes
   ⚠️ 1,1% s'applique APRÈS divorce définitif / rupture PACS — PAS aux concubins — PAS aux licitations

LICITATION :
- Droit commun (art 750-I CGI) : DMTO 5,80% ou 6,31% sur parts acquises
- Régime de faveur (art 750-II CGI) : 2,5% sur parts acquises (succession/communauté/époux-partenaires)

JURISPRUDENCE CLÉS À CONNAÎTRE :
- Cass 26 mai 2021 : apport en capital = créance entre indivisaires (pas contre indivision)
- Cass 5 juillet 2023 : remboursement anticipé = dépense nécessaire art 815-13
- Cass 20 oct 2021 : prise en charge par assurance emprunteur = pas de créance pour l'assuré
- Cass 1re civ 2019 : taxe d'habitation = dépense nécessaire art 815-13
- Cass 10 sept 2025 : légataire universel ≠ indivision avec réservataires (legs réductible en valeur)
- Cass 23 jan 2025 : congé pour vendre = acte de disposition → unanimité requise
- Cass 26 mars 2025 : cession d'actions communes indivises → accord des deux ex-époux requis
"""

# ─────────────────────────────────────────────
# FICHES FLASH — 20 fiches calibrées AUREP
# ─────────────────────────────────────────────
FICHES = [
    {
        "titre": "🔵 Actes conservatoires — Art 815-2 CC",
        "contenu": (
            "Un seul indivisaire peut agir SEUL pour éviter tout péril (depuis 2006, "
            "plus besoin de péril imminent).\n\n"
            "✅ Exemples : réparations toiture, commandement de payer, action en paiement "
            "indemnité d'occupation, souscription assurance\n\n"
            "💰 Financement : fonds indivis qu'il détient → à défaut oblige les autres → "
            "à défaut provision judiciaire\n\n"
            "⚠️ Piège exam : la constitution d'hypothèque pour financer des travaux ≠ acte "
            "conservatoire → UNANIMITÉ requise"
        ),
        "question": "Jean, seul dans l'indivision, veut faire un ravalement de façade ET constituer une hypothèque. Que peut-il faire seul ?"
    },
    {
        "titre": "🔵 Actes d'administration — Art 815-3 CC",
        "contenu": (
            "Majorité des 2/3 calculée en VALEUR (pas en têtes).\n\n"
            "✅ Possibles à 2/3 : mandat de gestion, vente meubles pour payer passif, "
            "baux d'habitation, action en bornage\n\n"
            "❌ Impossibles même à 2/3 : baux commerciaux/artisanaux/ruraux, "
            "vente immeuble (sauf art 815-5-1)\n\n"
            "⚠️ Obligation d'informer les minoritaires sinon INOPPOSABLE à eux\n\n"
            "📌 Art 815-5-1 : les 2/3 PEUVENT demander en justice l'autorisation de vendre "
            "si refus abusif → vente par licitation"
        ),
        "question": "Anna (40%), Alma (35%) et Audrey (25%) veulent donner un appartement en location. Peuvent-elles le faire sans Adrien (0%) ? Que faut-il faire ?"
    },
    {
        "titre": "🔵 Unanimité — Art 815-3 al.3 CC",
        "contenu": (
            "UNANIMITÉ obligatoire pour :\n"
            "• Tous actes de disposition (vente immeuble, hypothèque)\n"
            "• Baux commerciaux, artisanaux, ruraux\n"
            "• Renouvellement ou refus de renouvellement de ces baux\n"
            "• Congé pour vendre (= acte de disposition — Cass 23 jan 2025)\n\n"
            "Sanction du défaut d'unanimité : NULLITÉ RELATIVE (pas nullité absolue)\n\n"
            "⚠️ Exception : vente judiciaire possible sur demande des 2/3 (art 815-5-1 CC)"
        ),
        "question": "Un ex-époux cède seul les actions communes devenues indivises après divorce. Quelle est la sanction ? (Cass 26 mars 2025)"
    },
    {
        "titre": "🟡 Indemnité d'occupation — Art 815-9 CC",
        "contenu": (
            "Due dès que l'occupation est PRIVATIVE (l'indivisaire empêche les autres d'user du bien).\n\n"
            "✅ Due même si : pas d'occupation effective, bien vétuste, titre judiciaire\n"
            "❌ Pas due si : convention contraire écrite, décision judiciaire gratuite, "
            "héritier saisi (saisine successorale), locataire en place\n\n"
            "💰 Valorisation : valeur locative avec abattement 15-30% (précarité du statut)\n"
            "📅 Prescription : 5 ans (assimilée aux fruits et revenus)\n"
            "⚖️ Accroît à la MASSE indivise (pas directement aux coïndivisaires)"
        ),
        "question": "Antoine continue d'occuper l'appartement indivis après le décès de sa concubine Iris. Doit-il une indemnité d'occupation ? À partir de quand ?"
    },
    {
        "titre": "🟡 Créance d'acquisition — Cass 26 mai 2021",
        "contenu": (
            "Un indivisaire qui finance la PART DE L'AUTRE lors de l'acquisition :\n"
            "→ C'est une créance ENTRE INDIVISAIRES (pas contre l'indivision)\n"
            "→ Art 815-13 CC NE s'applique PAS aux dépenses d'acquisition\n\n"
            "💰 Valorisation selon le statut du couple :\n"
            "• Époux séparés de biens → profit subsistant (art 1469 CC)\n"
            "• Partenaires PACS → profit subsistant (art 515-7 CC → 1469 CC)\n"
            "• Concubins → NOMINAL (art 1895 CC) — pas de revalorisation !\n\n"
            "⚠️ Grande différence pratique : le concubin perd la revalorisation"
        ),
        "question": "Antoine (concubin) a apporté 50 000€ dont 25 000€ pour la part d'Iris lors de l'achat à 200 000€. L'immeuble vaut 240 000€ au partage. Quelle est la créance d'Antoine ?"
    },
    {
        "titre": "🟡 Dépenses nécessaires à la conservation — Art 815-13 CC",
        "contenu": (
            "Créance CONTRE L'INDIVISION\n\n"
            "Inclut :\n"
            "• Remboursement mensualités prêt (au-delà de sa quote-part)\n"
            "• Remboursement anticipé (avis Cass 5 juil 2023)\n"
            "• Taxe foncière (Cass 2019)\n"
            "• Taxe d'habitation (Cass 2019)\n"
            "• Charges de copropriété non récupérables\n"
            "• Assurance habitation\n\n"
            "💰 Calcul : PLUS FORTE des 2 sommes entre :\n"
            "→ la dépense faite (nominal)\n"
            "→ le profit subsistant (revalorisation)\n\n"
            "Règle de trois pour le prêt : (mensualités payées / coût global financement) × valeur actuelle"
        ),
        "question": "Iris a remboursé 20 000€ de mensualités sur un prêt de 100 000€. L'immeuble acheté 200 000€ vaut aujourd'hui 240 000€. Calculez la créance d'Iris contre l'indivision."
    },
    {
        "titre": "🟡 Dépenses d'amélioration — Art 815-13 al.1 CC",
        "contenu": (
            "Créance CONTRE L'INDIVISION\n\n"
            "💰 Calcul : PROFIT SUBSISTANT uniquement\n"
            "= différence entre valeur actuelle et valeur qu'aurait eu le bien sans la dépense\n\n"
            "⚠️ Règles importantes :\n"
            "• Industrie personnelle (bricolage, travail manuel) → PAS indemnisable sur ce fondement\n"
            "• Matériaux achetés → indemnisables (dépense en argent)\n"
            "• Dépenses somptuaires → JAMAIS indemnisées\n"
            "• Dépenses d'entretien → indemnisées SAUF si l'occupant privatif les a faites"
        ),
        "question": "Un indivisaire a refait entièrement la cuisine (matériaux + sa main d'œuvre) pour 15 000€. La valeur du bien a augmenté de 10 000€ grâce à ces travaux. Quelle est sa créance ?"
    },
    {
        "titre": "🟡 Prescription des créances d'indivision",
        "contenu": (
            "Règle générale : 5 ans (art 2224 CC) à compter de l'exigibilité\n\n"
            "Point de départ pour les mensualités : chaque échéance acquittée\n\n"
            "SUSPENSION :\n"
            "✅ Entre époux → suspendue pendant toute la durée du mariage (art 2236 CC)\n"
            "✅ Entre partenaires → suspendue pendant le PACS (art 2236 CC)\n"
            "❌ Entre concubins → PAS de suspension ! Risque de prescription en cours de vie commune\n\n"
            "⚠️ Conséquence pratique : le concubin solvens doit agir pendant la vie commune "
            "ce qui est irréaliste → piège fréquent à l'examen"
        ),
        "question": "Antoine et Iris sont concubins depuis 2018. Antoine a remboursé des mensualités depuis 2018. Ils se séparent en 2026. Quelles mensualités peut-il réclamer ?"
    },
    {
        "titre": "🟢 Partage — Formes et effet déclaratif",
        "contenu": (
            "2 formes :\n"
            "• Amiable (art 835 CC) : accord unanime, notaire obligatoire si immeubles\n"
            "• Judiciaire (art 840 CC) : si désaccord ou incapacité\n\n"
            "EFFET DÉCLARATIF (art 883 CC) :\n"
            "Chaque copartageant est censé avoir succédé directement depuis l'ouverture de l'indivision\n"
            "→ Rétroactivité au décès (pour succession) ou à la dissolution (pour communauté)\n\n"
            "⚠️ Limites de la rétroactivité :\n"
            "• Biens évalués au JOUR DU PARTAGE (pas au décès)\n"
            "• Fruits répartis à parts égales (pas reversés en totalité à l'attributaire)\n"
            "• Actes judiciaires conservent leurs effets (art 883 al.2)"
        ),
        "question": "Alex consent seul une hypothèque sur l'immeuble de Nice pendant l'indivision. L'immeuble est ensuite attribué à Anna au partage. L'hypothèque est-elle opposable à Anna ?"
    },
    {
        "titre": "🟢 Attribution préférentielle — Art 831 CC",
        "contenu": (
            "Qui peut en bénéficier ?\n"
            "✅ Conjoint survivant → DE DROIT (art 831-3 CC)\n"
            "✅ Partenaire survivant → si prévu par TESTAMENT\n"
            "❌ Concubin survivant → JAMAIS\n\n"
            "Objet : logement principal, local professionnel, entreprise, véhicule nécessaire\n\n"
            "Soulte éventuelle : le conjoint peut demander des délais jusqu'à 10 ans pour la moitié\n\n"
            "⚠️ Jurisprudence Cass 10 sept 2025 : pas d'attribution préférentielle pour le légataire "
            "universel (le legs est réductible en VALEUR, pas en nature → pas d'indivision)"
        ),
        "question": "Après le décès de son compagnon, une concubine souhaite garder le logement familial indivis. Peut-elle demander l'attribution préférentielle ?"
    },
    {
        "titre": "🟢 Partage fiscal — Droit commun vs Régime de faveur",
        "contenu": (
            "DROIT COMMUN (art 747 CGI) :\n"
            "• Partage pur et simple : 2,5% sur actif NET\n"
            "• Partage avec soulte : 2,5% sur (actif net - soultes) + DMTO 5,80% sur soultes\n\n"
            "RÉGIME DE FAVEUR (art 748 CGI) :\n"
            "Conditions : origine = succession / communauté / époux-partenaires / donation-partage\n"
            "ET qualité = membres originaires, conjoint, ascendants, descendants\n\n"
            "→ Succession : 2,5% sur actif net SANS déduction soultes (pas de DMTO)\n"
            "→ Divorce / rupture PACS : 1,1% sur actif net SANS déduction soultes\n\n"
            "⚠️ Le 1,1% NE s'applique PAS aux : concubins / licitations / avant divorce définitif"
        ),
        "question": "Alexandre et Élodie (concubins) partageaient un bien indivis 50/50. Valeur : 400 000€. Passif restant : 300 000€. Élodie récupère tout et verse une soulte. Calculez la fiscalité."
    },
    {
        "titre": "🟢 Licitation fiscale — Art 750 CGI",
        "contenu": (
            "DROIT COMMUN (art 750-I CGI) :\n"
            "• Licitation à un TIERS : DMTO 5,80% sur totalité du prix\n"
            "• Licitation à un INDIVISAIRE : DMTO 5,80% sur les PARTS ACQUISES\n"
            "(même si l'indivision est successorale → le droit fiscal requalifie en vente)\n\n"
            "RÉGIME DE FAVEUR (art 750-II CGI) :\n"
            "Conditions identiques à l'art 748 CGI\n"
            "→ Taux : 2,5% sur les parts acquises\n"
            "→ Si met fin à l'indivision : 2,5% sur valeur totale du bien (sans déduire part acquéreur)\n\n"
            "⚠️ Bercy 2022 : le taux 1,1% NE s'étend PAS aux licitations (toujours 2,5% minimum)"
        ),
        "question": "Élodie rachète la part d'Alexandre (bien 400 000€, passif 300 000€, parts 50/50). En licitation plutôt qu'en partage, quel est le coût fiscal total ?"
    },
    {
        "titre": "🔴 Indivision conventionnelle — Conditions et durée",
        "contenu": (
            "CONDITIONS DE VALIDITÉ :\n"
            "• Consentement UNANIME (art 1873-2 CC)\n"
            "• ÉCRIT obligatoire à peine de nullité\n"
            "• Acte notarié si immeubles (publicité foncière)\n"
            "• Mentions obligatoires : désignation des biens + quotes-parts\n\n"
            "DURÉE :\n"
            "• Déterminée : max 5 ans renouvelable à l'unanimité\n"
            "• Indéterminée : partage possible à tout moment sauf mauvaise foi / contretemps\n\n"
            "COÛT (si notariée) :\n"
            "• Émolument proportionnel (voir tableau tranches)\n"
            "• Taxe fixe 125€ + CSI 0,1% sur valeur biens\n\n"
            "Novation en durée indéterminée : révocation gérant / décès d'un indivisaire sans prévision"
        ),
        "question": "Des héritiers veulent maintenir l'indivision sur une maison de famille estimée à 500 000€ pendant 5 ans. Quelles sont les conditions ? Quel est le coût approximatif ?"
    },
    {
        "titre": "🔴 Gérant de l'indivision conventionnelle — Art 1873-6 CC",
        "contenu": (
            "Nomination : unanimité des indivisaires\n\n"
            "POUVOIRS : référence aux pouvoirs d'un époux en régime légal\n"
            "✅ Peut faire seul : gestion courante, baux habitation, entretien, exploitation fonds de commerce\n"
            "❌ Ne peut pas : aliéner immeuble, constituer hypothèque, bail rural, bail commercial\n\n"
            "La convention peut LIMITER ses pouvoirs mais PAS les étendre (clause extensive = non écrite)\n\n"
            "Exception incapable : ne peut pas conclure de bail avec droit au renouvellement\n\n"
            "Rémunération : librement fixée par les indivisaires (sans lui s'il est indivisaire)\n"
            "Responsabilité : comme un mandataire (faute de gestion)"
        ),
        "question": "Le gérant d'une indivision conventionnelle veut donner un appartement indivis à bail commercial. La convention lui donne mandat général d'administration. Peut-il agir seul ?"
    },
    {
        "titre": "🔴 Obstacles au partage — Sursis et maintien judiciaire",
        "contenu": (
            "SURSIS AU PARTAGE (art 820 CC) :\n"
            "• Demande d'un indivisaire\n"
            "• Durée max : 2 ANS\n"
            "• Motifs : atteinte à la valeur des biens / incapacité à reprendre une entreprise\n\n"
            "MAINTIEN JUDICIAIRE (art 821 CC) :\n"
            "• Durée : 5 ans renouvelables\n"
            "• Bénéficiaires : descendants MINEURS / conjoint survivant (si copropriétaire)\n"
            "• Porte sur : logement, local pro, entreprise exploitée par le défunt\n"
            "• Pour les mineurs : jusqu'à majorité du plus jeune\n"
            "• Pour le conjoint : jusqu'à son décès\n\n"
            "ATTRIBUTION ÉLIMINATOIRE (art 824 CC) :\n"
            "• Le juge attribue sa part à celui qui veut sortir\n"
            "• En nature ou en numéraire (prélevé sur l'indivision en priorité)"
        ),
        "question": "À la suite du décès de leur père, 3 enfants sont en indivision. Le plus jeune enfant a 12 ans. La mère (conjoint survivant) veut rester dans le logement familial. Quels mécanismes peut-elle invoquer ?"
    },
    {
        "titre": "🔴 Droit de préemption — Art 815-14 CC",
        "contenu": (
            "S'applique uniquement pour cession à titre ONÉREUX à un TIERS\n\n"
            "PROCÉDURE OBLIGATOIRE :\n"
            "1. Notification par acte EXTRAJUDICIAIRE (impératif)\n"
            "2. Mention : prix, conditions, identité/adresse/qualité de l'acquéreur\n"
            "3. Délai : 1 mois pour exercer le droit de préemption (par acte extrajudiciaire)\n\n"
            "Sanction si formalisme non respecté : NULLITÉ (art 815-16 CC)\n\n"
            "⚠️ Distinctions importantes :\n"
            "• Cession à un INDIVISAIRE → analysée comme PARTAGE (art 883 CC)\n"
            "• Cession d'une fraction de ses droits → VENTE (reste indivisaire)\n"
            "• Cession à un tiers → VENTE + droit de préemption"
        ),
        "question": "Arnaud, Alex et Anna sont en indivision à 1/3 chacun. Arnaud cède tous ses droits à Anna. Est-ce un partage ou une vente ? Y a-t-il droit de préemption ?"
    },
    {
        "titre": "🔴 Masse indivise — Composition et autonomie",
        "contenu": (
            "La masse indivise comprend :\n"
            "• Les biens indivis eux-mêmes\n"
            "• Les fruits et revenus (art 815-10 CC)\n"
            "• Les biens subrogés (prix de vente réemployé — si accord tous indivisaires)\n"
            "• Les créances de l'indivision\n"
            "• Les dettes et charges de l'indivision\n"
            "• Le compte d'indivision (créances/dettes de chaque indivisaire)\n\n"
            "⚠️ Autonomie SANS personnalité juridique :\n"
            "• Pas de capacité juridique propre\n"
            "• Actes au nom de chaque indivisaire ou d'un mandataire commun\n\n"
            "DIFFÉRENCE AVEC DÉMEMBREMENT : usufruitier + nu-propriétaire ≠ indivision "
            "(droits de nature différente — Cass 1993)"
        ),
        "question": "M. Duterte décède en laissant maison Toulouse, immeuble Biarritz (vendu en 2023, prix réemployé en appartement Bordeaux), portefeuille titres, compte courant, meubles, tableau légué à Ana. Quelle est la masse indivise au 1er janvier 2024 ?"
    },
    {
        "titre": "🔴 Contestation du partage — Nullité et lésion",
        "contenu": (
            "NULLITÉ (art 887 CC) :\n"
            "• Omission d'un copartageant (alternative : recevoir sa part en nature ou valeur)\n"
            "• Vices du consentement : violence, dol, ERREUR (si porte sur existence/quotité des droits)\n"
            "⚠️ L'erreur sur la VALEUR des lots ≠ cause de nullité (Cass 2018)\n"
            "Alternative à la nullité : partage complémentaire ou rectificatif\n\n"
            "LÉSION — Action en complément de part (art 889 CC) :\n"
            "• Remplace l'ancienne rescision\n"
            "• Condition : lésion de plus du QUART (lot < 3/4 de ce qu'il aurait dû recevoir)\n"
            "• Complément en nature ou en valeur\n"
            "• Prescription : 2 ANS à compter du partage\n"
            "• Omission d'un bien → partage complémentaire (art 892 CC) — IMPRESCRIPTIBLE"
        ),
        "question": "Lors du partage successoral, un copartageant réalise 3 ans après que son lot était sous-évalué de 30%. Peut-il agir ? Sur quel fondement ?"
    },
    {
        "titre": "🟠 Indivision post-communautaire vs post-successorale",
        "contenu": (
            "POST-COMMUNAUTAIRE :\n"
            "• Naissance : dissolution du régime (divorce, décès, changement régime)\n"
            "• En cas de divorce : naissance au prononcé du divorce\n"
            "• En cas de décès : naissance au décès\n"
            "• Parties : ex-époux / époux survivant + successeurs du prémourant\n\n"
            "POST-SUCCESSORALE :\n"
            "• Naissance : au décès, automatiquement, si plusieurs héritiers\n"
            "• Source la plus fréquente d'indivision\n"
            "• En pratique : se prolonge souvent jusqu'au décès du conjoint survivant\n\n"
            "⚠️ DOUBLE INDIVISION possible : décès époux commun en biens avec enfants\n"
            "→ Liquidation indivision post-communautaire ET indivision successorale\n\n"
            "INDIVISION FORCÉE : chemins d'accès, cours communes — perpétuelle par nature"
        ),
        "question": "M. et Mme Dupont sont mariés sous régime légal. M. Dupont décède laissant son épouse et 2 enfants. Quelles indivisions naissent ? Entre qui ?"
    },
    {
        "titre": "🟠 Méthode complète — Bilan liquidatif à l'examen",
        "contenu": (
            "PLAN À SUIVRE IMPÉRATIVEMENT :\n\n"
            "I. QUALIFICATION DES MOUVEMENTS DE VALEUR\n"
            "  Pour chaque flux financier :\n"
            "  1. Nature de la dépense (acquisition / conservation / amélioration / somptuaire)\n"
            "  2. Créance entre indivisaires OU contre l'indivision ?\n"
            "  3. Prescription vérifiée ?\n"
            "  4. Neutralisation par contributions aux charges ?\n\n"
            "II. LIQUIDATION DES CRÉANCES ENTRE INDIVISAIRES\n"
            "  (apports en capital)\n\n"
            "III. LIQUIDATION DU COMPTE D'INDIVISION\n"
            "  Compte de chaque indivisaire : créances - dettes = solde\n\n"
            "IV. COMPTE GÉNÉRAL DE L'INDIVISION\n"
            "  Actif (biens) - Passif (prêt + soldes comptes) = Actif net indivis\n\n"
            "V. DROITS DES PARTIES\n"
            "  Quote-part × actif net + solde compte ± créances entre indivisaires\n\n"
            "VI. MODALITÉS DE SORTIE\n"
            "  Soulte due = valeur du bien - passif repris - droits de l'attributaire"
        ),
        "question": "Antoine (concubin, 50%) a apporté 50 000€ dont 25 000€ pour la part d'Iris. Immeuble acheté 200 000€, valeur actuelle 240 000€. Iris a payé 20 000€ de mensualités, Antoine 10 000€. Prêt restant : 40 000€. Iris a payé TH (1 000€/an × 4) et TF (1 200€/an × 4). Antoine occupe depuis le décès (loyer marché : 700€/mois × 2,5 mois). Calculez les droits d'Antoine."
    },
]

# ─────────────────────────────────────────────
# ÉTATS DE CONVERSATION
# ─────────────────────────────────────────────
user_sessions = {}

def get_session(user_id):
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "mode": None,
            "fiche_index": 0,
            "quiz_history": [],
            "liquidatif_step": 0,
            "cas_en_cours": None,
        }
    return user_sessions[user_id]

# ─────────────────────────────────────────────
# KEYBOARDS
# ─────────────────────────────────────────────
def menu_principal():
    keyboard = [
        [InlineKeyboardButton("📚 Fiche du jour", callback_data="fiche")],
        [InlineKeyboardButton("❓ Question / QCM", callback_data="quiz")],
        [InlineKeyboardButton("🧮 Simulateur liquidatif", callback_data="liquidatif")],
        [InlineKeyboardButton("📋 Toutes les fiches", callback_data="fiches_all")],
    ]
    return InlineKeyboardMarkup(keyboard)

def menu_apres_fiche():
    keyboard = [
        [InlineKeyboardButton("📖 Voir la question associée", callback_data="fiche_question")],
        [InlineKeyboardButton("➡️ Fiche suivante", callback_data="fiche_next")],
        [InlineKeyboardButton("🏠 Menu principal", callback_data="menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

def menu_apres_quiz():
    keyboard = [
        [InlineKeyboardButton("🔄 Nouvelle question", callback_data="quiz")],
        [InlineKeyboardButton("🧮 Simulateur liquidatif", callback_data="liquidatif")],
        [InlineKeyboardButton("🏠 Menu principal", callback_data="menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ─────────────────────────────────────────────
# APPEL CLAUDE API
# ─────────────────────────────────────────────
async def appel_claude(system_msg: str, user_msg: str) -> str:
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=system_msg,
            messages=[{"role": "user", "content": user_msg}]
        )
        return response.content[0].text
    except Exception as e:
        logger.error(f"Erreur Claude API: {e}")
        return "❌ Erreur de connexion à l'API. Réessaie dans un moment."

async def generer_question_quiz() -> dict:
    system = COURS_AUREP + """
Tu génères des questions d'examen de type cas pratique AUREP CCP.
Réponds UNIQUEMENT en JSON valide avec cette structure exacte :
{
  "theme": "nom du thème",
  "faits": "description des faits en 3-5 phrases",
  "question": "question précise à répondre",
  "reponse_type": "ce que doit contenir une bonne réponse (pour le correcteur)",
  "articles": ["art 815-13 CC", "art 815-9 CC"]
}
Varie les thèmes : gestion de l'indivision / créances liquidatives / fiscalité du partage / 
attribution préférentielle / convention d'indivision / licitation.
"""
    user = "Génère une question de cas pratique AUREP CCP sur l'indivision. JSON uniquement, sans markdown."

    texte = await appel_claude(system, user)
    try:
        # Nettoie le JSON si besoin
        texte_clean = texte.strip()
        if texte_clean.startswith("```"):
            texte_clean = texte_clean.split("```")[1]
            if texte_clean.startswith("json"):
                texte_clean = texte_clean[4:]
        return json.loads(texte_clean)
    except Exception:
        return {
            "theme": "Gestion de l'indivision",
            "faits": "Trois héritiers sont en indivision sur un immeuble locatif. L'un d'eux détient 50%, les deux autres 25% chacun. Le majoritaire veut vendre l'immeuble mais les deux autres s'y opposent.",
            "question": "Quels sont les droits du majoritaire ? Quelle procédure peut-il suivre pour imposer la vente ?",
            "reponse_type": "Art 815-5-1 CC : les 2/3 peuvent demander en justice l'autorisation de vendre. Procédure : déclaration devant notaire + signification aux minoritaires (1 mois) + délai de réponse (3 mois) + autorisation judiciaire si refus.",
            "articles": ["art 815-5-1 CC", "art 815-3 CC"]
        }

async def evaluer_reponse(question: dict, reponse_utilisateur: str) -> str:
    system = COURS_AUREP + """
Tu es un correcteur exigeant du certificat CCP AUREP.
Évalue la réponse de l'étudiant de façon pédagogique :
1. Ce qui est correct ✅
2. Ce qui manque ou est inexact ❌
3. Les articles et jurisprudences à citer
4. Une note /10
Sois précis, concis (max 300 mots), et oriente vers la méthode AUREP.
"""
    user = f"""
FAITS DU CAS : {question['faits']}
QUESTION : {question['question']}
RÉPONSE TYPE ATTENDUE : {question['reponse_type']}
RÉPONSE DE L'ÉTUDIANT : {reponse_utilisateur}

Évalue cette réponse.
"""
    return await appel_claude(system, user)

async def generer_cas_liquidatif() -> dict:
    system = COURS_AUREP + """
Tu génères des cas pratiques de liquidation d'indivision pour l'examen AUREP CCP.
Crée un cas avec des chiffres précis impliquant :
- Un couple (concubins OU partenaires OU époux séparés de biens)
- Un bien immobilier indivis avec prêt
- Des flux financiers variés (mensualités, travaux, taxes, occupation)
- Différentes natures de dépenses

Réponds en JSON strict :
{
  "statut": "concubins/partenaires/époux SDB",
  "faits": "description complète avec tous les chiffres",
  "elements": {
    "prix_acquisition": 0,
    "valeur_actuelle": 0,
    "pret_initial": 0,
    "pret_restant": 0,
    "mensualites_A": 0,
    "mensualites_B": 0,
    "apport_capital_A": 0,
    "apport_capital_B": 0,
    "travaux_conservation": 0,
    "indemnite_occupation_mois": 0,
    "loyer_marche": 0,
    "taxes": 0
  },
  "solution_detaillee": "solution complète étape par étape"
}
"""
    user = "Génère un cas de liquidation d'indivision AUREP. JSON uniquement."

    texte = await appel_claude(system, user)
    try:
        texte_clean = texte.strip()
        if texte_clean.startswith("```"):
            texte_clean = texte_clean.split("```")[1]
            if texte_clean.startswith("json"):
                texte_clean = texte_clean[4:]
        return json.loads(texte_clean)
    except Exception:
        return {
            "statut": "partenaires",
            "faits": "Marc et Julie sont partenaires pacsés. Ils ont acheté un appartement 250 000€ en 2020 (moitié chacun). Marc a apporté 40 000€ en capital pour la part de Julie. L'appartement est financé par un prêt de 210 000€. Julie a remboursé 30 000€ de mensualités, Marc 15 000€. Marc occupe seul l'appartement depuis 1 an (valeur locative : 900€/mois). L'appartement vaut aujourd'hui 300 000€ et le prêt restant est de 165 000€. Ils se séparent.",
            "elements": {
                "prix_acquisition": 250000,
                "valeur_actuelle": 300000,
                "pret_initial": 210000,
                "pret_restant": 165000,
                "mensualites_A": 15000,
                "mensualites_B": 30000,
                "apport_capital_A": 40000,
                "apport_capital_B": 0,
                "travaux_conservation": 0,
                "indemnite_occupation_mois": 12,
                "loyer_marche": 900,
                "taxes": 0
            },
            "solution_detaillee": "À calculer selon la méthode AUREP"
        }

# ─────────────────────────────────────────────
# COMMANDES ET HANDLERS
# ─────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 *Bienvenue sur ton bot de révision AUREP CCP !*\n\n"
        "📖 *Cours couvert :* L'indivision et le partage — Aspects civils et fiscaux\n"
        "🎯 *Objectif :* Te préparer au cas pratique de 4h\n\n"
        "Que veux-tu faire ?"
    )
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=menu_principal())

async def aide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📚 *Commandes disponibles :*\n\n"
        "/start — Menu principal\n"
        "/fiche — Fiche flash du jour\n"
        "/quiz — Question cas pratique\n"
        "/liquidatif — Simulateur de bilan\n"
        "/fiches — Liste toutes les fiches\n"
        "/aide — Ce message\n"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def envoyer_fiche(update_or_query, context, fiche_index=None, edit=False):
    """Envoie une fiche synthétique."""
    if hasattr(update_or_query, 'from_user'):
        user_id = update_or_query.from_user.id
    else:
        user_id = update_or_query.message.chat_id

    session = get_session(user_id)

    if fiche_index is None:
        fiche_index = session["fiche_index"]

    fiche = FICHES[fiche_index % len(FICHES)]
    session["fiche_index"] = fiche_index

    msg = (
        f"*{fiche['titre']}*\n\n"
        f"{fiche['contenu']}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"_{fiche_index + 1}/{len(FICHES)} fiches_"
    )

    if edit and hasattr(update_or_query, 'edit_message_text'):
        await update_or_query.edit_message_text(msg, parse_mode="Markdown", reply_markup=menu_apres_fiche())
    elif hasattr(update_or_query, 'message'):
        await update_or_query.message.reply_text(msg, parse_mode="Markdown", reply_markup=menu_apres_fiche())
    else:
        await update_or_query.reply_text(msg, parse_mode="Markdown", reply_markup=menu_apres_fiche())

async def lancer_quiz(update_or_query, context, edit=False):
    """Lance une question de cas pratique."""
    if hasattr(update_or_query, 'message'):
        chat_id = update_or_query.message.chat_id
        msg_func = update_or_query.edit_message_text if edit else update_or_query.message.reply_text
    else:
        chat_id = update_or_query.chat_id
        msg_func = update_or_query.reply_text

    await msg_func("⏳ Génération d'une question en cours...", parse_mode="Markdown")

    question = await generer_question_quiz()
    user_id = update_or_query.from_user.id if hasattr(update_or_query, 'from_user') else update_or_query.message.chat_id
    session = get_session(user_id)
    session["mode"] = "quiz"
    session["quiz_history"].append({"question": question, "reponse": None})

    articles_str = " | ".join(question.get("articles", []))
    msg = (
        f"❓ *{question['theme']}*\n\n"
        f"📋 *Faits :*\n{question['faits']}\n\n"
        f"🎯 *Question :*\n_{question['question']}_\n\n"
        f"📌 Articles clés : `{articles_str}`\n\n"
        f"✍️ *Rédige ta réponse en texte libre.* Je l'évalue ensuite."
    )
    await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")

async def lancer_liquidatif(update_or_query, context, edit=False):
    """Lance un simulateur de bilan liquidatif."""
    if hasattr(update_or_query, 'message'):
        chat_id = update_or_query.message.chat_id
        msg_func = update_or_query.edit_message_text if edit else update_or_query.message.reply_text
    else:
        chat_id = update_or_query.chat_id
        msg_func = update_or_query.reply_text

    await msg_func("⏳ Génération d'un cas liquidatif...", parse_mode="Markdown")

    cas = await generer_cas_liquidatif()
    user_id = update_or_query.from_user.id if hasattr(update_or_query, 'from_user') else chat_id
    session = get_session(user_id)
    session["mode"] = "liquidatif"
    session["cas_en_cours"] = cas

    keyboard = [
        [InlineKeyboardButton("✅ Voir la solution complète", callback_data="liquidatif_solution")],
        [InlineKeyboardButton("🔄 Nouveau cas", callback_data="liquidatif")],
        [InlineKeyboardButton("🏠 Menu", callback_data="menu")],
    ]

    msg = (
        f"🧮 *SIMULATEUR BILAN LIQUIDATIF*\n"
        f"Statut : *{cas['statut']}*\n\n"
        f"📋 *Faits du cas :*\n{cas['faits']}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"*Ta mission :* Liquide cette indivision.\n"
        f"Applique la méthode en 5 étapes :\n"
        f"1️⃣ Qualifier chaque dépense\n"
        f"2️⃣ Qualifier chaque créance\n"
        f"3️⃣ Calculer les comptes d'indivision\n"
        f"4️⃣ Déterminer l'actif net indivis\n"
        f"5️⃣ Calculer les droits de chaque partie\n\n"
        f"✍️ *Fais tes calculs puis demande la solution.*"
    )
    await context.bot.send_message(
        chat_id=chat_id, text=msg, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ─────────────────────────────────────────────
# CALLBACK HANDLER (boutons)
# ─────────────────────────────────────────────
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    session = get_session(user_id)
    data = query.data

    if data == "menu":
        await query.edit_message_text(
            "🏠 *Menu principal* — Que veux-tu faire ?",
            parse_mode="Markdown", reply_markup=menu_principal()
        )

    elif data == "fiche":
        await envoyer_fiche(query, context, edit=True)

    elif data == "fiche_next":
        session["fiche_index"] = (session["fiche_index"] + 1) % len(FICHES)
        await envoyer_fiche(query, context, fiche_index=session["fiche_index"], edit=True)

    elif data == "fiche_question":
        fiche = FICHES[session["fiche_index"] % len(FICHES)]
        session["mode"] = "quiz_fiche"
        session["quiz_history"].append({
            "question": {
                "theme": fiche["titre"],
                "faits": "",
                "question": fiche["question"],
                "reponse_type": fiche["contenu"],
                "articles": []
            },
            "reponse": None
        })
        msg = (
            f"📝 *Question associée à la fiche :*\n\n"
            f"_{fiche['question']}_\n\n"
            f"✍️ Rédige ta réponse en texte libre."
        )
        await query.edit_message_text(msg, parse_mode="Markdown")

    elif data == "fiches_all":
        index_msg = "📚 *Toutes les fiches disponibles :*\n\n"
        keyboard = []
        for i, f in enumerate(FICHES):
            keyboard.append([InlineKeyboardButton(f["titre"], callback_data=f"fiche_{i}")])
        keyboard.append([InlineKeyboardButton("🏠 Menu", callback_data="menu")])
        await query.edit_message_text(index_msg, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("fiche_") and data[6:].isdigit():
        idx = int(data[6:])
        await envoyer_fiche(query, context, fiche_index=idx, edit=True)

    elif data == "quiz":
        await lancer_quiz(query, context, edit=True)

    elif data == "liquidatif":
        await lancer_liquidatif(query, context, edit=True)

    elif data == "liquidatif_solution":
        cas = session.get("cas_en_cours")
        if not cas:
            await query.edit_message_text("❌ Aucun cas en cours. Relance /liquidatif")
            return

        # Demander à Claude de détailler la solution
        system = COURS_AUREP
        user = f"""
Présente la solution complète et détaillée de ce cas de liquidation d'indivision AUREP.
Suis exactement la méthode en 5 étapes enseignée à l'AUREP.
Présente tous les calculs avec les formules.

CAS : {cas['faits']}
STATUT : {cas['statut']}
"""
        solution = await appel_claude(system, user)
        keyboard = [
            [InlineKeyboardButton("🔄 Nouveau cas", callback_data="liquidatif")],
            [InlineKeyboardButton("🏠 Menu", callback_data="menu")],
        ]
        await query.edit_message_text(
            f"✅ *SOLUTION DÉTAILLÉE*\n\n{solution}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ─────────────────────────────────────────────
# MESSAGE HANDLER (réponses texte de l'utilisateur)
# ─────────────────────────────────────────────
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    session = get_session(user_id)
    texte = update.message.text

    mode = session.get("mode")

    if mode in ("quiz", "quiz_fiche"):
        # L'utilisateur répond à une question
        if not session["quiz_history"]:
            await update.message.reply_text("Lance d'abord une question avec /quiz")
            return

        derniere = session["quiz_history"][-1]
        if derniere["reponse"] is not None:
            # Déjà répondu, proposer menu
            await update.message.reply_text(
                "Tu as déjà répondu à cette question. Lance /quiz pour une nouvelle.",
                reply_markup=menu_apres_quiz()
            )
            return

        derniere["reponse"] = texte
        session["mode"] = None

        await update.message.reply_text("⏳ Évaluation de ta réponse en cours...")
        evaluation = await evaluer_reponse(derniere["question"], texte)

        await update.message.reply_text(
            f"📊 *Évaluation de ta réponse :*\n\n{evaluation}",
            parse_mode="Markdown",
            reply_markup=menu_apres_quiz()
        )

    else:
        # Message libre → l'IA répond en mode prof AUREP
        system = COURS_AUREP + "\nRéponds de façon concise et pédagogique, comme un professeur AUREP en révision."
        reponse = await appel_claude(system, texte)
        await update.message.reply_text(
            reponse, parse_mode="Markdown", reply_markup=menu_principal()
        )

# ─────────────────────────────────────────────
# ENVOI AUTOMATIQUE DES FICHES (7h chaque matin)
# ─────────────────────────────────────────────
async def envoyer_fiche_quotidienne(context: ContextTypes.DEFAULT_TYPE):
    if not YOUR_CHAT_ID:
        return
    chat_id = int(YOUR_CHAT_ID)
    session = get_session(chat_id)
    idx = session["fiche_index"]
    fiche = FICHES[idx % len(FICHES)]

    msg = (
        f"☀️ *Fiche du jour — AUREP CCP*\n\n"
        f"*{fiche['titre']}*\n\n"
        f"{fiche['contenu']}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📝 _Question d'entraînement :_\n_{fiche['question']}_\n\n"
        f"Réponds en message ou appuie sur un bouton ↓"
    )

    keyboard = [
        [InlineKeyboardButton("✅ J'ai répondu, montrer corrigé", callback_data="fiche_question")],
        [InlineKeyboardButton("➡️ Fiche suivante", callback_data="fiche_next")],
    ]

    session["fiche_index"] = (idx + 1) % len(FICHES)
    await context.bot.send_message(
        chat_id=chat_id, text=msg, parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ─────────────────────────────────────────────
# COMMANDES DIRECTES
# ─────────────────────────────────────────────
async def cmd_fiche(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await envoyer_fiche(update.message, context)

async def cmd_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await lancer_quiz(update.message, context)

async def cmd_liquidatif(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await lancer_liquidatif(update.message, context)

async def cmd_fiches_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for i, f in enumerate(FICHES):
        keyboard.append([InlineKeyboardButton(f["titre"], callback_data=f"fiche_{i}")])
    keyboard.append([InlineKeyboardButton("🏠 Menu", callback_data="menu")])
    await update.message.reply_text(
        "📚 *Toutes les fiches disponibles :*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Commandes
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("aide", aide))
    app.add_handler(CommandHandler("help", aide))
    app.add_handler(CommandHandler("fiche", cmd_fiche))
    app.add_handler(CommandHandler("quiz", cmd_quiz))
    app.add_handler(CommandHandler("liquidatif", cmd_liquidatif))
    app.add_handler(CommandHandler("fiches", cmd_fiches_all))

    # Boutons
    app.add_handler(CallbackQueryHandler(button_handler))

    # Messages texte
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # Envoi automatique 7h chaque matin (heure de Paris)
    if YOUR_CHAT_ID:
        app.job_queue.run_daily(
            envoyer_fiche_quotidienne,
            time=time(hour=7, minute=0),
            days=(0, 1, 2, 3, 4, 5, 6)
        )

    logger.info("✅ Bot AUREP démarré !")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
