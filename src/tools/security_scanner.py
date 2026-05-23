import subprocess
import sys
import os

def run_security_scan(target_dir):
    print(f"IQ400 Security Audit: Scanning {target_dir} for vulnerabilities...")
    try:
        # Run bandit recursively, filtering for High severity issues
        # -r: recursive
        # -lll: severity level high
        # --format json: for structured output (though we'll print plain text for the user)
        result = subprocess.run(
            ['bandit', '-r', target_dir, '-lll', '--quiet'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            if not result.stdout.strip():
                 print("IQ400 Security Audit: PASS - No high-severity vulnerabilities detected.")
            else:
                 print("IQ400 Security Audit: REPORT")
                 print(result.stdout)
            return True
        else:
            print("IQ400 Security Audit: FAILURE - High-severity vulnerabilities found!")
            print(result.stdout)
            print(result.stderr)
            return False
    except FileNotFoundError:
        print("CRITICAL: 'bandit' binary not found. Security audit skipped.", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error during security audit: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "src"
    success = run_security_scan(target)
    sys.exit(0 if success else 1)
