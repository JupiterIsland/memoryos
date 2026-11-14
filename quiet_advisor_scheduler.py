"""
THE QUIET ADVISOR - Inference Logger & Scheduler
Part of: MemoryOS + Jupiter One unified system

This module logs every inference and runs daily pattern detection
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class InferenceLogger:
    """
    Logs every inference automatically.
    Integrates with Apex-Metal inference engine.
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def log_inference(self, 
                           user_id: str,
                           session_id: str,
                           model_id: str,
                           context_tokens_provided: int,
                           context_tokens_used: int,
                           time_to_first_token_ms: float,
                           total_latency_ms: float,
                           tokens_per_second: float,
                           gpu_state: Dict,
                           output_quality_score: Optional[float] = None,
                           error_flag: bool = False,
                           error_message: Optional[str] = None):
        """
        Log a single inference execution.
        Called automatically after every inference in Apex-Metal.
        """
        
        inference_record = {
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "model_id": model_id,
            "context_tokens_provided": context_tokens_provided,
            "context_tokens_used": context_tokens_used,
            "time_to_first_token_ms": time_to_first_token_ms,
            "total_latency_ms": total_latency_ms,
            "tokens_per_second": tokens_per_second,
            "gpu_id": gpu_state.get("gpu_id"),
            "gpu_utilization_percent": gpu_state.get("utilization"),
            "gpu_temperature_celsius": gpu_state.get("temperature"),
            "gpu_memory_used_mb": gpu_state.get("memory_used_mb"),
            "output_quality_score": output_quality_score,
            "error_flag": error_flag,
            "error_message": error_message,
        }
        
        try:
            # Insert into time-series database (e.g., InfluxDB, TimescaleDB)
            await self.db.insert("memoryos.inference_log", inference_record)
            logger.debug(f"Logged inference for user {user_id}: {model_id}")
        except Exception as e:
            logger.error(f"Failed to log inference: {e}")
            # Don't fail the inference, just log the error
            pass


class QuietAdvisorScheduler:
    """
    Runs daily pattern detection at off-peak hours (2 AM).
    Generates one card per user.
    """
    
    def __init__(self, db_connection, detector_engine):
        self.db = db_connection
        self.engine = detector_engine
    
    async def run_daily_detection(self, lookback_hours: int = 24):
        """
        Daily batch job: Detect patterns for all users.
        Runs at 2 AM UTC (off-peak) or on-demand for recent inferences.
        """
        logger.info("Starting daily pattern detection")
        
        try:
            # Get all active users
            users = await self.db.query("SELECT user_id FROM users WHERE active=true")
            
            for user in users:
                user_id = user["user_id"]
                
                # Get recent inferences in lookback window
                since = datetime.utcnow() - timedelta(hours=lookback_hours)
                inferences = await self._get_user_inferences(user_id, since, window_hours=lookback_hours)
                
                if len(inferences) < 3:
                    # Not enough data for meaningful patterns
                    logger.debug(f"Skipping user {user_id}: insufficient data")
                    continue
                
                # Get user preferences (what they care about)
                preferences = await self._get_user_preferences(user_id)
                
                # Run detectors
                insights = self.engine.detect_patterns(inferences, preferences)
                
                if not insights:
                    logger.debug(f"No insights for user {user_id}")
                    continue
                
                # Select top insight
                top_insight = insights[0]

                # Gate / route insight through Token Lab d3 aux-router
                d3_decision = self._route_with_d3(top_insight, preferences)
                if d3_decision and d3_decision.get("choice") == "ignore":
                    logger.info(
                        f"d3 suppressed low-signal card for user {user_id}: {top_insight.title} "
                        f"(confidence={d3_decision.get('confidence', 0.0):.2f})"
                    )
                    continue

                # Store card in database
                await self._store_card(user_id, top_insight, d3_decision=d3_decision)
                
                logger.info(f"Generated card for user {user_id}: {top_insight.title}")
                
        except Exception as e:
            logger.error(f"Daily detection failed: {e}")

    @staticmethod
    def _route_with_d3(insight, preferences: Optional[Dict] = None) -> Optional[Dict]:
        """Evaluate whether to surface an insight using Token Lab's d3 aux-router."""
        try:
            try:
                from src.memoryos.router import evaluate_insight_with_d3
            except ImportError:
                from memoryos.router import evaluate_insight_with_d3
            return evaluate_insight_with_d3(insight, preferences)
        except Exception as e:
            logger.warning(f"d3 routing unavailable, defaulting to local score: {e}")
            return None
    
    async def _get_user_inferences(self, user_id: str, from_date: datetime, window_hours: int = 24) -> List:
        """Fetch inferences from the given window for this user"""
        to_date = from_date + timedelta(hours=window_hours) + timedelta(minutes=1)
        
        query = f"""
        SELECT * FROM memoryos.inference_log
        WHERE user_id = '{user_id}'
        AND timestamp >= '{from_date.isoformat()}'
        AND timestamp < '{to_date.isoformat()}'
        ORDER BY timestamp
        """
        
        results = await self.db.query(query)
        if not results:
            return []
        try:
            try:
                from src.memoryos.quiet_advisor_db import row_to_inference_log
            except ImportError:
                from memoryos.quiet_advisor_db import row_to_inference_log
            return [row_to_inference_log(r) if isinstance(r, dict) else r for r in results]
        except Exception:
            return results
    
    async def _get_user_preferences(self, user_id: str) -> Dict:
        """Get user's card preferences (learned from past behavior)"""
        try:
            prefs = await self.db.query_one(
                f"SELECT card_type_preferences FROM quiet_advisor.user_preferences WHERE user_id = '{user_id}'"
            )
            return json.loads(prefs["card_type_preferences"]) if prefs else {}
        except:
            return {}
    
    async def _store_card(self, user_id: str, insight, d3_decision: Optional[Dict] = None):
        """Store generated card in database"""
        action_value = dict(insight.action_value) if isinstance(insight.action_value, dict) else {"value": insight.action_value}
        if d3_decision:
            action_value["d3_routing"] = d3_decision

        card_record = {
            "user_id": user_id,
            "detector_type": insight.detector_type.value,
            "insight_rank": insight.score(),
            "title": insight.title,
            "subtitle": insight.subtitle,
            "description": insight.description,
            "metric_1": list(insight.metrics.values())[0] if insight.metrics else "",
            "metric_2": list(insight.metrics.values())[1] if len(insight.metrics) > 1 else "",
            "metric_3": list(insight.metrics.values())[2] if len(insight.metrics) > 2 else "",
            "recommended_action": insight.recommended_action,
            "action_value": json.dumps(action_value),
            "time_savings_seconds": insight.time_savings_seconds,
            "quality_improvement_percent": insight.quality_improvement_percent,
            "suggested_experiments": json.dumps(insight.suggested_experiments or []),
            "user_dismissed": False,
            "user_archived": False,
            "user_actioned": False,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        }
        
        await self.db.insert("quiet_advisor.cards", card_record)


