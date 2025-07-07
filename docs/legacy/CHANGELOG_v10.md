# Changelog - OpenAI Whisper Web Interface

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.10.0] - 2025-07-02

### Added
- **Chat History Tab**: New dedicated tab in main interface for viewing transcription history
- **History Management**: Edit and delete individual transcriptions directly from the interface
- **Date Filtering**: Filter transcriptions by date range and source type
- **Search Functionality**: Real-time search through transcription text content
- **Export Functionality**: Export history as JSON or CSV
- **API Endpoints**: Update/delete transcriptions, filter by date range

### Enhanced
- **Main Interface**: Extended from 2 tabs to 3 tabs (Live Speech, Upload, History)
- **User Experience**: Added loading spinners, toast notifications, responsive design
- **ChatHistoryManager**: Added CRUD operations for individual transcription management

### Compatible
- **Preserves All Existing Features**: Live Speech, File Upload, Admin Panel remain unchanged
- **Backward Compatible**: All existing API endpoints continue to work

## [1.0.0-rc1] - 2025-07-01

### 🎯 **MAJOR REFACTORING - Release Candidate 1**
