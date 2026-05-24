# Cross-platform install guide

Digital Marketing Pro v3.6.0 ships **three platform-native manifests** alongside the Claude Code manifest, so the same 150 Agent Skills, 71 Python scripts, and 14 HTTP MCP connectors can install cleanly on:

| Platform | Manifest path | Status |
|---|---|---|
| **Claude Code** (CLI + Desktop) + **Anthropic Cowork** | `.claude-plugin/plugin.json` | Full support — agents, skills, commands, hooks, MCP, scripts |
| **OpenAI Codex** (CLI) | `.codex-plugin/plugin.json` | Skills + MCP + hooks + scripts; commands and agents via Codex-native invocation patterns |
| **Cursor** (IDE + CLI) | `.cursor-plugin/plugin.json` | Skills + hooks + scripts; MCP via Cursor's global mcp.json (see below) |

The key insight: **Agent Skills are an open standard.** The `name:` + `description:` SKILL.md frontmatter is interpreted the same way by every major coding agent surface as of May 2026 (Claude Code, OpenAI Codex, Cursor, GitHub Copilot CLI, Google Antigravity 2.0). DM Pro reuses the same `skills/` directory across all three platform manifests — no skill duplication, no maintenance fork.

---

## Install on Claude Code (canonical path)

```bash
# Add the marketplace (one time)
/plugin marketplace add indranilbanerjee/neels-plugins

# Install
/plugin install digital-marketing-pro@neels-plugins
```

See the [main README](../README.md#install-the-plugin) for the full Claude Code experience.

---

## Install on OpenAI Codex

Codex plugin install (CLI v0.6+ which added third-party plugin support, May 2026):

```bash
# Codex installs via direct GitHub reference — no marketplace layer needed
codex plugin install indranilbanerjee/digital-marketing-pro
```

After install, restart your Codex session. Codex auto-discovers the `skills/` directory and invokes skills based on natural-language intent — you don't need slash commands. Try:

```
"Set up a new brand for digital marketing engagement."
"Run an AEO audit for example.com across ChatGPT, Perplexity, AI Mode, and AI Overviews."
"Build an ad-creative brief for our Q3 Meta campaign with C2PA-signed visuals."
```

**What works on Codex:**
- All 150 Agent Skills (auto-discovered via SKILL.md frontmatter — same open standard as Claude Code)
- All 14 HTTP MCP connectors (Slack, HubSpot, Notion, Stripe, Gmail, Google Calendar, Asana, Webflow, Ahrefs, SimilarWeb, Klaviyo, Amplitude, Figma, Canva) — Codex reads `.mcp.json` directly
- All 71 Python scripts (campaign-tracker, geo-tracker, technical-seo-auditor, embed-c2pa, etc.) run when Python 3.8+ is present
- `hooks/hooks.json` (empty by default — no global hooks, matches Claude Code v3.1+ behaviour)

**What's Claude-Code-native and isn't auto-invoked on Codex:**
- Slash commands in `commands/` are Claude Code's `/<plugin>:<command>` syntax. On Codex, invoke the underlying workflow via natural language and the SKILL.md routing picks up the same handler. E.g., `/digital-marketing-pro:seo-audit` on Claude Code = "Run an SEO audit" on Codex.
- The 25 specialist sub-agents in `agents/*.md` use Claude Code's specific sub-agent format. Codex has its own sub-agent / app concept (`.app.json`) — DM Pro doesn't ship Codex-specific apps in v3.6.0. The skills still produce the same outputs because each skill embeds the relevant agent instructions inline.

---

## Install on Cursor

Cursor plugin install (Cursor v2.5+, which formalised the plugin marketplace in Feb 2026):

```bash
# In a Cursor terminal, or by clicking Install in the in-app plugin browser:
cursor plugin install indranilbanerjee/digital-marketing-pro
```

After install, restart Cursor (or run `Cursor: Reload Window` from the command palette). Cursor auto-discovers `skills/` and surfaces them to the Cursor Agent for context-driven invocation.

**What works on Cursor:**
- All 150 Agent Skills (auto-discovered — Cursor uses the same SKILL.md frontmatter convention)
- `hooks/hooks.json` (empty by default — `afterFileEdit` and `beforeMCPExecution` lifecycle events available if you want to register them)
- All 71 Python scripts run from Cursor's terminal context

**MCP on Cursor — manual one-time configuration:**

Cursor reads MCP servers from a global `mcp.json` (no leading dot), not from the plugin directory. To make DM Pro's 14 HTTP MCP connectors available in Cursor:

1. Open Cursor → Settings → MCP Servers
2. Copy the contents of `.mcp.json` from your installed DM Pro plugin directory into Cursor's MCP configuration
3. Set required env vars per connector (see `docs/integrations-guide.md`)

This is a Cursor platform constraint, not a DM Pro limitation. Cursor's MCP scoping is global per workspace, not per plugin (May 2026 behaviour).

**What's Claude-Code-native and isn't auto-invoked on Cursor:**
- The 10 slash commands are Claude Code syntax. On Cursor, the Cursor Agent picks the right skill from natural-language intent.
- 25 sub-agents in `agents/*.md` — Cursor has "rules" and "modes" instead of sub-agents; skills embed the agent instructions inline, so outputs are equivalent.

---

## What's portable vs platform-specific

| Component | Claude Code | Codex | Cursor | Notes |
|---|---|---|---|---|
| **Skills** (`skills/<name>/SKILL.md`) | yes | yes | yes | Open Agent Skills standard — identical frontmatter across all three |
| **Python scripts** (`scripts/*.py`) | yes | yes | yes | Run when Python 3.8+ is present; graceful fallback otherwise |
| **HTTP MCP catalog** (`.mcp.json`) | yes (auto-loaded) | yes (auto-loaded) | manual paste into Cursor global mcp.json | Same JSON shape; Cursor's plugin-scoped MCP not yet GA (May 2026) |
| **Hooks** (`hooks/hooks.json`) | yes | yes | yes | Empty by default in DM Pro v3.1+ |
| **Slash commands** (`commands/*.md`) | yes | partial (Codex `/cmds`) | n/a (natural language) | Codex maps; Cursor invokes via Agent |
| **Sub-agents** (`agents/*.md`) | yes | partial (Codex `.app.json`) | n/a | Skills already embed agent instructions — output parity preserved |

---

## Updating

| Platform | Update command |
|---|---|
| Claude Code | `/plugin update digital-marketing-pro@neels-plugins` (or auto-update via Marketplace settings) |
| Codex | `codex plugin update digital-marketing-pro` |
| Cursor | `cursor plugin update digital-marketing-pro` (or in-app Plugin Manager) |

All three platforms pull from the same GitHub `main` branch — no version drift between platform builds.

---

## Reporting platform-specific bugs

| Platform | Where to file |
|---|---|
| Claude Code platform bug (manifest parse, plugin install crash) | https://github.com/anthropics/claude-code/issues |
| Codex platform bug | https://github.com/openai/codex/issues |
| Cursor platform bug | https://github.com/cursor/plugins/issues |
| DM Pro skill/content bug (any platform) | https://github.com/indranilbanerjee/digital-marketing-pro/issues |
