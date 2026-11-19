# Webora — mode d'emploi des Reels quotidiens

Ce fichier est la source de vérité. Chaque exécution (tâche planifiée ou session à la main) le suit
de bout en bout. Langue des contenus : **français, tutoiement**.

## 0. Identité

| | |
|---|---|
| Agence | **Webora** — création de sites vitrines et boutiques pour artisans et indépendants |
| Instagram | **@webora.agence** |
| Metricool | brand / blogId **8213553**, fuseau **Europe/Paris** |
| Dépôt | `veyrierflorimond-hash/webora-reels` (public) — vidéos servies via `https://raw.githubusercontent.com/veyrierflorimond-hash/webora-reels/main/<chemin>` |
| Voix | Speko, clone **« Webora - voix IA dynamique »**, fournisseur `cartesia`, voice id **`0d3527fd-ceda-4a51-98d4-1849a3358d02`** |
| Couleurs | bleu pétrole `#04485B`, turquoise `#26B6C4`, blanc cassé `#F7F8F2` (déjà dans le moteur) |
| Publication | **1 Reel par jour à 10:00** (heure de Paris) |

Cibles : artisans du bâtiment (plombier, électricien, maçon, couvreur, menuisier, peintre, paysagiste…),
métiers de la beauté et du bien-être (esthéticienne, prothésiste ongulaire, spa, centre de soins, coiffeur…),
indépendants en général.

## 1. Règles fixes (ne jamais déroger)

1. **La fin de chaque Reel** : la dernière phrase de la voix se termine par
   **« Envoie-moi un message pour qu'on discute de ton projet ! »**. La scène `cta` affiche déjà
   le bouton « Envoie-moi un message » + « pour qu'on discute de ton projet ! » + @webora.agence.
2. **Pas de prix** dans les Reels ni les descriptions (l'offre se discute en message).
3. **Valeur, pas technique** : visibilité Google → plus de clients, mettre en avant services et réalisations,
   demandes de devis / RDV même quand l'artisan est occupé, clients qui passent sous le nez,
   chantiers / prestations loupés. Des situations vécues qui font dire « ah ouais, il me faut un site ».
4. **Ne rien inventer de vérifiable** : pas de statistique chiffrée, pas de faux client, pas de faux avis
   présenté comme réel. Les concurrents à l'écran sont des noms fictifs génériques (« Plomberie Bernard »).
5. **Une seule idée par Reel**, 15 à 22 secondes, 5 ou 6 scènes.
6. **Exactement 5 hashtags** (limite Instagram), à la fin de la description.
7. Case **« contenu généré par IA »** toujours cochée (`isAiGenerated: true`) : la voix est synthétique.
8. **Voix** : ne jamais retoucher l'audio (pas d'accélération, pas de compression maison) — ça sonne « IA ».

## 2. Choisir le sujet du jour

1. Lire `history.json` : ne pas reprendre un sujet des 30 derniers jours, et **alterner les cibles**
   (jamais deux jours de suite la même : bâtiment → beauté → tous artisans → …).
2. Lire `insights.md` (ce qui a marché / pas marché) et privilégier les angles gagnants.
3. Banque d'idées (à enrichir) :
   - Bâtiment : appel manqué sur le chantier ; « le client a choisi celui qui avait des photos » ;
     devis demandé le dimanche soir ; « tu bosses bien mais personne ne le sait » ;
     le bouche-à-oreille qui ne suffit plus ; le client qui vérifie sur Google après une recommandation ;
     les photos de chantiers qui dorment dans le téléphone ; la fiche Google sans site derrière.
   - Beauté / bien-être : messages pendant un soin ; la cliente qui veut voir les réalisations avant de réserver ;
     « c'est combien ? » répété 20 fois par jour ; la nouvelle cliente qui cherche « onglerie près de moi » ;
     le RDV pris ailleurs le soir ; tes prestations introuvables en dehors d'Instagram.
   - Tous : le client qui cherche « près de chez moi » ; ton concurrent moins bon mais plus visible ;
     « j'ai pas le temps de m'en occuper » ; le site qui travaille la nuit ; le client qui hésite et compare.
4. Chaque lundi, faire d'abord la **revue hebdo** (section 8).

## 3. Écrire le script

Structure (types de scènes disponibles dans `engine/build_reel.py`) :

| # | type | rôle |
|---|---|---|
| 1 | `hook` | l'accroche, ≤ 3 s de voix, 4 lignes courtes, un mot clé `*surligné*` |
| 2 | `phone` **ou** `search` | la situation (téléphone avec notifications, ou recherche Google) |
| 3 | `search` / `statement` | la conséquence (le client part ailleurs) |
| 4 | `solution` (fond clair) | « Avec un *site* : » + 3 bénéfices + notification positive |
| 5 | `cta` | phrase de conclusion + la phrase fixe de fin |

Variantes possibles : remplacer 2 ou 3 par des `statement` (texte plein écran, fond `dark` ou `light`, `pill` optionnelle).
Texte à l'écran : ≤ 6 mots par ligne, phrases courtes, tutoiement. La voix peut dire plus que l'écran.

## 4. Générer et vérifier la voix (Speko)

Pour **chaque scène**, une phrase de voix :

```
audio_synthesize body = {
  "text": "<phrase>",
  "intent": {"language": "fr", "optimizeFor": "accuracy"},
  "voice": "0d3527fd-ceda-4a51-98d4-1849a3358d02",
  "constraints": {"allowedProviders": {"tts": ["cartesia"]}}
}
```

