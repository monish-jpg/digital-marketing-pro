#!/usr/bin/env python3
"""
performance-monitor.py
======================
Aggregate metrics, detect anomalies, and manage baselines for Digital Marketing Pro.

Stores timestamped performance snapshots and uses statistical analysis to flag
metrics that deviate significantly from historical norms.

Storage: ~/.claude-marketing/brands/{slug}/performance/

Usage:
    python performance-monitor.py --brand acme --action pull-metrics --data '{"sessions": 1234, "conversions": 56, "revenue": 7890, "ctr": 3.2}'
    python performance-monitor.py --brand acme --action save-snapshot --data '{"sessions": 1234, "conversions": 56, "revenue": 7890}'
    python performance-monitor.py --brand acme --action detect-anomalies --data '{"sessions": 500, "conversions": 2, "revenue": 100}'
    python performance-monitor.py --brand acme --action get-baseline
"""

import argparse
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

BRANDS_DIR = Path.home() / ".claude-marketing" / "brands"

MAX_SNAPSHOTS = 90
BASELINE_WINDOW = 30
ANOMALY_THRESHOLD = 2.0  # standard deviations


def get_brand_dir(slug):
    """Get and validate brand directory."""
    brand_dir = BRANDS_DIR / slug
    if not brand_dir.exists():
        return None, f"Brand '{slug}' not found. Run /digital-marketing-pro:brand-setup first."
    return brand_dir, None


def _load_snapshots(perf_dir):
    """Load all performance snapshot files, sorted oldest to newest."""
    snapshots = []
    if not perf_dir.exists():
        return snapshots
    for fp in sorted(perf_dir.glob("snapshot-*.json")):
        try:
            snapshot = json.loads(fp.read_text())
            snapshots.append(snapshot)
        except json.JSONDecodeError:
            continue
    return snapshots


def _prune_snapshots(perf_dir):
    """Remove oldest snapshots if count exceeds MAX_SNAPSHOTS."""
    files = sorted(perf_dir.glob("snapshot-*.json"))
    if len(files) > MAX_SNAPSHOTS:
        for fp in files[: len(files) - MAX_SNAPSHOTS]:
            fp.unlink()


def _extract_metric_keys(snapshots):
    """Collect all unique metric keys across snapshots."""
    keys = set()
    for snap in snapshots:
        metrics = snap.get("metrics", {})
        keys.update(metrics.keys())
    return sorted(keys)


def _safe_stdev(values):
    """Calculate standard deviation, returning 0 for fewer than 2 values."""
    if len(values) < 2:
        return 0.0
    return statistics.stdev(values)


def pull_metrics(slug, data):
    """Normalize and store a metrics snapshot, returning the normalized result."""
    brand_dir, err = get_brand_dir(slug)
    if err:
        return {"error": err}

    if not data or not isinstance(data, dict):
        return {"error": "Provide a metrics object in --data."}

    perf_dir = brand_dir / "performance"
    perf_dir.mkdir(exist_ok=True)

    # Normalize: ensure all values are numeric
    normalized = {}
    for key, value in data.items():
        if isinstance(value, (int, float)):
            normalized[key] = value
        elif isinstance(value, str):
            try:
                normalized[key] = float(value)
            except ValueError:
                continue
        # Skip non-numeric values silently

    if not normalized:
        return {"error": "No valid numeric metrics found in --data."}

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    snapshot = {
        "snapshot_id": f"snapshot-{timestamp}",
        "recorded_at": datetime.now().isoformat(),
        "metrics": normalized,
    }

    filepath = perf_dir / f"snapshot-{timestamp}.json"
    filepath.write_text(json.dumps(snapshot, indent=2))
    _prune_snapshots(perf_dir)

    return {
        "status": "stored",
        "snapshot_id": snapshot["snapshot_id"],
        "metrics": normalized,
        "path": str(filepath),
    }


def save_snapshot(slug, data):
    """Save a timestamped performance snapshot (max 90 kept)."""
    brand_dir, err = get_brand_dir(slug)
    if err:
        return {"error": err}

    if not data or not isinstance(data, dict):
        return {"error": "Provide a metrics object in --data."}

    perf_dir = brand_dir / "performance"
    perf_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    snapshot = {
        "snapshot_id": f"snapshot-{timestamp}",
        "recorded_at": datetime.now().isoformat(),
        "metrics": data,
    }

    filepath = perf_dir / f"snapshot-{timestamp}.json"
    filepath.write_text(json.dumps(snapshot, indent=2))
    _prune_snapshots(perf_dir)

    # Count remaining
    remaining = len(list(perf_dir.glob("snapshot-*.json")))

    return {
        "status": "saved",
        "snapshot_id": snapshot["snapshot_id"],
        "total_snapshots": remaining,
        "path": str(filepath),
    }


