"""
API Documentation Module
Provides comprehensive API documentation interface
Preserves all original API docs features and enhances with better structure
"""

import logging

from flask import render_template_string

logger = logging.getLogger(__name__)


class APIDocs:
    """Manages API documentation interface"""

    def __init__(self, version="0.7.0"):
        self.version = version

    def get_docs_interface(self):
        """Enhanced API Documentation - Swagger-like interface with navigation"""
        docs_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>WhisperS2T API Documentation</title>
            <meta charset="utf-8">
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: Arial, sans-serif; line-height: 1.6; background: #f5f5f5; margin: 0; }}
                
                /* Navigation */
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
                .nav-title {{ font-size: 1.5em; font-weight: bold; }}
                .nav-links {{ display: flex; gap: 20px; }}
                .nav-links a {{
                    color: white;
                    text-decoration: none;
                    padding: 8px 16px;
                    border-radius: 5px;
                    transition: background 0.3s;
                }}
                .nav-links a:hover {{ background: rgba(255,255,255,0.2); }}
                .nav-links a.active {{ background: rgba(255,255,255,0.3); }}
                
                .container {{
                    max-width: 1200px;
                    margin: 20px auto;
                    background: white;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #333;
                    border-bottom: 3px solid #667eea;
                    padding-bottom: 10px;
                }}
                h2 {{
                    color: #667eea;
                    margin: 30px 0 15px 0;
                }}
                h3 {{
                    color: #555;
                    margin: 20px 0 10px 0;
                }}
                .endpoint {{
                    background: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 5px;
                    margin: 15px 0;
                    padding: 15px;
                }}
                .method {{
                    display: inline-block;
                    padding: 4px 8px;
                    color: white;
                    border-radius: 3px;
                    font-weight: bold;
                    margin-right: 10px;
                }}
                .GET {{ background: #28a745; }}
                .POST {{ background: #007bff; }}
                .WS {{ background: #6610f2; }}
                code {{
                    background: #f8f9fa;
                    padding: 2px 5px;
                    border-radius: 3px;
                    font-family: 'Courier New', monospace;
                }}
                pre {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    overflow-x: auto;
                }}
                .try-button {{
                    background: #28a745;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    cursor: pointer;
                    margin-top: 10px;
                }}
                .try-button:hover {{ background: #218838; }}
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
                        <a href="/docs" class="nav-link active">📚 API Docs</a>
                        <a href="/demo" class="nav-link">🎯 Demo</a>
                        <a href="/health" class="nav-link">🏥 Health</a>
                    </div>
                </div>
            </div>
            
            <div class="container">
                <h1>🎤 WhisperS2T API Documentation</h1>
                <p><strong>Version:</strong> {self.version} | <strong>Base URL:</strong> http://your-server:5001</p>

                <h2>📋 Available Endpoints</h2>
                
                <div class="endpoint">
                    <h3><span class="method GET">GET</span> /health</h3>
                    <p><strong>Description:</strong> Health check endpoint for monitoring</p>
                    <p><strong>Response:</strong> JSON object with system status, uptime, and service information</p>
                    <pre>{{"status": "healthy", "version": "{self.version}", "whisper_available": true, "uptime": "2h 15m 30s"}}</pre>
                    <button class="try-button" onclick="tryEndpoint('/health', 'GET')">Try it out</button>
                    <div id="result-health"></div>
                </div>
                
                <div class="endpoint">
                    <h3><span class="method POST">POST</span> /transcribe</h3>
                    <p><strong>Description:</strong> Upload and transcribe audio files</p>
                    <p><strong>Parameters:</strong></p>
                    <ul>
                        <li><code>audio</code> (file, required): Audio file to transcribe</li>
                        <li><strong>Max size:</strong> 100MB</li>
                        <li><strong>Supported formats:</strong> WAV, MP3, M4A, FLAC</li>
                    </ul>
                    <pre>{{"text": "Transcribed text content", "language": "en", "timestamp": "2025-06-29T18:30:00"}}</pre>
                    <p><strong>Example:</strong></p>
                    <pre>curl -X POST -F "audio=@recording.wav" http://your-server:5001/transcribe</pre>
                </div>
                
                <div class="endpoint">
                    <h3><span class="method POST">POST</span> /api/transcribe-live</h3>
                    <p><strong>Description:</strong> Real-time transcription for live recordings</p>
                    <p><strong>Parameters:</strong></p>
                    <ul>
                        <li><code>audio</code> (file, required): Live audio data</li>
                        <li><code>language</code> (string, optional): Target language (auto, de, en, fr, es, it)</li>
                    </ul>
                    <pre>{{"text": "Live transcribed text", "language": "de", "timestamp": "2025-06-29T18:30:00"}}</pre>
                </div>
                
                <div class="endpoint">
                    <h3><span class="method GET">GET</span> /api/status</h3>
                    <p><strong>Description:</strong> Detailed API status and system information</p>
                    <p><strong>Response:</strong> Comprehensive system status including statistics and endpoints</p>
                    <pre>{{"service": "WhisperS2T Enhanced Appliance", "whisper": {{"available": true}}, "statistics": {{"total_transcriptions": 42}}}}</pre>
                    <button class="try-button" onclick="tryEndpoint('/api/status', 'GET')">Try it out</button>
                    <div id="result-status"></div>
                </div>
                
                <div class="endpoint">
                    <h3><span class="method WS">WebSocket</span> /socket.io/</h3>
                    <p><strong>Description:</strong> Real-time WebSocket communication for live speech</p>
                    <p><strong>Events:</strong></p>
                    <ul>
                        <li><code>connect</code>: Establish WebSocket connection</li>
                        <li><code>audio_chunk</code>: Send audio data for real-time transcription</li>
                        <li><code>transcription_result</code>: Receive transcription results</li>
                        <li><code>transcription_error</code>: Receive error notifications</li>
                        <li><code>start_recording</code>: Start live recording session</li>
                        <li><code>stop_recording</code>: Stop live recording session</li>
                    </ul>
                    <pre>// JavaScript WebSocket Example
const socket = io();
socket.on('connection_status', (data) => {{
    console.log('Connected:', data);
}});
socket.emit('audio_chunk', {{audio_data: audioBlob}});</pre>
                </div>
                
                <h2>🔧 Administrative Endpoints</h2>
                
                <div class="endpoint">
                    <h3><span class="method GET">GET</span> /admin</h3>
                    <p><strong>Description:</strong> Administrative dashboard with system monitoring</p>
                    <p><strong>Features:</strong> Real-time statistics, system information, quick actions</p>
                </div>
                
                <div class="endpoint">
                    <h3><span class="method GET">GET</span> /demo</h3>
                    <p><strong>Description:</strong> Interactive demo interface for testing functionality</p>
                    <p><strong>Features:</strong> Health check, file upload test, WebSocket test</p>
                </div>
                
                <h2>🌍 Supported Languages</h2>
                <p><strong>Automatic Detection:</strong> <code>auto</code> (default)</p>
                <p><strong>Specific Languages:</strong> <code>de</code> (German), <code>en</code> (English), <code>fr</code> (French), <code>es</code> (Spanish), <code>it</code> (Italian)</p>
                
                <h2>📝 Usage Examples</h2>
                
                <h3>File Upload (cURL)</h3>
                <pre>curl -X POST -F "audio=@recording.wav" http://localhost:5001/transcribe</pre>
                
                <h3>Live Transcription with Language</h3>
                <pre>curl -X POST -F "audio=@live_audio.wav" -F "language=de" http://localhost:5001/api/transcribe-live</pre>
                
                <h3>Health Check</h3>
                <pre>curl http://localhost:5001/health</pre>
                
                <h2>⚠️ Error Responses</h2>
                <div class="endpoint">
                    <h3>Common Error Format</h3>
                    <pre>{{"error": "Error description", "timestamp": "2025-06-29T18:30:00"}}</pre>
                    <p><strong>HTTP Status Codes:</strong></p>
                    <ul>
                        <li><code>400</code>: Bad Request (missing parameters, invalid file)</li>
                        <li><code>413</code>: Payload Too Large (file > 100MB)</li>
                        <li><code>500</code>: Internal Server Error (transcription failed)</li>
                        <li><code>503</code>: Service Unavailable (Whisper model not loaded)</li>
                    </ul>
                </div>
                
                <h2>🚀 Getting Started</h2>
                <ol>
                    <li>Check system health: <code>GET /health</code></li>
                    <li>Upload a test audio file: <code>POST /transcribe</code></li>
                    <li>Try the demo interface: <a href="/demo">Demo Page</a></li>
                    <li>Monitor system: <a href="/admin">Admin Panel</a></li>
                </ol>
            </div>
            
            <script>
                async function tryEndpoint(endpoint, method) {{
                    const resultDiv = document.getElementById('result-' + endpoint.replace('/', '').replace('/', '-'));
                    try {{
                        resultDiv.innerHTML = '<div style="background: #fff3cd; padding: 10px; border-radius: 4px; margin-top: 10px;">🔄 Testing...</div>';
                        
                        const response = await fetch(endpoint);
                        const data = await response.json();
                        
                        resultDiv.innerHTML = '<div style="background: #d4edda; padding: 10px; border-radius: 4px; margin-top: 10px;"><strong>✅ Response:</strong><br><pre>' + JSON.stringify(data, null, 2) + '</pre></div>';
                    }} catch (error) {{
                        resultDiv.innerHTML = '<div style="background: #f8d7da; padding: 10px; border-radius: 4px; margin-top: 10px;"><strong>❌ Error:</strong> ' + error.message + '</div>';
                    }}
                }}
            </script>
        </body>
        </html>
        """
        return docs_html
