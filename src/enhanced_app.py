            threading.Thread(target=live_transcription_worker, daemon=True).start()
            logger.info("Live transcription started")
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Failed to start audio recording"})
            
    except Exception as e:
        logger.error(f"Failed to start live transcription: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route("/live/stop", methods=["POST"])
def stop_live_transcription():
    global live_transcription_active
    
    try:
        live_transcription_active = False
        if AUDIO_MANAGER:
            AUDIO_MANAGER.stop_recording()
        
        # Clear the queue
        while not live_transcription_queue.empty():
            try:
                live_transcription_queue.get_nowait()
            except queue.Empty:
                break
                
        logger.info("Live transcription stopped")
        return jsonify({"success": True})
        
    except Exception as e:
        logger.error(f"Failed to stop live transcription: {e}")
        return jsonify({"success": False, "error": str(e)})

@app.route("/live/update")
def get_live_transcription_update():
    try:
        # Get latest transcription from queue (non-blocking)
        transcription = ""
        while not live_transcription_queue.empty():
            try:
                transcription = live_transcription_queue.get_nowait()
            except queue.Empty:
                break
        
        return jsonify({
            "transcription": transcription,
            "is_active": live_transcription_active
        })
        
    except Exception as e:
        logger.error(f"Failed to get transcription update: {e}")
        return jsonify({"transcription": "", "is_active": False, "error": str(e)})

def live_transcription_worker():
    """Background worker for live transcription"""
    global live_transcription_active
    
    accumulated_text = ""
    
    while live_transcription_active and AUDIO_MANAGER:
        try:
            # Get audio chunk
            audio_chunk = AUDIO_MANAGER.get_audio_chunk(timeout=2.0)
            
            if audio_chunk is not None and len(audio_chunk) > 0:
                # Get recent audio for transcription (last 5 seconds)
                recent_audio = AUDIO_MANAGER.get_recent_audio(duration=5.0)
                
                if len(recent_audio) > 8000:  # Minimum audio length
                    try:
                        # Transcribe using Whisper
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                            # Save audio to temp file
                            import soundfile as sf
                            sf.write(tmp_file.name, recent_audio, AUDIO_MANAGER.sample_rate)
                            
                            # Transcribe
                            result = model.transcribe(tmp_file.name)
                            transcribed_text = result["text"].strip()
                            
                            # Clean up
                            os.unlink(tmp_file.name)
                            
                            if transcribed_text and transcribed_text != accumulated_text:
                                accumulated_text = transcribed_text
                                # Put in queue for frontend
                                try:
                                    live_transcription_queue.put_nowait(accumulated_text)
                                except queue.Full:
                                    # Remove old transcription and add new
                                    try:
                                        live_transcription_queue.get_nowait()
                                        live_transcription_queue.put_nowait(accumulated_text)
                                    except queue.Empty:
                                        pass
                                        
                    except Exception as e:
                        logger.error(f"Transcription error: {e}")
            
            time.sleep(0.5)  # Small delay to prevent excessive CPU usage
            
        except Exception as e:
            logger.error(f"Live transcription worker error: {e}")
            time.sleep(1.0)

# Audio system endpoints
@app.route("/audio/status")
def get_audio_status():
    if not AUDIO_MANAGER:
        return jsonify({
            "devices_available": 0,
            "current_device": None,
            "hardware_available": False,
            "sample_rate": 0,
            "channels": 0,
            "error": "Audio manager not available"
        })
    
    try:
        status = AUDIO_MANAGER.get_device_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/audio/test")
def test_audio_system():
    if not AUDIO_MANAGER:
        return jsonify({
            "microphone_detected": False,
            "error": "Audio manager not available"
        })
    
    try:
        test_result = AUDIO_MANAGER.test_microphone()
        return jsonify(test_result)
    except Exception as e:
        return jsonify({"error": str(e)})

# File upload transcription (existing functionality)
@app.route("/transcribe", methods=["POST"])
def transcribe():
    if not WHISPER_AVAILABLE:
        return jsonify({"error": "Whisper model not available"})
    
    try:
        if "audio" not in request.files:
            return jsonify({"error": "No audio file provided"})
        
        audio_file = request.files["audio"]
        if audio_file.filename == "":
            return jsonify({"error": "No audio file selected"})
        
        filename = secure_filename(audio_file.filename)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            audio_file.save(tmp_file.name)
            
            logger.info(f"Transcribing file: {filename}")
            result = model.transcribe(tmp_file.name)
            
            os.unlink(tmp_file.name)
            
            logger.info("Transcription completed successfully")
            return jsonify({"text": result["text"]})
    
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return jsonify({"error": str(e)})

# System management endpoints
@app.route("/restart", methods=["POST"])
def restart_service():
    try:
        # Stop any active transcription
        global live_transcription_active
        live_transcription_active = False
        
        if AUDIO_MANAGER:
            AUDIO_MANAGER.stop_recording()
        
        # Schedule restart
        def restart_in_background():
            time.sleep(2)
            os.system("sudo systemctl restart whisper-appliance")
        
        threading.Thread(target=restart_in_background, daemon=True).start()
        
        return jsonify({"success": True, "message": "Service restart initiated"})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    logger.info("🎤 Enhanced WhisperS2T Appliance starting...")
    logger.info(f"Whisper available: {WHISPER_AVAILABLE}")
    logger.info(f"Audio manager available: {AUDIO_MANAGER is not None}")
    
    if AUDIO_MANAGER:
        logger.info(f"Audio devices: {len(AUDIO_MANAGER.input_devices)}")
        logger.info(f"Hardware audio: {AUDIO_MANAGER.hardware_available}")
    
    app.run(host="0.0.0.0", port=5001, debug=False, threaded=True)
