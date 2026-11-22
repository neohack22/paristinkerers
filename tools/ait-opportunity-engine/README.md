# AI Tinkerers Opportunity Engine — MVP interne

Ce dossier fournit un moteur **local et non connecté** de recommandations d'activations. Il ne contacte aucun sponsor et ne modifie aucun événement.

## Exécuter sur un graphe local autorisé

```bash
python engine.py --input ait_project_graph_pilot_v1.json --output opportunities.json
python build_dashboard.py ait_project_graph_pilot_v1.json opportunities.json ma_page_ait.html
python -m unittest discover -p 'test_*.py'
```

Les scores de démos absents sont conservés comme inconnus. Un workshop est suggéré seulement si une note réelle, avec échelle, satisfait le seuil configurable (par défaut 8/10). Deux projets de même thème et chapitre peuvent faire apparaître un meetup thématique. Les invitations à des dîners requièrent un profil technique en entreprise ou technical founder explicitement confirmé. Les relations de concurrence doivent être confirmées avant de suggérer une migration.

## API AI Tinkerers

La documentation officielle : https://aitinkerers.org/docs/public/ai_tinkerers_agents_api.md. Authentification personnelle via une clé agent `sk_` ; la liste des opérations permises varie selon cette clé. Une simple vérification de permissions (sans stocker de données) :

```bash
AIT_AGENT_KEY='clé configurée uniquement en environnement privé' python api_probe.py
```

Ne placez jamais la clé dans un message, un fichier de graphe ou GitHub. Ce MVP n'implémente pas d'extraction de masse ; après validation des permissions, utiliser uniquement les opérations pertinentes accessibles, avec minimisation et contraintes de conservation. Les données obtenues via l'API ne doivent pas être transférées vers un produit sponsor sans autorisation d'AI Tinkerers.

## Gmail et autres sources

Les sept projets actuels ont été extraits des messages reçus. La synchronisation planifiée Gmail n'est pas active : elle nécessite un exécuteur connecté disposant de droits d'écriture dans le référentiel. Garder une seule entité par projet et une provenance par affirmation ; les notes d'événement ne sont pas les notes des projets.

## État des composants

- Modèle : étendu et conservé séparément ; les données CRM existantes n'ont pas été écrasées.
- Graphe de démonstration : 7 projets réels sourcés ; ne constitue pas un inventaire de la communauté.
- Moteur et tests : opérationnels localement.
- Dashboard : HTML local, non publié dans ChatGPT Sites.
- API authentifiée, Gmail planifié, site publié, writes autonomes : non connectés.
- `Routines_Operationnelles.md` : règles ajoutées ; ne vaut pas activation technique de ces connexions.

## Connecteur REST incrémental (novembre 2026)

`rest_sync.py` a été ajouté pour éviter d'employer Codex à chaque lecture. Il utilise **uniquement les opérations GET exposées par l'OpenAPI authentifiée** de ton compte. Aucune requête d'écriture sur la plateforme n'est prévue. Le fichier de configuration exemple est volontairement **non fonctionnel** tant que les vrais identifiants d'opérations et les chemins de réponse n'ont pas été constatés ; ceci évite d'inventer des endpoints.

```bash
# Sur ton ordinateur / serveur, dans un terminal privé (ne pas communiquer la clé dans ChatGPT)
export AIT_AGENT_KEY='sk_...'
python rest_sync.py discover --out capabilities.json
# Lire capabilities.json, choisir les seules lectures nécessaires et adapter sync_config.example.json
python rest_sync.py sync --config sync_config.json --state sync_state.json --out snapshot.json
# Choisir un opérationId autorisé correspondant à de VRAIS projets
python import_snapshot.py --graph ait_project_graph_pilot_v1.json --snapshot snapshot.json \
  --allowed-operation OPERATION_ID_AUTORISE --out graph_updated.json
python engine.py --input graph_updated.json --output opportunities_updated.json
python build_dashboard.py graph_updated.json opportunities_updated.json ma_page_ait.html
```

Le `sync_state.json` joue le rôle d'index de synchronisation : le script ne remplace que les enregistrements dont l'empreinte a changé. **Cette version lit la première page de chaque opération configurée**, au maximum 100 lignes par défaut, sans pagination automatique ; elle n'est donc pas exhaustive pour une grosse communauté. Pour une API qui impose POST pour certaines lectures, il faudra ajouter une prise en charge explicite et limitée après examen de la spécification. Les champs `rating` ne sont importés que si **l'échelle** est fournie et valide. Les technologies ou les profils ne sont jamais inventés. Les fichiers résultants sont des projections locales ; ils **ne modifient pas `/CRM/Entity_Registry.json`** et ne sont pas automatiquement synchronisés avec un Site publié.

**Exécution récurrente sans Codex :** une fois l'accès et les champs testés, un ordonnanceur local (cron/systemd) peut lancer la même séquence Python. Le serveur doit assurer l'accès sécurisé à la clé, le chiffrement/contrôle d'accès des fichiers, la durée de conservation permise par AIT, les erreurs et les permissions. Aucun ordonnanceur n'est installé par cette livraison.

Test local sans clé : `python -m unittest discover -p 'test_*.py'`.