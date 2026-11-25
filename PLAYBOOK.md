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
| Publication | **du lundi au vendredi uniquement : un Reel à 10:00** (heure de Paris). Plus de story ni de carrousel, rien le week-end (décidé par Florimond le 25/11/2026 : forfait Metricool limité à 20 publications par mois) |

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
9. **Musique de fond** (validée par Florimond le 21/11/2026) : chaque Reel a une petite musique pop générée par
   `engine/music.py` (libre de droits, aucun morceau existant), loin sous la voix et qui baisse quand la voix
   ou les bruitages arrivent. Elle est ajoutée automatiquement par `build_reel.py` ; la mélodie change d'un Reel
   à l'autre (12 variantes, choisies d'après le nom du fichier). On peut forcer `"music": {"variant": n}` ou
   la couper avec `"music": false` dans le scénario.

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

**Varier l'interface (souhait de Florimond)** : mêmes couleurs, mais pas toujours le même décor. Choisir les scènes
**selon le sujet** (pas de changement pour le plaisir) et éviter de reprendre exactement la même suite de scènes que
les Reels précédents (champ `interfaces` de `history.json`). Interfaces disponibles en plus de `phone` / `search` / `statement` :

| type | quand l'utiliser | champs |
|---|---|---|
| `chat` | une conversation (cliente qui pose des questions, client qui attend une réponse) | `lines`, `contact`, `status`, `messages` [{`at`, `from`: `client`/`moi`, `text`}] (≤ 4 messages courts), `alert` {`at`, `text`} optionnel (pastille rouge) |
| `site` | montrer ce que voit le client sur un site (fond clair) ; la souris clique sur le bouton | `lines`, `name` (fictif ou « Ton entreprise »), `url`, `tagline`, `button`, `gallery` (3 libellés), `click_at`, `notif` {`at`, `title`, `body`} |
| `compare` | avant / après, sans site / avec un site | `lines`, `left_title`, `right_title`, `rows` [{`at`, `left`, `right`}] (3 lignes max, ≤ 4 mots chacune) ; la carte de droite arrive 0,35 s après `at` |

Les `at` se synchronisent sur les mots comme ailleurs. `site` peut remplacer `solution` ; `chat` peut remplacer `phone` ;
`compare` peut remplacer `statement` ou `solution`. Garder toujours `hook` au début et `cta` à la fin.
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
- `ffmpeg -i <mp4> -af volumedetect -f null -` : max_volume ≤ −0,5 dB ;
- la sortie du rendu affiche `music variant <n>` (la musique est bien présente).

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

1. Vérifier dans Metricool (`getScheduledPosts`, brandId 8213553, Europe/Paris) le **prochain jour ouvré libre**
   (lundi à vendredi) à partir de demain ; ignorer les posts en brouillon (`draft: true`) ; jamais de week-end,
   jamais deux Reels le même jour.
