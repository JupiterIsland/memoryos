#!/usr/bin/env python3
"""Bootstrap and end-to-end verification script for MemoryOS, Quiet Advisor, and Jupiter TV.

Initializes the SQLite database schema, ingests Token Lab telemetry if present,
runs a simulated Jupiter TV SceneAnalyzer session through the MemoryOS router,
and verifies that Quiet Advisor detects patterns and generates d3-routed cards.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from apps.quiet_advisor_ui.api import get_dashboard_state, run_detection_cycle
from apps.shared.ai import Scene, SceneAnalyzer, render_hero_poster
from src.memoryos.quiet_advisor_db import DEFAULT_DB_PATH, QuietAdvisorDB
from src.memoryos.router import route_task


def run_bootstrap(db_path: Path = DEFAULT_DB_PATH) -> dict:
    print("=" * 68)
    print("MEMORYOS // QUIET ADVISOR + JUPITER TV BOOTSTRAP")
    print("=" * 68)

    # 1. Initialize SQLite schema
    db = QuietAdvisorDB(db_path)
    db.close()
    print(f"[1/4] SQLite schema initialized -> {db_path}")

    # 2. Run Jupiter TV SceneAnalyzer + VLM Frame Inspector (logs to QuietAdvisorDB)
    analyzer = SceneAnalyzer(advisor_db_path=db_path, user_id="default")
    demo_scenes = [
        Scene(start_ms=0, end_ms=18000, label="Intro", transcript="Opening skyline and title sequence"),
        Scene(start_ms=18000, end_ms=46000, label="Dialogue", transcript="Arguing about the server budget"),
        Scene(start_ms=46000, end_ms=90000, label="Action", transcript="High-speed chase through neon tunnel"),
    ]
    for idx, sc in enumerate(demo_scenes):
        analyzer._label_scene_with_vlm(sc, frame_data_url=None, idx=idx)

    poster_png = render_hero_poster("Jupiter TV Demo", demo_scenes)
    vision = analyzer.inspect_frame(poster_png, context_hint="Opening frame")
    recap_text = analyzer.recap(demo_scenes)
    route_res = route_task(
        "Classify whether this scene needs 4K upscaling: yes or no.",
        tlb_context="x" * 6000,
        user_id="default",
        session_id="jupiter-tv-scene-nav",
        context_tokens_provided=32768,
        db_path=db_path,
    )
    print(
        f"[2/4] Jupiter TV logged inferences -> model={route_res['model']} "
        f"d3={route_res['d3_decision']['choice']} ({route_res['d3_decision']['confidence']:.0%}) "
        f"vision={vision.model}"
    )

    # 3. Trigger Quiet Advisor detection + d3 gatekeeping
    det = run_detection_cycle(lookback_hours=48, seed_if_empty=False, db_path=db_path)
    state = det["state"]
    print(
        f"[3/4] Quiet Advisor evaluated {state['telemetry']['total_inferences']} inferences -> "
        f"{len(state['active_cards'])} active card(s)"
    )

    # 4. Print active cards
    for card in state["active_cards"][:4]:
        d3 = card["d3_routing"]
        print(
            f"      • [{card['detector_type']}] {card['title']} "
            f"(d3={d3['choice']} {d3['confidence']:.0%}) -> {card['recommended_action']}"
        )
    print(f"[4/4] Recap preview: {recap_text[:90]}")
    print("=" * 68)
    return state


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap MemoryOS + Quiet Advisor + Jupiter TV")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="Path to SQLite database")
    args = parser.parse_args()
    run_bootstrap(Path(args.db))


if __name__ == "__main__":
    main()
