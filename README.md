# Grafana Enterprise demo stack

Local **Docker Compose** environment for **customer-facing demos**: self-managed **Grafana Enterprise** with live **metrics, logs, and traces** (via [TNS](https://github.com/grafana/tns)), plus **OpenSearch** for a “remote search / logs platform” story, and optional wiring for **Grafana Assistant** (hybrid with Grafana Cloud).

This is meant to feel like a small **customer Grafana Enterprise** footprint: real datasources, real traffic, and a credible mix of **observability-native** and **OpenSearch** data—without standing up a full production LGTM platform by hand.

---

## What’s included

| Layer | Role |
|--------|------|
| **Grafana Enterprise** | Main UI on port **3000**; plugins **Grafana Assistant**, **OpenSearch**, and **Synthetic Monitoring** pre-installed via `GF_INSTALL_PLUGINS`. |
| **TNS** (`app`, `db`, `loadgen`) | Demo app generating **Prometheus** metrics, **Tempo** traces (Jaeger HTTP), and HTTP traffic. |
| **Prometheus** | Scrapes TNS and monitoring targets (**9090**). |
| **Loki** | Log store (**3100**). |
| **Promtail** | Ships Docker container logs to Loki (no host **Loki Docker logging** plugin required). |
| **Tempo** | Trace backend; query API published on host **8004** → container **3200**. |
| **OpenSearch + Dashboards** | Search engine (**9200**) and UI to load **sample datasets** (**5601**). |
| **cAdvisor / node_exporter** | Extra metrics for a “fuller” Prometheus experience. |

Datasources for the **local** stack are provisioned from `config/provisioning/datasources/local-stack.yaml`. Optional **Grafana Cloud** datasources for Synthetic Monitoring are described in `config/provisioning/README.md`.

---

## Prerequisites

- **Docker** + **Docker Compose** (Docker Desktop is fine).
- **Network** on first `docker compose build` for TNS (clone + compile from GitHub).
- **RAM**: OpenSearch is set to ~1 GiB heap; **4 GiB+** Docker memory is comfortable.

**Apple Silicon:** TNS services use `platform: linux/amd64` (emulation). Expect a short first-time **Go build** when building the custom TNS images.

---

## Quick start

```bash
git clone <this-repo> && cd grafana-enterprise-demo

# First run (or after changing docker/tns-trace-names.Dockerfile): build TNS images
docker compose build db app loadgen

docker compose up -d
```

Open **http://localhost:3000** (default admin user/password are set in `docker-compose.yml`; change after first login).

### Useful URLs

| URL | Service |
|-----|---------|
| http://localhost:3000 | Grafana Enterprise |
| http://localhost:9090 | Prometheus |
| http://localhost:3100 | Loki API |
| http://localhost:8004 | Tempo query HTTP (maps to 3200 in container) |
| http://localhost:9200 | OpenSearch HTTP |
| http://localhost:5601 | OpenSearch Dashboards (sample data) |
| http://localhost:8000–8002 | TNS db / app / loadgen (optional direct pokes) |

---

## Grafana Assistant (optional)

Grafana Assistant in **self-managed** Grafana still uses a **Grafana Cloud** stack for the **Assistant backend** (models, limits, billing). Your **data** stays in this compose stack; prompts/query context go to Cloud per product docs.

1. Enable Assistant on your **Grafana Cloud** stack.
2. In this Grafana instance: **Administration → Plugins → Grafana Assistant → Connection** and complete **Connect to Grafana Cloud** (or manual config).

Official references:

- [Grafana Assistant (admin)](https://grafana.com/docs/grafana/latest/administration/assistant/)
- [Assistant on self-managed Grafana](https://grafana.com/docs/grafana-cloud/machine-learning/assistant/on-premise/)

---

## Grafana Cloud Synthetic Monitoring app (optional)

The **[Synthetic Monitoring](https://grafana.com/grafana/plugins/grafana-synthetic-monitoring-app/)** plugin is installed via `GF_INSTALL_PLUGINS` and kept **enabled** via `GF_PLUGIN_GRAFANA_SYNTHETIC_MONITORING_APP_ENABLED` in `docker-compose.yml` (equivalent to `grafana.ini` `[plugin.grafana-synthetic-monitoring-app] enabled = true`). The app **will not talk to Grafana Cloud** until you add **provisioning**: Grafana Cloud **Prometheus** + **Loki** datasources and an **app** config (`apiHost`, `stackId`, `hostedId`, `publisherToken` — the same values you would enter under **“Already have an account? Connect”** in the SM UI). Without that, you see **“Provisioning missing or invalid”**.

**Do this:** follow **[config/provisioning/README.md](config/provisioning/README.md)** (copy the two `.example` files, fill in values from your Cloud stack, restart Grafana).

Short official overview: [Set up Synthetic Monitoring in a local Grafana instance](https://grafana.com/docs/grafana-cloud/testing/synthetic-monitoring/set-up/grafana-oss-enterprise/).

Licensing and entitlements follow your Grafana contract; see the [plugin page](https://grafana.com/grafana/plugins/grafana-synthetic-monitoring-app/) if install or enable is blocked.
---

## OpenSearch sample data

1. Open **http://localhost:5601**.
2. Use **Add sample data** (e.g. flights, e-commerce, web logs).
3. In Grafana, the provisioned OpenSearch datasource uses index pattern `opensearch_dashboards_sample_data*` (see `config/provisioning/datasources/local-stack.yaml`). Adjust in **Connections → Data sources** if your indices differ.

**Dashboards security plugin:** Compose sets **`DISABLE_SECURITY_DASHBOARDS_PLUGIN`** (note **DASHBOARDS** plural). A typo there leaves a login screen even when the OpenSearch API is open on `:9200`.

---

## Persistence

Grafana stores dashboards, users, and plugin state under the **`grafana-storage`** named volume.

- **`docker compose down`** — data **kept**.
- **`docker compose down -v`** — volumes **removed**; Grafana dashboards and OpenSearch data are **lost** unless you back them up or export.

---

## Verifying Grafana Enterprise

The stack uses image **`grafana/grafana-enterprise`**. In the UI, check **Help → About** and **Administration → Enterprise license**. A valid **license** is separate from “Enterprise image”: apply your license in the UI for full entitlement demos.

---

## Project layout

```
├── docker-compose.yml
├── docker/
│   └── tns-trace-names.Dockerfile
├── config/
│   ├── provisioning/
│   │   ├── README.md                 # Synthetic Monitoring + Cloud datasource setup
│   │   ├── datasources/
│   │   │   ├── local-stack.yaml    # Local Prometheus / Loki / Tempo / OpenSearch
│   │   │   └── *.example           # Copy → grafana-cloud-sm.yaml (gitignored)
│   │   └── plugins/
│   │       └── *.example           # Copy → synthetic-monitoring.yaml (gitignored)
│   ├── prometheus.yaml
│   ├── tempo.yaml
│   └── promtail.yaml
└── .gitignore
```

---

## Design notes (for presenters)

- **“Local data” story:** TNS + OpenSearch run beside Grafana; good for demos that should not depend on Grafana Cloud for **metrics/logs/traces/search**.
- **Tempo datasource URL** uses **`http://host.docker.internal:8004`** so Traces Drilldown / metrics calls work reliably on Docker Desktop (see comments in `docker-compose.yml`).
- **TNS trace service names** are patched to **`tns-app`**, **`tns-db`**, **`tns-loadgen`** in the custom Dockerfile (upstream loadgen used **`lb`** by design).

---

## Disclaimer

Defaults (passwords, OpenSearch security disabled, etc.) are for **local demos only**. Do not expose this compose stack to the internet as-is.
