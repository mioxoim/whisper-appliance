# WHISPER MODEL CHECKSUM FIX

## 🔧 **BEKANNTES PROBLEM AUS LOGS IDENTIFIZIERT:**

```
UserWarning: /home/whisper/.cache/whisper/base.pt exists, but the SHA256 checksum does not match; re-downloading the file
```

**URSACHE:** Corrupted Whisper model cache

## **FIX-COMMANDS FÜR USER:**

```bash
# 1. Clear corrupted Whisper model cache
docker exec whisper-appliance rm -rf /home/whisper/.cache/whisper/

# 2. Force clean model re-download
docker exec whisper-appliance python3 -c "
import whisper
print('🔄 Re-downloading Whisper base model...')
model = whisper.load_model('base')
print('✅ Model loaded successfully:', type(model))
"

# 3. Restart service to use clean model
docker exec whisper-appliance systemctl restart whisper-appliance

# 4. Verify no more checksum warnings
docker logs whisper-appliance --since="1m" | grep -i "checksum\|warning"
```

## **VERIFICATION TESTS:**

```bash
# Test model functionality directly
docker exec whisper-appliance python3 -c "
import whisper
import numpy as np

# Load model
model = whisper.load_model('base')
print('✅ Model loaded')

# Create test audio (5 seconds of silence)
test_audio = np.zeros(80000)  # 5 seconds at 16kHz
result = model.transcribe(test_audio)
print('✅ Model transcription test:', result.get('text', 'SUCCESS'))
"
```
