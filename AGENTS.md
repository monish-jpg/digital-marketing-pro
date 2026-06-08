# Digital Marketing Pro — agent context

This file is auto-loaded by OpenAI Codex, Google Antigravity, GitHub Copilot CLI, Cursor (when in the agent context chain), and other Agent Skills runtimes. It is the equivalent of `CLAUDE.md` for non-Claude surfaces.

## What this plugin is

Digital Marketing Pro is a comprehensive open-source AI marketing plugin shipping **158 skills, 25 specialist agents, a 12-Part Strategy Flow, and EU AI Act Article 50 readiness**. Built for marketing agencies, in-house teams running 50–200 brands, and consultancies.

**Supported surfaces (v3.12.0):** Claude Code (CLI + IDE extensions, min v2.1.157), Anthropic Cowork, OpenAI Codex (CLI + IDE + App), Cursor 2.5+, GitHub Copilot CLI, Google Antigravity 2.0 (CLI + IDE).

**Cowork-specific:** On Anthropic Cowork the per-session filesystem is ephemeral (`~/.claude-marketing/` AND `${CLAUDE_PLUGIN_DATA}` BOTH vanish at session end — known platform issue #51398). Run `/digital-marketing-pro:cowork-setup` once per team to route brand state through a Google Drive MCP so profiles, plans, and reports survive across sessions.

## How to use it as an agent

1. **Discover skills by description.** All 158 skills auto-discover via SKILL.md frontmatter (`name:` + `description:`). Match user intent to skill description.
2. **Run skills by routing user requests to the matching SKILL.md.** Read the skill body for instructions, scripts to run, references to pull.
3. **Skill bodies may reference Python scripts at `scripts/<name>.py`** — invoke via Bash / `run_shell_command`.
4. **HTTP MCP connectors are opt-in.** See `.mcp.json.connectors-reference` for the full catalog (Slack, HubSpot, Notion, Gmail, Google Calendar, Stripe, Ahrefs, SimilarWeb, Klaviyo, Amplitude, Canva, Figma, Asana, Webflow). User must configure env vars or set up MCP servers before they connect.
5. **Compliance is mandatory.** Skills enforce GDPR / CCPA / EU AI Act / DPDPA / LGPD / 11 other privacy jurisdictions. Don't skip the compliance gates.
6. **C2PA content provenance is required for AI-generated assets in EU campaigns** (Article 50, applicable 2 Aug 2026). Use `scripts/embed-c2pa.py` to sign before delivery.

## Canonical entry points

| User intent | Run skill |
|---|---|
| "Set up a new brand" | `brand-setup` |
| "Run the full strategy flow" | `engagement-workflow` |
| "Build a campaign plan" | `campaign-plan` |
| "Run AEO/GEO audit" | `aeo-geo` (covers Google AI Mode, AI Overviews, ChatGPT search, Claude search, Perplexity, Copilot, Gemini App) |
| "Validate the brand profile" | `validate-profile` |
| "Audit current campaign state" | `campaign-audit` |
| "Launch a multi-channel campaign" | `launch-campaign` |
| "Check connector readiness" | `doctor` (also reports model-registry freshness and Cowork+Drive routing status) |
| "Set up Cowork team persistence" | `cowork-setup` (first-run + when brand state isn't persisting) |
| "Generate an executive dashboard" | `executive-dashboard` |
| "Run a full SEO audit" | `seo-audit` |

## Files in this repo

- `skills/<name>/SKILL.md` — 157 Agent Skills (the surface area). Each is byte-portable across all supported surfaces.
- `agents/<name>.md` — 25 specialist agent definitions (Claude Code subagent format; on Codex use TOML conversion at `~/.codex/agents/`, on Antigravity use `/agent` ad-hoc spawn).
- `commands/<name>.md` — Claude Code slash commands (`/digital-marketing-pro:<name>`). On other surfaces invoke via natural-language intent — the SKILL.md routing picks up the same handler.
- `scripts/*.py` — 84 Python helpers (optional, run when Python 3.8+ is present). Includes `connector_resolver.py` + `connector_executor.py` (8 executable HTTP connectors) + `resolve_model.py` + `refresh_models.py` (shared model curator with auto-fall-forward on deprecated IDs) + `plugin-metadata.py` (environment + asset probes) + `drive-sync-state.py` (Cowork+Drive routing ledger, v3.12.0) + `skill-line-check.py` (CI line guard).
- `tests/test_*.py` + `tests/run_all.py` — 49 stdlib-unittest tests covering `resolve_model`, `drive-sync-state`, `plugin-metadata`, `skill-line-check`, `connector_resolver`. Run with `python tests/run_all.py`.
- `settings.json.example` — recommended user settings: `fallbackModel` 3-model resilience chain, `requiredMinimumVersion`, `skillOverrides`, OTel resource attrs.
- `hooks/hooks.json` — ships as `{"hooks":{}}` (zero global hooks). Add hooks at user scope if needed.
- `.mcp.json` — ships as `{"mcpServers":{}}` (zero auto-connecting MCPs). Full catalog at `.mcp.json.connectors-reference`.
- `references/` — 167 reference knowledge files for compliance, channel mechanics, AEO/GEO targets.

## Cross-platform notes

- **Skills are the universal interface.** Same SKILL.md works on Claude Code, Codex, Antigravity, Cursor, Copilot CLI, Gemini CLI (Agent Skills open standard adopted Dec 2025).
- **Claude Code subagents (`agents/*.md`) are Claude-only as static files.** On Codex use the TOML equivalent at `~/.codex/agents/*.toml`. On Antigravity use the `/agent` slash command for ad-hoc spawning.
- **Slash commands are Claude-only as `commands/*.md` files.** On other surfaces invoke skills by name or natural-language intent.
- **MCP env-var syntax differs by surface.** Claude uses `${user_config.VAR}`; Codex/Antigravity use `$VAR`. Our `.mcp.json` ships empty so this doesn't bite.

## Identity / authority

Built and maintained by Indranil Banerjee (https://indranil.in). MIT-licensed. No telemetry. Part of the Neelverse Marketing Suite alongside ContentForge and SocialForge.
