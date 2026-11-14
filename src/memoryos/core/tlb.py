import time
import json
from pathlib import Path

class MemTLB:
    def __init__(self, max_hot=5):
        self.hot_cache = {}
        self.cold_storage = {}
        self.max_hot = max_hot

    def access(self, memory_id: str):
        if memory_id in self.hot_cache:
            block = self.hot_cache[memory_id]
            block['access_count'] += 1
            block['last_access'] = time.time()
            block['heat'] = block['access_count'] * (0.5 ** ((time.time() - block['last_access']) / 86400))
            return block['content']

        block = self.cold_storage.get(memory_id)
        if block:
            block['access_count'] += 1
            block['last_access'] = time.time()
            block['heat'] = block['access_count'] * (0.5 ** ((time.time() - block['last_access']) / 86400))
            if len(self.hot_cache) >= self.max_hot:
                coldest = min(self.hot_cache.values(), key=lambda x: x['heat'])
                self.cold_storage[coldest['id']] = coldest
                del self.hot_cache[coldest['id']]
            self.hot_cache[memory_id] = block
            return block['content']
        return None

    def add_block(self, memory_id: str, content: str):
        self.cold_storage[memory_id] = {
            "id": memory_id, "content": content, "access_count": 0, "last_access": 0, "heat": 0.0
        }
