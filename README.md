# Digital Marketing Pro

**End-to-end engagement methodology for marketing teams running on Claude Code & Cowork.**

[![Version](https://img.shields.io/badge/version-3.4.2-blue.svg)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-optional-yellow.svg)](#python-dependencies-optional)
[![Cowork](https://img.shields.io/badge/cowork-compatible-purple.svg)](docs/claude-interfaces.md#claude-cowork-full-support)

DM Pro is the most ambitious marketing plugin in the Neelverse suite. It runs every brand engagement through a canonical **12-Part Strategy Flow** producing the **Four Core Documents** (61 explicit steps), the Two-Views Model (v1 unbiased + v2 client-validated), the Decision Matrix for selective re-runs, and the Living Project Instruction File. 25 specialist agents, 150 skills, 71 Python scripts, 14 HTTP MCP connectors, 16 industry profiles, 16 privacy-law jurisdictions. **v3.4** adds end-to-end-tested C2PA content provenance for EU AI Act Article 50 compliance, unified ads-platform MCPs (Synter Media AI / Ryze AI / Northbeam community), explicit parallel subagent dispatch (4–6× parallelism, ~50–80% wall-clock reduction), and an Anthropic Software Directory submission packet. Designed for digital marketing agencies, in-house teams running 50–200 brands, and consultancies who want consistent depth and auditable handoffs.

> **Current version:** 3.4.2 — see [Release notes](#release-notes) at the bottom of this README.

---

## Quick start

### 1. Install the plugin

```bash
# Add the marketplace (one time)
/plugin marketplace add indranilbanerjee/neels-plugins

# Install Digital Marketing Pro
/plugin install digital-marketing-pro@neels-plugins
```

Tested in Claude Code CLI, Claude Code Desktop, and Anthropic Cowork. Web chat (`claude.ai`) does not support `/plugin` commands.

### 2. Turn on auto-update (one-time, recommended)

**Third-party marketplaces — including this one — have auto-update OFF by default in Claude Code.** When v3.3.0 is the latest and you're still on v3.2.2, nothing tells you. There's no banner, no badge.

Open `/plugin`, go to the **Marketplaces** tab, find `neels-plugins`, and toggle **Enable auto-update**. Done — Claude Code will refresh and pull new DM Pro releases at startup from now on, prompting `/reload-plugins` to apply changes mid-session (no full restart needed; conversation context preserved).

To update manually instead, see the [Updating](#updating) section below.

### 3. Set up your first brand

```
/digital-marketing-pro:brand-setup
```

Interactive brand profiling — voice, audience, channels, industry, jurisdictions, competitors, goals. Choose **quick mode** (5 questions) or **full mode** (17 questions). Optional: import existing brand guidelines, SOPs, or templates with `/digital-marketing-pro:import-guidelines`.

### 4. Run your first engagement

```
/digital-marketing-pro:engagement
```

Walks the brand through the full **12-Part Strategy Flow**. Each part has a defined output (Stone-vs-Opinion intake → external research → Four Core Documents → competitive/customer/market analysis → Client Validation → selective v2 re-runs → preparation docs → Growth Plan + Yearly Planner → channel strategy fan-out → execution artefacts → AI creative instructions → continuous improvement loop). Produces ~50–60 canonical files per engagement.

Or jump straight to a specific workflow:
- `/digital-marketing-pro:campaign-plan` — multi-channel campaign with budget, timeline, KPIs
- `/digital-marketing-pro:seo-audit` — technical + content + E-E-A-T + AI visibility audit
- `/digital-marketing-pro:content-engine` — blog / ad / email / social / landing / video drafts
- `/digital-marketing-pro:competitor-analysis` — multi-dimensional deep-dive
- `/digital-marketing-pro:check` — pre-publish quality gate (hallucination + brand voice + structure + claims)
- `/digital-marketing-pro:status` — unified brand snapshot

### 5. Find your output

Everything lands in:

```
~/.claude-marketing/<brand-slug>/
├── brand-profile.json           ← brand voice, audience, guardrails, jurisdictions
├── engagements/
│   └── <engagement-slug>/
│       ├── 01-client-inputs/    ← Part 1 Stone-vs-Opinion intake
│       ├── 02-research/         ← Part 2 external market research
│       ├── 03-four-core/        ← Part 3 Four Core Documents (61 steps)
│       ├── 04-analysis/         ← Part 4 competitive / customer / market
│       ├── 05-validation/       ← Part 5 Client Validation Document (the one true stop)
│       ├── 06-v2-reruns/        ← Part 6 selective v2 re-runs per Decision Matrix
│       ├── 07-prep/             ← Part 7 internal operating layer
│       ├── 08-growth-plan/      ← Part 8 Growth Plan + Yearly Planner
│       ├── 09-channels/         ← Part 9 channel-strategy fan-out
│       ├── 10-execution/        ← Part 10 ad copy / post copy / headlines / CTAs
│       ├── 11-creative-briefs/  ← Part 11 AI creative instructions
│       ├── 12-improvement/      ← Part 12 continuous improvement loop
│       └── PROJECT_INSTRUCTIONS.md  ← Living Project Instruction File
└── insights/                    ← cross-engagement learnings
```

The [Multi-Brand & Agency Guide](docs/multi-brand-guide.md) covers the multi-client switching workflow.

---

## The 12-Part Engagement Methodology

Most marketing tools generate isolated outputs — a campaign brief here, an email there. There is no canonical sequence, no shared state, no enforced structure. Result: inconsistent depth, missed dependencies, outputs that don't compound.

DM Pro v3.0+ runs every brand engagement through the same 12 parts in sequence, producing the same files in the same order, with explicit dependency rules between them.

| Part | Name | Output |
|------|------|--------|
| 1 | Client Inputs | Stone vs Opinion intake (what client knows for certain vs what they believe) |
| 2 | External Research | Unbiased market research (no client docs used) |
| 3 | **Four Core Documents** | 61 explicit steps across Business & SBU Analysis (18), Segmentation Framework (15), Brand Positioning & Communications (19), DMFlow (9) |
| 4 | Competitive + Customer + Market | 4 unbiased analysis documents (4.1–4.4) |
| 5 | **Client Validation Document** | The one true stop. Client accepts/rejects/edits each finding |
| 6 | Selective v2 Re-runs | Subset of Part 3 + Part 4 docs re-run per the Decision Matrix |
| 7 | Preparation Documents | Internal operating layer (campaign architecture, KPI tree, content pillars, asset inventory, approval chains) |
| 8 | **Growth Plan + Yearly Planner** | The flagship 11-section client-facing strategy + 12-month operational calendar |
| 9 | Channel Strategy Fan-out | Up to 17 channel docs grouped into 7 families (Search & Campaign, Paid platforms, Organic & Influencer, Marketplace & CRM, Content/ATL/BTL/PR, Web + Measurement) |
| 10 | Execution Artefacts | Communication outputs (ad copy, post copy, headlines, CTAs) |
| 11 | AI Creative Instructions | Visual asset briefs |
| 12 | **Continuous Improvement Loop** | Quarterly briefs + ad-hoc briefs feeding market + operating signals back into product/offering decisions |

### Key architectural concepts

- **Two-Views Model** — After Part 5, every engagement carries both v1 (unbiased market view) and v2 (client-validated view). Operating decisions reference v2; ideation references both. v1 is never deleted.
- **Stone vs Opinion** — Every fact captured at intake is tagged with confidence. Stone = client knows for certain. Opinion = client believes (becomes a research question, not ground truth).
- **Decision Matrix** — Maps client validation responses to which v1 documents need v2 re-runs. Prevents over- and under-re-running.
- **Update-Back Rule** — When live operations surface corrections after Part 7, source documents get versioned (v2.1, v2.2 etc.) and the Living Project Instruction File propagates the change to all downstream skills.
- **Living Project Instruction File** — Single source of truth per engagement. All skills read it first. Auto-updated when source docs change.

15 strategic-framework reference documents in `skills/context-engine/` support the methodology — Five Digital Markets, Channel Families, In-Market vs Out-Market, Multi-Dimensional Decision Framework, Unit Economics, Actionable Persona Format, B2B Decision-Making Unit, Three-Scenario Forecasting, 30/60/90-Day Framework, Reporting Cadence, Fixed vs Variable Budget, Competitor 3-Question Output, India Market Context, plus more.

---

## Architecture

### 25 specialist agents

Marketing strategist · brand guardian · content creator · email specialist · social-media manager · PR outreach · SEO specialist · CRO specialist · analytics analyst · marketing scientist · competitor intelligence · campaign orchestrator · crisis communicator · synthetic-audience moderator · creative director · channel specialist · paid-media planner · influencer-relations · MarTech architect · GEO/AEO intelligence · multilingual coordinator · agency-operations · pricing strategist · partnership-development · attribution analyst.

Each agent has scoped responsibilities, explicit input/output contracts, and references the Living Project Instruction File before acting.

### 149 skills

Skills are invoked by description match through the Skill tool, addressable as `/digital-marketing-pro:<skill-name>` from the chat. Coverage: brand setup, content production (blog / ad / email / social / landing / video / PR / case study), SEO / AEO / GEO audits, competitor monitoring, campaign planning, channel-specific strategies, attribution, churn risk, lifecycle journeys, intelligence reports, eval framework, knowledge management, multi-brand operations, regional configuration.

### 10 top-level commands (Customize panel)

These are the discoverable slash commands in Claude Code's slash palette. Each wraps the related skill(s) and adds argument hints + execution safety:

| Command | What it does |
|---|---|
| `/digital-marketing-pro:brand-setup` | Set up a new brand profile with voice, audience, competitors, compliance |
| `/digital-marketing-pro:engagement` | Run the full 12-part engagement methodology |
| `/digital-marketing-pro:campaign-plan` | Generate a multi-channel campaign plan with budget, timeline, KPIs |
| `/digital-marketing-pro:seo-audit` | Comprehensive SEO audit — technical, on-page, content, E-E-A-T, AI visibility |
| `/digital-marketing-pro:content-engine` | Draft blog posts, ad copy, emails, social, landing pages, video scripts |
| `/digital-marketing-pro:performance-report` | Performance report with trends, anomaly detection, recommendations |
| `/digital-marketing-pro:competitor-analysis` | Multi-dimensional competitive analysis across content, SEO, ads, social, pricing |
| `/digital-marketing-pro:email-sequence` | Complete email sequences with subject lines, copy, timing, segmentation |
| `/digital-marketing-pro:check` | Pre-publish quality gate (hallucination + brand voice + structure + claims) |
| `/digital-marketing-pro:status` | Unified brand snapshot (profile, engagements, recent insights, compliance) |

Plus 113 additional skills addressable via `/digital-marketing-pro:<skill-name>` — `:competitor-monitor`, `:churn-risk`, `:autopilot-status`, `:agency-dashboard`, `:integrations`, `:connect`, `:help`, `:learn`, `:switch-brand`, `:keyword-research`, `:tech-seo-audit`, `:local-seo-audit`, `:aeo-audit`, `:client-onboarding`, `:journey-design` … see `/digital-marketing-pro:help` for the full list once installed, or browse `skills/` in the repo.

### 70 Python scripts

Optional. Knowledge-only mode (0 MB, no install) covers all 149 skills + 25 agents + 170+ reference knowledge files. Lite mode (~15 MB, `pip install nltk textstat`) adds brand-voice scoring, content quality scoring, readability analysis. Full mode (~50 MB, `pip install -r scripts/requirements.txt`) adds competitor scraping, QR generation, AI visibility API checking. See [Python dependencies](#python-dependencies-optional).

---

## v3.2 + v3.3 — closing the hook-removal gaps and modernizing for May 2026

v3.0 was a methodology release. v3.1 was a hygiene release that removed the global `SessionStart` and `PreToolUse` hooks that fired on every Claude Code operation in every project. v3.2 added explicit replacements (`/check`, `/status`, embedded hallucination checks, opt-in `auto_save_insights` flag). **v3.3 modernizes the May 2026 reality** across pricing, regulation, and channel mechanics — see [Release notes](#release-notes) below for the full list.

### Quick examples

```bash
# Pre-publish quality gate (replaces the global PreToolUse hook)
/digital-marketing-pro:check drafts/q2-launch-blog.md

# Status snapshot (replaces the global SessionStart banner)
/digital-marketing-pro:status

# Status with options
/digital-marketing-pro:status --brand acme-corp --section engagements
/digital-marketing-pro:status --json
```

### Opt in to ambient insight capture

If you want the prior v3.0 ambient learning behavior, set `auto_save_insights: true` in your `brand-profile.json`. Insights are saved to `~/.claude-marketing/<brand>/insights/` at session end.

### Re-enable hooks at your own settings level

Plugin hooks fire globally regardless of working directory. If you genuinely want a global `PreToolUse` content-check or `SessionStart` brand banner, copy the snippet from `hooks/hooks-reference.example.json` into your own `~/.claude/settings.json`. That keeps the hook scoped to your installation, not pushed onto everyone who installs the plugin.

---

## Updating

```
/plugin marketplace update neels-plugins
/plugin uninstall digital-marketing-pro@neels-plugins
/plugin install digital-marketing-pro@neels-plugins
/reload-plugins
```

`/plugin marketplace update` only refreshes the catalog — it does not bump installed plugin versions. The uninstall + reinstall is what actually pulls the new version. `/reload-plugins` applies the change without a full restart.

If a version stays the same but content changed (fast-iteration debugging):
```
rm -rf ~/.claude/plugins/cache/neels-plugins
/plugin install digital-marketing-pro@neels-plugins
/reload-plugins
```

### Installs in Cowork

Cowork is the Anthropic Desktop computer-use product (macOS/Windows). It supports third-party plugins from custom marketplaces — same `/plugin marketplace add indranilbanerjee/neels-plugins` install pattern, then `/plugin install digital-marketing-pro@neels-plugins`. Cowork has local filesystem access, so the full DM Pro pipeline including all 70 Python scripts runs natively. The only Cowork-specific limitation is **HTTP MCPs only** (no stdio/npx) — DM Pro's 14 HTTP connectors are all Cowork-compatible; for stdio servers see `.mcp.json.example`.

---

## Connectors (MCP integrations)

DM Pro ships with **14 HTTP MCP connectors** that work in both Cowork and Claude Code:

Notion · Slack · Canva · Figma · HubSpot · Amplitude · Ahrefs · Similarweb · Klaviyo · Google Calendar · Gmail · Stripe · Asana · Webflow

For Claude Code users who want the full ~68-server stdio configuration (Google Ads, Meta Ads, GA4, GSC, Mixpanel, Marketo, Brevo, etc. via npx), copy the example:

```bash
cp .mcp.json.example .mcp.json
```

For Cowork users who need services without first-party HTTP MCPs (Google Sheets, Drive, Salesforce, dozens more SaaS), see `.mcp.json.connectors-reference` for **Pipedream / Composio / Zapier / Make.com** aggregator paths.

See [CONNECTORS.md](CONNECTORS.md) for the full reference and [MCP Integration Guide](docs/integrations-guide.md) for setup walkthroughs.

---

## Privacy & compliance — 16 jurisdictions

DM Pro carries jurisdiction-specific compliance rules that auto-apply when a brand declares its target markets. Coverage includes the GDPR umbrella, EU AI Act, CCPA / CPRA (with the Jan 2026 ADMT amendments and AI-derived sensitive data classification), DPDP Act (India — Phase II consent-manager framework effective Nov 13 2026, Phase III hard enforcement May 13 2027), LGPD (Brazil), APPI (Japan), Privacy Act (Australia), POPIA (South Africa), PIPEDA (Canada), PIPL (China), and more.

**v3.3 modernization adds:**
- **EU AI Act Article 50** (applicable Aug 2 2026) — generative-AI marketing content must carry machine-readable C2PA-style watermarks; deepfakes must be visibly disclosed; AI-generated text on matters of public interest must be disclosed. Penalty up to €15M or 3% global turnover.
- **NY synthetic-performer disclosure law** (live June 2026) — $1K–$5K per violation, $10K repeat. Applies to synthetic influencers and AI-generated endorsements.
- **FTC May 2026 endorsement guidance** — covers synthetic influencers, AI testimonials, AI-edited creator content. The `compliance-rules` skill flags these for any campaign targeting US consumers.
- **CJEU March 2026 ruling** — pseudonymized cookie IDs are personal data when re-identification is feasible. Adtech identifier handling now flagged in EU campaigns.
- **DPDP Phase II preparation** — consent manager registration window opens Nov 2026; brands targeting India should prepare consent flows now.

---

## AEO / GEO — May 2026 reality

The search landscape pivoted hard:
- Google AI Overviews now appear on roughly 55% of all Google searches (Seer Interactive, Sept 2025).
- Organic CTR on AI Overview queries dropped ~61% (1.76% → 0.61%).
- ~58% of Google searches are now zero-click.
- ChatGPT search reaches ~883M MAU; Perplexity heavily skews citations to Reddit (47% of factual cites); Wikipedia drives 48% of ChatGPT citations.

DM Pro's AEO / GEO skills (`/digital-marketing-pro:aeo-audit`, `/digital-marketing-pro:geo-monitor`, `/digital-marketing-pro:entity-audit`) reflect this shift:
- **Schema strategy refresh**: Google's March 2026 core update demoted FAQ / Review / HowTo schema on non-primary pages. Skills now emphasize entity-rich JSON-LD (Article + Organization + Person + Product) and produce an **LLMs.txt** companion file (curated map of high-value pages for AI crawlers).
- **Citation tracking**: agentic skills detect mentions across ChatGPT, Perplexity, Google AI Overviews, Claude, Bing Copilot, Gemini. For ongoing measurement, integrate with Profound / Otterly / Conductor AgentStack via the connectors layer.
- **Share of AI Voice** as a first-class metric in `/digital-marketing-pro:performance-report`.

---

## Channel guidance — May 2026 updates

- **LinkedIn (March 2026 algorithm shift):** external links and engagement bait penalized ~60%. New **Depth Score** measures dwell time on post. Followers no longer guarantee reach. Skills updated to optimize for relevance and Depth Score.
- **Email:** Apple Mail Privacy Protection now affects ~64% of B2C opens — open rate is functionally dead as a primary KPI. **DMARC + RFC 8058 one-click POST unsubscribe** is mandatory; non-compliant bulk mail to Gmail / Yahoo / Microsoft gets permanent 550 rejections (was temp 421). Spam threshold tightened to <0.10%. The `email-sequence` skill enforces all of this.
- **TikTok (post Jan 22 2026 USDS Joint Venture closing):** US data and algorithm under USDS LLC; ByteDance retains <20%. AI-generated creators allowed only with disclosure; AI content excluded from Creator Rewards Program. Daily shoppable-post limits effective May 11 2026. Channel skills updated.
- **WhatsApp (per-message pricing since 1 July 2025):** India marketing template ≈ USD 0.0118 per message — cheapest globally. 72-hour free service window opens from CTWA ads or Page CTAs. Service messages in the 24-hour customer-care window remain free. India-market context skills carry the new pricing.
- **Third-party cookies — deprecation cancelled:** Chrome formally abandoned the timeline. Privacy Sandbox APIs being retired (CHIPS, FedCM, Private State Tokens kept). First-party data is now the strategic priority — 85% of publishers expect first-party data role to grow in 2026. The `attribution-model` skill defaults to first-party + MMM + incrementality stack.
- **Sora dependency note:** OpenAI's consumer Sora app is being discontinued April 26 2026; Sora API September 24 2026. AI creative briefs default to Runway Gen-4 / Veo 3.x / Kling 3.0 instead.

---

## How it works

### Session lifecycle

1. **Session start** — brand context is available on demand via `/digital-marketing-pro:status`. (v3.0 had this auto-load via SessionStart hook; v3.1 removed the global hook; v3.3 keeps it on-demand only — no global side effects.)
2. **During the session** — request marketing help naturally. The plugin matches your request to the right module(s) and agent(s), auto-applies brand voice, compliance rules, industry benchmarks, guidelines.
3. **Pre-publish** — `/digital-marketing-pro:check` runs the unified quality gate (hallucination + brand voice + structure + claims) before content ships.
4. **Session end** — if `auto_save_insights: true` is in your brand profile, key learnings auto-save to `~/.claude-marketing/<brand>/insights/`. Otherwise insights stay session-local.

### Multi-client workflow (agencies)

1. Create profiles per client: `/digital-marketing-pro:brand-setup`
2. Switch clients: `/digital-marketing-pro:switch-brand` or just say "switch to [client name]"
3. Outputs adapt to the active client's voice, compliance, jurisdictions, history
4. Each client's data lives in its own `~/.claude-marketing/<brand-slug>/` directory

See [Multi-Brand & Agency Guide](docs/multi-brand-guide.md) for detailed workflows.

---

## Documentation

| Guide | Description |
|---|---|
| [Getting Started](docs/getting-started.md) | Installation, first brand setup, first marketing task — with worked examples |
| [Brand Guidelines](docs/brand-guidelines.md) | Importing voice guides, restrictions, channel styles, templates, agency SOPs |
| [Multi-Brand & Agency Guide](docs/multi-brand-guide.md) | Multi-brand corporations and agency multi-client workflows |
| [Strategy & KPI Mapping](docs/strategy-and-kpis.md) | Business objectives → KPI frameworks → campaign strategy → measurement loop |
| [Integrations Guide](docs/integrations-guide.md) | MCP setup for GA4, HubSpot, Google Ads, Meta, and more |
| [Engagement Methodology](docs/engagement-methodology.md) | Deep-dive on the 12-Part Strategy Flow |
| [Competitor Intelligence](docs/competitor-intelligence.md) | Setting up competitors, running analysis, responding to competitive moves |
| [Claude Interfaces](docs/claude-interfaces.md) | What works in Claude Code, Cowork, Desktop, claude.ai |
| [Architecture](docs/architecture.md) | Technical deep-dive for contributors and power users |
| [Testing Guide](TESTING-GUIDE.md) | Per-phase test checklist for plugin contributors |

Two PDF references at the repo root: `DM_Strategy_Complete_Learning_Guide.pdf` (full methodology) and `DM_Strategy_Flow_v3_2_Visualization_v1_23Apr26.pdf` (one-page visual map).

---

## Python dependencies (optional)

The plugin works fully without any Python installation. All marketing knowledge, frameworks, agent capabilities, and slash commands work out of the box.

**Knowledge-only mode (0 MB, no install) — Default**
All 16 modules, 25 agents, 149 skills, and 170+ reference knowledge files work with zero dependencies.

**Lite mode (~15 MB) — Enables scoring scripts**
```
pip install nltk textstat
```
Adds: brand-voice scoring, content quality scoring, readability analysis.

**Full mode (~50 MB) — Enables all scripts**
```
pip install -r scripts/requirements.txt
```
Adds everything in lite mode plus: competitor scraping (`beautifulsoup4`, `requests`), QR code generation, AI visibility API checking.

---

## Troubleshooting

### `/digital-marketing-pro:<skill-name>` doesn't autocomplete in the slash palette
Only the 10 commands in `commands/` show in slash autocomplete. The other 113 skills are addressable via `/digital-marketing-pro:<name>` but won't appear in autocomplete. Use `/digital-marketing-pro:help` to see the full list, or open `skills/` in the repo.

### `/dm:` shortcut commands no longer work
As of v3.2.2 the canonical namespace is `/digital-marketing-pro:`. The `/dm:` prefix was removed in the namespace sweep — use `/digital-marketing-pro:brand-setup`, `/digital-marketing-pro:engagement`, etc. ~600 references were swept across docs and runtime files.

### Manifest install error: "repository field is an object" or "$schema unknown"
Fixed in v3.2.1. Update via the [Updating](#updating) section.

### The plugin claims `/dm:check` will run automatically on every Write/Edit
That was the v3.0/v3.1 behavior via a global PreToolUse hook. Removed in v3.1 because plugin hooks fire across every project regardless of context. Now use `/digital-marketing-pro:check` explicitly before publishing, or re-enable the hook at your own user-settings level — see `hooks/hooks-reference.example.json` for the snippet.

### Where is my brand data stored?
`~/.claude-marketing/<brand-slug>/`. Engagements live in `engagements/<engagement-slug>/` with the 12 numbered subdirectories (01-client-inputs … 12-improvement) plus the Living Project Instruction File at the engagement root.

### Compliance rule for [my jurisdiction] looks out of date
Open an issue with the citation. Privacy and AI law change quarterly. v3.3 covers the May 2026 state of the EU AI Act, CCPA ADMT, DPDP Phase II, NY synthetic-performer law, and the FTC May 2026 endorsement guidance — but enforcement actions and amendments will continue.

---

## FAQ

**Q: Which Claude interface should I use?**

| | Claude Code | Claude Cowork | Claude Desktop (no Cowork) | claude.ai web |
|-|:-:|:-:|:-:|:-:|
| Full plugin support | Yes | Yes | Partial | No |
| Brand memory | Yes | Yes | No | No |
| MCP integrations | All | HTTP only | HTTP only | No |
| Document creation (Excel, PPT) | No | Yes | No | No |
| Recommended for | Terminal workflows + scripting | Visual desktop workflows | Quick content | One-off questions |

**Q: How does this compare to Anthropic's official marketing plugins?**
Anthropic's directory has not yet accepted a full multi-agent marketing methodology plugin. DM Pro covers a much wider surface — full 12-part methodology, 16 industry profiles, 16 jurisdictions, multi-brand operations — than any single official marketing plugin currently in the directory.

**Q: How much does it cost to run?**
Plugin is MIT-licensed and free. Claude API costs vary with engagement complexity. A full 12-part engagement using Opus 4.7 typically runs $15–40 in API costs across 50–60 documents.

**Q: Can I run multiple brands in parallel?**
Yes. Each brand has its own `~/.claude-marketing/<brand-slug>/` directory and Python script state. Switch brands with `/digital-marketing-pro:switch-brand`.

**Q: What if I only want a campaign plan, not the full 12-part methodology?**
Skip straight to `/digital-marketing-pro:campaign-plan`. The full engagement is the canonical path but every individual surface (campaign / SEO audit / content / competitor / email / report) is independently runnable.

---

## Cross-platform compatibility

| Platform | Status |
|---|---|
| Claude Code CLI | Full support |
| Claude Code Desktop | Full support |
| Anthropic Cowork | Full support (HTTP MCPs only — see `.mcp.json.connectors-reference`) |
| claude.ai web chat | Not supported (`/plugin` not available) |
| Codex / Cursor / Gemini CLI | Skills (SKILL.md files) are portable; rename `.claude-plugin/` to platform's convention |

---

## Neelverse Marketing Suite

DM Pro is part of a three-plugin suite that share the same brand profiles:

| Plugin | What it does |
|---|---|
| **Digital Marketing Pro** (this plugin) | End-to-end engagement methodology — 12-Part Strategy Flow, Four Core Documents, Two-Views Model |
| [ContentForge](https://github.com/indranilbanerjee/contentforge) | Publication-ready content via 11-phase pipeline, three-category internal linking, real .docx output |
| [SocialForge](https://github.com/indranilbanerjee/socialforge) | Social media calendar with AI image + video generation (Vertex AI / Kling v3.0) |

```
/plugin marketplace add indranilbanerjee/neels-plugins
/plugin install digital-marketing-pro@neels-plugins
/plugin install contentforge@neels-plugins
/plugin install socialforge@neels-plugins
```

---

## Release notes

**v3.4.1 (2026-05-17)** — Audit & corrections pass on v3.4.0. **(1) C2PA script — actually works now.** v3.4.0 shipped with broken API calls (`c2pa.create_signer`, `c2pa.sign_file` — neither exists in c2pa-python 0.32.6). Rewrote against the real `c2pa.Builder` + `c2pa.Signer.from_info(C2paSignerInfo)` API, fixed the self-signed dev cert to include the EKU + Subject Key Identifier extensions C2PA requires, fixed the manifest read-back to use `c2pa.Reader(format, stream)` not the non-existent `Reader.from_file`. End-to-end tested: 75-byte test PNG → 42,818-byte signed PNG with `manifest_embedded_and_verified=true` and round-trippable assertions. **(2) Unified ads MCP entries corrected.** Synter endpoint was wrong (`mcp.synter.com/sse` → actual `mcp.syntermedia.ai/mcp/`, X-Synter-Key auth) and platform count overstated (claimed 14, actual 7: Google + Meta + LinkedIn + Microsoft + Reddit + TikTok + X). Ryze AI is a managed OAuth service not a generic HTTP MCP — corrected to point at the per-platform Google Ads endpoint and noted the managed-OAuth nature. Northbeam GitHub URL corrected to `mattcoatsworth/Northbeam-MCP-Server` (community-maintained, not first-party from Northbeam Inc). **(3) Parallel-dispatch speedup claim softened** from flat "~6× wall-clock speedup" to honest "4–6× parallelism with ~50–80% wall-clock reduction (3–8 concurrent subagents is the sweet spot; past 8 you queue against rate limits)" with a token-cost note. Applied in engagement-workflow + competitor-analysis + seo-audit. **(4) Submission URLs:** `platform.claude.com/plugins/submit` confirmed; `claude.ai/settings/plugins/submit` removed as unverified.

**v3.4.0 (2026-05-16)** — Four deferred items from the v3.3 audit, now shipped: **(1)** C2PA content-provenance for EU AI Act Article 50 compliance — new `scripts/embed-c2pa.py` wrapping `c2pa-python`, new `/digital-marketing-pro:c2pa-metadata` skill, pre-publish gate integration so `/check` treats missing C2PA manifest on AI-flagged assets in EU campaigns as CRITICAL (BLOCKED), new `Section 1.1b` in `compliance-rules.md` documenting Article 50. **(2)** Unified ads-platform MCPs added to connectors catalog (corrections in v3.4.1). **(3)** Explicit parallel subagent dispatch in `engagement-workflow` (Parts 2, 4, 9, 10, 11 dispatch independent sub-tasks via multiple Task calls in one message; Parts 1→2, 3→4, 5→6, 7→8, 8→9 remain sequential due to real data dependencies) + `competitor-analysis` + `seo-audit` + `content-engine` + `campaign-plan` (speedup claims corrected in v3.4.1). Leverages Claude Code's April 2026 parallel-subagent initialization. **(4)** Anthropic Software Directory submission packet at `SUBMISSION.md` pre-stages every input the form requires. Skill count 149 → **150**, script count 70 → **71**.

**v3.3.0 (2026-05-15)** — May 2026 modernization sweep. Privacy & compliance updates: EU AI Act Article 50 (Aug 2 2026 enforcement, C2PA metadata for AI marketing content), DPDP Phase II timeline (Nov 2026), NY synthetic-performer disclosure law (June 2026), FTC May 2026 endorsement guidance, CCPA ADMT amendments (Jan 2026), CJEU pseudonymized-cookie ruling (March 2026). Channel guidance updates: LinkedIn algorithm shift (external-link penalty, Depth Score), email DMARC + RFC 8058 one-click POST baseline (open rate dropped as KPI), TikTok USDS Joint Venture mechanics + AI creator labeling, WhatsApp per-message pricing (corrected from deprecated conversation-based model in 3 skill files), schema refresh (LLMs.txt, entity-rich JSON-LD, deprecate FAQ/Review/HowTo on non-primary pages), Sora deprecation note for AI creative briefs. AEO/GEO modernization: Google AI Overviews + zero-click reality, Profound/Otterly/Conductor measurement integration. README fully restructured — Quick Start at top with install + auto-update toggle as steps 1-2, "Where your files go" section, version histories collapsed at the bottom. Top Commands table corrected to use `/digital-marketing-pro:` prefix (was bare `/brand-setup` form that conflicted with other plugins). Duplicate "Option C" install heading fixed. Top version badge bumped 3.2.0 → 3.3.0.

**v3.2.2 (2026-05-09)** — Swept all `/dm:` shorthand to `/digital-marketing-pro:` across ~600 references in README, getting-started, TESTING-GUIDE, engagement-methodology, multi-brand-guide, brand-guidelines, architecture, all agent files, all 149 skill SKILL.md files, command files, and CHANGELOG. Users can now copy-paste any command from any doc and have it work.

**v3.2.1 (2026-05-04)** — Fixed plugin manifest install format: `repository` must be a string URL (not npm-shorthand object), `$schema` field removed.

**v3.2.0 (2026-05-03)** — Closes the v3.1 hook-removal gaps with explicit replacements: `/digital-marketing-pro:check` pre-publish gate, `/digital-marketing-pro:status` brand snapshot, embedded mandatory hallucination check inside content-creator/email-specialist/social-media-manager/pr-outreach agents, opt-in `auto_save_insights` brand flag for ambient learning capture.

**v3.1.0 (2026-05-03)** — Removed all global hooks. Prior `SessionStart` and `PreToolUse mcp_.*` matchers were firing across every project regardless of context. Hook config preserved as reference at `hooks/hooks-reference.example.json`.

**v3.0.0 (2026-04-23)** — 12-Part Engagement Methodology. Four Core Documents (61 explicit steps). Two-Views Model. Decision Matrix. Update-Back Rule. Living Project Instruction File. 23 strategic-framework reference docs.

**Earlier versions:** see [CHANGELOG.md](CHANGELOG.md) for v2.7 and earlier — 25 specialist agents, 14 HTTP MCP connectors, 16 industry profiles, 16 privacy-law jurisdictions, full execution-layer support.

---

## License

MIT — see [LICENSE](LICENSE).

## Support

- **Issues:** [GitHub Issues](https://github.com/indranilbanerjee/digital-marketing-pro/issues)
- **Discussions:** [GitHub Discussions](https://github.com/indranilbanerjee/digital-marketing-pro/discussions)

## Credits

Created by Indranil Banerjee. Built for Claude Code & Cowork. Powered by Anthropic Claude.
