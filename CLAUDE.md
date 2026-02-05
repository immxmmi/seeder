# Seeder - Projektnotizen

## Architektur-Überblick

Eigenständiges Projekt das Daten von externen APIs (Jira, Kubernetes, REST-Dienste) abholt,
per Mapping ins Provisioner-Format transformiert und als `inputs.yaml` schreibt.
Läuft als CronJob, erkennt Änderungen per Diff und schreibt nur bei Abweichungen.

## Datenfluss

```
settings.yaml (API-Quellen + Mapping konfiguriert)
       ↓
GenericCollector.collect()  →  Ruft externe API ab
       ↓
Rohdaten (List[dict])
       ↓
_transform()  →  Mapping (API-Felder → Output-Felder) + Defaults
       ↓
YamlWriter.diff()  →  Vergleich mit bestehender inputs.yaml
       ↓
Änderungen?  →  Nein: nichts tun  /  Ja: inputs.yaml schreiben
```

## Wichtige Dateien

| Komponente        | Pfad                                                                 |
|-------------------|----------------------------------------------------------------------|
| Entry Point       | `src/main.py`                                                        |
| Config Loader     | `src/config/loader.py` (Singleton, env > settings.yaml)              |
| Settings          | `src/config/settings.yaml`                                           |
| HTTP Client       | `src/gateway/client.py` (Session, Auth, TLS)                         |
| Base Collector    | `src/collectors/base_collector.py` (abstrakte Klasse)                |
| Generic Collector | `src/collectors/generic_collector.py` (REST API Collector + Mapping) |
| Notifier Model    | `src/models/notifier_input.py` (Pydantic)                            |
| Integration Model | `src/models/integration_input.py` (Pydantic)                         |
| YAML Writer       | `src/output/yaml_writer.py` (Diff-Erkennung + Schreiben)             |
| Logger            | `src/utils/logger.py`                                                |

## Source-Konfiguration (settings.yaml)

Jede Source definiert:

- `name`: Eindeutiger Name
- `host`: Basis-URL der API
- `auth_type`: bearer/basic/apikey
- `token_env`: Name der Umgebungsvariable mit dem Token
- `endpoint`: API-Pfad
- `target_key`: Schlüssel in der output inputs.yaml
- `mapping`: Feld-Mapping (API-Feldname → Output-Feldname), wirkt als Whitelist
- `defaults`: Statische Werte die jedem Item hinzugefügt werden

Umgebungsvariablen überschreiben settings.yaml-Werte.

## Mapping

Wenn `mapping` definiert ist, landen nur gemappte Felder im Output (Whitelist-Prinzip):

```yaml
mapping:
  title: "name"              # API "title" → Output "name"
  notification_type: "type"  # API "notification_type" → Output "type"
```

Ohne `mapping` werden alle API-Felder 1:1 durchgereicht.

`defaults` fügt statische Werte hinzu (werden nicht überschrieben wenn API sie liefert):

```yaml
defaults:
  traits:
    mutabilityMode: "ALLOW_MUTATE"
```

## Diff-Erkennung

YamlWriter vergleicht neue Daten mit bestehender `inputs.yaml`:

- Vergleich pro `target_key`-Section (notifiers, integrations, ...)
- Matching per `name`-Feld
- Erkennt: hinzugefügt (+), entfernt (-), geändert (~) mit betroffenen Feldern
- Keine Änderungen → Datei wird nicht angefasst

## Collector-Architektur

- `BaseCollector`: Abstrakte Basisklasse mit `collect()` Methode
- `GenericCollector`: Konfigurierbar über settings.yaml, ruft beliebige REST APIs ab
- `_transform()`: Wendet Mapping + Defaults auf jedes Item an
- Erweiterbar um `JiraCollector`, `K8sCollector` etc.

## Besonderheiten

- HTTP Client übernommen/angepasst von acs-provisioner
- Config ist Singleton: `Config()` gibt immer dieselbe Instanz zurück
- Jede Source bekommt eigenen ApiClient (verschiedene Hosts/Auth möglich)
- Gedacht als K8s CronJob (nicht event-basiert)
