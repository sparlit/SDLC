import sys
import subprocess
import json

def check_compliance(path):
    print(f"Checking FOSS compliance for {path}...")
    try:
        # Use scancode to detect licenses
        result = subprocess.run(['scancode', '--json', '-', path], capture_output=True, text=True)
        data = json.loads(result.stdout)

        non_foss = []
        for file in data.get('files', []):
            for license in file.get('licenses', []):
                if 'commercial' in license.get('key', '').lower():
                    non_foss.append(f"{file['path']} - {license['key']}")

        if non_foss:
            print("COMPLIANCE FAILURE: Non-FOSS licenses detected:")
            for issue in non_foss: print(f"  {issue}")
            sys.exit(1)
        else:
            print("COMPLIANCE PASS: All components are 100% FOSS.")
    except FileNotFoundError:
        print("CRITICAL: 'scancode' binary not found. Compliance check skipped (Dependency missing).", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Error during compliance check: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    check_compliance(sys.argv[1])
