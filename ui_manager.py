# UI管理模块，负责游戏界面渲染和交互处理
import pygame
from constants import *

class UIManager:
    def __init__(self, screen):
        self.screen = screen
        # 初始化字体
        pygame.font.init()
        
        # 尝试使用支持中文的字体
        # 字体列表按优先级排序，确保至少有一个可用字体
        chinese_fonts = ['SimHei', 'Microsoft YaHei', 'SimSun', 'WenQuanYi Micro Hei', 'Heiti TC']
        
        # 初始化不同大小的字体
        self.font = self._get_font(chinese_fonts, FONT_SIZE)
        self.small_font = self._get_font(chinese_fonts, FONT_SIZE_SMALL)
        self.large_font = self._get_font(chinese_fonts, FONT_SIZE_LARGE)
    
    def _get_font(self, font_names, size):
        """
        获取可用的字体，如果指定字体不可用则回退到系统默认字体
        """
        # 首先尝试获取指定的中文字体
        for font_name in font_names:
            try:
                font = pygame.font.SysFont(font_name, size)
                # 测试是否能渲染中文
                test_surface = font.render("测试", True, WHITE)
                if test_surface.get_width() > 0:  # 确保能正常渲染
                    print(f"使用字体: {font_name}, 大小: {size}")
                    return font
            except Exception as e:
                print(f"字体 {font_name} 不可用: {e}")
        
        # 如果所有指定字体都不可用，使用系统默认字体
        print(f"使用系统默认字体，大小: {size}")
        return pygame.font.SysFont(None, size)
    
    def draw_text(self, text, x, y, color=WHITE, font=None, center=True):
        """
        在屏幕上绘制文本
        """
        if font is None:
            font = self.font
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        if center:
            text_rect.center = (x, y)
        else:
            text_rect.topleft = (x, y)
        self.screen.blit(text_surface, text_rect)
        return text_rect
    
    def create_button(self, x, y, width=BUTTON_WIDTH, height=BUTTON_HEIGHT, 
                     text="", action=None, disabled=False, color=BUTTON_COLOR):
        """
        创建按钮
        """
        rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
        return {
            "rect": rect,
            "text": text,
            "action": action,
            "disabled": disabled,
            "color": color
        }
    
    def draw_button(self, button, mouse_pos):
        """
        绘制按钮，支持悬停效果
        """
        # 确定按钮颜色
        color = button["color"]
        if button["disabled"]:
            color = GRAY
        elif button["rect"].collidepoint(mouse_pos):
            color = BUTTON_HOVER_COLOR
        
        # 绘制按钮
        pygame.draw.rect(self.screen, color, button["rect"])
        pygame.draw.rect(self.screen, WHITE, button["rect"], 2)  # 边框
        
        # 绘制按钮文本
        text_color = GRAY if button["disabled"] else BUTTON_TEXT_COLOR
        self.draw_text(button["text"], button["rect"].centerx, button["rect"].centery, text_color)
    
    def draw_menu(self, title, buttons, mouse_pos):
        """
        绘制菜单界面
        """
        # 绘制背景
        self.screen.fill(BLACK)
        
        # 绘制标题
        self.draw_text(title, SCREEN_WIDTH // 2, 100, WHITE, self.large_font)
        
        # 绘制按钮
        for button in buttons:
            self.draw_button(button, mouse_pos)
    
    def draw_room_browse(self, title, buttons, mouse_pos):
        """
        绘制房间浏览界面
        """
        self.draw_menu(title, buttons, mouse_pos)
    
    def draw_input_box(self, prompt, current_text, active):
        """
        绘制输入框
        """
        # 绘制背景
        self.screen.fill(BLACK)
        
        # 绘制提示文本
        self.draw_text(prompt, SCREEN_WIDTH // 2, 200, WHITE)
        
        # 绘制输入框
        input_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 250, 300, 50)
        pygame.draw.rect(self.screen, LIGHT_GRAY if active else GRAY, input_rect)
        pygame.draw.rect(self.screen, WHITE, input_rect, 2)  # 边框
        
        # 绘制输入的文本
        if active:
            display_text = current_text + "|"  # 添加光标
        else:
            display_text = current_text
        self.draw_text(display_text, input_rect.centerx, input_rect.centery, BLACK)
    
    def draw_room(self, room_info, players, is_host, is_ready, buttons, mouse_pos, username):
        """
        绘制房间界面，显示玩家列表和准备状态
        """
        # 绘制背景
        self.screen.fill(BLACK)
        
        # 绘制房间信息
        if room_info and "name" in room_info:
            self.draw_text(f"房间: {room_info['name']}", SCREEN_WIDTH // 2, 50, WHITE, self.large_font)
        
        # 绘制玩家列表标题
        self.draw_text("玩家列表", SCREEN_WIDTH // 2, 120, WHITE)
        
        # 绘制玩家列表
        y_position = 160
        player_count = len(players) if players else 0
        
        if players:
            for player_id, player_info in players.items():
                player_name = player_info.get("username", f"玩家{player_id}")
                is_player_host = player_info.get("is_host", False)
                player_ready = player_info.get("ready", False)
                
                # 根据状态设置文本颜色
                if player_name == username:
                    # 本地玩家
                    name_color = YELLOW
                else:
                    name_color = WHITE
                
                # 准备状态文本和颜色
                ready_text = "[已准备]" if player_ready else "[未准备]"
                ready_color = GREEN if player_ready else RED
                
                # 房主标识
                host_mark = " [房主]" if is_player_host else ""
                
                # 绘制玩家信息
                player_text = f"{player_name}{host_mark}"
                self.draw_text(player_text, SCREEN_WIDTH // 2 - 100, y_position, name_color, self.small_font, False)
                self.draw_text(ready_text, SCREEN_WIDTH // 2 + 100, y_position, ready_color, self.small_font, False)
                
                y_position += 30
        
        # 显示玩家数量
        self.draw_text(f"人数: {player_count}/4", SCREEN_WIDTH // 2, y_position + 20, WHITE)
        
        # 绘制按钮
        for button in buttons:
            self.draw_button(button, mouse_pos)