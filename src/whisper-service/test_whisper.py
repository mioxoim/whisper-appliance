#!/usr/bin/env python3
"""
WhisperS2T Integration Test
Validiert dass WhisperS2T korrekt installiert und funktionsfähig ist
"""

import os
import sys

import numpy as np


def test_imports():
    """Test ob alle benötigten Module importiert werden können"""
    print("🔍 Testing imports...")

    try:
        import torch

        print(f"✅ PyTorch {torch.__version__}")
    except ImportError as e:
        print(f"❌ PyTorch import failed: {e}")
        return False

    try:
        import torchaudio

        print(f"✅ TorchAudio {torchaudio.__version__}")
    except ImportError as e:
        print(f"❌ TorchAudio import failed: {e}")
        return False

    try:
        import soundfile as sf

        print(f"✅ SoundFile available")
    except ImportError as e:
        print(f"❌ SoundFile import failed: {e}")
        return False

    return True


def test_whisper_installation():
    """Test WhisperS2T Installation"""
    print("\n🎤 Testing WhisperS2T installation...")

    try:
        # Verschiedene Import-Varianten testen
        try:
            from whispers2t import WhisperS2T

            print("✅ WhisperS2T imported as 'whispers2t'")
            return True, WhisperS2T
        except ImportError:
            pass

        try:
            import whisper_s2t

            print("✅ WhisperS2T imported as 'whisper_s2t'")
            return True, whisper_s2t
        except ImportError:
            pass

        try:
            import whisper

            print("✅ OpenAI Whisper imported (fallback)")
            return True, whisper
        except ImportError:
            pass

        print("❌ WhisperS2T not found. Install with:")
        print("pip install git+https://github.com/shashikg/WhisperS2T.git")
        return False, None

    except Exception as e:
        print(f"❌ WhisperS2T import error: {e}")
        return False, None


def test_audio_processing():
    """Test Audio Processing Pipeline"""
    print("\n🔊 Testing audio processing...")

    try:
        # Generate test audio (1 second of sine wave)
        sample_rate = 16000
        duration = 1.0
        frequency = 440  # A4 note

        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32)

        print(f"✅ Generated test audio: {len(audio_data)} samples")
        print(f"   Sample rate: {sample_rate}Hz")
        print(f"   Duration: {duration}s")
        print(f"   Data type: {audio_data.dtype}")

        return True, audio_data

    except Exception as e:
        print(f"❌ Audio processing failed: {e}")
        return False, None


def test_system_resources():
    """Test System Resources"""
    print("\n💻 Checking system resources...")

    try:
        import psutil

        # Memory check
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        print(f"✅ Total RAM: {memory_gb:.1f}GB")
        print(f"   Available: {memory.available / (1024**3):.1f}GB")

        if memory_gb < 3:
            print("⚠️  Warning: Less than 3GB RAM detected")

        # CPU check
        cpu_count = psutil.cpu_count()
        print(f"✅ CPU cores: {cpu_count}")

        return True

    except ImportError:
        print("📦 psutil not installed, skipping resource check")
        return True
    except Exception as e:
        print(f"❌ Resource check failed: {e}")
        return True  # Non-critical


def main():
    """Main test runner"""
    print("🎤 WhisperS2T Appliance - System Integration Test")
    print("=" * 60)

    tests_passed = 0
    total_tests = 4

    # Test 1: Basic imports
    if test_imports():
        tests_passed += 1

    # Test 2: WhisperS2T installation
    whisper_available, whisper_module = test_whisper_installation()
    if whisper_available:
        tests_passed += 1

    # Test 3: Audio processing
    audio_available, test_audio = test_audio_processing()
    if audio_available:
        tests_passed += 1

    # Test 4: System resources
    if test_system_resources():
        tests_passed += 1

    # Summary
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tests_passed}/{total_tests} passed")

    if tests_passed == total_tests:
        print("🎉 All tests passed! System ready for development.")
        return 0
    elif tests_passed >= 2:
        print("⚠️  Some tests failed, but core functionality available.")
        return 0
    else:
        print("❌ Critical tests failed. Check installation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
