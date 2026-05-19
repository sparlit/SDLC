import psutil
import sys

def check_hardware():
    cpu_usage = psutil.cpu_percent(interval=1)
    mem_usage = psutil.virtual_memory().percent

    print(f"Hardware Health: CPU {cpu_usage}%, MEM {mem_usage}%")

    if cpu_usage > 90 or mem_usage > 90:
        print("CRITICAL: Hardware stress detected. Throttling AI operations.")
        sys.exit(1)
    else:
        print("Status: STABLE")
        sys.exit(0)

if __name__ == "__main__":
    check_hardware()
