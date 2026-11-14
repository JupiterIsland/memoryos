"""End-to-end live verification for Auto-Router, Quiet Advisor Loop, and Jupiter TV Scene Navigator."""

import asyncio
import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from apps.shared.ai import Scene, SceneAnalyzer
from apps.shared.memory_store import MemoryStore
from quiet_advisor_detectors import QuietAdvisorEngine
from quiet_advisor_scheduler import CardDisplayService, InferenceLogger, QuietAdvisorScheduler
from src.memoryos.quiet_advisor_db import QuietAdvisorDB, log_routed_inference
from src.memoryos.router import route_task


async def main() -> None:
    print("=== 1. MULTI-MODEL AUTO-ROUTER (d3 -> Token Lab) ===")
    res_fast = route_task(
        "Reply with the single word: OK",
        save_checkpoint=True,
    )
    print(f"  Prompt 1 routed to: {res_fast['route']} ({res_fast['model']}) | {res_fast['latency_ms']} ms")
    print(f"  Checkpoint: {res_fast.get('checkpoint_path')}")

    res_code = route_task(
        "Write a 2-line Python function add(a, b) with type hints.",
        save_checkpoint=True,
    )
    print(f"  Prompt 2 routed to: {res_code['route']} ({res_code['model']}) | {res_code['latency_ms']} ms")

    print("\n=== 2. QUIET ADVISOR LIVE LOOP (SQLite + Detectors + d3) ===")
    with tempfile.TemporaryDirectory() as tmpdir:
        db = QuietAdvisorDB(Path(tmpdir) / "quiet_advisor_test.db")
        try:
            inf_logger = InferenceLogger(db)
            await log_routed_inference(inf_logger, res_fast, user_id="rjmed", session_id="verify")
            await log_routed_inference(inf_logger, res_code, user_id="rjmed", session_id="verify")

            # Add 4 more inferences showing context padding waste so ContextWasteDetector triggers (>=5 samples)
            for i in range(4):
                await inf_logger.log_inference(
                    user_id="rjmed",
                    session_id="verify",
                    model_id=res_code["model"],
                    context_tokens_provided=16384,
                    context_tokens_used=1100 + i * 50,
                    time_to_first_token_ms=220.0,
                    total_latency_ms=1450.0 + i * 40,
                    tokens_per_second=68.0,
                    gpu_state={"gpu_id": "tokenlab-remote", "utilization": 0.0, "temperature": 0.0, "memory_used_mb": 0},
                    output_quality_score=0.92,
                )

            scheduler = QuietAdvisorScheduler(db, QuietAdvisorEngine())
            await scheduler.run_daily_detection(lookback_hours=24)

            display = CardDisplayService(db)
            card = await display.get_card_for_user("rjmed")
            assert card is not None, "Expected Quiet Advisor card to be generated and stored"
            action_val = json.loads(card["action_value"])
            print(f"  Generated Card: {card['title']} ({card['detector_type']})")
            print(f"  d3 Routing Decision: {action_val.get('d3_routing')}")
        finally:
            db.close()

    print("\n=== 3. JUPITER TV AI SCENE NAVIGATOR (MemoryStore + Search + Recap) ===")
    analyzer = SceneAnalyzer(memory_store=MemoryStore())
    sample_scenes = [
        Scene(start_ms=0, end_ms=120000, label="Soundcheck and studio setup", summary="Band tunes guitars before the live set."),
        Scene(start_ms=120000, end_ms=280000, label="Black Magic Woman breakdown", summary="Mick Fleetwood explains the origin of the riff."),
        Scene(start_ms=280000, end_ms=420000, label="Acoustic encore", summary="Closing solo acoustic performance on stage."),
    ]
    matches = analyzer.search_scenes(sample_scenes, "Fleetwood riff origin")
    assert matches and matches[0].start_ms == 120000
    print(f"  Scene Search Match: {matches[0]}")

    recap_text = analyzer.recap(sample_scenes, up_to_ms=200000)
    print(f"  AI Recap: {recap_text}")
    print("\nALL 3 SYSTEMS VERIFIED SUCCESSFULLY.")


if __name__ == "__main__":
    asyncio.run(main())
