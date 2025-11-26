import os

# 禁用libpng警告
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
os.environ['SDL_AUDIODRIVER'] = 'directsound'

import pygame
from sprites import *
import game_engine
import game_state_manager
import ui_manager
import time
import random
from network_manager import NetworkManager


class TankWar:
    # 游戏状态常量
    MENU = 0
    GAME_RUNNING = 1
    GAME_OVER = 2
    
    # 房间相关状态
    ROOM_BROWSE = 3  # 浏览房间
    CREATE_ROOM = 4  # 创建房间
    JOIN_ROOM = 5    # 加入房间
    IN_ROOM = 6      # 在房间内
    
    # 输入框状态
    INPUT_USERNAME = 7
    INPUT_ROOM_NAME = 8
    INPUT_ROOM_PASSWORD = 9
    INPUT_JOIN_IP = 10
    INPUT_JOIN_PORT = 11
    INPUT_JOIN_PASSWORD = 12

    def __init__(self):
        # 先初始化pygame
        self.__init_game()
        
        self.screen = pygame.display.set_mode(Settings.SCREEN_RECT.size)
        self.clock = pygame.time.Clock()
        self.game_still = True
        self.hero = None
        self.enemies = None
        self.enemy_bullets = None
        self.walls = None
        self.menu_buttons = []
        
        # 初始化游戏状态管理器
        from game_state_manager import GameStateManager
        self.state_manager = GameStateManager()
        self.game_state = self.state_manager.game_state
        
        # 初始化UI管理器
        self.ui_manager = ui_manager.UIManager(self.screen)
        
        # 网络相关初始化
        self.network_manager = None
        
        # 输入框相关（保留UI相关的变量）
        self.input_placeholder = ""  # 输入框占位符
        
        self.__init_menu()

    def __init_menu(self):
        """
        初始化菜单按钮和相关资源
        """
        # 初始化主菜单按钮
        self.__update_main_menu_buttons()
        
        # 输入框矩形
        self.input_box = pygame.Rect(Settings.SCREEN_RECT.centerx - 200, Settings.SCREEN_RECT.centery, 400, 50)
        
    def __update_main_menu_buttons(self):
        """
        更新主菜单按钮
        """
        # 清空菜单按钮
        self.menu_buttons = []
        
        # 创建开始游戏按钮
        start_btn = self.ui_manager.create_button(Settings.SCREEN_RECT.centerx, Settings.SCREEN_RECT.centery - 100, text="开始游戏", action="start")
        start_btn["text"] = self.font.render("开始游戏", True, (255, 255, 255)) if hasattr(self, 'font') else "开始游戏"
        self.menu_buttons.append(start_btn)
        
        # 创建联机游戏按钮
        online_btn = self.ui_manager.create_button(Settings.SCREEN_RECT.centerx, Settings.SCREEN_RECT.centery, text="联机游戏", action="online")
        online_btn["text"] = self.font.render("联机游戏", True, (255, 255, 255)) if hasattr(self, 'font') else "联机游戏"
        self.menu_buttons.append(online_btn)
        
        # 创建退出按钮
        exit_btn = self.ui_manager.create_button(Settings.SCREEN_RECT.centerx, Settings.SCREEN_RECT.centery + 100, text="退出", action="exit")
        exit_btn["text"] = self.font.render("退出", True, (255, 255, 255)) if hasattr(self, 'font') else "退出"
        self.menu_buttons.append(exit_btn)
        
    def __update_room_menu_buttons(self):
        """
        更新房间菜单按钮
        """
        self.menu_buttons = []
        
        # 创建房间按钮
        create_btn = self.ui_manager.create_button(Settings.SCREEN_RECT.centerx, Settings.SCREEN_RECT.centery - 50, text="创建房间", action="create_room")
        create_btn["text"] = self.small_font.render("创建房间", True, (255, 255, 255)) if hasattr(self, 'small_font') else "创建房间"
        self.menu_buttons.append(create_btn)
        
        # 加入房间按钮
        join_btn = self.ui_manager.create_button(Settings.SCREEN_RECT.centerx, Settings.SCREEN_RECT.centery + 50, text="加入房间", action="join_room")
        join_btn["text"] = self.small_font.render("加入房间", True, (255, 255, 255)) if hasattr(self, 'small_font') else "加入房间"
        self.menu_buttons.append(join_btn)
        
        # 返回按钮
        back_btn = self.ui_manager.create_button(Settings.SCREEN_RECT.centerx, Settings.SCREEN_RECT.centery + 150, text="返回", action="back")
        back_btn["text"] = self.small_font.render("返回", True, (255, 255, 255)) if hasattr(self, 'small_font') else "返回"
        self.menu_buttons.append(back_btn)
        
    def __update_in_room_buttons(self):
        """
        更新房间内按钮
        """
        self.menu_buttons = []
        
        # 从状态管理器获取准备状态和房主状态
        is_ready = self.state_manager.is_ready
        is_host = self.state_manager.is_host
        
        # 准备/取消准备按钮
        ready_text = "取消准备" if is_ready else "准备"
        ready_btn = self.ui_manager.create_button(Settings.SCREEN_RECT.centerx - 150, Settings.SCREEN_RECT.centery + 200, text=ready_text, action="toggle_ready")
        ready_btn["text"] = self.small_font.render(ready_text, True, (255, 255, 255)) if hasattr(self, 'small_font') else ready_text
        self.menu_buttons.append(ready_btn)
        
        # 如果是房主，显示开始游戏按钮
        if is_host:
            # 检查所有玩家是否都已准备
            all_ready = True
            for peer_id, player in self.state_manager.players.items():
                if not player.get("ready", False):
                    all_ready = False
                    break
            
            start_text = "开始游戏"
            start_btn = self.ui_manager.create_button(Settings.SCREEN_RECT.centerx + 150, Settings.SCREEN_RECT.centery + 200, text=start_text, action="start_game")
            start_btn["text"] = self.small_font.render(start_text, True, (255, 255, 255)) if hasattr(self, 'small_font') else start_text
            start_btn["disabled"] = not all_ready
            self.menu_buttons.append(start_btn)
        
        # 退出房间按钮
        leave_btn = self.ui_manager.create_button(Settings.SCREEN_RECT.centerx, Settings.SCREEN_RECT.centery + 280, text="退出房间", action="leave_room")
        leave_btn["text"] = self.small_font.render("退出房间", True, (255, 255, 255)) if hasattr(self, 'small_font') else "退出房间"
        self.menu_buttons.append(leave_btn)
        
    def __draw_input_box(self):
        """
        绘制输入框
        """
        # 使用UI管理器绘制输入框
        self.ui_manager.draw_input_box(self.input_placeholder, self.input_text, self.input_active)
        
    def __draw_room(self):
        """
        绘制房间内界面，包括玩家列表和准备状态
        """
        # 获取房间信息
        room_info = self.state_manager.room_info
        
        # 转换按钮格式为UI管理器所需的格式
        ui_buttons = []
        for btn in self.menu_buttons:
            # 获取按钮文本
            btn_text = ""
            if hasattr(btn["text"], "_text"):
                btn_text = btn["text"]._text
            else:
                btn_text = str(btn["text"])
            
            ui_btn = {
                "rect": btn["rect"],
                "text": btn_text,
                "action": btn["action"],
                "disabled": btn.get("disabled", False),
                "color": (0, 150, 0)  # 默认按钮颜色
            }
            ui_buttons.append(ui_btn)
        
        # 获取当前玩家信息
        mouse_pos = pygame.mouse.get_pos()
        is_host = self.state_manager.is_host
        is_ready = self.state_manager.is_ready
        username = self.state_manager.username
        
        # 使用UI管理器绘制房间界面
        self.ui_manager.draw_room(room_info, self.state_manager.players, is_host, is_ready, ui_buttons, mouse_pos, username)
    
    def __handle_network_message(self, message):
        """
        处理网络消息
        """        
        msg_type = message.get("type")
        
        if msg_type == "room_info":
            # 使用状态管理器设置房间信息
            self.state_manager.set_room_info(message)
            # 设置房主状态
            self.state_manager.is_host = self.network_manager.is_host
            self.game_state = self.IN_ROOM
            self.__update_in_room_buttons()
            
        elif msg_type == "player_joined":
            # 玩家加入，由状态管理器处理
            peer_id = message.get("peer_id")
            username = message.get("username")
            self.state_manager.add_player(peer_id, {"username": username, "ready": False})
            self.__update_in_room_buttons()
            # 如果游戏已经开始，创建新玩家的坦克
            if hasattr(self, 'game_state') and self.game_state == self.GAME_RUNNING:
                if hasattr(self, 'player_tanks') and peer_id not in self.player_tanks:
                    from sprites import PlayerTank
                    import random
                    other_tank = PlayerTank(Settings.PLAYER_IMAGES[0], self.screen)
                    other_tank.player_id = peer_id
                    other_tank.username = username
                    other_tank.rect.x = random.randint(100, Settings.SCREEN_WIDTH - 100)
                    other_tank.rect.y = random.randint(100, Settings.SCREEN_HEIGHT - 100)
                    self.player_tanks[peer_id] = other_tank
            
        elif msg_type == "player_left":
            # 玩家离开，由状态管理器处理
            peer_id = message.get("peer_id")
            self.state_manager.remove_player(peer_id)
            # 从玩家坦克字典中移除
            if hasattr(self, 'player_tanks') and peer_id in self.player_tanks:
                del self.player_tanks[peer_id]
            self.__update_in_room_buttons()
            
        elif msg_type == "ready_status_changed":
            # 准备状态变更，由状态管理器处理
            username = message.get("username", "")
            ready = message.get("ready", False)
            
            # 查找对应用户的peer_id
            for peer_id, player_info in self.state_manager.players.items():
                if player_info.get("username") == username:
                    self.state_manager.update_player_status(peer_id, {"ready": ready})
                    print(f"玩家 {username} 的准备状态已更新为: {ready}")
                    break
            
            self.__update_in_room_buttons()
            
        elif msg_type == "game_starting":
            # 游戏开始
            self.game_state = self.GAME_RUNNING
            self.__create_sprite()
            
        elif msg_type == "error":
            # 错误消息
            error_msg = message.get("message", "未知错误")
            print(f"网络错误: {error_msg}")
            # 可以在这里添加错误提示UI
            
        elif msg_type == "password_required":
            # 房间需要密码
            print("该房间需要密码")
            self.__start_input(self.INPUT_ROOM_PASSWORD, "请输入房间密码", self.__join_room_with_password)
            
        elif msg_type == "password_correct":
            # 密码正确
            print("密码正确，正在加入房间...")
            # 设置玩家状态
            self.state_manager.is_host = False
            self.state_manager.is_ready = False
            
            # 使用状态管理器初始化房间信息
            self.state_manager.set_room_info(message)
            
            # 切换到房间内状态
            self.game_state = self.IN_ROOM
            self.__update_in_room_buttons()
            
        elif msg_type == "password_incorrect":
            # 密码错误
            print("密码错误，请重新输入")
            self.__start_input(self.INPUT_ROOM_PASSWORD, "密码错误，请重新输入", self.__join_room_with_password)
            
        elif msg_type == "check_password":
            # 作为房主，检查加入者的密码
            if self.state_manager.is_host:
                username = message.get("username", "")
                password = message.get("password", "")
                
                # 验证密码
                if self.state_manager.room_info and self.state_manager.room_info.get("has_password", False):
                    if password == self.state_manager.room_info.get("password", ""):
                        # 密码正确，允许加入
                        if self.network_manager:
                            self.network_manager.send_message({
                                "type": "password_correct",
                                "username": username,
                                "players": self.state_manager.players
                            })
                    else:
                        # 密码错误，拒绝加入
                        if self.network_manager:
                            self.network_manager.send_message({
                                "type": "password_incorrect",
                                "username": username
                            })
                else:
                    # 房间没有密码，直接允许加入
                    if self.network_manager:
                        self.network_manager.send_message({
                            "type": "password_correct",
                            "username": username,
                            "players": self.state_manager.players
                        })
        
        # 多人游戏同步相关消息
        elif msg_type == "player_move":
            # 玩家移动
            if hasattr(self, 'player_tanks'):
                peer_id = message.get("sender_id", message.get("peer_id"))
                if peer_id in self.player_tanks and peer_id != "local":
                    tank = self.player_tanks[peer_id]
                    tank.direction = message.get("direction", tank.direction)
                    tank.is_moving = message.get("is_moving", False)
                    # 平滑更新位置
                    if "x" in message and "y" in message:
                        target_x = message["x"]
                        target_y = message["y"]
                        # 使用插值平滑移动
                        tank.rect.x = int(tank.rect.x * 0.7 + target_x * 0.3)
                        tank.rect.y = int(tank.rect.y * 0.7 + target_y * 0.3)
                        
        elif msg_type == "player_shot":
            # 玩家射击
            if hasattr(self, 'player_tanks'):
                peer_id = message.get("sender_id", message.get("peer_id"))
                if peer_id in self.player_tanks and peer_id != "local":
                    tank = self.player_tanks[peer_id]
                    # 在指定位置创建子弹
                    direction = message.get("direction", tank.direction)
                    x = message.get("x", tank.rect.centerx)
                    y = message.get("y", tank.rect.centery)
                    # 直接创建子弹而不调用shot方法，避免再次发送网络消息
                    from sprites import Bullet
                    bullet = Bullet(Settings.BULLET_IMAGE_NAME, self.screen)
                    bullet.rect.centerx = x
                    bullet.rect.centery = y
                    bullet.direction = direction
                    bullet.speed = Settings.BULLET_SPEED
                    tank.bullets.add(bullet)
                    
        elif msg_type == "player_position":
            # 玩家位置更新
            if hasattr(self, 'player_tanks'):
                peer_id = message.get("sender_id", message.get("peer_id"))
                if peer_id in self.player_tanks and peer_id != "local":
                    tank = self.player_tanks[peer_id]
                    if "x" in message and "y" in message:
                        tank.rect.x = message["x"]
                        tank.rect.y = message["y"]
                    if "direction" in message:
                        tank.direction = message["direction"]
                        
        elif msg_type == "player_killed":
            # 玩家被击杀
            if hasattr(self, 'player_tanks'):
                peer_id = message.get("player_id", message.get("sender_id"))
                if peer_id in self.player_tanks and peer_id != "local":
                    tank = self.player_tanks[peer_id]
                    tank.kill()
                    print(f"玩家 {tank.username} 被击杀")
        
    def __start_input(self, input_type, placeholder, callback):
        """
        开始输入
        """
        self.input_placeholder = placeholder
        self.state_manager.start_input(input_type, callback)
        self.game_state = self.state_manager.game_state
        self.input_active = self.state_manager.input_active
        self.input_text = self.state_manager.input_text
        
    def __finish_input(self):
        """
        结束输入
        """
        self.state_manager.finish_input()
        self.game_state = self.state_manager.game_state
        self.input_active = self.state_manager.input_active
        self.input_text = self.state_manager.input_text
        
    def __set_username(self, username):
        """
        设置用户名
        """
        self.state_manager.set_username(username)
        print(f"用户名设置为: {self.state_manager.username}")
            
    def __on_room_name_input(self, room_name):
        """
        处理房间名称输入，询问是否需要设置密码
        """
        if room_name.strip():
            self.room_info = {
                "name": room_name.strip(),
                "has_password": False,
                "password": ""
            }
            
            # 询问是否需要设置密码
            self.__start_input(self.INPUT_PASSWORD_OPTION, "是否设置房间密码？(y/n)", self.__on_password_option_input)
        else:
            # 如果房间名为空，重新输入
            self.__start_input(self.INPUT_ROOM_NAME, "房间名称不能为空，请重新输入", self.__on_room_name_input)
    
    def __on_password_option_input(self, option):
        """
        处理是否设置密码的选择
        """
        option = option.lower().strip()
        
        if option == 'y':
            # 需要设置密码
            self.__start_input(self.INPUT_ROOM_PASSWORD, "请输入房间密码", self.__on_room_password_input)
        elif option == 'n':
            # 不需要设置密码，直接创建房间
            self.__create_room()
        else:
            # 输入错误，重新询问
            self.__start_input(self.INPUT_PASSWORD_OPTION, "输入无效，请输入y或n", self.__on_password_option_input)
    
    def __on_room_password_input(self, password):
        """
        处理房间密码输入
        """
        if password.strip():
            # 设置密码
            self.room_info["has_password"] = True
            self.room_info["password"] = password.strip()
            
            # 创建房间
            self.__create_room()
        else:
            # 如果密码为空，重新输入或询问是否跳过
            self.__start_input(self.INPUT_PASSWORD_OPTION, "密码不能为空，是否仍要创建无密码房间？(y/n)", 
                             lambda option: self.__handle_empty_password(option))
    
    def __handle_empty_password(self, option):
        """
        处理空密码的情况
        """
        option = option.lower().strip()
        
        if option == 'y':
            # 仍要创建无密码房间
            self.room_info["has_password"] = False
            self.room_info["password"] = ""
            self.__create_room()
        elif option == 'n':
            # 返回重新输入密码
            self.__start_input(self.INPUT_ROOM_PASSWORD, "请输入房间密码", self.__on_room_password_input)
        else:
            # 输入错误，重新询问
            self.__start_input(self.INPUT_PASSWORD_OPTION, "输入无效，请输入y或n", self.__handle_empty_password)
            
    def __create_room(self):
        """
        创建房间
        """
        # 导入网络管理器
        from network_manager import NetworkManager
        
        # 初始化网络管理器作为主机
        self.network_manager = NetworkManager(username=self.username)
        self.network_manager.start_server()
        
        # 设置为房主
        self.is_host = True
        self.is_ready = False
        
        # 初始化玩家列表由状态管理器处理
        
        # 切换到房间内状态
        self.game_state = self.IN_ROOM
        self.__update_in_room_buttons()
        
        print(f"房间 '{self.room_info['name']}' 创建成功！")
        if self.room_info["has_password"]:
            print("房间已设置密码保护")
            
    def __join_room_with_password(self, password):
        """
        使用密码加入房间
        """
        print(f"尝试使用密码加入房间: {'******' if password else '无密码'}")
        
        # 保存密码以便后续验证
        self.join_room_password = password
        
        # 发送加入房间的请求，包含密码
        if hasattr(self, 'network_manager') and self.network_manager:
            self.network_manager.send_message({
                "type": "join_room",
                "room_id": self.room_to_join if hasattr(self, 'room_to_join') else "",
                "username": self.username if hasattr(self, 'username') else "玩家",
                "password": password
            })
    
    def __draw_menu(self):
        """
        绘制开始菜单
        """
        # 转换按钮格式为UI管理器所需的格式
        ui_buttons = []
        for btn in self.menu_buttons:
            # 获取按钮文本
            btn_text = ""
            if hasattr(btn["text"], "_text"):
                btn_text = btn["text"]._text
            else:
                # 尝试从按钮文本对象中提取文本
                btn_text = str(btn["text"])
            
            ui_btn = {
                "rect": btn["rect"],
                "text": btn_text,
                "action": btn["action"],
                "disabled": btn.get("disabled", False),
                "color": (0, 150, 0)  # 默认按钮颜色
            }
            ui_buttons.append(ui_btn)
        
        # 使用UI管理器绘制菜单
        mouse_pos = pygame.mouse.get_pos()
        self.ui_manager.draw_menu("坦克大战", ui_buttons, mouse_pos)
    
    def __handle_menu_events(self):
        """
        处理菜单事件
        """
        # 这里不直接处理pygame.event.get()，因为__event_handler会处理
        # 只处理鼠标点击菜单按钮的逻辑
        # 首先检查是否有鼠标点击事件
        mouse_clicked = False
        mouse_pos = None
        
        # 获取当前鼠标位置
        mouse_pos = pygame.mouse.get_pos()
        
        # 检查鼠标按钮状态
        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]:  # 左键点击
            mouse_clicked = True
        
        # 如果有鼠标点击，处理按钮点击
        if mouse_clicked:
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
                        if not hasattr(self, 'username') or not self.username or self.username == "玩家":
                            # 如果没有设置用户名，先设置用户名
                            self.__start_input(self.INPUT_USERNAME, "请输入您的用户名", self.__set_username)
                        else:
                            self.game_state = self.ROOM_BROWSE
                            self.__update_room_menu_buttons()
                        
                    elif action == "create_room":
                        # 创建房间
                        self.was_in_room = True
                        self.__start_input(self.INPUT_ROOM_NAME, "请输入房间名称", self.__on_room_name_input)
                        
                    elif action == "join_room":
                        # 加入房间 - 这里简化处理，实际上应该显示房间列表
                        if hasattr(self, 'network_manager') and self.network_manager:
                            if hasattr(self.network_manager, 'disconnect'):
                                self.network_manager.disconnect()
                        
                        # 尝试连接到其他玩家创建的房间
                        # 简化实现：假设有一个已知的IP地址（实际应该扫描局域网）
                        try:
                            peer_ip = input("请输入房间IP地址: ")
                            self.network_manager = NetworkManager(username=self.username)
                            self.network_manager.connect(peer_ip)
                            # 发送加入请求
                            self.network_manager.send_message({
                                "type": "join_request",
                                "username": self.username
                            })
                        except Exception as e:
                            print(f"连接失败: {e}")
                        
                    elif action == "back":
                        # 返回主菜单
                        self.game_state = self.MENU
                        self.__update_main_menu_buttons()
                        
                    elif action == "toggle_ready":
                        # 调用切换准备状态方法
                        self.__toggle_ready()
                    
                    elif action == "start_game":
                        # 开始游戏（房主功能）
                        if hasattr(self, 'is_host') and self.is_host and hasattr(self, 'network_manager') and self.network_manager and hasattr(self.network_manager, 'connected') and self.network_manager.connected:
                            self.network_manager.send_message({
                                "type": "start_game"
                            })
                        
                    elif action == "leave_room":
                        # 退出房间
                        self.__leave_room()
                    
                    elif action == "exit":
                        # 退出游戏
                        if hasattr(self, 'network_manager') and self.network_manager and hasattr(self.network_manager, 'disconnect'):
                            self.network_manager.disconnect()
                        TankWar.__game_over()
    
    def __toggle_ready(self):
        """
        切换准备状态
        """
        # 使用状态管理器切换准备状态
        self.state_manager.toggle_ready()
        print(f"{self.state_manager.username} 准备状态: {'已准备' if self.state_manager.is_ready else '未准备'}")
        
        # 发送准备状态给其他玩家
        if hasattr(self, 'network_manager') and self.network_manager:
            self.network_manager.send_message({
                "type": "ready_status_changed",
                "username": self.state_manager.username,
                "ready": self.state_manager.is_ready
            })
        
        # 更新按钮状态
        self.__update_in_room_buttons()
                        
    def __leave_room(self):
        """
        离开房间
        """
        print(f"玩家 {self.username if hasattr(self, 'username') else '未知'} 离开房间")
        
        # 发送离开房间消息
        if hasattr(self, 'network_manager') and self.network_manager:
            # 断开网络连接，消息处理由network_manager内部处理
            self.network_manager.disconnect()
        
        # 重置游戏状态
        self.__reset_game_state()
        self.game_state = self.ROOM_MENU
        self.__update_room_menu_buttons()
        
    def __back_to_main_menu(self):
        """
        返回主菜单
        """
        # 如果在房间内，先离开房间
        if self.game_state == self.IN_ROOM:
            self.__leave_room()
        # 断开网络连接
        if hasattr(self, 'network_manager') and self.network_manager:
            self.network_manager.disconnect()
        # 重置游戏状态
        self.__reset_game_state()
        self.game_state = self.MENU
        self.__update_main_menu_buttons()
        
    def __reset_game_state(self):
        """
        重置游戏状态
        """
        # 安全地重置玩家相关属性
        for attr in ['is_host', 'is_ready', 'players', 'room_info', 'room_to_join', 'join_room_password', 'join_attempt_password']:
            if hasattr(self, attr):
                delattr(self, attr)
        # 重置输入状态
        self.input_active = None
        self.input_text = ""
    
    def __start_game(self):
        """
        开始游戏（房主权限）
        """
        # 检查是否是房主
        if not hasattr(self, 'is_host') or not self.is_host:
            print("只有房主才能开始游戏")
            return
        
        # 检查所有玩家是否都已准备
        all_ready = True
        if hasattr(self, 'players'):
            for peer_id, player in self.state_manager.players.items():
                if not player.get("ready", False):
                    all_ready = False
                    break
        
        if all_ready:
            print("所有玩家都已准备，开始游戏")
            # 切换到游戏运行状态
            self.game_state = self.GAME_RUNNING
            # 初始化游戏精灵
            self.__create_sprite()
        else:
            print("等待所有玩家准备")
            # 可以在这里添加提示UI，通知用户等待所有玩家准备
    
    @staticmethod
    def __init_game():
        """
        初始化游戏的一些设置
        :return:
        """
        pygame.init()   # 初始化pygame模块
        pygame.display.set_caption(Settings.GAME_NAME)  # 设置窗口标题
        pygame.mixer.init()    # 初始化音频模块

    def __create_sprite(self):
        # 初始化游戏引擎
        self.game_engine = game_engine.GameEngine(self.screen)
        
        # 初始化玩家坦克字典（存储所有玩家）
        self.player_tanks = {}
        
        # 初始化自己的坦克
        self.hero = Hero(Settings.HERO_IMAGE_NAME, self.screen)
        self.hero.player_id = "local"  # 标识为本地玩家
        self.hero.username = getattr(self, 'username', "玩家")
        self.player_tanks["local"] = self.hero
        
        # 添加本地玩家到游戏引擎
        self.game_engine.add_player_tank(self.hero)
        
        # 初始化其他玩家坦克（将在网络消息中更新）
        if hasattr(self, 'players'):
            for peer_id, player_info in self.state_manager.players.items():
                if peer_id != "local":  # 避免重复添加本地玩家
                    # 创建其他玩家的坦克
                    other_tank = PlayerTank(Settings.PLAYER_IMAGES[0], self.screen)
                    other_tank.player_id = peer_id
                    other_tank.username = player_info.get("username", f"玩家{peer_id[:4]}")
                    # 设置随机位置
                    other_tank.rect.x = random.randint(100, Settings.SCREEN_WIDTH - 100)
                    other_tank.rect.y = random.randint(100, Settings.SCREEN_HEIGHT - 100)
                    self.player_tanks[peer_id] = other_tank
                    # 添加到游戏引擎
                    self.game_engine.add_player_tank(other_tank)
        
        # 创建地图和敌人
        self.game_engine.create_map()
        self.game_engine.create_enemies(Settings.ENEMY_COUNT)
        
        # 发送初始位置给其他玩家
        if hasattr(self, 'network_manager') and self.network_manager:
            self.network_manager.send_message({
                "type": "player_position",
                "x": self.hero.rect.x,
                "y": self.hero.rect.y,
                "direction": self.hero.direction
            })



    def __check_keydown(self, event):
        """检查按下按钮的事件"""
        if event.key == pygame.K_LEFT:
            # 按下左键
            self.hero.direction = Settings.LEFT
            self.hero.is_moving = True
            self.hero.is_hit_wall = False
            # 发送移动消息给其他玩家
            if hasattr(self, 'network_manager') and self.network_manager:
                self.network_manager.send_message({
                    "type": "player_move",
                    "direction": self.hero.direction,
                    "is_moving": True,
                    "x": self.hero.rect.x,
                    "y": self.hero.rect.y
                })
        elif event.key == pygame.K_RIGHT:
            # 按下右键
            self.hero.direction = Settings.RIGHT
            self.hero.is_moving = True
            self.hero.is_hit_wall = False
            # 发送移动消息给其他玩家
            if hasattr(self, 'network_manager') and self.network_manager:
                self.network_manager.send_message({
                    "type": "player_move",
                    "direction": self.hero.direction,
                    "is_moving": True,
                    "x": self.hero.rect.x,
                    "y": self.hero.rect.y
                })
        elif event.key == pygame.K_UP:
            # 按下上键
            self.hero.direction = Settings.UP
            self.hero.is_moving = True
            self.hero.is_hit_wall = False
            # 发送移动消息给其他玩家
            if hasattr(self, 'network_manager') and self.network_manager:
                self.network_manager.send_message({
                    "type": "player_move",
                    "direction": self.hero.direction,
                    "is_moving": True,
                    "x": self.hero.rect.x,
                    "y": self.hero.rect.y
                })
        elif event.key == pygame.K_DOWN:
            # 按下下键
            self.hero.direction = Settings.DOWN
            self.hero.is_moving = True
            self.hero.is_hit_wall = False
            # 发送移动消息给其他玩家
            if hasattr(self, 'network_manager') and self.network_manager:
                self.network_manager.send_message({
                    "type": "player_move",
                    "direction": self.hero.direction,
                    "is_moving": True,
                    "x": self.hero.rect.x,
                    "y": self.hero.rect.y
                })
        elif event.key == pygame.K_SPACE:
            # 坦克发子弹
            self.hero.shot()
            # 发送射击消息给其他玩家
            if hasattr(self, 'network_manager') and self.network_manager:
                # 获取刚发射的子弹信息
                bullet_info = {
                    "type": "player_shot",
                    "direction": self.hero.direction,
                    "x": self.hero.rect.centerx,
                    "y": self.hero.rect.centery
                }
                self.network_manager.send_message(bullet_info)

    def __check_keyup(self, event):
        """检查松开按钮的事件"""
        if event.key in [pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN]:
            # 更新移动状态
            current_direction = self.hero.direction
            self.hero.is_moving = False
            
            # 发送停止移动消息给其他玩家
            if hasattr(self, 'network_manager') and self.network_manager:
                self.network_manager.send_message({
                    "type": "player_move",
                    "direction": current_direction,
                    "is_moving": False,
                    "x": self.hero.rect.x,
                    "y": self.hero.rect.y
                })

    def __event_handler(self):
        for event in pygame.event.get():
            # 判断是否是退出游戏
            if event.type == pygame.QUIT:
                # 断开网络连接
                if self.network_manager and hasattr(self.network_manager, 'connected') and self.network_manager.connected:
                    self.network_manager.disconnect()
                TankWar.__game_over()
            
            # 处理输入框事件
            if self.input_active is not None:
                self.__handle_input_events(event)
                continue
            
            elif event.type == pygame.KEYDOWN:
                TankWar.__check_keydown(self, event)
            elif event.type == pygame.KEYUP:
                TankWar.__check_keyup(self, event)
                
    def __handle_input_events(self, event):
        """
        处理输入框相关事件
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                # 确认输入
                self.__finish_input()
                
                # 根据输入类型处理后续逻辑
                if self.input_active == self.INPUT_USERNAME:
                    # 用户名输入完成，进入房间浏览
                    self.game_state = self.ROOM_BROWSE
                    self.__update_room_menu_buttons()
                elif self.input_active == self.INPUT_ROOM_NAME:
                    # 房间名称输入完成，请求输入密码
                    self.room_name = self.input_text
                    self.__start_input(self.INPUT_ROOM_PASSWORD, "输入房间密码（不输入则无密码）", self.__create_room_with_info)
                elif self.input_active == self.INPUT_ROOM_PASSWORD:
                    # 密码输入完成，创建房间
                    pass  # 这里不需要额外处理，__create_room_with_info会在__finish_input中调用
                elif self.input_active == self.INPUT_JOIN_PASSWORD:
                    # 加入密码输入完成
                    self.__join_room_with_password(self.input_text)
                
            elif event.key == pygame.K_BACKSPACE:
                # 删除字符
                self.input_text = self.input_text[:-1]
            else:
                # 添加字符
                if len(self.input_text) < 30:  # 限制输入长度
                    self.input_text += event.unicode
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # 点击输入框外部取消输入
            if not hasattr(self, 'input_box') or not self.input_box.collidepoint(event.pos):
                self.input_active = None
                self.input_text = ""
                
                # 返回到相应界面
                if hasattr(self, 'was_in_room') and self.was_in_room:
                    self.game_state = self.ROOM_BROWSE
                    self.__update_room_menu_buttons()
                else:
                    self.game_state = self.MENU
                    self.__update_main_menu_buttons()

    def __check_collide(self):
        # 使用游戏引擎处理碰撞检测
        collisions = self.game_engine.check_collisions()
        
        # 处理特殊碰撞结果
        if collisions.get('boss_wall_destroyed'):
            self.game_still = False
            
        # 处理玩家死亡
        for player_id in collisions.get('dead_players', []):
            if player_id == "local" and hasattr(self, 'network_manager') and self.network_manager:
                self.network_manager.send_message({
                    "type": "player_killed",
                    "player_id": player_id
                })

    def __update_sprites(self):
        # 使用游戏引擎更新和绘制游戏对象
        self.game_engine.update()
        self.game_engine.render()
        
        # 额外绘制玩家名称
        for player_id, tank in self.player_tanks.items():
            if hasattr(tank, 'is_alive') and tank.is_alive:
                font = pygame.font.SysFont(None, 24)
                name_text = font.render(tank.username, True, (255, 255, 255))
                name_rect = name_text.get_rect(center=(tank.rect.centerx, tank.rect.top - 15))
                self.screen.blit(name_text, name_rect)

    def run_game(self):
        # pygame已经在__init__中初始化
        
        while True:
            # 设置刷新帧率
            self.clock.tick(Settings.FPS)
            
            # 检查网络消息（如果已连接）
            if self.network_manager and hasattr(self.network_manager, 'connected') and self.network_manager.connected:
                for message in self.network_manager.get_messages():
                    self.__handle_network_message(message)
            
            # 根据游戏状态执行不同的逻辑
            if self.game_state == self.MENU:
                # 菜单状态
                self.__draw_menu()
                self.__handle_menu_events()
            elif self.game_state == self.ROOM_BROWSE:
                # 房间浏览状态
                self.__draw_room_browse()
                self.__handle_menu_events()
            elif self.game_state in [self.INPUT_USERNAME, self.INPUT_ROOM_NAME, self.INPUT_ROOM_PASSWORD, self.INPUT_JOIN_PASSWORD]:
                # 输入状态
                title_map = {
                    self.INPUT_USERNAME: "请输入您的用户名",
                    self.INPUT_ROOM_NAME: "请输入房间名称",
                    self.INPUT_ROOM_PASSWORD: "请输入房间密码（可选）",
                    self.INPUT_JOIN_PASSWORD: "请输入房间密码"
                }
                self.__draw_input_screen(title_map.get(self.game_state, "请输入"))
                # 事件处理在__event_handler中处理输入框
                self.__event_handler()
            elif self.game_state == self.IN_ROOM:
                # 在房间内状态
                self.__draw_room()
                self.__handle_menu_events()
            elif self.game_state == self.GAME_RUNNING:
                # 游戏运行状态
                if hasattr(self, 'hero') and self.hero and self.hero.is_alive and self.game_still:
                    self.screen.fill(Settings.SCREEN_COLOR)
                    # 1、事件监听
                    self.__event_handler()
                    # 2、碰撞监测
                    self.__check_collide()
                    # 3、更新/绘制精灵/经理组
                    self.__update_sprites()
                else:
                    # 游戏结束
                    self.game_state = self.GAME_OVER
                    # 可以添加游戏结束画面
                    self.__game_over()
            elif self.game_state == self.GAME_OVER:
                # 游戏结束状态
                self.__game_over()
            
            # 统一更新显示
            pygame.display.update()

    @staticmethod
    def __game_over():
        # 清理缓存资源，释放内存
        from sprites import IMAGE_CACHE, SOUND_CACHE
        IMAGE_CACHE.clear()
        SOUND_CACHE.clear()
        pygame.quit()
        exit()
