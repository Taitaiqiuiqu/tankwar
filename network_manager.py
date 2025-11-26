# 网络通信模块，负责P2P连接和消息传递
import socket
import threading
import json
import time

class NetworkManager:
    def __init__(self, username="玩家"):
        self.username = username
        self.connected = False
        self.socket = None
        self.server_socket = None
        self.peer_ip = None
        self.peer_port = 5555
        self.local_ip = self.get_local_ip()
        self.local_port = 5555
        self.message_queue = []
        self.threads = []
        self.running = False
        self.peer_id = None
        self.host_id = None
    
    def get_local_ip(self):
        """
        获取本地IP地址
        """
        try:
            # 创建一个临时socket连接来获取本地IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # 连接到一个公共服务器
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception as e:
            print(f"获取本地IP失败: {e}")
            return "127.0.0.1"  # 默认返回本地回环地址
    
    def start_server(self):
        """
        启动服务器，等待其他玩家连接
        """
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.local_ip, self.local_port))
            self.server_socket.listen(3)  # 最多接受3个连接（总共4名玩家）
            self.running = True
            
            # 启动服务器线程
            server_thread = threading.Thread(target=self.accept_connections, daemon=True)
            server_thread.start()
            self.threads.append(server_thread)
            
            print(f"服务器已启动，IP: {self.local_ip}, 端口: {self.local_port}")
            return True
        except Exception as e:
            print(f"启动服务器失败: {e}")
            return False
    
    def accept_connections(self):
        """
        接受新连接的线程函数
        """
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                self.socket = conn
                self.peer_ip = addr[0]
                self.connected = True
                
                # 启动接收消息线程
                receive_thread = threading.Thread(target=self.receive_messages, args=(conn,), daemon=True)
                receive_thread.start()
                self.threads.append(receive_thread)
                
                # 发送连接确认消息
                self.send_message({
                    "type": "connection_established",
                    "host_id": self.username,
                    "peer_id": self.peer_id
                })
                
                print(f"玩家已连接: {addr}")
            except Exception as e:
                if self.running:  # 只有在服务器运行时才打印错误
                    print(f"接受连接失败: {e}")
    
    def connect(self, peer_ip, peer_port=5555):
        """
        连接到其他玩家的服务器
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((peer_ip, peer_port))
            self.peer_ip = peer_ip
            self.peer_port = peer_port
            self.connected = True
            
            # 启动接收消息线程
            receive_thread = threading.Thread(target=self.receive_messages, args=(self.socket,), daemon=True)
            receive_thread.start()
            self.threads.append(receive_thread)
            
            print(f"已连接到 {peer_ip}:{peer_port}")
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            self.connected = False
            return False
    
    def receive_messages(self, conn):
        """
        接收消息的线程函数
        """
        buffer = ""
        while self.running and self.connected:
            try:
                data = conn.recv(4096).decode("utf-8")
                if not data:
                    # 连接关闭
                    self.connected = False
                    print("连接已关闭")
                    break
                
                buffer += data
                # 处理缓冲区中的消息（假设消息以换行符分隔）
                while "\n" in buffer:
                    message_str, buffer = buffer.split("\n", 1)
                    try:
                        message = json.loads(message_str)
                        self.message_queue.append(message)
                        # 处理连接确认消息，获取peer_id
                        if message.get("type") == "connection_established":
                            self.host_id = message.get("host_id")
                            if message.get("peer_id") is None:
                                # 为客户端分配peer_id
                                self.peer_id = f"client_{int(time.time()) % 1000}"
                    except json.JSONDecodeError:
                        print(f"收到无效的JSON消息: {message_str}")
            except Exception as e:
                if self.running and self.connected:  # 只有在连接正常时才打印错误
                    print(f"接收消息失败: {e}")
                    self.connected = False
    
    def send_message(self, message):
        """
        发送消息给连接的玩家
        """
        try:
            if self.connected and self.socket:
                message_str = json.dumps(message) + "\n"
                self.socket.sendall(message_str.encode("utf-8"))
                return True
            else:
                print("未连接，无法发送消息")
                return False
        except Exception as e:
            print(f"发送消息失败: {e}")
            self.connected = False
            return False
    
    def get_messages(self):
        """
        获取接收到的消息列表
        """
        messages = self.message_queue.copy()
        self.message_queue.clear()
        return messages
    
    def disconnect(self):
        """
        断开连接，清理资源
        """
        self.running = False
        
        # 关闭socket
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass
            self.server_socket = None
        
        # 等待线程结束
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1.0)  # 等待1秒
        
        self.threads.clear()
        self.connected = False
        self.message_queue.clear()
        print("已断开连接并清理资源")