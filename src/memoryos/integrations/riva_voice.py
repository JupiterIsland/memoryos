"""
MemoryOS Voice Integration v0.2.0
==================================
NVIDIA Riva-powered voice interface for Neural Memory Graph.
Listen to hot memories, speak commands, and interact hands-free.

Features:
- Text-to-speech (TTS) for hot memory playback
- Speech-to-text (STT) for voice commands
- Audio streaming with GPU acceleration
- Memory narration for accessibility
"""

import os
import json
import time
from pathlib import Path
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass
import threading
import queue
from datetime import datetime


@dataclass
class VoiceConfig:
    """Configuration for Riva voice interface."""
    language_code: str = "en-US"
    sample_rate: int = 16000
    voice_name: str = "English-US.Female-1"  # NVIDIA Riva voice
    speaking_rate: float = 1.0
    enable_tts: bool = True
    enable_stt: bool = True
    audio_output_path: Optional[str] = None


class RivaVoiceClient:
    """
    NVIDIA Riva voice client for MemoryOS.
    Provides TTS and STT capabilities for memory interactions.
    """
    
    def __init__(self, 
                 riva_server_url: str = None,
                 config: VoiceConfig = None):
        """
        Initialize Riva voice client.
        
        Args:
            riva_server_url: RIVA server endpoint (default: localhost:50051)
            config: VoiceConfig object for customization
        """
        self.riva_url = riva_server_url or os.getenv("RIVA_SERVER_URL", "localhost:50051")
        self.config = config or VoiceConfig()
        self.audio_queue = queue.Queue()
        self.is_listening = False
        
        print(f"[Riva] Initialized. Server: {self.riva_url}")
        print(f"[Riva] Voice: {self.config.voice_name} | Sample Rate: {self.config.sample_rate}Hz")
    
    def text_to_speech(self, text: str, save_path: Optional[str] = None) -> bytes:
        """
        Convert text to speech using NVIDIA Riva.
        
        Args:
            text: Text to synthesize
            save_path: Optional path to save audio file
        
        Returns:
            Raw audio bytes (PCM)
        """
        print(f"[TTS] Synthesizing: '{text[:100]}...'")
        
        # In production, this calls Riva gRPC API:
        # client = riva.client.SpeechSynthesisServiceClient("grpc://localhost:50051")
        # response = client.synthesize(text, voice_name=self.config.voice_name)
        
        # For demo, simulate audio generation
        audio_data = self._simulate_audio_synthesis(text)
        
        if save_path:
            self._save_audio(audio_data, save_path)
            print(f"[TTS] Saved to {save_path}")
        
        return audio_data
    
    def speech_to_text(self, audio_path: str) -> str:
        """
        Convert speech to text using NVIDIA Riva.
        
        Args:
            audio_path: Path to audio file
        
        Returns:
            Transcribed text
        """
        print(f"[STT] Transcribing: {audio_path}")
        
        # In production, this calls Riva gRPC API:
        # with open(audio_path, 'rb') as f:
        #     audio_data = f.read()
        # client = riva.client.SpeechRecognitionServiceClient("grpc://localhost:50051")
        # response = client.recognize(audio=audio_data)
        
        # For demo, simulate transcription
        transcription = self._simulate_speech_recognition(audio_path)
        
        print(f"[STT] Transcribed: '{transcription}'")
        return transcription
    
    def narrate_memory(self, memory_block: Dict) -> str:
        """
        Generate natural narration for a memory block.
        
        Args:
            memory_block: Memory block dict with title, content, etc.
        
        Returns:
            Path to audio file
        """
        title = memory_block.get('title', 'Unknown')
        content = memory_block.get('content', '')
        category = memory_block.get('category', '')
        heat = memory_block.get('heat_score', 0)
        
        # Create natural narration
        narration = f"Memory: {title}. Category: {category}. Heat: {heat:.0%}. Content: {content}"
        
        output_path = self.config.audio_output_path or f"./audio/{memory_block['id']}_narration.wav"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        audio = self.text_to_speech(narration, output_path)
        
        print(f"[Narrate] Generated audio for: {title}")
        return output_path
    
    def listen_for_command(self, timeout_seconds: float = 10.0) -> str:
        """
        Listen for voice command with timeout.
        
        Args:
            timeout_seconds: Seconds to listen before timing out
        
        Returns:
            Recognized command text
        """
        print(f"[Listen] Listening for command... (timeout: {timeout_seconds}s)")
        
        # In production:
        # streaming_config = riva.client.StreamingRecognitionConfig(...)
        # responses = client.streaming_recognize(streaming_config, audio_generator())
        
        # For demo, simulate command recognition
        command = self._simulate_listen(timeout_seconds)
        return command
    
    def _simulate_audio_synthesis(self, text: str) -> bytes:
        """Simulate audio synthesis for demo."""
        # In real implementation, returns actual PCM audio from Riva
        return b"PCM_AUDIO_SIMULATION" + text.encode()[:100]
    
    def _simulate_speech_recognition(self, audio_path: str) -> str:
        """Simulate speech recognition for demo."""
        # In real implementation, returns transcribed text from Riva
        return "show me hot memories in architecture category"
    
    def _simulate_listen(self, timeout: float) -> str:
        """Simulate listening for command."""
        time.sleep(0.5)  # Simulate listening delay
        return "sync hot cache"
    
    def _save_audio(self, audio_data: bytes, path: str):
        """Save audio data to file."""
        with open(path, 'wb') as f:
            f.write(audio_data)


