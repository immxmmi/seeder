# Seeder

Seeder pulls data from external REST APIs, maps fields into the provisioner input format, and writes an `inputs.yaml`.
On each run it diffs against the existing output and only rewrites the file when changes are detected.

## How It Works

- Load global settings and connector definitions from `src/config/settings.yaml`.
- For each enabled connector, perform an HTTP `GET` against the configured endpoint.
- Normalize the response into a list.
- Apply mapping + defaults.
- Write output via `YamlWriter` with diff detection.

## Configuration

All connector definitions live in `src/config/settings.yaml` under `connectors`.
An ACS example file is provided at `src/config/settings.example.yaml`.
An APIs.guru mapping walkthrough is provided at `_docs/mapping_example_apis_guru.md`.

```yaml
output:
  file: "../acs-provisioner/src/pipelines/inputs.yaml"

debug:
  enabled: false

app:
  version: "1.0.0"

connectors:
  - name: "cmdb-notifiers"
    enabled: true
    connection:
      host: "https://cmdb.example.com"
      auth_type: "bearer"   # bearer | basic | apikey
      token_env: "CMDB_TOKEN"
      endpoint: "/api/v1/notifiers"

    mapping:
      replace_object: "notifiers"
      fields:
        - from: "title"
          to: "name"
        - from: "notification_type"
          to: "type"
        - from: "ui_endpoint"
          to: "uiEndpoint"
        - from: "config"
          to: "jira"

    defaults:
      traits:
        mutabilityMode: "ALLOW_MUTATE"
        visibility: "VISIBLE"
        origin: "IMPERATIVE"
```

Notes:

- `mapping.replace_object` is used as the output section name (e.g. `notifiers`).
- If `target_key` is set and differs from `replace_object`, Seeder warns in logs.
- If neither `target_key` nor `mapping.replace_object` is set, Seeder fails fast.

## Environment Variables

- `OUTPUT_FILE`: override output path from `output.file`
- `DEBUG_ENABLED`: enable debug logging (`true`/`false`)
- `API_TIMEOUT`: request timeout in seconds
- `DISABLE_TLS_VERIFY`: disable TLS verification
- `CA_BUNDLE`: path to custom CA bundle

## Run

```bash
make install
make run
```

## Tests

```bash
make test
```

Optional live HTTP test:

```bash
make test-integration
```

## Project Structure

```
seeder/
├── _docs/
│   └── overview.md
├── src/
│   ├── main.py
│   ├── config/
│   │   ├── loader.py
│   │   └── settings.yaml
│   ├── collectors/
│   │   ├── base_collector.py
│   │   └── generic_collector.py
│   ├── gateway/
│   │   └── client.py
│   ├── output/
│   │   └── yaml_writer.py
│   └── utils/
│       ├── display.py
│       └── logger.py
└── tests/
    ├── test_transform.py
    ├── test_diff.py
    └── test_config_loader.py
```
