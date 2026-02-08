import http.server
import ssl
import socket

def get_real_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

ip = get_real_ip()
port = 8000
httpd = http.server.HTTPServer(('0.0.0.0', port), http.server.SimpleHTTPRequestHandler)

# 使用临时生成的证书 (由 start.sh 生成)
httpd.socket = ssl.wrap_socket(httpd.socket, certfile='./cert.pem', keyfile='./key.pem', server_side=True)

print(f"HTTPS 服务器已启动: https://{ip}:{port}")
httpd.serve_forever()
