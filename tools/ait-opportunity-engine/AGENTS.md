# AI Tinkerers Opportunity Engine — agent handoff

## Purpose
Internal sponsor/event intelligence for chapters where the user actually works. This is a code repository, **not** the canonical data store, CRM, or an AI Tinkerers official product.

## Source boundary (mandatory)
- AIT **REST or MCP** data access may only target: **Paris, Lima, Bamako (BKO), Conakry (CKY), Casablanca (Casa), San Francisco (SF)**.
- San Francisco: **exceptional/limited** access only; disabled by default. Enable only for an explicitly relevant event or use case, with an approved chapter/event filter and low result cap.
- Other locations (including **Singapore, Kuala Lumpur, Ho Chi Minh City, Da Nang, Hong Kong, Shenzhen, Beijing, Tokyo, Eindhoven**) may use **public web sources or user-supplied information only**. Do not query AIT REST/MCP for them, even if accessible via broad account permissions.
- Never run unscoped API/MCP requests to collect projects, participants, events, evaluations or sponsors across chapters. OpenAPI capability discovery is not a data harvesting operation.
- API jobs must have an authenticated, documented GET operation, an explicit chapter/event parameter whose value is in the approved allowlist, and evidence of the chapter in every returned record. Fail closed otherwise. Check real parameter and response field names before enabling a job; the example config contains no activated jobs.
- Every published recommendation must carry source, date, verification status and any uncertainty. Do not infer scores or speaker commitments.

## Privacy and execution
- Never commit API credentials, Gmail content, individual AIT participant/project data, private CRM records, query results, snapshots, logs, or exported dashboards to the **public** GitHub repository.
- Key `AIT_AGENT_KEY` is injected as a secret in the authorized runtime, never embedded in GitHub, prompts, CLI arguments or scripts. Do not echo it.
- Prefer REST+Python for deterministic bulk/incremental processing; ChatGPT/Codex may orchestrate this in a secure runtime, but **no dedicated always-on machine is assumed**.
- The scripts are currently read-only against AIT and have no real authenticated API test. They do not run autonomously or update a published ChatGPT Site.
- Library CRM: `/CRM/Entity_Registry.json` is the shared identity registry; canonical CRM facts are in per-record JSON files. The pilot JSON is **not yet reconciled** with this registry. Do not overwrite it to "finish" an integration.
- Existing `Routines_Operationnelles.md` is the canonical routine definition. Do not create new routines or independent task registries.
- AIT sponsor-facing disclosures / cross-chapter data use require appropriate authorization; keep this system organizer-private.

## Development and checks
```bash
python -m pip install -r requirements.txt
python -m unittest discover -p 'test_*.py'
python rest_sync.py discover --out capabilities.json # requires private AIT_AGENT_KEY
```
`sync_config.example.json` is intentionally inert (`jobs: []`). After authenticated capability discovery, an authorized agent can explicitly configure only chapter/event-scoped operations and test on a single event. `import_snapshot.py` also requires a `--policy` file.

## Next technical actions
1. Connect AIT securely in ChatGPT or Codex runtime. Do not solicit the secret in chat.
2. Discover actual API operations / filters, and prove chapter-scoping for one **Paris or Lima** meetup using a small read-only query.
3. Verify response chapter/evaluation fields; define API jobs in a **private** `sync_config.json`, keep the approved tokens only there.
4. Test incremental sync, import, opportunity inference, and duplicate handling with evidence, keeping private data in Library/authorized storage.
5. Evaluate whether the published ChatGPT Site can securely ingest projections; do not presume write access or automatic operation.