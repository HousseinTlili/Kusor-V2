# frontend/serve_frontend.py
"""
High-performance SPA Web Server for KUSOR v3 Angular UI.
Serves static assets from dist/kusor-ui/browser/ with HTML5 fallback for SPA client-side routes,
and proxies API calls to http://127.0.0.1:5000.
"""

import http.server
import socketserver
import os
import urllib.request
import urllib.error

PORT = 4200
DIST_DIR = os.path.join(os.path.dirname(__file__), "kusor-ui/dist/kusor-ui/browser")
BACKEND_URL = "http://127.0.0.1:5000"


class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIST_DIR, **kwargs)

    def do_GET(self):
        # Proxy /api requests to Flask
        if self.path.startswith("/api"):
            self._proxy_request()
            return

        # Check if requested static file exists in dist
        req_path = self.path.split("?")[0].lstrip("/")
        full_path = os.path.join(DIST_DIR, req_path)
        if not os.path.exists(full_path) or os.path.isdir(full_path):
            # Fallback to index.html for Angular HTML5 routing (/kyc, /credit, /graph, etc.)
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith("/api"):
            self._proxy_request()
            return
        self.send_error(405, "Method Not Allowed")

    def do_PUT(self):
        if self.path.startswith("/api"):
            self._proxy_request()
            return
        self.send_error(405, "Method Not Allowed")

    def do_DELETE(self):
        if self.path.startswith("/api"):
            self._proxy_request()
            return
        self.send_error(405, "Method Not Allowed")

    def _proxy_request(self):
        target_url = f"{BACKEND_URL}{self.path}"
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        req = urllib.request.Request(target_url, data=body, method=self.command)
        for key, value in self.headers.items():
            if key.lower() not in ["host", "content-length"]:
                req.add_header(key, value)

        try:
            with urllib.request.urlopen(req) as response:
                self.send_response(response.status)
                for key, value in response.headers.items():
                    if key.lower() not in ["transfer-encoding", "content-length"]:
                        self.send_header(key, value)
                resp_body = response.read()
                self.send_header("Content-Length", str(len(resp_body)))
                self.end_headers()
                self.wfile.write(resp_body)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for key, value in e.headers.items():
                if key.lower() not in ["transfer-encoding", "content-length"]:
                    self.send_header(key, value)
            resp_body = e.read()
            self.send_header("Content-Length", str(len(resp_body)))
            self.end_headers()
            self.wfile.write(resp_body)
        except Exception as err:
            self.send_error(502, f"Bad Gateway: {err}")


def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", PORT), SPAHandler) as httpd:
        print(f"🚀 KUSOR v3 Angular UI running at http://localhost:{PORT}")
        httpd.serve_forever()


if __name__ == "__main__":
    run_server()