class MemoryVoiceInterface:
    """
    Voice interface for MemoryOS Heat Stream.
    Integrates Riva TTS/STT with Neural Memory Graph.
    """
    
    def __init__(self, 
                 heat_stream,
                 riva_client: Optional[RivaVoiceClient] = None):
        """
        Initialize memory voice interface.
        
        Args:
            heat_stream: MemoryHeatStream instance
            riva_client: RivaVoiceClient (creates default if None)
        """
        self.heat_stream = heat_stream
        self.riva = riva_client or RivaVoiceClient()
        self.command_handlers: Dict[str, Callable] = {
            'sync': self.handle_sync_command,
            'list': self.handle_list_command,
            'read': self.handle_read_command,
            'update': self.handle_update_command,
            'search': self.handle_search_command,
        }
    
    def handle_sync_command(self, *args, **kwargs) -> str:
        """Handle 'sync hot cache' voice command."""
        print("[Voice] Executing: Sync hot cache")
        hot = self.heat_stream.scan_for_hot_memories()
        response = f"Synchronized {len(hot)} hot memories. Top memory: {hot[0].title if hot else 'None'}"
        self.riva.text_to_speech(response)
        return response
    
    def handle_list_command(self, *args, **kwargs) -> str:
        """Handle 'list memories' voice command."""
        print("[Voice] Executing: List memories")
        hot = self.heat_stream.scan_for_hot_memories()
        titles = [b.title for b in hot[:5]]
        response = f"Found {len(hot)} hot memories: {', '.join(titles)}"
        self.riva.text_to_speech(response)
        return response
    
    def handle_read_command(self, memory_id: str, *args, **kwargs) -> str:
        """Handle 'read memory' voice command."""
        print(f"[Voice] Executing: Read memory {memory_id}")
        # Would look up memory and narrate
        response = f"Reading memory {memory_id}"
        self.riva.text_to_speech(response)
        return response
    
    def handle_update_command(self, memory_id: str, heat_increment: float = 0.1, *args, **kwargs) -> str:
        """Handle 'increase heat' voice command."""
        print(f"[Voice] Executing: Update heat for {memory_id}")
        self.heat_stream.update_block_heat(memory_id, heat_increment)
        response = f"Increased heat for memory {memory_id}"
        self.riva.text_to_speech(response)
        return response
    
    def handle_search_command(self, query: str, *args, **kwargs) -> str:
        """Handle 'search memories' voice command."""
        print(f"[Voice] Executing: Search for '{query}'")
        # Would search memory index
        response = f"Searching for memories matching {query}"
        self.riva.text_to_speech(response)
        return response
    
    def voice_loop(self, interactive: bool = True):
        """
        Start voice interaction loop.
        
        Args:
            interactive: If True, listen for commands; if False, narrate hot memories
        """
        print("[Voice] Starting voice interface loop...")
        
        if interactive:
            while True:
                try:
                    command = self.riva.listen_for_command(timeout_seconds=10.0)
                    
                    if not command or command.lower() in ['quit', 'exit', 'bye']:
                        self.riva.text_to_speech("Goodbye!")
                        break
                    
                    self._route_command(command)
                    
                except KeyboardInterrupt:
                    print("\n[Voice] Interrupted by user")
                    break
                except Exception as e:
                    print(f"[Voice] Error: {e}")
        else:
            # Narration mode - read hot memories aloud
            hot = self.heat_stream.scan_for_hot_memories()
            for block in hot[:3]:
                block_dict = {
                    'id': block.id,
                    'title': block.title,
                    'content': block.content,
                    'category': block.category,
                    'heat_score': block.heat_score
                }
                self.riva.narrate_memory(block_dict)
                time.sleep(1)
    
    def _route_command(self, command: str):
        """Route voice command to appropriate handler."""
        command_lower = command.lower()
        
        for cmd_key, handler in self.command_handlers.items():
            if cmd_key in command_lower:
                handler(command)
                return
        
        # Unknown command
        response = f"I didn't understand '{command}'. Try 'sync', 'list', 'read', or 'search'."
        self.riva.text_to_speech(response)


# CLI Interface
def voice_sync_command() -> str:
    """CLI: Sync hot cache with voice confirmation."""
    from memoryos.core.heat_stream import MemoryHeatStream
    
    heat_stream = MemoryHeatStream()
    interface = MemoryVoiceInterface(heat_stream)
    return interface.handle_sync_command()


def voice_narrate_hot_memories(limit: int = 3):
    """CLI: Narrate top hot memories using Riva TTS."""
    from memoryos.core.heat_stream import MemoryHeatStream
    
    heat_stream = MemoryHeatStream()
    interface = MemoryVoiceInterface(heat_stream)
    
    hot = heat_stream.scan_for_hot_memories()
    for block in hot[:limit]:
        block_dict = {
            'id': block.id,
            'title': block.title,
            'content': block.content,
            'category': block.category,
            'heat_score': block.heat_score
        }
        audio_path = interface.riva.narrate_memory(block_dict)
        print(f"[CLI] Audio saved: {audio_path}")


def voice_interactive_mode():
    """CLI: Start interactive voice command mode."""
    from memoryos.core.heat_stream import MemoryHeatStream
    
    heat_stream = MemoryHeatStream()
    interface = MemoryVoiceInterface(heat_stream)
    
    print("[Voice CLI] Starting interactive mode. Say commands like 'sync', 'list', 'read memory 1'")
    print("[Voice CLI] Say 'exit' or 'quit' to stop")
    
    interface.voice_loop(interactive=True)
