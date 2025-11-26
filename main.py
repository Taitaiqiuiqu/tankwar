# 坦克大战游戏主入口文件
import pygame
import sys
from constants import *
from ui_manager import UIManager
from network_manager import NetworkManager
from game_state_manager import GameStateManager
from game_engine import GameEngine

class TankWar:
    def __init__(self):
        # 初始化pygame
        pygame.init()
        # 设置游戏窗口
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("坦克大战")
        # 设置时钟
        self.clock = pygame.time.Clock()
        
        # 初始化各模块
        self.ui_manager = UIManager(self.screen)
        self.network_manager = None
        self.game_state_manager = GameStateManager()
        self.game_engine = GameEngine()
        
        # 菜单按钮
        self.menu_buttons = []
        self.__update_main_menu_buttons()
    
    def __update_main_menu_buttons(self):
        """
        更新主菜单按钮
        """
        self.menu_buttons = [
            self.ui_manager.create_button(SCREEN_WIDTH // 2, 200, text="开始游戏", action="start"),
            self.ui_manager.create_button(SCREEN_WIDTH // 2, 280, text="联机游戏", action="online"),
            self.ui_manager.create_button(SCREEN_WIDTH // 2, 360, text="退出", action="exit")
        ]
    
    def __update_room_menu_buttons(self):
        """
        更新房间菜单按钮
        """
        self.menu_buttons = [
            self.ui_manager.create_button(SCREEN_WIDTH // 2, 200, text="创建房间", action="create_room"),
            self.ui_manager.create_button(SCREEN_WIDTH // 2, 280, text="加入房间", action="join_room"),
            self.ui_manager.create_button(SCREEN_WIDTH // 2, 360, text="返回", action="back")
        ]
    
    def __update_in_room_buttons(self):
        """
        更新房间内按钮
        """
        buttons = []
        
        # 准备/取消准备按钮
        ready_text = "取消准备" if self.game_state_manager.is_ready else "准备"
        buttons.append(self.ui_manager.create_button(SCREEN_WIDTH // 2 - 120, 450, 
                                                  width=180, text=ready_text, action="toggle_ready"))
        
        # 房主专属：开始游戏按钮
        if self.game_state_manager.is_host:
            # 检查所有玩家是否都已准备
            all_ready = self.game_state_manager.check_all_players_ready()
            buttons.append(self.ui_manager.create_button(SCREEN_WIDTH // 2 + 120, 450, 
                                                      width=180, text="开始游戏", 
                                                      action="start_game", disabled=not all_ready))
        
        # 退出房间按钮
        buttons.append(self.ui_manager.create_button(SCREEN_WIDTH // 2, 520, 
                                                  text="退出房间", action="leave_room"))
        
        self.menu_buttons = buttons
    
    def __handle_menu_events(self):
        """
        处理菜单事件
        """
        # 获取当前鼠标位置
        mouse_pos = pygame.mouse.get_pos()
        
        # 检查鼠标按钮状态
        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]:  # 左键点击
            for button in self.menu_buttons:
                # 检查按钮是否被禁用
                if button.get("disabled", False):
                    continue
                    
                # 检查按钮是否被点击
                if button["rect"].collidepoint(mouse_pos):
                    action = button["action"]
                    
                    # 根据不同的按钮执行不同的操作
                    if action == "start":
                        # 开始游戏
                        self.__start_game()
                        
                    elif action == "online":
                        # 进入联机游戏界面
                        if not self.game_state_manager.username or self.game_state_manager.username == "玩家":
                            # 如果没有设置用户名，先设置用户名
                            self.game_state_manager.start_input(INPUT_USERNAME, self.__set_username)
                        else:
                            self.game_state_manager.set_game_state(ROOM_BROWSE)
                            self.__update_room_menu_buttons()
                        
                    elif action == "create_room":
                        # 创建房间
                        self.game_state_manager.was_in_room = True
                        self.game_state_manager.start_input(INPUT_ROOM_NAME, self.__on_room_name_input)
                        
                    elif action == "join_room":
                        # 加入房间
                        self.__join_room()
                        
                    elif action == "back":
                        # 返回主菜单
                        self.game_state_manager.set_game_state(MENU)
                        self.__update_main_menu_buttons()
                        
                    elif action == "toggle_ready":
                        # 切换准备状态
                        self.__toggle_ready()
                    
                    elif action == "start_game":
                        # 开始游戏（房主功能）
                        self.__start_game_network()
                        
                    elif action == "leave_room":
                        # 退出房间
                        self.__leave_room()
                    
                    elif action == "exit":
                        # 退出游戏
                        self.__disconnect_network()
                        TankWar.__game_over()
    
    def __set_username(self, username):
        """
        设置用户名
        """
        self.game_state_manager.set_username(username)
        self.game_state_manager.set_game_state(ROOM_BROWSE)
        self.__update_room_menu_buttons()
    
    def __on_room_name_input(self, room_name):
        """
        处理房间名称输入
        """
        if not room_name:
            room_name = "默认房间"
        
        # 设置房间信息
        self.game_state_manager.set_room_info({"name": room_name})
        
        # 进入密码设置选项
        self.game_state_manager.start_input(INPUT_PASSWORD_OPTION, self.__on_password_option_input)
    
    def __on_password_option_input(self, option):
        """
        处理密码选项输入
        """
        if option.lower() in ["y", "yes", "是", "1"]:
            # 需要密码，进入密码输入
            self.game_state_manager.start_input(INPUT_ROOM_PASSWORD, self.__on_room_password_input)
        else:
            # 不需要密码，直接创建房间
            self.__create_room(False, "")
    
    def __on_room_password_input(self, password):
        """
        处理房间密码输入
        """
        self.__create_room(True, password)
    
    def __create_room(self, has_password, password):
        """
        创建房间
        """
        # 更新房间信息
        room_info = self.game_state_manager.room_info
        room_info["has_password"] = has_password
        if has_password:
            room_info["password"] = password
        
        # 设置为房主
        self.game_state_manager.is_host = True
        
        # 初始化网络管理器
        self.network_manager = NetworkManager(self.game_state_manager.username)
        
        # 启动服务器
        if self.network_manager.start_server():
            # 添加本地玩家到玩家列表
            self.game_state_manager.add_player(self.network_manager.username, {
                "username": self.game_state_manager.username,
                "is_host": True,
                "ready": False
            })
            
            # 进入房间
            self.game_state_manager.set_game_state(IN_ROOM)
            self.__update_in_room_buttons()
            print(f"房间 '{room_info['name']}' 已创建，IP: {self.network_manager.local_ip}")
        else:
            print("创建房间失败")
            self.game_state_manager.set_game_state(ROOM_BROWSE)
            self.__update_room_menu_buttons()
    
    def __join_room(self):
        """
        加入房间
        """
        # 如果已有网络连接，先断开
        self.__disconnect_network()
        
        try:
            peer_ip = input("请输入房间IP地址: ")
            self.network_manager = NetworkManager(self.game_state_manager.username)
            
            # 尝试连接
            if self.network_manager.connect(peer_ip):
                # 发送加入请求
                self.network_manager.send_message({
                    "type": "join_request",
                    "username": self.game_state_manager.username
                })
                # 等待房间信息
                print("正在等待房间信息...")
            else:
                print("连接失败，请检查IP地址是否正确")
        except Exception as e:
            print(f"加入房间时出错: {e}")
    
    def __toggle_ready(self):
        """
        切换准备状态
        """
        # 切换准备状态
        is_ready = self.game_state_manager.toggle_ready()
        print(f"{self.game_state_manager.username} 准备状态: {'已准备' if is_ready else '未准备'}")
        
        # 发送准备状态给其他玩家
        if self.network_manager and self.network_manager.connected:
            self.network_manager.send_message({
                "type": "ready_status_changed",
                "username": self.game_state_manager.username,
                "ready": is_ready
            })
        
        # 更新按钮状态
        self.__update_in_room_buttons()
    
    def __leave_room(self):
        """
        离开房间
        """
        print(f"玩家 {self.game_state_manager.username} 离开房间")
        
        # 发送离开房间消息
        if self.network_manager:
            # 如果是房主，需要特殊处理
            if self.game_state_manager.is_host:
                # 发送房主离开消息，通知其他玩家房间已关闭
                self.network_manager.send_message({"type": "host_left", "message": "房主已离开，房间已关闭"})
            else:
                # 普通玩家离开消息
                self.network_manager.send_message({"type": "player_left", "username": self.game_state_manager.username})
            
            # 断开网络连接
            self.__disconnect_network()
        
        # 重置游戏状态
        self.game_state_manager.reset_game_state()
        self.game_state_manager.set_game_state(ROOM_BROWSE)
        self.__update_room_menu_buttons()
    
    def __back_to_main_menu(self):
        """
        返回主菜单
        """
        # 如果在房间内，先离开房间
        if self.game_state_manager.game_state == IN_ROOM:
            self.__leave_room()
        # 断开网络连接
        self.__disconnect_network()
        # 重置游戏状态
        self.game_state_manager.reset_game_state()
        self.game_state_manager.set_game_state(MENU)
        self.__update_main_menu_buttons()
    
    def __reset_game_state(self):
        """
        重置游戏状态
        """
        self.game_state_manager.reset_game_state()
    
    def __start_game(self):
        """
        开始单人游戏
        """
        print("开始单人游戏")
        # 初始化玩家信息
        players = {
            "local_player": {
                "username": self.game_state_manager.username or "玩家",
                "is_host": True,
                "ready": True
            }
        }
        # 初始化游戏引擎
        self.game_engine.init_game(players, "local_player")
        # 切换到游戏运行状态
        self.game_state_manager.set_game_state(GAME_RUNNING)
    
    def __start_game_network(self):
        """
        通过网络开始游戏
        """
        # 检查是否是房主
        if not self.game_state_manager.is_host:
            print("只有房主才能开始游戏")
            return
        
        # 检查所有玩家是否都已准备
        if self.game_state_manager.check_all_players_ready():
            print("所有玩家都已准备，开始游戏")
            # 发送游戏开始消息给所有玩家
            if self.network_manager and self.network_manager.connected:
                self.network_manager.send_message({"type": "game_starting"})
            # 初始化游戏引擎
            self.game_engine.init_game(self.game_state_manager.players, self.network_manager.username)
            # 切换到游戏运行状态
            self.game_state_manager.set_game_state(GAME_RUNNING)
        else:
            print("等待所有玩家准备")
    
    def __handle_network_messages(self):
        """
        处理网络消息
        """
        if not self.network_manager or not self.network_manager.connected:
            return
        
        messages = self.network_manager.get_messages()
        for message in messages:
            message_type = message.get("type")
            
            if message_type == "join_request":
                # 处理加入请求（房主端）
                if self.game_state_manager.is_host:
                    username = message.get("username", "未知玩家")
                    peer_id = username  # 使用用户名作为peer_id
                    
                    # 检查房间是否已满
                    if len(self.game_state_manager.players) >= 4:
                        self.network_manager.send_message({
                            "type": "join_rejected",
                            "reason": "房间已满"
                        })
                        continue
                    
                    # 检查房间是否需要密码
                    if self.game_state_manager.room_info and self.game_state_manager.room_info.get("has_password", False):
                        # 需要密码，要求输入密码
                        self.network_manager.send_message({
                            "type": "password_required"
                        })
                    else:
                        # 不需要密码，直接允许加入
                        self.game_state_manager.add_player(peer_id, {
                            "username": username,
                            "is_host": False,
                            "ready": False
                        })
                        
                        # 通知新玩家已加入
                        self.network_manager.send_message({
                            "type": "join_accepted",
                            "room_info": self.game_state_manager.room_info,
                            "players": self.game_state_manager.players
                        })
                        
                        # 通知其他玩家有新玩家加入
                        for existing_peer_id in self.game_state_manager.players:
                            if existing_peer_id != peer_id:
                                # 这里简化处理，实际上应该单独发送给每个玩家
                                pass
                        
                        print(f"玩家 '{username}' 加入了房间")
                        
                        # 更新房间内按钮状态
                        self.__update_in_room_buttons()
            
            elif message_type == "password_required":
                # 客户端收到需要密码的消息
                print("该房间需要密码")
                # 这里应该显示密码输入界面
            
            elif message_type == "password_attempt":
                # 房主收到密码尝试
                if self.game_state_manager.is_host:
                    password = message.get("password", "")
                    expected_password = self.game_state_manager.room_info.get("password", "")
                    
                    if password == expected_password:
                        # 密码正确，允许加入
                        username = message.get("username", "未知玩家")
                        peer_id = username
                        
                        self.game_state_manager.add_player(peer_id, {
                            "username": username,
                            "is_host": False,
                            "ready": False
                        })
                        
                        self.network_manager.send_message({
                            "type": "join_accepted",
                            "room_info": self.game_state_manager.room_info,
                            "players": self.game_state_manager.players
                        })
                        
                        print(f"玩家 '{username}' 通过密码验证加入了房间")
                        self.__update_in_room_buttons()
                    else:
                        # 密码错误
                        self.network_manager.send_message({
                            "type": "password_incorrect"
                        })
            
            elif message_type == "join_accepted":
                # 客户端收到加入成功的消息
                room_info = message.get("room_info")
                players = message.get("players", {})
                
                self.game_state_manager.set_room_info(room_info)
                self.game_state_manager.players = players
                self.game_state_manager.set_game_state(IN_ROOM)
                self.__update_in_room_buttons()
                
                print(f"成功加入房间: {room_info.get('name', '未知房间')}")
            
            elif message_type == "join_rejected":
                # 客户端收到加入被拒绝的消息
                reason = message.get("reason", "未知原因")
                print(f"加入房间被拒绝: {reason}")
            
            elif message_type == "password_incorrect":
                # 客户端收到密码错误的消息
                print("密码错误，请重新输入")
            
            elif message_type == "player_left":
                # 玩家离开房间
                username = message.get("username", "未知玩家")
                
                # 从玩家列表中移除
                for peer_id, player in list(self.game_state_manager.players.items()):
                    if player.get("username") == username:
                        self.game_state_manager.remove_player(peer_id)
                        break
                
                print(f"玩家 '{username}' 离开了房间")
                
                # 更新房间内按钮状态
                if self.game_state_manager.game_state == IN_ROOM:
                    self.__update_in_room_buttons()
            
            elif message_type == "host_left":
                # 房主离开，房间关闭
                message_text = message.get("message", "房主已离开，房间已关闭")
                print(message_text)
                
                # 断开连接
                self.__disconnect_network()
                
                # 返回房间浏览界面
                self.game_state_manager.reset_game_state()
                self.game_state_manager.set_game_state(ROOM_BROWSE)
                self.__update_room_menu_buttons()
            
            elif message_type == "ready_status_changed":
                # 玩家准备状态改变
                username = message.get("username")
                ready = message.get("ready", False)
                
                # 更新玩家准备状态
                if self.game_state_manager.update_player_ready_status(username, ready):
                    print(f"玩家 '{username}' 准备状态: {'已准备' if ready else '未准备'}")
                    
                    # 更新房间内按钮状态
                    if self.game_state_manager.game_state == IN_ROOM:
                        self.__update_in_room_buttons()
            
            elif message_type == "start_game":
                # 收到开始游戏消息（房主发送的）
                print("收到开始游戏指令")
                # 初始化游戏
                self.game_engine.init_game(self.game_state_manager.players, self.network_manager.username)
                # 切换到游戏运行状态
                self.game_state_manager.set_game_state(GAME_RUNNING)
            
            elif message_type == "game_starting":
                # 收到游戏开始消息
                print("游戏开始！")
                # 初始化游戏
                self.game_engine.init_game(self.game_state_manager.players, self.network_manager.username)
                # 切换到游戏运行状态
                self.game_state_manager.set_game_state(GAME_RUNNING)
            
            elif message_type == "game_state":
                # 收到游戏状态同步消息
                game_state = message.get("game_state", {})
                self.game_engine.set_game_state(game_state)
    
    def __disconnect_network(self):
        """
        断开网络连接
        """
        if self.network_manager:
            self.network_manager.disconnect()
            self.network_manager = None
    
    def __handle_input_events(self, event):
        """
        处理输入框事件
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                # 完成输入
                self.game_state_manager.finish_input()
            elif event.key == pygame.K_BACKSPACE:
                # 删除字符
                self.game_state_manager.input_text = self.game_state_manager.input_text[:-1]
            else:
                # 添加字符
                self.game_state_manager.input_text += event.unicode
    
    def __event_handler(self):
        """
        处理游戏事件
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # 退出游戏
                self.__disconnect_network()
                TankWar.__game_over()
            
            # 处理输入状态下的事件
            if self.game_state_manager.game_state == INPUT:
                self.__handle_input_events(event)
            
            # 处理游戏运行状态下的按键事件
            elif self.game_state_manager.game_state == GAME_RUNNING:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        # 射击
                        if self.network_manager and self.network_manager.connected:
                            # 发送射击消息
                            self.network_manager.send_message({
                                "type": "shoot",
                                "player_id": self.network_manager.username
                            })
                        else:
                            # 本地射击
                            self.game_engine.handle_shoot(self.network_manager.username if self.network_manager else "local_player")
                    elif event.key == pygame.K_ESCAPE:
                        # 退出游戏回到主菜单
                        self.game_state_manager.set_game_state(MENU)
                        self.__update_main_menu_buttons()
    
    def run_game(self):
        """
        游戏主循环
        """
        while True:
            # 处理事件
            self.__event_handler()
            
            # 获取当前鼠标位置（用于按钮悬停效果）
            mouse_pos = pygame.mouse.get_pos()
            
            # 根据游戏状态执行不同的逻辑
            if self.game_state_manager.game_state == MENU:
                # 主菜单
                self.ui_manager.draw_menu("坦克大战", self.menu_buttons, mouse_pos)
                self.__handle_menu_events()
            
            elif self.game_state_manager.game_state == ROOM_BROWSE:
                # 房间浏览界面
                self.ui_manager.draw_room_browse("联机游戏", self.menu_buttons, mouse_pos)
                self.__handle_menu_events()
            
            elif self.game_state_manager.game_state == INPUT:
                # 输入状态
                prompt = ""
                if self.game_state_manager.input_active == INPUT_USERNAME:
                    prompt = "请输入您的用户名"
                elif self.game_state_manager.input_active == INPUT_ROOM_NAME:
                    prompt = "请输入房间名称"
                elif self.game_state_manager.input_active == INPUT_PASSWORD_OPTION:
                    prompt = "是否需要密码保护房间？(y/n)"
                elif self.game_state_manager.input_active == INPUT_ROOM_PASSWORD:
                    prompt = "请设置房间密码"
                
                self.ui_manager.draw_input_box(prompt, self.game_state_manager.input_text, True)
            
            elif self.game_state_manager.game_state == IN_ROOM:
                # 房间内
                self.ui_manager.draw_room(
                    self.game_state_manager.room_info,
                    self.game_state_manager.players,
                    self.game_state_manager.is_host,
                    self.game_state_manager.is_ready,
                    self.menu_buttons,
                    mouse_pos,
                    self.game_state_manager.username
                )
                self.__handle_menu_events()
                
                # 处理网络消息
                self.__handle_network_messages()
            
            elif self.game_state_manager.game_state == GAME_RUNNING:
                # 游戏运行中
                # 获取按键状态
                keys = pygame.key.get_pressed()

                # 处理本地玩家按键移动（每帧调用 move）
                try:
                    local_id = self.game_engine.local_player_id
                except AttributeError:
                    local_id = None

                local_tank = None
                if local_id is not None:
                    for t in self.game_engine.tanks:
                        if t.player_id == local_id:
                            local_tank = t
                            break

                if local_tank:
                    moved = False
                    if keys[pygame.K_LEFT]:
                        local_tank.move("left")
                        moved = True
                    elif keys[pygame.K_RIGHT]:
                        local_tank.move("right")
                        moved = True
                    elif keys[pygame.K_UP]:
                        local_tank.move("up")
                        moved = True
                    elif keys[pygame.K_DOWN]:
                        local_tank.move("down")
                        moved = True

                    # 如果移动且联机，则发送位置同步（避免过多发送，可按帧发送）
                    if moved and self.network_manager and getattr(self.network_manager, 'connected', False):
                        self.network_manager.send_message({
                            "type": "player_position",
                            "sender_id": self.network_manager.username,
                            "x": local_tank.rect.x,
                            "y": local_tank.rect.y,
                            "direction": local_tank.direction
                        })

                # 更新游戏状态
                self.game_engine.update()
                
                # 绘制游戏画面
                self.game_engine.draw(self.screen)
                
                # 处理网络消息
                self.__handle_network_messages()
            
            elif self.game_state_manager.game_state == GAME_OVER:
                # 游戏结束
                # 这里可以添加游戏结束画面的绘制
                pass
            
            # 更新显示
            pygame.display.flip()
            
            # 控制帧率
            self.clock.tick(60)
    
    @staticmethod
    def __game_over():  # 保持静态方法以便在类外部调用
        """
        游戏结束，清理资源
        """
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = TankWar()
    game.run_game()