- Le résultat donne un chemin local du WAV : le **copier** dans `work/<date>/v<n>.wav`.
- **Vérifier chaque phrase** avec `audio_transcribe` (url = le lien de téléchargement renvoyé, `language: fr`).
  Pour les scènes à synchroniser (`phone`, `search`), ajouter `word_timestamps: true`.
- Si un mot diffère (hors homophones : site/cite, sois/soit, pose/pause), **reformuler et régénérer**
  (ex. « en plein soin » était entendu « en plein sommeil » → « pendant tes soins »).
- Pour éviter les « r » et liaisons avalées, préférer des phrases courtes ; « Le lien est en bio » plutôt que « Lien en bio ».
- Vérifier le crédit avec `credits_balance_get` ; s'il passe sous 0,50 $, prévenir l'utilisateur.

## 5. Écrire le scénario et construire la vidéo

Écrire `scenarios/<date>_<slug>.json` (format complet en tête de `engine/build_reel.py`).
**Synchronisation** : les champs `at` sont en secondes réelles depuis le début de la scène ;
la voix commence à 0,1 s ⇒ `at = 0.1 + start_ms/1000` du mot visé
(ex. les 3 appels manqués sur « une fois / deux fois / trois fois », la carte « Introuvable » sur le mot).
Dans une scène `search`, les cartes doivent arriver après 1,55 s (fin de la frappe).

```bash
pip install --break-system-packages pillow numpy >/dev/null 2>&1 || true   # si absents
python3 -I engine/build_reel.py --preview scenarios/<date>_<slug>.json work/<date>/preview   # images de contrôle
python3 -I engine/build_reel.py scenarios/<date>_<slug>.json videos/<date>_<slug>.mp4
```

Contrôles obligatoires avant publication :
- regarder les images de `--preview` (texte lisible, rien ne déborde, rien sous y=1440 ni collé au bord droit) ;
- durée 13–25 s ; taille < 15 Mo ;
- `ffmpeg -i <mp4> -af volumedetect -f null -` : max_volume ≤ −0,5 dB.

## 6. Description (légende)

```
<Accroche ≤ 125 caractères : la situation, concrète, qui parle à la cible>

<Paragraphe 2-3 phrases : le problème vécu, sans chiffre inventé>

<Paragraphe 2 phrases : ce que change un site (visibilité Google, réalisations, demandes même quand on est occupé)>

👉 Envoie-moi un message pour qu'on discute de ton projet !

#tag1 #tag2 #tag3 #tag4 #tag5
```
Hashtags (5, choisir selon la cible) :
- Bâtiment : #artisan #artisanbatiment #plombier #electricien #maçon #couvreur #menuisier #renovation #sitevitrine
- Beauté : #estheticienne #prothesisteongulaire #institutdebeaute #spa #onglerie #coiffeuse #siteweb
- Tous : #artisan #independant #siteinternet #referencementlocal #entrepreneur #sitevitrine

## 7. Publier

1. Vérifier dans Metricool (`getScheduledPosts`, brandId 8213553, Europe/Paris) le **prochain jour libre**
   à partir de demain ; ne jamais programmer deux Reels le même jour.
2. Ajouter à `history.json` : `{"date", "slug", "audience", "topic", "hook", "video", "metricool_id"}`.
3. `git add videos/… scenarios/… history.json && git commit && git push` (branche `main`).
4. Vérifier le lien : `curl -sIL https://raw.githubusercontent.com/veyrierflorimond-hash/webora-reels/main/videos/<fichier>`
   → 200 + `content-length` = taille du fichier.
5. `createScheduledPost` (blogId 8213553), date `<jour>T10:00:00+01:00` (ou +02:00 l'été), `info` :
```json
{"autoPublish": true, "draft": false, "descendants": [], "firstCommentText": "", "hasNotReadNotes": false,
 "media": ["<lien raw>"], "mediaAltText": [], "videoCoverMilliseconds": 1500,
 "providers": [{"network": "instagram"}],
 "publicationDate": {"dateTime": "<jour>T10:00:00", "timezone": "Europe/Paris"},
 "shortener": false, "smartLinkData": {"ids": []}, "text": "<description>",
 "instagramData": {"type": "REEL", "showReelOnFeed": true, "isAiGenerated": true}}
```
6. Reporter le `id` Metricool dans `history.json`, commit + push.
7. Prévenir l'utilisateur (message court) : sujet, date de publication, lien `plannerUrl`, la vidéo jointe.

Si une étape échoue (voix non conforme après 2 essais, rendu cassé, Metricool en erreur) :
**ne rien programmer**, prévenir l'utilisateur avec l'erreur exacte.

## 8. Revue hebdomadaire (le lundi)

1. Metricool `getAnalyticsDataByMetrics` sur les Reels des 7 derniers jours (vues, portée, partages,
   enregistrements, commentaires). `getAnalyticsAvailableMetrics` (network instagram, connector reels)
   pour obtenir les identifiants de métriques.
2. vidIQ `vidiq_instagram_tiktok_outlier_search` (5 crédits) sur 1 ou 2 requêtes de la niche, ex. :
   `query: "artisan site internet clients"`, `audienceQuery: "Culture/Region: France/French; Global: false; Demographics: artisans du bâtiment et indépendants 25-55 ans;"`,
   `descriptionLanguage: ["fr"]`.
3. Écrire 3 à 5 enseignements dans `insights.md` (sujets, accroches, formats qui marchent), commit + push,
   et les appliquer aux Reels de la semaine.
