#!/usr/bin/env python3
"""
execution-tracker.py
====================
Audit trail for all executed actions across platforms in Digital Marketing Pro.

Logs every publish, send, launch, and sync so the plugin maintains a complete
record of what was done, when, and on which platform.

Storage: ~/.claude-marketing/brands/{slug}/executions/

Usage:
    python execution-tracker.py --brand acme --action log-execution --data '{"platform": "wordpress", "action_type": "publish-blog", "content_id": "q1-recap", "result": "success", "url": "https://example.com/q1", "details": "Published via REST API"}'
    python execution-tracker.py --brand acme --action get-history
    python execution-tracker.py --brand acme --action get-history --platform wordpress --status success --limit 10
    python execution-tracker.py --brand acme --action get-stats
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

BRANDS_DIR = Path.home() / ".claude-marketing" / "brands"


def get_brand_dir(slug):
    """Get and validate brand directory."""
    brand_dir = BRANDS_DIR / slug
    if not brand_dir.exists():
        return None, f"Brand '{slug}' not found. Run /digital-marketing-pro:brand-setup first."
    return brand_dir, None


def _load_index(executions_dir):
    """Load the execution index file."""
    index_path = executions_dir / "_index.json"
    if not index_path.exists():
        return []
    try:
        return json.loads(index_path.read_text())
    except json.JSONDecodeError:
        return []


def _save_index(executions_dir, index):
    """Save the execution index file."""
    index_path = executions_dir / "_index.json"
    index_path.write_text(json.dumps(index, indent=2))


def log_execution(slug, data):
    """Log an executed action to the audit trail."""
    brand_dir, err = get_brand_dir(slug)
    if err:
        return {"error": err}

    # Validate required fields
    platform = data.get("platform")
    if not platform:
        return {"error": "Missing required field: platform"}

    action_type = data.get("action_type")
    if not action_type:
        return {"error": "Missing required field: action_type"}

    result = data.get("result")
    if result not in ("success", "failure"):
        return {"error": "result must be 'success' or 'failure'."}

    executions_dir = brand_dir / "executions"
    executions_dir.mkdir(exist_ok=True)

    # Generate execution_id: exec-{platform}-{YYYYMMDD-HHMMSS}
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    execution_id = f"exec-{platform}-{timestamp}"

    execution = {
        "execution_id": execution_id,
        "platform": platform,
        "action_type": action_type,
        "content_id": data.get("content_id"),
        "result": result,
        "url": data.get("url"),
        "details": data.get("details"),
        "approval_id": data.get("approval_id"),
        "executed_at": datetime.now().isoformat(),
    }

    # Save individual execution file
    filepath = executions_dir / f"{execution_id}.json"
    filepath.write_text(json.dumps(execution, indent=2))

    # Update index
    index = _load_index(executions_dir)
    index.append({
        "execution_id": execution_id,
        "platform": platform,
        "action_type": action_type,
        "result": result,
        "executed_at": execution["executed_at"],
    })
    _save_index(executions_dir, index)

    return {
        "status": "logged",
        "execution_id": execution_id,
        "path": str(filepath),
    }


def get_history(slug, platform=None, status=None, limit=50):
    """List all executions with optional filters, most recent first."""
    brand_dir, err = get_brand_dir(slug)
    if err:
        return {"error": err}

    executions_dir = brand_dir / "executions"
    if not executions_dir.exists():
        return {"executions": [], "total": 0, "note": "No executions logged yet."}

    # Load all execution files (not just index) for full detail
    executions = []
    for fp in sorted(executions_dir.glob("exec-*.json"), reverse=True):
        try:
            execution = json.loads(fp.read_text())
            executions.append(execution)
        except json.JSONDecodeError:
            continue

    # Apply filters
    if platform:
        executions = [e for e in executions if e.get("platform") == platform]
    if status:
        executions = [e for e in executions if e.get("result") == status]

    # Sort most recent first
    executions.sort(key=lambda e: e.get("executed_at", ""), reverse=True)

    # Apply limit
    total = len(executions)
    executions = executions[:limit]

    return {
        "executions": executions,
        "returned": len(executions),
        "total": total,
    }


def get_stats(slug):
    """Summary statistics for all executions."""
    brand_dir, err = get_brand_dir(slug)
    if err:
        return {"error": err}

    executions_dir = brand_dir / "executions"
    if not executions_dir.exists():
        return {
            "total_executed": 0,
            "by_platform": {},
            "by_status": {},
            "success_rate": 0,
            "last_execution": None,
            "note": "No executions logged yet.",
        }

    # Load index for fast stats
    index = _load_index(executions_dir)
    if not index:
        return {
            "total_executed": 0,
            "by_platform": {},
            "by_status": {},
            "success_rate": 0,
            "last_execution": None,
            "note": "No executions logged yet.",
        }

    total = len(index)
    by_platform = {}
    by_status = {}
    last_execution = None

    for entry in index:
        plat = entry.get("platform", "unknown")
        by_platform[plat] = by_platform.get(plat, 0) + 1

        result = entry.get("result", "unknown")
        by_status[result] = by_status.get(result, 0) + 1

        executed_at = entry.get("executed_at", "")
        if not last_execution or executed_at > last_execution:
            last_execution = executed_at

    success_count = by_status.get("success", 0)
    success_rate = round(success_count / total * 100, 1) if total else 0

    return {
        "total_executed": total,
        "by_platform": by_platform,
        "by_status": by_status,
        "success_rate": success_rate,
        "last_execution": last_execution,
    }


def _stub_action(action: str, brand: str, plan_path: str | None = None,
                  automation_id: str | None = None, platform: str | None = None) -> dict:
    """Structured contract for the launch-campaign skill's 5 activation actions.
    See performance-monitor.py for the design rationale."""
    schemas = {
        "enable-automation": {
            "purpose": "Enable an existing automation / journey / sequence in the configured email or CRM platform. Idempotent — re-running on an already-enabled automation is a no-op.",
            "data_source": "Email platform API (Klaviyo / HubSpot / ActiveCampaign / Brevo / Marketo) via the brand's configured connector.",
            "manual_fallback": "Open the email platform > Flows / Workflows / Journeys, find the automation_id, toggle Active = ON.",
            "fields_returned_when_implemented": ["platform", "automation_id", "previous_state", "new_state", "enabled_at"],
            "called_with": {"automation_id": automation_id, "platform": platform},
        },
        "schedule-posts": {
            "purpose": "Schedule the organic-social posts defined in the campaign plan into the brand's scheduler (Buffer / Hootsuite / Sprout / Later / native platform schedulers).",
            "data_source": "Scheduler API per platform; falls back to native platform scheduling APIs (Meta Graph / LinkedIn Pages API / TikTok Business / Twitter API).",
            "manual_fallback": "Open the scheduler, paste each post's copy + asset + schedule from the plan JSON. Verify timezone alignment with the brand's market.",
            "fields_returned_when_implemented": ["scheduler", "scheduled_post_ids", "platform_count", "first_post_at", "last_post_at"],
            "plan_path_received": plan_path,
        },
        "notify-influencers": {
            "purpose": "Send the campaign-specific creator brief to each contracted influencer named in the plan. Brief content is generated by /digital-marketing-pro:influencer-brief; this action only delivers it.",
            "data_source": "Email (Gmail MCP / SES / SendGrid) or DM via the platform the brand uses for creator relationships.",
            "manual_fallback": "Open the brief PDF for each creator, email it from the brand's account manager.",
            "fields_returned_when_implemented": ["delivery_channel", "creator_count", "delivered_ids", "failed_ids", "sent_at"],
            "plan_path_received": plan_path,
        },
        "pr-send": {
            "purpose": "Distribute the launch press release to the configured press contact list (HARO / Muckrack / native journalist database).",
            "data_source": "PR distribution tool API (Cision / Muckrack / PRWeb) or manual email send.",
            "manual_fallback": "Send the press release as a mail-merge from the brand's PR account; track opens via the chosen tool.",
            "fields_returned_when_implemented": ["distribution_tool", "press_contact_count", "sent_at", "tracking_id"],
            "plan_path_received": plan_path,
        },
        "internal-kickoff": {
            "purpose": "Send the internal kickoff message to the brand team: Slack message to the channel listed in the plan, email to the distribution_list, calendar invite for the launch-day standup if specified.",
            "data_source": "Slack MCP / Gmail MCP / Google Calendar MCP — all via the brand's configured connectors.",
            "manual_fallback": "Post the kickoff message in the team Slack channel; send an email to the distribution list; create a calendar event for the launch-day standup.",
            "fields_returned_when_implemented": ["slack_message_url", "email_message_id", "calendar_event_id", "recipients_count"],
            "plan_path_received": plan_path,
        },
        "launch-ads": {
            "purpose": "Activate the paid-ads portion of the campaign plan across Google Ads / Meta Ads / LinkedIn Ads / TikTok Ads in dependency order. Delegates to the per-platform launch logic but tracks the full multi-platform launch as one transaction.",
            "data_source": "Google Ads API + Meta Marketing API + LinkedIn Marketing API + TikTok Business API via the brand's configured ad-platform connectors.",
            "manual_fallback": "Open each ad platform UI in order (Google Ads, then Meta Ads Manager, then LinkedIn Campaign Manager, then TikTok Ads), activate the campaigns matching the plan's campaign_ids. Record activation timestamps in the launch-record.",
            "fields_returned_when_implemented": ["platforms_activated", "campaign_ids_per_platform", "total_daily_budget", "activated_at"],
            "plan_path_received": plan_path,
            "delegates_to": "/digital-marketing-pro:launch-ad-campaign (paid-ads-only subset)",
        },
    }
    if action not in schemas:
        return {"error": f"unknown stub action: {action}"}
    return {
        "status": "stub_implementation",
        "action": action,
        "brand": brand,
        "version": "3.7.6",
        "note": "Part of the launch-campaign skill surface (v3.7.5). Action contract stable; live implementation staged across releases. Use manual_fallback or wire the listed connector.",
        **schemas[action],
    }


def main():
    parser = argparse.ArgumentParser(description="Execution audit trail for Digital Marketing Pro")
    parser.add_argument("--brand", required=True, help="Brand slug")
    parser.add_argument("--action", required=True,
                        choices=["log-execution", "get-history", "get-stats",
                                 # v3.7.6 — launch-campaign skill surface
                                 "enable-automation", "schedule-posts",
                                 "notify-influencers", "pr-send", "internal-kickoff",
                                 # v3.7.7 — additional launch-campaign surface
                                 "launch-ads"],
                        help="Action to perform")
    parser.add_argument("--data", help="JSON data (for log-execution)")
    parser.add_argument("--platform", help="Filter history by platform")
    parser.add_argument("--status", help="Filter history by result (success/failure)")
    parser.add_argument("--limit", type=int, default=50, help="Max items to return")
    parser.add_argument("--plan", help="Path to approved campaign plan JSON "
                                       "(for schedule-posts / notify-influencers / pr-send / internal-kickoff)")
    parser.add_argument("--automation-id", help="Automation id (for enable-automation)")
    args = parser.parse_args()

    if args.action == "log-execution":
        if not args.data:
            print(json.dumps({"error": "Provide --data with execution JSON"}))
            sys.exit(1)
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid JSON in --data"}))
            sys.exit(1)
        result = log_execution(args.brand, data)

    elif args.action == "get-history":
        result = get_history(args.brand, args.platform, args.status, args.limit)

    elif args.action == "get-stats":
        result = get_stats(args.brand)

    elif args.action in {"enable-automation", "schedule-posts",
                         "notify-influencers", "pr-send", "internal-kickoff",
                         "launch-ads"}:
        result = _stub_action(args.action, args.brand,
                              plan_path=args.plan,
                              automation_id=args.automation_id,
                              platform=args.platform)

    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
