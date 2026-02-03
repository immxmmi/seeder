# Seeder

> Saet die Daten, die die Provisioner ernten.

Seeder ist der Daten-Zulieferer fuer die PipelineExecutionPlatform. Er fragt externe Systeme (CMDBs, Jira, Kubernetes, beliebige REST APIs) ab, transformiert die Antworten per konfigurierbarem Mapping und schreibt das Ergebnis als `inputs.yaml` im Format das die Provisioner (`acs-provisioner`, `quay-provisioner`) erwarten.

Seeder ist nicht event-basiert sondern laeuft periodisch (z.B. als K8s CronJob), vergleicht die neuen Daten mit dem aktuellen Stand und schreibt nur bei Aenderungen.

## Wie es funktioniert

```
  Externe APIs (CMDB, Jira, ...)
           |
           v
    +-------------+
    |  Collector   |  Holt Rohdaten per REST
    +-------------+
           |
           v
    +-------------+
    |   Mapping    |  API-Felder → Provisioner-Felder
    +-------------+
           |
           v
    +-------------+
    |    Diff      |  Vergleich mit bestehender inputs.yaml
    +-------------+
           |
      Aenderungen?
      /         \
    Nein        Ja
     |           |
   (skip)    Schreibt inputs.yaml
```

## Quickstart

```bash
# 1. Abhaengigkeiten installieren
pip install -r requirements.txt

# 2. Konfiguration anpassen
cp .env.example .env
# .env editieren: API-Tokens setzen
# src/config/settings.yaml editieren: Sources konfigurieren

# 3. Ausfuehren
cd src
python main.py
```

### Docker

```bash
# Build
docker build -t seeder .

# Run
docker run --env-file .env seeder
```

## Konfiguration

### settings.yaml

Definiert welche APIs abgefragt werden und wie die Daten transformiert werden:

```yaml
sources:
  - name: "jira-notifiers"
    enabled: true
    host: "https://cmdb.example.com"
    auth_type: "bearer"          # bearer | basic | apikey
    token_env: "CMDB_TOKEN"      # Env-Variable mit dem Token
    endpoint: "/api/v1/notifiers"
    target_key: "notifiers"      # Key in der output inputs.yaml

    # Mapping: API-Feldname → Output-Feldname (Whitelist)
    mapping:
      title: "name"
      notification_type: "type"
      ui_endpoint: "uiEndpoint"

    # Statische Werte die jedem Item hinzugefuegt werden
    defaults:
      traits:
        mutabilityMode: "ALLOW_MUTATE"
        visibility: "VISIBLE"
        origin: "IMPERATIVE"

output:
  file: "../acs-provisioner/src/pipelines/inputs.yaml"
```

### Umgebungsvariablen

| Variable | Beschreibung | Default |
|---|---|---|
| `CMDB_TOKEN` | API-Token (Name konfigurierbar via `token_env`) | - |
| `OUTPUT_FILE` | Ueberschreibt den Output-Pfad | aus settings.yaml |
| `DISABLE_TLS_VERIFY` | TLS-Verifikation deaktivieren | `false` |
| `CA_BUNDLE` | Pfad zu eigenem CA-Bundle | - |
| `DEBUG_ENABLED` | Debug-Logging aktivieren | `false` |
| `API_TIMEOUT` | HTTP-Timeout in Sekunden | `30` |

## Mapping

Das Mapping transformiert API-Antworten ins Provisioner-Format:

```yaml
# API liefert:
{"title": "Jira-Security", "notification_type": "jira", "internal_id": "xyz"}

# Mapping:
mapping:
  title: "name"
  notification_type: "type"

# Output:
{"name": "Jira-Security", "type": "jira"}
# "internal_id" faellt weg (nicht im Mapping → Whitelist)
```

Ohne `mapping` werden alle Felder 1:1 durchgereicht.

`defaults` fuegt statische Werte hinzu die nicht von der API kommen:

```yaml
defaults:
  traits:
    mutabilityMode: "ALLOW_MUTATE"

# Ergebnis: {"name": "Jira-Security", "type": "jira", "traits": {"mutabilityMode": "ALLOW_MUTATE"}}
```

## Diff-Erkennung

Beim Schreiben vergleicht Seeder die neuen Daten mit der bestehenden `inputs.yaml`:

```
  + [notifiers] added: Splunk-SIEM           Neues Item
  - [notifiers] removed: Old-Notifier        Item entfernt
  ~ [notifiers] changed: Jira-Security (url) Feld geaendert
```

- Keine Aenderungen → Datei wird nicht angefasst
- Aenderungen → Diff wird geloggt, Datei wird ueberschrieben

## Projektstruktur

```
seeder/
├── CLAUDE.md
├── README.md
├── Dockerfile
├── Makefile
├── requirements.txt
├── .env.example
├── tests/
│   ├── test_transform.py          # Mapping-Tests
│   └── test_diff.py               # Diff-Tests
└── src/
    ├── main.py                        # Entry Point
    ├── config/
    │   ├── loader.py                  # Config Singleton
    │   └── settings.yaml              # Source-Definitionen + Mapping
    ├── gateway/
    │   └── client.py                  # HTTP Client (Bearer/Basic/APIKey, TLS)
    ├── collectors/
    │   ├── base_collector.py          # Abstrakte Basisklasse
    │   └── generic_collector.py       # REST API Collector + Mapping
    ├── models/
    │   ├── notifier_input.py          # Pydantic Model (Notifier)
    │   └── integration_input.py       # Pydantic Model (Integration)
    ├── output/
    │   └── yaml_writer.py             # YAML-Ausgabe mit Diff-Erkennung
    └── utils/
        └── logger.py                  # Farbiger Logger
```

## Tests

```bash
make install        # Abhaengigkeiten + pytest
make test           # Alle Tests
make test-mapping   # Nur Mapping-Tests
make test-diff      # Nur Diff-Tests
```

## Erweiterung

Neue Collector-Typen koennen einfach hinzugefuegt werden:

```python
from collectors.base_collector import BaseCollector

class JiraCollector(BaseCollector):
    def collect(self):
        # Jira-spezifische Logik
        ...
```

Der `GenericCollector` deckt bereits alle REST APIs ab die JSON zurueckliefern.
# seeder
