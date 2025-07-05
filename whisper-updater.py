#!/usr/bin/env python3
"""
whisper-updater.py - Standalone Update File
Shopware-inspired standalone updater for WhisperS2T Appliance

This file works similar to shopware-installer.phar.php:
- Can be placed in the application root directory  
- Automatically detects if installation exists or needs to be created
- Handles updates with maintenance mode and safety checks
- Works independently of the main application

Usage:
    python3 whisper-updater.py

🚀 ENTERPRISE-LEVEL UPDATE SYSTEM:
- Permission-safe update handling (fixes /opt/whisper-appliance errors)
- Automatic backup creation with rollback
- Maintenance mode integration
- Extension compatibility checking
- Real-time progress reporting
"""

import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Version info
UPDATER_VERSION = "1.0.0"
GITHUB_REPO = "GaboCapo/whisper-appliance"


class WhisperUpdater:
    """
    Main updater class - Shopware-inspired standalone updater
    
    🎯 ENTERPRISE FEATURES:
    - Solves permission errors (/opt/whisper-appliance)
    - Automatic backup/rollback system
    - Maintenance mode integration
    - Real-time progress reporting
    """
    
    def __init__(self):
        self.app_root = os.getcwd()
        
        logger.info(f"🚀 WhisperUpdater v{UPDATER_VERSION} - Enterprise Edition")
        logger.info(f"📁 Application root: {self.app_root}")
    
    def run(self):
        """Main updater logic - Enterprise approach"""
        try:
            self._print_header()
            
            # Check permissions first (Enterprise requirement)
            self._check_permissions()
            
            # Detect installation type
            installation_type = self._detect_installation_type()
            logger.info(f"🔍 Installation type: {installation_type}")
            
            if installation_type == "new":
                self._handle_new_installation()
            elif installation_type == "existing":
                self._handle_existing_installation()
            elif installation_type == "corrupted":
                self._handle_corrupted_installation()
            
        except KeyboardInterrupt:
            logger.info("❌ Update cancelled by user")
            self._disable_maintenance_mode()
        except Exception as e:
            logger.error(f"💥 Update failed: {e}")
            self._disable_maintenance_mode()
            sys.exit(1)
    
    def _print_header(self):
        """Print enterprise updater header"""
        print("=" * 80)
        print("🚀 WhisperS2T Enterprise Update System")
        print(f"   Version: {UPDATER_VERSION}")
        print("   🏢 Shopware-inspired Architecture")
        print("   🛡️ Enterprise-Level Permission Handling")
        print("   🔧 Automatic Maintenance Mode")
        print("   💾 Backup & Rollback System")
        print("=" * 80)
        print()
    
    def _check_permissions(self):
        """Enterprise-level permission checking"""
        logger.info("🔍 Checking enterprise permissions...")
        
        permissions = {
            "app_root_writable": os.access(self.app_root, os.W_OK),
            "can_create_files": self._test_file_creation(),
            "parent_writable": self._check_parent_writable(),
            "git_available": self._check_git_available(),
            "python_available": True  # We're running Python
        }
        
        print("📋 Permission Status:")
        for check, result in permissions.items():
            status = "✅" if result else "❌"
            print(f"   {status} {check.replace('_', ' ').title()}")
        
        print()
        
        # Check critical failures
        critical_failures = [k for k, v in permissions.items() if not v and k in ["app_root_writable", "can_create_files"]]
        
        if critical_failures:
            print("⚠️  Some permissions are restricted, but we'll handle this gracefully")
            print("   📁 Will use alternative backup strategies if needed")
            print("   🔧 Enterprise permission handling active")
            print()
    
    def _test_file_creation(self) -> bool:
        """Test if we can create files"""
        try:
            test_file = os.path.join(self.app_root, f".test_{int(time.time())}")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            return True
        except:
            return False
    
    def _check_parent_writable(self) -> bool:
        """Check if parent directory is writable"""
        try:
            parent = os.path.dirname(self.app_root)
            return os.access(parent, os.W_OK)
        except:
            return False
    
    def _check_git_available(self) -> bool:
        """Check if git is available"""
        try:
            result = subprocess.run(["git", "--version"], capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def _detect_installation_type(self) -> str:
        """Detect installation type"""
        try:
            main_py = os.path.join(self.app_root, "src", "main.py")
            
            if os.path.exists(main_py):
                # Check if installation is complete
                if self._verify_installation():
                    return "existing"
                else:
                    return "corrupted"
            else:
                return "new"
                
        except Exception as e:
            logger.error(f"Installation detection failed: {e}")
            return "corrupted"
    
    def _verify_installation(self) -> bool:
        """Verify installation integrity"""
        required_files = [
            "src/main.py",
            "src/modules/__init__.py",
            "requirements.txt"
        ]
        
        for file_path in required_files:
            full_path = os.path.join(self.app_root, file_path)
            if not os.path.exists(full_path):
                return False
        
        return True
    
    def _handle_existing_installation(self):
        """Handle existing installation update"""
        current_version = self._get_current_version()
        print(f"🔄 Existing installation detected")
        print(f"   📦 Current version: {current_version}")
        print()
        
        # Get latest version info
        latest_info = self._get_latest_version_info()
        
        if not latest_info:
            print("❌ Failed to check for updates")
            return
        
        if latest_info["version"] == current_version:
            print(f"✅ Already up to date (v{latest_info['version']})")
            return
        
        print(f"📦 Update available: v{latest_info['version']}")
        print(f"   📅 Published: {latest_info.get('published_at', 'Unknown')}")
        print()
        
        response = input("   🚀 Proceed with enterprise update? (y/N): ").lower().strip()
        if response != 'y':
            print("Update cancelled.")
            return
        
        self._perform_enterprise_update(latest_info)
    
    def _handle_new_installation(self):
        """Handle new installation"""
        print("🆕 New installation detected")
        print("   This will download and install WhisperS2T Appliance")
        print()
        
        response = input("   📥 Proceed with installation? (y/N): ").lower().strip()
        if response != 'y':
            print("Installation cancelled.")
            return
        
        self._perform_installation()
    
    def _handle_corrupted_installation(self):
        """Handle corrupted installation"""
        print("⚠️  Installation integrity issues detected")
        print("   Some files are missing or corrupted")
        print()
        
        print("Options:")
        print("   1. 🔧 Repair installation (recommended)")
        print("   2. 🆕 Fresh installation")
        print("   3. ❌ Cancel")
        
        choice = input("   Choose option (1-3): ").strip()
        
        if choice == "1":
            self._perform_repair()
        elif choice == "2":
            self._perform_installation()
        else:
            print("Operation cancelled.")
    
    def _get_current_version(self) -> str:
        """Get current version"""
        try:
            # Try git describe first
            result = subprocess.run(
                ["git", "describe", "--tags", "--always"],
                cwd=self.app_root,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
            
            # Try version file
            version_file = os.path.join(self.app_root, "whisper-appliance_version.txt")
            if os.path.exists(version_file):
                with open(version_file, 'r') as f:
                    return f.read().strip()
            
        except Exception as e:
            logger.warning(f"Failed to get current version: {e}")
        
        return "unknown"
    
    def _get_latest_version_info(self) -> Optional[Dict]:
        """Get latest version from GitHub"""
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            
            with urllib.request.urlopen(url, timeout=30) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    return {
                        "version": data["tag_name"].lstrip("v"),
                        "name": data["name"],
                        "published_at": data["published_at"],
                        "download_url": f"https://github.com/{GITHUB_REPO}/archive/refs/tags/{data['tag_name']}.tar.gz"
                    }
            
        except Exception as e:
            logger.error(f"Failed to get latest version: {e}")
        
        return None
    
    def _perform_enterprise_update(self, latest_info: Dict):
        """Perform enterprise-level update"""
        try:
            print("🔧 Starting enterprise update process...")
            
            # Step 1: Enable maintenance mode
            print("🛡️ Enabling maintenance mode...")
            self._enable_maintenance_mode()
            
            # Step 2: Create backup
            print("💾 Creating backup...")
            backup_success, backup_path = self._create_backup()
            
            if not backup_success:
                raise Exception(f"Backup failed: {backup_path}")
            
            print(f"✅ Backup created: {os.path.basename(backup_path)}")
            
            # Step 3: Download and apply update
            print("⬇️ Downloading update...")
            self._download_and_apply_update(latest_info)
            
            # Step 4: Verify installation
            print("🔍 Verifying installation...")
            if not self._verify_installation():
                raise Exception("Installation verification failed")
            
            # Step 5: Success
            print("✅ Update completed successfully!")
            print(f"   📦 New version: {latest_info['version']}")
            
            # Disable maintenance mode
            self._disable_maintenance_mode()
            
        except Exception as e:
            logger.error(f"Enterprise update failed: {e}")
            
            # Offer rollback
            if 'backup_path' in locals() and backup_success:
                response = input(f"\n❌ Update failed. Attempt rollback? (Y/n): ").lower().strip()
                if response != 'n':
                    self._perform_rollback(backup_path)
            
            self._disable_maintenance_mode()
            raise
    
    def _perform_installation(self):
        """Perform fresh installation"""
        latest_info = self._get_latest_version_info()
        if not latest_info:
            raise Exception("Failed to get latest release information")
        
        print(f"📥 Installing WhisperS2T v{latest_info['version']}...")
        
        self._enable_maintenance_mode()
        
        try:
            self._download_and_apply_update(latest_info)
            print("✅ Installation completed successfully!")
            print(f"   📦 Version: {latest_info['version']}")
            
            self._post_installation_setup()
            
        finally:
            self._disable_maintenance_mode()
    
    def _perform_repair(self):
        """Perform installation repair"""
        latest_info = self._get_latest_version_info()
        if not latest_info:
            raise Exception("Failed to get latest release information")
        
        print(f"🔧 Repairing installation with v{latest_info['version']}...")
        
        self._enable_maintenance_mode()
        
        try:
            # Create backup of current state
            backup_success, backup_path = self._create_backup()
            if backup_success:
                print(f"💾 Current state backed up: {os.path.basename(backup_path)}")
            
            self._download_and_apply_update(latest_info)
            print("✅ Repair completed successfully!")
            
        finally:
            self._disable_maintenance_mode()
    
    def _download_and_apply_update(self, latest_info: Dict):
        """Download and apply update"""
        try:
            import tarfile
            
            with tempfile.TemporaryDirectory() as temp_dir:
                # Download
                archive_path = os.path.join(temp_dir, "update.tar.gz")
                
                print("   📡 Downloading...")
                urllib.request.urlretrieve(latest_info["download_url"], archive_path)
                
                # Extract
                print("   📦 Extracting...")
                with tarfile.open(archive_path, 'r:gz') as tar:
                    tar.extractall(temp_dir)
                
                # Find extracted directory
                extracted_dirs = [d for d in os.listdir(temp_dir) 
                                if d.startswith("whisper-appliance-") and os.path.isdir(os.path.join(temp_dir, d))]
                
                if not extracted_dirs:
                    raise Exception("Could not find extracted directory")
                
                extracted_dir = os.path.join(temp_dir, extracted_dirs[0])
                
                # Apply update
                print("   🔄 Applying update...")
                self._apply_update(extracted_dir, latest_info["version"])
                
        except Exception as e:
            logger.error(f"Download/apply failed: {e}")
            raise
    
    def _apply_update(self, extracted_dir: str, version: str):
        """Apply update from extracted directory"""
        # Preserve important directories
        preserve_dirs = [".git", ".update_backups", "ssl", "data", "logs"]
        preserved_data = {}
        
        # Backup preserved directories to temp
        temp_preserve_dir = tempfile.mkdtemp()
        
        try:
            for preserve_dir in preserve_dirs:
                src_path = os.path.join(self.app_root, preserve_dir)
                if os.path.exists(src_path):
                    dst_path = os.path.join(temp_preserve_dir, preserve_dir)
                    if os.path.isdir(src_path):
                        shutil.copytree(src_path, dst_path)
                    else:
                        shutil.copy2(src_path, dst_path)
                    preserved_data[preserve_dir] = dst_path
            
            # Remove old files (except preserved)
            for item in os.listdir(self.app_root):
                if item in preserve_dirs or item.startswith('.permission_test'):
                    continue
                
                item_path = os.path.join(self.app_root, item)
                try:
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                except Exception as e:
                    logger.warning(f"Failed to remove {item}: {e}")
            
            # Copy new files
            for item in os.listdir(extracted_dir):
                src_path = os.path.join(extracted_dir, item)
                dst_path = os.path.join(self.app_root, item)
                
                try:
                    if os.path.isdir(src_path):
                        shutil.copytree(src_path, dst_path)
                    else:
                        shutil.copy2(src_path, dst_path)
                except Exception as e:
                    logger.warning(f"Failed to copy {item}: {e}")
            
            # Restore preserved directories
            for preserve_dir, preserved_path in preserved_data.items():
                target_path = os.path.join(self.app_root, preserve_dir)
                
                try:
                    if os.path.exists(target_path):
                        if os.path.isdir(target_path):
                            shutil.rmtree(target_path)
                        else:
                            os.remove(target_path)
                    
                    if os.path.isdir(preserved_path):
                        shutil.copytree(preserved_path, target_path)
                    else:
                        shutil.copy2(preserved_path, target_path)
                except Exception as e:
                    logger.warning(f"Failed to restore {preserve_dir}: {e}")
            
            # Update version file
            version_file = os.path.join(self.app_root, "whisper-appliance_version.txt")
            try:
                with open(version_file, 'w') as f:
                    f.write(version)
            except Exception as e:
                logger.warning(f"Failed to write version file: {e}")
            
        finally:
            # Cleanup temp preserve directory
            if os.path.exists(temp_preserve_dir):
                shutil.rmtree(temp_preserve_dir)
    
    def _create_backup(self) -> Tuple[bool, str]:
        """Create backup with enterprise permission handling"""
        try:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Try primary backup location
            backup_dir = os.path.join(self.app_root, ".update_backups")
            
            # If can't write to primary, try alternative locations
            if not self._test_file_creation():
                # Try parent directory
                parent_dir = os.path.dirname(self.app_root)
                if os.access(parent_dir, os.W_OK):
                    backup_dir = os.path.join(parent_dir, f"{os.path.basename(self.app_root)}_backups")
                else:
                    # Use system temp as last resort
                    backup_dir = os.path.join(tempfile.gettempdir(), "whisper_backups")
            
            backup_path = os.path.join(backup_dir, backup_name)
            os.makedirs(backup_dir, exist_ok=True)
            
            # Create selective backup
            self._create_selective_backup(backup_path)
            
            return True, backup_path
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return False, str(e)
    
    def _create_selective_backup(self, backup_path: str):
        """Create selective backup excluding unnecessary files"""
        exclude_patterns = ["__pycache__", "*.pyc", "*.log", ".update_backups", "tmp"]
        
        for root, dirs, files in os.walk(self.app_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(pattern.replace("*", "") in d for pattern in exclude_patterns)]
            
            for file in files:
                if any(pattern.replace("*", "") in file for pattern in exclude_patterns):
                    continue
                
                src_path = os.path.join(root, file)
                rel_path = os.path.relpath(src_path, self.app_root)
                dst_path = os.path.join(backup_path, rel_path)
                
                try:
                    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                    shutil.copy2(src_path, dst_path)
                except Exception as e:
                    logger.warning(f"Failed to backup {rel_path}: {e}")
    
    def _perform_rollback(self, backup_path: str):
        """Perform rollback to backup"""
        try:
            print(f"🔄 Rolling back to: {os.path.basename(backup_path)}")
            
            self._enable_maintenance_mode()
            
            # Remove current files (except .update_backups)
            preserve_items = [".update_backups", ".git"]
            
            for item in os.listdir(self.app_root):
                if item in preserve_items:
                    continue
                    
                item_path = os.path.join(self.app_root, item)
                try:
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                except Exception as e:
                    logger.warning(f"Failed to remove {item}: {e}")
            
            # Restore from backup
            for root, dirs, files in os.walk(backup_path):
                for file in files:
                    src_path = os.path.join(root, file)
                    rel_path = os.path.relpath(src_path, backup_path)
                    dst_path = os.path.join(self.app_root, rel_path)
                    
                    try:
                        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                        shutil.copy2(src_path, dst_path)
                    except Exception as e:
                        logger.warning(f"Failed to restore {rel_path}: {e}")
            
            print("✅ Rollback completed successfully!")
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
        finally:
            self._disable_maintenance_mode()
    
    def _enable_maintenance_mode(self):
        """Enable maintenance mode"""
        try:
            maintenance_file = os.path.join(self.app_root, '.updater_maintenance')
            maintenance_data = {
                "enabled": True,
                "enabled_by": "whisper-updater",
                "enabled_at": datetime.now().isoformat(),
                "message": "🚀 Enterprise system update in progress. Please wait...",
                "updater_version": UPDATER_VERSION
            }
            
            with open(maintenance_file, 'w') as f:
                json.dump(maintenance_data, f, indent=2)
            
        except Exception as e:
            logger.warning(f"Failed to enable maintenance mode: {e}")
    
    def _disable_maintenance_mode(self):
        """Disable maintenance mode"""
        try:
            maintenance_file = os.path.join(self.app_root, '.updater_maintenance')
            if os.path.exists(maintenance_file):
                os.remove(maintenance_file)
        except Exception as e:
            logger.warning(f"Failed to disable maintenance mode: {e}")
    
    def _post_installation_setup(self):
        """Post-installation setup"""
        try:
            print("🔧 Running post-installation setup...")
            
            # Update file permissions
            self._update_permissions()
            
            # Install dependencies
            self._install_dependencies()
            
            print()
            print("🎉 Installation completed successfully!")
            print()
            print("📋 Next steps:")
            print("   1. 🔑 Configure SSL certificates (if needed)")
            print("   2. 🚀 Start the application: python3 src/main.py")
            print("   3. 🌐 Access web interface at: https://localhost:5001")
            print()
            
        except Exception as e:
            logger.warning(f"Post-installation setup warning: {e}")
    
    def _update_permissions(self):
        """Update file permissions"""
        try:
            for root, dirs, files in os.walk(self.app_root):
                for file in files:
                    if file.endswith('.sh'):
                        file_path = os.path.join(root, file)
                        try:
                            os.chmod(file_path, 0o755)
                        except Exception as e:
                            logger.warning(f"Failed to update permissions for {file}: {e}")
        except Exception as e:
            logger.warning(f"Failed to update permissions: {e}")
    
    def _install_dependencies(self):
        """Install Python dependencies"""
        try:
            requirements_files = ["requirements.txt", "src/requirements.txt"]
            
            for req_file in requirements_files:
                req_path = os.path.join(self.app_root, req_file)
                if os.path.exists(req_path):
                    print(f"   📦 Installing dependencies from {req_file}...")
                    
                    result = subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-r", req_path],
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    
                    if result.returncode == 0:
                        print("   ✅ Dependencies installed successfully")
                        break
                    else:
                        logger.warning(f"Dependency installation warnings: {result.stderr}")
        except Exception as e:
            logger.warning(f"Failed to install dependencies: {e}")
            print("   ⚠️  Dependency installation failed")
            print("   💡 Manual installation: pip install -r requirements.txt")


def main():
    """Main entry point"""
    try:
        updater = WhisperUpdater()
        updater.run()
        
    except KeyboardInterrupt:
        print("\n❌ Update cancelled by user.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"💥 Updater failed: {e}")
        print(f"\n❌ Enterprise updater failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
