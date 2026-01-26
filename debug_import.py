import sys
import os

# Ensure the current directory is in sys.path
sys.path.append(os.getcwd())

print("Attempting to import function_app...")
try:
    import function_app

    print("Successfully imported function_app")
except Exception as e:
    print(f"Error importing function_app: {e}")
    import traceback

    traceback.print_exc()

print("\nAttempting to import app.main...")
try:
    from app import main

    print("Successfully imported app.main")
except Exception as e:
    print(f"Error importing app.main: {e}")
    import traceback

    traceback.print_exc()
