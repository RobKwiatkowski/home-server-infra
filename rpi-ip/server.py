import json
import socket
import subprocess
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


PORT = 8099


def get_hostname_ips():
    result = subprocess.run(
        ["hostname", "-I"],
        check=False,
        capture_output=True,
        text=True,
    )
    output = result.stdout.strip()
    if result.returncode == 0 and output:
        return output, [ip for ip in output.split() if ip], None

    error = result.stderr.strip() or f"hostname -I exited with {result.returncode}"
    return "", [], error


def get_route_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("1.1.1.1", 80))
        return sock.getsockname()[0], None
    except OSError as exc:
        return "", str(exc)
    finally:
        sock.close()


def choose_primary_ip(ips):
    for ip in ips:
        if "." in ip and not ip.startswith("127."):
            return ip
    return ips[0] if ips else ""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        hostname_output, ips, command_error = get_hostname_ips()
        primary_ip = choose_primary_ip(ips)

        route_error = None
        if not primary_ip:
            primary_ip, route_error = get_route_ip()

        payload = {
            "primary_ip": primary_ip,
            "hostname_I": hostname_output or primary_ip,
            "quiz_url": f"http://{primary_ip}:8081" if primary_ip else "",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if command_error:
            payload["hostname_error"] = command_error
        if route_error:
            payload["route_error"] = route_error

        status = 200

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
