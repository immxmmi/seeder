# APIs.guru Mapping Example

Input from `https://api.apis.guru/v2/list.json` is a dictionary where each key is an API id. Seeder normalizes this into
a list by adding `api_id` to each item.

Example input (shortened):

```json
{
  "1forge.com": {"preferred": "0.0.1", "versions": {"0.0.1": {"info": {"title": "1Forge Finance APIs"}}}},
  "1password.com:events": {"preferred": "1.0.0", "versions": {"1.0.0": {"info": {"title": "Events API"}}}}
}
```

After normalization:

```json
[
  {"api_id": "1forge.com", "preferred": "0.0.1", "versions": {"0.0.1": {"info": {"title": "1Forge Finance APIs"}}}},
  {"api_id": "1password.com:events", "preferred": "1.0.0", "versions": {"1.0.0": {"info": {"title": "Events API"}}}}
]
```

Mapping example:

```yaml
connectors:
  - name: "apis-guru"
    enabled: true
    target_key: "apis"
    connection:
      host: "https://api.apis.guru"
      auth_type: "none"
      endpoint: "/v2/list.json"

    mapping:
      replace_object: "apis"
      fields:
        - from: "api_id"
          to: "id"
        - from: "preferred"
          to: "preferred"
        - from: "versions"
          to: "versions"
```

If you want specific nested values (e.g. preferred version info), use dot-paths:

```yaml
      fields:
        - from: "preferred_info.title"
          to: "title"
```

Note: To use `preferred_info.*` fields, you need a pre-step that flattens `versions[preferred].info` into
`preferred_info`.
