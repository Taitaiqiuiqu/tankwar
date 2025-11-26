# 游戏引擎模块，包含核心游戏逻辑
import os
import pygame
import random
from constants import *

# 导入设置和创建图像缓存
from settings import Settings

IMAGE_CACHE = {}

class GameObject:
    """
    游戏对象基类
    """
    def __init__(self, x, y, width, height, color=WHITE, image_name=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.active = True
        self.image_name = image_name
        self.image = None
        
        # 如果提供了图像名称，加载图像
        if image_name:
            self.load_image(image_name)
    
    def load_image(self, image_name):
        """
        加载图像到缓存，确保使用正确的路径格式
        """
        # 确保图像路径格式正确（统一使用./开头的相对路径）
        if not image_name.startswith('./') and not image_name.startswith('resources/'):
            # 如果路径不以./或resources/开头，添加./
            if os.path.exists(f'./{image_name}'):
                image_name = f'./{image_name}'
            elif os.path.exists(f'resources/{image_name}'):
                image_name = f'resources/{image_name}'
        
        if image_name not in IMAGE_CACHE:
            try:
                # 尝试加载图像
                image = pygame.image.load(image_name)
                # 缩放图像以匹配对象大小
                image = pygame.transform.scale(image, (self.rect.width, self.rect.height))
                IMAGE_CACHE[image_name] = image
                print(f"成功加载图像: {image_name}")
            except Exception as e:
                print(f"无法加载图像 {image_name}: {e}")
                return False
        
        self.image = IMAGE_CACHE[image_name]
        return True
    
    def draw(self, screen):
        """
        绘制游戏对象
        """
        if self.active:
            if self.image:
                # 确保图像和矩形大小一致
                if self.image.get_width() != self.rect.width or self.image.get_height() != self.rect.height:
                    self.image = pygame.transform.scale(self.image, (self.rect.width, self.rect.height))
                # 使用图像绘制
                screen.blit(self.image, self.rect)
            else:
                # 备用：如果没有图像，使用矩形绘制
                pygame.draw.rect(screen, self.color, self.rect)
    
    def update(self):
        """
        更新游戏对象状态
        """
        pass

class Tank(GameObject):
    """
    坦克类
    """
    def __init__(self, x, y, player_id, username, color=GREEN, is_local=False):
        # 初始不加载图像，等待direction设置后再加载
        super().__init__(x, y, 30, 30, color)
        self.player_id = player_id
        self.username = username
        self.direction = "up"  # 初始方向
        self.speed = 3
        self.shoot_cooldown = 0
        self.max_health = 100
        self.health = self.max_health
        self.is_local = is_local  # 是否是本地玩家
        
        # 根据是否是本地玩家选择图像路径字典
        if is_local:
            self.image_dict = Settings.HERO_IMAGES
            print("本地玩家图像字典:", self.image_dict)
        else:
            self.image_dict = Settings.ENEMY_IMAGES
            print("敌方玩家图像字典:", self.image_dict)
        
        # 加载初始方向的图像
        self.update_image()
    
    def update_image(self):
        """
        根据当前方向更新坦克图像，确保方向映射正确且图像加载成功
        """
        # 方向映射：将字符串方向映射到Settings中的常量
        direction_map = {
            "up": Settings.UP,
            "down": Settings.DOWN,
            "left": Settings.LEFT,
            "right": Settings.RIGHT
        }
        
        # 获取对应的方向常量
        dir_constant = direction_map.get(self.direction, Settings.UP)
        print(f"坦克方向: {self.direction}, 方向常量: {dir_constant}")
        
        # 检查方向常量是否在图像字典中
        if dir_constant in self.image_dict:
            image_path = self.image_dict[dir_constant]
            print(f"加载图像: {image_path}")
            success = self.load_image(image_path)
            if not success:
                print(f"警告: 无法加载图像 {image_path}")
        else:
            print(f"错误: 方向常量 {dir_constant} 不在图像字典中")
            # 使用默认图像作为备选
            if hasattr(Settings, 'HERO_IMAGE_NAME') and self.is_local:
                self.load_image(Settings.HERO_IMAGE_NAME)
            elif hasattr(Settings, 'ENEMY_IMAGES') and not self.is_local and Settings.UP in Settings.ENEMY_IMAGES:
                self.load_image(Settings.ENEMY_IMAGES[Settings.UP])
    
    def move(self, direction):
        """
        移动坦克
        """
        self.direction = direction
        
        # 更新图像
        self.update_image()
        
        if direction == "up":
            self.rect.y -= self.speed
        elif direction == "down":
            self.rect.y += self.speed
        elif direction == "left":
            self.rect.x -= self.speed
        elif direction == "right":
            self.rect.x += self.speed
        
        # 确保坦克不会移出屏幕
        self.rect.x = max(0, min(self.rect.x, SCREEN_WIDTH - self.rect.width))
        self.rect.y = max(0, min(self.rect.y, SCREEN_HEIGHT - self.rect.height))
    
    def shoot(self):
        """
        发射子弹
        """
        if self.shoot_cooldown <= 0:
            # 计算子弹初始位置（从坦克中心发射）
            if self.direction == "up":
                bullet_x = self.rect.centerx - 5
                bullet_y = self.rect.top - 10
            elif self.direction == "down":
                bullet_x = self.rect.centerx - 5
                bullet_y = self.rect.bottom
            elif self.direction == "left":
                bullet_x = self.rect.left - 10
                bullet_y = self.rect.centery - 5
            elif self.direction == "right":
                bullet_x = self.rect.right
                bullet_y = self.rect.centery - 5
            
            bullet = Bullet(bullet_x, bullet_y, self.direction, self.player_id)
            self.shoot_cooldown = 20  # 冷却时间
            return bullet
        return None
    
    def update(self):
        """
        更新坦克状态
        """
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

        # 如果坦克有 is_moving 属性，按照方向持续移动
        if hasattr(self, 'is_moving') and self.is_moving:
            # 支持字符串方向或Settings常量
            dir_map = {
                Settings.LEFT: "left",
                Settings.RIGHT: "right",
                Settings.UP: "up",
                Settings.DOWN: "down",
                "left": "left",
                "right": "right",
                "up": "up",
                "down": "down"
            }
            cur_dir = self.direction
            if cur_dir in dir_map:
                self.move(dir_map[cur_dir])
    
    def draw(self, screen):
        """
        绘制坦克
        """
        super().draw(screen)
        
        # 绘制坦克炮管
        if self.direction == "up":
            pygame.draw.rect(screen, WHITE, (self.rect.centerx - 2, self.rect.top - 10, 4, 10))
        elif self.direction == "down":
            pygame.draw.rect(screen, WHITE, (self.rect.centerx - 2, self.rect.bottom, 4, 10))
        elif self.direction == "left":
            pygame.draw.rect(screen, WHITE, (self.rect.left - 10, self.rect.centery - 2, 10, 4))
        elif self.direction == "right":
            pygame.draw.rect(screen, WHITE, (self.rect.right, self.rect.centery - 2, 10, 4))
        
        # 绘制血量条
        health_bar_width = self.rect.width
        health_bar_height = 5
        health_percentage = self.health / self.max_health
        
        # 背景
        pygame.draw.rect(screen, RED, (self.rect.x, self.rect.y - 10, health_bar_width, health_bar_height))
        # 当前血量
        pygame.draw.rect(screen, GREEN, (self.rect.x, self.rect.y - 10, health_bar_width * health_percentage, health_bar_height))

class Bullet(GameObject):
    """
    子弹类
    """
    def __init__(self, x, y, direction, owner_id):
        # 使用Settings中的子弹图像
        super().__init__(x, y, 10, 10, YELLOW, Settings.BULLET_IMAGE_NAME)
        self.direction = direction
        self.owner_id = owner_id
        self.speed = 6
        self.lifetime = 60  # 子弹存在时间
    
    def update(self):
        """
        更新子弹位置
        """
        if self.direction == "up":
            self.rect.y -= self.speed
        elif self.direction == "down":
            self.rect.y += self.speed
        elif self.direction == "left":
            self.rect.x -= self.speed
        elif self.direction == "right":
            self.rect.x += self.speed
        
        # 减少子弹寿命
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.active = False
        
        # 检查是否超出屏幕
        if (self.rect.x < 0 or self.rect.x > SCREEN_WIDTH or 
            self.rect.y < 0 or self.rect.y > SCREEN_HEIGHT):
            self.active = False

class Wall(GameObject):
    """
    墙壁类
    支持多种墙壁类型：
    RED_WALL (1): 红墙（可破坏）
    IRON_WALL (2): 铁墙（不可破坏）
    WEED_WALL (3): 草（半透明，可穿过）
    BOSS_WALL (5): 老家/boss墙（特殊处理）
    """
    def __init__(self, x, y, wall_type=1):
        # 确保使用Settings中定义的墙壁类型常量
        self.wall_type = wall_type
        print(f"创建墙壁，类型: {wall_type}")
        
        # 根据墙壁类型设置颜色和图像路径
        if wall_type == Settings.RED_WALL:  # 红墙
            color = RED
            # 使用与Settings中一致的图像路径格式
            image_path = f"./resources/images/walls/{wall_type}.png"
            self.destructible = True
        elif wall_type == Settings.IRON_WALL:  # 铁墙
            color = GRAY
            image_path = f"./resources/images/walls/{wall_type}.png"
            self.destructible = False
        elif wall_type == Settings.WEED_WALL:  # 草
            color = GREEN
            image_path = f"./resources/images/walls/{wall_type}.png"
            self.destructible = False  # 草通常不可破坏
        elif wall_type == Settings.BOSS_WALL:  # 老家/boss墙
            color = YELLOW
            # 特殊处理老家墙图像路径
            if hasattr(Settings, 'BOSS_IMAGE'):
                image_path = Settings.BOSS_IMAGE
            else:
                image_path = f"./resources/images/walls/{wall_type}.png"
            self.destructible = False  # 老家墙不可破坏
        else:
            color = WHITE
            image_path = None
            self.destructible = False
            print(f"警告: 未知的墙壁类型 {wall_type}")
        
        # 初始化父类，传入图像路径
        super().__init__(x, y, 30, 30, color, image_path)
        
        # 如果图像加载失败，尝试备用路径
        if image_path and not self.image:
            print(f"尝试备用图像路径: resources/images/walls/{wall_type}.png")
            self.load_image(f"resources/images/walls/{wall_type}.png")
        
        # 对于草墙，设置半透明属性
        if wall_type == Settings.WEED_WALL and self.image:
            self.image.set_alpha(100)  # 设置半透明效果

class GameEngine:
    """
    游戏引擎类，管理游戏对象和游戏逻辑
    """
    def __init__(self):
        self.tanks = []
        self.bullets = []
        self.walls = []
        self.local_player_id = None
        self.game_over = False
        self.winner_id = None
    
    def init_game(self, players, local_player_id):
        """
        初始化游戏
        """
        self.tanks = []
        self.bullets = []
        self.walls = []
        self.local_player_id = local_player_id
        self.game_over = False
        self.winner_id = None
        
        # 创建坦克
        colors = [GREEN, RED, BLUE, YELLOW]
        start_positions = [
            (50, 50),
            (SCREEN_WIDTH - 80, 50),
            (50, SCREEN_HEIGHT - 80),
            (SCREEN_WIDTH - 80, SCREEN_HEIGHT - 80)
        ]
        
        # 创建玩家坦克
        for i, (player_id, player_info) in enumerate(players.items()):
            username = player_info.get("username", f"玩家{i+1}")
            is_local = player_id == local_player_id
            color_index = i % len(colors)
            x, y = start_positions[i % len(start_positions)]
            
            tank = Tank(x, y, player_id, username, colors[color_index], is_local)
            self.tanks.append(tank)
        
        # 单人游戏时生成敌人坦克
        if len(players) == 1:
            enemy_count = Settings.ENEMY_COUNT
            enemy_positions = [
                (100, 100),
                (SCREEN_WIDTH - 130, 100),
                (100, SCREEN_HEIGHT - 130),
                (SCREEN_WIDTH - 130, SCREEN_HEIGHT - 130),
                (SCREEN_WIDTH // 2 - 15, 100)
            ]
            
            for i in range(enemy_count):
                enemy_id = f"enemy_{i+1}"
                enemy_name = f"敌人{i+1}"
                is_local = False
                # 敌人使用红色
                color = RED
                # 从敌人起始位置列表中选择位置
                x, y = enemy_positions[i % len(enemy_positions)]
                
                # 创建敌人坦克
                enemy_tank = Tank(x, y, enemy_id, enemy_name, color, is_local)
                self.tanks.append(enemy_tank)
                print(f"生成敌人坦克 {enemy_name} 在位置 ({x}, {y})")
        
        # 创建地图障碍
        self._create_map()
    
    def _create_map(self):
        """
        创建游戏地图
        使用settings.py中的MAP_ONE预设地图
        """
        # 调用load_map方法加载预设地图
        self.load_map(Settings.MAP_ONE)
    
    def update(self):
        """
        更新游戏状态
        """
        if self.game_over:
            return
        
        # 更新坦克
        for tank in self.tanks[:]:
            if hasattr(tank, 'is_alive') and not tank.is_alive:
                self.tanks.remove(tank)
                continue
                
            # 调用tank的update方法，这将处理基于is_moving属性的移动
            # 简单AI: 如果不是本地玩家，则随机移动/转向
            if not getattr(tank, 'is_local', False):
                # 确保is_moving属性存在
                if not hasattr(tank, 'is_moving'):
                    tank.is_moving = False
                # 随机决定是否改变移动状态或方向
                if random.random() < 0.02:  # ~2% 每帧改变一次行为
                    tank.is_moving = not tank.is_moving
                if random.random() < 0.05:  # ~5% 改变方向
                    tank.direction = random.choice(["up", "down", "left", "right"])
            tank.update()
            
            # 处理边界碰撞
            if hasattr(tank, 'hit_wall'):
                tank.hit_wall()
                
            # 对于Enemy类，处理撞墙转向
            if hasattr(tank, 'hit_wall_turn'):
                tank.hit_wall_turn()
                
        # 更新敌人坦克AI逻辑（如果有）
        # 更新子弹
        for bullet in self.bullets[:]:
            if not bullet.active:
                self.bullets.remove(bullet)
                continue
                
            bullet.update()
        
        # 检测碰撞
        self._check_collisions()
        
        # 检查游戏是否结束
        active_tanks = [tank for tank in self.tanks if tank.active and tank.health > 0]
        if len(active_tanks) <= 1:
            if active_tanks:
                self.winner_id = active_tanks[0].player_id
            self.game_over = True
    
    def _check_collisions(self):
        """
        检测游戏对象之间的碰撞
        """
        # 子弹与墙壁碰撞
        for bullet in self.bullets[:]:
            for wall in self.walls[:]:
                if bullet.active and wall.active and bullet.rect.colliderect(wall.rect):
                    bullet.active = False
                    if wall.destructible:
                        wall.active = False
                        self.walls.remove(wall)
                    break
        
        # 子弹与坦克碰撞
        for bullet in self.bullets[:]:
            if not bullet.active:
                continue
                
            for tank in self.tanks[:]:
                if (bullet.active and tank.active and tank.health > 0 and 
                    bullet.owner_id != tank.player_id and 
                    bullet.rect.colliderect(tank.rect)):
                    bullet.active = False
                    tank.health -= 25  # 子弹造成25点伤害
                    
                    if tank.health <= 0:
                        tank.health = 0
                        tank.active = False
                    break
        
        # 坦克与墙壁碰撞
        for tank in self.tanks[:]:
            if not tank.active:
                continue
                
            # 保存当前位置
            prev_x, prev_y = tank.rect.x, tank.rect.y
            
            # 检查与所有墙壁的碰撞
            collision = False
            for wall in self.walls:
                if wall.active and tank.rect.colliderect(wall.rect):
                    collision = True
                    break
            
            # 如果发生碰撞，恢复到之前的位置
            if collision:
                tank.rect.x, tank.rect.y = prev_x, prev_y
        
        # 坦克之间的碰撞
        for i, tank1 in enumerate(self.tanks):
            if not tank1.active:
                continue
                
            for tank2 in self.tanks[i+1:]:
                if tank1.active and tank2.active and tank1.rect.colliderect(tank2.rect):
                    # 简单处理：将两个坦克分开一点
                    dx = tank1.rect.centerx - tank2.rect.centerx
                    dy = tank1.rect.centery - tank2.rect.centery
                    
                    # 归一化方向向量
                    distance = max(1, (dx**2 + dy**2)**0.5)
                    dx /= distance
                    dy /= distance
                    
                    # 移动坦克
                    push_distance = 2
                    tank1.rect.x += dx * push_distance
                    tank1.rect.y += dy * push_distance
                    tank2.rect.x -= dx * push_distance
                    tank2.rect.y -= dy * push_distance
    
    def handle_shoot(self, player_id):
        """
        处理射击事件
        """
        for tank in self.tanks:
            if tank.player_id == player_id:
                bullet = tank.shoot()
                if bullet:
                    self.bullets.append(bullet)
                    return bullet
        return None
    
    def draw(self, screen):
        """
        绘制游戏画面
        """
        # 绘制背景
        screen.fill(BLACK)
        
        # 绘制墙壁
        for wall in self.walls:
            wall.draw(screen)
        
        # 绘制子弹
        for bullet in self.bullets:
            bullet.draw(screen)
        
        # 绘制坦克
        for tank in self.tanks:
            tank.draw(screen)
        
        # 如果游戏结束，显示游戏结束信息
        if self.game_over:
            font = pygame.font.SysFont(None, 64)
            if self.winner_id:
                winner_tank = next((t for t in self.tanks if t.player_id == self.winner_id), None)
                winner_name = winner_tank.username if winner_tank else "未知"
                text = font.render(f"游戏结束！胜利者: {winner_name}", True, WHITE)
            else:
                text = font.render("游戏结束！", True, WHITE)
            
            text_rect = text.get_rect(center=(Settings.SCREEN_RECT.width // 2, Settings.SCREEN_RECT.height // 2))
            screen.blit(text, text_rect)
    
    def get_game_state(self):
        """
        获取当前游戏状态（用于网络同步）
        """
        return {
            "tanks": [{
                "id": tank.player_id,
                "x": tank.rect.x,
                "y": tank.rect.y,
                "health": tank.health,
                "direction": tank.direction
            } for tank in self.tanks],
            "bullets": [{
                "x": bullet.rect.x,
                "y": bullet.rect.y,
                "direction": bullet.direction,
                "owner_id": bullet.owner_id
            } for bullet in self.bullets],
            "game_over": self.game_over,
            "winner_id": self.winner_id
        }
    
    def load_map(self, map_data):
        """
        加载地图数据
        """
        self.walls = []
        for y, row in enumerate(map_data):
            for x, cell in enumerate(row):
                if cell == 1 or cell == 2 or cell == 3 or cell == 5:
                    # 根据cell值设置墙壁类型
                    wall_type = cell
                    # 创建墙壁，使用BOX_SIZE作为单元格大小
                    wall = Wall(x * Settings.BOX_SIZE, y * Settings.BOX_SIZE, wall_type)
                    self.walls.append(wall)
    
    def set_game_state(self, game_state):
        """
        设置游戏状态（用于网络同步）
        """
        # 这里可以实现根据接收到的游戏状态更新本地游戏对象
        pass