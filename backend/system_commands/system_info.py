import subprocess
import shutil
import platform


def get_info() -> str:
    info = []

    info.append(f"macOS {platform.mac_ver()[0]}")
    info.append(f"Chip: {platform.processor() or 'Apple Silicon'}")

    battery = subprocess.run(
        ["pmset", "-g", "batt"], capture_output=True, text=True
    )
    for line in battery.stdout.splitlines():
        if "%" in line:
            info.append(f"Battery: {line.strip()}")
            break

    disk = shutil.disk_usage("/")
    free_gb = disk.free / (1024 ** 3)
    total_gb = disk.total / (1024 ** 3)
    info.append(f"Disk: {free_gb:.0f}GB free / {total_gb:.0f}GB total")

    wifi = subprocess.run(
        ["networksetup", "-getairportnetwork", "en0"],
        capture_output=True, text=True
    )
    if wifi.returncode == 0:
        info.append(f"WiFi: {wifi.stdout.strip()}")

    return "\n".join(info)
