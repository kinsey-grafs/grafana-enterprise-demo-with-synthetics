# Grafana Assistant prompt: OpenSearch Web Logs dashboard

Copy everything inside the fenced block below into **Grafana Assistant** (or use it in Cursor with the Grafana MCP server). It matches the provisioned dashboard in this repo.

---

## Prompt (copy from here)

```
Create a Grafana dashboard titled "OpenSearch Web Logs Overview" for the **OpenSearch Logs** datasource only.

## Datasource (critical)
- Name: OpenSearch Logs
- UID: opensearch-logs
- Type: grafana-opensearch-datasource
- Index (already on datasource): opensearch_dashboards_sample_data_logs
- Time field: timestamp (NOT @timestamp)

Every panel MUST use datasource uid `opensearch-logs`. Do not use uid `opensearch` (that is the Flights index).

## Time range
- Default dashboard range: Last 90 days (now-90d to now)
- Sample data timestamps span roughly the last few months; if panels are empty, widen to Last 6 months.

## Index fields (use in queries)
| Field | Use |
|-------|-----|
| timestamp | Time field for all panels |
| bytes | number — sum for volume stats |
| clientip | ip — cardinality for unique clients |
| response.keyword | terms agg for HTTP codes (values: 200, 404, 503) |
| host.keyword | terms agg for top hosts |
| geo.dest | keyword — terms agg for top destinations |
| message, request, extension.keyword, tags | logs panel / optional filters |

For terms aggregations on text fields, always use the `.keyword` subfield (e.g. response.keyword, host.keyword).

## Panels (layout)

**Row 1 — Stat panels (4 across)**  
Each stat target needs a `date_histogram` on `timestamp` in `bucketAggs` (OpenSearch plugin rejects metric-only Lucene queries with “invalid query, missing metrics and aggregations”). Use panel reduce **Sum** (or **Last non-null** for cardinality) over the histogram buckets.
1. Total requests — date_histogram + count, query: *
2. Total bytes — date_histogram + sum on field `bytes`, query: *
3. Unique client IPs — date_histogram + cardinality on `clientip`, query: *
4. Non-200 responses — date_histogram + count, Lucene query: `NOT response.keyword:200`

**Row 2 — Time series (2 panels)**
5. Requests over time — date_histogram on `timestamp` + count
6. Bytes over time — date_histogram on `timestamp` + sum(bytes)

**Row 3 — Breakdowns (3 panels)**
7. HTTP response codes — pie/donut, terms on `response.keyword`, metric count, `format: table`, `reduceOptions.values: true` (so each status code is a slice, not one total)
8. Top hosts — horizontal bar chart, terms on `host.keyword`, size 10
9. Top destinations — horizontal bar chart, terms on `geo.dest`, size 10

**Row 4**
10. Recent log lines — Logs panel, logs metric, limit 500, order by timestamp desc

## Query format
- queryType: lucene
- timeField: timestamp on each target
- Do NOT apply currencyUSD or money units to HTTP codes or host names.

## Tags
demo, opensearch, logs

## Dashboard UID
opensearch-logs-overview
```

---

## Already provisioned in this demo

If you run `docker compose up` with the dashboard volume mounted, Grafana loads:

- **Folder:** Demo  
- **Dashboard:** [OpenSearch Web Logs Overview](http://localhost:3000/d/opensearch-logs-overview) (`uid: opensearch-logs-overview`)

Files:

- `config/provisioning/dashboards/opensearch-logs-overview.json`
- `config/provisioning/dashboards/default.yaml`

Restart Grafana after adding the mount:

```bash
docker compose restart grafana
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| All panels empty | Set time range to **Last 90 days** or **Last 6 months** |
| Wrong index / no data | Confirm panel datasource is **OpenSearch Logs** (`opensearch-logs`) |
| Pie/bar shows one blob | Use `.keyword` fields for terms aggs |
| Stats show $ on codes | Remove `currencyUSD` from default field config |
