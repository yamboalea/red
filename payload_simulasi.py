import time
import datetime

# File log untuk "memantau" aktivitas
LOG_FILE = "activity_log.txt"

# Pesan ini mensimulasikan data yang "dikirim"
print("Payload simulasi aktif. Menulis log setiap 5 detik. Tekan Ctrl+C untuk berhenti.")

with open(LOG_FILE, "a") as f:
    f.write(f"--- Sesi log dimulai pada {datetime.datetime.now()} ---\n")

try:
    while True:
        # Dapatkan waktu saat ini
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Pesan log yang akan ditulis
        log_entry = f"[{timestamp}] Payload 'heartbeat' aktif.\n"
        
        # Tulis ke file log
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)
            
        # Tunggu selama 5 detik
        time.sleep(5)
except KeyboardInterrupt:
    print("\nPayload simulasi dihentikan.")
    with open(LOG_FILE, "a") as f:
        f.write(f"--- Sesi log dihentikan pada {datetime.datetime.now()} ---\n\n")
