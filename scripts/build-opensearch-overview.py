#!/usr/bin/env python3
"""Build OpenSearch Overview V2 dashboard from flights, ecommerce, and classic logs JSON."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOGS_CLASSIC = ROOT / "config/provisioning/dashboards/opensearch-logs-overview.json"
OUT = ROOT / "config/provisioning/dashboards/opensearch-overview.json"

GRAFANA_VERSION = "13.0.1+security-01"

ANNOTATION = {
    "kind": "AnnotationQuery",
    "spec": {
        "builtIn": True,
        "enable": True,
        "hide": True,
        "iconColor": "rgba(0, 211, 255, 1)",
        "name": "Annotations & Alerts",
        "query": {
            "datasource": {"name": "-- Grafana --"},
            "group": "grafana",
            "kind": "DataQuery",
            "spec": {},
            "version": "v0",
        },
    },
}


def lucene_query_type(target: dict) -> str:
    metrics = target.get("metrics") or []
    if metrics and metrics[0].get("type") == "logs":
        return "Logs"
    return "Metric"


def classic_panel_to_v2(panel: dict, element_name: str, ds_name: str, index: str) -> dict:
    target = panel["targets"][0]
    query_spec = {
        "bucketAggs": target.get("bucketAggs", []),
        "index": index,
        "luceneQueryType": lucene_query_type(target),
        "metrics": target.get("metrics", []),
        "query": target.get("query", "*"),
        "queryType": target.get("queryType", "lucene"),
        "range": True,
        "timeField": target.get("timeField", "timestamp"),
    }
    if target.get("format"):
        query_spec["format"] = target["format"]
    if target.get("alias"):
        query_spec["alias"] = target["alias"]

    transformations = []
    viz_group = panel["type"]
    if viz_group == "piechart":
        viz_group = "piechart"

    element = {
        "kind": "Panel",
        "spec": {
            "data": {
                "kind": "QueryGroup",
                "spec": {
                    "queries": [
                        {
                            "kind": "PanelQuery",
                            "spec": {
                                "hidden": False,
                                "query": {
                                    "datasource": {"name": ds_name},
                                    "group": "grafana-opensearch-datasource",
                                    "kind": "DataQuery",
                                    "spec": query_spec,
                                    "version": "v0",
                                },
                                "refId": target.get("refId", "A"),
                            },
                        }
                    ],
                    "queryOptions": {},
                    "transformations": transformations,
                },
            },
            "description": panel.get("description", ""),
            "id": panel["id"],
            "links": [],
            "title": panel["title"],
            "vizConfig": {
                "group": viz_group,
                "kind": "VizConfig",
                "spec": {
                    "fieldConfig": panel.get("fieldConfig", {"defaults": {}, "overrides": []}),
                    "options": panel.get("options", {}),
                },
                "version": GRAFANA_VERSION,
            },
        },
    }
    return element_name, element


def grid_item(name: str, x: int, y: int, w: int, h: int) -> dict:
    return {
        "kind": "GridLayoutItem",
        "spec": {
            "element": {"kind": "ElementReference", "name": name},
            "height": h,
            "width": w,
            "x": x,
            "y": y,
        },
    }


def auto_item(name: str) -> dict:
    return {
        "kind": "AutoGridLayoutItem",
        "spec": {"element": {"kind": "ElementReference", "name": name}},
    }


def logs_tab_layout() -> dict:
    """Classic logs dashboard -> GridLayout matching original gridPos."""
    classic = json.loads(LOGS_CLASSIC.read_text())
    elements = {}
    items = []
    index = "opensearch_dashboards_sample_data_logs"
    ds = "opensearch-logs"

    for panel in classic["panels"]:
        ename = f"logs-panel-{panel['id']}"
        _, element = classic_panel_to_v2(panel, ename, ds, index)
        elements[ename] = element
        gp = panel["gridPos"]
        items.append(grid_item(ename, gp["x"], gp["y"], gp["w"], gp["h"]))

    return {
        "kind": "GridLayout",
        "spec": {"items": items},
    }, elements


def main() -> None:
    flights_path = ROOT / "config/dashboard-sources/flights.json"
    ecommerce_path = ROOT / "config/dashboard-sources/ecommerce.json"

    if not flights_path.exists():
        raise SystemExit(
            "Missing source dashboards. Run script after sources are written."
        )

    flights = json.loads(flights_path.read_text())
    ecommerce = json.loads(ecommerce_path.read_text())

    elements = {}
    elements.update(flights["elements"])
    elements.update(ecommerce["elements"])

    logs_layout, logs_elements = logs_tab_layout()
    elements.update(logs_elements)

    combined = {
        "annotations": [ANNOTATION],
        "cursorSync": "Off",
        "description": "OpenSearch sample data: Flights, Ecommerce, and Web Logs in one dashboard.",
        "editable": True,
        "elements": elements,
        "layout": {
            "kind": "TabsLayout",
            "spec": {
                "tabs": [
                    {
                        "kind": "TabsLayoutTab",
                        "spec": {
                            "title": "Flights",
                            "layout": flights["layout"],
                        },
                    },
                    {
                        "kind": "TabsLayoutTab",
                        "spec": {
                            "title": "Ecommerce",
                            "layout": ecommerce["layout"],
                        },
                    },
                    {
                        "kind": "TabsLayoutTab",
                        "spec": {
                            "title": "Web Logs",
                            "layout": logs_layout,
                        },
                    },
                ]
            },
        },
        "links": [],
        "liveNow": False,
        "preload": False,
        "tags": ["demo", "opensearch"],
        "timeSettings": {
            "autoRefresh": "",
            "autoRefreshIntervals": [
                "5s",
                "10s",
                "30s",
                "1m",
                "5m",
                "15m",
                "30m",
                "1h",
                "2h",
                "1d",
            ],
            "fiscalYearStartMonth": 0,
            "from": "now-90d",
            "hideTimepicker": False,
            "timezone": "browser",
            "to": "now",
        },
        "title": "OpenSearch Overview",
        "variables": [],
    }

    # File provisioning in Grafana 13 requires the Kubernetes envelope for V2 dashboards.
    provisioned = {
        "apiVersion": "dashboard.grafana.app/v2",
        "kind": "Dashboard",
        "metadata": {
            "name": "opensearch-overview",
            "namespace": "default",
            "uid": "opensearch-overview",
        },
        "spec": combined,
    }

    OUT.write_text(json.dumps(provisioned, indent=2) + "\n")
    print(f"Wrote {OUT} ({len(elements)} panels, v2 k8s envelope)")


if __name__ == "__main__":
    main()
