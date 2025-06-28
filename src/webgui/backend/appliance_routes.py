('Please connect WebSocket first!');
                return;
            }

            const deviceId = microphoneSelect.value;
            const language = languageSelect.value;

            if (!deviceId) {
                alert('Please select a microphone first!');
                return;
            }

            try {
                if (audioStream) {
                    audioStream.getTracks().forEach(track => track.stop());
                }

                const constraints = {
                    audio: {
                        deviceId: deviceId,
                        sampleRate: 16000,
                        channelCount: 1,
                        echoCancellation: true,
                        noiseSuppression: true
                    }
                };

                audioStream = await navigator.mediaDevices.getUserMedia(constraints);

                const options = {
                    mimeType: 'audio/webm;codecs=opus',
                    audioBitsPerSecond: 16000
                };

                if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                    options.mimeType = 'audio/webm';
                }

                mediaRecorder = new MediaRecorder(audioStream, options);
                let audioChunks = [];

                mediaRecorder.ondataavailable = function(event) {
                    if (event.data.size > 0) {
                        audioChunks.push(event.data);
                    }
                };

                mediaRecorder.onstop = function() {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    sendAudioToServer(audioBlob, language);
                    audioChunks = [];
                };

                mediaRecorder.start();
                isRecording = true;
                recordBtn.disabled = true;
                stopBtn.disabled = false;

                document.getElementById('recordingStatus').textContent = 'Yes';
                document.getElementById('recordingStatus').className = 'status-value recording';

                // Send audio chunks every 3 seconds
                recordingInterval = setInterval(() => {
                    if (mediaRecorder && mediaRecorder.state === 'recording') {
                        mediaRecorder.stop();
                        setTimeout(() => {
                            if (isRecording && audioStream) {
                                mediaRecorder.start();
                            }
                        }, 100);
                    }
                }, 3000);

                // Send recording start command
                ws.send(JSON.stringify({
                    command: 'start_real_recording',
                    device_id: deviceId,
                    language: language,
                    mode: 'real_microphone'
                }));

                transcript.textContent = '🎙️ Recording started... Speak now!';

            } catch (error) {
                console.error('Failed to start recording:', error);
                alert('Failed to start recording: ' + error.message);
            }
        }

        function stopRecording() {
            isRecording = false;
            recordBtn.disabled = false;
            stopBtn.disabled = true;

            document.getElementById('recordingStatus').textContent = 'No';
            document.getElementById('recordingStatus').className = 'status-value';

            if (recordingInterval) {
                clearInterval(recordingInterval);
                recordingInterval = null;
            }

            if (mediaRecorder && mediaRecorder.state === 'recording') {
                mediaRecorder.stop();
            }

            if (audioStream) {
                audioStream.getTracks().forEach(track => track.stop());
                audioStream = null;
            }

            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    command: 'stop_recording'
                }));
            }

            transcript.textContent += '\n🛑 Recording stopped.';
        }

        async function sendAudioToServer(audioBlob, language) {
            try {
                const reader = new FileReader();
                reader.onloadend = function() {
                    const base64Audio = reader.result.split(',')[1];
                    
                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({
                            command: 'process_audio',
                            audio_data: base64Audio,
                            language: language,
                            format: 'webm'
                        }));
                    }
                };
                reader.readAsDataURL(audioBlob);
            } catch (error) {
                console.error('Failed to send audio:', error);
            }
        }

        function copyTranscript() {
            navigator.clipboard.writeText(transcriptText).then(() => {
                alert('Transcript copied to clipboard!');
            }).catch(err => {
                console.error('Failed to copy transcript:', err);
            });
        }

        function clearTranscript() {
            transcriptText = '';
            transcript.textContent = 'Transcript cleared. Ready for new recordings...';
        }

        function downloadTranscript() {
            if (!transcriptText.trim()) {
                alert('No transcript to download!');
                return;
            }

            const blob = new Blob([transcriptText], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `transcript-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
    </script>
</body>
</html>
    """)

# ==============================================================================
# WEBSOCKET HANDLERS
# ==============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Enhanced WebSocket endpoint with comprehensive session management"""
    session_id = f"session_{int(time.time())}_{len(state.connected_clients)}"
    
    await websocket.accept()
    state.connected_clients.add(websocket)
    
    # Create session info
    session_info = {
        'id': session_id,
        'connected_at': datetime.now(),
        'ip_address': websocket.client.host if websocket.client else 'unknown',
        'transcriptions': 0,
        'audio_minutes': 0.0,
        'last_activity': datetime.now()
    }
    state.active_sessions[session_id] = session_info
    
    try:
        logger.info(f"🌐 WebSocket client connected: {session_id} from {session_info['ip_address']}")
        logger.info(f"📊 Total active connections: {len(state.connected_clients)}")
        
        # Send welcome message with system info
        await websocket.send_text(json.dumps({
            "type": "connection",
            "message": "Enhanced WhisperS2T Appliance connected",
            "session_id": session_id,
            "version": "0.5.0-appliance",
            "system": {
                "current_model": state.current_model_name,
                "available_models": list(model_manager.model_info.keys()),
                "max_ram_gb": state.max_ram_usage,
                "max_cpu_percent": state.max_cpu_usage
            }
        }))
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            command = message.get('command')
            session_info['last_activity'] = datetime.now()
            
            logger.info(f"📨 Command received from {session_id}: {command}")
            
            if command == 'start_real_recording':
                device_id = message.get('device_id')
                language = message.get('language', 'auto')
                mode = message.get('mode', 'real_microphone')
                
                await websocket.send_text(json.dumps({
                    "type": "status",
                    "message": f"Real recording started - Device: {device_id}, Language: {language}",
                    "recording": True,
                    "session_id": session_id
                }))
                
                logger.info(f"🎤 Recording started for {session_id}: device={device_id}, language={language}")
                
            elif command == 'process_audio':
                audio_data = message.get('audio_data')
                language = message.get('language', 'auto')
                audio_format = message.get('format', 'webm')
                
                if audio_data:
                    # Process audio with resource management
                    transcript = await process_real_audio_managed(audio_data, language, audio_format)
                    
                    if transcript and transcript != "No speech detected":
                        session_info['transcriptions'] += 1
                        session_info['audio_minutes'] += 0.05  # Rough estimate for 3s chunks
                        state.stats['total_transcriptions'] += 1
                        
                        await websocket.send_text(json.dumps({
                            "type": "transcript",
                            "transcript": transcript,
                            "language": language,
                            "source": "real_microphone",
                            "session_id": session_id,
                            "timestamp": datetime.now().isoformat()
                        }))
                        
                        logger.info(f"🎯 Transcript for {session_id}: {transcript[:50]}...")
                    else:
                        await websocket.send_text(json.dumps({
                            "type": "status",
                            "message": transcript or "No speech detected",
                            "session_id": session_id
                        }))
                
            elif command == 'stop_recording':
                await websocket.send_text(json.dumps({
                    "type": "status",
                    "message": "Recording stopped",
                    "recording": False,
                    "session_id": session_id
                }))
                
                logger.info(f"🛑 Recording stopped for {session_id}")
                
            elif command == 'load_model':
                model_name = message.get('model_name', 'tiny')
                
                try:
                    await model_manager.load_model_with_limits(model_name)
                    await websocket.send_text(json.dumps({
                        "type": "model_loaded",
                        "message": f"Model {model_name} loaded successfully",
                        "model": model_name,
                        "ram_usage_mb": model_manager.model_info[model_name]["ram_mb"],
                        "session_id": session_id
                    }))
                    
                    logger.info(f"🧠 Model {model_name} loaded for {session_id}")
                    
                except Exception as e:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Model loading failed: {str(e)}",
                        "session_id": session_id
                    }))
                    
                    logger.error(f"❌ Model loading failed for {session_id}: {e}")
                
            elif command == 'get_system_status':
                system_info = resource_manager.get_system_info()
                await websocket.send_text(json.dumps({
                    "type": "system_status",
                    "data": system_info,
                    "session_id": session_id
                }))
                
            else:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": f"Unknown command: {command}",
                    "session_id": session_id
                }))
                
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket client disconnected: {session_id}")
    except Exception as e:
        logger.error(f"❌ WebSocket error for {session_id}: {e}")
    finally:
        # Cleanup session
        state.connected_clients.discard(websocket)
        if session_id in state.active_sessions:
            session_duration = (datetime.now() - session_info['connected_at']).seconds
            logger.info(f"📊 Session {session_id} ended - Duration: {session_duration}s, Transcriptions: {session_info['transcriptions']}")
            del state.active_sessions[session_id]
        
        logger.info(f"📊 Remaining active connections: {len(state.connected_clients)}")

# ==============================================================================
# APPLIANCE MANAGEMENT ENDPOINTS
# ==============================================================================

@app.get("/api/appliance/info")
async def get_appliance_info():
    """Get comprehensive appliance information for network management"""
    system_info = resource_manager.get_system_info()
    
    # Network interfaces
    network_interfaces = []
    for interface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET:  # IPv4
                network_interfaces.append({
                    'interface': interface,
                    'ip_address': addr.address,
                    'netmask': addr.netmask
                })
    
    return {
        "appliance": {
            "name": "Enhanced WhisperS2T Appliance",
            "version": "0.5.0-appliance",
            "build_type": "iso_ready",
            "deployment_ready": True
        },
        "network": {
            "hostname": system_info['hostname'],
            "interfaces": network_interfaces,
            "primary_ip": system_info['local_ip'],
            "web_port": 5000,
            "ssh_enabled": False,  # Will be configurable in ISO
            "firewall_status": "not_configured"
        },
        "system": system_info,
        "services": {
            "whisper_service": "running" if state.current_model else "stopped",
            "web_interface": "running",
            "websocket_server": "running",
            "resource_monitor": "running" if resource_manager.monitoring else "stopped"
        },
        "storage": {
            "config_path": "/etc/whisper-appliance",
            "models_path": "~/.cache/",
            "logs_path": "/var/log/whisper-appliance.log",
            "temp_path": "/tmp"
        }
    }

@app.post("/api/appliance/restart")
async def restart_appliance_service():
    """Restart the appliance service (for ISO deployment)"""
    try:
        logger.info("🔄 Appliance restart requested")
        
        # In ISO deployment, this would restart the systemd service
        # For now, we simulate the restart
        
        # Stop monitoring
        resource_manager.monitoring = False
        
        # Clear connections
        for client in list(state.connected_clients):
            try:
                await client.close()
            except:
                pass
        state.connected_clients.clear()
        state.active_sessions.clear()
        
        # Reset state
        state.system_ready = False
        
        # Restart monitoring
        resource_manager.start_monitoring()
        state.system_ready = True
        
        logger.info("✅ Appliance restart completed")
        
        return {
            "success": True,
            "message": "Appliance service restarted successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Appliance restart failed: {e}")
        raise HTTPException(status_code=500, detail=f"Restart failed: {str(e)}")

@app.get("/api/appliance/logs")
async def get_appliance_logs(lines: int = 100):
    """Get recent appliance logs"""
    try:
        log_file = "/var/log/whisper-appliance.log"
        
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                
            return {
                "success": True,
                "lines": len(recent_lines),
                "logs": ''.join(recent_lines)
            }
        else:
            return {
                "success": False,
                "message": "Log file not found",
                "logs": "No logs available"
            }
            
    except Exception as e:
        logger.error(f"Failed to read logs: {e}")
        raise HTTPException(status_code=500, detail=f"Log reading failed: {str(e)}")

@app.post("/api/appliance/shutdown")
async def shutdown_appliance():
    """Graceful appliance shutdown (for ISO deployment)"""
    try:
        logger.info("🔴 Appliance shutdown requested")
        
        # Stop all services gracefully
        resource_manager.monitoring = False
        
        # Close all WebSocket connections
        for client in list(state.connected_clients):
            try:
                await client.send_text(json.dumps({
                    "type": "system_shutdown",
                    "message": "Appliance is shutting down"
                }))
                await client.close()
            except:
                pass
        
        # Unload model to free memory
        if state.current_model:
            del state.current_model
            state.current_model = None
            gc.collect()
        
        logger.info("✅ Appliance shutdown preparation completed")
        
        # In ISO deployment, this would trigger system shutdown
        # For development, we just return success
        
        return {
            "success": True,
            "message": "Appliance shutdown initiated",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Shutdown preparation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Shutdown failed: {str(e)}")

# ==============================================================================
# FILE UPLOAD & BATCH PROCESSING
# ==============================================================================

@app.post("/api/transcribe/file")
async def transcribe_uploaded_file(
    file: UploadFile = File(...),
    language: str = Form("auto"),
    model: str = Form("current")
):
    """Transcribe uploaded audio file"""
    
    if not state.current_model:
        raise HTTPException(status_code=503, detail="No Whisper model loaded")
    
    # Check file size (max 100MB)
    if file.size and file.size > 100 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 100MB)")
    
    # Check file type
    allowed_types = ['audio/wav', 'audio/mp3', 'audio/webm', 'audio/ogg', 'audio/m4a']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=415, detail="Unsupported audio format")
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_audio_path = temp_file.name
        
        start_time = time.time()
        
        # Process with current model
        language_code = None if language == 'auto' else language
        
        model_type = getattr(state.current_model, 'model_type', 'unknown')
        
        if model_type == "faster-whisper" or hasattr(state.current_model, 'model'):
            segments, info = state.current_model.transcribe(
                temp_audio_path,
                language=language_code,
                beam_size=5,
                word_timestamps=True
            )
            
            transcript_parts = []
            timestamps = []
            
            for segment in segments:
                transcript_parts.append(segment.text)
                timestamps.append({
                    'start': segment.start,
                    'end': segment.end,
                    'text': segment.text
                })
            
            transcript = ''.join(transcript_parts).strip()
            detected_language = info.language if hasattr(info, 'language') else 'unknown'
            
        else:
            # OpenAI Whisper
            result = state.current_model.transcribe(
                temp_audio_path,
                language=language_code,
                verbose=True
            )
            transcript = result.get('text', '').strip()
            detected_language = result.get('language', 'unknown')
            timestamps = result.get('segments', [])
        
        processing_time = time.time() - start_time
        
        # Update statistics
        state.stats['total_transcriptions'] += 1
        
        logger.info(f"📁 File transcribed: {file.filename} ({processing_time:.2f}s)")
        
        return {
            "success": True,
            "filename": file.filename,
            "transcript": transcript,
            "language": detected_language,
            "processing_time": round(processing_time, 2),
            "timestamps": timestamps,
            "model_used": state.current_model_name,
            "file_size_mb": round(len(content) / (1024 * 1024), 2)
        }
        
    except Exception as e:
        logger.error(f"File transcription failed: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        # Cleanup temp file
        try:
            os.unlink(temp_audio_path)
        except:
            pass

# ==============================================================================
# HEALTH & MONITORING ENDPOINTS
# ==============================================================================

@app.get("/health")
async def health_check():
    """Comprehensive health check for load balancer/monitoring"""
    
    try:
        system_info = resource_manager.get_system_info()
        
        # Calculate health score
        health_score = 100
        issues = []
        
        # CPU check
        if system_info['cpu']['current_usage'] > 90:
            health_score -= 30
            issues.append("High CPU usage")
        elif system_info['cpu']['current_usage'] > 70:
            health_score -= 15
            issues.append("Elevated CPU usage")
        
        # RAM check
        if system_info['memory']['percent'] > 90:
            health_score -= 30
            issues.append("High RAM usage")
        elif system_info['memory']['percent'] > 70:
            health_score -= 15
            issues.append("Elevated RAM usage")
        
        # Disk check
        if system_info['disk']['percent'] > 95:
            health_score -= 20
            issues.append("Low disk space")
        elif system_info['disk']['percent'] > 85:
            health_score -= 10
            issues.append("Limited disk space")
        
        # Model check
        if not state.current_model:
            health_score -= 25
            issues.append("No Whisper model loaded")
        
        # Service check
        if not state.system_ready:
            health_score -= 50
            issues.append("System not ready")
        
        health_status = "healthy" if health_score >= 80 else "degraded" if health_score >= 50 else "unhealthy"
        
        return {
            "status": health_status,
            "health_score": max(0, health_score),
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - state.stats['uptime_start']).seconds,
            "version": "0.5.0-appliance",
            "issues": issues,
            "system": {
                "cpu_usage": system_info['cpu']['current_usage'],
                "ram_usage": system_info['memory']['percent'],
                "disk_usage": system_info['disk']['percent'],
                "active_connections": len(state.connected_clients),
                "current_model": state.current_model_name,
                "model_loading": state.model_loading
            },
            "services": {
                "websocket": "running",
                "resource_monitor": "running" if resource_manager.monitoring else "stopped",
                "whisper_engine": "running" if state.current_model else "stopped"
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "health_score": 0,
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.get("/metrics")
async def get_prometheus_metrics():
    """Prometheus-compatible metrics endpoint"""
    
    try:
        system_info = resource_manager.get_system_info()
        
        metrics = []
        
        # System metrics
        metrics.append(f'whisper_cpu_usage {system_info["cpu"]["current_usage"]}')
        metrics.append(f'whisper_ram_usage_percent {system_info["memory"]["percent"]}')
        metrics.append(f'whisper_ram_usage_gb {system_info["memory"]["used_gb"]}')
        metrics.append(f'whisper_disk_usage_percent {system_info["disk"]["percent"]}')
        metrics.append(f'whisper_disk_usage_gb {system_info["disk"]["used_gb"]}')
        
        # Application metrics
        metrics.append(f'whisper_active_connections {len(state.connected_clients)}')
        metrics.append(f'whisper_total_transcriptions {state.stats["total_transcriptions"]}')
        metrics.append(f'whisper_audio_minutes_processed {state.stats["total_audio_minutes"]}')
        metrics.append(f'whisper_uptime_seconds {(datetime.now() - state.stats["uptime_start"]).seconds}')
        
        # Model metrics
        metrics.append(f'whisper_model_loaded {1 if state.current_model else 0}')
        metrics.append(f'whisper_model_loading {1 if state.model_loading else 0}')
        metrics.append(f'whisper_model_ram_mb {system_info["whisper_model"]["ram_usage_mb"]}')
        
        # Resource limits
        metrics.append(f'whisper_max_ram_gb {state.max_ram_usage}')
        metrics.append(f'whisper_max_cpu_percent {state.max_cpu_usage}')
        
        return "\n".join(metrics)
        
    except Exception as e:
        logger.error(f"Metrics generation failed: {e}")
        return f"# Error generating metrics: {str(e)}"

if __name__ == "__main__":
    # Enhanced production startup
    logger.info("🚀 Starting Enhanced WhisperS2T Appliance v0.5.0")
    logger.info("🌐 Network Appliance Mode - ISO Deployment Ready")
    
    uvicorn.run(
        "appliance_routes:app",
        host="0.0.0.0", 
        port=5000,
        log_level="info",
        access_log=True,
        reload=False  # Disabled for production appliance
    )
