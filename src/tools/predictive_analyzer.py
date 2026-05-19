import subprocess
import sys
import os

def analyze_git_history(path):
    print(f"Analyzing git risk for {path}...")
    try:
        # Hotspot detection: Find files with most churn/changes
        result = subprocess.run(['git', '-C', path, 'log', '--pretty=format:', '--name-only'],
                                capture_output=True, text=True)
        files = result.stdout.split('\n')
        file_counts = {}
        for f in files:
            if f: file_counts[f] = file_counts.get(f, 0) + 1

        # Identify top 5 hotspots
        hotspots = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        return hotspots
    except Exception as e:
        return []

if __name__ == "__main__":
    hotspots = analyze_git_history(sys.argv[1])
    if hotspots:
        for f, count in hotspots:
            print(f"HIGH RISK: {f} changed {count} times. Proactive fix recommended.")
    else:
        print("No git history found or analysis failed.")
