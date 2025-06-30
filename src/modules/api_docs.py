"""
API Documentation Module with Real SwaggerUI
Provides professional API documentation interface using SwaggerUI
Replaces custom HTML with industry-standard documentation
"""

import logging

from flask import jsonify, request

logger = logging.getLogger(__name__)


class APIDocs:
    """Manages SwaggerUI API documentation interface"""

    def __init__(self, version="0.7.2"):
        self.version = version

    def get_current_base_url(self, request_obj):
        """Get current base URL dynamically from request"""
        return f"{request_obj.scheme}://{request_obj.host}"

    def get_openapi_spec(self, request_obj):
        """Generate OpenAPI 3.0 specification for SwaggerUI"""
        base_url = self.get_current_base_url(request_obj)

        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "WhisperS2T Enhanced Appliance API",
                "description": "Professional Speech-to-Text API with Live Processing & File Upload",
                "version": self.version,
                "contact": {"name": "WhisperS2T Team"},
                "license": {"name": "MIT"},
            },
            "servers": [{"url": base_url, "description": "WhisperS2T Server"}],
            "paths": {
                "/health": {
                    "get": {
                        "summary": "Health Check",
                        "description": "Check system health and status",
                        "responses": {
                            "200": {
                                "description": "System health information",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "status": {"type": "string", "example": "healthy"},
                                                "whisper_available": {"type": "boolean"},
                                                "version": {"type": "string"},
                                                "uptime_seconds": {"type": "number"},
                                                "total_transcriptions": {"type": "integer"},
                                                "active_connections": {"type": "integer"},
                                            },
                                        }
                                    }
                                },
                            }
                        },
                    }
                },
                "/transcribe": {
                    "post": {
                        "summary": "Upload File Transcription",
                        "description": "Upload audio file for transcription",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "multipart/form-data": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "audio": {
                                                "type": "string",
                                                "format": "binary",
                                                "description": "Audio file (WAV, MP3, M4A, FLAC)",
                                            }
                                        },
                                        "required": ["audio"],
                                    }
                                }
                            },
                        },
                        "responses": {
                            "200": {
                                "description": "Transcription successful",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "text": {"type": "string"},
                                                "language": {"type": "string"},
                                                "timestamp": {"type": "string", "format": "date-time"},
                                            },
                                        }
                                    }
                                },
                            },
                            "400": {"description": "Bad request (no file, invalid format)"},
                            "413": {"description": "File too large (max 100MB)"},
                            "500": {"description": "Transcription failed"},
                            "503": {"description": "Whisper model unavailable"},
                        },
                    }
                },
                "/api/transcribe-live": {
                    "post": {
                        "summary": "Live Audio Transcription",
                        "description": "Real-time transcription for live recordings",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "multipart/form-data": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "audio": {
                                                "type": "string",
                                                "format": "binary",
                                                "description": "Live audio data",
                                            },
                                            "language": {
                                                "type": "string",
                                                "enum": ["auto", "de", "en", "fr", "es", "it"],
                                                "default": "auto",
                                                "description": "Target language for transcription",
                                            },
                                        },
                                        "required": ["audio"],
                                    }
                                }
                            },
                        },
                        "responses": {
                            "200": {
                                "description": "Live transcription successful",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "text": {"type": "string"},
                                                "language": {"type": "string"},
                                                "timestamp": {"type": "string", "format": "date-time"},
                                            },
                                        }
                                    }
                                },
                            }
                        },
                    }
                },
                "/api/status": {
                    "get": {
                        "summary": "Detailed API Status",
                        "description": "Comprehensive system status and statistics",
                        "responses": {
                            "200": {
                                "description": "Detailed system information",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "service": {"type": "string"},
                                                "version": {"type": "string"},
                                                "whisper": {
                                                    "type": "object",
                                                    "properties": {
                                                        "available": {"type": "boolean"},
                                                        "model_loaded": {"type": "boolean"},
                                                        "model_type": {"type": "string"},
                                                    },
                                                },
                                                "statistics": {
                                                    "type": "object",
                                                    "properties": {
                                                        "uptime_seconds": {"type": "number"},
                                                        "total_transcriptions": {"type": "integer"},
                                                        "active_websocket_connections": {"type": "integer"},
                                                    },
                                                },
                                                "endpoints": {"type": "object"},
                                                "architecture": {"type": "object"},
                                            },
                                        }
                                    }
                                },
                            }
                        },
                    }
                },
            },
            "components": {
                "schemas": {
                    "Error": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string"},
                            "timestamp": {"type": "string", "format": "date-time"},
                        },
                    }
                }
            },
        }

        return openapi_spec

    def get_swagger_config(self):
        """Get SwaggerUI configuration"""
        return {
            "app_name": "WhisperS2T API Documentation",
            "dom_id": "#swagger-ui",
            "url": "/api/openapi.json",
            "layout": "StandaloneLayout",
            "deepLinking": True,
        }
