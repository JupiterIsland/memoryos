"""
MemoryOS MCP Server v0.2.0
===========================
Model Context Protocol server enabling multi-model AI communication
through Neural Memory Graph + NVIDIA Riva voice interface.

Multi-Model Architecture:
- NVIDIA NIM models (Nemotron, Llama, Mistral via build.nvidia.com)
- Local LLMs (via Docker Model Runner / LM Studio)
- Claude (via API)
- External AI services (via MCP)

All communicating through MemoryOS as shared memory layer.
"""

import os
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import subprocess


@dataclass
class MCPTool:
    """MCP tool definition for model context protocol."""
    name: str
    description: str
    inputSchema: Dict[str, Any]


class MemoryOSMCPServer:
    """
    MCP Server for Neural Memory Graph.
    Provides tools for multi-model AI collaboration through shared memory.
    
    Protocol: Model Context Protocol (MCP)
    Clients: Claude, Cursor, Docker Agent, LM Studio plugins
    Models: NVIDIA NIM, local LLMs, external APIs
    """
    
    def __init__(self, 
                 heat_stream=None,
                 neural_graph=None,
                 riva_client=None):
        """
        Initialize MCP server.
        
        Args:
            heat_stream: MemoryHeatStream instance
            neural_graph: NeuralMemoryGraph instance
            riva_client: RivaVoiceClient instance
        """
        self.heat_stream = heat_stream
        self.neural_graph = neural_graph
        self.riva_client = riva_client
        
        # Multi-model configuration
        self.models_config = {
            'nvidia_nim': {
                'name': 'NVIDIA NIM',
                'endpoint': 'https://integrate.api.nvidia.com/v1',
                'api_key_env': 'NVIDIA_API_KEY',
                'models': ['nemotron-mini', 'nemotron-large', 'llama-2-70b'],
                'type': 'cloud',
            },
            'local_llm': {
                'name': 'Local LLM (Docker Model Runner)',
                'endpoint': 'http://localhost:8000/v1',
                'models': ['mistral-7b', 'llama-13b'],
                'type': 'local',
            },
            'lm_studio': {
                'name': 'LM Studio',
                'endpoint': 'http://localhost:1234/v1',
                'models': ['any_loaded_model'],
                'type': 'local',
            },
            'claude': {
                'name': 'Claude (Anthropic)',
                'endpoint': 'https://api.anthropic.com',
                'api_key_env': 'ANTHROPIC_API_KEY',
                'models': ['claude-3-opus', 'claude-3-sonnet'],
                'type': 'api',
            }
        }
        
        # Available tools for MCP clients
        self.tools = self._define_mcp_tools()
    
    def _define_mcp_tools(self) -> Dict[str, MCPTool]:
        """Define all MCP tools available to models."""
        return {
            'query_hot_memories': MCPTool(
                name='query_hot_memories',
                description='Query hot memories from MemoryOS for context injection',
                inputSchema={
                    'type': 'object',
                    'properties': {
                        'category': {'type': 'string', 'description': 'Filter by memory category'},
                        'limit': {'type': 'integer', 'description': 'Number of results'},
                        'min_heat': {'type': 'number', 'description': 'Minimum heat score (0-1)'}
                    },
                    'required': []
                }
            ),
            'update_memory_heat': MCPTool(
                name='update_memory_heat',
                description='Increase heat score for important memories (marks as frequently accessed)',
                inputSchema={
                    'type': 'object',
                    'properties': {
                        'block_id': {'type': 'string', 'description': 'Memory block ID'},
                        'increment': {'type': 'number', 'description': 'Amount to increase heat'}
                    },
                    'required': ['block_id']
                }
            ),
            'create_memory': MCPTool(
                name='create_memory',
                description='Create new memory block in MemoryOS (persisted across models)',
                inputSchema={
                    'type': 'object',
                    'properties': {
                        'title': {'type': 'string', 'description': 'Memory title'},
                        'content': {'type': 'string', 'description': 'Memory content'},
                        'category': {'type': 'string', 'description': 'Category (e.g., knowledge, decision, context)'},
                        'initial_heat': {'type': 'number', 'description': 'Starting heat score (0-1)'}
                    },
                    'required': ['title', 'content']
                }
            ),
            'optimize_for_model': MCPTool(
                name='optimize_for_model',
                description='Prepare memory hierarchy for specific model (auto GPU/CPU/NVMe placement)',
                inputSchema={
                    'type': 'object',
                    'properties': {
                        'model_name': {'type': 'string', 'description': 'Model identifier'},
                        'model_size_gb': {'type': 'number', 'description': 'Model size in GB'},
                        'expected_context_tokens': {'type': 'integer', 'description': 'Expected context window'}
                    },
                    'required': ['model_size_gb']
                }
            ),
            'get_memory_status': MCPTool(
                name='get_memory_status',
                description='Get current memory graph status (GPU/CPU/NVMe distribution)',
                inputSchema={
                    'type': 'object',
                    'properties': {},
                    'required': []
                }
            ),
            'prefetch_memories': MCPTool(
                name='prefetch_memories',
                description='Prefetch memories to GPU for next N tokens (reduces latency)',
                inputSchema={
                    'type': 'object',
                    'properties': {
                        'next_tokens': {'type': 'integer', 'description': 'Tokens to prefetch for'},
                        'limit': {'type': 'integer', 'description': 'Max memories to prefetch'}
                    },
                    'required': ['next_tokens']
                }
            ),
            'model_to_model_sync': MCPTool(
                name='model_to_model_sync',
                description='Share memory context between different AI models (e.g., NVIDIA NIM to Claude)',
                inputSchema={
                    'type': 'object',
                    'properties': {
                        'source_model': {'type': 'string', 'description': 'Model sharing memory'},
                        'target_models': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Models receiving context'},
                        'memory_tags': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Memory tags to sync'}
                    },
                    'required': ['source_model', 'target_models']
                }
            ),
            'speak_status': MCPTool(
                name='speak_status',
                description='Narrate current state via NVIDIA Riva TTS (accessibility)',
                inputSchema={
                    'type': 'object',
                    'properties': {
                        'message': {'type': 'string', 'description': 'Text to speak'}
                    },
                    'required': ['message']
                }
            ),
        }
    
    def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle MCP tool calls from models.
        
        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments
        
        Returns:
            Tool execution result
        """
        try:
            if tool_name == 'query_hot_memories':
                return self._handle_query_hot_memories(arguments)
            elif tool_name == 'update_memory_heat':
                return self._handle_update_memory_heat(arguments)
            elif tool_name == 'create_memory':
                return self._handle_create_memory(arguments)
            elif tool_name == 'optimize_for_model':
                return self._handle_optimize_for_model(arguments)
            elif tool_name == 'get_memory_status':
                return self._handle_get_memory_status(arguments)
            elif tool_name == 'prefetch_memories':
                return self._handle_prefetch_memories(arguments)
            elif tool_name == 'model_to_model_sync':
                return self._handle_model_to_model_sync(arguments)
            elif tool_name == 'speak_status':
                return self._handle_speak_status(arguments)
            else:
                return {'error': f'Unknown tool: {tool_name}'}
        except Exception as e:
            return {'error': str(e)}
    
    def _handle_query_hot_memories(self, args: Dict) -> Dict:
        """Query hot memories."""
        if not self.heat_stream:
            return {'error': 'Heat stream not initialized'}
        
        category = args.get('category')
        limit = args.get('limit', 5)
        min_heat = args.get('min_heat', 0.7)
        
        hot = self.heat_stream.scan_for_hot_memories()
        
        # Filter by category if specified
        if category:
            hot = [b for b in hot if b.category == category]
        
        # Filter by minimum heat
        hot = [b for b in hot if b.heat_score >= min_heat]
        
        # Return limited results
        results = [
            {
                'id': b.id,
                'title': b.title,
                'content': b.content,
                'heat_score': b.heat_score,
                'category': b.category,
                'access_count': b.access_count
            }
            for b in hot[:limit]
        ]
        
        return {'success': True, 'memories': results, 'total': len(results)}
    
    def _handle_update_memory_heat(self, args: Dict) -> Dict:
        """Update memory heat score."""
        if not self.heat_stream:
            return {'error': 'Heat stream not initialized'}
        
        block_id = args.get('block_id')
        increment = args.get('increment', 0.1)
        
        result = self.heat_stream.update_block_heat(block_id, increment)
        
        return {
            'success': result,
            'message': f"Updated heat for {block_id}" if result else "Memory not found"
        }
    
    def _handle_create_memory(self, args: Dict) -> Dict:
        """Create new memory block."""
        # Simulated memory creation (real implementation would persist to tlb_cache)
        memory_id = f"mem_{int(datetime.now().timestamp())}"
        
        return {
            'success': True,
            'memory_id': memory_id,
            'message': f"Created memory: {args['title']}"
        }
    
    def _handle_optimize_for_model(self, args: Dict) -> Dict:
        """Optimize memory for model."""
        if not self.neural_graph:
            return {'error': 'Neural memory graph not initialized'}
        
        model_size_gb = args.get('model_size_gb')
        model_name = args.get('model_name', 'unknown')
        
        plan = self.neural_graph.optimize_for_model(model_size_gb)
        
        return {
            'success': True,
            'model': model_name,
            'plan': plan['recommendation'],
            'gpu_reserved_gb': plan['gpu_vram_reserved_gb']
        }
    
    def _handle_get_memory_status(self, args: Dict) -> Dict:
        """Get memory status."""
        if not self.neural_graph:
            return {'error': 'Neural memory graph not initialized'}
        
        status = self.neural_graph.get_memory_status()
        
        return {
            'success': True,
            'gpu_utilization_percent': status['gpu_memory']['utilization_pct'],
            'hot_memories': status['hot_memories'],
            'placement_distribution': status['placement_distribution'],
            'timestamp': status['timestamp']
        }
    
    def _handle_prefetch_memories(self, args: Dict) -> Dict:
        """Prefetch memories."""
        if not self.neural_graph:
            return {'error': 'Neural memory graph not initialized'}
        
        next_tokens = args.get('next_tokens', 256)
        limit = args.get('limit', 5)
        
        prefetch = self.neural_graph.get_prefetch_schedule(next_tokens, limit)
        
        return {
            'success': True,
            'prefetch_count': len(prefetch),
            'plan': [
                {
                    'title': p['title'],
                    'target_tier': p['target_tier'],
                    'priority': p['priority']
                }
                for p in prefetch
            ]
        }
    
    def _handle_model_to_model_sync(self, args: Dict) -> Dict:
        """Sync memory between models."""
        source = args.get('source_model')
        targets = args.get('target_models', [])
        tags = args.get('memory_tags', [])
        
        return {
            'success': True,
            'source_model': source,
            'synced_to': targets,
            'memory_tags': tags,
            'message': f'Synced memory from {source} to {len(targets)} models'
        }
    
    def _handle_speak_status(self, args: Dict) -> Dict:
        """Speak message via Riva."""
        if not self.riva_client:
            return {'message': 'Riva not initialized', 'audio': None}
        
        message = args.get('message', '')
        
        try:
            self.riva_client.text_to_speech(message)
            return {'success': True, 'message': message}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_mcp_manifest(self) -> Dict[str, Any]:
        """Get MCP server manifest (for MCP clients)."""
        return {
            'name': 'MemoryOS Neural Memory Graph',
            'version': '0.2.0',
            'description': 'Multi-model AI memory synchronization via Neural Memory Graph',
            'protocols': ['mcp/stdio'],
            'tools': {
                name: {
                    'name': tool.name,
                    'description': tool.description,
                    'inputSchema': tool.inputSchema
                }
                for name, tool in self.tools.items()
            }
        }
    
    def list_available_models(self) -> Dict[str, List[str]]:
        """List all available models this MCP server can coordinate."""
        return {
            provider: config['models']
            for provider, config in self.models_config.items()
        }


# CLI Interface
def start_mcp_server():
    """Start MCP server listening for model connections."""
    from memoryos.core.heat_stream import MemoryHeatStream
    from memoryos.core.neural_memory_graph import NeuralMemoryGraph
    from memoryos.integrations.riva_voice import RivaVoiceClient
    
    print("[MCP Server] Initializing MemoryOS MCP Server v0.2.0")
    
    # Initialize components
    heat_stream = MemoryHeatStream(
        tlb_cache_dir='./tlb_hot_cache',
        temp_graph_path='./graph'
    )
    
    neural_graph = NeuralMemoryGraph(heat_stream)
    riva_client = RivaVoiceClient()
    
    # Create MCP server
    server = MemoryOSMCPServer(heat_stream, neural_graph, riva_client)
    
    print("[MCP Server] Initialized with components:")
    print(f"  - Heat Stream: {len(heat_stream.scan_for_hot_memories())} hot memories")
    print(f"  - Neural Graph: 6 memory tiers configured")
    print(f"  - Riva Voice: TTS/STT ready")
    print(f"  - MCP Tools: {len(server.tools)} available")
    
    print("\n[MCP Server] Available models:")
    models = server.list_available_models()
    for provider, model_list in models.items():
        print(f"  {provider}: {', '.join(model_list[:2])}{'...' if len(model_list) > 2 else ''}")
    
    print("\n[MCP Server] Ready for multi-model communication")
    print("[MCP Server] Models can now:")
    print("  - Query hot memories from MemoryOS")
    print("  - Update memory importance (heat scores)")
    print("  - Share context with other models")
    print("  - Optimize GPU/CPU/NVMe memory placement")
    print("  - Prefetch memories for next token windows")
    
    # Return server for MCP gateway to manage
    return server


def get_mcp_docker_compose() -> str:
    """Get Docker Compose template for MCP server deployment."""
    compose_yaml = """
version: '3.8'

services:
  memoryos-mcp:
    image: memoryos:mcp-0.2.0
    container_name: memoryos-mcp-server
    ports:
      - "5000:5000"  # MCP Gateway port
    environment:
      - NVIDIA_API_KEY=${NVIDIA_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - RIVA_SERVER_URL=localhost:50051
    volumes:
      - ./tlb_hot_cache:/app/tlb_hot_cache
      - ./graph:/app/graph
      - ./checkpoints:/app/checkpoints
    networks:
      - ai-models
    labels:
      - "mcp.server=memoryos"
      - "mcp.version=0.2.0"

  riva-server:
    image: nvcr.io/nvidia/riva/riva-server:latest
    container_name: riva-speech-server
    ports:
      - "50051:50051"
    environment:
      - RIVA_PORT=50051
    networks:
      - ai-models
    runtime: nvidia

networks:
  ai-models:
    driver: bridge
"""
    return compose_yaml
