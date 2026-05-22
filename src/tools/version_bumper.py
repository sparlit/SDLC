# Version: 1.1.0
# Version: 1.1.0
import sys
import os

def bump_version(path):
    version_file = os.path.join(path, "VERSION")
    if not os.path.exists(version_file):
        with open(version_file, 'w') as f:
            f.write("1.0.0")
        return "1.0.0"

    with open(version_file, 'r') as f:
        version = f.read().strip()

    parts = version.split('.')
    if len(parts) == 3:
        parts[2] = str(int(parts[2]) + 1)
        new_version = '.'.join(parts)
        with open(version_file, 'w') as f:
            f.write(new_version)
        return new_version
    return version

if __name__ == "__main__":
    print(bump_version(sys.argv[1] if len(sys.argv) > 1 else "."))
