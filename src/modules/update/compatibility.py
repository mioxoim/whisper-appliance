"""
Update Compatibility Checker
Professional compatibility checking for WhisperS2T modules and dependencies
"""

import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)


class UpdateCompatibilityChecker:
    """
    Professional compatibility checker for modules and dependencies
    """

    def __init__(self, app_root: str):
        self.app_root = app_root

    def check_module_compatibility(self, target_version: str) -> Dict:
        """
        Check if current modules are compatible with target version

        Args:
            target_version: Version to check compatibility against

        Returns:
            Dict: Compatibility status for each module
        """
        results = {"compatible": [], "incompatible": [], "unknown": [], "total_checked": 0}

        try:
            # Check Python modules in requirements.txt
            requirements_file = os.path.join(self.app_root, "requirements.txt")
            if os.path.exists(requirements_file):
                results.update(self._check_python_requirements(requirements_file, target_version))

            # Check custom modules
            modules_dir = os.path.join(self.app_root, "src", "modules")
            if os.path.exists(modules_dir):
                results.update(self._check_custom_modules(modules_dir, target_version))

        except Exception as e:
            logger.error(f"Module compatibility check failed: {e}")
            results["error"] = str(e)

        return results

    def _check_python_requirements(self, requirements_file: str, target_version: str) -> Dict:
        """Check Python package compatibility"""
        compatible = []
        incompatible = []
        unknown = []

        try:
            with open(requirements_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        package_name = line.split("==")[0].split(">=")[0].split("<=")[0]
                        # For now, assume all packages are compatible unless proven otherwise
                        compatible.append(f"python-package:{package_name}")

        except Exception as e:
            logger.error(f"Failed to check Python requirements: {e}")

        return {"compatible": compatible, "incompatible": incompatible, "unknown": unknown}

    def _check_custom_modules(self, modules_dir: str, target_version: str) -> Dict:
        """Check custom module compatibility"""
        compatible = []
        incompatible = []
        unknown = []

        try:
            for module_file in os.listdir(modules_dir):
                if module_file.endswith(".py") and not module_file.startswith("__"):
                    module_name = module_file[:-3]  # Remove .py extension
                    # For now, assume all custom modules are compatible
                    compatible.append(f"custom-module:{module_name}")

        except Exception as e:
            logger.error(f"Failed to check custom modules: {e}")

        return {"compatible": compatible, "incompatible": incompatible, "unknown": unknown}
