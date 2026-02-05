import os
import sys
from datetime import datetime

src_dir = os.path.dirname(os.path.abspath(__file__))
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from config.loader import Config
from collectors.generic_collector import GenericCollector
from output.yaml_writer import YamlWriter
from utils.display import Display, SeederStats, ConnectorResult
from utils.logger import Logger as log


def main():
    config = Config()

    Display.banner(config.version, config.debug)

    start_ts = datetime.now()

    enabled_connectors = [s for s in config.sources if s.enabled]
    disabled_connectors = [s for s in config.sources if not s.enabled]

    Display.connectors_overview(config.sources, debug=config.debug)

    stats = SeederStats(
        total_connectors=len(enabled_connectors),
        skipped_connectors=len(disabled_connectors),
    )

    if not enabled_connectors:
        log.warn("Main", "No enabled connectors configured")
        duration = (datetime.now() - start_ts).total_seconds()
        Display.summary(stats, duration)
        sys.exit(0)

    collected_data = {}

    for i, source in enumerate(enabled_connectors, 1):
        Display.source_start(i, len(enabled_connectors), source.name)

        collector = GenericCollector(source)
        items = collector.collect()

        if items:
            collected_data[source.target_key] = items
            Display.source_result(success=True, items=len(items))
            stats.add_result(ConnectorResult(
                name=source.name, target_key=source.target_key,
                items_collected=len(items), success=True,
            ))
        else:
            Display.source_result(success=False, message=f"No data from {source.name}")
            stats.add_result(ConnectorResult(
                name=source.name, target_key=source.target_key,
                items_collected=0, success=False,
                message=f"No data returned",
            ))

    if collected_data:
        updated = YamlWriter.write(config.output_file, collected_data)
        stats.output_updated = updated
    else:
        log.warn("Main", "No data collected from any source, skipping output")

    duration = (datetime.now() - start_ts).total_seconds()
    Display.summary(stats, duration)

    if stats.failed_connectors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
