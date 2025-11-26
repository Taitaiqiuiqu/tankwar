# 游戏状态管理模块，负责处理游戏状态和状态转换
from constants import *

class GameStateManager:
    def __init__(self):
        # 初始化游戏状态
        self.game_state = MENU
        # 初始化输入状态
        self.input_active = None
        self.input_text = ""
        self.input_callback = None
        # 游戏相关状态
        self.is_host = False
        self.is_ready = False
        self.players = {}
        self.room_info = None
        self.room_to_join = None
        self.join_room_password = None
        self.join_attempt_password = None
        self.username = "玩家"
        self.was_in_room = False
    
    def set_game_state(self, state):
        """
        设置游戏状态
        """
        self.game_state = state
    
    def start_input(self, input_type, callback):
        """
        开始输入模式
        """
        self.game_state = INPUT
        self.input_active = input_type
        self.input_text = ""
        self.input_callback = callback
    
    def finish_input(self):
        """
        完成输入，调用回调函数
        """
        if self.input_callback and self.input_active is not None:
            self.input_callback(self.input_text)
        self.input_active = None
        self.input_text = ""
        self.input_callback = None
    
    def reset_game_state(self):
        """
        重置游戏状态，清理房间相关信息
        """
        # 重置房间相关属性
        self.is_host = False
        self.is_ready = False
        self.players = {}
        self.room_info = None
        self.room_to_join = None
        self.join_room_password = None
        self.join_attempt_password = None
        # 重置输入状态
        self.input_active = None
        self.input_text = ""
        self.input_callback = None
    
    def set_username(self, username):
        """
        设置用户名
        """
        self.username = username or "玩家"
    
    def toggle_ready(self):
        """
        切换准备状态
        """
        self.is_ready = not self.is_ready
        return self.is_ready
    
    def add_player(self, peer_id, player_info):
        """
        添加玩家
        """
        self.players[peer_id] = player_info
    
    def remove_player(self, peer_id):
        """
        移除玩家
        """
        if peer_id in self.players:
            del self.players[peer_id]
    
    def update_player_status(self, peer_id, status):
        """
        更新玩家状态
        """
        if peer_id in self.players:
            self.players[peer_id].update(status)
    
    def update_player_ready_status(self, username, ready):
        """
        根据用户名更新玩家准备状态
        """
        for peer_id, player in self.players.items():
            if player.get("username") == username:
                player["ready"] = ready
                return True
        return False
    
    def set_room_info(self, room_info):
        """
        设置房间信息
        """
        self.room_info = room_info
    
    def check_all_players_ready(self):
        """
        检查所有玩家是否都已准备
        """
        if not self.players:
            return False
        
        for peer_id, player in self.players.items():
            if not player.get("ready", False):
                return False
        return True
    
    def get_player_count(self):
        """
        获取玩家数量
        """
        return len(self.players)
    
    def is_input_active(self):
        """
        检查是否处于输入状态
        """
        return self.input_active is not None