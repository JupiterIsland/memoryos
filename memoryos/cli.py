#!/usr/bin/env python3
import argparse
from pathlib import Path
from memoryos.core.init import initialize_memory_repo
from memoryos.core.writer import create_decision_adr
from memoryos.core.indexer import build_timeline_index

def main():
    parser = argparse.ArgumentParser(
        prog="memoryos",
        description="MemoryOS: Institutional decision and context memory CLI."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: memoryos init
    init_parser = subparsers.add_parser("init", help="Initialize memory/ structure")
    init_parser.add_argument("--path", type=str, default=".", help="Target directory path")

    # Command: memoryos log decision
    log_parser = subparsers.add_parser("log", help="Log an entry into MemoryOS")
    log_subparsers = log_parser.add_subparsers(dest="log_type", help="Type of log entry")

    dec_parser = log_subparsers.add_parser("decision", help="Log a new Architecture Decision Record")
    dec_parser.add_argument("--title", required=True, help="Short title of the decision")
    dec_parser.add_argument("--decision", required=True, help="What was decided?")
    dec_parser.add_argument("--reason", required=True, help="Why was this decision made?")
    dec_parser.add_argument("--evidence", default="N/A", help="Supporting benchmarks or data")
    dec_parser.add_argument("--outcome", default="Pending review", help="Expected or observed outcome")
    dec_parser.add_argument("--time-saved", default="N/A", help="Estimated time saved")
    dec_parser.add_argument("--cost-impact", default="N/A", help="Cost impact or budget delta")
    dec_parser.add_argument("--risk-reduction", default="N/A", help="Risk reduction achieved")
    dec_parser.add_argument("--strategic-value", default="N/A", help="Long-term strategic value")

    # Command: memoryos index
    index_parser = subparsers.add_parser("index", help="Compile memory/timeline/index.json")
    index_parser.add_argument("--path", type=str, default=".", help="Target directory path")

    args = parser.parse_args()

    if args.command == "init":
        target = Path(args.path)
        initialize_memory_repo(target)
        print(f"Success: Initialized memory/ taxonomy in {target.resolve()}")

    elif args.command == "log" and args.log_type == "decision":
        impact = {
            "time_saved": args.time_saved,
            "cost_impact": args.cost_impact,
            "risk_reduction": args.risk_reduction,
            "strategic_value": args.strategic_value
        }
        file_created = create_decision_adr(
            title=args.title,
            decision=args.decision,
            reason=args.reason,
            evidence=args.evidence,
            outcome=args.outcome,
            impact=impact
        )
        print(f"Success: Created {file_created}")
        
        # Auto-rebuild timeline index
        index_file = build_timeline_index()
        print(f"Success: Updated {index_file}")

    elif args.command == "index":
        target = Path(args.path)
        index_file = build_timeline_index(target)
        print(f"Success: Compiled timeline index at {index_file.resolve()}")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
