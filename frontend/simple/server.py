#!/usr/bin/env python3
"""
Simple HTTP server for the GitHub PR Metrics frontend
Serves static files and handles basic routing
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

# Set the directory to serve files from
FRONTEND_DIR = Path(__file__).parent
os.chdir(FRONTEND_DIR)

# Configuration
PORT = 3000
HOST = 'localhost'

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers to allow frontend to communicate with backend
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_GET(self):
        # Serve index.html for all routes (SPA behavior)
        if self.path == '/' or not os.path.exists(self.path.lstrip('/')):
            self.path = '/index.html'
        return super().do_GET()

def start_server():
    """Start the development server"""
    try:
        with socketserver.TCPServer((HOST, PORT), CustomHTTPRequestHandler) as httpd:
            print(f"""
🚀 GitHub PR Metrics Frontend Server Starting...

📱 Frontend URL: http://{HOST}:{PORT}
🔗 Backend API: http://localhost:8000
📚 API Docs: http://localhost:8000/docs

Press Ctrl+C to stop the server
            """)
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        sys.exit(0)
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {PORT} is already in use. Please stop other servers or use a different port.")
        else:
            print(f"❌ Server error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    start_server()