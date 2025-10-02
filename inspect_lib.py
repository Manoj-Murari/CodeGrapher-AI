# --- inspect_lib.py ---
import importlib

# The module we want to inspect
module_name = "langgraph.prebuilt"

print(f"--- 🔬 Inspecting module: {module_name} ---")

try:
    # Dynamically import the module
    module = importlib.import_module(module_name)

    # Get a list of all public attributes (names that don't start with '_')
    available_items = [item for item in dir(module) if not item.startswith('_')]

    if available_items:
        print(f"\n✅ Found the following public items in '{module_name}':")
        for item in sorted(available_items):
            print(f"  - {item}")
    else:
        print(f"\n⚠️ No public items found in '{module_name}'.")

except ImportError:
    print(f"\n❌ Error: Could not import the module '{module_name}'.")
except Exception as e:
    print(f"\n❌ An unexpected error occurred: {e}")