class CardActionHandler:
    """
    Handles user interactions with cards.
    Logs actions and triggers workflows.
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def handle_action(self, user_id: str, card_id: str, action: str, 
                           metadata: Optional[Dict] = None):
        """
        Handle user action on card.
        
        Actions:
        - 'view': User viewed the card
        - 'dismiss': User dismissed temporarily
        - 'archive': User never wants this type again
        - 'learn_more': User clicked learn more
        - 'action': User executed the suggestion
        """
        
        action_record = {
            "user_id": user_id,
            "card_id": card_id,
            "action_type": action,
            "action_result": json.dumps(metadata or {}),
            "created_at": datetime.utcnow().isoformat(),
        }
        
        await self.db.insert("quiet_advisor.card_actions", action_record)
        
        # Update card status
        if action == "dismiss":
            await self.db.execute(
                f"UPDATE quiet_advisor.cards SET user_dismissed = true WHERE id = '{card_id}'"
            )
        elif action == "archive":
            await self.db.execute(
                f"UPDATE quiet_advisor.cards SET user_archived = true WHERE id = '{card_id}'"
            )
        elif action in ("action", "acknowledge"):
            await self.db.execute(
                f"UPDATE quiet_advisor.cards SET user_actioned = true WHERE id = '{card_id}'"
            )
        
        # Update user preferences based on action (closed-loop routing feedback)
        await self._update_user_preferences(user_id, card_id, action, metadata=metadata)
        
        logger.info(f"Card action: user={user_id}, card={card_id}, action={action}")
    
    async def _update_user_preferences(
        self,
        user_id: str,
        card_id: str,
        action: str,
        metadata: Optional[Dict] = None,
    ):
        """Learn from user actions and write routing penalties into quiet_advisor_user_preferences."""
        
        # Get card detector type and action_value payload
        card = await self.db.query_one(
            f"SELECT detector_type, recommended_action, action_value FROM quiet_advisor.cards WHERE id = '{card_id}'"
        )
        if not card:
            return
        
        detector_type = card["detector_type"]
        recommended_action = card.get("recommended_action") or ""
        try:
            action_val = json.loads(card.get("action_value") or "{}")
            if not isinstance(action_val, dict):
                action_val = {}
        except Exception:
            action_val = {}
        
        # Get or create user preferences
        prefs = await self.db.query_one(
            f"SELECT card_type_preferences FROM quiet_advisor.user_preferences WHERE user_id = '{user_id}'"
        )
        
        if prefs:
            preferences = json.loads(prefs["card_type_preferences"])
        else:
            preferences = {}
        
        # Update preference weight based on action
        current_pref = float(preferences.get(detector_type, 0.5))
        
        if action in ("action", "acknowledge"):
            new_pref = min(current_pref + 0.1, 1.0)
        elif action == "archive":
            new_pref = max(current_pref - 0.2, 0.0)
        elif action == "dismiss":
            new_pref = max(current_pref - 0.02, 0.0)
        else:
            new_pref = current_pref
        
        preferences[detector_type] = new_pref

        # Closed-loop routing policy updates when user clicks [Acknowledge & Apply]
        if action in ("action", "acknowledge"):
            meta = metadata or {}
            if detector_type in ("vram_thrashing", "model_thrashing") or recommended_action == "force_tokenlab_offload":
                penalty = float(meta.get("penalty") or action_val.get("vram_thrashing_penalty") or 1.5)
                preferences["vram_thrashing_penalty"] = penalty
                preferences["force_remote_offload"] = True
                preferences["preferred_vision_model"] = str(action_val.get("forced_model") or "Gemma-4-31B-IT")
            elif f"{detector_type}_penalty" not in preferences and "penalty" in meta:
                preferences[f"{detector_type}_penalty"] = float(meta["penalty"])
            if detector_type == "context_waste" and "context_tokens" in action_val:
                preferences["recommended_context_cap"] = int(action_val["context_tokens"])

        prefs_json = json.dumps(preferences)
        if hasattr(self.db, "conn"):
            self.db.conn.execute(
                """
                INSERT INTO quiet_advisor_user_preferences (user_id, card_type_preferences)
                VALUES (?, ?)
                ON CONFLICT (user_id) DO UPDATE SET card_type_preferences = excluded.card_type_preferences
                """,
                (user_id, prefs_json),
            )
            self.db.conn.commit()
        else:
            escaped = prefs_json.replace("'", "''")
            await self.db.execute(f"""
            INSERT INTO quiet_advisor.user_preferences (user_id, card_type_preferences)
            VALUES ('{user_id}', '{escaped}')
            ON CONFLICT (user_id) DO UPDATE
            SET card_type_preferences = '{escaped}'
            """)


# Integration with Apex-Metal
class ApexMetalHook:
    """
    Integrates Quiet Advisor with Apex-Metal inference engine.
    Automatically logs every inference.
    """
    
    def __init__(self, logger: InferenceLogger):
        self.logger = logger
    
    async def post_inference_hook(self, inference_result):
        """
        Called after every inference completes in Apex-Metal.
        """
        
        await self.logger.log_inference(
            user_id=inference_result.user_id,
            session_id=inference_result.session_id,
            model_id=inference_result.model_id,
            context_tokens_provided=inference_result.context_length,
            context_tokens_used=inference_result.tokens_generated,
            time_to_first_token_ms=inference_result.time_to_first_token_ms,
            total_latency_ms=inference_result.total_latency_ms,
            tokens_per_second=inference_result.tokens_per_second,
            gpu_state={
                "gpu_id": inference_result.gpu_id,
                "utilization": inference_result.gpu_utilization,
                "temperature": inference_result.gpu_temperature,
                "memory_used_mb": inference_result.gpu_memory_used,
            },
            output_quality_score=inference_result.output_quality if hasattr(inference_result, 'output_quality') else None,
            error_flag=inference_result.error_flag if hasattr(inference_result, 'error_flag') else False,
            error_message=inference_result.error_message if hasattr(inference_result, 'error_message') else None,
        )


# Integration with Jupiter One UI
class CardDisplayService:
    """
    Serves cards to Jupiter One UI.
    Handles display logic and expiration.
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    async def get_card_for_user(self, user_id: str) -> Optional[Dict]:
        """Get the active card to display for this user"""
        
        # Find newest non-dismissed, non-archived, non-expired card
        query = f"""
        SELECT * FROM quiet_advisor.cards
        WHERE user_id = '{user_id}'
        AND user_dismissed = false
        AND user_archived = false
        AND expires_at > NOW()
        ORDER BY created_at DESC
        LIMIT 1
        """
        
        card = await self.db.query_one(query)
        
        if card:
            # Record that user viewed this card
            action_handler = CardActionHandler(self.db)
            await action_handler.handle_action(user_id, card["id"], "view")
        
        return card
    
    async def get_card_archive(self, user_id: str) -> List[Dict]:
        """Get all dismissed/archived cards for user"""
        
        query = f"""
        SELECT * FROM quiet_advisor.cards
        WHERE user_id = '{user_id}'
        AND (user_dismissed = true OR user_archived = true OR expires_at < NOW())
        ORDER BY created_at DESC
        LIMIT 50
        """
        
        return await self.db.query(query)


# Example usage / testing
if __name__ == "__main__":
    import asyncio
    
    async def test():
        # This would be initialized with real database connection
        logger.info("Quiet Advisor logging and scheduling module loaded")
        
        # In production:
        # 1. InferenceLogger.log_inference called by Apex-Metal after each inference
        # 2. QuietAdvisorScheduler.run_daily_detection() runs at 2 AM daily
        # 3. CardDisplayService.get_card_for_user() called when user opens Jupiter One
        # 4. CardActionHandler.handle_action() called when user interacts with card
    
    asyncio.run(test())
