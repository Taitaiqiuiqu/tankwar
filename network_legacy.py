import socket
import threading
import json
import time
import uuid
import random
import struct

class NetworkManager:
    def __init__(self, username="玩家"):
        self.username = username
        self.peer_id = str(uuid.uuid4())[:8]  # 生成唯一的客户端ID
        self.port = random.randint(50000, 60000)  # 随机端口
        self.server_socket = None
        self.connections = {}
        self.listen_thread = None
        self.running = False
        self.message_handler = None
        self.room_info = None  # 当前房间信息
        self.is_host = False
        self.player_status = {"ready": False}
        
    def set_message_handler(self, handler):
        """设置消息处理函数"""
        self.message_handler = handler
    
    def start_server(self):
        """启动服务器监听连接"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(5)
            self.running = True
            self.listen_thread = threading.Thread(target=self.listen_connections)
            self.listen_thread.daemon = True
            self.listen_thread.start()
            return True, self.get_local_ip()
        except Exception as e:
            return False, str(e)
    
    def listen_connections(self):
        """监听新连接的线程函数"""
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                # 接收客户端的初始信息
                client_info = self.receive_message(client_socket)
                if client_info:
                    client_id = client_info.get('peer_id')
                    username = client_info.get('username')
                    # 向新连接的客户端发送房间信息
                    room_info_msg = {
                        "type": "room_info",
                        "room": self.room_info,
                        "host": self.peer_id,
                        "players": {}
                    }
                    
                    # 如果是房主，发送所有玩家信息
                    if self.is_host:
                        for pid, conn_info in self.connections.items():
                            room_info_msg["players"][pid] = {
                                "username": conn_info["username"],
                                "ready": conn_info.get("ready", False)
                            }
                    
                    self.send_message(client_socket, room_info_msg)
                    
                    # 存储连接信息
                    self.connections[client_id] = {
                        "socket": client_socket,
                        "address": addr,
                        "username": username,
                        "ready": False
                    }
                    
                    # 启动接收消息的线程
                    threading.Thread(target=self.handle_client_messages, 
                                    args=(client_socket, client_id), daemon=True).start()
                    
                    # 如果是房主，通知其他玩家有新玩家加入
                    if self.is_host:
                        self.broadcast_message({
                            "type": "player_joined",
                            "peer_id": client_id,
                            "username": username
                        }, exclude=[client_id])
                    
                    # 通知应用层有新玩家加入
                    if self.message_handler:
                        self.message_handler({
                            "type": "player_joined",
                            "peer_id": client_id,
                            "username": username
                        })
            except Exception as e:
                if self.running:  # 避免在关闭时报告错误
                    print(f"监听连接错误: {e}")
                break
    
    def connect_to_host(self, host_ip, host_port, room_password=""):
        """连接到主机"""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((host_ip, host_port))
            
            # 发送连接请求
            connect_request = {
                "type": "connect_request",
                "peer_id": self.peer_id,
                "username": self.username,
                "password": room_password,
                "port": self.port
            }
            self.send_message(client_socket, connect_request)
            
            # 等待房间信息响应
            response = self.receive_message(client_socket)
            if not response:
                client_socket.close()
                return False, "连接被拒绝"
            
            if response.get("type") == "error":
                client_socket.close()
                return False, response.get("message", "未知错误")
            
            if response.get("type") == "room_info":
                # 连接成功，保存房间信息
                self.room_info = response.get("room")
                self.is_host = False
                
                # 启动接收消息的线程
                host_id = response.get("host")
                self.connections[host_id] = {
                    "socket": client_socket,
                    "address": (host_ip, host_port),
                    "username": "房主",
                    "ready": False
                }
                
                threading.Thread(target=self.handle_client_messages, 
                                args=(client_socket, host_id), daemon=True).start()
                
                # 通知应用层连接成功，并发送房间信息
                if self.message_handler:
                    self.message_handler(response)
                
                return True, "连接成功"
            
            client_socket.close()
            return False, "无效的响应"
        except Exception as e:
            return False, str(e)
    
    def create_room(self, room_name, password=""):
        """创建房间"""
        # 先启动服务器
        success, ip = self.start_server()
        if not success:
            return False, ip
        
        # 创建房间信息
        self.room_info = {
            "name": room_name,
            "password": password,
            "host_ip": ip,
            "host_port": self.port
        }
        self.is_host = True
        
        return True, f"房间创建成功，IP: {ip}, 端口: {self.port}"
    
    def handle_client_messages(self, client_socket, client_id):
        """处理从客户端接收的消息"""
        while self.running:
            try:
                message = self.receive_message(client_socket)
                if not message:
                    break
                
                # 处理不同类型的消息
                if message.get("type") == "ready_status":
                    # 更新玩家准备状态
                    if self.is_host and client_id in self.connections:
                        self.connections[client_id]["ready"] = message.get("ready", False)
                        # 广播准备状态给所有玩家
                        self.broadcast_message({
                            "type": "player_ready",
                            "peer_id": client_id,
                            "ready": message.get("ready", False)
                        })
                    # 转发给房主处理
                    elif not self.is_host and list(self.connections.keys())[0] == message.get("target"):
                        self.send_message_to(list(self.connections.keys())[0], message)
                
                elif message.get("type") == "start_game" and self.is_host:
                    # 房主发起开始游戏
                    self.broadcast_message({"type": "game_starting"})
                
                elif message.get("target") and message["target"] == self.peer_id:
                    # 消息是发给我的
                    if self.message_handler:
                        self.message_handler(message)
                
                elif self.is_host and message.get("target"):
                    # 作为房主，转发消息给目标玩家
                    self.send_message_to(message["target"], message)
            except Exception as e:
                print(f"处理消息错误: {e}")
                break
        
        # 处理断开连接
        self.handle_disconnect(client_id)
    
    def handle_disconnect(self, client_id):
        """处理客户端断开连接"""
        if client_id in self.connections:
            try:
                self.connections[client_id]["socket"].close()
            except:
                pass
            del self.connections[client_id]
            
            # 通知其他玩家
            if self.is_host:
                self.broadcast_message({
                    "type": "player_left",
                    "peer_id": client_id
                })
            
            # 通知应用层
            if self.message_handler:
                self.message_handler({
                    "type": "player_left",
                    "peer_id": client_id
                })
    
    def send_message(self, sock, message):
        """发送消息到指定socket"""
        try:
            message_json = json.dumps(message)
            # 使用struct打包消息长度
            message_length = struct.pack('!I', len(message_json))
            sock.sendall(message_length + message_json.encode())
            return True
        except Exception as e:
            print(f"发送消息错误: {e}")
            return False
    
    def receive_message(self, sock):
        """从socket接收消息"""
        try:
            # 先接收消息长度
            length_data = sock.recv(4)
            if not length_data:
                return None
            
            message_length = struct.unpack('!I', length_data)[0]
            
            # 接收消息内容
            data = b''
            while len(data) < message_length:
                packet = sock.recv(min(4096, message_length - len(data)))
                if not packet:
                    return None
                data += packet
            
            return json.loads(data.decode())
        except Exception as e:
            print(f"接收消息错误: {e}")
            return None
    
    def send_message_to(self, peer_id, message):
        """发送消息给指定的peer"""
        if peer_id in self.connections:
            return self.send_message(self.connections[peer_id]["socket"], message)
        return False
    
    def broadcast_message(self, message, exclude=None):
        """广播消息给所有连接的客户端"""
        if exclude is None:
            exclude = []
        
        for peer_id, conn_info in list(self.connections.items()):
            if peer_id not in exclude:
                self.send_message(conn_info["socket"], message)
    
    def set_ready_status(self, ready):
        """设置玩家准备状态"""
        self.player_status["ready"] = ready
        
        if self.is_host:
            # 房主直接广播自己的准备状态
            self.broadcast_message({
                "type": "player_ready",
                "peer_id": self.peer_id,
                "ready": ready
            })
        else:
            # 普通玩家发送给房主
            self.send_message_to(list(self.connections.keys())[0], {
                "type": "ready_status",
                "peer_id": self.peer_id,
                "ready": ready
            })
    
    def start_game(self):
        """开始游戏（房主专用）"""
        if self.is_host:
            self.broadcast_message({"type": "game_starting"})
            return True
        return False
    
    def get_local_ip(self):
        """获取本地IP地址"""
        try:
            # 创建临时socket来获取本地IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return '127.0.0.1'
    
    def stop(self):
        """停止网络服务"""
        self.running = False
        
        # 关闭所有连接
        for conn_info in list(self.connections.values()):
            try:
                conn_info["socket"].close()
            except:
                pass
        self.connections.clear()
        
        # 关闭服务器socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        # 等待监听线程结束
        if self.listen_thread:
            self.listen_thread.join(1)

# 测试函数
def test_network():
    nm = NetworkManager("测试玩家")
    print(f"本地IP: {nm.get_local_ip()}")
    nm.stop()

if __name__ == "__main__":
    test_network()
