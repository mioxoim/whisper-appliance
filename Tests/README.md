# 🧪 Tests Directory

## Structure

```
Tests/
├── TestResults/          # Test execution results and feedback
│   └── YYYY-MM-DD-[Feature].md
└── README.md            # This file
```

## Test-Feedback-Loop Workflow

### 1. Development Phase
- Claude develops features on Fedora PC (Development Environment)
- No testing or command execution on development machine

### 2. Testing Request
Claude asks for testing after changes:
```
"✅ TESTING NEEDED: I changed [FEATURE/BUG].

Could you please test:
1. [Specific Function A]
2. [Specific Function B]
3. [Edge Case C]

Should I document the test results?"
```

### 3. User Testing
- User executes tests on Proxmox Container (Test Environment)
- User provides feedback on what works/doesn't work

### 4. Result Documentation
Claude documents results in `/Tests/TestResults/YYYY-MM-DD-[Feature].md`

## Test Environments

### 📍 Development Environment (Fedora PC)
- **Path**: `/home/commander/Code/whisper-appliance`
- **Purpose**: Code development only
- **Access**: Claude (read/write files)

### 📍 Test Environment (Proxmox Container)
- **Path**: `/opt/whisper-appliance`
- **Purpose**: Testing and deployment
- **Access**: User only (Claude requests logs if needed)

## Deployment Targets

- **Primary**: Proxmox LXC → Docker → Whisper Appliance
- **Secondary**: Pure Docker for local development
- **Fallback**: Direct installation without containers
