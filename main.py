from app import create_app
import webbrowser
from threading import Timer
import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

def open_browser():
    ip = get_local_ip()
    url = f"http://{ip}:5000/api/server_qr"
    print(f"[*] Deschid browserul la adresa: {url}")
    webbrowser.open(url)

if __name__ == "__main__":
    app = create_app()
    
    Timer(1.0, open_browser).start()
    
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
