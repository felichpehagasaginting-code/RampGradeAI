import socket
import uvicorn
from backend.app.main import app

if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 8000))
    sock.listen(128)
    print("[Server] Listening on http://127.0.0.1:8000 (SO_REUSEADDR enabled)")
    
    config = uvicorn.Config(app=app, log_level="info")
    server = uvicorn.Server(config)
    server.run(sockets=[sock])
