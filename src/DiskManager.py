import os
import subprocess

def get_file_info(file, network=False):
    try:
        if network:
            process = subprocess.check_output(f"df '{file}' --block-size=1000 -T | awk 'NR==1 {{next}} {{print $1,$2,$3,$4,$5,$7; exit}}'", shell=True, timeout=1)
        else:
            process = subprocess.check_output(f"df '{file}' --block-size=1000 -T | awk 'NR==1 {{next}} {{print $1,$2,$3,$4,$5,$7; exit}}'", shell=True)

        if len(process.decode("utf-8").strip().split(" ")) == 6:
            keys = ["device", "fstype", "total_kb", "usage_kb", "free_kb", "mountpoint"]
            obj = dict(zip(keys, process.decode("utf-8").strip().split(" ")))
            try:
                obj["usage_percent"] = (int(obj['total_kb']) - int(obj['free_kb'])) / int(obj['total_kb'])
            except:
                obj["usage_percent"] = 0
            try:
                obj["free_percent"] = int(obj['free_kb']) / int(obj['total_kb'])
            except:
                obj["free_percent"] = 0
        else:
            obj = {"device": "", "fstype": "", "total_kb": 0, "usage_kb": 0, "free_kb": 0, "mountpoint": "",
                   "usage_percent": 0, "free_percent": 0}
    except subprocess.TimeoutExpired:
        print("timeout error on {}".format(file))
        return None
    return obj

def get_uuid_from_dev(dev_path):
    process = subprocess.run(["lsblk", "-o", "PATH,UUID", "--raw"], capture_output=True, text=True)
    if process.returncode != 0:
        return ""

    lines = process.stdout.strip().split("\n")
    for line in lines:
        parts = line.split()
        if parts[0] == dev_path:
            return parts[1]

    return ""

def is_drive_automounted(dev_path):
    uuid = get_uuid_from_dev(dev_path)

    process = subprocess.run(["grep", "-E", f"{dev_path}|{uuid}", "/etc/fstab"], capture_output=True, text=True)
    if process.returncode != 0:
        return False

    lines = process.stdout.strip().split("\n")
    for line in lines:
        if not line.startswith("#"):
            return True

    return False

def set_automounted(dev_path, value):
    if value and not is_drive_automounted(dev_path):
        partition = dev_path.split("/")[-1]  # /dev/sda1 -> sda1
        fstab_string = f"{dev_path} /mnt/{partition} auto nosuid,nodev,nofail,x-gvfs-show 0 0"

        with open("/etc/fstab", "a") as f:
            f.write(f"\n{fstab_string}")
    elif not value and is_drive_automounted(dev_path):
        uuid = get_uuid_from_dev(dev_path)
        cmd = ["sudo", "sed", "-ri", f"/({dev_path}|{uuid})/d", "/etc/fstab"]
        subprocess.run(cmd)

def get_filesystem_of_partition(partition_path):
    process = subprocess.run(["lsblk", "-o", "TYPE,PATH,FSTYPE", "-r"], capture_output=True, text=True)
    if process.returncode != 0:
        return "-"

    lines = process.stdout.strip().split("\n")
    for line in lines:
        parts = line.split()
        if parts[1] == partition_path:
            return parts[2]

    return "-"

