#!/usr/bin/env python3
"""
Audio Input Manager für WhisperS2T Appliance (Fallback-Version)
Simuliert Audio-Input wenn kein Mikrofon verfügbar ist
"""

import numpy as np
import asyncio
import time
import queue
import logging
from typing import Dict, List, Optional, Callable
from collections import deque

logger = logging.getLogger(__name__)

class AudioInputManager:
    def __init__(self, sample_rate: int = 16000, channels: int = 1, chunk_duration: float = 1.0):
        """
        Initialize Audio Input Manager with fallback support
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        
        # Audio streaming state
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.audio_buffer = deque(maxlen=10)
        
        # Device management
        self.input_devices = []
        self.current_device = None
        self.hardware_available = False
        
        # Callbacks
        self.on_audio_chunk: Optional[Callable] = None
        self.on_recording_start: Optional[Callable] = None
        self.on_recording_stop: Optional[Callable] = None
        
        # Try to detect real audio devices
        self._detect_audio_devices()
    
    def _detect_audio_devices(self):
        """Detect available audio input devices"""
        try:
            # Try to import sounddevice
            import sounddevice as sd
            
            devices = sd.query_devices()
            self.input_devices = []
            
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    device_info = {
                        'index': i,
                        'name': device['name'],
                        'channels': device['max_input_channels'],
                        'sample_rate': device['default_samplerate'],
                        'type': 'hardware'
                    }
                    self.input_devices.append(device_info)
            
            if self.input_devices:
                self.current_device = self.input_devices[0]
                self.hardware_available = True
                logger.info(f"Found {len(self.input_devices)} hardware audio devices")
            else:
                self._setup_fallback_devices()
                
        except (ImportError, OSError) as e:
            logger.warning(f"Hardware audio not available: {e}")
            self._setup_fallback_devices()
    
    def _setup_fallback_devices(self):
        """Setup simulated audio devices for testing"""
        self.input_devices = [
            {
                'index': 0,
                'name': 'Simulated Microphone (Test Mode)',
                'channels': 1,
                'sample_rate': 16000,
                'type': 'simulated'
            },
            {
                'index': 1,
                'name': 'Demo Audio Generator',
                'channels': 1,
                'sample_rate': 16000,
                'type': 'simulated'
            }
        ]
        self.current_device = self.input_devices[0]
        self.hardware_available = False
        logger.info("Using simulated audio devices (no hardware microphone)")
    
    def get_device_status(self) -> Dict:
        """Get current audio device status"""
        return {
            "devices_available": len(self.input_devices),
            "input_devices": self.input_devices,
            "current_device": self.current_device,
            "is_recording": self.is_recording,
            "hardware_available": self.hardware_available,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "chunk_duration": self.chunk_duration
        }
    
    def has_microphone(self) -> bool:
        """Check if microphone is available (real or simulated)"""
        return len(self.input_devices) > 0
    
    def _generate_test_audio(self, duration: float = 1.0) -> np.ndarray:
        """Generate test audio for simulation"""
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        # Generate speech-like audio with multiple frequencies
        audio = (
            0.3 * np.sin(2 * np.pi * 220 * t) +  # Base tone
            0.2 * np.sin(2 * np.pi * 440 * t) +  # Harmonic
            0.1 * np.sin(2 * np.pi * 880 * t) +  # Higher harmonic
            0.05 * np.random.normal(0, 1, samples)  # Noise
        )
        
        # Apply envelope to make it more speech-like
        envelope = np.exp(-t * 0.5) * (1 + 0.5 * np.sin(2 * np.pi * 3 * t))
        audio *= envelope
        
        # Normalize
        audio = audio / np.max(np.abs(audio)) * 0.3
        
        return audio.astype(np.float32)
    
    def start_recording(self) -> bool:
        """Start audio recording (real or simulated)"""
        if self.is_recording:
            logger.warning("Already recording")
            return True
        
        if not self.has_microphone():
            logger.error("No audio input available")
            return False
        
        try:
            if self.hardware_available:
                # Try real hardware recording
                return self._start_hardware_recording()
            else:
                # Start simulated recording
                return self._start_simulated_recording()
                
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            return False
    
    def _start_hardware_recording(self) -> bool:
        """Start hardware recording"""
        try:
            import sounddevice as sd
            
            device_index = self.current_device['index']
            
            def audio_callback(indata, frames, time, status):
                if status:
                    logger.warning(f"Audio callback status: {status}")
                
                # Convert to mono
                if indata.shape[1] > 1:
                    audio_data = np.mean(indata, axis=1)
                else:
                    audio_data = indata[:, 0]
                
                self.audio_buffer.append(audio_data.copy())
                
                try:
                    self.audio_queue.put_nowait(audio_data.copy())
                except queue.Full:
                    try:
                        self.audio_queue.get_nowait()
                        self.audio_queue.put_nowait(audio_data.copy())
                    except queue.Empty:
                        pass
            
            self.audio_stream = sd.InputStream(
                device=device_index,
                channels=self.channels,
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                callback=audio_callback,
                dtype=np.float32
            )
            
            self.audio_stream.start()
            self.is_recording = True
            
            logger.info(f"Started hardware recording: {self.current_device['name']}")
            
            if self.on_recording_start:
                self.on_recording_start()
            
            return True
            
        except Exception as e:
            logger.error(f"Hardware recording failed: {e}")
            return False
    
    def _start_simulated_recording(self) -> bool:
        """Start simulated recording"""
        self.is_recording = True
        
        # Start background thread for audio generation
        import threading
        
        def generate_audio():
            while self.is_recording:
                # Generate audio chunk
                audio_chunk = self._generate_test_audio(self.chunk_duration)
                self.audio_buffer.append(audio_chunk)
                
                try:
                    self.audio_queue.put_nowait(audio_chunk)
                except queue.Full:
                    try:
                        self.audio_queue.get_nowait()
                        self.audio_queue.put_nowait(audio_chunk)
                    except queue.Empty:
                        pass
                
                time.sleep(self.chunk_duration)
        
        self.audio_thread = threading.Thread(target=generate_audio, daemon=True)
        self.audio_thread.start()
        
        logger.info(f"Started simulated recording: {self.current_device['name']}")
        
        if self.on_recording_start:
            self.on_recording_start()
        
        return True
    
    def stop_recording(self) -> bool:
        """Stop audio recording"""
        if not self.is_recording:
            return True
        
        try:
            self.is_recording = False
            
            if self.hardware_available and hasattr(self, 'audio_stream'):
                self.audio_stream.stop()
                self.audio_stream.close()
                del self.audio_stream
            
            # Clear queue
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                except queue.Empty:
                    break
            
            logger.info("Stopped recording")
            
            if self.on_recording_stop:
                self.on_recording_stop()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            return False
    
    def get_audio_chunk(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """Get next audio chunk from queue"""
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    async def get_audio_chunk_async(self, timeout: float = 1.0) -> Optional[np.ndarray]:
        """Get next audio chunk asynchronously"""
        loop = asyncio.get_event_loop()
        
        try:
            return await loop.run_in_executor(
                None, 
                lambda: self.audio_queue.get(timeout=timeout)
            )
        except queue.Empty:
            return None
    
    def get_audio_level(self) -> float:
        """Get current audio input level (0.0 to 1.0)"""
        if not self.audio_buffer:
            return 0.0
        
        # Get RMS of last audio chunk
        latest_chunk = self.audio_buffer[-1]
        rms = np.sqrt(np.mean(latest_chunk ** 2))
        
        # Normalize to 0-1 range
        level = min(rms / 0.1, 1.0)
        return level
    
    def get_recent_audio(self, duration: float = 5.0) -> np.ndarray:
        """Get recent audio data for transcription"""
        if not self.audio_buffer:
            return np.array([], dtype=np.float32)
        
        chunks_needed = int(duration / self.chunk_duration)
        chunks_needed = min(chunks_needed, len(self.audio_buffer))
        
        if chunks_needed == 0:
            return np.array([], dtype=np.float32)
        
        recent_chunks = list(self.audio_buffer)[-chunks_needed:]
        audio_data = np.concatenate(recent_chunks)
        
        return audio_data
    
    def test_microphone(self) -> Dict:
        """Test microphone functionality"""
        test_result = {
            "microphone_detected": self.has_microphone(),
            "device_count": len(self.input_devices),
            "current_device": self.current_device,
            "hardware_available": self.hardware_available,
            "test_recording": False,
            "audio_level": 0.0,
            "error": None
        }
        
        if not self.has_microphone():
            test_result["error"] = "No audio input available"
            return test_result
        
        try:
            # Try a short test recording
            original_recording = self.is_recording
            
            if not original_recording:
                if self.start_recording():
                    test_result["test_recording"] = True
                    
                    # Wait for audio
                    time.sleep(2.0)
                    
                    # Get audio level
                    test_result["audio_level"] = self.get_audio_level()
                    
                    self.stop_recording()
                else:
                    test_result["error"] = "Failed to start test recording"
            else:
                test_result["test_recording"] = True
                test_result["audio_level"] = self.get_audio_level()
                
        except Exception as e:
            test_result["error"] = str(e)
        
        return test_result

# Test function
async def test_audio_system():
    """Test the audio input system"""
    print("🎤 Testing Audio Input System")
    print("=" * 40)
    
    # Initialize audio manager
    audio_manager = AudioInputManager()
    
    # Test device detection
    status = audio_manager.get_device_status()
    print(f"📱 Devices found: {status['devices_available']}")
    print(f"🔧 Hardware available: {status['hardware_available']}")
    
    if status['current_device']:
        print(f"🎙️ Current device: {status['current_device']['name']}")
        print(f"📡 Type: {status['current_device']['type']}")
    else:
        print("❌ No audio input available")
        return False
    
    # Test microphone
    print("\n🧪 Testing microphone...")
    test_result = audio_manager.test_microphone()
    
    for key, value in test_result.items():
        print(f"   {key}: {value}")
    
    if test_result.get("test_recording"):
        print("✅ Audio input test successful!")
        
        # Test actual audio capture
        print("\n🎧 Testing audio capture...")
        if audio_manager.start_recording():
            print("Recording for 3 seconds...")
            
            for i in range(3):
                chunk = audio_manager.get_audio_chunk(timeout=2.0)
                if chunk is not None:
                    level = np.sqrt(np.mean(chunk ** 2))
                    print(f"  Chunk {i+1}: {len(chunk)} samples, RMS: {level:.4f}")
                else:
                    print(f"  Chunk {i+1}: No audio received")
            
            audio_manager.stop_recording()
            print("✅ Audio capture test completed!")
        
        return True
    else:
        print("❌ Audio input test failed!")
        return False

if __name__ == "__main__":
    # Run the test
    asyncio.run(test_audio_system())
