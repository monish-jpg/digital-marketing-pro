# Changelog

All notable changes to the Digital Marketing Pro plugin are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This project uses [Semantic Versioning](https://semver.org/).

## [3.7.11] — 2026-05-26

**Closes the resolver loop: actions can now actually fire HTTP requests from Python.** v3.7.10 introduced a resolver that returned a manifest of "what would be sent" when a connector was configured. v3.7.11 introduces `scripts/connector_executor.py` (stdlib `urllib.request`, no third-party deps) that takes that manifest and actually executes the request against the real API, with credential substitution, write-op gates, audit logging, and per-endpoint success-code handling.

### What can execute end-to-end from Python (8 connectors, verified docs)

Verified against current vendor docs (May 2026 research pass — see CHANGELOG source citations below):

| Connector | Env var | Auth pattern | Endpoint examples |
|-----------|---------|--------------|---------------------|
| Slack | `SLACK_BOT_TOKEN` | `Authorization: Bearer xoxb-...` | `POST /api/chat.postMessage` (HTTP 200 + body.ok=true required) |
| HubSpot | `HUBSPOT_PRIVATE_APP_TOKEN` | `Authorization: Bearer pat-...` | `GET /automation/v4/flows`, `POST /marketing/v3/campaigns` (201) |
| Klaviyo | `KLAVIYO_PRIVATE_KEY` | `Authorization: Klaviyo-API-Key ...` + revision `2026-04-15` | `GET /api/flows`, `PATCH /api/flows/{id}` (vnd.api+json) |
| SendGrid | `SENDGRID_API_KEY` | `Authorization: Bearer SG.xxx` | `POST /v3/mail/send` (202 + empty body) |
| Brevo | `BREVO_API_KEY` | `api-key:` header (lowercase, NOT Authorization) | `POST /v3/smtp/email` (201) |
| Customer.io | `CUSTOMERIO_APP_API_KEY` | `Authorization: Bearer <App-API-key>` (App key, NOT Site/Track) | `POST /v1/send/email` |
| Mailchimp | `MAILCHIMP_API_KEY` | `Authorization: Basic <base64(anystring:key)>`, dc from key suffix | `GET /3.0/automations` |
| Ahrefs | `AHREFS_API_KEY` | `Authorization: Bearer ...` | `GET /v3/site-explorer/metrics` (not `/overview`) |

### What requires the MCP path (25 OAuth-only connectors)

Cannot execute from Python because OAuth flows require a browser redirect. The resolver still returns `manifest_ready` with the exact request shape, and the executor returns `execute_blocked_reason: "use MCP path"` with an `alternative` field pointing to the MCP route:

Google Ads, Meta Marketing, LinkedIn Marketing, LinkedIn Publishing, TikTok Ads, Twitter/X (OAuth 1.0a HMAC), Gmail, Google Calendar, Google Analytics, Google Search Console, Meta Graph (organic), Salesforce, Pipedrive, Zoho CRM, Buffer, Hootsuite, Cision, Muckrack, Amplitude, Similarweb, SEMrush, Moz, Intercom, Canva, Figma.

### Safety gates (all 6 tested)

1. **No `--execute`** -> dry-run, returns resolver manifest, no HTTP fired
2. **Write op without `--confirm`** -> blocked with reason naming the action
3. **OAuth-only connector** -> blocked with `alternative` MCP path hint
4. **Missing env var credential** -> blocked with `setup_hint_credential` naming the var
5. **Unconfigured connector** -> blocked at resolver level (`stub_unconfigured`)
6. **Unresolved `{VAR}` placeholder** -> request NEVER sent (prevents leaking placeholder text to APIs)

Every executed call is logged to `~/.claude-marketing/{brand}/executions/exec-{connector}-{action}-{ts}.json` with HTTP status, elapsed_ms, success/failure, and any error reason.

### Manifest corrections from research pass

The May 2026 doc verification surfaced 6 errors in the v3.7.10 manifests, now fixed:

1. **Klaviyo `revision` header** — bumped from `2024-10-15` (18 months stale) to `2026-04-15`
2. **Klaviyo PATCH `Content-Type`** — was `application/json` (rejected by API), now `application/vnd.api+json` per JSON:API spec
3. **Ahrefs site-explorer URL** — was `/v3/site-explorer/overview` (doesn't exist), now `/v3/site-explorer/metrics`
4. **Brevo auth note** — clarified custom lowercase `api-key:` header, NOT `Authorization: Bearer`
5. **SendGrid success code** — documented that 202 is success (not 200) per async-queue behavior
6. **Slack success check** — documented that HTTP 200 with `body.ok=false` is logical failure (chat.postMessage returns 200 even on `channel_not_found` errors); executor now does the body.ok check

### Added

- **`scripts/connector_executor.py`** — stdlib HTTP executor. Public API: `execute_manifest(http_request, env, data, timeout, connector)` for direct manifest execution; `execute_action(action_id, brand, execute, confirm, data, timeout, log_to_tracker, env, **kwargs)` for resolve+execute orchestration. `EXECUTE_PROFILES` table holds per-connector env var + auth handler + success codes + post-checks. CLI mode supports dry-run / execute / confirm / data flags.
- **`commands/execute-action.md`** — `/digital-marketing-pro:execute-action` slash command. Wraps `connector_executor.py` with full safety-gate documentation, executable-vs-OAuth-only matrix, and 6 worked examples covering dry-run, read-op execute, write-op execute, blocked-without-confirm, OAuth-only, missing-credential.
- **`_shared/dmp_executor_test_harness.py`** — 17 tests against a stdlib `http.server` mock HTTP server in a daemon thread. Coverage:
  - 8 connector-specific tests (Slack incl. body.ok check + logical-failure variant, HubSpot read + write, Klaviyo list + PATCH with vnd.api+json, SendGrid 202, Brevo lowercase header, Mailchimp Basic auth)
  - 6 safety-gate tests (OAuth-only blocks, write requires confirm, missing credential, unconfigured connector, 404 = failure, network error = clean status, unresolved placeholder NEVER fires)
  - 1 utility test (data-substitution from `{plan.field}` placeholders)

### Changed

- Plugin command count: 13 -> 14 (`/digital-marketing-pro:execute-action` added)
- Script count: 76 -> 77 (`connector_executor.py` added)
- Manifest builders in `connector_resolver.py` updated with the 6 corrections above

### Anthropic submission readiness

- 17/17 mock-server tests pass (covers actual HTTP send-and-receive against a real local server, not just request shape inspection)
- 27/27 resolver tests still pass (no regressions from v3.7.10)
- Every executable endpoint cited to its current vendor documentation
- OAuth-only connectors honestly flagged with explicit MCP fallback path
- All safety gates tested

### Source citations for executable endpoints

- Slack `chat.postMessage` — https://docs.slack.dev/reference/methods/chat.postMessage
- HubSpot `/marketing/v3/campaigns` — https://developers.hubspot.com/docs/reference/api/marketing/campaigns
- HubSpot `/automation/v4/flows` — https://developers.hubspot.com/docs/guides/api/automation/create-manage-workflows (BETA flag)
- Klaviyo `/api/flows` (list) — https://developers.klaviyo.com/en/reference/get_flows
- Klaviyo `/api/flows/{id}` (PATCH) — https://developers.klaviyo.com/en/reference/update_flow
- SendGrid `/v3/mail/send` — https://www.twilio.com/docs/sendgrid/api-reference/mail-send/mail-send
- Brevo `/v3/smtp/email` — https://developers.brevo.com/reference/sendtransacemail
- Customer.io `/v1/send/email` — https://docs.customer.io/api/app/#operation/sendEmail
- Mailchimp `/3.0/automations` — https://mailchimp.com/developer/marketing/api/automation/list-automations/ (Classic Automations — flag for new tenants)
- Ahrefs `/v3/site-explorer/metrics` — https://docs.ahrefs.com/api/reference/site-explorer/get-metrics

## [3.7.10] — 2026-05-26

**Replaces 14 unconfigured-only action stubs with a connector-aware three-mode resolver.** The v3.7.5–v3.7.7 stubs always returned `status: stub_implementation` no matter what connectors the user had configured. They were honest about being scaffolds but they could not graduate to real calls. v3.7.10 introduces a resolver layer that probes the live connector state and chooses one of three modes per action, every call:

| mode | when it applies |
|------|----------------|
| `real` | The action runs end-to-end with no external API. Currently only `arm-watchdog` (writes a watchdog config to `~/.claude-marketing/{brand}/watchdogs/`). |
| `manifest_ready` | A matching connector is configured. The response includes the exact HTTP request manifest (method, URL, headers, body template, auth pattern) for the orchestrator (Claude via MCP) to execute. For write/launch ops the response sets `approval_required: true`. |
| `stub_unconfigured` | No matching connector is configured. The response includes the manual fallback PLUS copy-paste setup hints with `.mcp.json` snippets, env vars, and a Cowork-compatibility warning. |

### Added

- **`scripts/_connector_registry.py`** — single source of truth for the connector catalog (33 connectors, 11 categories). Imported by both `connector-status.py` and the new resolver. Includes `is_connector_configured(name)` (probes `.mcp.json` membership + env-var presence), `redact_secrets()` for credential-safe response filtering.
- **`scripts/connector_resolver.py`** — the resolver layer. `ACTION_SPECS` table maps each of the 14 actions (`inventory`, `automations`, `cadence`, `diagnostic`, `arm-watchdog`, `audit-workflows`, `create-campaign`, `enable-automation`, `schedule-posts`, `notify-influencers`, `pr-send`, `internal-kickoff`, `launch-ads`, `audit-current`) to its candidate connectors, manifest builder (concrete HTTP request shapes for Google Ads / Meta Marketing / LinkedIn / TikTok / HubSpot / Salesforce / Klaviyo / Mailchimp / Brevo / Customer.io / SendGrid / Gmail / Cision / Muckrack / Slack / Google Calendar / Ahrefs / Similarweb / SEMrush / Google Search Console), and operation type (`read` / `write` / `local`). `arm-watchdog` is fully implemented as a local executor that writes a real watchdog config; the remaining 13 return either `manifest_ready` (one of the candidates is configured) or `stub_unconfigured` (none are).
- **`scripts/action-doctor.py`** — per-action readiness diagnostic. Resolves every action against the live `.mcp.json` + env-var state and reports the mode (`real` / `manifest_ready` / `stub_unconfigured`) for each one, with a one-step unlock guide for the blocked ones. Defensive UTF-8 stdout reconfigure for Windows cp1252 consoles.
- **`commands/doctor.md`** — `/digital-marketing-pro:doctor` slash command. Wraps `action-doctor.py`. The canonical pre-flight check before running `campaign-audit` or `launch-campaign`. Output options: full readiness table, `--summary` one-liner, `--action <id>` drill-in, `--json`.
- **`_shared/dmp_action_test_harness.py`** — comprehensive test harness. For every non-local action, exercises (1) unconfigured mode — empty `.mcp.json` → expects `stub_unconfigured` with `setup_hint.setup_options` populated; (2) configured mode — temporarily writes a single matching connector entry to `.mcp.json` → expects `manifest_ready` with a complete `http_request` shape (method + url + headers/body/params + auth_pattern). For `arm-watchdog`, runs an end-to-end execution test and verifies the watchdog file is written to disk and matches the response. Backs up + restores the user's real `.mcp.json` around every scenario. 27 total scenarios; all pass.

### Changed

- **`scripts/performance-monitor.py`** — `inventory`, `automations`, `cadence`, `diagnostic`, `arm-watchdog` actions now delegate to `connector_resolver.resolve_action()`. The inline `_stub_action()` helper from v3.7.6 is removed.
- **`scripts/crm-sync.py`** — `audit-workflows`, `create-campaign` actions now delegate to the resolver. Inline `_stub_action()` removed.
- **`scripts/execution-tracker.py`** — `enable-automation`, `schedule-posts`, `notify-influencers`, `pr-send`, `internal-kickoff`, `launch-ads` actions now delegate to the resolver. Inline `_stub_action()` removed.
- **`scripts/seo-executor.py`** — `audit-current` action now delegates to the resolver. Inline stub block removed.

### Cross-platform verification

- All new scripts run clean on Windows cp1252 console (UTF-8 stdout reconfigure where needed; otherwise pure ASCII output).
- No Windows-only paths (`pathlib.Path` everywhere, `Path.home()` for user dirs, no hardcoded drive letters).
- No `os.system()` / `shell=True` calls (subprocess uses argv lists).
- HTTP connectors work in Claude Code CLI + IDE + Anthropic Cowork. npx connectors (Salesforce, Google Ads, Meta Marketing, etc.) work in Claude Code only; the resolver flags this in `setup_hint.platforms_warning` so Cowork users know to use the Pipedream/Composio/Zapier aggregator alternatives.

### Anthropic submission readiness

- 27/27 test scenarios pass.
- Every action has a documented purpose, manual fallback, fields-returned schema, and live status (real / manifest_ready / stub_unconfigured) — no silent stubs anywhere.
- Every stub response is self-documenting about how to upgrade itself.

## [3.7.9] — 2026-05-25

**Corrects an inaccuracy in the v3.7.8 README callout.** v3.7.8 said the `/plugin isn't available in this environment` error applies to **claude.ai web chat**. User correction: it also applies to the **Claude Desktop app**. The actual rule: `/plugin` slash commands are supported only in **Claude Code** (CLI / IDE at claude.com/code) and **Anthropic Cowork** — not in the standard Claude chat app, whether browser OR installed desktop.

### Changed

- **`README.md`** — re-worded the "/plugin isn't available" callout in the Updating section + the Quick start install note (line 74) to name both environments accurately.

## [3.7.8] — 2026-05-25

**README fix for the "claude.ai web" gotcha.** User-team report from a CF v3.12.2-cycle WhatsApp screenshot: `/plugin update ...` produces `"/plugin isn't available in this environment"` when used in claude.ai web chat. The plugin is installed (skills show up correctly), but the `/plugin` slash command is not supported in claude.ai web — only in Claude Code CLI / Desktop / Cowork. Same gotcha applies to DMP and to the marketplace.

### Changed

- **`README.md`** — added a prominent "If you see /plugin isn't available in this environment" callout at the top of the Updating section. Recovery paths: (1) **Plugins** UI button at the bottom of the web chat → **Manage plugins** → Remove + Add for a re-pull, OR (2) switch to Claude Code CLI / Desktop / Cowork for the management commands.

## [3.7.7] — 2026-05-25

**Direct fix for "dm pro also taking too long to process" (user-team feedback from the v3.12.2-cycle WhatsApp transcript) + an audit pass that caught 4 additional broken refs missed by v3.7.6.**

### Audit pass — 4 newly-found gaps fixed

Full audit across all 153 SKILL.md + 25 agent + 10 command files (broader than v3.7.6's "just the 3 new skills" audit):

- 2 more missing actions: `execution-tracker.py --action launch-ads`, `seo-executor.py --action audit-current` (called from the v3.7.5 skills, missed in v3.7.6). Both added as stub-implementation handlers.
- 2 broken slash refs in v3.7.5 SKILL.md docs: `/digital-marketing-pro:performance-monitor` (no such skill — corrected to `/digital-marketing-pro:performance-check`) and `/digital-marketing-pro:setup` (no such command — corrected to `/digital-marketing-pro:add-integration`).
- 2 broken internal file refs: `docs/custom-mcp-guide.md` (corrected to `skills/context-engine/custom-mcp-guide.md`) and `skills/context-engine/industry-benchmarks.md` (replaced with the existing `industry-profiles.md` + `channel-families.md` fallback chain).
- Re-audit after fixes: **0 broken slash refs, 0 missing script actions, 0 broken internal file refs**.

### Added — resumable workflows (Shreea's "too long" fix)

- **`scripts/checkpoint-manager.py`** — per-step checkpoint storage for every long DMP workflow. Supports `engagement` (the 12-Part Strategy Flow), `campaign-plan`, `content-engine`, `seo-audit`, `competitor-analysis`, `campaign-audit`, `launch-campaign`, plus a `custom` slot for any other long flow. Subcommands: `init`, `save`, `status`, `load`, `list`, `resume`, `finalize`, `discard`. Atomic writes; stdlib only; works in headless / cron contexts. Ported from the ContentForge v3.12.3 pattern, adapted for DMP's multi-workflow surface (CF was content-only; DMP has 8 distinct long workflows).
- **`commands/resume.md`** — `/digital-marketing-pro:resume [workflow] [run-id]`. Picks the run to resume (auto-pick latest in_progress, or filter by workflow, or explicit run-id), reloads every saved part as context, hands control to the agent/sub-flow that owns the next un-checkpointed part. Warns if `last_updated` > 7 days (market data drifts). Lists all in-progress runs when there's ambiguity.

### Added — dual-copy save (visible output folder)

- **`scripts/output-publisher.py`** — dual-copy publisher. Every artifact a workflow produces now lands in TWO locations: internal tracking copy under `~/.claude-marketing/{brand}/output/{workflow}/...` (system-of-record) AND user-visible copy under `~/Documents/DigitalMarketingPro/{brand}/{workflow}/{YYYY-MM}/{filename}` (visible in Explorer / Finder by default). Override the visible root with `DIGITAL_MARKETING_PRO_PUBLISH_DIR` env var or `--publish-dir`. Subcommands: `publish` (single file), `publish-run` (bulk-publish every artifact in a checkpoint-manager run), `where` (print both paths without copying), `open` (print + open in OS file manager via Windows `start` / macOS `open` / Linux `xdg-open`).
- **`commands/output-folder.md`** — `/digital-marketing-pro:output-folder [brand] [workflow]`. Direct answer to "where did my 50 engagement files save?" Prints the absolute visible path and opens it in the OS file manager. Configuration section documents the env-var override for Dropbox / shared-drive setups.

### Changed

- **`commands/engagement.md`** — added a "Checkpointing (v3.7.7+)" section explaining the per-part `checkpoint-manager.py save` cadence + the `output-publisher.py publish-run` finalize step. The `start` subcommand description now mentions that it opens a checkpoint run automatically.
- **README** — new "Resumable workflows + visible output folder (v3.7.7+)" section above the Model Curator section; new entries in the slash command list for `/resume` + `/output-folder`.
- **plugin.json count fields** — none change (the 3 v3.7.5 skills are still counted; the 2 new commands bring the total from 10 → 12).

### Honesty disclosure

The 12 stub-implementation action handlers added in v3.7.6 are unchanged in v3.7.7 — they still return structured `stub_implementation` contracts, not live API calls. The checkpoint-manager and output-publisher are **fully implemented** (no stubs there).

The /engagement workflow itself is unchanged in runtime — Opus 4.7 still takes ~60 minutes for the full 12-Part Strategy Flow. What's new is that a single interruption no longer means losing 30+ minutes of work. That's the direct addressing of "dm pro also taking too long to process" — the workflow can't be made faster (LLM latency is the dominant cost), but it can be made resilient to interruption.

### Verification

- Full e2e simulation `_shared/dmp_engagement_simulation.py` — 5 scenarios: (A) clean 12-part engagement → dual-copy publish → finalize, (B) interrupt at Part 5 → /resume → continue to Part 12, (C) 3 parallel workflows (engagement + campaign-plan + seo-audit) preserved state independently, (D) Part 7 quality-gate fail leaves run in_progress, (E) all 8 workflows accept the checkpoint contract. **5/5 PASS in 5.8 seconds.**
- 12 visible deliverables landed in `~/Documents/DigitalMarketingPro/EngagementSim/engagement/2026-05/` (the user-visible folder) — verified by directory listing.
- All **73 DMP scripts** (was 71, added 2) pass `--help` smoke test; **0** scripts take > 2 seconds on import.
- Sweep across 188 SKILL.md / 25 agents / 167 references files clean.

## [3.7.6] — 2026-05-25

**Wires the v3.7.5 skill surface to actual script implementations.** The 3 new skills shipped in v3.7.5 (`/validate-profile`, `/campaign-audit`, `/launch-campaign`) referenced ~15 script actions that **did not exist** in the underlying Python scripts. The skills were documented but uncallable end-to-end — the orchestrator would dispatch an action and the script would error with `argparse: invalid choice`. Caught by an audit pass mirroring the ContentForge v3.12.3 → v3.12.4 production-simulation fix.

### Added — script action surface that the v3.7.5 skills actually need

- **`scripts/performance-monitor.py`** — 5 new actions: `inventory`, `automations`, `cadence`, `diagnostic`, `arm-watchdog`. Plus new flags `--channel`, `--campaign-id`, `--kpis`, `--read-only`.
- **`scripts/crm-sync.py`** — 2 new actions: `audit-workflows`, `create-campaign`. Plus new flag `--plan` for the approved-plan JSON path.
- **`scripts/execution-tracker.py`** — 5 new actions: `enable-automation`, `schedule-posts`, `notify-influencers`, `pr-send`, `internal-kickoff`. Plus new flags `--plan`, `--automation-id`.
- **`scripts/connector-status.py`** — 2 new flags: `--probe-only` (credential-safe reachability probe used by `/validate-profile`) and `--no-secrets` (walks the response object and redacts any token/secret/password/api_key field before printing). New `_redact_secrets()` and `_probe_only()` helpers.

### Honesty disclosure

Each of the 12 new action handlers in `performance-monitor.py` / `crm-sync.py` / `execution-tracker.py` is a **stub implementation** that returns a structured contract with a `status: "stub_implementation"` field, a `purpose` description, the `data_source` connector that would back it, a `manual_fallback` procedure, and the `fields_returned_when_implemented` schema. The orchestrator gets a clean JSON response it can surface to the user as "this part of the workflow is the design, here is what it would do, here is the manual fallback for now." Live implementation is staged across subsequent releases. The action contract is stable; what's marked `stub_implementation` today will become a live API call as the underlying connectors are integrated.

The `connector-status.py` flags (`--probe-only`, `--no-secrets`) are **fully implemented** — they're a thin wrapper over the existing `check_connector()` function plus a recursive secret-redactor for the response.

### Quality

- All 14 new action invocations return valid structured JSON (`14/14 PASS`).
- All **71 DMP scripts** still pass `--help` smoke test after the additions (no regressions).
- End-to-end `/validate-profile` simulation against a deliberately-broken brand profile correctly produces 1 BLOCKER + 1 WARN + 6 PASSED checks, with credential-safe `--probe-only --no-secrets` connector probes verifying no credential values leak into output.
- Only one DMP script calls LLM APIs at runtime (`ai-visibility-checker.py`) and it correctly uses the model curator from v3.7.4 — no hidden hardcoded model ids elsewhere.

## [3.7.5] — 2026-05-25

**Three new skills shipped to close gaps from the v3.7.4 audit.** No breaking changes.

### Added — 3 new skills (`skills/`)

- **`validate-profile/SKILL.md`** — `/digital-marketing-pro:validate-profile`. The canonical "is this brand ready to ship work?" gate. Validates the brand profile is complete enough for production AND that every connector / MCP / credential it references is actually reachable — without ever printing credential values. Ten validation dimensions: required identity, voice profile, audience profile, guardrails (upgraded to BLOCKER for regulated industries), compliance-jurisdiction cross-check against `compliance-rules.md`, connector reachability (`--no-secrets` probes), MCP server health, credential storage, output-path writeability, model-curator currency. Emits both a human report and a machine-readable JSON summary. **Pre-requisite for `/engagement`, `/campaign-plan`, `/launch-campaign`.**
- **`campaign-audit/SKILL.md`** — `/digital-marketing-pro:campaign-audit`. Cross-channel current-state audit covering paid search, paid social, retail media, email, organic social, content/SEO, AEO/GEO across the 6 AI surfaces (Google AI Mode + Perplexity + ChatGPT search + Claude search + Copilot + Gemini App), CRM/automation, web analytics, influencer/PR, compliance posture. Scores every item across four tiers (🟢 healthy / 🟡 quick win / 🟠 strategic gap / 🔴 red flag) with a configurable spend threshold for waste detection. Produces a single audit document with executive summary, per-channel inventory, cross-channel observations, compliance posture, AEO/GEO snapshot, quick-wins backlog, strategic gaps, red flags, and channels-not-running-that-should-be. Dual-copy save (internal tracking + user-visible `~/Documents/DigitalMarketingPro/{brand}/audits/`) mirroring the ContentForge v3.12.3 pattern.
- **`launch-campaign/SKILL.md`** — `/digital-marketing-pro:launch-campaign`. Multi-channel launch orchestrator — broader than `launch-ad-campaign` (paid-ads only). Takes an approved campaign plan and walks the full 14-step activation in dependency order: CRM Campaign object → landing-page verify → email automation enable → paid search → paid social → retail media → organic social → influencer notification → PR send → internal kickoff → UTM tracking → attribution confirmation → day-1 watchdog → launch record. Refuses to start unless every prerequisite passes (`validate-profile` clean, plan status `approved`, assets reachable, conversion tracking live, EU AI Act Article 50 disclosure verified for EU launches). Dry-run preview mandatory before execution; per-step checkpoint after each action; no auto-retry on failure (day-1 retries create duplicate campaigns / doubled emails); dual-copy launch record.

### Changed — context-engine guides reverted to real skill refs

- **`skills/context-engine/agency-operations-guide.md`** step 8 now points at `/digital-marketing-pro:campaign-audit` directly (v3.7.4 used a workaround chain of `competitor-analysis` + `performance-check` because the skill didn't exist yet).
- **`skills/context-engine/agency-operations-guide.md`** credential-rotation guidance now points at `/digital-marketing-pro:validate-profile --connectors ...` instead of the v3.7.4 workaround of `check` + `status`.
- **`skills/context-engine/crm-integration-guide.md`** Campaign-object creation now references `/digital-marketing-pro:launch-campaign` (with `launch-ad-campaign` cited as the paid-ads-only subset).

### Changed — counts

- `150 skills` → `153 skills` across `README.md` hero + Architecture section + `docs/architecture.md` + `docs/getting-started.md` + `docs/claude-interfaces.md` + `.claude-plugin/plugin.json`. Reality matches: `ls skills/ | wc -l` returns 153.

### Quality

- Per-file content sweep (`_shared/sweep_skill_quality.py`) — **188 SKILL.md + 43 agents + 69 reference docs** clean. Zero issues across frontmatter, slash refs, deprecated model ids, dead MCP URLs, hardcoded paths.

## [3.7.4] — 2026-05-25

**Model curator + correctness sweep.** Adds the model-selection infrastructure the suite was missing, plus a 13-finding correctness pass across scripts, skills, agents, and reference docs.

### Added

- **Model curator (`scripts/model_registry.json` + `scripts/resolve_model.py` + `scripts/refresh_models.py`)** — single source of truth for every model id the plugin hands to a provider SDK. Aliases like `latest-balanced-anthropic`, `latest-fast-anthropic`, `latest-text-openai`, `latest-vision-google`, `latest-image-google`, `latest-video-google`, `latest-video-wavespeed` resolve to concrete ids at call time. Deprecated ids auto-fall-forward to their `replacement_id`. Catalog covers Claude Opus 4.7 / Sonnet 4.7 preview / Sonnet 4.6 / Haiku 4.5; GPT-5 / 5-mini / 5-nano (and supported-but-older 4o / 4o-mini with replacements); Gemini 3 Pro / 3.5 Flash / Omni; Nano Banana Pro / 2 / 3.1 Flash Image; Imagen 4; Veo 3.1; Kling v3.0 Pro via WaveSpeed; Higgsfield Soul v2. `refresh_models.py` reports drift against live provider catalogs (Anthropic / OpenAI / Google list endpoints). See [`docs/MODEL-CURATOR.md`](docs/MODEL-CURATOR.md).
- **`--openai-model` + `--anthropic-model` + `--list-models` flags** on `scripts/ai-visibility-checker.py`. Defaults pull from curator aliases; user overrides validated against the registry with deprecation warnings.

### Changed

- **`scripts/ai-visibility-checker.py`** — replaced the hardcoded deprecated `claude-sonnet-4-5-20250929` and stale `gpt-4o-mini` defaults with curator-resolved `latest-balanced-anthropic` and `latest-balanced-openai`. Per-call model now shown in the result `platform` field (e.g. `Anthropic claude-sonnet-4-6`).
- **Gmail / Calendar / Drive MCP endpoints** — replaced the dead `*.mcp.claude.com` URLs (all returning HTTP 404 as of May 2026) with the Google-hosted equivalents in `.mcp.json.connectors-reference`, `scripts/connector-status.py`, and `TESTING-GUIDE.md`. New endpoints respond with HTTP 405 to GET probes (alive; POST-only as expected for MCP).
- **Slash-command refs in Python error messages** — swept 51 shorthand `/dm:X` references and rewrote to the canonical `/digital-marketing-pro:X` namespace. Claude Code's auto-namespacing does NOT accept the short form, so the previous error messages pointed users at slash commands that wouldn't actually invoke.
- **`skills/context-engine/compliance-rules.md` § 1.11 India — DPDPA** — replaced the stale "rules pending finalization as of early 2025" line. Section now reflects the **Digital Personal Data Protection Rules 2025** (notified by MeitY 3 Jan 2025; phased commencement through 2025-2026), the live Consent Manager framework under Rule 4, the children's targeted-advertising ban, and the Significant Data Fiduciary obligations.
- **`docs/c2pa-production-cert-guide.md`** — replaced the broken `contentauthenticity.org/community/cr-cli` URL with the working `opensource.contentauthenticity.org/docs/c2patool/` and corrected the framing (open-source `c2patool` CLI, not an Adobe-only program).
- **`skills/status/SKILL.md`** — removed hardcoded `/Users/indra/.claude-marketing` example, replaced with `~/.claude-marketing` and a note about `$CLAUDE_PLUGIN_DATA`.
- **`skills/influencer-brief/SKILL.md`** — added Sora deprecation note (consumer Sora app discontinued 26 Apr 2026; Sora API ends 24 Sep 2026) to the AI-tool clauses, with Veo 3.1 / Kling v3.0 Pro / Runway Gen-4 as the recommended set.
- **`agents/seo-specialist.md` + CHANGELOG entries + `skills/page-seo-analysis/SKILL.md` + `skills/sitemap-manager/SKILL.md`** — fixed broken slash refs `/digital-marketing-pro:page-analysis` (skill is named `page-seo-analysis`) and `/digital-marketing-pro:sitemap` (skill is named `sitemap-manager`).
- **`skills/context-engine/agency-operations-guide.md`** — replaced references to non-existent `/digital-marketing-pro:campaign-audit` and `/digital-marketing-pro:validate-profile` with concrete chains of existing skills (`competitor-analysis` + `performance-check`; `check` + `status`).
- **`skills/context-engine/crm-integration-guide.md`** — `launch-campaign` → `launch-ad-campaign` (the actual skill name).

### Quality

- Smoke-tested every Python script via `--help` — **102 of 103 scripts** return valid usage (1 timeout on first-run pip auto-install of `pyairtable`; pre-existing UX issue, not a regression).
- Per-file content sweep across **185 SKILL.md + 43 agent files + 69 reference docs** for: frontmatter validity, slash-shorthand refs, deprecated model ids, dead MCP URLs, hardcoded local paths. **Zero issues** after the sweeps.
- License compliance: MIT across all 4 manifests; zero GPL-licensed Python imports detected.

## [3.7.3] — 2026-05-24

**Community-standards + Star History.** Patch bump — no functional changes.

### Added

- **`CODE_OF_CONDUCT.md`** — Contributor Covenant v2.1, adapted with project-specific scope (Neelverse Marketing Suite, related repositories, Discussions, Issues, PRs). Five-step enforcement ladder (Correction → Warning → Temporary Ban → Permanent Ban). Reporting routed through the maintainer contact at [indranil.in](https://indranil.in) or GitHub Private Security Advisories.
- **`SECURITY.md`** — Supported-versions table, private vulnerability reporting via GitHub Private Security Advisories (no public Issues for security), coordinated-disclosure timeline (Day 0 ack → Day 7 assessment → Day 30 patch → Day 45 public advisory), scope boundaries (in scope vs upstream-vendor scope), hardening recommendations for operators (don't commit `.mcp.json`, treat `~/.claude-marketing/` as sensitive, rotate API keys quarterly, review SKILL.md PRs as production code, pin version in agency environments).
- **`.github/PULL_REQUEST_TEMPLATE.md`** — checklist covering platform coverage (5 surfaces), version-bump-in-all-sibling-manifests reminder, compliance-source requirement (primary source only — Wikipedia / blog posts NOT acceptable), AI-content disclosure clause.
- **Star History chart** in README — live SVG via star-history.com showing 112-star trajectory. Visual social proof for first-time visitors.
- **`Contributing` section in README** now references CoC + PR template + SECURITY.md explicitly so contributors land on the right artefacts.

### Why this matters

GitHub computes a "Community Standards" score under the repo's Insights tab. Repos with all four (Description, README, Code of Conduct, Contributing, License, Issue templates, PR template, Security policy) get a green checklist that increases organic discovery and contributor trust. v3.7.3 closes the three gaps DMP still had (CoC, SECURITY, PR template).

### Compatibility

- No functional changes. No new commands, skills, agents, scripts, or MCP connectors.
- All 4 sibling manifests bumped 3.7.2 → 3.7.3.
- Plugin version: 3.7.2 → 3.7.3 (patch — community-standards files + Star History).

---

## [3.7.2] — 2026-05-24

**Personal-handles correction.** Patch bump — README only.

### Fixed

- The v3.7.1 "Star + share" CTA at the bottom of the maintainer section used `@neelverse` as a social-handle suggestion. That's the **product/suite brand name**, not Indranil's personal handle. Corrected to use Indranil's actual handles across LinkedIn and X:
  - **LinkedIn:** [linkedin.com/in/askneelnow](https://www.linkedin.com/in/askneelnow)
  - **X / Twitter:** [@askneelnow](https://x.com/askneelnow)

### Changed

- "About the maintainer" links block now includes LinkedIn and X rows alongside Website, GitHub, Other plugins, Discussions, and Issues — so readers can one-click follow Indranil on the platform they prefer.
- The keyword `"neelverse"` in `plugin.json` stays — it's a brand/marketplace-search keyword, not a social handle.
- "Neelverse Marketing Suite" branding throughout the README is preserved — that's the correct name for the bundle of DMP + ContentForge + SocialForge.

### Compatibility

- No functional changes. No new commands, skills, agents, scripts, or MCP connectors.
- All 4 sibling manifests bumped 3.7.1 → 3.7.2.
- Plugin version: 3.7.1 → 3.7.2 (patch — README + branding correction only).

---

## [3.7.1] — 2026-05-24

**Polish + discoverability pass.** No functional changes; no new commands, skills, agents, or scripts. Patch bump for a comprehensive README rewrite and a sweep of stale asset counts across the docs.

### Changed

#### README rewrite for organic GitHub + AI-engine discoverability

- **Hero section rewritten** — leads with a tweet-worthy one-liner positioning DM Pro as "the most comprehensive open-source AI marketing plugin" and the only one installable on 5 coding-agent surfaces. Adds GitHub stars / forks / issues / last-commit badges (live counts from shields.io), Cowork-compatible badge, EU AI Act Article 50 badge, and a "5 platforms" badge. Install command moved to the top of the document.
- **New "Why Digital Marketing Pro" section** — explicit differentiator vs ad-hoc prompts. Six-row comparison table covering canonical 12-Part Flow, Two-Views Model, Decision Matrix, Living Project Instruction File, EU AI Act readiness, 6-platform AEO/GEO audit.
- **New "What you get in 60 minutes" section** — outcome-focused list of the ~50–60 canonical files produced by `/digital-marketing-pro:engagement` with explicit API-spend range ($15–40 on Opus 4.7) and time estimate.
- **New "Installs on 5 coding-agent surfaces" matrix** — install commands per platform (Claude Code, Codex, Cursor, Copilot CLI, Antigravity) with status per platform and a one-sentence "why this works without code duplication" (Agent Skills became an open standard in Dec 2025).
- **Compliance section restructured** — adds flag emojis per jurisdiction for visual scannability, hoists EU AI Act Article 50 readiness as a sub-section with explicit C2PA + pre-publish-gate + production-cert-guide references.
- **AEO/GEO section restructured** — "6-platform audit standard" called out (was 5 before AI Mode added in v3.5). Lists exact platforms (ChatGPT, Perplexity, Google AI Mode, Google AI Overviews, Gemini, Microsoft Copilot).
- **New "About the maintainer" section** — author block with website link ([indranil.in](https://indranil.in)), GitHub, other Neelverse plugins, Discussions, Issues, and the "why this plugin exists" story.
- **New FAQ entries** — comparison vs LangChain marketing templates / CrewAI marketing crews, per-engagement API cost ($15–40), cross-platform support clarification, "is this an Anthropic product?" disambiguation.
- **⭐ Star CTAs** added at hero, maintainer section, and footer. Footer "Made with care by Indranil Banerjee · Powered by Anthropic Claude · MIT-licensed" line at bottom.
- **SEO keyword density** improved throughout — "AI marketing plugin", "Claude Code marketing", "Google AI Mode", "EU AI Act Article 50", "C2PA content provenance", "OpenAI Codex marketing", "GitHub Copilot CLI marketing", "agency operations", "multi-brand marketing", "agent skills standard".

#### Stale asset counts swept across docs

| File | Before | After |
|---|---|---|
| `docs/claude-interfaces.md` | "13 specialist agents" | "25 specialist agents" |
| `docs/claude-interfaces.md` | "117 reference files" | "167 reference files" |
| `docs/claude-interfaces.md` | "34 Python scripts" | "69 Python scripts" |
| `docs/claude-interfaces.md` | "42 commands" | "10 commands" |
| `docs/claude-interfaces.md` | "18 MCP integrations" | "14 HTTP MCP connectors" |
| `docs/architecture.md` | "149 skills total" | "150 skills total" |
| `docs/getting-started.md` | "149 skills" (×3 places) | "150 skills" |
| `docs/competitor-intelligence.md` | "117 reference knowledge files" | "167 reference knowledge files" |
| `docs/cross-platform-install.md` | "71 Python scripts" (×4 places) | "69 Python scripts" |
| `skills/context-engine/memory-architecture.md` | "All 13 agents" | "All 25 agents" |
| `.claude-plugin/plugin.json` description | "71 Python scripts, 16 industry profiles, 16 privacy-law jurisdictions" | "69 Python scripts, 16 privacy-law jurisdictions" (industry-profiles claim removed pending re-count) |

Audit method: JSON-validated all 6 manifest/config files (`.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, `.cursor-plugin/plugin.json`, `.antigravity/plugin.json`, `.mcp.json`, `hooks/hooks.json`). Smoke-tested all 69 Python scripts via `python3 <script> --help` (69 pass, 0 fail). Verified all 150 SKILL.md files have valid `name:` + `description:` frontmatter. Checked all internal markdown links in README.md for broken references (none found).

#### Plugin manifest keywords expanded for GitHub + marketplace search

Added: `marketing-automation`, `marketing-plugin`, `ai-marketing`, `ai-mode`, `ai-overviews`, `generative-engine-optimization`, `answer-engine-optimization`, `google-ai-mode`, `performance-max`, `advantage-plus`, `content-strategy`, `brand-guidelines`, `gdpr`, `ccpa`, `eu-ai-act`, `article-50`, `c2pa`, `content-provenance`, `synthid`, `deepfake-disclosure`, `claude-code-plugin`, `claude-skills`, `agent-skills`, `anthropic-claude`, `openai-codex`, `cursor-plugin`, `github-copilot`, `antigravity`, `mcp`, `model-context-protocol`, `gemini`, `nano-banana-pro`, `veo-3`, `gemini-omni`, `neelverse`. Total keyword count: 26 → 61.

### Compatibility

- No breaking changes. All previous v3.7.x commands, skills, agents, scripts, and MCP connectors continue to work unchanged.
- Plugin version: 3.7.0 → 3.7.1 (patch bump — docs + branding only).
- All 4 sibling manifests bumped to 3.7.1 (`.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/`, `.antigravity/`).
- Skills count, agents count, commands count, scripts count: unchanged from v3.7.0.

---

## [3.7.0] — 2026-05-24

**Install-surface expansion: GitHub Copilot CLI (auto-discovered) + Google Antigravity 2.0 (experimental).** DM Pro now installs cleanly on five coding-agent surfaces from a single source repository — Claude Code (canonical), OpenAI Codex, Cursor (added v3.6), GitHub Copilot CLI, and Google Antigravity 2.0 (experimental). No new core dependencies; same 150 skills, same scripts, same MCP catalog.

### Added

- **GitHub Copilot CLI compatibility — no new manifest needed.** Copilot CLI's plugin discovery explicitly checks `.claude-plugin/plugin.json` as one of its accepted manifest paths (alongside `.plugin/plugin.json`, `plugin.json`, and `.github/plugin/plugin.json`). DM Pro's existing Claude Code manifest is therefore directly readable by Copilot CLI. Install: `copilot plugin install indranilbanerjee/digital-marketing-pro`. The MCP catalog (`.mcp.json`), hooks (`hooks/hooks.json`), and SKILL.md auto-discovery all work natively.
- **`.antigravity/plugin.json`** — Experimental manifest for Google Antigravity 2.0 CLI (launched 19 May 2026 at Google I/O, replacing Gemini CLI). Mirrors the Gemini-CLI-extensions format that Antigravity's `agy plugin import gemini` converter accepts. Includes a `_status` field flagging the experimental nature. Will be updated against the v2-native plugin spec when Google publishes it.
- **`docs/cross-platform-install.md` — expanded** to cover all 5 platforms with: install commands, what works natively per platform, the Antigravity caveat (spec not yet public — Gemini-extensions importer is the most reliable current path), `agy plugin import gemini` workflow, update commands per platform, and where to file platform-specific bugs.

### Why Copilot CLI works without a new manifest

GitHub Copilot CLI plugin discovery (May 2026 Public Preview) is intentionally inclusive — it accepts `.claude-plugin/plugin.json`, `.plugin/plugin.json`, `plugin.json`, and `.github/plugin/plugin.json` interchangeably. The manifest format (name, version, description, skills, mcpServers, hooks fields) is a near-superset of Claude Code's, so the existing DM Pro manifest is directly readable. Skills, MCP, and hooks all auto-load without modification.

### Why Antigravity ships as experimental

Antigravity CLI (announced 19 May 2026) preserves Gemini CLI's plugin concepts but has not yet published an open v2-native plugin manifest spec. Third-party plugin libraries (e.g., antigravity-awesome-skills) currently distribute via Antigravity's Gemini-CLI-extensions importer (`agy plugin import gemini`). DM Pro ships an experimental `.antigravity/plugin.json` against the same format the importer accepts; when Google publishes the v2-native spec, this will be updated and the experimental flag removed.

### Compatibility

- No breaking changes for existing Claude Code, Codex, or Cursor users.
- Plugin version: 3.6.0 → 3.7.0 (minor bump — new install surfaces, no breaking changes).
- Files added: 1 (`.antigravity/plugin.json`); 1 expanded (`docs/cross-platform-install.md`).
- Skills count, agents count, commands count, scripts count: unchanged from v3.6.0.

---

## [3.6.0] — 2026-05-24

**Cross-platform compatibility pack.** Digital Marketing Pro now installs cleanly on three coding-agent surfaces from a single source repository — Claude Code (canonical), OpenAI Codex, and Cursor — by adding platform-native manifest files alongside the existing Claude Code manifest. No skill duplication: all three platforms read the same `skills/` directory, the same `scripts/`, the same `.mcp.json`, and the same `hooks/hooks.json`.

### Added

- **`.codex-plugin/plugin.json`** — OpenAI Codex plugin manifest. Includes the `interface` block (displayName, shortDescription, longDescription, category, capabilities, defaultPrompt) Codex uses to render the plugin in its install surfaces. Points at `./skills/`, `./.mcp.json`, `./hooks/hooks.json` — same directories Claude Code reads.
- **`.cursor-plugin/plugin.json`** — Cursor plugin manifest. Minimal manifest (Cursor only requires `name`) plus author, repository, license, keywords, and skills path. Cursor auto-discovers `skills/` via the open SKILL.md frontmatter standard.
- **`docs/cross-platform-install.md`** — Full install guide covering all three platforms with: install commands per platform, what works natively vs what requires platform-specific configuration (notably Cursor's global mcp.json paste step), portability matrix, update commands per platform, and where to file platform-specific bugs.

### Why this works without code duplication

Agent Skills became an open standard (donated to the Agentic AI Foundation, Dec 2025; adopted by 32+ tools by May 2026). All three target platforms — Claude Code, Codex, Cursor — parse the same `name:` + `description:` SKILL.md frontmatter the same way. DM Pro's 150 skills are platform-portable as written; the v3.6.0 manifests are thin platform-specific wrappers around shared content.

### Platform-specific gotchas (documented in cross-platform-install.md)

| Gotcha | Affects | Workaround |
|---|---|---|
| Cursor reads MCP from global `mcp.json` (no leading dot), not from plugin-scoped `.mcp.json` | Cursor only | One-time paste of `.mcp.json` contents into Cursor → Settings → MCP Servers (documented step) |
| Codex slash-command syntax differs (`/cmds` vs Claude Code's `/<plugin>:<command>`) | Codex only | Skills are invoked via natural-language intent on Codex; outputs are equivalent |
| Sub-agent format differs across platforms | Codex, Cursor | DM Pro skills embed agent instructions inline so outputs are equivalent on platforms without Claude Code sub-agent support |

### Compatibility

- No breaking changes for Claude Code users.
- No new dependencies — the new manifests are sibling JSON files; existing tooling untouched.
- Plugin version: 3.5.0 → 3.6.0 (minor bump — new platform surfaces, no breaking changes)
- Files added: 3 (2 manifests + 1 docs)
- Skills count, agents count, commands count, scripts count: unchanged from v3.5.0

---

## [3.5.0] — 2026-05-24

A May-2026-ecosystem modernisation pass covering Google I/O 2026, the active broad core algorithm update, EU AI Act draft implementing guidelines, Meta platform expansions, and Claude Code's new cost-attribution capability. No breaking changes. No new commands or skills — six discrete content updates applied across 14 existing files + 1 script.

### Changed — Six discrete content updates

#### 1. Google AI Mode added as a first-class AEO/GEO surface (5 files)

Google AI Mode (default conversational search since Google I/O on 19 May 2026, ~1B MAUs, Gemini 3.5 Flash backbone) is now tracked as a distinct platform separate from AI Overviews. The 5-platform AEO/GEO testing protocol is now 6-platform. Files updated:

- `skills/aeo-audit/SKILL.md` — Purpose section now explains the AI Mode vs AI Overviews distinction (citations diverge 40–60% for the same query)
- `skills/aeo-geo/SKILL.md` — Module trigger phrases + testing protocol updated to 6 platforms; AI Mode treated as a distinct surface in process steps
- `skills/aeo-geo/ai-visibility-audit.md` — Scoring rubric updated (max per query = 30, not 25), platform-specific notes added for AI Mode (Gemini 3.5 Flash, captures conversational follow-ups), monitoring cadence updated, baseline-normalisation guidance for pre-vs-post May 2026 score comparisons
- `skills/geo-monitor/SKILL.md` — Input "platforms to monitor" now includes AI Mode by default; output scorecard exposes the 6th surface
- `scripts/geo-tracker.py` — `PLATFORMS` list updated to include `ai-mode`; docstring clarifies the AI Mode vs AI Overviews separation. Smoke-tested via `--help`.

#### 2. May 2026 broad core algorithm update triage guidance (2 files)

Google began a broad core update on 21 May 2026 (still in the typical ~2-week deployment window when this ships). Reactive changes during/immediately after a Core Update tend to make things worse — both SEO audit skills now lead with explicit triage guidance:

- `skills/seo-audit/SKILL.md` — Purpose section adds "May 2026 Core Update context" subsection: wait for the rollout + 7–14 days settling before drawing conclusions; segment Search Console data pre/in/post rollout; Core Updates re-weight existing signals (E-E-A-T, content quality) rather than introducing new ones
- `skills/tech-seo-audit/SKILL.md` — Adds the parallel note: run the technical audit anyway (Core Updates surface pre-existing technical debt), but technical "fixes" sold as Core Update remedies won't undo a quality-driven hit

#### 3. EU AI Act Article 50 draft implementing guidelines (1 file, major addition)

The European Commission published draft Article 50 implementing guidelines on **8 May 2026**; public consultation closes **3 June 2026**; final guidelines expected July 2026 ahead of the **2 August 2026** enforcement date. Added as new sub-section §1.1b.i in `skills/context-engine/compliance-rules.md`:

- Six-row clarification table covering: "substantial AI manipulation" definition, "matters of public interest" scope, machine-readable marking (C2PA = presumption of compliance), deepfake visible-disclosure requirements (perceivable at normal viewing distance), editorial-responsibility carve-out conditions, and enforcement priorities
- Five-point action list: audit EU AI-asset inventory now, file consultation comment by 3 June if materially affected, lock in C2PA signing-cert procurement (Adobe approval = 2–4 weeks; start by 1 July), update Definition of Done so creative is C2PA-signed at production time, treat the human-review carve-out as conditional (named accountability required)

#### 4. Meta platform updates — Advantage+ Leads global, Threads ads global, brand-safety controls (1 file)

Three May 2026 Meta updates added to `skills/context-engine/execution-workflows.md` Section 3 (Ad Campaign Workflow):

- **Advantage+ Leads** — now globally available; only works well with Conversions API + CRM-quality feedback; not compatible with Special Ad Categories (housing/credit/employment)
- **Threads ads** — global rollout completing May 2026; image-only formats only; cheap-to-moderate inventory; best for younger / news-adjacent / B2B-thought-leadership; cap at <10% of Meta budget until account-level CPA proves out
- **Brand-safety inventory filters** — three tiers (Expanded/Moderate/Limited); default Moderate; move to Limited only for regulated industries or after a documented incident (Limited costs ~30% reach); Brand Suitability dashboard now exposes Reels topic adjacencies

#### 5. Gemini Omni + Nano Banana Pro + Veo 3.1 in AI creative briefs (4 files)

Added an "AI image & video generation guidance (May 2026)" sub-section to four creative-production skills, with consistent C2PA-by-default and Article 50 disclosure clauses:

- `skills/ad-creative/SKILL.md` — Asset-type-to-model table (Nano Banana Pro for stills with on-image text, Veo 3.1 for short-form video, Gemini Omni for connected multimodal packages); workflow recommendation to hand visual spec to SocialForge `/sf:image` and `/sf:video`
- `skills/content-brief/SKILL.md` — Visual/media spec requires explicit model, provenance marking, deepfake flag, and editorial-responsibility owner for YMYL topics
- `skills/creative-testing-framework/SKILL.md` — AI creative variant production note: cost-per-variant becomes the new floor for minimum-budget math; EU-targeted ad sets blocked unless C2PA-signed
- `skills/influencer-brief/SKILL.md` — Three explicit AI-tool clauses for creator contracts: permitted AI use, required platform disclosures, EU deepfake clause (mandatory for EU placements)

#### 6. Claude Code v2.1.149+ `/usage` per-model breakdown (2 files)

Claude Code v2.1.149 (May 2026) exposes per-model token consumption and projected USD cost via `/usage`. For agencies, this is the cleanest brand-attributable AI-cost source.

- `docs/claude-interfaces.md` — New "Cost tracking" section under Claude Code (Full Support) documenting `/usage`, `/usage --since 7d`, per-directory scoping, and the operational implications for 12-Part engagement billing and Opus-1M context tradeoffs
- `skills/agency-dashboard/SKILL.md` — Process step 8 (team utilization) now pulls `/usage --since 7d` per brand directory; output adds "Claude Code consumption (per brand)" line flagging brands at >2× portfolio median for retainer-tier rate review

### Compatibility

- No breaking changes. All previous v3.4.x commands, skills, agents, scripts, and MCP connectors continue to work unchanged.
- `geo-tracker.py` now accepts `ai-mode` as a platform argument (previously: rejected with argparse error).
- Historical GEO scores baselined pre–May 2026 should be normalised ×1.2 OR rerun against the 6-platform set before comparison. See `skills/aeo-geo/ai-visibility-audit.md`.

### Auditor notes

- Plugin version: 3.4.2 → 3.5.0 (minor bump — new feature surface for AI Mode + Article 50 draft + Gemini Omni; no breaking changes)
- Files modified: 15 (14 SKILL/docs + 1 script)
- Skills count, agents count, commands count: unchanged from v3.4.2

---

## [3.4.2] — 2026-05-17

### Added — Three documentation expansions (no code changes; no breaking changes)

#### 1. Opus 4.7 1M-context guidance in `skills/engagement-workflow/SKILL.md`

The full 12-part engagement (50–60 documents, 250K–600K tokens) now fits in a single conversation when running on Opus 4.7 with the 1M context window (generally available to Max, Team, and Enterprise users as of May 2026). New section documents:

- When 1M context is available: skip LIF re-load between parts, run Parts 1–8 sequentially in one conversation, dispatch Part 9 channel families in parallel, complete Parts 10–12 in the same conversation
- When 1M context is NOT available (Pro tier, third-party API access, batch mode): use the existing engagement-state.py persistence pattern; chunk by Part; re-load LIF at each transition
- The local persistence pattern stays the default — it's correct in both worlds and the only one that works for multi-day / multi-author engagements

#### 2. WhatsApp Business voice calling in `skills/context-engine/india-market-context.md`

WhatsApp Business now supports brand-to-customer voice calls in/out of WhatsApp (May 2026 launch). Use cases: high-AOV consult (real estate, automotive, financial services), post-purchase support, B2B account management. Practical guidance: pilot with a single use case rather than treating it as a broadcast channel; voice calls preserve the 24-hour customer-care window for the next 24 hours after the call ends.

#### 3. May 2026 platform updates in `skills/context-engine/execution-workflows.md` Section 3 (Ad Campaign Workflow)

- **Google Performance Max 2026:** brand exclusion lists first-class, per-network placement reporting exposed, first-party audience exclusions, 15 videos per asset group (was 5), PMax experiments. The old "black box" criticism is mostly addressed.
- **Meta Advantage+ shopping 2026:** in-app checkout, AI product overlays on hover, retailer integrations standard. Creative at product-tile scale, not full-frame. Catalog quality dominates performance.
- **LinkedIn Ads:** March 2026 algorithm shift carries into ad relevance — ads with external links score lower than in-platform formats (lead gen forms, document ads, conversation ads).
- **TikTok Ads (post-USDS Jan 2026):** US-served ads run through USDS LLC infrastructure; AI-generated creative requires AI disclosure label.
- **Retail media (Amazon, Walmart, Instacart):** combined US spend ~$60B+/year in 2026. Worth a campaign track for DTC + CPG brands.

#### 4. New `docs/roadmap-multiagent-sessions-api.md`

Planning document for v3.5 / v4.0 — how DMP would adopt Anthropic's Multiagent Sessions API + Memory for Managed Agents API (both in public beta under the `managed-agents-2026-04-01` Messages API beta header). Three-phase plan: (A) v3.5 dual-write opt-in path, (B) v4.0 flip default to managed-agents with local-file fallback, (C) v4.1+ long-running engagements as managed sessions. Open questions documented: pricing, Cowork compatibility, cross-API-provider availability, migration story. No code in v3.4.2 implements any of this — it's a planning artifact.

### Rationale

User asked what's worth doing next from the May 2026 reality. These three documentation expansions are the small, low-risk content adds; the multi-agent roadmap is the longer-term direction setter. Bundled into one patch release rather than three separate ones because none of them ship code.

---

## [3.4.1] — 2026-05-17

### Fixed — Audit & corrections pass on v3.4.0

User explicitly asked whether the v3.4 work had been audited. Answer: no. Ran a real audit. Found four issues, fixed all four.

#### (1) C2PA script — actually works now

**Problem:** v3.4.0 `scripts/embed-c2pa.py` called `c2pa.create_signer(...)` and `c2pa.sign_file(...)` as top-level module functions. Neither exists in c2pa-python 0.32.6 (the current library). Script would have failed at runtime the first time a user invoked `/digital-marketing-pro:c2pa-metadata`.

**Fix:**
- Rewrote against the real API: `c2pa.Signer.from_info(C2paSignerInfo(...))` → `c2pa.Builder(manifest_json)` → `builder.sign_file(source, dest, signer)`.
- Fixed `C2paSignerInfo` field types (`c_char_p` ctypes — alg=b"es256", cert_bytes, key_bytes, b"http://timestamp.digicert.com").
- Switched manifest assertions label from `c2pa.actions` to `c2pa.actions.v2` (current spec).
- Bound `digital_source_type` via `builder.set_intent(C2paBuilderIntent.CREATE, C2paDigitalSourceType.{TRAINED_ALGORITHMIC_MEDIA|COMPOSITE_WITH_TRAINED_ALGORITHMIC_MEDIA|HUMAN_EDITS})` rather than embedding raw IPTC URIs in the manifest.
- Fixed the self-signed dev cert to include the certificate extensions C2PA requires: BasicConstraints(ca=false, critical), KeyUsage(digital_signature=true, critical), ExtendedKeyUsage(EMAIL_PROTECTION), SubjectKeyIdentifier, AuthorityKeyIdentifier. Without these the C2PA library rejects with "the certificate is invalid".
- Fixed the read-back verification to use `c2pa.Reader(format, stream)` context manager — the prior `Reader.from_file` API doesn't exist either.

**Verified end-to-end:** 75-byte test PNG → 42,818-byte signed PNG. Read-back confirms `active_manifest` ID, title, signer ("Digital Marketing Pro"), cert algorithm "Es256", assertions `["c2pa.actions.v2", "stds.schema-org.CreativeWork"]`, action `c2pa.created (Test Generator)`, CreativeWork.author `[{"@type": "Organization", "name": "Test Brand"}]`. `manifest_embedded_and_verified: true`. Validation state shows "Invalid" only because self-signed certs aren't in C2PA's trust list — production CAI-issued certs validate as "Valid".

#### (2) Unified ads MCP entries — corrected endpoints + coverage

Prior research agent told me Synter endpoint was `https://mcp.synter.com/sse` covering 14 platforms, and Ryze was `https://mcp.ryze.ai/mcp`. Neither matches reality.

**Fix:**
- **Synter (real name: Synter Media AI):** corrected endpoint `https://mcp.syntermedia.ai/mcp/` with `X-Synter-Key` header auth. Platform coverage corrected from claimed 14 to actual 7: Google Ads, Meta Ads, LinkedIn Ads, Microsoft Ads, Reddit Ads, TikTok Ads, X. Source: `github.com/Synter-Media-AI/mcp-server`. Renamed entry from `synter` to `synter-media-ai`.
- **Ryze AI:** corrected entry — it's primarily a managed OAuth connector service at `app.get-ryze.ai/mcp-connector`, not a generic self-serve HTTP MCP. The Google Ads per-platform endpoint is `https://ryze-google-ads-mcp-kyfjuf4chq-uc.a.run.app/mcp`. Coverage clarified: Google Ads primary; separate per-platform connectors for Meta and Google Analytics via the managed OAuth service. Renamed entry from `ryze-ai` to `ryze-ai-google-ads`.
- **Northbeam:** corrected GitHub URL to `github.com/mattcoatsworth/Northbeam-MCP-Server` (community-maintained, NOT first-party from Northbeam Inc — the prior reference implied otherwise). Platform coverage (Google + Meta + LinkedIn + TikTok) verified. Renamed entry from `northbeam-selfhosted` to `northbeam-mcp-selfhosted`.
- Added explicit caveat at top of `_section_unified_ads_mcps`: "Endpoint URLs and platform-coverage claims below were verified May 2026 — re-verify before production use as these are early-stage services."
- `CONNECTORS.md` "Unified ads MCPs" table updated with the corrected URLs, auth, and source-repo links.

#### (3) Parallel-dispatch speedup claim — softened from overstated to honest

**Problem:** v3.4.0 claimed flat "~6× wall-clock speedup" across multiple surfaces (CHANGELOG, README, plugin.json, marketplace.json, engagement-workflow SKILL, competitor-analysis command, seo-audit command). Published Anthropic guidance is more nuanced: 4–6× parallelism with 50–80% wall-clock reduction for 3–8 concurrent subagents; past 8 you queue against rate limits and the win drops; under 3 there's nothing to parallelize.

**Fix:**
- `skills/engagement-workflow/SKILL.md`: replaced overclaim with "4–6× parallelism with roughly 50–80% wall-clock reduction for 3–8 concurrent subagents" + cost note ("total token usage is broadly similar; billed-per-turn input costs trend up slightly because each parallel subagent re-loads its context") + the queue-after-8 caveat.
- `commands/competitor-analysis.md`: changed "parallel → ~6 min wall-clock" to "parallel dispatch reduces this by 50–80% wall-clock per Claude Code's April 2026 parallel-subagent initialization — typical run lands at ~7–17 min (rate-limit dependent)".
- `commands/seo-audit.md`: changed "parallel ~5 min wall-clock" to "parallel dispatch typically lands at ~5–12 min wall-clock (rate-limit dependent) — roughly 50–80% reduction".

#### (4) Submission URLs — removed unverified URL

**Problem:** `SUBMISSION.md` referenced two submission URLs: `https://claude.ai/settings/plugins/submit` (consumer) and `https://platform.claude.com/plugins/submit` (Console). Only the second is verifiable in Anthropic's public docs as of May 2026.

**Fix:** Removed `claude.ai/settings/plugins/submit` references from SUBMISSION.md introduction and the 12-step submission flow. Sole submission URL is now `https://platform.claude.com/plugins/submit`.

### Rationale

User explicitly pushed back on the previous turn's "ship-fast, verify-later" pattern. Audit found exactly the kind of issues that pattern produces: a Python script that won't run, MCP endpoint URLs that don't resolve, performance claims that misrepresent published Anthropic guidance, and a submission URL that may not exist. All four fixed in v3.4.1. The C2PA script is now end-to-end empirically tested — signing succeeds, manifest reads back round-trip, all assertion fields verified.

---

## [3.4.0] — 2026-05-16

### Added — The Four Deferred Items from v3.3 audit

User asked why these were deferred. Answer: sequencing — content/regulatory drift was bleeding trust and shipped first. They're now in.

#### 1. C2PA content provenance (EU AI Act Article 50 compliance)

- **New script** `scripts/embed-c2pa.py` (~250 lines) wrapping `c2pa-python>=0.5.0`. Embeds machine-readable provenance manifests into AI-generated images / video / audio / PDF. Supports `.png .jpg .jpeg .webp .gif .tiff .mp4 .mov .webm .mp3 .wav .pdf`.
- **New skill** `/digital-marketing-pro:c2pa-metadata` at `skills/c2pa-metadata/SKILL.md`. Full doc with usage examples, IPTC digital-source-type vocabulary mapping (ai-generated-content / ai-assisted-edits / ai-no-substantive-changes), signing-certificate guidance (CAI-recognized authority for prod; auto-generated 90-day self-signed cert for dev).
- **Pre-publish gate integration** — `/digital-marketing-pro:check` now treats missing/invalid C2PA manifest on AI-flagged assets in EU-targeted campaigns as a CRITICAL issue (BLOCKED decision). Wired through `commands/check.md`.
- **Compliance rule binding** — new `Section 1.1b EU/EEA — AI Act Article 50 (Generative AI Disclosure)` in `skills/context-engine/compliance-rules.md` documents the regulatory basis, applicability date (2 Aug 2026), penalty (€15M or 3% global turnover), and how the c2pa-metadata skill satisfies the marking requirement.
- **requirements.txt updated** with optional `c2pa-python>=0.5.0` and `cryptography>=42.0` (commented; install only when needed).
- Output is verifiable at https://contentcredentials.org/verify and any C2PA-aware viewer (Photoshop, Lightroom, Truepic).

#### 2. Unified ads-platform MCPs

- **New `_section_unified_ads_mcps` in `.mcp.json.connectors-reference`** documenting three purpose-built MCPs:
  - **Synter** — 14 platforms in one (Google, Meta, LinkedIn, TikTok, Reddit, Pinterest, Snapchat, X, Microsoft, Taboola, Outbrain, Quora, Spotify, Amazon Ads)
  - **Ryze AI** — Google + Meta + GA4 with confirmation patterns
  - **Northbeam (self-hosted)** — Google + Meta + LinkedIn + TikTok, open-source, BYO OAuth
- **CONNECTORS.md updated** with a new "Unified ads MCPs (added v3.4)" section and a callout on the Advertising row in the npx-only table directing users to the unified options.
- All three are HTTP — fully Cowork-compatible. Replaces the per-platform stdio servers in `.mcp.json.example` for teams who want one ads tool surface instead of four.

#### 3. Parallel subagent dispatch

Leverages Claude Code's **April 2026 parallel-subagent initialization**. Realistic speedup: 4–6× parallelism with ~50–80% wall-clock reduction for 3–8 concurrent subagents (past 8 you queue against rate limits). See v3.4.1 entry above for corrected per-command numbers.

- **`skills/engagement-workflow/SKILL.md`** — new "Parallel Dispatch" section identifies Parts 2 (External Research), 4 (Competitive + Customer + Market), 9 (Channel Strategy Fan-out), 10 (Execution Artefacts), 11 (AI Creative Instructions) as parallel-eligible, with explicit subagent-dispatch instructions. Parts 1→2, 3→4, 5→6, 7→8, 8→9 remain sequential (real data dependencies). New Quality Discipline rule #6: "Always parallelize independent work."
- **`commands/competitor-analysis.md`** — 7 dimensions (content, SEO, paid ads, social, AI visibility, pricing, positioning) dispatched in one message with 7 parallel Task calls. ~35 min sequential → ~6 min parallel. Multi-competitor analyses sequence competitors but parallelize dimensions within each.
- **`commands/seo-audit.md`** — 6 dimensions (technical, on-page, content, E-E-A-T, link profile, AEO) parallel; aggregation + impact-to-effort prioritization sequential. ~25 min sequential → ~5 min parallel.
- **`commands/content-engine.md`** — per-format drafting parallel when multiple formats requested from one brief (blog + 3 socials + email + ad copy → 6 parallel Task calls); SME calibration + quality gate + aggregation sequential.
- **`commands/campaign-plan.md`** — per-channel briefs parallel after channel-mix approval; KPI tree + attribution + reporting cadence parallel in the measurement layer; budget allocation sequential.

#### 4. Anthropic Software Directory submission packet

- **New `SUBMISSION.md` at repo root** pre-stages every input the directory form requires: one-line + long description, category, target audience, 4 working use cases, testing-account/sample-data declaration, ownership verification, compliance-with-policy checklist, Cowork compatibility statement, Verified-badge candidacy assessment, screenshot checklist, step-by-step submission instructions.
- Reduces actual submission at https://claude.ai/settings/plugins/submit from a multi-hour task to ~5 minutes.
- Maintained in the repo so it can be refreshed each release before re-submission.

### Changed

- Skill count bumped from 149 → **150** (new c2pa-metadata skill).
- Script count bumped from 70 → **71** (new embed-c2pa.py script).
- Plugin description in plugin.json + marketplace.json updated to lead with the four v3.4 additions.

### Rationale

The four deferred items from the v3.3 audit aren't optional polish — C2PA is a hard regulatory requirement for EU markets in 81 days (2 Aug 2026); unified ads MCPs eliminate connector sprawl that's been the #2 user complaint; parallel dispatch makes the 12-part engagement viable inside a single conversation rather than an hour-long wait; the directory submission packet is the path to discoverability beyond word-of-mouth.

---

## [3.3.0] — 2026-05-15

### Added — May 2026 Modernization Sweep

Comprehensive refresh against current marketing/regulatory/AI-search reality. **Content + documentation release** — no breaking changes to skills, agents, or scripts.

#### Privacy & Compliance updates (16-jurisdiction matrix)

- **EU AI Act Article 50 (applicable 2 Aug 2026)** — generative-AI marketing content must carry machine-readable C2PA-style watermarks; deepfakes must be visibly disclosed; AI-generated text on matters of public interest must be disclosed. Penalty up to €15M or 3% global turnover.
- **DPDP Phase II preparation (effective 13 Nov 2026)** — consent-manager framework registration window opens. Phase III hard enforcement 13 May 2027 with INR 2.5B max penalty.
- **NY synthetic-performer disclosure law (live June 2026)** — $1K–$5K per violation, $10K repeat. Synthetic influencers and AI-generated endorsements flagged.
- **FTC May 2026 endorsement guidance** — covers synthetic influencers, AI testimonials, AI-edited creator content.
- **CJEU March 2026 ruling** — pseudonymized cookie IDs are personal data when re-identification is feasible.
- **CCPA/CPRA Jan 2026 amendments** — neural networks and AI-derived personal data classified as sensitive. ADMT compliance (Jan 1 2027) flagged.

#### Channel guidance updates

- **LinkedIn (March 2026 algorithm shift)** — external links and engagement bait penalized ~60%; new Depth Score measures dwell time. `social-strategy` and content-engine LinkedIn guidance updated.
- **Email** — Apple MPP affects ~64% of B2C opens; open rate dropped as primary KPI. **DMARC + RFC 8058 one-click POST unsubscribe** mandatory; non-compliant bulk mail to Gmail/Yahoo/Microsoft gets permanent 550 rejections. Spam threshold tightened to <0.10%.
- **TikTok (post Jan 22 2026 USDS Joint Venture closing)** — US data and algorithm under USDS LLC. AI-generated creators allowed only with disclosure; AI content excluded from Creator Rewards Program. Daily shoppable-post limits effective May 11 2026.
- **WhatsApp (per-message pricing since 1 July 2025)** — corrected from deprecated conversation-based model in 3 skill files: `skills/context-engine/execution-workflows.md`, `skills/context-engine/india-market-context.md`, `skills/emerging-channels/conversational-commerce.md`. India marketing template ≈ USD 0.0118 per message. 72-hour free service window from CTWA ads or Page CTAs.
- **Schema strategy refresh** — Google's March 2026 core update demoted FAQ/Review/HowTo schema on non-primary pages. Skills now emphasize entity-rich JSON-LD and produce an LLMs.txt companion file.
- **Sora deprecation note** — OpenAI's consumer Sora app discontinues April 26 2026; Sora API September 24 2026. AI creative briefs default to Runway Gen-4 / Veo 3.x / Kling 3.0.
- **Third-party cookies — deprecation cancelled** — Chrome formally abandoned the timeline. The `attribution-model` skill defaults to first-party + MMM + incrementality stack.

#### AEO / GEO modernization

- Google AI Overviews now appear on ~55% of all Google searches. Organic CTR on AI Overview queries dropped ~61%. ~58% of searches are zero-click.
- Citation-tracking guidance updated for ChatGPT, Perplexity, Google AI Overviews, Claude, Bing Copilot, Gemini.
- For ongoing measurement, integrate with **Profound / Otterly / Conductor AgentStack** via the connectors layer.
- **Share of AI Voice** as a first-class metric in `/digital-marketing-pro:performance-report`.

#### README + Top Commands fixes

- **README fully restructured** to ContentForge v3.9.5 pattern: Quick Start at top with install + auto-update toggle as steps 1-2; "Where your files go" section showing the 12-part engagement directory layout; version histories collapsed at the bottom.
- **Top Commands table corrected** — was using bare `/brand-setup` form that conflicts with other plugins. Now uses canonical `/digital-marketing-pro:brand-setup`.
- **Duplicate "Option C" install heading fixed** (was Option C twice instead of A/B/C/D).
- **Top version badge bumped** from 3.2.0 → 3.3.0 (was two patches stale).
- **Auto-update guidance** — explicit two-option flow (toggle vs manual uninstall+reinstall) since third-party marketplaces have auto-update OFF by default.
- **Cowork install correctness** — Cowork is the Anthropic Desktop computer-use product with local filesystem access; full DM Pro pipeline including all 70 Python scripts runs natively. Only Cowork-specific limitation is HTTP MCPs only.
- **Script count corrected** from "68 Python scripts" to actual file count of 70.
- **Two PDF references at repo root** documented (`DM_Strategy_Complete_Learning_Guide.pdf` and `DM_Strategy_Flow_v3_2_Visualization_v1_23Apr26.pdf`).

### Rationale

Marketing tech moves quarterly. A plugin that documents WhatsApp's per-conversation pricing (deprecated July 2025) or treats email open rate as a primary KPI (Apple MPP affects 64% of B2C opens) erodes user trust. v3.3 brings DM Pro's content surface up to the May 2026 reality.

---

## [3.2.2] — 2026-05-09

### Fixed — Slash Command Namespace Consistency

All `/dm:` references in docs and runtime files swept to the canonical `/digital-marketing-pro:` form that Claude Code auto-namespacing actually produces. The `/dm:` shorthand was used in ~600 places across README, getting-started, TESTING-GUIDE, engagement-methodology, multi-brand-guide, brand-guidelines, architecture, v3.2-opt-ins, all agent files, all 149 skill SKILL.md files, command files, and the CHANGELOG. Users can now copy-paste any command from any doc and have it work.

The replacements include agent files (content-creator, email-specialist, social-media-manager, pr-outreach, quality-assurance, seo-specialist) which emit slash command recommendations during execution. Before this release, agents may have been emitting commands that didn't match the documented namespace.

Skill filenames preserved.

No behavioral changes. If `/dm:` shortcuts work in your environment they'll continue to work; this just makes the docs match the documented Claude Code namespace pattern.

---

## [3.2.1] — 2026-05-03

### Fixed — Plugin Manifest Install Format (CRITICAL)

The plugin manifest format that v3.0 inherited (and v3.1.1 / v3.2.0 carried forward) used two fields that Claude Code's plugin schema does not accept, causing `claude plugins install digital-marketing-pro` to fail with "the manifest's `repository` field is an object when Claude Code expects a string." This release fixes both issues so install works.

#### Changes

- **`repository` field**: converted from npm-shorthand object form (`{type: "git", url: "..."}`) to the string URL form Claude Code's plugin schema requires. New value: `"https://github.com/indranilbanerjee/digital-marketing-pro.git"`.
- **`$schema` field removed**: Claude Code's plugin schema parser rejects this top-level key. Editor validation benefit isn't worth a broken install.

Same fixes shipped same-day to ContentForge v3.9.2, SocialForge v1.5.2, and marketplace v2.8.0.

### Migration

Pure manifest fix. No behavioral changes; the v3.2 12-Part Methodology + opt-in safety nets continue to work identically.

---

## [3.2.0] — 2026-05-03

### Added — Closing the v3.1 Hook-Removal Gaps

v3.1 removed all four global hooks for multi-plugin coexistence (the `PreToolUse mcp_.*` matcher in particular was intercepting every MCP call from every installed plugin). That fix was correct, but it left real gaps — most notably, the loss of automatic hallucination detection on every Write/Edit operation. v3.2 closes those gaps with explicit on-demand replacements, agent-embedded safety, and opt-in ambient capture — without bringing back the global-scoping problem.

#### New: `/digital-marketing-pro:check` — explicit pre-publish quality gate

Replaces the `PreToolUse Write|Edit` global hook. Wraps `scripts/eval-runner.py` (the master eval orchestrator) and produces a single PASS / WARN / BLOCKED decision with actionable issues. Three modes:

- `/digital-marketing-pro:check <file>` → quick eval (~2s, no external deps): hallucination + content quality + readability
- `/digital-marketing-pro:check <file> --full --brand <slug>` → full 6-dimension eval including brand voice + claims + structure
- `/digital-marketing-pro:check <file> --compliance --brand <slug> --evidence <facts.json> --schema <name>` → compliance-focused for regulated industries

New files:
- `commands/check.md`
- `skills/check/SKILL.md`

#### New: `/digital-marketing-pro:status` — unified on-demand brand snapshot

Replaces the `SessionStart` global hook (which printed a brand summary banner at every Claude Code launch in every project). Richer than the old banner: brand profile, all engagements with current part + days-since-update + pending decisions + versioned doc count, recent insights with last-save age, recent compliance violations, Python dependency mode. Five subcommand modes:

- `/digital-marketing-pro:status` → full snapshot for active brand
- `/digital-marketing-pro:status --quiet` → one-line compact summary
- `/digital-marketing-pro:status --json` → machine-readable JSON for downstream skills
- `/digital-marketing-pro:status --brand <slug>` → snapshot for a specific brand
- `/digital-marketing-pro:status --section <brand|engagements|insights|compliance|deps>` → single section

New files:
- `commands/status.md`
- `skills/status/SKILL.md`
- `scripts/dm-status.py` (560-line script; reads brand profile + engagement state + insights + violations + deps; never modifies state)

#### Embedded mandatory hallucination check in 4 content-producer agents

Replaces the `PreToolUse Write|Edit` global hook with stronger architectural guarantees. Each agent now runs `hallucination-detector.py` on its final draft before delivering content to the user. Severity-based decision rules:
- `severity: "high"` (placeholder URLs, fabricated stats in headlines, made-up academic citations, unsupported "#1" / "best in industry" / "leading" claims) → DO NOT deliver; return issues + suggested fixes
- `severity: "medium"` (unverified body stats, missing hedging, entities-to-verify) → deliver but include warnings inline
- `severity: "low"` → mention; not blocking
- Overall hallucination_score < 60 → flag for revision (PR content uses stricter < 75 threshold)

This is stronger than the v3.0 hook because (a) the check runs on the actual draft the agent intends to deliver, not on every intermediate Write/Edit; (b) the agent has the context to interpret findings appropriately; (c) the check is part of the agent's deliverable contract, not an external gate.

Agents updated:
- `agents/content-creator.md` — Behaviour Rule 12 added
- `agents/email-specialist.md` — Behaviour Rule 11 added
- `agents/social-media-manager.md` — Behaviour Rule 11 added
- `agents/pr-outreach.md` — Behaviour Rule 10 added (with stricter PR-specific thresholds)

#### New: `auto_save_insights` opt-in flag for ambient learning capture

Replaces the `SessionEnd` global hook (which auto-prompted insight saving on every session end across every project). Opt-in per brand:

```json
{
  "auto_save_insights": true,
  "...": "...rest of brand profile..."
}
```

When enabled, marketing agents call `scripts/auto-save-insight.py` at meaningful checkpoints to persist session learnings. When disabled (default), the helper returns `{"status": "no_op"}` — clean no-op, no surprise side effects, no cross-project noise.

New file: `scripts/auto-save-insight.py` (240-line helper with subcommands: save, save with `--force`, `--dry-run`; falls back to direct `insights.json` write if `campaign-tracker.py` cannot resolve the brand).

Atomic writes; honours `CLAUDE_PLUGIN_DATA` env var; respects the same workspace path as `dm-status.py` and `engagement-state.py`.

#### New: `docs/v3.2-opt-ins.md` — comprehensive opt-in guide

Documents:
- What was lost when v3.1 removed each of the four global hooks
- How to re-enable any hook at the user-level (`~/.claude/settings.json`) or project-level (`.claude/settings.local.json`) — this gives users the v3.0 ambient experience without forcing it on the entire plugin user base
- Why the `PreToolUse mcp_.*` matcher should NOT be re-enabled (it intercepts every MCP call from every plugin)
- How `auto_save_insights` works and when to enable it
- How `/digital-marketing-pro:status` and `/digital-marketing-pro:check` map to the removed hooks
- How the embedded agent check is stronger than the v3.0 hook
- Recommended workflow for minimum / opt-in / power-user / project-scoped configurations

#### Plugin manifest

`.claude-plugin/plugin.json` bumped to v3.2.0 with updated description surfacing the new commands, agent updates, opt-in flag, and hook re-enable pattern.

### Compatibility

- All v2.7 + v3.0 + v3.1 capabilities continue to work unchanged
- New skills and scripts are purely additive
- The `auto_save_insights` flag defaults to `false` — opt-in only; existing brand profiles without the flag get no behavioural change
- Hook re-enabling is documented as a user-side action; the plugin still ships zero global hooks

### Migration

No migration needed. To start using the new compensations:

```
# On-demand status snapshot
/digital-marketing-pro:status

# Pre-publish quality gate
/digital-marketing-pro:check drafts/your-content.md --brand <your-slug>

# Enable ambient insight capture (opt-in per brand)
# Edit ~/.claude-marketing/brands/<your-slug>/profile.json:
#   "auto_save_insights": true

# Re-enable v3.0 SessionStart banner at user level (optional)
# Copy SessionStart block from hooks/hooks-reference.example.json into ~/.claude/settings.json
# (Do NOT re-enable the PreToolUse mcp_.* matcher — see docs/v3.2-opt-ins.md)
```

---

## [3.1.1] — 2026-05-03

### Added — Cowork-Compatible Connectors Reference Catalog

The v3.1.0 audit confirmed DMP runs in Anthropic Cowork, but surfaced a documentation gap: the `.mcp.json.example` file ships ~60 stdio/npx MCP servers (Google Analytics, Google Search Console, Google Ads, Meta Marketing, Mailchimp, LinkedIn, TikTok, Salesforce, etc.) — none of which work in Cowork. Cowork users had no documented HTTP path to these services. v3.1.1 adds a reference catalog of HTTP MCP equivalents.

#### New file: [.mcp.json.connectors-reference](.mcp.json.connectors-reference)

Sectioned catalog of 25+ HTTP MCPs covering DMP's full integration surface:

- **First-party marketing MCPs** (already in active `.mcp.json`): HubSpot, Stripe, Klaviyo, Amplitude, Ahrefs, Similarweb — all OAuth, all Cowork-compatible
- **Collaboration & publishing**: Notion, Slack, Asana, Webflow, Canva, Figma, Gmail, Google Calendar
- **Aggregator MCPs for Cowork** — the critical addition. Pipedream entries for Google Analytics, Google Search Console, Google Ads, Google Sheets, Google Drive, Meta Marketing, Mailchimp, LinkedIn, Salesforce, plus a generic template covering Pipedream's 1000+ services. Composio (`https://connect.composio.dev/mcp`), Zapier (`https://mcp.zapier.com/api/v1/connect`), and Make.com as alternatives
- **Image/video generation**: fal-ai, Replicate (covers Stability, Gemini Imagen, FLUX, Recraft, etc.)

Per-entry `_auth` notes document the OAuth flow or API key requirement. Bottom-of-file `_cowork_compatibility_summary` makes the CLI-vs-Cowork mapping explicit.

#### What this means for users

- **Claude Code CLI users**: nothing changes. `.mcp.json.example` still documents the 60+ stdio/npx options, and the active `.mcp.json` (gitignored) still ships the 14 HTTP MCPs you've already configured.
- **Cowork users**: open `.mcp.json.connectors-reference` instead of `.mcp.json.example`. Every category has a Cowork-compatible HTTP path, either via a first-party MCP or via a Pipedream/Composio/Zapier aggregator.

#### Compliance posture

All listed connectors satisfy the [Anthropic Software Directory Policy](https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy): no financial-transaction processing, no advertising delivery, no safety circumvention. All MCPs use OAuth 2.0 or API key auth via the provider's official endpoint.

### Migration

Pure additive release. No breaking changes. Existing connector setups continue to work. Cowork teams gain a documented path for every category previously only available via npx.

---

## [3.1.0] — 2026-05-03

### Changed — Multi-Plugin Coexistence (Removed All Global Hooks)

Audit of the v3.0 install footprint surfaced the same issue that prompted ContentForge v3.9.0 and SocialForge v1.5.0 the same day: Claude Code plugin hooks fire *globally* when the plugin is enabled. There is no per-directory or per-project scoping. DMP's four prior hooks were particularly problematic because one of them — the `PreToolUse mcp_.*` matcher — intercepted EVERY MCP tool call from EVERY installed plugin (Slack, Notion, GitHub MCP, Stripe, anything), forcing a brand-compliance LLM evaluation on every MCP write regardless of whether it had any connection to marketing work.

#### Removed All 4 Global Hooks

[hooks/hooks.json](hooks/hooks.json) now contains an empty `hooks: {}` object plus a `_readme` explaining the rationale. The four prior hooks are preserved with per-hook rationale notes at [hooks/hooks-reference.example.json](hooks/hooks-reference.example.json):

- **SessionStart** — ran `python3 scripts/setup.py --check-deps --summary` on every Claude Code launch in every project. Now run on demand.
- **PreToolUse Write|Edit** — large brand-compliance + hallucination-check prompt fired on every file edit. Compliance and hallucination checks already run inside the agents responsible for generating the marketing content; the hook was a duplicate execution layer with a SKIP guard that still cost a model invocation per edit.
- **PreToolUse mcp_.\*** — the worst offender. Gated every MCP tool call from every plugin through DMP's brand-compliance prompt. A user installing DMP alongside other MCP-using plugins (which is common) saw this prompt fire on every Slack message, every Notion page write, every GitHub PR creation, etc. — even when those operations had nothing to do with marketing. Per-agent decision flows already require explicit user approval for marketing MCP writes.
- **SessionEnd** — insight-saving prompt for marketing work, fired at every session end. Insight capture should be opt-in (run the engagement orchestrator), not automatic.

#### Why It Matters

The mcp_.* matcher meant DMP was effectively becoming a global gatekeeper for every MCP tool call across the user's entire Claude Code installation. That is far beyond DMP's scope of authority. Removing it fixes the most acute multi-plugin coexistence problem in the marketing plugin family.

#### Behavior Preserved

All compliance checks, brand voice enforcement, MCP write approvals, and dependency setup still run — they were always also encoded in the agent files, the engagement orchestrator, and the per-agent decision flows. The hook layer was a duplicate execution path. Removing it produces identical output quality with zero side-effects on other Claude Code work or other installed plugins.

### Migration

No breaking changes to commands, skills, agents, or production behavior. Brand profiles, engagement state, tracking data, and the v3.0 12-Part Methodology are all preserved. If you specifically want a hook back, copy the relevant entry from `hooks/hooks-reference.example.json` into `hooks/hooks.json` — but be aware that the `mcp_.*` matcher will gate every MCP call from every installed plugin.

---

## [3.0.0] — 2026-05-03

### Added — The 12-Part Engagement Methodology

Major release introducing a sequential engagement workflow that transforms the plugin from a catalog of 141 atomic skills into a methodology-driven engagement system. Every brand engagement now runs through 12 canonical parts producing ~50–60 files in a defined structure.

#### New Methodology Layer

- **12-Part Strategy Flow** — sequential engagement workflow from intake through continuous improvement (`skills/context-engine/engagement-flow-methodology.md`)
- **Four Core Documents** — the strategic spine produced in Part 3 with 61 explicit steps across 3.1 Business & SBU Analysis (18 steps), 3.2 Segmentation Framework (15 steps), 3.3 Brand Positioning & Communications (19 steps), 3.4 DMFlow (9 steps) (`skills/context-engine/four-core-documents-spec.md`)
- **Two-Views Model** — v1 unbiased market view + v2 client-validated view; both kept forever for different decision types (`skills/context-engine/two-views-model.md`)
- **Stone vs Opinion intake** — every Part 1 fact tagged with confidence level; Stone facts treated as ground truth, Opinion hypotheses become research questions (`skills/context-engine/stone-vs-opinion.md`)
- **Decision Matrix for v2 Re-runs** — explicit mapping of client validation responses to which Core Documents need re-running (`skills/context-engine/decision-matrix-rerun.md`)
- **Update-Back Rule** — versioning protocol (v2.1, v2.2 etc.) for in-life corrections after Part 7+ (`skills/context-engine/update-back-rule.md`)
- **Living Project Instruction File** — single source of truth per engagement that all skills read first (`skills/context-engine/living-instruction-file-spec.md`)

#### New Strategic Framework References (15 docs)

- **Five Digital Markets** — Search / Profile / Contextual / Marketplace / Utility taxonomy (`skills/context-engine/five-digital-markets.md`)
- **Channel Families** — 7 families covering 17 channels for Part 9 (`skills/context-engine/channel-families.md`)
- **In-Market vs Out-Market** — 3-5% vs 95-97% audience split, budget allocation logic (`skills/context-engine/in-market-out-market.md`)
- **Multi-Dimensional Decision Framework** — weight + score + weighted total for any consequential decision (`skills/context-engine/decision-framework.md`)
- **Unit Economics Framework** — CAC / LTV / LTV:CAC ≥ 3.0 / payback period; foundation for all recommendations (`skills/context-engine/unit-economics-framework.md`)
- **Actionable Persona Format** — 6-question format replacing biographical narratives (`skills/context-engine/actionable-persona-format.md`)
- **B2B Decision-Making Unit** — User / Influencer / Decision-maker / Gatekeeper roles with role-specific messaging (`skills/context-engine/b2b-decision-making-unit.md`)
- **Three-Scenario Forecasting** — Conservative / Moderate / Aggressive for every projection (`skills/context-engine/three-scenario-forecasting.md`)
- **30 / 60 / 90-Day Framework** — Foundation / Validation / Optimisation phasing (`skills/context-engine/30-60-90-framework.md`)
- **Reporting Cadence** — daily / weekly / monthly / quarterly / annual scopes and audiences (`skills/context-engine/reporting-cadence.md`)
- **Fixed vs Variable Budget** — Fixed monthly + Variable reserve mechanism with monthly recommendation conversation (`skills/context-engine/fixed-vs-variable-budget.md`)
- **Competitor 3-Question Output** — what they do well / poorly / are NOT doing — enforced output for every competitor analysis (`skills/context-engine/competitor-3-question-output.md`)
- **India Market Context** — regional context module (DPDP Act, mobile-first, festive seasonality, WhatsApp, vernacular content, INR pricing benchmarks, tier-1/2/3 differentiation) (`skills/context-engine/india-market-context.md`)
- **Growth Plan Template** — canonical 11-section structure for the Part 8 flagship deliverable (`skills/context-engine/growth-plan-template.md`)
- **Yearly Planner Template** — canonical structure for the 12-month operational companion (`skills/context-engine/yearly-planner-template.md`)
- **Monthly Report Template** — 9-section structure with writing principles enforcing insight over data (`skills/context-engine/monthly-report-template.md`)

#### New Engagement Skills (6)

- `engagement-workflow` — the 12-Part orchestrator that owns engagement lifecycle
- `four-core-documents` — produces all 4 Part 3 documents (61 steps); supports `--view v2` for re-runs
- `client-validation-document` — produces the Part 5 deliverable (the "one true stop")
- `growth-plan` — produces the Part 8 flagship 11-section client deliverable
- `yearly-planner` — produces the Part 8 operational 12-month companion
- `continuous-improvement-loop` — Part 12 quarterly briefs and ad-hoc briefs aggregating market + operating signals into product/offering recommendations

#### New Command

- `/digital-marketing-pro:engagement` — entry point with subcommands: `start`, `status`, `next`, `validate`, `re-run-decision`, `update-back`, `lif-show`, `file-tree`, `list-engagements`, `four-core`, `growth-plan`, `yearly-planner`, `loop`

#### New Persistence Script

- `scripts/engagement-state.py` — manages the engagement state, directory tree, Stone/Opinion intake, Decision Matrix evaluation, Update-Back versioning, Living Project Instruction File. 14 subcommands with JSON I/O for skill consumption. Atomic writes; no hand-editing of `_engagement.json` required.

#### New Engagement Directory Structure

Every engagement now lives at:
```
~/.claude-marketing/brands/{brand-slug}/engagements/{engagement-id}/
```
With a canonical 12-part directory tree, v1/v2 split for Parts 3 and 4, persistent reports directory, and the Living Project Instruction File.

#### Plugin Manifest Modernised to 2026 Spec

`.claude-plugin/plugin.json` updated with:
- `$schema` reference for JSON schema validation
- `homepage` and `repository` URLs
- `license` field
- Expanded `keywords` array for marketplace discovery
- Author URL added

### Compatibility

- **All existing v2.7.0 skills, agents, scripts, hooks remain functional and unchanged.** v3.0 is purely additive at the methodology layer.
- The 12-Part workflow uses existing skills as Part-specific producers (e.g., Part 4 uses existing `competitor-analysis`, `audience-intelligence`, `market-intelligence`).
- Engagements are an opt-in workflow. Single-skill invocations (e.g., `/digital-marketing-pro:content-engine` for a one-off blog post) continue to work without an engagement context.

### Migration

No migration needed. Existing brand profiles at `~/.claude-marketing/brands/{slug}/profile.json` continue to work. Engagements are new directories that sit alongside the existing brand state.

To start using the new methodology:
```
/digital-marketing-pro:engagement start <your-brand-slug> <your-engagement-id>
```

---

## [2.7.0] — 2026-03-31

### Changed — Skill Budget, Agent Safety, Execution Safety

Structural quality release addressing plugin best practice audit. No feature changes — all existing functionality preserved.

#### Skill Description Optimization (141 skills)

- All 141 descriptions trimmed to <130 characters (from 130-400+) to fit within the ~15,500 char skill discovery budget
- Preserves trigger intent: "[Verb] [domain]. Use when: [triggers]." pattern
- Previously 140/141 skills exceeded convention — Claude may not have discovered all skills

#### Agent Safety (25 agents)

- `maxTurns` added to all 25 agents — prevents runaway execution
- 10 turns (5 agents), 15 turns (15 agents), 20 turns (5 agents)

#### Execution Safety

- `disable-model-invocation: true` added to `launch-plan` (total: 18 protected skills)

#### Hook Stability

- SessionStart: `timeout 30` wrapper on setup.py prevents session hang

---

## [2.6.0] — 2026-03-30

### Added — SEO Capability Expansion

Closes the gap with dedicated SEO tools by adding 6 new SEO sub-skills, expanded schema markup support, reference documentation, and a new MCP integration. Inspired by capabilities identified in [claude-seo](https://github.com/AgriciDaniel/claude-seo) — adapted to work within the full marketing system architecture with brand context, execution layer, multi-client support, and quality evaluation.

#### New Skills (6)

- **`/digital-marketing-pro:programmatic-seo`** — Programmatic SEO at scale: data source assessment, template engine planning, URL pattern strategy, internal linking automation, thin content safeguards with quality gates (WARNING at 100 pages, HARD STOP at 500), index bloat prevention, and Google's Scaled Content Abuse policy enforcement (June 2025 / August 2025 escalation context)
- **`/digital-marketing-pro:competitor-pages`** — SEO-optimized competitor comparison page generator: "X vs Y" pages, "alternatives to X" pages, "best tools" roundup pages, feature matrix tables. Includes Product/SoftwareApplication/ItemList schema markup, conversion-optimized CTA layouts, keyword targeting formulas, fairness guidelines, and social proof integration
- **`/digital-marketing-pro:image-seo-audit`** — Dedicated image optimization audit: alt text quality, tiered file size thresholds (thumbnail/content/hero), format analysis (WebP/AVIF/JPEG XL status), responsive images (`srcset`/`sizes`), lazy loading validation (flags `loading="lazy"` on LCP images), `fetchpriority="high"` checks, `decoding="async"`, CLS prevention via dimensions, file naming, CDN usage
- **`/digital-marketing-pro:page-seo-analysis`** — Deep single-page SEO analysis: all ranking dimensions for one URL (title, meta, headings, content depth, E-E-A-T, schema detection with deprecation tracking, images, internal links, technical signals, AI search readiness). More granular than site-wide `/digital-marketing-pro:seo-audit`. Use for landing page optimization, content refresh prioritization, or pre-publish quality checks
- **`/digital-marketing-pro:sitemap-manager`** — XML sitemap analysis and generation: parse existing sitemaps for issues (stale lastmod, 404s, noindex conflicts, missing URLs, protocol limit violations), or generate new sitemaps with industry-specific templates (SaaS, ecommerce, local, publisher, agency). Includes sitemap index strategy, robots.txt registration, and compression recommendations
- **`/digital-marketing-pro:seo-plan`** — Comprehensive SEO strategy planning with industry-specific templates: discovery, competitive analysis, architecture design, content strategy, technical foundation, and 4-phase implementation roadmap (Foundation → Expansion → Scale → Authority). Templates for SaaS, ecommerce, local service, publisher/media, and agency business models

#### New Reference Files (2)

- **`schema-templates.json`** — Ready-to-use JSON-LD template library with 12 schema types: VideoObject, BroadcastEvent (LIVE badge), Clip (key moments), SeekToAction (video seek), SoftwareSourceCode, ProductGroup (e-commerce variants), ProfilePage (E-E-A-T), Certification (replaced EnergyConsumptionDetails), OfferShippingDetails, MerchantReturnPolicy, SoftwareApplication, ItemList. Includes deprecation tracker for HowTo (Sept 2023), FAQ (Aug 2023), SpecialAnnouncement (July 2025), EnergyConsumptionDetails (April 2025)
- **`google-seo-reference.md`** — Concise Google SEO quick reference for agents: Search Essentials, E-E-A-T framework (with December 2025 update extending to all competitive queries), Core Web Vitals (INP current, FID removed), schema markup status table, image SEO best practices, AI search optimization signals, spam policies including Scaled Content Abuse and Site Reputation Abuse

#### Updated — schema-generator.py

- **9 new schema types** added: BroadcastEvent, Clip, SeekToAction, SoftwareSourceCode, SoftwareApplication, ProductGroup, ProfilePage, Certification, ItemList, plus dedicated builder functions for each
- **Deprecation warnings** — Automatic warnings when generating HowTo or FAQPage schemas, citing deprecation dates and recommending alternatives
- Total supported types: 18 (was 9)

#### Updated — seo-specialist Agent

- References new skills (programmatic-seo, competitor-pages, image-seo-audit, page-seo-analysis, sitemap-manager, seo-plan) with invocation guidance
- References new reference files (google-seo-reference.md, schema-templates.json)

#### New MCP Integration

- **DataForSEO** — Live SERP data, keyword research, backlink profiles, on-page analysis, content analysis, competitor domain analysis, AI visibility checking, LLM mention tracking. 9 API modules. Added to `.mcp.json.example` with `DATAFORSEO_USERNAME` and `DATAFORSEO_PASSWORD` environment variables

### Summary

| Metric | Before (v2.5.1) | After (v2.6.0) |
|--------|-----------------|-----------------|
| Skills | 135 | 141 |
| Schema types in generator | 9 | 18 |
| SEO-specific commands | ~14 | ~20 |
| MCP integrations | 67 | 68 |
| Reference files | 146 | 148 |

---

## [2.5.1] — 2026-03-05

### Added — Skill Platform Enhancements

- **`argument-hint`** added to all 55 user-invocable skills — provides autocomplete hints in the Skills UI (e.g., `[URL]`, `[brand-name --full]`, `[competitor1, competitor2, ...]`)
- **`disable-model-invocation: true`** added to 17 execution skills — prevents Claude from auto-triggering skills that write to external platforms (publish, send, launch, import, export). Users must explicitly invoke these via `/digital-marketing-pro:skill-name`
- **`evals/evals.json`** added to 3 key skills (campaign-plan, seo-audit, content-engine) — structured test cases with prompts, expected outputs, and quantitative/qualitative assertions for quality benchmarking
- **Fixed** `/digital-marketing-pro:help` skill — added missing `name: help` field in frontmatter (required by Agent Skills spec for skill registration)

### How it works

**Argument hints** appear as placeholder text when a user types `/digital-marketing-pro:` in the Skills UI, showing what arguments each skill accepts. For example, `/digital-marketing-pro:seo-audit` shows `[URL]` and `/digital-marketing-pro:campaign-plan` shows `[product/service description --budget=N]`.

**Execution safety** ensures that skills which write to external platforms (like `/digital-marketing-pro:publish-blog`, `/digital-marketing-pro:send-email-campaign`, `/digital-marketing-pro:launch-ad-campaign`) cannot be triggered by Claude autonomously — the user must explicitly type the slash command. This is a critical safety layer on top of the existing MCP write approval hook.

**Evals** provide reproducible test cases for key skills. Each eval includes a realistic prompt, expected output description, and assertions that can be verified programmatically. Located at `skills/{skill-name}/evals/evals.json`.

---

## [2.5.0] — 2026-02-26

### Added — Commands & Version Consistency

- **7 command files** in `commands/` directory — visible in the Customize panel "Commands" section:
  - `brand-setup` — Set up a new brand profile with voice, audience, competitors, and compliance rules
  - `campaign-plan` — Generate a multi-channel campaign plan with objectives, audience, budget, and KPIs
  - `seo-audit` — Run a comprehensive SEO audit covering technical, on-page, content, E-E-A-T, and link profile
  - `content-engine` — Draft blog posts, ad copy, emails, social, landing pages, and video scripts
  - `performance-report` — Generate marketing performance reports with KPI tracking and anomaly detection
  - `competitor-analysis` — Multi-dimensional competitive analysis across content, SEO, ads, social, and AI visibility
  - `email-sequence` — Design complete email sequences with subject lines, timing, and deliverability guidance
- **New `/digital-marketing-pro:help` skill** — Quick reference with all commands, examples, and troubleshooting

### Fixed

- Updated stale version references across docs (getting-started.md, architecture.md, integrations-guide.md) from v2.2.0/v2.4.0 to v2.5.0

---

## [2.4.0] — 2026-02-25

### Added — Connector Discovery & Onboarding

- **New `/digital-marketing-pro:integrations` skill** — Status dashboard showing all connected vs available MCP connectors, grouped by category (CRM, SEO, advertising, email, social, etc.), with which skills each connector unlocks and quick-win recommendations
- **New `/digital-marketing-pro:connect` skill** — Guided setup for connecting specific services (e.g., `/digital-marketing-pro:connect google-ads`). Provides platform-specific credential instructions, `.mcp.json` configuration, and post-setup verification. Handles HTTP (OAuth) vs npx (API key) connectors differently
- **New `connector-status.py` script** — Backend for connector discovery. Maintains a registry of 45+ connectors across 17 categories, checks `.mcp.json` and environment variables to report connection status, and generates setup guides
- **Updated `CONNECTORS.md`** — Added "Managing connectors" section linking to `/digital-marketing-pro:integrations`, `/digital-marketing-pro:connect`, `/digital-marketing-pro:add-integration`, and `/digital-marketing-pro:credential-switch` skills

### How it works

Users can now discover and manage integrations interactively:
- `/digital-marketing-pro:integrations` — "What's connected? What can I add?"
- `/digital-marketing-pro:connect salesforce` — "Walk me through connecting Salesforce"
- `/digital-marketing-pro:add-integration` — "I have a custom MCP server to add"

All 14 HTTP connectors auto-load on install (Slack, Canva, Figma, HubSpot, etc.) and authenticate via OAuth on first use. The 45+ npx connectors are discoverable through these skills and require API keys.

Skills that depend on connectors already handle missing connections gracefully — they check for connectivity at startup and guide users to setup if not connected.

## [2.3.1] — 2026-02-25

### Fixed

- Added missing YAML frontmatter to `localization-specialist.md` and `quality-assurance.md` agents — without frontmatter, these agents failed to register during plugin installation, potentially causing installation rollback

## [2.3.0] — 2026-02-25

### Changed — HTTP Connector Architecture

This release rebuilds the MCP integration layer to follow Anthropic's official plugin pattern — HTTP-only connectors that work in both Cowork and Claude Code.

- **New `.mcp.json` with 14 HTTP connectors**: Slack, Canva, Figma, HubSpot, Amplitude, Notion, Ahrefs, Similarweb, Klaviyo, Google Calendar, Gmail, Stripe, Asana, Webflow — all `"type": "http"`, all work through Cowork's VM NAT
- **New `CONNECTORS.md`** documenting 12 connector categories with `~~category` placeholder pattern (matching Anthropic's official convention)
- **`.mcp.json.example` preserved** for Claude Code users who want the full 67-server npx configuration
- **Minimal `plugin.json`** — stripped to 4 fields (name, version, description, author) matching Anthropic's official plugin format. Removed non-standard fields: `author.title`, `author.organization`, `author.email`, `author.work_email`, `homepage`, `repository`, `license`, `keywords`
- **Script path resolution** — `setup.py` now outputs the plugin root and scripts directory path at session start, so Claude can resolve relative script paths in both Cowork and Claude Code

### Environment Compatibility

| Feature | Cowork | Claude Code |
|---------|--------|-------------|
| 115 skills, 25 agents | Full | Full |
| HTTP connectors (14) | Full | Full |
| npx/stdio servers (67) | Not available | Full (via .mcp.json.example) |
| Python scripts (64) | Works (Python 3.10 in VM) | Full |
| Persistent brand data | Per-session | Persistent |

## [2.2.1] — 2026-02-24

### Fixed — CLI Contract & Script Bugs
- **CRITICAL: Removed undefined `${CLAUDE_PLUGIN_ROOT}` env var** from all 22+ SKILL.md files, 23 agent files, hooks.json, and 2 documentation files — replaced with relative `scripts/` paths that work across all environments
- **Fixed CLI argument mismatches in 8 SKILL.md files** where script invocation commands did not match actual argparse definitions:
  - eval-content: `--content`/`--type` → `--text`/`--content-type`, `--composite`/`--dimensions` → `--data '{json}'`
  - verify-claims: removed non-existent `--brand` flag, `--content` → `--text`
  - validate-output: removed non-existent `--brand` flag, `--content` → `--text`, `--action detect-schema` → `--action list-schemas`
  - translate-content: `--content` → `--text`, `--source-lang`/`--target-lang` → `--source`/`--target`/`--original`/`--translated`, removed non-existent `--language`
  - localize-campaign: `--content` → `--text`, removed non-existent `--language`
  - eval-suite: `--content` → `--text`, quality-tracker `--action log --content-label --scores --suite-id` → `--action log-eval --data '{json}'`
  - prompt-test: `--content` → `--text`
  - quality-report: `--type` → `--content-type`
- **Fixed content-scorer.py keyword density bug**: multi-word keywords used substring matching (`str.count()`) instead of word-boundary matching — "AI tools" would match inside "AI toolset". Now uses `re.findall()` with `\b` word boundaries
- **Fixed hallucination-detector.py sentence splitting bug**: `re.split(r'(?<=[.!?])\s+', ...)` split on abbreviation periods (Dr., Inc., U.S.) — now requires uppercase letter after split point: `(?<=[.!?])\s+(?=[A-Z])`
- **Fixed hooks.json SessionStart**: replaced fragile compound shell command with nested subshells and `2>/dev/null` (Unix-only) with simple `python scripts/setup.py --check-deps --summary`
- **Fixed custom-mcp-guide.md**: stale "46 MCP servers" count updated to 67

### Fixed — ContentForge Plugin
- **Added YAML frontmatter** (`name` + `description`) to all 10 agent files for Claude Cowork routing compatibility
- **Replaced 5 invented MCP tool names** in Output Manager agent (`mcp_google-drive_list_folders`, `mcp_google-drive_create_folder`, `mcp_google-drive_upload_file`, `mcp_google-sheets_read_row`, `mcp_google-sheets_update_row`) with adaptive MCP approach that checks available tools at runtime

### Changed
- Updated CONTRIBUTING.md verification checklist to reference `scripts/` instead of `${CLAUDE_PLUGIN_ROOT}`
- Updated docs/architecture.md agent template to reference `scripts/` instead of `${CLAUDE_PLUGIN_ROOT}`

## [2.2.0] — 2026-02-13

### Added — Evaluation/QA Layer
- **8 new scripts**: hallucination-detector.py, claim-verifier.py, output-validator.py, eval-runner.py, quality-tracker.py, eval-config-manager.py, prompt-ab-tester.py, language-router.py
- **1 new agent**: quality-assurance — orchestrates multi-dimensional content evaluation
- **7 new eval commands**: eval-content, verify-claims, validate-output, quality-report, eval-config, prompt-test, eval-suite
- **2 new reference files**: eval-framework-guide.md, eval-rubrics.md
- Hallucination detection: pattern-based detection of fabricated statistics, fake URLs, unsubstantiated claims, made-up entities
- Claim verification: cross-check marketing claims against user-provided evidence data
- Output validation: 8 built-in schemas (blog_post, email, ad_copy, social_post, landing_page, press_release, content_brief, campaign_plan)
- Composite eval scoring: 6-dimension evaluation with A+ through F grading and configurable weights per brand
- Quality regression tracking: 30-day rolling baselines with automatic regression detection
- Prompt A/B testing: compare quality scores across content variations with significance detection
- Eval-before-publish gate: execution-coordinator runs eval-runner before creating approval records
- Hallucination scanning added to Write|Edit PreToolUse hook for real-time content checking

### Added — Multilingual Support
- **4 new MCP servers** (67 total): DeepL, Sarvam AI, Google Cloud Translation, Lara Translate
- **1 new agent**: localization-specialist — translation routing, transcreation, cultural adaptation
- **6 new multilingual commands**: translate-content, localize-campaign, language-audit, language-config, multilingual-score, hreflang-check
- **2 new reference files**: multilingual-execution-guide.md, transcreation-framework.md
- Automatic language detection via Unicode script analysis for 35+ languages
- Translation service routing: Indic → Sarvam AI, European → DeepL, CJK → DeepL, broad → Google Cloud
- Translation quality scoring: length ratio, formatting preservation, key term consistency, placeholder integrity
- Transcreation framework: cultural recreation for emotional content with brief templates and quality rubrics
- Cultural adaptation: Hofstede dimensions applied to marketing (social proof, urgency, trust signals per market)
- Multilingual SEO: hreflang auditing, international sitemaps, Baidu/Yandex/Naver optimization guidance
- RTL support for Arabic, Hebrew, Farsi, Urdu
- Indic language expertise: Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi via Sarvam AI
- Language configuration in brand profile: primary/secondary languages, do-not-translate terms, translation preferences, locale formatting

### Changed
- Updated content-creator agent with language awareness (creates in primary_language by default)
- Updated brand-guardian agent with hallucination detection capability
- Updated execution-coordinator agent with eval-before-execution gate
- Added multilingual scoring rubric to scoring-rubrics.md
- Added language fields to brand profile schema in setup.py
- Enhanced Write|Edit hook with hallucination scanning
- Updated plugin.json to v2.2.0 with eval and multilingual keywords

### Totals
- **~402 files** | 115 commands | 25 agents | 64 scripts | 67 MCP servers | 143 reference files

## [2.1.0] — 2026-02-13

### Added — Intelligence, Monitoring & Execution Gaps (~78 new files, ~11 modified)

**MCP Expansion (46 → 63 servers)**
- 7 new CRM MCPs: Odoo, Freshsales, Monday CRM, Microsoft Dynamics 365, Copper, Close, Keap
- 5 new PM/Design MCPs: Jira, Asana, ClickUp, Canva, Figma
- 3 new SEO/Monitoring MCPs: Moz, Google PageSpeed, Brandwatch
- 2 new Marketing Automation MCPs: Marketo, Pardot

**SEO Execution Layer (4 commands + 1 script + 1 ref)**
- Commands: seo-implement, rank-monitor, serp-tracker, redirect-manager
- Script: seo-executor.py — track and execute SEO changes via CMS MCPs
- Reference: seo-execution-guide.md

**Competitor Monitoring System (3 commands + 1 agent + 1 script + 1 ref)**
- Commands: competitor-monitor, share-of-voice, competitor-alerts
- Agent: competitor-intelligence — ongoing competitive scanning with change detection
- Script: competitor-tracker.py — baselines, diff, mentions, SOV, pricing, ads, win/loss
- Reference: competitive-monitoring-guide.md

**GEO Execution & Monitoring (3 commands + 1 script + 1 ref)**
- Commands: geo-monitor, entity-audit, narrative-tracker
- Script: geo-tracker.py — AI visibility auditing across ChatGPT, Perplexity, Gemini, Copilot
- Reference: geo-execution-guide.md

**Advanced Reporting (4 commands + 1 script + 1 ref)**
- Commands: pdf-report, live-dashboard, attribution-report, cohort-analysis
- Script: pdf-generator.py — report generation and scheduling
- Reference: advanced-reporting-guide.md

**Programmatic Gaps (2 ref)**
- native-advertising.md — Taboola, Outbrain, Nativo, TripleLift, Sharethrough
- audio-programmatic.md — Spotify, Pandora, podcast programmatic

**Inter-System Connectivity (2 commands + 1 ref)**
- Commands: data-import, add-integration
- Reference: custom-mcp-guide.md

**Predictive Intelligence (3 commands + 2 agents + 3 scripts + 2 ref)**
- Commands: simulate, what-if, churn-risk
- Agents: marketing-scientist, market-intelligence
- Scripts: revenue-simulator.py, churn-predictor.py, macro-signal-tracker.py
- References: marketing-science-guide.md, market-intelligence-guide.md

**Creative Intelligence (2 commands + 1 script + 1 ref)**
- Commands: creative-health, content-decay-scan
- Script: creative-fatigue-predictor.py
- Reference: creative-intelligence-guide.md

**Compound Intelligence (2 commands + 1 agent + 1 script + 1 ref)**
- Commands: learn, recall
- Agent: intelligence-curator — cross-agent learning hub with confidence scoring
- Script: intelligence-graph.py
- Reference: compound-intelligence-guide.md

**Journey & Growth (3 commands + 1 agent + 2 scripts + 1 ref)**
- Commands: journey-design, loop-detect, dark-funnel
- Agent: journey-orchestrator — cross-channel journey state machines
- Scripts: journey-engine.py, growth-loop-modeler.py
- Reference: journey-growth-guide.md

**Self-Healing Operations (1 command + 1 script + 1 ref)**
- Command: autopilot-status
- Script: campaign-health-monitor.py
- Reference: self-healing-ops-guide.md

**Competitive Narrative (2 commands + 1 script + 1 ref)**
- Commands: narrative-landscape, counter-narrative
- Script: narrative-mapper.py
- Reference: narrative-warfare-guide.md

**Synthetic Audience (2 commands + 1 script + 1 ref)**
- Commands: focus-group, message-test
- Script: audience-simulator.py
- Reference: synthetic-audience-guide.md

**Additional Commands (3)**
- market-weather, intelligence-report, pricing-test

### Changed
- Updated CRM integration guide with 7 new platform field mappings
- Updated plugin.json description and keywords
- Updated README with all new counts and capability sections
- Updated .gitignore with new data directories

## [2.0.0] - 2026-02-12

### Added — Execution Layer
- **26 new slash commands** bringing the total from 42 to 68 — adding a complete execution layer:
  - **Publishing (5)**: `/digital-marketing-pro:publish-blog`, `/digital-marketing-pro:send-email-campaign`, `/digital-marketing-pro:launch-ad-campaign`, `/digital-marketing-pro:schedule-social`, `/digital-marketing-pro:send-report`
  - **CRM & Data (5)**: `/digital-marketing-pro:crm-sync`, `/digital-marketing-pro:lead-import`, `/digital-marketing-pro:pipeline-update`, `/digital-marketing-pro:segment-audience`, `/digital-marketing-pro:data-export`
  - **Monitoring (4)**: `/digital-marketing-pro:performance-check`, `/digital-marketing-pro:campaign-status`, `/digital-marketing-pro:anomaly-scan`, `/digital-marketing-pro:budget-tracker`
  - **Memory & Knowledge (3)**: `/digital-marketing-pro:save-knowledge`, `/digital-marketing-pro:search-knowledge`, `/digital-marketing-pro:sync-memory`
  - **Communication (2)**: `/digital-marketing-pro:send-sms`, `/digital-marketing-pro:send-notification`
  - **Agency Operations (4)**: `/digital-marketing-pro:agency-dashboard`, `/digital-marketing-pro:client-report`, `/digital-marketing-pro:sop-library`, `/digital-marketing-pro:credential-switch`
  - **Brand Team (3)**: `/digital-marketing-pro:team-assign`, `/digital-marketing-pro:region-config`, `/digital-marketing-pro:exec-summary`
- **5 new specialist agents** bringing the total from 13 to 18:
  - `execution-coordinator` — bridges planning and execution with approval workflow
  - `performance-monitor-agent` — live data monitoring, anomaly detection, campaign health
  - `crm-manager` — cross-CRM operations (Salesforce/HubSpot/Zoho/Pipedrive)
  - `memory-manager` — persistent brand knowledge via RAG, knowledge graphs, cross-session memory
  - `agency-operations` — multi-client portfolio management, SOPs, credential profiles, team management
- **8 new Python scripts** bringing the total from 34 to 42:
  - `approval-manager.py` — approval lifecycle (draft → pending → approved → executed)
  - `execution-tracker.py` — audit trail for all platform executions
  - `performance-monitor.py` — metrics aggregation, anomaly detection, baseline management
  - `memory-manager.py` — vector DB/RAG interface, knowledge graph prep, sync orchestration
  - `crm-sync.py` — CRM data preparation, field mapping, deduplication
  - `report-generator.py` — formatted reports for Slack, email, Google Sheets
  - `credential-manager.py` — per-brand credential profiles for agency multi-client management
  - `team-manager.py` — team roles, permissions, approval chains, capacity management
- **7 new reference knowledge files** bringing the total from 117 to 124:
  - `execution-workflows.md` — standard operating procedures for every execution type
  - `approval-framework.md` — risk classification, approval rules, rollback procedures
  - `platform-publishing-specs.md` — platform API requirements and content format specs
  - `memory-architecture.md` — 5-layer persistent memory system design
  - `crm-integration-guide.md` — CRM connection patterns, field mapping, deduplication
  - `agency-operations-guide.md` — multi-client management, portfolio scoring, SOPs, credential isolation
  - `team-roles-framework.md` — role definitions, permission matrix, approval chains, capacity planning
- **28 new MCP server integrations** bringing the total from 18 to 46: Twitter/X, Instagram, LinkedIn Publishing, TikTok Content, YouTube, Pinterest, SendGrid, Klaviyo, Customer.io, Brevo, Mailgun, Zoho CRM, Pipedrive, Mixpanel, Amplitude, BigQuery, Pinecone, Qdrant, Supermemory, Graphiti, Notion, Google Drive, Webflow, Twilio, Intercom, Linear, Optimizely, Supabase
- **Execution safety hook**: New PreToolUse hook with `mcp_.*` matcher that intercepts all MCP write operations — verifies user approval, compliance, budget limits, and consent before allowing any external platform action
- **Human-in-the-loop approval workflow**: Every execution action classified by risk level (low/medium/high/critical) with industry-specific compliance gates and rollback procedures
- **5-layer memory architecture**: Session context → Vector DB RAG (Pinecone/Qdrant) → Temporal knowledge graphs (Graphiti) → Universal agent memory (Supermemory) → Knowledge base (Notion/Google Drive)
- **Agency multi-client operations**: Per-client credential profiles, portfolio health dashboards, SOP library with compliance tracking, team role management with capacity planning
- **Brand team management**: Team roles and permissions, cross-team workflows, regional/market configuration, executive reporting

### Changed
- `plugin.json` updated to v2.0.0 with execution layer description and updated counts
- `.mcp.json` expanded from 18 to 46 server configurations
- `hooks/hooks.json` extended with MCP write safety interceptor
- All documentation updated with v2.0.0 counts and new sections

## [1.9.0] - 2026-02-12

### Added
- **8 new slash commands** bringing the total from 34 to 42 — closing the agency operations gap:
  - `/digital-marketing-pro:client-onboarding` (`skills/client-onboarding/SKILL.md`) — post-sale onboarding workflow with kickoff meeting agenda, discovery questionnaire, stakeholder mapping, access checklist, 30-60-90 day expectations setting
  - `/digital-marketing-pro:qbr-plan` (`skills/qbr-plan/SKILL.md`) — Quarterly Business Review preparation with performance retrospective, strategic recommendations, upsell opportunities, next quarter roadmap
  - `/digital-marketing-pro:media-plan` (`skills/media-plan/SKILL.md`) — holistic paid media planning across channels with flight dates, budget waves, creative rotation, channel allocation, contingency reserves
  - `/digital-marketing-pro:video-script` (`skills/video-script/SKILL.md`) — video marketing script writing for YouTube, TikTok, Instagram Reels, LinkedIn with hook variants, timestamps, visual direction, accessibility
  - `/digital-marketing-pro:executive-dashboard` (`skills/executive-dashboard/SKILL.md`) — C-suite dashboard design with business-outcome north-star metrics, visualization recommendations, alert thresholds, narrative guidance
  - `/digital-marketing-pro:case-study-plan` (`skills/case-study-plan/SKILL.md`) — structured case study creation workflow with CSR framework, interview questions, format variations (PDF/web/slide/video), distribution strategy
  - `/digital-marketing-pro:attribution-model` (`skills/attribution-model/SKILL.md`) — multi-touch attribution setup with model selection (last-touch/first-touch/linear/time-decay/position-based/data-driven/MMM), credit distribution rules, platform implementation guides
  - `/digital-marketing-pro:creative-testing-framework` (`skills/creative-testing-framework/SKILL.md`) — systematic creative testing strategy with testing matrix, holdout controls, sample size per variant, significance thresholds, iteration cadence
- **2 new reference knowledge files** bringing the total from 115 to 117:
  - `skills/paid-advertising/media-planning.md` — media planning framework, channel allocation methodology, flighting strategies (continuous/pulsing/fighting), budget waves, creative rotation cadence, cross-channel synergy
  - `skills/content-engine/video-scripting.md` — platform-specific video formats (YouTube/TikTok/Reels/Shorts/LinkedIn), script structures (AIDA/PAS), 12 hook formulas, timestamp annotation, visual direction, accessibility, CTA placement

### Fixed
- `scripts/setup.py` `create_brand()` function now initializes `insights.json` file when creating new brands — previously this file was referenced by all 13 agents and context-engine but not auto-created, causing errors on first insight save

### Removed
- `.mcp_new.json` — empty orphan file from development
- `mcp_config.json` — legacy 12-server MCP config (replaced by `.mcp.json` in v1.8.0)

### Changed
- `.claude-plugin/plugin.json` version bumped from 1.8.0 to 1.9.0, command count 34 → 42, reference files 115 → 117
- `README.md` updated: version badge 1.8.0 → 1.9.0, command count 34 → 42, reference files 115 → 117, 8 new command rows in commands table, architecture tree updated
- `docs/getting-started.md` version 1.8.0 → 1.9.0, command count and reference file counts updated
- `docs/architecture.md` version 1.8.0 → 1.9.0, file tree updated, file count 233 → 243, command list updated with 8 new entries

## [1.8.0] - 2026-02-12

### Added
- **Marketing Automation module** (`skills/marketing-automation/`) — new dedicated module covering automation workflow design, lead scoring models, nurture sequences, marketing operations, and MAP platform strategy
  - `skills/marketing-automation/SKILL.md` — module definition with workflow design, lead scoring, nurture sequences, and marketing ops capabilities
  - `skills/marketing-automation/automation-workflows.md` — trigger types, 10+ workflow patterns (welcome, abandoned cart, re-engagement, onboarding, win-back), branching logic, cross-channel orchestration
  - `skills/marketing-automation/lead-scoring.md` — explicit and implicit scoring, negative scoring, score thresholds (cold/warm/MQL/SQL), progressive profiling, decay, sales handoff rules
  - `skills/marketing-automation/nurture-sequences.md` — lifecycle stages, 7 sequence types with cadence and content mapping, multi-channel nurture, timing science, template sequences
  - `skills/marketing-automation/marketing-ops.md` — data hygiene, tech stack management, deliverability (SPF/DKIM/DMARC), compliance automation, MAP comparison matrix (HubSpot/ActiveCampaign/Klaviyo/Mailchimp/Marketo/Pardot)
- **15 new reference knowledge files** across 10 existing modules, bringing reference files from 96 to 115:
  - `skills/paid-advertising/microsoft-ads.md` — Bing Ads, Microsoft Audience Network, LinkedIn profile targeting, Import from Google Ads
  - `skills/paid-advertising/retargeting-audiences.md` — audience segments, platform-specific retargeting, sequential messaging, frequency capping, privacy impact
  - `skills/analytics-insights/dashboard-design.md` — dashboard hierarchy (executive/operational/campaign), visualization best practices, alert thresholds, tool recommendations
  - `skills/analytics-insights/clv-analysis.md` — CLV models (historical/predictive/contractual), CLV:CAC ratio, cohort analysis, industry benchmarks
  - `skills/content-engine/personalization.md` — personalization levels, data requirements, email/website/ad personalization, testing personalization, privacy
  - `skills/content-engine/case-studies.md` — CSR framework, interview questions, data presentation, format variations, distribution strategy, industry templates
  - `skills/campaign-orchestrator/sales-enablement.md` — battle cards, sales content mapping to stages, objection handling, proposal templates, content metrics
  - `skills/growth-engineering/experimentation-frameworks.md` — ICE/RICE/PIE scoring, hypothesis format, experiment types, growth experiment categories, velocity
  - `skills/digital-pr/link-building-tactics.md` — 13 link building methods ranked, outreach templates, anchor text strategy, red flags, competitive gap analysis
  - `skills/cro/personalization-testing.md` — segment-based testing, behavioral targeting, dynamic content, holdout testing, testing roadmap
  - `skills/audience-intelligence/customer-research-methods.md` — quantitative and qualitative methods, survey design, JTBD research, win/loss analysis, VoC programs
  - `skills/funnel-architect/sales-marketing-alignment.md` — shared funnel definitions, SLAs, lead handoff, feedback loops, RevOps, shared metrics
  - `skills/reputation-management/review-management-platforms.md` — review platforms by industry, generation strategies, response framework by rating, monitoring tools, legal considerations
  - `skills/emerging-channels/ai-marketing-tools.md` — AI for content/SEO/ads/email/social/analytics/CRO, prompt engineering for marketers, AI governance, cost-benefit
  - `skills/influencer-creator/micro-influencer-strategy.md` — influencer tiers, micro/nano advantages, discovery, vetting, compensation models, gifting programs, scaling
- **6 new MCP integrations** bringing the total from 12 to 18:
  - `tiktok-ads` — TikTok Ads campaign performance, creative insights, audience analytics, Spark Ads data
  - `shopify` — Shopify eCommerce orders, products, customers, inventory, sales analytics
  - `wordpress` — WordPress content publishing, post management, SEO metadata
  - `salesforce` — Salesforce CRM pipeline, opportunity data, lead management, account insights
  - `google-looker-studio` — Google Looker Studio dashboard data, report embedding, cross-platform visualization
  - `activecampaign` — ActiveCampaign email automation, lead scoring, CRM contacts, automation workflows

### Changed
- `.claude-plugin/plugin.json` version bumped from 1.7.0 to 1.8.0, module count 15 → 16, reference files 96 → 115, MCP integrations 12 → 18
- `.mcp.json` expanded with 6 new server entries
- `README.md` updated: version badge 1.7.0 → 1.8.0, module count 15 → 16, new module row, MCP count 12 → 18, 6 new MCP rows, architecture tree updated
- `docs/getting-started.md` version 1.7.0 → 1.8.0, module count and reference file counts updated
- `docs/architecture.md` version 1.7.0 → 1.8.0, file tree updated, file count 213 → 233, module list updated, MCP server list updated

## [1.7.0] - 2026-02-12

### Added
- **10 new slash commands** bringing the total from 24 to 34:
  - `/digital-marketing-pro:keyword-research` (`skills/keyword-research/SKILL.md`) — guided keyword research with clustering, intent mapping, and content gap analysis
  - `/digital-marketing-pro:roi-calculator` (`skills/roi-calculator/SKILL.md`) — campaign ROI calculation with 5 attribution models and budget efficiency ranking
  - `/digital-marketing-pro:ab-test-plan` (`skills/ab-test-plan/SKILL.md`) — A/B test planning with hypothesis framework, sample size calculation, and test duration estimation
  - `/digital-marketing-pro:content-repurpose` (`skills/content-repurpose/SKILL.md`) — content repurposing strategy with derivative format matrix, effort estimates, and publishing calendar
  - `/digital-marketing-pro:retargeting-strategy` (`skills/retargeting-strategy/SKILL.md`) — retargeting campaign architecture with audience segmentation, frequency capping, and creative sequencing
  - `/digital-marketing-pro:martech-audit` (`skills/martech-audit/SKILL.md`) — marketing technology stack audit across 11 functions with overlap detection and gap analysis
  - `/digital-marketing-pro:budget-optimizer` (`skills/budget-optimizer/SKILL.md`) — data-driven budget reallocation with diminishing returns modeling and efficiency ranking
  - `/digital-marketing-pro:client-proposal` (`skills/client-proposal/SKILL.md`) — agency client proposal generation with situation analysis, strategy, scope, timeline, and pricing
  - `/digital-marketing-pro:review-response` (`skills/review-response/SKILL.md`) — brand-aligned review response drafting with tone templates, escalation detection, and multi-variant output
  - `/digital-marketing-pro:webinar-plan` (`skills/webinar-plan/SKILL.md`) — end-to-end webinar planning with promotion timeline, email sequences, and post-event nurture strategy
- **8 new Python scripts** (all zero-dependency, stdlib-only), bringing the total from 26 to 34:
  - `scripts/roi-calculator.py` — campaign ROI with 5 attribution models (last_touch, first_touch, linear, time_decay, position_based), LTV:CAC ratio, budget efficiency ranking
  - `scripts/budget-optimizer.py` — budget reallocation using diminishing returns model (square-root scaling), efficiency-proportional allocation, minimum spend thresholds
  - `scripts/clv-calculator.py` — customer lifetime value with 3 models (simple, contractual, cohort), LTV:CAC health assessment, segment-weighted analysis
  - `scripts/content-repurposer.py` — 9 source content types mapping to 4-8 derivative formats, auto-generated content calendar, ROI multiplier calculation
  - `scripts/review-response-drafter.py` — 5-tier rating response logic, 4 tone modifiers, escalation detection (health/safety, legal, profanity), 3 response variants per review
  - `scripts/ad-budget-pacer.py` — spend pacing with linear projection, trend analysis (7-day moving average, weekend patterns), per-channel pacing, severity classification
  - `scripts/link-profile-analyzer.py` — domain diversity, authority bucketing (5 DA ranges), follow/nofollow ratio, anchor text classification (6 categories), profile health score 0-100
  - `scripts/revenue-forecaster.py` — linear regression + growth rate models, blended forecast, seasonal multipliers, confidence ranges (±15% widening by 3% per month)

### Changed
- **5 agent files updated** with new script references in "Tools & Scripts" section:
  - `agents/analytics-analyst.md` — added roi-calculator.py, clv-calculator.py, budget-optimizer.py, revenue-forecaster.py, ad-budget-pacer.py
  - `agents/media-buyer.md` — added ad-budget-pacer.py, budget-optimizer.py
  - `agents/content-creator.md` — added content-repurposer.py, review-response-drafter.py
  - `agents/marketing-strategist.md` — added roi-calculator.py, budget-optimizer.py, revenue-forecaster.py
  - `agents/seo-specialist.md` — added link-profile-analyzer.py
- `.claude-plugin/plugin.json` version bumped from 1.6.0 to 1.7.0, command count 24 → 34, script count 26 → 34
- `README.md` updated: version badge 1.6.0 → 1.7.0, command count 24 → 34, script count 26 → 34, 10 new command rows in commands table, architecture tree updated
- `docs/getting-started.md` version 1.6.0 → 1.7.0, command count and script count updated
- `docs/architecture.md` version 1.6.0 → 1.7.0, file tree updated with new scripts, file count 195 → 213, command list updated, agent roster updated, dependency tier table updated

## [1.6.0] - 2026-02-12

### Added
- **Technical SEO module** (`skills/technical-seo/`) — new dedicated module covering Core Web Vitals optimization, crawlability audits, site architecture, indexation management, JavaScript SEO, mobile-first indexing, redirect auditing, structured data, and international technical SEO
  - `skills/technical-seo/SKILL.md` — module definition with 12-step audit process
  - `skills/technical-seo/core-web-vitals.md` — LCP, INP, CLS thresholds, causes, fixes, measurement tools, optimization priority framework
  - `skills/technical-seo/crawlability.md` — robots.txt, XML sitemaps, crawl budget, JavaScript rendering, log file analysis, orphan pages
  - `skills/technical-seo/site-architecture.md` — URL structure, internal linking, pagination, faceted navigation, breadcrumbs, site migration planning
  - `skills/technical-seo/indexation.md` — canonical tags, meta robots, index coverage, duplicate content, index bloat, new content indexation
  - `skills/technical-seo/international-seo.md` — hreflang implementation, ccTLD vs subdomain vs subdirectory, geotargeting, localization vs translation, search engine market share by country
- **Local SEO module** (`skills/local-seo/`) — new dedicated module covering Google Business Profile optimization, NAP consistency, citation management, local pack strategy, location pages, multi-location management, and local schema
  - `skills/local-seo/SKILL.md` — module definition with 10-step local SEO audit process
  - `skills/local-seo/gbp-optimization.md` — GBP completeness checklist, categories, attributes, photos, posts, Q&A, insights, suspension prevention
  - `skills/local-seo/citation-management.md` — NAP consistency, citation sources by industry, data aggregators, audit methodology, multi-location citations
  - `skills/local-seo/local-content.md` — local keyword research, location pages, city pages, "near me" optimization, voice search, seasonal content
  - `skills/local-seo/multi-location.md` — multi-location GBP management, store locators, franchise SEO, location opening/closing checklists, hierarchy
- **2 new slash commands**:
  - `/digital-marketing-pro:tech-seo-audit` (`skills/tech-seo-audit/SKILL.md`) — comprehensive technical SEO audit with Core Web Vitals scorecard, crawlability, indexation, site architecture, security, and prioritized fixes
  - `/digital-marketing-pro:local-seo-audit` (`skills/local-seo-audit/SKILL.md`) — local SEO audit with GBP scorecard, NAP consistency report, citation audit, review analysis, and 90-day action plan
- **2 new Python scripts** (both zero-dependency, stdlib-only):
  - `scripts/tech-seo-auditor.py` — URL-level technical SEO checks using `urllib.request`: HTTP status codes, redirect chain detection, meta tag parsing (title, description, canonical, viewport, robots), security headers (HTTPS, HSTS), TTFB measurement, compression detection, scoring (0-100)
  - `scripts/local-seo-checker.py` — NAP consistency analysis with address normalization (18 abbreviation expansions) and GBP profile completeness scoring across 16 weighted fields with industry-specific recommendations

### Changed
- `agents/seo-specialist.md` — added tech-seo-auditor.py and local-seo-checker.py to Tools & Scripts section; added 9 new reference files (5 technical-seo + 4 local-seo) to Reference Files section
- `.claude-plugin/plugin.json` version bumped from 1.5.0 to 1.6.0, module count 13 → 15, script count 24 → 26
- `README.md` updated: version badge 1.5.0 → 1.6.0, module count 13 → 15, command count 22 → 24, script count 24 → 26, reference file count 87 → 96, 2 new module rows in core modules table, 2 new command rows in commands table, architecture tree updated
- `docs/getting-started.md` version 1.5.0 → 1.6.0, module count and command count updated
- `docs/architecture.md` version 1.5.0 → 1.6.0, file tree updated with new modules/commands/scripts, file count 180 → 195, module list and command list updated, agent roster updated, dependency tier table updated

## [1.5.0] - 2026-02-12

### Added
- **9 new domain-specific Python scripts** (all zero-dependency, stdlib-only), bringing the total from 15 to 24 scripts:
  - **Email domain** (3 scripts for `email-specialist` agent):
    - `scripts/email-subject-tester.py` — Score email subject lines for open-rate effectiveness (length, spam triggers, personalization, power words, emoji usage)
    - `scripts/spam-score-checker.py` — Check email content for spam risk indicators (word density, punctuation, caps ratio, link density)
    - `scripts/send-time-optimizer.py` — Recommend optimal email send times by industry and audience type (built-in benchmark tables)
  - **CRO domain** (3 scripts for `cro-specialist` agent):
    - `scripts/sample-size-calculator.py` — Calculate A/B test sample size and estimated test duration (Z-test based, stdlib math)
    - `scripts/significance-tester.py` — Test A/B results for statistical significance (Z-test for proportions + chi-squared, p-value, confidence intervals)
    - `scripts/form-analyzer.py` — Analyze web forms for conversion optimization (field friction scoring, mobile-friendliness, progressive disclosure)
  - **Social media domain** (3 scripts for `social-media-manager` agent):
    - `scripts/hashtag-analyzer.py` — Analyze hashtags per platform (count, length, broad/niche mix, banned hashtag detection)
    - `scripts/posting-time-analyzer.py` — Recommend optimal posting times per platform and industry (built-in engagement data)
    - `scripts/calendar-validator.py` — Validate content calendar structure (frequency, variety, gap detection, weekend coverage)

### Changed
- **7 SKILL.md files updated** with new agent references:
  - 5 command skills gained new agents in "Agents Used" section: `email-sequence` (+email-specialist), `landing-page-audit` (+cro-specialist), `social-strategy` (+social-media-manager), `content-calendar` (+social-media-manager), `funnel-audit` (+cro-specialist)
  - 2 module skills gained new "Agents Used" section: `cro` (+cro-specialist), `emerging-channels` (+social-media-manager)
- **3 agent files updated** with new script references in "Tools & Scripts" section:
  - `agents/email-specialist.md` — Added email-subject-tester.py, spam-score-checker.py, send-time-optimizer.py
  - `agents/cro-specialist.md` — Added sample-size-calculator.py, significance-tester.py, form-analyzer.py
  - `agents/social-media-manager.md` — Added hashtag-analyzer.py, posting-time-analyzer.py, calendar-validator.py
- `.claude-plugin/plugin.json` version bumped from 1.4.0 to 1.5.0, script count 15 → 24
- `README.md` updated version badge and script counts
- `docs/getting-started.md` version 1.4.0 → 1.5.0
- `docs/architecture.md` version 1.4.0 → 1.5.0, file tree updated with 9 new scripts, script tables updated, file count 171 → 180

## [1.4.0] - 2026-02-11

### Added
- **3 new specialist agents** — Email Specialist, CRO Specialist, and Social Media Manager, bringing the total from 10 to 13 agents
  - `agents/email-specialist.md` — deliverability engineering, automation architecture, lifecycle sequences, A/B testing, list hygiene, CAN-SPAM/GDPR/CASL compliance
  - `agents/cro-specialist.md` — landing page optimization, A/B testing methodology, form optimization, pricing psychology, checkout optimization, statistical analysis
  - `agents/social-media-manager.md` — platform-native strategy (8 platforms), content calendars, algorithm optimization, community management, social commerce, UGC curation

### Changed
- **All 13 agents upgraded** from ~30-37 lines to ~100-120 lines each with 5 new functional sections:
  - **Tools & Scripts** — exact CLI commands for calling the plugin's 15 Python scripts with arguments and usage context
  - **MCP Integrations** — which of the 12 MCP servers each agent should query (all marked optional)
  - **Brand Data & Campaign Memory** — which persistent files to load from `~/.claude-marketing/brands/{slug}/`
  - **Reference Files** — which context-engine reference files to consult for each domain
  - **Cross-Agent Collaboration** — specific handoff recommendations between agents
- 8 agents gained **guideline enforcement behavior rules** (marketing-strategist, seo-specialist, media-buyer, analytics-analyst, competitive-intel, pr-outreach, growth-engineer, influencer-manager) — all 13 agents now enforce brand guidelines
- All 13 agents now reference `campaign-tracker.py` for campaign memory and `guidelines-manager.py` for brand guideline loading
- `brand-guardian.md` gained rule 11 (campaign memory pattern analysis) and expanded tool integration (6 scripts)
- `content-creator.md` gained rule 10 (campaign memory) and expanded tool integration (9 scripts)
- `.claude-plugin/plugin.json` version bumped from 1.3.0 to 1.4.0
- `README.md` updated agent count references (10 → 13), version badge
- `docs/getting-started.md` updated agent count references and version
- `docs/architecture.md` updated to v1.4.0 — agent roster expanded, agent definition structure updated with 5 new sections, file counts updated

## [1.3.0] - 2026-02-11

### Added
- **Brand Guidelines System** — persistent per-brand guidelines that go beyond numeric voice scores to capture detailed rules, restrictions, and styles
  - 5 built-in guideline categories: voice & tone, messaging, restrictions, channel styles, visual identity — plus custom guidelines
  - `_manifest.json` index with rule counts, metadata, and category tracking
  - Channel styles override base voice settings per platform (LinkedIn can be formal while Instagram is casual)
  - Automatic enforcement across all 13 modules, 22 commands, and content review
- **Deliverable Templates** — custom output formats for reports, proposals, briefs, and other deliverables
  - Per-brand template storage at `~/.claude-marketing/brands/{slug}/templates/`
  - Commands check for matching templates before using default formats
- **Agency SOPs** — workflow definitions that apply across all clients
  - Stored at `~/.claude-marketing/sops/` (agency-level, not per-brand)
  - Content approval workflows, campaign checklists, escalation procedures, QA processes
- **Guideline Violation Tracking** — `campaign-tracker.py` now tracks guideline violations with severity, category, and suggestions for pattern analysis
- `scripts/guidelines-manager.py` — new CLI script for guidelines, templates, and SOP CRUD operations (stdlib-only, no new dependencies)
- `skills/context-engine/guidelines-framework.md` — reference file for structuring and applying brand guidelines
- `/digital-marketing-pro:import-guidelines` command — interactive import of brand guidelines, restrictions, and channel styles
- `/digital-marketing-pro:import-sop` command — import agency SOPs and workflow definitions
- `/digital-marketing-pro:import-template` command — import deliverable templates for custom output formats
- `docs/brand-guidelines.md` — comprehensive guide for guidelines, templates, and SOPs with worked examples
- Brand Context point 9 in all 13 module SKILL.md files — automatic guideline checking and enforcement
- Guidelines summary line in SessionStart brand output (rule counts, restriction counts, template counts)

### Changed
- All 22 command SKILL.md files: step 1 extended to load guidelines, templates, and SOPs alongside brand profile
- `hooks/hooks.json` SessionStart: now also runs `guidelines-manager.py --action summary` for guideline context
- `hooks/hooks.json` PreToolUse: now checks `restrictions.md` for banned words and restricted claims in content
- `hooks/hooks.json` SessionEnd: now logs guideline violations via `campaign-tracker.py --action save-violation`
- `agents/brand-guardian.md`: added rules 9-10 for guideline restriction checking and SOP compliance verification
- `agents/content-creator.md`: added rule 9 for applying guidelines, messaging framework, and channel styles before writing
- `scripts/setup.py`: `init_memory_dirs()` now creates `sops/` directory; `create_brand()` now creates `guidelines/` and `templates/` subdirectories; `print_brand_summary()` now outputs guidelines summary line
- `scripts/campaign-tracker.py`: added `save-violation` and `get-violations` actions with severity/category filtering
- `docs/getting-started.md`: added section 5 "Importing Your Brand Guidelines" with walkthrough, updated section numbers, added guidelines to Next Steps
- `README.md`: added 3 new commands to Commands table, updated Key Differentiators, updated architecture tree, added Documentation table entry
- `.claude-plugin/plugin.json` version bumped from 1.2.1 to 1.3.0

## [1.2.1] - 2026-02-11

### Added
- Claude Cowork compatibility documentation — full Cowork section in `docs/claude-interfaces.md` with installation instructions, bonus capabilities (document creation, visual review, app integration), setup guide, and comparison with Anthropic's official marketing plugin
- Cowork installation option (Option C) in `README.md` and `docs/getting-started.md`
- Cowork badge in `README.md`
- Plugin Marketplace section in `docs/claude-interfaces.md`

### Changed
- `docs/claude-interfaces.md` rewritten — expanded from 234 to ~350 lines, added Cowork (full support) section, updated Feature Comparison table with 4 columns (Code, Cowork, Desktop, Web), added document creation and visual review rows
- `README.md` title updated: "Claude Code Plugin" → "Claude Code & Cowork Plugin"
- `README.md` "Which Claude Interface?" table updated with Cowork column
- `docs/getting-started.md` prerequisites and installation updated for Cowork, Next Steps links to Cowork guide
- `plugin.json` version bumped from 1.2.0 to 1.2.1

## [1.2.0] - 2026-02-11

### Added
- Rich brand context injection at session start — Claude receives full brand summary (voice, industry, compliance, goals, competitors) automatically
- `print_brand_summary()` function in `setup.py` with `--summary` CLI flag — outputs 15-line brand context
- `## Brand Context (Auto-Applied)` section in all 13 module SKILL.md files — references context-engine reference files
- Explicit brand loading path (`_active-brand.json` → `profile.json`) in all 17 command SKILL.md files
- SessionEnd hook auto-saves marketing insights via `campaign-tracker.py`
- "How It Works" section in README.md (session lifecycle, brand context flow, multi-client workflow)
- Comprehensive documentation suite (`docs/` folder with 10 guides)
- LICENSE file (MIT)
- CHANGELOG.md
- CONTRIBUTING.md

### Fixed
- `brand-voice-scorer.py` graceful fallback — returns structured JSON and `exit(0)` instead of crashing when NLTK is missing
- `content-scorer.py` graceful fallback — same pattern for missing NLTK and textstat dependencies
- SessionStart hook now uses `--summary` flag (was `--check-brand` which only output the brand name)

### Changed
- `hooks.json` SessionStart command: `--check-brand` replaced with `--summary` for rich context injection
- `hooks.json` SessionEnd prompt: simple reminder replaced with auto-save insights workflow
- `setup.py` no-args fallback: calls `print_brand_summary()` instead of `check_brand()`
- `plugin.json` version bumped from 1.1.0 to 1.2.0

## [1.1.0] - 2026-02-10

### Added
- `campaign-tracker.py` — persistent campaign memory with save/retrieve for campaigns, performance snapshots, and insights (200-entry rolling buffer)
- `adaptive-scorer.py` — brand-context-aware content scoring with industry, business model, and goal-based weight adjustments
- `intelligence-layer.md` — documentation of the adaptive learning system architecture
- `/digital-marketing-pro:switch-brand` command for multi-client brand switching
- Quick setup mode in `/digital-marketing-pro:brand-setup` (5 essential questions vs. 17 full questions)
- 12 MCP server integrations (GA4, Google Search Console, Google Ads, Meta, HubSpot, Mailchimp, LinkedIn, SEMrush, Ahrefs, Stripe, Google Sheets, Slack)
- Threads and Bluesky platform support in `social-post-formatter.py`
- Cross-platform SessionStart hook (works on Windows, macOS, Linux)

### Fixed
- Schema alignment: `brand-voice-scorer.py` `normalize_profile()` now correctly converts setup.py integer scale (1-10) to float scale (0.0-1.0)
- `requirements.txt` stripped from 16 packages (~600 MB) to 4 core packages (~15 MB)
- TikTok character limit updated to 4,000 characters
- PreToolUse hook SKIP logic improved — no longer interferes with non-marketing file edits

### Changed
- `plugin.json` version bumped from 1.0.0 to 1.1.0
- SessionEnd hook uses natural language prompt instead of rigid format
- `requirements.txt` reorganized into core and optional dependencies

## [1.0.0] - 2026-02-09

### Added
- Initial release
- 13 marketing modules: Content Engine, Campaign Orchestrator, Paid Advertising, Analytics & Insights, AEO/GEO Intelligence, Audience Intelligence, CRO, Digital PR, Funnel Architect, Growth Engineering, Influencer & Creator, Reputation Management, Emerging Channels
- 19 slash commands (`/digital-marketing-pro:campaign-plan`, `/digital-marketing-pro:ad-creative`, `/digital-marketing-pro:seo-audit`, etc.)
- 10 specialist agents (Marketing Strategist, Content Creator, SEO Specialist, Analytics Analyst, Brand Guardian, Media Buyer, Growth Engineer, Influencer Manager, Competitive Intel, PR Outreach)
- 14 Python execution scripts (setup, scoring, formatting, analysis, generation)
- Context engine with 5 reference files: industry profiles (22 industries), compliance rules (16 jurisdictions), platform specs (20+ platforms), scoring rubrics (7 frameworks), intelligence layer
- 86 reference knowledge files across all modules
- Brand profiling system with persistent storage at `~/.claude-marketing/`
- SessionStart, PreToolUse, and SessionEnd hooks
- `.mcp.json` configuration template for 12 marketing platforms