def detect_anomalies(slug, data):
    """Detect metrics that deviate significantly from recent baselines."""
    brand_dir, err = get_brand_dir(slug)
    if err:
        return {"error": err}

    if not data or not isinstance(data, dict):
        return {"error": "Provide current metrics in --data."}

    perf_dir = brand_dir / "performance"
    snapshots = _load_snapshots(perf_dir)

    # Use last BASELINE_WINDOW snapshots
    recent = snapshots[-BASELINE_WINDOW:]

    if len(recent) < 3:
        return {
            "status": "insufficient_data",
            "snapshots_available": len(recent),
            "minimum_required": 3,
            "note": "Need at least 3 historical snapshots to detect anomalies.",
        }

    anomalies = []
    metric_keys = set(data.keys())

    for key in sorted(metric_keys):
        current_value = data.get(key)
        if not isinstance(current_value, (int, float)):
            continue

        # Collect historical values for this metric
        historical = []
        for snap in recent:
            val = snap.get("metrics", {}).get(key)
            if isinstance(val, (int, float)):
                historical.append(val)

        if len(historical) < 3:
            continue

        mean = statistics.mean(historical)
        stdev = _safe_stdev(historical)

        if stdev == 0:
            # All historical values identical; flag if current differs at all
            if current_value != mean:
                anomalies.append({
                    "metric": key,
                    "current": current_value,
                    "mean": mean,
                    "std_dev": 0,
                    "deviation": "inf",
                    "direction": "above" if current_value > mean else "below",
                })
            continue

        z_score = (current_value - mean) / stdev

        if abs(z_score) > ANOMALY_THRESHOLD:
            anomalies.append({
                "metric": key,
                "current": current_value,
                "mean": round(mean, 2),
                "std_dev": round(stdev, 2),
                "z_score": round(z_score, 2),
                "deviation": f"{abs(round(z_score, 1))} std devs",
                "direction": "above" if z_score > 0 else "below",
            })

    return {
        "anomalies": anomalies,
        "total_anomalies": len(anomalies),
        "snapshots_analyzed": len(recent),
        "threshold": f"{ANOMALY_THRESHOLD} std devs",
    }


def get_baseline(slug):
    """Calculate baseline statistics from stored performance snapshots."""
    brand_dir, err = get_brand_dir(slug)
    if err:
        return {"error": err}

    perf_dir = brand_dir / "performance"
    snapshots = _load_snapshots(perf_dir)

    # Use last BASELINE_WINDOW snapshots
    recent = snapshots[-BASELINE_WINDOW:]

    if len(recent) < 3:
        return {
            "status": "insufficient_data",
            "snapshots_available": len(recent),
            "minimum_required": 3,
            "note": "Need at least 3 snapshots to calculate a meaningful baseline.",
        }

    metric_keys = _extract_metric_keys(recent)
    baselines = {}

    for key in metric_keys:
        values = []
        for snap in recent:
            val = snap.get("metrics", {}).get(key)
            if isinstance(val, (int, float)):
                values.append(val)

        if len(values) < 2:
            baselines[key] = {"status": "insufficient_data", "data_points": len(values)}
            continue

        baselines[key] = {
            "mean": round(statistics.mean(values), 2),
            "std_dev": round(_safe_stdev(values), 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2),
            "data_points": len(values),
        }

    return {
        "baselines": baselines,
        "snapshots_used": len(recent),
        "window": f"last {BASELINE_WINDOW} snapshots",
    }


