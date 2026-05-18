import json
import subprocess
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


PORT = 8099


def get_hostname_ips():
    output = subprocess.check_output(["hostname", "-I"], text=True).strip()
    return [ip for ip in output.split() if ip]


def choose_primary_ip(ips):
    for ip in ips:
        if "." in ip and not ip.startswith("127."):
            return ip
    return ips[0] if ips else ""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            ips = get_hostname_ips()
            primary_ip = choose_primary_ip(ips)
            payload = {
                "primary_ip": primary_ip,
                "hostname_I": " ".join(ips),
                "quiz_url": f"http://{primary_ip}:8081" if primary_ip else "",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            status = 200
        except Exception as exc:
            payload = {"error": str(exc)}
            status = 500

        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()
