#!/usr/bin/env python3
"""
WhisperS2T Integration with faster-whisper
Real Speech-to-Text functionality for the appliance
"""

import asyncio
import logging
import threading
import time
from collections import deque
from typing import Any, Dict, List, Optional

import numpy as np
from faster_whisper import WhisperModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WhisperManager:
    def __init__(self):
        self.model = None
        self.current_model_name = None
        self.available_models = ["tiny", "base", "small", "medium", "large-v3"]
        self.device = "cpu"
        self.compute_type = "int8"  # Optimize for low memory
        self.model_loading = False

        # For real-time transcription
        self.transcription_active = False
        self.audio_buffer = deque(maxlen=50)  # 50 chunks buffer
        self.transcription_thread = None

    async def load_model(self, model_name: str) -> Dict[str, Any]:
        """Load a Whisper model asynchronously"""
        if model_name not in self.available_models:
            raise ValueError(f"Model {model_name} not available. Available: {self.available_models}")

        if self.model_loading:
            raise RuntimeError("Model is already being loaded")

        logger.info(f"Loading Whisper model: {model_name}")
        self.model_loading = True

        try:
            # Load model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            start_time = time.time()

            self.model = await loop.run_in_executor(None, self._load_model_sync, model_name)

            load_time = time.time() - start_time
            self.current_model_name = model_name
            self.model_loading = False

            logger.info(f"Model {model_name} loaded successfully in {load_time:.2f}s")

            return {
                "status": "success",
                "model": model_name,
                "load_time": round(load_time, 2),
                "device": self.device,
                "compute_type": self.compute_type,
            }

        except Exception as e:
            self.model_loading = False
            logger.error(f"Failed to load model {model_name}: {e}")
            raise

    def _load_model_sync(self, model_name: str):
        """Synchronous model loading"""
        return WhisperModel(
            model_name, device=self.device, compute_type=self.compute_type, download_root="./models"  # Local model storage
        )

    async def transcribe_audio(self, audio_data: np.ndarray, language: str = None) -> Dict[str, Any]:
        """Transcribe audio data"""
        if self.model is None:
            # Auto-load tiny model if none loaded
            await self.load_model("tiny")

        try:
            # Ensure audio is in correct format
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)

            # Normalize audio if needed
            if np.max(np.abs(audio_data)) > 1.0:
                audio_data = audio_data / np.max(np.abs(audio_data))

            # Run transcription in thread pool
            loop = asyncio.get_event_loop()
            start_time = time.time()

            result = await loop.run_in_executor(None, self._transcribe_sync, audio_data, language)

            transcription_time = time.time() - start_time

            return {
                "text": result["text"],
                "language": result["language"],
                "confidence": result.get("confidence", 0.0),
                "processing_time": round(transcription_time, 3),
                "model": self.current_model_name,
                "audio_length": len(audio_data) / 16000,  # Assume 16kHz
                "segments": result.get("segments", []),
            }

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return {"text": "", "language": "unknown", "confidence": 0.0, "error": str(e)}

    def _transcribe_sync(self, audio_data: np.ndarray, language: str = None) -> Dict[str, Any]:
        """Synchronous transcription"""
        try:
            # Transcribe with faster-whisper
            segments, info = self.model.transcribe(
                audio_data, language=language, beam_size=1, word_timestamps=True  # Faster transcription
            )

            # Collect all text segments
            full_text = ""
            segment_list = []

            for segment in segments:
                full_text += segment.text + " "
                segment_list.append(
                    {
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text,
                        "confidence": getattr(segment, "avg_logprob", 0.0),
                    }
                )

            return {
                "text": full_text.strip(),
                "language": info.language,
                "confidence": getattr(info, "language_probability", 0.0),
                "segments": segment_list,
            }

        except Exception as e:
            logger.error(f"Sync transcription error: {e}")
            return {"text": "", "language": "unknown", "confidence": 0.0, "error": str(e)}

    def get_model_info(self) -> Dict[str, Any]:
        """Get current model information"""
        return {
            "current_model": self.current_model_name,
            "available_models": self.available_models,
            "device": self.device,
            "compute_type": self.compute_type,
            "model_loaded": self.model is not None,
            "model_loading": self.model_loading,
        }


# Audio processing utilities
class AudioProcessor:
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.chunk_duration = 1.0  # 1 second chunks
        self.chunk_size = int(sample_rate * self.chunk_duration)

    def generate_test_audio(self, duration: float = 2.0, frequency: float = 440.0) -> np.ndarray:
        """Generate test audio for testing"""
        samples = int(self.sample_rate * duration)
        t = np.linspace(0, duration, samples)

        # Generate a simple sine wave
        audio = np.sin(2 * np.pi * frequency * t).astype(np.float32)

        # Add some envelope to make it more realistic
        envelope = np.exp(-t * 0.5)  # Decay envelope
        audio *= envelope

        return audio

    def preprocess_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """Preprocess audio for better transcription"""
        # Ensure float32
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)

        # Normalize
        if np.max(np.abs(audio_data)) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))

        # Simple noise gate (remove very quiet parts)
        threshold = 0.01
        audio_data[np.abs(audio_data) < threshold] = 0

        return audio_data


# Test functions
async def test_whisper_integration():
    """Test the WhisperManager integration"""
    print("🧪 Testing WhisperManager Integration")
    print("=" * 50)

    # Initialize manager and audio processor
    whisper_manager = WhisperManager()
    audio_processor = AudioProcessor()

    # Test 1: Model loading
    print("📦 Testing model loading...")
    try:
        result = await whisper_manager.load_model("tiny")
        print(f"✅ Model loaded: {result}")
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        return False

    # Test 2: Generate test audio
    print("\n🔊 Generating test audio...")
    test_audio = audio_processor.generate_test_audio(duration=3.0)
    print(f"✅ Generated {len(test_audio)} samples ({len(test_audio)/16000:.1f}s)")

    # Test 3: Transcription
    print("\n🎤 Testing transcription...")
    try:
        result = await whisper_manager.transcribe_audio(test_audio)
        print(f"✅ Transcription result:")
        print(f"   Text: '{result['text']}'")
        print(f"   Language: {result['language']}")
        print(f"   Confidence: {result['confidence']:.3f}")
        print(f"   Processing time: {result['processing_time']:.3f}s")
        print(f"   Model: {result['model']}")
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        return False

    # Test 4: Model info
    print("\n📊 Model information:")
    info = whisper_manager.get_model_info()
    for key, value in info.items():
        print(f"   {key}: {value}")

    print("\n🎉 All tests passed! WhisperManager is ready.")
    return True


if __name__ == "__main__":
    # Run the test
    asyncio.run(test_whisper_integration())