def _stub_action(action: str, brand: str, channel: str | None = None, **kwargs) -> dict:
    """Return a structured contract for actions that the campaign-audit and
    launch-campaign skills depend on but whose full implementation is staged
    over multiple releases. The orchestrator gets a clean response it can
    surface to the user as 'these are the steps that need to run; here's what
    each one would do; here is the manual fallback'.

    This is intentionally NOT a silent stub — every response includes a
    `status: stub_implementation` field so the orchestrator and the user
    always know which actions are scaffolded vs fully wired."""
    schemas = {
        "inventory": {
            "purpose": "List active campaigns / ad groups / keywords / audiences / creatives for the channel, with daily budget and last-modified date.",
            "data_source": "Channel API (Google Ads / Meta Ads / LinkedIn / etc.) via the brand's configured connector.",
            "manual_fallback": "Open the channel's native UI and export the active-campaigns list. Save to ~/.claude-marketing/{brand}/audits/{channel}-inventory.json.",
            "fields_returned_when_implemented": ["campaign_id", "campaign_name", "status", "daily_budget", "last_modified", "spend_30d", "conversions_30d"],
        },
        "automations": {
            "purpose": "List active automations / journeys for the channel (e.g. Klaviyo flows, HubSpot workflows) with last-execution and per-step health.",
            "data_source": "Email/CRM platform API via the brand's configured connector.",
            "manual_fallback": "Open the email/CRM platform, list active automations, export to JSON.",
            "fields_returned_when_implemented": ["automation_id", "name", "trigger", "last_execution", "active_subscribers", "deliverability_30d"],
        },
        "cadence": {
            "purpose": "Report posting cadence per platform over the last 90 days (post count, engagement rate, follower trend).",
            "data_source": "Organic social platform APIs (Meta Graph / LinkedIn API / Twitter API) via the brand's configured connectors.",
            "manual_fallback": "Pull from each platform's native analytics. Use Buffer / Hootsuite if scheduling-tool tracking is in place.",
            "fields_returned_when_implemented": ["platform", "post_count_90d", "engagement_rate", "follower_trend"],
        },
        "diagnostic": {
            "purpose": "Diagnose tag-firing health, conversion tracking, consent-mode state, event-naming consistency on the configured GA4/GSC property.",
            "data_source": "GA4 Admin API + Real Time API + GSC API.",
            "manual_fallback": "Open GA4 DebugView and walk a test session; check Tag Assistant; verify GSC ownership.",
            "fields_returned_when_implemented": ["ga4_property_id", "events_firing_24h", "conversion_events_configured", "consent_mode_state", "gsc_property_ownership"],
        },
        "arm-watchdog": {
            "purpose": "Activate a day-1 monitoring watchdog on a launched campaign — track CPC, conversion volume, deliverability, error rates against the campaign's stated KPI targets and alert on deviation > N%.",
            "data_source": "All channel APIs in the campaign plan.",
            "manual_fallback": "Set up dashboards in GA4 + Looker Studio + the channel native UIs, schedule a 24-hour manual review.",
            "fields_returned_when_implemented": ["watchdog_id", "campaign_id", "kpis_monitored", "alert_thresholds", "next_check_at"],
        },
    }
    if action not in schemas:
        return {"error": f"unknown stub action: {action}"}
    base = {
        "status": "stub_implementation",
        "action": action,
        "brand": brand,
        "channel": channel,
        "version": "3.7.6",
        "note": "This action is part of the campaign-audit / launch-campaign skill surface added in v3.7.5. The action contract is stable; the live implementation is staged across releases. Use the manual_fallback for now or wire the connector listed in data_source.",
        **schemas[action],
    }
    if kwargs:
        base["called_with"] = kwargs
    return base


def main():
    parser = argparse.ArgumentParser(description="Performance monitoring for Digital Marketing Pro")
    parser.add_argument("--brand", required=True, help="Brand slug")
    parser.add_argument("--action", required=True,
                        choices=["pull-metrics", "save-snapshot", "detect-anomalies",
                                 "get-baseline",
                                 # v3.7.6 — campaign-audit / launch-campaign skill surface
                                 "inventory", "automations", "cadence", "diagnostic",
                                 "arm-watchdog"],
                        help="Action to perform")
    parser.add_argument("--data", help="JSON data (metrics object)")
    parser.add_argument("--channel", help="Channel name (for inventory/automations/cadence/diagnostic): "
                                          "google_ads / meta_ads / linkedin_ads / tiktok_ads / email / "
                                          "organic_social / seo / ga4_health / etc.")
    parser.add_argument("--campaign-id", help="Campaign id (for arm-watchdog)")
    parser.add_argument("--kpis", help="Comma-separated KPI list (for arm-watchdog)")
    parser.add_argument("--read-only", action="store_true",
                        help="Inventory / inspection actions are read-only by default; this flag is documentation.")
    args = parser.parse_args()

    if args.action == "pull-metrics":
        if not args.data:
            print(json.dumps({"error": "Provide --data with metrics JSON"}))
            sys.exit(1)
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid JSON in --data"}))
            sys.exit(1)
        result = pull_metrics(args.brand, data)

    elif args.action == "save-snapshot":
        if not args.data:
            print(json.dumps({"error": "Provide --data with metrics JSON"}))
            sys.exit(1)
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid JSON in --data"}))
            sys.exit(1)
        result = save_snapshot(args.brand, data)

    elif args.action == "detect-anomalies":
        if not args.data:
            print(json.dumps({"error": "Provide --data with current metrics JSON"}))
            sys.exit(1)
        try:
            data = json.loads(args.data)
        except json.JSONDecodeError:
            print(json.dumps({"error": "Invalid JSON in --data"}))
            sys.exit(1)
        result = detect_anomalies(args.brand, data)

    elif args.action == "get-baseline":
        result = get_baseline(args.brand)

    elif args.action in {"inventory", "automations", "cadence", "diagnostic", "arm-watchdog"}:
        extra = {}
        if args.campaign_id:
            extra["campaign_id"] = args.campaign_id
        if args.kpis:
            extra["kpis"] = [k.strip() for k in args.kpis.split(",") if k.strip()]
        result = _stub_action(args.action, args.brand, channel=args.channel, **extra)

    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
