import os

# 禁用libpng警告
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
os.environ['SDL_AUDIODRIVER'] = 'directsound'

import pygame
from sprites import *


class TankWar:
    # 游戏状态常量
    MENU = 0
    GAME_RUNNING = 1
    GAME_OVER = 2

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
        self.game_state = self.MENU  # 初始状态为菜单
        self.menu_buttons = []
        self.__init_menu()

    def __init_menu(self):
        """
        初始化菜单按钮
        """
        # 按钮颜色
        self.button_color = (0, 150, 0)
        self.button_hover_color = (0, 200, 0)
        self.text_color = (255, 255, 255)
        
        # 创建字体
        self.font = pygame.font.SysFont(None, 48)
        self.title_font = pygame.font.SysFont(None, 72)
        
        # 创建按钮
        # 开始游戏按钮
        start_text = self.font.render("开始游戏", True, self.text_color)
        start_rect = start_text.get_rect(center=(Settings.SCREEN_RECT.centerx, Settings.SCREEN_RECT.centery - 50))
        self.menu_buttons.append({"text": start_text, "rect": start_rect, "action": "start"})
        
        # 退出游戏按钮
        exit_text = self.font.render("退出游戏", True, self.text_color)
        exit_rect = exit_text.get_rect(center=(Settings.SCREEN_RECT.centerx, Settings.SCREEN_RECT.centery + 50))
        self.menu_buttons.append({"text": exit_text, "rect": exit_rect, "action": "exit"})
    
    def __draw_menu(self):
        """
        绘制开始菜单
        """
        # 填充背景色
        self.screen.fill(Settings.SCREEN_COLOR)
        
        # 绘制游戏标题
        title = self.title_font.render("坦克大战", True, (255, 0, 0))
        title_rect = title.get_rect(center=(Settings.SCREEN_RECT.centerx, Settings.SCREEN_RECT.centery - 200))
        self.screen.blit(title, title_rect)
        
        # 绘制按钮
        mouse_pos = pygame.mouse.get_pos()
        for button in self.menu_buttons:
            # 检查鼠标是否悬停在按钮上
            if button["rect"].collidepoint(mouse_pos):
                # 绘制悬停状态的按钮背景
                pygame.draw.rect(self.screen, self.button_hover_color, 
                                (button["rect"].x - 10, button["rect"].y - 5, 
                                button["rect"].width + 20, button["rect"].height + 10))
            else:
                # 绘制普通状态的按钮背景
                pygame.draw.rect(self.screen, self.button_color, 
                                (button["rect"].x - 10, button["rect"].y - 5, 
                                button["rect"].width + 20, button["rect"].height + 10))
            # 绘制按钮文字
            self.screen.blit(button["text"], button["rect"])
        
        # 更新显示
        pygame.display.update()
    
    def __handle_menu_events(self):
        """
        处理菜单事件
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                TankWar.__game_over()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    # 按Enter键开始游戏
                    self.__start_game()
                elif event.key == pygame.K_ESCAPE:
                    # 按ESC键退出游戏
                    TankWar.__game_over()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    for button in self.menu_buttons:
                        if button["rect"].collidepoint(event.pos):
                            if button["action"] == "start":
                                self.__start_game()
                            elif button["action"] == "exit":
                                TankWar.__game_over()
    
    def __start_game(self):
        """
        开始游戏
        """
        self.game_state = self.GAME_RUNNING
        self.__create_sprite()
    
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
        self.hero = Hero(Settings.HERO_IMAGE_NAME, self.screen)
        self.enemies = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.walls = pygame.sprite.Group()
        for i in range(Settings.ENEMY_COUNT):
            direction = random.randint(0, 3)
            enemy = Enemy(Settings.ENEMY_IMAGES[direction], self.screen)
            enemy.direction = direction
            self.enemies.add(enemy)
        self.__draw_map()

    def __draw_map(self):
        """
        绘制地图
        :return:
        """
        for y in range(len(Settings.MAP_ONE)):
            for x in range(len(Settings.MAP_ONE[y])):
                if Settings.MAP_ONE[y][x] == 0:
                    continue
                wall = Wall(Settings.WALLS[Settings.MAP_ONE[y][x]], self.screen)
                wall.rect.x = x*Settings.BOX_SIZE
                wall.rect.y = y*Settings.BOX_SIZE
                if Settings.MAP_ONE[y][x] == Settings.RED_WALL:
                    wall.type = Settings.RED_WALL
                elif Settings.MAP_ONE[y][x] == Settings.IRON_WALL:
                    wall.type = Settings.IRON_WALL
                elif Settings.MAP_ONE[y][x] == Settings.WEED_WALL:
                    wall.type = Settings.WEED_WALL
                elif Settings.MAP_ONE[y][x] == Settings.BOSS_WALL:
                    wall.type = Settings.BOSS_WALL
                    wall.life = 1
                self.walls.add(wall)

    def __check_keydown(self, event):
        """检查按下按钮的事件"""
        if event.key == pygame.K_LEFT:
            # 按下左键
            self.hero.direction = Settings.LEFT
            self.hero.is_moving = True
            self.hero.is_hit_wall = False
        elif event.key == pygame.K_RIGHT:
            # 按下右键
            self.hero.direction = Settings.RIGHT
            self.hero.is_moving = True
            self.hero.is_hit_wall = False
        elif event.key == pygame.K_UP:
            # 按下上键
            self.hero.direction = Settings.UP
            self.hero.is_moving = True
            self.hero.is_hit_wall = False
        elif event.key == pygame.K_DOWN:
            # 按下下键
            self.hero.direction = Settings.DOWN
            self.hero.is_moving = True
            self.hero.is_hit_wall = False
        elif event.key == pygame.K_SPACE:
            # 坦克发子弹
            self.hero.shot()

    def __check_keyup(self, event):
        """检查松开按钮的事件"""
        if event.key == pygame.K_LEFT:
            # 松开左键
            self.hero.direction = Settings.LEFT
            self.hero.is_moving = False
        elif event.key == pygame.K_RIGHT:
            # 松开右键
            self.hero.direction = Settings.RIGHT
            self.hero.is_moving = False
        elif event.key == pygame.K_UP:
            # 松开上键
            self.hero.direction = Settings.UP
            self.hero.is_moving = False
        elif event.key == pygame.K_DOWN:
            # 松开下键
            self.hero.direction = Settings.DOWN
            self.hero.is_moving = False

    def __event_handler(self):
        for event in pygame.event.get():
            # 判断是否是退出游戏
            if event.type == pygame.QUIT:
                TankWar.__game_over()
            elif event.type == pygame.KEYDOWN:
                TankWar.__check_keydown(self, event)
            elif event.type == pygame.KEYUP:
                TankWar.__check_keyup(self, event)

    def __check_collide(self):
        # 保证坦克不移出屏幕
        self.hero.hit_wall()
        for enemy in self.enemies:
            enemy.hit_wall_turn()

        # 收集所有敌方子弹到一个组，便于批量检测
        all_enemy_bullets = pygame.sprite.Group()
        for enemy in self.enemies:
            all_enemy_bullets.add(enemy.bullets)

        # 使用pygame内置的groupcollide方法优化子弹与墙的碰撞检测
        # 我方子弹与墙的碰撞
        for bullet, walls_hit in pygame.sprite.groupcollide(self.hero.bullets, self.walls, False, False).items():
            for wall in walls_hit:
                bullet.kill()
                if wall.type == Settings.RED_WALL:
                    wall.kill()
                elif wall.type == Settings.BOSS_WALL:
                    self.game_still = False

        # 敌方子弹与墙的碰撞
        for bullet, walls_hit in pygame.sprite.groupcollide(all_enemy_bullets, self.walls, False, False).items():
            for wall in walls_hit:
                bullet.kill()
                if wall.type == Settings.RED_WALL:
                    wall.kill()
                elif wall.type == Settings.BOSS_WALL:
                    self.game_still = False

        # 坦克与墙的碰撞检测 - 使用spritecollide方法
        # 我方坦克撞墙
        walls_hit_by_hero = pygame.sprite.spritecollide(self.hero, self.walls, False)
        for wall in walls_hit_by_hero:
            if wall.type == Settings.RED_WALL or wall.type == Settings.IRON_WALL or wall.type == Settings.BOSS_WALL:
                self.hero.is_hit_wall = True
                self.hero.move_out_wall(wall)

        # 敌方坦克撞墙
        for enemy in self.enemies:
            walls_hit_by_enemy = pygame.sprite.spritecollide(enemy, self.walls, False)
            for wall in walls_hit_by_enemy:
                if wall.type == Settings.RED_WALL or wall.type == Settings.IRON_WALL or wall.type == Settings.BOSS_WALL:
                    enemy.move_out_wall(wall)
                    enemy.random_turn()

        # 我方子弹击中敌方坦克
        pygame.sprite.groupcollide(self.hero.bullets, self.enemies, True, True)
        
        # 敌方子弹击中我方坦克
        if self.hero.is_alive:
            bullets_hit_hero = pygame.sprite.spritecollide(self.hero, all_enemy_bullets, True)
            if bullets_hit_hero:
                self.hero.kill()

    def __update_sprites(self):
        # 总是更新英雄坦克，确保方向变化时图像也会更新
        self.hero.update()
        self.walls.update()
        self.hero.bullets.update()
        self.enemies.update()
        for enemy in self.enemies:
            enemy.bullets.update()
            enemy.bullets.draw(self.screen)
        self.enemies.draw(self.screen)
        self.hero.bullets.draw(self.screen)
        self.screen.blit(self.hero.image, self.hero.rect)
        self.walls.draw(self.screen)

    def run_game(self):
        # pygame已经在__init__中初始化
        
        while True:
            # 设置刷新帧率
            self.clock.tick(Settings.FPS)
            
            # 根据游戏状态执行不同的逻辑
            if self.game_state == self.MENU:
                # 菜单状态
                self.__draw_menu()
                self.__handle_menu_events()
            elif self.game_state == self.GAME_RUNNING:
                # 游戏运行状态
                if self.hero.is_alive and self.game_still:
                    self.screen.fill(Settings.SCREEN_COLOR)
                    # 1、事件监听
                    self.__event_handler()
                    # 2、碰撞监测
                    self.__check_collide()
                    # 3、更新/绘制精灵/经理组
                    self.__update_sprites()
                    # 4、更新显示
                    pygame.display.update()
                else:
                    # 游戏结束
                    self.game_state = self.GAME_OVER
                    # 可以添加游戏结束画面
                    self.__game_over()
            elif self.game_state == self.GAME_OVER:
                # 游戏结束状态
                self.__game_over()

    @staticmethod
    def __game_over():
        # 清理缓存资源，释放内存
        from sprites import IMAGE_CACHE, SOUND_CACHE
        IMAGE_CACHE.clear()
        SOUND_CACHE.clear()
        pygame.quit()
        exit()
