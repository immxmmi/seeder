# Seeder Overview

Seeder pulls data from external REST APIs, maps it into provisioner input structures, and writes an `inputs.yaml`. It is
designed for periodic execution (e.g. CronJob). Each run only rewrites the output if changes are detected.

## Runtime Flow

- Load `src/config/settings.yaml`.
- Build connector list from `connectors`.
- For each enabled connector, `GET` data from the configured endpoint.
- Normalize response to a list.
- Apply mapping + defaults.
- `YamlWriter` diffs and writes the output file if needed.

## Connector Structure

Each connector has:

- `connection`: host, auth type, env var for token, endpoint
- `mapping`: `replace_object` + list of `{from, to}`
- `defaults`: static values merged into each item

`mapping.replace_object` is used as the output section name in `inputs.yaml` (e.g. `notifiers`, `integrations`).

## Output

The output path is configured via:

- `output.file` in `settings.yaml`, or
- `OUTPUT_FILE` environment variable

Example config: `src/config/settings.example.yaml`

## Key Modules

- `src/main.py`: orchestration
- `src/config/loader.py`: config parsing + validation
- `src/gateway/client.py`: HTTP client (auth + TLS)
- `src/collectors/generic_collector.py`: GET + mapping + defaults
- `src/output/yaml_writer.py`: diff + write

## Notes

- Current implementation only performs HTTP `GET` requests.
- Auth types supported: `bearer`, `basic`, `apikey`.
- When `DEBUG_ENABLED=true`, Seeder prints connector details, mapping fields, and request/response metadata.
