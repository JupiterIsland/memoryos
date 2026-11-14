"""
Browser Context Sync Bridge v0.2.0
==================================
Syncs Memory Heat Stream output into Browser App context window.
No Cloud. Local-first. Auto-injection ready.
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any


class ContextSyncBridge:
    """
    Browser App <-> MemoryOS Heat Stream Bridge
    
    Provides one-click sync from CLI heat cache to browser context.
    """
    
    def __init__(self, 
                 memoryos_cli_dir: str = None,
                 browser_context_file: str = None):
        """
        Initialize Context Sync Bridge
        
        Args:
            memoryos_cli_dir: Path to MemoryOS CLI installation
            browser_context_file: Path to browser context storage file
        """
        self.cli_dir = memoryos_cli_dir or os.getenv("MEMORYOS_CLI_DIR", "./")
        self.context_file = browser_context_file or os.getenv(
            "BROWSER_CONTEXT_FILE", 
            "./browser_context.md"
        )
        
        # Internal Heat Stream import
        try:
            from memoryos.core.heat_stream import MemoryHeatStream
            self._heat_stream = MemoryHeatStream()
        except ImportError:
            print("[ContextSync] Using fallback sync mode")
            self._heat_stream = None
    
    def sync_hot_cache(self, limit: int = 5) -> str:
        """
        Sync hot cache to browser context window.
        
        Args:
            limit: Number of hot memories to inject
        
        Returns:
            Formatted Markdown ready for LLM system prompt
        """
        if self._heat_stream:
            return self._heat_stream.get_hot_context(limit=limit)
        
        # Fallback: Read existing context file
        if os.path.exists(self.context_file):
            with open(self.context_file, 'r') as f:
                return f.read()
        
        return "# No Context Loaded\n\nOpen MemoryOS CLI and run:\n  memoryos index\n"
    
    def export_context_file(self, output_path: str = None) -> bool:
        """
        Export current hot context to markdown file.
        
        Args:
            output_path: Path to save context file
        
        Returns:
            True if successful, False otherwise
        """
        if not self._heat_stream:
            return False
        
        try:
            context = self.sync_hot_cache(limit=5)
            
            if output_path:
                with open(output_path, 'w') as f:
                    f.write(context)
            
            return True
            
        except Exception as e:
            print(f"[ContextSync] Export error: {e}")
        
        return False
    
    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary statistics about current context."""
        if not self._heat_stream:
            return {'status': 'uninitialized'}
        
        try:
            hot_blocks = self._heat_stream.scan_for_hot_memories()
            
            return {
                'total_blocks': len(hot_blocks),
                'hot_threshold': self._heat_stream.state.hot_threshold,
                'last_scan': datetime.fromtimestamp(
                    self._heat_stream.state.last_scan
                ).isoformat(),
                'is_active': self._heat_stream.state.is_active
            }
        except Exception:
            return {'status': 'error'}
    
    def inject_into_prompt(self, prompt_template: str) -> str:
        """
        Inject hot context into LLM prompt template.
        
        Args:
            prompt_template: Your existing system prompt template
        
        Returns:
            Prompt with injected context
        """
        if not self._heat_stream:
            return prompt_template
        
        context = self.sync_hot_cache(limit=3)
        
        # Simple injection pattern (customize as needed)
        injected = prompt_template.replace(
            "{HOT_CONTEXT}",
            context,
            1
        )
        
        return injected


# CLI Commands for Browser App Integration
def sync_command() -> str:
    """Sync hot cache command for browser app."""
    bridge = ContextSyncBridge()
    return bridge.sync_hot_cache(limit=5)


def export_command(output_path: str = None) -> bool:
    """Export context to file command."""
    bridge = ContextSyncBridge()
    return bridge.export_context_file(output_path=output_path)