2. Ajouter à `history.json` : `{"date", "slug", "audience", "topic", "hook", "video", "metricool_id", "interfaces"}`
   (`interfaces` = liste des types de scènes dans l'ordre, pour varier d'un Reel à l'autre).
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
6. ~~**Story**~~ (**supprimée depuis le 25/11/2026**, ne plus programmer) : programmer la même vidéo en story le même jour à **12:30** — `createScheduledPost` avec le même
   `media`, **sans `text`**, `"instagramData": {"type": "STORY", "isAiGenerated": true}`, sans `videoCoverMilliseconds`.
7. Reporter l'`id` Metricool du Reel dans `history.json`, commit + push.
8. ~~Carrousel du jour~~ : **supprimé depuis le 25/11/2026** (voir section 9).
9. Prévenir l'utilisateur (message court) : sujet, date de publication, lien `plannerUrl`, la vidéo jointe.

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

## 9. Carrousel du jour (publication à 18:00) — **SUSPENDU depuis le 25/11/2026**

> Ne plus faire de carrousel (forfait Metricool limité à 20 publications par mois). Section gardée pour le jour
> où Florimond voudra les relancer.

Une publication par jour, en **carrousel** (couverture + 3 à 5 slides + slide finale), même date que le Reel.

1. **Sujet** : mêmes exigences que les Reels — **un sujet différent chaque jour** (jamais repris sur 30 jours,
   vérifier les entrées `"format": "carousel"` de `history.json`), **cible alternée**, même cible que le Reel du jour,
   toujours autour de **l'offre Webora et de ce qu'elle apporte aux clients**. Faire tourner ces familles
   (ne jamais en enchaîner deux identiques) :
   - **Problèmes vécus** : « 3 erreurs qui font fuir tes clients », « Pourquoi ton bouche-à-oreille ne suffit plus »,
     « Ce qui se passe quand un client ne te trouve pas ».
   - **Conseils pratiques** : « Check-list : le site d'un(e) <métier> doit avoir… », « Ce que ton client regarde en 10 secondes »,
     « Les photos qui donnent envie de t'appeler », « Comment rassurer un client qui ne te connaît pas ».
   - **L'offre Webora** (≈ 1 à 2 fois par semaine) : site vitrine **ou** boutique en ligne selon le besoin, pour qui,
     comment ça se passe étape par étape, ce que ça change au quotidien. **N'affirmer que ce qui est dans la section 10.**
   - **Mythes / réalité** : « Un site c'est compliqué », « Instagram suffit », « J'ai déjà assez de clients »,
     « Ma fiche Google suffit ».
   - **Questions de clients** : « 5 questions que tes clients se posent avant de t'appeler », « Fiche Google seule vs fiche + site ».
   - **Par métier** : un carrousel dédié à un métier précis (plombier, électricien, couvreur, paysagiste, esthéticienne,
     prothésiste ongulaire, spa, coiffeur…) : ses situations, ce que son site doit montrer.
   Pas de prix, pas de chiffre ni de client inventés.
2. Écrire `posts_src/<date>_<slug>.json` (format en tête de `engine/post.py`) :
   `tag` (cible, en majuscules), `cover` (2-4 lignes courtes, un mot `*surligné*`), `cover_sub` (optionnel),
   `slides` : 3 à 5 × {`title` ≤ 8 mots, `body` ≤ 30 mots, `fix` ≤ 18 mots = « La solution »}, `cta_lines` (1-2 lignes).
   La slide finale ajoute toujours « Envoie-moi un message » / « pour qu'on discute de ton projet ! » / @webora.agence.
3. `python3 -I engine/post.py posts_src/<date>_<slug>.json posts/<date>_<slug>/` puis **regarder chaque image**
   (texte qui ne déborde pas, encadré « La solution » complet).
4. Description : mêmes règles qu'en section 6 (accroche ≤ 125 caractères, « 👉 Envoie-moi un message pour qu'on discute de ton projet ! », **exactement 5 hashtags**),
   et inviter à enregistrer le post (« Enregistre-le pour plus tard »).
5. Commit + push `posts/<date>_<slug>/` et `posts_src/…`, vérifier chaque lien raw (200), puis `createScheduledPost` :
```json
{"autoPublish": true, "draft": false, "descendants": [], "firstCommentText": "", "hasNotReadNotes": false,
 "media": ["<raw>/posts/<date>_<slug>/01.jpg", "<raw>/.../02.jpg", "..."], "mediaAltText": [],
 "providers": [{"network": "instagram"}],
 "publicationDate": {"dateTime": "<jour>T18:00:00", "timezone": "Europe/Paris"},
 "shortener": false, "smartLinkData": {"ids": []}, "text": "<description>",
 "instagramData": {"type": "POST", "isAiGenerated": false}}
```
6. Ajouter l'entrée à `history.json` avec `"format": "carousel"` et l'`id` Metricool.

## 10. Ce que l'on sait de l'offre Webora (ne rien affirmer d'autre)

- Webora crée des **sites vitrines** et des **boutiques en ligne (shop)**, **sur mesure**, selon les besoins du client.
- Clients : artisans du bâtiment, métiers de la beauté et du bien-être (centres de soins, spas, onglerie, esthéticiennes…),
  indépendants — **partout en France** (tout se fait à distance).
- **Livraison : site livré en 3 jours maximum.**
- **Inclus** : nom de domaine, hébergement, maintenance, référencement Google (SEO), modifications après la mise en ligne.
- **Site complet de 5 pages minimum**, travaillé dans le détail selon les besoins du client.
- **Comment ça se passe** :
  1. premier échange avec un **mini-audit** des points à améliorer sur sa visibilité ;
  2. **maquette** du site ;
  3. si le client valide, **création du site complet** (5 pages minimum, sur mesure) ;
  4. **mise en ligne**.
- Angle de communication : visibilité sur Google, mise en avant des services et des réalisations, demandes de devis /
  de rendez-vous même quand le client est occupé, ne plus laisser filer de clients.
- **Ne jamais mentionner** : le tarif (donné en message privé), la création de fiche Google (option en plus, discutée en privé).
  Ne pas dire que l'audit ou la maquette sont « gratuits » ou « offerts » (non précisé).

Idées de contenus tirées de l'offre (Reels ou carrousels) : « Ton site en ligne en 3 jours », « Comment ça se passe
avec Webora, en 4 étapes », « Ce qui est inclus dans ton site » (domaine, hébergement, maintenance, référencement,
modifications), « Le mini-audit : ce qu'on regarde sur ta visibilité », « Tu n'as rien à gérer après la mise en ligne »,
« 5 pages minimum : ce qu'on met dedans pour un(e) <métier> », « Où que tu sois en France ».
