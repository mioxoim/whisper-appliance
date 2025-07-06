"""
Enterprise Update Package
Professional enterprise features for WhisperS2T Update System

🎯 ENTERPRISE WRAPPER: Extends modular update architecture with enterprise features
- Enhanced deployment detection with container type recognition
- Professional Flask API integration
- Enterprise-grade logging and audit trails
- Permission-safe operations for LXC environments

Components:
- EnterpriseDeploymentDetector: Enhanced deployment detection
- EnterpriseLogger: Professional audit logging
- integrate_with_flask_app: Complete Flask API integration

Author: WhisperS2T Enterprise Team
Version: 0.8.0
"""

from .detector import EnterpriseDeploymentDetector, EnterpriseDeploymentType
from .integration import integrate_with_flask_app
from .logger import EnterpriseLogger

__version__ = "0.8.0"

# Backward compatibility aliases
DeploymentDetector = EnterpriseDeploymentDetector
DeploymentType = EnterpriseDeploymentType

__all__ = [
    # Main enterprise classes
    "EnterpriseDeploymentDetector",
    "EnterpriseDeploymentType",
    "EnterpriseLogger",
    # Flask integration
    "integrate_with_flask_app",
    # Backward compatibility aliases
    "DeploymentDetector",
    "DeploymentType",
]
