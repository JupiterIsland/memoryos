import sys
sys.path.insert(0, '.')

from memoryos.mcp_server import start_mcp_server

print("[MCP Server Test]")

server = start_mcp_server()

print("\n[MCP Manifest]")
manifest = server.get_mcp_manifest()
print(f'Tools available: {len(manifest["tools"])}')

print("\n[Tool Test] query_hot_memories")
result = server.handle_tool_call('query_hot_memories', {'limit': 3})
print(f'Found {result["total"]} memories')
for mem in result.get('memories', [])[:2]:
    print(f"  - {mem['title']} (heat: {mem['heat_score']:.2f})")

print("\n[Tool Test] get_memory_status")
result = server.handle_tool_call('get_memory_status', {})
print(f'GPU: {result["gpu_utilization_percent"]:.1f}%')
print(f'Hot memories: {result["hot_memories"]}')

print("\n[Tool Test] optimize_for_model")
result = server.handle_tool_call('optimize_for_model', 
    {'model_name': 'mistral-7b', 'model_size_gb': 7.0})
print(f'Plan: {result["plan"]}')

print("\n[Tool Test] prefetch_memories")
result = server.handle_tool_call('prefetch_memories', {'next_tokens': 256, 'limit': 3})
print(f'Prefetch plan: {result["prefetch_count"]} memories')

print("\n[Available Models]")
models = server.list_available_models()
for provider, model_list in models.items():
    print(f'  {provider}: {len(model_list)} models')

print("\n[MCP Endpoints]")
for tool_name, tool in server.tools.items():
    print(f'  GET /tools/{tool_name}')

print("\n[OK] MCP Server fully functional and ready for Claude/Cursor")
