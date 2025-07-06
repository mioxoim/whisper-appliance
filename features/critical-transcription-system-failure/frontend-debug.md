# BROWSER FRONTEND DEBUG STRATEGY

## 🌐 **FRONTEND TRANSCRIPTION DEBUGGING**

### **BROWSER CONSOLE TESTING COMMANDS:**

```javascript
// 1. TEST MICROPHONE ACCESS
navigator.mediaDevices.getUserMedia({audio: true})
  .then(stream => {
    console.log('✅ Microphone access granted');
    console.log('Audio tracks:', stream.getAudioTracks());
    stream.getTracks().forEach(track => track.stop());
  })
  .catch(err => console.error('❌ Microphone access denied:', err));

// 2. TEST DEVICE ENUMERATION  
navigator.mediaDevices.enumerateDevices()
  .then(devices => {
    const audioInputs = devices.filter(d => d.kind === 'audioinput');
    console.log('✅ Audio input devices:', audioInputs);
  })
  .catch(err => console.error('❌ Device enumeration failed:', err));

// 3. TEST WEBSOCKET CONNECTION
const wsUrl = 'wss://' + window.location.host + '/api/live-speech';
console.log('Testing WebSocket:', wsUrl);

const ws = new WebSocket(wsUrl);
ws.onopen = () => console.log('✅ WebSocket connected');
ws.onclose = (e) => console.log('❌ WebSocket closed:', e.code, e.reason);
ws.onerror = (err) => console.error('❌ WebSocket error:', err);
ws.onmessage = (msg) => console.log('📨 WebSocket message:', msg.data);

// Close test connection
setTimeout(() => ws.close(), 5000);
```

### **COMMON ISSUES CHECKLIST:**

1. **HTTPS Certificate Issues:**
   - Browser shows "Not Secure" warning
   - Click "Advanced" → "Continue to localhost"
   - Self-signed certificates block audio access

2. **Microphone Permission Issues:**
   - Browser blocks getUserMedia() without permission
   - Check address bar for microphone icon
   - Grant microphone permissions explicitly

3. **WebSocket Connection Issues:**
   - Mixed content warnings (HTTP vs HTTPS)
   - CORS policy blocks cross-origin WebSocket
   - Network connectivity problems

### **USER TESTING SEQUENCE:**

```bash
# 1. Open browser to container
firefox https://192.168.178.67:5001 &

# 2. Open Developer Tools (F12)
# 3. Go to Console Tab
# 4. Paste and run JavaScript commands above
# 5. Try microphone/recording functionality
# 6. Report all console output
```
