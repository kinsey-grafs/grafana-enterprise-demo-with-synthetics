# Grafana provisioning (datasources + apps)

## Local demo stack

`datasources/local-stack.yaml` provisions Prometheus, Loki, Tempo, and OpenSearch for the Docker Compose services.

## Grafana Cloud Synthetic Monitoring (optional)

The Synthetic Monitoring **app** does not work with only `GF_INSTALL_PLUGINS`. This demo also sets **`GF_PLUGIN_GRAFANA_SYNTHETIC_MONITORING_APP_ENABLED=true`** in `docker-compose.yml`, matching **`[plugin.grafana-synthetic-monitoring-app] enabled = true`** in `grafana.ini` (see Grafana docs on overriding config with environment variables).

You must still add **two** Cloud datasources and **one** app provisioning file, then restart Grafana. That file-based config is the same information the SM UI asks for when you use **“Already have an account? Connect”**: **SM API base URL** → `jsonData.apiHost`, **access token** → `secureJsonData.publisherToken` (Grafana Cloud access policy with the scopes below), plus `stackId` / `hostedId` alignment with your Cloud Prometheus and Loki users.

### Cloud Access Policy scopes

Create a [Cloud Access Policy](https://grafana.com/docs/grafana-cloud/security-and-account-management/authentication-and-permissions/access-policies/) scoped to your stack (realm type **stack**, identifier = your stack ID from **grafana.com → Stacks → Details**). Use the same region as the stack (e.g. `prod-us-west-0`).

Use **one** access policy token for both `publisherToken` and datasource `basicAuthPassword` (simplest for demos).

| Scope | Read | Write | Used for |
|--------|:----:|:-----:|----------|
| **stacks** | ✓ | — | **Get started** / install (looks up your Cloud stack via the [Grafana Cloud API](https://grafana.com/docs/grafana/latest/developer-resources/api-reference/cloud-api/)). Not used by Explore. |
| **metrics** | ✓ | ✓ | Cloud Prometheus datasource; probe metrics from SM |
| **logs** | ✓ | ✓ | Cloud Loki datasource; check logs from SM |
| **traces** | — | ✓ | SM publisher / install validation ([CONTRIBUTING](https://github.com/grafana/synthetic-monitoring-app/blob/main/CONTRIBUTING.md)) |

**Minimum for Synthetic Monitoring install:** `stacks:read`, `metrics:write`, `logs:write`, `traces:write`.

**Minimum for Cloud datasources in Explore:** `metrics:read`, `logs:read` on the same stack.

A policy with only read on metrics/logs can make **Explore work** while **Get started** still fails (e.g. `cannot get information for grafana instance with ID …` or `Something went wrong`). Add the scopes above, then **create a new token** — existing tokens do not pick up scope changes.

### 1. Copy templates (filenames without `.example` are loaded by Grafana)

Run these from **this demo’s repository root** — the directory that contains **`docker-compose.yml`** (for example `.../grafana-enterprise-demo`), not a parent monorepo folder.

If `git rev-parse --show-toplevel` points at a parent repo (e.g. `~/repos`), `cd` there first, then into this project: `cd grafana-enterprise-demo` (adjust the folder name if yours differs).

```bash
cd /path/to/grafana-enterprise-demo

cp config/provisioning/datasources/grafana-cloud-sm.yaml.example \
   config/provisioning/datasources/grafana-cloud-sm.yaml

cp config/provisioning/plugins/synthetic-monitoring.yaml.example \
   config/provisioning/plugins/synthetic-monitoring.yaml
```

Quick check: `test -f config/provisioning/datasources/grafana-cloud-sm.yaml.example && echo OK` — if that prints nothing, you are in the wrong directory.

`grafana-cloud-sm.yaml` and `synthetic-monitoring.yaml` are **gitignored** so you do not commit Cloud tokens.

### 2. Edit `grafana-cloud-sm.yaml`

From your Grafana Cloud stack (**Connections** for Hosted Prometheus and Loki):

- Set each **`url`** to your region’s Prometheus / Loki endpoints.
- For **Hosted Prometheus**, use the **query** base URL ending in **`/api/prom`**. Do **not** use the remote-write URL (`/api/prom/push`) — Grafana queries that datasource; the wrong path often surfaces in the Synthetic Monitoring UI as **“failed to read incoming data”** or similar.
- Set **`basicAuthUser`** to the **user / instance id** shown in the portal (often numeric).
- Set **`basicAuthPassword`** to the access policy token (see **Cloud Access Policy scopes** above; needs `metrics:read` and `logs:read`).

The **`name`** fields must stay exactly:

- `Grafana Cloud Logs (SM)`
- `Grafana Cloud Prometheus (SM)`

unless you change the same strings under `jsonData.logs.grafanaName` / `metrics.grafanaName` in the plugin file.

### 3. Edit `synthetic-monitoring.yaml`

- **`apiHost`**: HTTPS base URL for your stack’s Synthetic Monitoring API region. See [Probe API server URL](https://grafana.com/docs/grafana-cloud/testing/synthetic-monitoring/set-up/set-up-private-probes/#probe-api-server-url). Many US/GCP stacks use `https://synthetic-monitoring-api.grafana.net`.
- **`stackId`**: Integer stack ID from [Grafana Cloud stacks](https://grafana.com/) (stack details / URL).
- **`hostedId`**: Must match **`basicAuthUser`** for the Loki and Prometheus entries above (same values as in the portal).
- **`publisherToken`**: Same access policy token as the datasources (see **Cloud Access Policy scopes** above).

### 4. Restart Grafana

```bash
docker compose up -d --force-recreate grafana
```

Then open **Testing & synthetics → Synthetic Monitoring**.

**“Get started” / initialization:** The button calls **`POST .../install`**, which runs a **one-time** Synthetic Monitoring setup on your **Grafana Cloud** stack (validate publisher token, confirm hosted Prometheus/Loki, import bundled dashboards). If Synthetic Monitoring was **already initialized** for that stack (typical if you ever used SM in **hosted** Grafana on the same stack), this call often returns **400** and the UI may show **“failed to read incoming data”** instead of a clear message. That is **not** a problem for reading existing metrics in Explore/Drilldown — you can **skip Get started** and open **Checks** (`/a/grafana-synthetic-monitoring-app/checks`) or **Endpoints** from the Synthetic Monitoring nav. To see the real error, use the browser **Network** tab on the **`install`** request and read the JSON response body.

If you are on a **brand-new** stack that has never run SM before and **`install`** still returns 400, confirm **`apiHost`** matches your region, access policy scopes match the table above (mint a **new** token after any scope change), and both Cloud datasources **Save & test** successfully in Grafana.

Official guide: [Set up Synthetic Monitoring in a local Grafana instance](https://grafana.com/docs/grafana-cloud/testing/synthetic-monitoring/set-up/grafana-oss-enterprise/).

## Provisioned dashboards

`dashboards/default.yaml` loads JSON dashboards from this folder into Grafana folder **Demo**.

| Dashboard | UID | Notes |
|-----------|-----|--------|
| **OpenSearch Overview** | `opensearch-overview` | V2 dynamic dashboard with tabs: **Flights**, **Ecommerce**, **Web Logs**. URL: `/d/opensearch-overview/opensearch-overview` |
| OpenSearch Web Logs Overview | `opensearch-logs-overview` | Classic schema; same Web Logs tab content (standalone) |

**OpenSearch Overview** requires all three sample datasets in OpenSearch Dashboards (**http://localhost:5601** → **Add sample data**): flights, e-commerce, and web logs. Default time range is **Last 90 days**.

To regenerate the combined dashboard after editing a source tab:

```bash
python3 scripts/build-opensearch-overview.py
```

Sources: `config/dashboard-sources/flights.json`, `ecommerce.json` (not under `provisioning/dashboards/` — avoids duplicate import). Web Logs tab is converted from `opensearch-logs-overview.json`.

**V2 provisioning:** `opensearch-overview.json` uses the Kubernetes envelope (`apiVersion: dashboard.grafana.app/v2`). Plain V2 spec-only JSON is rejected by the file provisioner.

Assistant copy-paste prompt (logs only): [`docs/grafana-assistant-opensearch-logs-dashboard.md`](../../docs/grafana-assistant-opensearch-logs-dashboard.md).
