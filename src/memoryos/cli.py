#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parents[1]
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from memoryos.core.checkpoint import CheckpointEngine
from memoryos.core.event_writer import log_event
from memoryos.core.indexer import build_timeline_index
from memoryos.core.init import initialize_memory_repo
from memoryos.core.query import query_timeline
from memoryos.core.tlb import MemTLB
from memoryos.core.writer import create_decision_adr


def detect_gpu():
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return f"NVIDIA: {result.stdout.strip().splitlines()[0]}"
    except Exception:
        pass
    try:
        result = subprocess.run(["rocm-smi", "--showproductname"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return "AMD ROCm"
    except Exception:
        pass
    return "CPU Mode (No Dedicated GPU Detected)"


def main():
    parser = argparse.ArgumentParser(prog="memoryos", description="MemoryOS CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Init
    init_parser = subparsers.add_parser("init", help="Initialize memory repository")
    init_parser.add_argument("--path", type=str, default=".", help="Target directory")

    # Log Decision
    log_parser = subparsers.add_parser("log", help="Log entries")
    log_sub = log_parser.add_subparsers(dest="log_type", required=True)

    dec_parser = log_sub.add_parser("decision", help="Log an ADR")
    dec_parser.add_argument("--title", required=True)
    dec_parser.add_argument("--decision", required=True)
    dec_parser.add_argument("--reason", required=True)
    dec_parser.add_argument("--evidence", default="N/A")
    dec_parser.add_argument("--outcome", default="Pending")

    event_parser = log_sub.add_parser("event", help="Log an operational event")
    event_parser.add_argument("--type", required=True)
    event_parser.add_argument(
        "--context",
        type=str,
        default="{}",
        help="JSON string of context (status, priority, etc.)",
    )

    # Index
    subparsers.add_parser("index", help="Build timeline index.json")

    # TLB
    tlb_parser = subparsers.add_parser("tlb", help="Manage Mem-TLB cache")
    tlb_parser.add_argument("--show", action="store_true", help="Show hot cache contents")
    tlb_parser.add_argument("--access", type=str, help="Access a memory block by ID")

    # Checkpoint
    cp_parser = subparsers.add_parser("checkpoint", help="Manage checkpoints")
    cp_parser.add_argument("--save", action="store_true", help="Save current state")
    cp_parser.add_argument("--load", type=str, help="Load checkpoint by name")

    # Query
    query_parser = subparsers.add_parser("query", help="Query the timeline")
    query_parser.add_argument("--tag", type=str, help="Filter by tag")

    # Hardware
    subparsers.add_parser("hw", help="Detect hardware capabilities")

    # Heat-Stream (registered BEFORE parse_args!)
    subparsers.add_parser("heat", help="Scan hot memories via MemoryHeatStream")

    args = parser.parse_args()
    target_path = Path(args.path) if hasattr(args, "path") else Path(".")

    if args.command == "init":
        print(f"Initializing memory repository at {target_path.resolve()}...")
        initialize_memory_repo(target_path)
        print("Memory repository initialized.")

    elif args.command == "log":
        if args.log_type == "decision":
            impact = {}
            create_decision_adr(
                args.title,
                args.decision,
                args.reason,
                args.evidence,
                args.outcome,
                impact,
                target_path,
            )
            print(f"ADR logged: {args.title}")
            build_timeline_index(target_path)
        elif args.log_type == "event":
            context = json.loads(args.context)
            log_event(args.type, context, target_path)
            print(f"Event logged: {args.type}")
            build_timeline_index(target_path)

    elif args.command == "index":
        build_timeline_index(target_path)
        print(f"Timeline index built at {target_path.resolve()}/memory/timeline/index.json")

    elif args.command == "tlb":
        tlb = MemTLB()
        if args.show:
            print("Hot Cache:")
            for bid, block in tlb.hot_cache.items():
                print(f"  {bid} (Heat: {block['heat']:.2f})")
        elif args.access:
            res = tlb.access(args.access)
            print(f"Accessed: {res}")

    elif args.command == "checkpoint":
        engine = CheckpointEngine(target_path)
        if args.save:
            engine.save()
        elif args.load:
            engine.load(args.load)

    elif args.command == "query":
        results = query_timeline(target_path, args.tag)
        print(json.dumps(results, indent=2))

    elif args.command == "hw":
        print(f"Hardware Profile: {detect_gpu()}")

    elif args.command == "heat":
        from memoryos.core.heat_stream import MemoryHeatStream

        hs = MemoryHeatStream()
        hot = hs.scan_for_hot_memories()
        print(f"Hot memories scanned ({len(hot)} active blocks).")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
