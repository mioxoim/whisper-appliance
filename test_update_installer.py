import sys
# Add src to path to allow importing modules from src
sys.path.insert(0, "/app/src")

from modules.update.installer import UpdateInstaller

def run_test():
    print("Attempting to instantiate UpdateInstaller with repo_path='/app'")
    try:
        installer = UpdateInstaller(repo_path="/app")
        print("UpdateInstaller instantiated successfully.")
    except Exception as e:
        print(f"Error instantiating UpdateInstaller: {e}")
        return

    print("Calling install_update()...")
    try:
        result = installer.install_update()
        print("install_update() result:")
        print(f"  Success: {result.get('success')}")
        print(f"  Message: {result.get('message')}")
        print(f"  Backup Path: {result.get('backup_path')}")
        print(f"  Restart Required: {result.get('restart_required')}")

        if not result.get('success') and "Permission denied" in str(result.get('message')):
            print("\nTEST FAILED: Permission denied error still present.")
        elif not result.get('success'):
            print(f"\nTEST FAILED: Update failed for other reasons: {result.get('message')}")
        else:
            # Check if pull_result.stdout indicates 'Already up to date.' or similar
            # This part is tricky as the actual output of git pull can vary.
            # For now, success means no permission error and git pull command itself didn't error out.
            if "Already up to date" in str(result.get('message')) or result.get('success'): # Git pull success messages can vary
                 print("\nTEST PASSED (potentially): Update process completed without permission error. Git reported success or already up to date.")
            else:
                 print("\nTEST PASSED: Update process completed without permission error.")


    except Exception as e:
        print(f"Error calling install_update(): {e}")
        print("\nTEST FAILED: Exception during call.")

if __name__ == "__main__":
    run_test()
