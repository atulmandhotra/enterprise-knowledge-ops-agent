from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import threading

PORT = 8080

CHROMA_DIR = Path("/app/chroma_db")
MARKER = CHROMA_DIR / ".ingestion_complete"


class HealthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/health/live":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK")
            return

        if self.path == "/health/ready":
            if MARKER.exists():
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"READY")
            else:
                self.send_response(503)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"NOT READY")
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        # Disable HTTP request logging.
        return


def start_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)

    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True,
    )

    thread.start()

    print(f"Health server started on port {PORT}")