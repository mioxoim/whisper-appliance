 dict):
    device_index = request.get('device_index')
    if device_index is not None:
        success = audio_manager.set_device(device_index)
        return {"success": success, "device": audio_manager.current_device}
    return {"success": False}

@app.post("/api/set-language")
async def set_language(request: dict):
    language = request.get('language')
    if language:
        success = whisper_manager.set_language(language)
        return {"success": success, "language": language}
    return {"success": False}

@app.websocket("/ws/live-audio")
async def websocket_endpoint(websocket: WebSocket):
    print("🔌 Enhanced WebSocket connection...")
    await websocket.accept()
    connected_clients.append(websocket)
    
    # Send enhanced welcome
    status = audio_manager.get_status()
    await websocket.send_text(json.dumps({
        "type": "connected",
        "message": f"Enhanced system ready! Device: {status['current_device']['name']}",
        "timestamp": datetime.now().isoformat(),
        "audio_status": status,
        "whisper_info": {
            "model": whisper_manager.current_model,
            "language": whisper_manager.current_language or "auto",
            "available_languages": whisper_manager.languages
        }
    }))
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            action = message.get('action')
            
            if action == "start_recording":
                if audio_manager.start_recording():
                    device_info = f"{audio_manager.current_device['name']}"
                    if audio_manager.current_device.get('language'):
                        device_info += f" ({audio_manager.current_device['language'].upper()})"
                    
                    await websocket.send_text(json.dumps({
                        "type": "recording_started",
                        "message": f"🎤 Recording with {device_info}",
                        "timestamp": datetime.now().isoformat(),
                        "device": audio_manager.current_device
                    }))
                    asyncio.create_task(transcription_loop(websocket))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Failed to start recording",
                        "timestamp": datetime.now().isoformat()
                    }))
            
            elif action == "stop_recording":
                audio_manager.stop_recording()
                await websocket.send_text(json.dumps({
                    "type": "recording_stopped",
                    "message": "🛑 Recording stopped",
                    "timestamp": datetime.now().isoformat()
                }))
            
            elif action == "transcribe_recent":
                duration = message.get("duration", 5.0)
                recent_audio = audio_manager.get_recent_audio(duration)
                
                if len(recent_audio) > 0:
                    await websocket.send_text(json.dumps({
                        "type": "processing",
                        "message": f"Transcribing {duration}s of audio...",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                    result = await whisper_manager.transcribe(recent_audio)
                    
                    await websocket.send_text(json.dumps({
                        "type": "transcription_result",
                        "result": result,
                        "source": "recent_audio",
                        "timestamp": datetime.now().isoformat()
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "No audio available for transcription",
                        "timestamp": datetime.now().isoformat()
                    }))
            
            elif action == "change_device":
                device_index = message.get("device_index")
                if device_index is not None and audio_manager.set_device(device_index):
                    await websocket.send_text(json.dumps({
                        "type": "device_changed",
                        "message": f"Switched to: {audio_manager.current_device['name']}",
                        "device": audio_manager.current_device,
                        "timestamp": datetime.now().isoformat()
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Failed to change device",
                        "timestamp": datetime.now().isoformat()
                    }))
            
            elif action == "change_language":
                language = message.get("language")
                if language and whisper_manager.set_language(language):
                    await websocket.send_text(json.dumps({
                        "type": "language_changed",
                        "message": f"Language set to: {whisper_manager.languages.get(language, language)}",
                        "language": language,
                        "timestamp": datetime.now().isoformat()
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Failed to change language",
                        "timestamp": datetime.now().isoformat()
                    }))
    
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        audio_manager.stop_recording()
        print(f"🔌 WebSocket disconnected. Remaining: {len(connected_clients)}")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        if websocket in connected_clients:
            connected_clients.remove(websocket)

async def transcription_loop(websocket: WebSocket):
    try:
        print("🎤 Starting enhanced transcription loop...")
        
        while audio_manager.is_recording and websocket in connected_clients:
            audio_chunk = await audio_manager.get_audio_async(timeout=3.5)
            
            if audio_chunk is not None:
                level = audio_manager.get_level()
                
                # Send audio level
                await websocket.send_text(json.dumps({
                    "type": "audio_level",
                    "level": level,
                    "timestamp": datetime.now().isoformat()
                }))
                
                # Transcribe if significant audio
                if level > 0.03:  # Adjusted threshold
                    recent_audio = audio_manager.get_recent_audio(4.0)
                    
                    if len(recent_audio) > 16000:  # At least 1 second
                        result = await whisper_manager.transcribe(recent_audio)
                        
                        # Only send meaningful text
                        if result["text"].strip() and len(result["text"].strip()) > 1:
                            await websocket.send_text(json.dumps({
                                "type": "live_transcription", 
                                "result": result,
                                "audio_level": level,
                                "device_info": {
                                    "name": audio_manager.current_device['name'],
                                    "type": audio_manager.current_device['type'],
                                    "language": audio_manager.current_device.get('language')
                                },
                                "timestamp": datetime.now().isoformat()
                            }))
            
            await asyncio.sleep(0.5)
        
        print("🛑 Enhanced transcription loop ended")
    except Exception as e:
        print(f"❌ Transcription loop error: {e}")

@app.get("/demo")
async def demo():
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>WhisperS2T Enhanced Demo</title>
        <style>
            body { font-family: Arial; margin: 20px; background: #f8f9fa; }
            .container { max-width: 1100px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            button { padding: 12px 24px; margin: 8px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; transition: all 0.2s; }
            .btn-primary { background: #007bff; color: white; }
            .btn-success { background: #28a745; color: white; }
            .btn-record { background: #dc3545; color: white; font-size: 18px; padding: 15px 30px; }
            .btn-record.recording { background: #28a745; animation: pulse 1s infinite; }
            @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.7; } 100% { opacity: 1; } }
            
            .status { padding: 12px; border-radius: 5px; margin: 15px 0; font-weight: bold; text-align: center; }
            .connected { background: #d4edda; color: #155724; }
            .disconnected { background: #f8d7da; color: #721c24; }
            .recording { background: #fff3cd; color: #856404; }
            
            .controls { background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: center; }
            .config { background: #e9ecef; padding: 15px; border-radius: 5px; margin: 15px 0; }
            
            .transcription { background: #f0fff0; border: 1px solid #90ee90; border-radius: 5px; padding: 15px; margin: 10px 0; border-left: 4px solid #28a745; }
            .transcription.german { border-left-color: #dc3545; background: #fff5f5; }
            .transcription.french { border-left-color: #6610f2; background: #f8f7ff; }
            .transcription.spanish { border-left-color: #fd7e14; background: #fff8f1; }
            
            .audio-level { width: 100%; height: 25px; background: #e9ecef; border-radius: 12px; margin: 10px 0; overflow: hidden; }
            .audio-level-bar { height: 100%; background: linear-gradient(90deg, #28a745, #ffc107, #dc3545); border-radius: 12px; transition: width 0.1s ease; width: 0%; }
            
            select { padding: 8px; margin: 5px; border-radius: 4px; border: 1px solid #ddd; min-width: 180px; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            .info { background: #d1ecf1; border: 1px solid #bee5eb; border-radius: 5px; padding: 10px; margin: 10px 0; font-size: 14px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🎤 WhisperS2T Enhanced Demo</h2>
            <p>Real-time speech recognition with device & language selection</p>
            
            <div id="status" class="status disconnected">❌ Disconnected</div>
            
            <div class="grid">
                <div>
                    <div class="config">
                        <h4>⚙️ Device & Language Selection</h4>
                        
                        <div style="margin: 10px 0;">
                            <label><strong>🎤 Audio Device:</strong></label><br>
                            <select id="deviceSelect">
                                <option value="">Loading devices...</option>
                            </select>
                            <button onclick="changeDevice()" style="padding: 6px 12px;">Apply</button>
                        </div>
                        
                        <div style="margin: 10px 0;">
                            <label><strong>🌐 Language:</strong></label><br>
                            <select id="languageSelect">
                                <option value="auto">Auto-detect</option>
                                <option value="en">English</option>
                                <option value="de">German</option>
                                <option value="fr">French</option>
                                <option value="es">Spanish</option>
                                <option value="it">Italian</option>
                            </select>
                            <button onclick="changeLanguage()" style="padding: 6px 12px;">Apply</button>
                        </div>
                        
                        <div class="info">
                            <strong>🎭 Enhanced Test Mode:</strong><br>
                            If no hardware microphone is detected, realistic test audio will be generated in different languages. Each test device speaks in its native language with realistic speech patterns.
                        </div>
                    </div>
                    
                    <div class="controls">
                        <h4>🔌 Recording Controls</h4>
                        <button onclick="connect()" class="btn-primary">🔌 Connect WebSocket</button>
                        <br><br>
                        
                        <button id="recordBtn" onclick="toggleRecording()" class="btn-record">🎙️ START RECORDING</button>
                        <br><br>
                        
                        <button onclick="transcribeRecent()" class="btn-success">📝 Transcribe Last 5s</button>
                        
                        <h4>🎛️ Audio Level Monitor</h4>
                        <div class="audio-level">
                            <div id="audioLevelBar" class="audio-level-bar"></div>
                        </div>
                        <span id="audioLevelText">Level: 0%</span>
                        
                        <div id="deviceInfo" class="info">
                            <small>Device info will appear here...</small>
                        </div>
                    </div>
                </div>
                
                <div>
                    <div id="results" style="min-height: 450px;">
                        <h4>📝 Live Transcription Results</h4>
                        <div id="liveResults">
                            <div class="info">
                                <strong>🚀 Welcome to Enhanced WhisperS2T!</strong><br>
                                Click "Connect WebSocket" to start, then "START RECORDING" to begin live transcription.
                                <br><br>
                                <strong>Features:</strong><br>
                                • Real microphone detection<br>
                                • Multi-language support<br>
                                • Realistic test voices<br>
                                • Live audio level monitoring
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let ws = null;
            let isRecording = false;
            let currentDevices = [];
            
            function connect() {
                const wsUrl = `ws://${window.location.host}/ws/live-audio`;
                console.log('Connecting to Enhanced WebSocket:', wsUrl);
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function() { 
                    updateStatus('connected'); 
                    addMessage('✅ Enhanced WebSocket connected successfully!');
                };
                
                ws.onmessage = function(event) { 
                    const data = JSON.parse(event.data);
                    handleMessage(data); 
                };
                
                ws.onclose = function() { 
                    updateStatus('disconnected'); 
                    isRecording = false; 
                    updateRecordButton(); 
                    addMessage('❌ WebSocket connection closed');
                };
                
                ws.onerror = function(error) { 
                    console.error('WebSocket error:', error); 
                    updateStatus('disconnected'); 
                    addMessage('❌ WebSocket connection error');
                };
            }
            
            function toggleRecording() {
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    alert('Not connected! Click "Connect WebSocket" first.');
                    return;
                }
                
                if (!isRecording) {
                    ws.send(JSON.stringify({action: 'start_recording'}));
                } else {
                    ws.send(JSON.stringify({action: 'stop_recording'}));
                }
            }
            
            function transcribeRecent() {
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    alert('Not connected!');
                    return;
                }
                ws.send(JSON.stringify({action: 'transcribe_recent', duration: 5.0}));
            }
            
            function changeDevice() {
                const deviceIndex = parseInt(document.getElementById('deviceSelect').value);
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    addMessage('⚠️ Not connected - will apply when connected');
                    return;
                }
                
                ws.send(JSON.stringify({
                    action: 'change_device',
                    device_index: deviceIndex
                }));
            }
            
            function changeLanguage() {
                const language = document.getElementById('languageSelect').value;
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    addMessage('⚠️ Not connected - will apply when connected');
                    return;
                }
                
                ws.send(JSON.stringify({
                    action: 'change_language',
                    language: language
                }));
            }
            
            function handleMessage(data) {
                console.log('Received:', data.type);
                
                switch(data.type) {
                    case 'connected':
                        addMessage('✅ ' + data.message);
                        if (data.audio_status) {
                            updateDeviceList(data.audio_status.input_devices);
                            updateDeviceInfo(data.audio_status.current_device);
                        }
                        if (data.whisper_info) {
                            addMessage(`🧠 Whisper Model: ${data.whisper_info.model} | Language: ${data.whisper_info.language}`);
                        }
                        break;
                        
                    case 'recording_started':
                        isRecording = true;
                        updateRecordButton();
                        updateStatus('recording');
                        addMessage('🎤 ' + data.message);
                        if (data.device) {
                            updateDeviceInfo(data.device);
                        }
                        break;
                        
                    case 'recording_stopped':
                        isRecording = false;
                        updateRecordButton();
                        updateStatus('connected');
                        addMessage('🛑 Recording stopped');
                        break;
                        
                    case 'live_transcription':
                        displayLiveTranscription(data.result, data.audio_level, data.device_info);
                        break;
                        
                    case 'transcription_result':
                        displayTranscriptionResult(data.result, data.source);
                        break;
                        
                    case 'audio_level':
                        updateAudioLevel(data.level);
                        break;
                        
                    case 'device_changed':
                        addMessage('🎤 ' + data.message);
                        updateDeviceInfo(data.device);
                        break;
                        
                    case 'language_changed':
                        addMessage('🌐 ' + data.message);
                        break;
                        
                    case 'processing':
                        addMessage('🔄 ' + data.message);
                        break;
                        
                    case 'error':
                        addMessage('❌ ' + data.message);
                        break;
                }
            }
            
            function updateDeviceList(devices) {
                const select = document.getElementById('deviceSelect');
                select.innerHTML = '';
                
                devices.forEach((device, index) => {
                    const option = document.createElement('option');
                    option.value = index;
                    option.textContent = device.name;
                    select.appendChild(option);
                });
                
                currentDevices = devices;
            }
            
            function updateDeviceInfo(device) {
                const info = document.getElementById('deviceInfo');
                if (device) {
                    let deviceText = `<strong>Current:</strong> ${device.name}<br><strong>Type:</strong> ${device.type}`;
                    
                    if (device.language) {
                        deviceText += `<br><strong>Test Language:</strong> ${device.language.toUpperCase()}`;
                    }
                    
                    if (device.type === 'test') {
                        deviceText += `<br><small>🎭 Realistic ${device.language || 'test'} speech simulation</small>`;
                    } else if (device.type === 'hardware') {
                        deviceText += `<br><small>🎤 Real microphone input</small>`;
                    }
                    
                    info.innerHTML = deviceText;
                }
            }
            
            function displayLiveTranscription(result, audioLevel, deviceInfo) {
                const div = document.createElement('div');
                
                let languageClass = '';
                if (result.language === 'de') languageClass = 'german';
                else if (result.language === 'fr') languageClass = 'french'; 
                else if (result.language === 'es') languageClass = 'spanish';
                
                div.className = `transcription ${languageClass}`;
                
                const levelText = audioLevel ? ` (Level: ${Math.round(audioLevel * 100)}%)` : '';
                
                let deviceText = '';
                if (deviceInfo && deviceInfo.type === 'test' && deviceInfo.language) {
                    deviceText = ` | 🎭 ${deviceInfo.language.toUpperCase()} Voice`;
                } else if (deviceInfo && deviceInfo.type === 'hardware') {
                    deviceText = ` | 🎤 Hardware`;
                }
                
                div.innerHTML = `
                    <h5>🔴 LIVE: ${new Date().toLocaleTimeString()}${levelText}</h5>
                    <p><strong>"${result.text}"</strong></p>
                    <small>
                        🌐 Detected: ${result.language.toUpperCase()} | 
                        🎯 Target: ${result.target_language.toUpperCase()} | 
                        ⚙️ Model: ${result.model} | 
                        ⏱️ Processing: ${result.processing_time}s | 
                        🎵 Audio: ${result.audio_length.toFixed(1)}s${deviceText}
                    </small>
                `;
                
                document.getElementById('liveResults').appendChild(div);
                div.scrollIntoView({ behavior: 'smooth' });
            }
            
            function displayTranscriptionResult(result, source) {
                const div = document.createElement('div');
                div.className = 'transcription';
                
                div.innerHTML = `
                    <h5>📝 ${source.toUpperCase()}: ${new Date().toLocaleTimeString()}</h5>
                    <p><strong>"${result.text}"</strong></p>
                    <small>
                        🌐 Language: ${result.language.toUpperCase()} | 
                        🎯 Target: ${result.target_language.toUpperCase()} | 
                        ⚙️ Model: ${result.model} | 
                        ⏱️ Processing: ${result.processing_time}s | 
                        🎵 Audio: ${result.audio_length.toFixed(1)}s
                    </small>
                `;
                
                document.getElementById('liveResults').appendChild(div);
                div.scrollIntoView({ behavior: 'smooth' });
            }
            
            function addMessage(message) {
                const div = document.createElement('div');
                div.style.cssText = 'padding: 8px; margin: 5px 0; background: #f8f9fa; border-radius: 3px; font-size: 14px; border-left: 3px solid #6c757d;';
                div.innerHTML = `<small>${new Date().toLocaleTimeString()}: ${message}</small>`;
                document.getElementById('liveResults').appendChild(div);
                div.scrollIntoView({ behavior: 'smooth' });
            }
            
            function updateAudioLevel(level) {
                const percentage = Math.round(level * 100);
                document.getElementById('audioLevelBar').style.width = percentage + '%';
                document.getElementById('audioLevelText').textContent = `Level: ${percentage}%`;
            }
            
            function updateRecordButton() {
                const btn = document.getElementById('recordBtn');
                if (isRecording) {
                    btn.innerHTML = '⏹️ STOP RECORDING';
                    btn.className = 'btn-record recording';
                } else {
                    btn.innerHTML = '🎙️ START RECORDING';
                    btn.className = 'btn-record';
                }
            }
            
            function updateStatus(status) {
                const statusDiv = document.getElementById('status');
                switch(status) {
                    case 'connected':
                        statusDiv.className = 'status connected';
                        statusDiv.innerHTML = '✅ Connected - Enhanced Features Ready!';
                        break;
                    case 'recording':
                        statusDiv.className = 'status recording';
                        statusDiv.innerHTML = '🔴 RECORDING - Speak now!';
                        break;
                    case 'disconnected':
                        statusDiv.className = 'status disconnected';
                        statusDiv.innerHTML = '❌ Disconnected - Click Connect';
                        break;
                }
            }
            
            window.onload = function() {
                addMessage('🚀 Enhanced demo loaded - ready to connect!');
                
                // Load initial device list
                fetch('/api/status')
                    .then(response => response.json())
                    .then(data => {
                        if (data.audio && data.audio.input_devices) {
                            updateDeviceList(data.audio.input_devices);
                            updateDeviceInfo(data.audio.current_device);
                        }
                        addMessage(`📊 System Status: ${data.version} - ${data.status}`);
                    })
                    .catch(error => {
                        console.error('Error loading status:', error);
                        addMessage('⚠️ Could not load initial status');
                    });
            };
        </script>
    </body>
    </html>
    """)

if __name__ == "__main__":
    import uvicorn
    
    print("🎤 Starting WhisperS2T Enhanced Live Audio Server (Final)...")
    print("🌐 Main Interface: http://localhost:5000")
    print("🎙️ Enhanced Demo: http://localhost:5000/demo")
    print("📊 Status API: http://localhost:5000/api/status")
    print()
    print("🆕 ENHANCED FEATURES:")
    print("   ✅ Real microphone detection & selection")
    print("   ✅ Multi-language support (DE/EN/FR/ES/IT)")
    print("   ✅ Realistic language-specific test voices")
    print("   ✅ Enhanced device management")
    print("   ✅ Live language detection with confidence")
    print("   ✅ Improved audio processing & level detection")
    print("   ✅ WebSocket device & language switching")
    print()
    print("🎭 ENHANCED TEST MODE:")
    print("   If no hardware microphone is detected, the system will")
    print("   generate realistic test audio in different languages:")
    print("   • German Voice Simulator - speaks German")
    print("   • English Voice Simulator - speaks English") 
    print("   • French Voice Simulator - speaks French")
    print()
    print("   Each test device generates realistic speech patterns")
    print("   with proper pauses, emphasis, and language-specific sounds!")
    
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
