# Changelog

All notable changes to the Digital Marketing Pro plugin are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). This project uses [Semantic Versioning](https://semver.org/).

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
- **`/digital-marketing-pro:page-analysis`** — Deep single-page SEO analysis: all ranking dimensions for one URL (title, meta, headings, content depth, E-E-A-T, schema detection with deprecation tracking, images, internal links, technical signals, AI search readiness). More granular than site-wide `/digital-marketing-pro:seo-audit`. Use for landing page optimization, content refresh prioritization, or pre-publish quality checks
- **`/digital-marketing-pro:sitemap`** — XML sitemap analysis and generation: parse existing sitemaps for issues (stale lastmod, 404s, noindex conflicts, missing URLs, protocol limit violations), or generate new sitemaps with industry-specific templates (SaaS, ecommerce, local, publisher, agency). Includes sitemap index strategy, robots.txt registration, and compression recommendations
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
