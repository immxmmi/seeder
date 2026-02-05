"""Display utilities for seeder console output."""

from dataclasses import dataclass, field
from typing import List, Optional


class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BLACK = "\033[30m"

    BG_GREEN = "\033[42m"
    BG_RED = "\033[41m"
    BG_YELLOW = "\033[43m"


BANNER = r"""
  ____                _
 / ___|  ___  ___  __| | ___ _ __
 \___ \ / _ \/ _ \/ _` |/ _ \ '__|
  ___) |  __/  __/ (_| |  __/ |
 |____/ \___|\___|\__,_|\___|_|
"""


@dataclass
class ConnectorResult:
    """Result of a single connector collection."""
    name: str
    target_key: str
    items_collected: int
    success: bool
    message: Optional[str] = None


@dataclass
class SeederStats:
    """Statistics for a seeder run."""
    total_connectors: int = 0
    successful_connectors: int = 0
    failed_connectors: int = 0
    skipped_connectors: int = 0
    total_items: int = 0
    output_updated: bool = False
    changes: List[str] = field(default_factory=list)
    results: List[ConnectorResult] = field(default_factory=list)

    def add_result(self, result: ConnectorResult):
        self.results.append(result)
        if result.success:
            self.successful_connectors += 1
            self.total_items += result.items_collected
        else:
            self.failed_connectors += 1


class Display:
    """Handles all visual output for seeder."""

    @staticmethod
    def banner(version: str, debug: bool = False):
        print(f"{Colors.CYAN}{BANNER}{Colors.RESET}")
        print(f"{Colors.DIM}{'─' * 50}{Colors.RESET}")
        print(f"  {Colors.BOLD}Version:{Colors.RESET} {version}")
        print(f"  {Colors.BOLD}Debug:{Colors.RESET}   {'enabled' if debug else 'disabled'}")
        print(f"{Colors.DIM}{'─' * 50}{Colors.RESET}")
        print()

    @staticmethod
    def connectors_overview(sources, debug: bool = False):
        """Show loaded connector definitions."""
        enabled = [s for s in sources if s.enabled]
        disabled = [s for s in sources if not s.enabled]

        print(f"  {Colors.MAGENTA}{Colors.BOLD}Connectors{Colors.RESET}")
        print(f"  {Colors.DIM}{'─' * 40}{Colors.RESET}")

        for s in sources:
            if s.enabled:
                status = f"{Colors.GREEN}●{Colors.RESET}"
                name_style = Colors.BOLD
            else:
                status = f"{Colors.DIM}○{Colors.RESET}"
                name_style = Colors.DIM

            print(f"  {status} {name_style}{s.name}{Colors.RESET}")
            print(f"      {Colors.DIM}Host:{Colors.RESET}     {s.host}")
            print(f"      {Colors.DIM}Endpoint:{Colors.RESET} {s.endpoint}")
            print(f"      {Colors.DIM}Target:{Colors.RESET}   {s.target_key}")

            if debug and s.mapping_fields:
                print(f"      {Colors.DIM}Mapping:{Colors.RESET}  {len(s.mapping_fields)} field(s)")
                if s.mapping_replace_object:
                    print(f"      {Colors.DIM}Replace:{Colors.RESET}  {s.mapping_replace_object}")
                for m in s.mapping_fields:
                    api_f = m.get("from", "")
                    out_f = m.get("to", "")
                    print(f"        {Colors.DIM}{api_f} -> {out_f}{Colors.RESET}")

            if debug and s.defaults:
                print(f"      {Colors.DIM}Defaults:{Colors.RESET} {list(s.defaults.keys())}")

            print()

        print(f"  {Colors.DIM}{'─' * 40}{Colors.RESET}")
        summary = f"  {Colors.GREEN}{len(enabled)} enabled{Colors.RESET}"
        if disabled:
            summary += f" {Colors.DIM}| {len(disabled)} disabled{Colors.RESET}"
        print(summary)
        print()

    @staticmethod
    def source_start(current: int, total: int, name: str):
        bar_width = 20
        filled = int(bar_width * current / total)
        bar = "█" * filled + "░" * (bar_width - filled)
        progress = f"[{current}/{total}]"

        print(f"\n{Colors.CYAN}{progress}{Colors.RESET} {bar} {Colors.BOLD}{name}{Colors.RESET}")

    @staticmethod
    def source_result(success: bool, items: int = 0, message: str = None):
        if success:
            print(f"    {Colors.GREEN}✓ {items} item(s) collected{Colors.RESET}")
        else:
            print(f"    {Colors.RED}✗ FAILED{Colors.RESET}")
            if message:
                print(f"    {Colors.RED}{message}{Colors.RESET}")

    @staticmethod
    def diff_output(changes: list):
        if not changes:
            return
        print(f"\n  {Colors.YELLOW}{Colors.BOLD}Changes detected:{Colors.RESET}")
        for change in changes:
            if change.strip().startswith("+"):
                color = Colors.GREEN
            elif change.strip().startswith("-"):
                color = Colors.RED
            else:
                color = Colors.YELLOW
            print(f"  {color}{change}{Colors.RESET}")

    @staticmethod
    def summary(stats: SeederStats, duration: float):
        print()
        print(f"{Colors.DIM}{'─' * 50}{Colors.RESET}")
        print()

        if stats.failed_connectors == 0 and stats.total_items > 0:
            header = f"{Colors.BG_GREEN}{Colors.BLACK}{Colors.BOLD} SEEDER SUCCESSFUL {Colors.RESET}"
        elif stats.failed_connectors > 0:
            header = f"{Colors.BG_RED}{Colors.WHITE}{Colors.BOLD} SEEDER FAILED {Colors.RESET}"
        else:
            header = f"{Colors.BG_YELLOW}{Colors.BLACK}{Colors.BOLD} SEEDER NO DATA {Colors.RESET}"

        print(f"  {header}")
        print()
        print(f"  {Colors.BOLD}Summary:{Colors.RESET}")
        print(f"    Connectors:  {stats.total_connectors}")
        print(f"    {Colors.GREEN}Successful:{Colors.RESET}  {stats.successful_connectors}")
        if stats.failed_connectors > 0:
            print(f"    {Colors.RED}Failed:{Colors.RESET}      {stats.failed_connectors}")
        if stats.skipped_connectors > 0:
            print(f"    {Colors.YELLOW}Skipped:{Colors.RESET}     {stats.skipped_connectors}")
        print(f"    Items:       {stats.total_items}")

        if stats.output_updated:
            print(f"    Output:      {Colors.GREEN}updated{Colors.RESET}")
        else:
            print(f"    Output:      {Colors.DIM}unchanged{Colors.RESET}")

        print(f"    {Colors.BOLD}Duration:{Colors.RESET}    {duration:.2f}s")
        print()

        failed = [r for r in stats.results if not r.success]
        if failed:
            print(f"  {Colors.RED}{Colors.BOLD}Failed Connectors:{Colors.RESET}")
            for r in failed:
                print(f"    - {r.name}: {r.message or 'Unknown error'}")
            print()

        print(f"{Colors.DIM}{'─' * 50}{Colors.RESET}")
