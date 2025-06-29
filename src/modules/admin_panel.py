"""
Admin Panel Module
Provides comprehensive admin interface with navigation and system monitoring
Preserves all original admin features and enhances with navigation
"""

import logging
from datetime import datetime

from flask import render_template_string

logger = logging.getLogger(__name__)


class AdminPanel:
    """Manages admin interface and system monitoring"""

    def __init__(self, whisper_available, system_stats, connected_clients, model):
        self.whisper_available = whisper_available
        self.system_stats = system_stats
        self.connected_clients = connected_clients
        self.model = model

    def get_admin_interface(self):
        """Enhanced Admin Panel with Navigation - Preserving original + adding navigation"""
        uptime = (datetime.now() - self.system_stats["uptime_start"]).total_seconds()
        uptime_formatted = f"{int(uptime // 3600)}h {int((uptime % 3600) // 60)}m {int(uptime % 60)}s"

        admin_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>WhisperS2T Admin Panel</title>
            <meta charset="utf-8">
            <meta http-equiv="refresh" content="30">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: Arial, sans-serif; background: #f0f2f5; margin: 0; }}
                
                /* Navigation Header */
                .nav-header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 15px 0;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .nav-container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 0 20px;
                }}
                .nav-title {{
                    font-size: 1.5em;
                    font-weight: bold;
                }}
                .nav-links {{
                    display: flex;
                    gap: 20px;
                }}
                .nav-links a {{
                    color: white;
                    text-decoration: none;
                    padding: 8px 16px;
                    border-radius: 5px;
                    transition: background 0.3s;
                }}
                .nav-links a:hover {{
                    background: rgba(255,255,255,0.2);
                }}
                .nav-links a.active {{
                    background: rgba(255,255,255,0.3);
                }}
                
                /* Main Content */
                .container {{ 
                    max-width: 1400px; 
                    margin: 0 auto; 
                    padding: 20px;
                }}
                .header {{ 
                    background: white;
                    color: #333;
                    padding: 20px; 
                    border-radius: 10px; 
                    margin-bottom: 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .stats-grid {{ 
                    display: grid; 
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
                    gap: 20px; 
                    margin-bottom: 20px; 
                }}
                .stat-card {{ 
                    background: white; 
                    padding: 20px; 
                    border-radius: 10px; 
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
                }}
                .stat-value {{ 
                    font-size: 2em; 
                    font-weight: bold; 
                    color: #667eea; 
                }}
                .stat-label {{ 
                    color: #666; 
                    margin-top: 5px; 
                }}
                .status-good {{ color: #28a745; }}
                .status-warning {{ color: #ffc107; }}
                .status-error {{ color: #dc3545; }}
                table {{ 
                    width: 100%; 
                    border-collapse: collapse; 
                    margin-top: 10px; 
                }}
                th, td {{ 
                    padding: 10px; 
                    text-align: left; 
                    border-bottom: 1px solid #ddd; 
                }}
                th {{ background: #f8f9fa; }}
                
                /* Quick Actions */
                .quick-actions {{
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    margin-bottom: 20px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                .action-buttons {{
                    display: flex;
                    gap: 15px;
                    margin-top: 15px;
                }}
                .btn {{
                    padding: 10px 20px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    text-decoration: none;
                    display: inline-block;
                    transition: all 0.3s;
                }}
                .btn-primary {{ background: #667eea; color: white; }}
                .btn-success {{ background: #28a745; color: white; }}
                .btn-info {{ background: #17a2b8; color: white; }}
                .btn-warning {{ background: #ffc107; color: black; }}
                .btn:hover {{ transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }}
            </style>
        </head>
        <body>
            <!-- Navigation Header -->
            <div class="nav-header">
                <div class="nav-container">
                    <div class="nav-title">🎤 WhisperS2T Control Center</div>
                    <div class="nav-links">
                        <a href="/" class="nav-link">🏠 Home</a>
                        <a href="/admin" class="nav-link active">⚙️ Admin</a>
                        <a href="/docs" class="nav-link">📚 API Docs</a>
                        <a href="/demo" class="nav-link">🎯 Demo</a>
                        <a href="/health" class="nav-link">🏥 Health</a>
                    </div>
                </div>
            </div>
            
            <div class="container">
                <div class="header">
                    <h1>⚙️ System Administration Dashboard</h1>
                    <p>Real-time monitoring and system control interface</p>
                </div>
                
                <!-- Quick Actions -->
                <div class="quick-actions">
                    <h3>🚀 Quick Actions</h3>
                    <div class="action-buttons">
                        <a href="/health" class="btn btn-success">🏥 Health Check</a>
                        <a href="/api/status" class="btn btn-info">📊 API Status</a>
                        <a href="/docs" class="btn btn-primary">📚 API Documentation</a>
                        <a href="/demo" class="btn btn-warning">🎯 Test Interface</a>
                    </div>
                </div>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value status-good">{"✅ Online" if self.whisper_available else "❌ Offline"}</div>
                        <div class="stat-label">Whisper Service Status</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-value">{uptime_formatted}</div>
                        <div class="stat-label">System Uptime</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-value">{self.system_stats['total_transcriptions']}</div>
                        <div class="stat-label">Total Transcriptions</div>
                    </div>
                    
                    <div class="stat-card">
                        <div class="stat-value">{len(self.connected_clients)}</div>
                        <div class="stat-label">Active WebSocket Connections</div>
                    </div>
                </div>
                
                <div class="stat-card">
                    <h3>🔧 System Information</h3>
                    <table>
                        <tr><th>Property</th><th>Value</th></tr>
                        <tr><td>Service Name</td><td>WhisperS2T Enhanced Appliance</td></tr>
                        <tr><td>Version</td><td>0.7.1</td></tr>
                        <tr><td>Framework</td><td>Flask + SocketIO</td></tr>
                        <tr><td>Whisper Available</td><td>{"Yes" if self.whisper_available else "No"}</td></tr>
                        <tr><td>Model Type</td><td>{"base" if self.model else "Not loaded"}</td></tr>
                        <tr><td>Architecture</td><td>Modular (live_speech, upload_handler, admin_panel, api_docs)</td></tr>
                        <tr><td>Features</td><td>Live Speech, Upload Transcription, WebSocket, API Docs</td></tr>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """
        return admin_html

    def get_demo_interface(self):
        """Enhanced Demo Interface - Preserving original functionality"""
        demo_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>WhisperS2T Demo Interface</title>
            <meta charset="utf-8">
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body { font-family: Arial, sans-serif; background: #f8f9fa; margin: 0; }
                
                /* Navigation */
                .nav-header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 15px 0;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .nav-container {
                    max-width: 1400px;
                    margin: 0 auto;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 0 20px;
                }
                .nav-title { font-size: 1.5em; font-weight: bold; }
                .nav-links { display: flex; gap: 20px; }
                .nav-links a {
                    color: white;
                    text-decoration: none;
                    padding: 8px 16px;
                    border-radius: 5px;
                    transition: background 0.3s;
                }
                .nav-links a:hover { background: rgba(255,255,255,0.2); }
                .nav-links a.active { background: rgba(255,255,255,0.3); }
                
                .container { max-width: 800px; margin: 20px auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { text-align: center; margin-bottom: 30px; }
                .demo-section { background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }
                button { background: #667eea; color: white; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer; margin: 10px; }
                button:hover { background: #5a67d8; }
                .result { background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 10px 0; border-left: 4px solid #28a745; }
                .error { background: #f8d7da; border-left-color: #dc3545; }
                input[type="file"] { margin: 10px 0; }
            </style>
        </head>
        <body>
            <!-- Navigation -->
            <div class="nav-header">
                <div class="nav-container">
                    <div class="nav-title">🎤 WhisperS2T Control Center</div>
                    <div class="nav-links">
                        <a href="/" class="nav-link">🏠 Home</a>
                        <a href="/admin" class="nav-link">⚙️ Admin</a>
                        <a href="/docs" class="nav-link">📚 API Docs</a>
                        <a href="/demo" class="nav-link active">🎯 Demo</a>
                        <a href="/health" class="nav-link">🏥 Health</a>
                    </div>
                </div>
            </div>
            
            <div class="container">
                <div class="header">
                    <h1>🎯 WhisperS2T Demo Interface</h1>
                    <p>Quick testing interface for API functionality</p>
                </div>

                <div class="demo-section">
                    <h3>🏥 System Health Check</h3>
                    <button onclick="checkHealth()">Check System Health</button>
                    <div id="healthResult"></div>
                </div>
                
                <div class="demo-section">
                    <h3>📁 File Upload Transcription</h3>
                    <input type="file" id="audioFile" accept="audio/*">
                    <button onclick="uploadFile()">Upload & Transcribe</button>
                    <div id="uploadResult"></div>
                </div>
                
                <div class="demo-section">
                    <h3>🎙️ Live Speech Recording Demo</h3>
                    <p>Test real-time speech-to-text with your microphone</p>
                    
                    <div style="margin: 15px 0;">
                        <label for="demoLanguage">🌍 Language:</label>
                        <select id="demoLanguage" style="margin: 5px; padding: 5px;">
                            <option value="auto">Auto-detect</option>
                            <option value="de">German (Deutsch)</option>
                            <option value="en">English</option>
                            <option value="fr">French (Français)</option>
                            <option value="es">Spanish (Español)</option>
                            <option value="it">Italian (Italiano)</option>
                        </select>
                    </div>
                    
                    <div>
                        <button id="startRecordingDemo" onclick="startLiveRecording()">🎙️ Start Recording</button>
                        <button id="stopRecordingDemo" onclick="stopLiveRecording()" disabled>⏹️ Stop Recording</button>
                        <span id="recordingStatus" style="margin-left: 15px; color: #666;">Ready to record</span>
                    </div>
                    
                    <div id="liveSpeechResult" style="margin-top: 15px; min-height: 60px; padding: 15px; background: #f8f9fa; border-radius: 5px; border-left: 4px solid #667eea;">
                        Click "Start Recording" to test live speech recognition...
                    </div>
                </div>
                
                <div class="demo-section">
                    <h3>🔗 WebSocket Connection Test</h3>
                    <button onclick="testWebSocket()">Test WebSocket Connection</button>
                    <div id="websocketResult"></div>
                </div>
            </div>
            
            <script>
                async function checkHealth() {
                    try {
                        const response = await fetch('/health');
                        const data = await response.json();
                        document.getElementById('healthResult').innerHTML = 
                            '<div class="result"><strong>Health Status:</strong><br>' + 
                            JSON.stringify(data, null, 2) + '</div>';
                    } catch (error) {
                        document.getElementById('healthResult').innerHTML = 
                            '<div class="result error"><strong>Error:</strong> ' + error.message + '</div>';
                    }
                }
                
                async function uploadFile() {
                    const fileInput = document.getElementById('audioFile');
                    if (!fileInput.files[0]) {
                        alert('Please select an audio file first!');
                        return;
                    }
                    
                    const formData = new FormData();
                    formData.append('audio', fileInput.files[0]);
                    
                    try {
                        document.getElementById('uploadResult').innerHTML = '<div class="result">🔄 Processing...</div>';
                        
                        const response = await fetch('/transcribe', {
                            method: 'POST',
                            body: formData
                        });
                        const data = await response.json();
                        
                        if (data.error) {
                            document.getElementById('uploadResult').innerHTML = 
                                '<div class="result error"><strong>Error:</strong> ' + data.error + '</div>';
                        } else {
                            document.getElementById('uploadResult').innerHTML = 
                                '<div class="result"><strong>Transcription:</strong><br>"' + data.text + '"</div>';
                        }
                    } catch (error) {
                        document.getElementById('uploadResult').innerHTML = 
                            '<div class="result error"><strong>Error:</strong> ' + error.message + '</div>';
                    }
                }
                
                // Live Speech Recording Demo
                let demoSocket = null;
                let demoMediaRecorder = null;
                let demoAudioChunks = [];
                let isDemoRecording = false;
                
                function initDemoWebSocket() {
                    if (!demoSocket) {
                        demoSocket = io();
                        
                        demoSocket.on('connect', function() {
                            console.log('Demo WebSocket connected');
                        });
                        
                        demoSocket.on('transcription_result', function(data) {
                            document.getElementById('liveSpeechResult').innerHTML = 
                                '<div class="result"><strong>📝 Transcription Result:</strong><br>"' + 
                                data.text + '"<br><small>Language: ' + data.language + 
                                ' | Time: ' + new Date().toLocaleTimeString() + '</small></div>';
                        });
                        
                        demoSocket.on('transcription_error', function(data) {
                            document.getElementById('liveSpeechResult').innerHTML = 
                                '<div class="result error"><strong>❌ Error:</strong> ' + data.error + '</div>';
                        });
                    }
                }
                
                async function startLiveRecording() {
                    try {
                        // Initialize WebSocket if needed
                        initDemoWebSocket();
                        
                        // Get microphone access
                        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                        demoMediaRecorder = new MediaRecorder(stream);
                        demoAudioChunks = [];
                        
                        demoMediaRecorder.ondataavailable = function(event) {
                            if (event.data.size > 0) {
                                demoAudioChunks.push(event.data);
                            }
                        };
                        
                        demoMediaRecorder.onstop = function() {
                            const audioBlob = new Blob(demoAudioChunks, { type: 'audio/wav' });
                            sendDemoAudioToServer(audioBlob);
                        };
                        
                        demoMediaRecorder.start();
                        isDemoRecording = true;
                        
                        // Update UI
                        document.getElementById('startRecordingDemo').disabled = true;
                        document.getElementById('stopRecordingDemo').disabled = false;
                        document.getElementById('recordingStatus').innerHTML = '🔴 Recording...';
                        document.getElementById('recordingStatus').style.color = '#dc3545';
                        document.getElementById('liveSpeechResult').innerHTML = '🎙️ Recording in progress... Speak now!';
                        
                        // Emit start recording event
                        if (demoSocket) {
                            demoSocket.emit('start_recording', {
                                language: document.getElementById('demoLanguage').value
                            });
                        }
                        
                    } catch (error) {
                        console.error('Error starting demo recording:', error);
                        document.getElementById('liveSpeechResult').innerHTML = 
                            '<div class="result error"><strong>❌ Microphone Error:</strong> ' + error.message + 
                            '<br><small>Please allow microphone access and try again.</small></div>';
                    }
                }
                
                function stopLiveRecording() {
                    if (demoMediaRecorder && isDemoRecording) {
                        demoMediaRecorder.stop();
                        isDemoRecording = false;
                        
                        // Stop all tracks
                        demoMediaRecorder.stream.getTracks().forEach(track => track.stop());
                        
                        // Update UI
                        document.getElementById('startRecordingDemo').disabled = false;
                        document.getElementById('stopRecordingDemo').disabled = true;
                        document.getElementById('recordingStatus').innerHTML = '🔄 Processing...';
                        document.getElementById('recordingStatus').style.color = '#667eea';
                        document.getElementById('liveSpeechResult').innerHTML = '🔄 Processing audio for transcription...';
                        
                        // Emit stop recording event
                        if (demoSocket) {
                            demoSocket.emit('stop_recording', {});
                        }
                    }
                }
                
                function sendDemoAudioToServer(audioBlob) {
                    const reader = new FileReader();
                    reader.onload = function() {
                        const base64Data = reader.result.split(',')[1];
                        if (demoSocket) {
                            demoSocket.emit('audio_chunk', {
                                audio_data: base64Data,
                                language: document.getElementById('demoLanguage').value
                            });
                        }
                        
                        // Reset status
                        document.getElementById('recordingStatus').innerHTML = 'Ready to record';
                        document.getElementById('recordingStatus').style.color = '#666';
                    };
                    reader.readAsDataURL(audioBlob);
                }
                
                function testWebSocket() {
                    try {
                        const socket = io();
                        document.getElementById('websocketResult').innerHTML = '<div class="result">🔄 Connecting...</div>';
                        
                        socket.on('connection_status', function(data) {
                            document.getElementById('websocketResult').innerHTML = 
                                '<div class="result"><strong>WebSocket Status:</strong><br>' + 
                                JSON.stringify(data, null, 2) + '</div>';
                        });
                        
                        socket.on('connect_error', function(error) {
                            document.getElementById('websocketResult').innerHTML = 
                                '<div class="result error"><strong>Connection Error:</strong> ' + error + '</div>';
                        });
                        
                    } catch (error) {
                        document.getElementById('websocketResult').innerHTML = 
                            '<div class="result error"><strong>Error:</strong> ' + error.message + '</div>';
                    }
                }
            </script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.0/socket.io.js"></script>
        </body>
        </html>
        """
        return demo_html
