"""
Health check HTTP server module
"""
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler

logger = logging.getLogger(__name__)


class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP handler for health check"""
    
    def do_GET(self):
        """Handler for GET requests"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "healthy"}')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Silence HTTP server logs"""
        pass


class HealthCheckServer:
    """Health check server"""
    
    def __init__(self, port: int):
        """
        Initializes the health check server
        
        Args:
            port: Server port
        """
        self.port = port
        self.server = None
    
    def start(self):
        """Starts the health check server"""
        self.server = HTTPServer(('0.0.0.0', self.port), HealthCheckHandler)
        logger.info(f"Health check server listening on port {self.port}")
        self.server.serve_forever()
    
    def stop(self):
        """Stops the health check server"""
        if self.server:
            self.server.shutdown()
            logger.info("Health check server stopped")
