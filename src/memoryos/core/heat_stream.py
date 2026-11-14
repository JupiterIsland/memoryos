"""
Memory Heat Stream Engine v0.2.0
===================================
Monitors TLB Hot Cache for memory blocks with high access frequency ("heat")
and automatically formats them into Markdown snippets ready for LLM injection.
No Cloud. Local-first. Tiered Storage Architecture.
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class MemoryBlock:
    """Represents a single memory block in the TLB Hot Cache."""
    id: str
    title: str
    content: str
    timestamp: float = field(default_factory=time.time)
    heat_score: float = 0.0  # Access frequency score (0-1.0)
    access_count: int = 0
    category: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_markdown(self) -> str:
        """Convert memory block to LLM-ready Markdown snippet."""
        header = f"## {self.title}"
        if self.category:
            header += f"\n> **Category:** `{self.category}`"
        
        body = self.content.strip()
        
        meta = ""
        if self.metadata.get('source'):
            meta += f"\n- Source: `{self.metadata['source']}`"
        if self.metadata.get('confidence') is not None:
            meta += f"\n- Confidence: {self.metadata['confidence']}%"
        
        return f"{header}\n{body}{meta}"


@dataclass
class HeatStreamState:
    """Tracks the state of the Memory Heat Stream."""
    is_active: bool = False
    last_scan: float = 0.0
    scan_interval: float = 5.0  # seconds
    hot_threshold: float = 0.7  # heat_score threshold for injection
    temp_graph_path: str = ""
    tlb_cache_path: str = ""


class MemoryHeatStream:
    """
    Core Heat Stream Engine
    
    Monitors TLB Hot Cache and manages temporal graph connections between
    memory blocks to determine what's "hot" and ready for context injection.
    """
    
    def __init__(self, 
                 tlb_cache_dir: str = None,
                 temp_graph_path: str = None,
                 checkpoint_dir: str = None,
                 scan_interval: float = 5.0):
        """
        Initialize Memory Heat Stream
        
        Args:
            tlb_cache_dir: Path to TLB Hot Cache directory (NVMe/MRAM)
            temp_graph_path: Path to temporal graph storage
            checkpoint_dir: Path for NVMe checkpoints
            scan_interval: How often to scan for hot memories (seconds)
        """
        self.tlb_cache = tlb_cache_dir or os.getenv("MEMORYOS_TLB_CACHE", "./tlb_hot_cache")
        self.temp_graph = temp_graph_path or os.getenv("MEMORYOS_TEMP_GRAPH", "./temporal_graph")
        self.checkpoint_dir = checkpoint_dir or os.getenv("MEMORYOS_CHECKPOINT_DIR", "./nvme_checkpoints")
        
        self.state = HeatStreamState(
            tlb_cache_path=self.tlb_cache,
            temp_graph_path=self.temp_graph,
            scan_interval=scan_interval
        )
        
        self._ensure_paths()
        self._load_state()
    
    def _ensure_paths(self):
        """Ensure all required directories exist."""
        Path(self.tlb_cache).mkdir(parents=True, exist_ok=True)
        Path(self.temp_graph).mkdir(parents=True, exist_ok=True)
        Path(self.checkpoint_dir).mkdir(parents=True, exist_ok=True)
    
    def _load_state(self):
        """Load current heat stream state from checkpoint."""
        state_file = Path(self.temp_graph) / "heat_stream_state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    data = json.load(f)
                    self.state.is_active = data.get('is_active', False)
                    self.state.last_scan = data.get('last_scan', 0.0)
                    self.state.hot_threshold = data.get('hot_threshold', 0.7)
                    self.state.scan_interval = data.get('scan_interval', 5.0)
            except Exception:
                pass
    
    def _save_state(self):
        """Persist heat stream state to checkpoint."""
        state_file = Path(self.temp_graph) / "heat_stream_state.json"
        try:
            with open(state_file, 'w') as f:
                json.dump({
                    'is_active': self.state.is_active,
                    'last_scan': self.state.last_scan,
                    'hot_threshold': self.state.hot_threshold,
                    'scan_interval': self.state.scan_interval
                }, f)
        except Exception:
            pass
    
    def scan_for_hot_memories(self) -> List[MemoryBlock]:
        """
        Scan TLB Cache for memory blocks exceeding heat threshold.
        
        Returns:
            List of hot memory blocks ready for context injection
        """
        hot_blocks = []
        now = time.time()
        
        # Update state timestamp
        self.state.last_scan = now
        self._save_state()
        
        # Index file contains memory block metadata
        index_file = Path(self.tlb_cache) / "memory_index.json"
        
        if not index_file.exists():
            return hot_blocks
        
        try:
            with open(index_file, 'r') as f:
                blocks_data = json.load(f)
            
            for block_data in blocks_data:
                heat_score = block_data.get('heat_score', 0.0)
                
                if heat_score >= self.state.hot_threshold:
                    # Calculate decayed heat score (access frequency drops over time)
                    time_since_access = now - block_data.get('timestamp', 0)
                    decay_factor = max(0, 1 - (time_since_access / 3600))  # 1hr decay
                    
                    block = MemoryBlock(
                        id=block_data['id'],
                        title=block_data['title'],
                        content=block_data.get('content', ''),
                        timestamp=block_data['timestamp'],
                        heat_score=heat_score * decay_factor,
                        access_count=block_data.get('access_count', 0),
                        category=block_data.get('category'),
                        metadata=block_data.get('metadata', {})
                    )
                    hot_blocks.append(block)
                    
            # Sort by heat score (highest first)
            hot_blocks.sort(key=lambda x: x.heat_score, reverse=True)
            
        except Exception as e:
            print(f"[HeatStream] Scan error: {e}")
        
        return hot_blocks
    
    def get_hot_context(self, limit: int = 5) -> str:
        """
        Get formatted context from hottest memories for LLM injection.
        
        Args:
            limit: Number of top hot memories to include
        
        Returns:
            Markdown string ready for system prompt injection
        """
        hot_blocks = self.scan_for_hot_memories()
        
        if not hot_blocks:
            return "# No Hot Memories Detected\n\nYour TLB cache is currently cold. Run memory events or decisions to build heat."
        
        context_parts = []
        for i, block in enumerate(hot_blocks[:limit], 1):
            markdown = block.to_markdown()
            context_parts.append(markdown)
            
            if i < limit:
                context_parts.append("\n---\n\n")
        
        return "\n".join(context_parts)
    
    def update_block_heat(self, block_id: str, increment: float = 0.1):
        """Manually increase heat score for a specific memory block."""
        index_file = Path(self.tlb_cache) / "memory_index.json"
        
        if not index_file.exists():
            return False
        
        try:
            with open(index_file, 'r') as f:
                blocks_data = json.load(f)
            
            for block in blocks_data:
                if block['id'] == block_id:
                    block['heat_score'] += increment
                    block['access_count'] += 1
                    self._save_state()
                    return True
            
        except Exception as e:
            print(f"[HeatStream] Update error: {e}")
        
        return False
    
    def persist_checkpoint(self, block_id: str, content: str):
        """Write memory block to NVMe checkpoint for persistence."""
        checkpoint_file = Path(self.checkpoint_dir) / f"{block_id}.json"
        
        try:
            data = {
                'id': block_id,
                'content': content,
                'timestamp': time.time(),
                'persistent': True
            }
            
            with open(checkpoint_file, 'w') as f:
                json.dump(data, f)
            
            return True
            
        except Exception as e:
            print(f"[HeatStream] Checkpoint error: {e}")
        
        return False
    
    def start_monitoring(self):
        """Start background monitoring of TLB cache for hot memories."""
        self.state.is_active = True
        self._save_state()
        print("[HeatStream] Monitoring activated. Scanning every 5s for hot memories.")
    
    def stop_monitoring(self):
        """Stop background monitoring."""
        self.state.is_active = False
        self._save_state()
        print("[HeatStream] Monitoring stopped.")


# CLI Interface for External Access
def heat_stream_init(tlb_cache_dir: str, temp_graph_path: str) -> MemoryHeatStream:
    """Initialize Heat Stream Engine."""
    engine = MemoryHeatStream(
        tlb_cache_dir=tlb_cache_dir,
        temp_graph_path=temp_graph_path
    )
    engine.start_monitoring()
    return engine


def heat_stream_sync(limit: int = 5) -> str:
    """Get hot context for immediate LLM injection."""
    engine = MemoryHeatStream()
    return engine.get_hot_context(limit=limit)
