import os
import time
import random

# 禁用libpng警告
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
os.environ['SDL_AUDIODRIVER'] = 'directsound'

import pygame
from settings import Settings

# 图像和音效缓存
IMAGE_CACHE = {}
SOUND_CACHE = {}


class BaseSprite(pygame.sprite.Sprite):
    """
    BaseSprite类，游戏中所有变化物体的底层父类
    """
    def __init__(self, image_name, screen):
        super().__init__()
        self.screen = screen
        self.direction = None
        self.speed = None
        # 使用图像缓存避免重复加载
        if image_name not in IMAGE_CACHE:
            IMAGE_CACHE[image_name] = pygame.image.load(image_name)
        self.image = IMAGE_CACHE[image_name]
        self.rect = self.image.get_rect()

    def update(self):
        # 只有在is_moving为True时才移动（如果对象有这个属性）
        if hasattr(self, 'is_moving') and not self.is_moving:
            return
        
        # 根据方向移动
        if self.direction == Settings.LEFT:
            self.rect.x -= self.speed
        elif self.direction == Settings.RIGHT:
            self.rect.x += self.speed
        elif self.direction == Settings.UP:
            self.rect.y -= self.speed
        elif self.direction == Settings.DOWN:
            self.rect.y += self.speed


class Bullet(BaseSprite):

    def __init__(self, image_name, screen):
        super().__init__(image_name, screen)
        self.speed = Settings.BULLET_SPEED
        self.original_image = self.image  # 保存原始图像，用于旋转
    
    def rotate(self):
        """
        根据方向旋转子弹图像
        """
        if self.direction == Settings.RIGHT:
            # 向右方向，无需旋转（默认可能就是向右）
            pass
        elif self.direction == Settings.LEFT:
            # 向左方向，旋转180度
            self.image = pygame.transform.rotate(self.original_image, 180)
        elif self.direction == Settings.UP:
            # 向上方向，旋转90度（逆时针）
            self.image = pygame.transform.rotate(self.original_image, 90)
        elif self.direction == Settings.DOWN:
            # 向下方向，旋转270度（顺时针）或-90度
            self.image = pygame.transform.rotate(self.original_image, -90)
        
        # 更新矩形位置以保持中心不变
        old_center = self.rect.center
        self.rect = self.image.get_rect()
        self.rect.center = old_center


class TankSprite(BaseSprite):
    """
    ImageSprite类，BaseSprite的子类，所有带图片的精灵的父类
    """
    def __init__(self, image_name, screen):
        super().__init__(image_name, screen)
        self.type = None
        self.bullets = pygame.sprite.Group()
        self.is_alive = True
        self.is_moving = False

    def shot(self):
        """
        射击类，坦克调用该类发射子弹
        :return:
        """

        # 把消失的子弹移除
        self.__remove_sprites()
        if not self.is_alive:
            return
        if len(self.bullets) >= 3:
            return
        if self.type == Settings.HERO:
            # 使用声音缓存避免重复加载
            if Settings.FIRE_MUSIC not in SOUND_CACHE:
                SOUND_CACHE[Settings.FIRE_MUSIC] = pygame.mixer.Sound(Settings.FIRE_MUSIC)
            SOUND_CACHE[Settings.FIRE_MUSIC].play()

        # 发射子弹
        bullet = Bullet(Settings.BULLET_IMAGE_NAME, self.screen)
        # 确保在设置子弹位置之前设置方向
        current_direction = self.direction  # 保存当前方向，避免在设置过程中方向被更改
        bullet.direction = current_direction
        
        # 旋转子弹图像以匹配方向
        bullet.rotate()
        
        if current_direction == Settings.LEFT:
            bullet.rect.right = self.rect.left
            bullet.rect.centery = self.rect.centery
        elif current_direction == Settings.RIGHT:
            bullet.rect.left = self.rect.right
            bullet.rect.centery = self.rect.centery
        elif current_direction == Settings.UP:
            bullet.rect.bottom = self.rect.top
            bullet.rect.centerx = self.rect.centerx
        elif current_direction == Settings.DOWN:
            bullet.rect.top = self.rect.bottom
            bullet.rect.centerx = self.rect.centerx
        
        self.bullets.add(bullet)

    def move_out_wall(self, wall):
        if self.direction == Settings.LEFT:
            self.rect.left = wall.rect.right + 2
        elif self.direction == Settings.RIGHT:
            self.rect.right = wall.rect.left - 2
        elif self.direction == Settings.UP:
            self.rect.top = wall.rect.bottom + 2
        elif self.direction == Settings.DOWN:
            self.rect.bottom = wall.rect.top - 2

    def __remove_sprites(self):
        """
        移除无用的子弹
        :return:
        """
        for bullet in self.bullets:
            if bullet.rect.bottom <= 0 or \
                    bullet.rect.top >= Settings.SCREEN_RECT.bottom or \
                    bullet.rect.right <= 0 or \
                    bullet.rect.left >= Settings.SCREEN_RECT.right:
                self.bullets.remove(bullet)
                bullet.kill()

    def update(self):
        if not self.is_alive:
            return
        super(TankSprite, self).update()

    def boom(self):
        # 使用声音缓存
        if Settings.BOOM_MUSIC not in SOUND_CACHE:
            SOUND_CACHE[Settings.BOOM_MUSIC] = pygame.mixer.Sound(Settings.BOOM_MUSIC)
        SOUND_CACHE[Settings.BOOM_MUSIC].play()
        
        # 使用图像缓存播放爆炸动画
        for boom in Settings.BOOMS:
            if boom not in IMAGE_CACHE:
                IMAGE_CACHE[boom] = pygame.image.load(boom)
            self.image = IMAGE_CACHE[boom]
            # 只更新精灵组，不直接更新显示，由主循环统一管理更新
            # pygame.display.update(self.rect)
            
        super(TankSprite, self).kill()

    def kill(self):
        self.is_alive = False
        # 直接调用boom方法，避免使用线程导致的内存泄漏
        self.boom()


class Hero(TankSprite):

    def __init__(self, image_name, screen):
        super(Hero, self).__init__(image_name, screen)
        self.type = Settings.HERO
        self.speed = Settings.HERO_SPEED
        self.direction = Settings.UP
        self.is_hit_wall = False

        # 初始化英雄的位置
        self.rect.centerx = Settings.SCREEN_RECT.centerx - Settings.BOX_RECT.width * 2
        self.rect.bottom = Settings.SCREEN_RECT.bottom

    def __turn(self):
        image_name = Settings.HERO_IMAGES.get(self.direction)
        if image_name not in IMAGE_CACHE:
            IMAGE_CACHE[image_name] = pygame.image.load(image_name)
        self.image = IMAGE_CACHE[image_name]

    def hit_wall(self):
        if self.direction == Settings.LEFT and self.rect.left <= 0 or \
                self.direction == Settings.RIGHT and self.rect.right >= Settings.SCREEN_RECT.right or \
                self.direction == Settings.UP and self.rect.top <= 0 or \
                self.direction == Settings.DOWN and self.rect.bottom >= Settings.SCREEN_RECT.bottom:
            self.is_hit_wall = True

    def update(self):
        # 始终更新图像方向
        self.__turn()
        # 只有在移动且没有撞墙时才更新位置
        if not self.is_hit_wall and self.is_moving:
            super().update()

    def kill(self):
        self.is_alive = False
        self.boom()


class Enemy(TankSprite):

    def __init__(self, image_name, screen):
        super().__init__(image_name, screen)
        self.is_hit_wall = False
        self.type = Settings.ENEMY
        self.speed = Settings.ENEMY_SPEED
        self.direction = random.randint(0, 3)
        self.terminal = float(random.randint(40*2, 40*8))
        # 添加帧计数器来控制AI更新频率
        self.ai_update_counter = 0
        self.shoot_update_counter = 0
        # 随机设置每个敌人的AI和射击间隔，增加行为多样性
        self.ai_update_interval = random.randint(30, 60)  # 30-60帧更新一次AI
        self.shoot_update_interval = random.randint(20, 50)  # 20-50帧尝试射击一次

    def random_turn(self):
        # 随机转向
        self.is_hit_wall = False
        directions = [i for i in range(4)]
        directions.remove(self.direction)
        self.direction = directions[random.randint(0, 2)]
        self.terminal = float(random.randint(40*2, 40*8))
        image_name = Settings.ENEMY_IMAGES.get(self.direction)
        if image_name not in IMAGE_CACHE:
            IMAGE_CACHE[image_name] = pygame.image.load(image_name)
        self.image = IMAGE_CACHE[image_name]

    def random_shot(self):
        shot_flag = random.choice([True] + [False]*59)
        if shot_flag:
            super().shot()

    def hit_wall_turn(self):
        turn = False
        if self.direction == Settings.LEFT and self.rect.left <= 0:
            turn = True
            self.rect.left = 2
        elif self.direction == Settings.RIGHT and self.rect.right >= Settings.SCREEN_RECT.right-1:
            turn = True
            self.rect.right = Settings.SCREEN_RECT.right-2
        elif self.direction == Settings.UP and self.rect.top <= 0:
            turn = True
            self.rect.top = 2
        elif self.direction == Settings.DOWN and self.rect.bottom >= Settings.SCREEN_RECT.bottom-1:
            turn = True
            self.rect.bottom = Settings.SCREEN_RECT.bottom-2
        if turn:
            self.random_turn()

    def update(self):
        # 控制射击频率
        self.shoot_update_counter += 1
        if self.shoot_update_counter >= self.shoot_update_interval:
            self.random_shot()
            self.shoot_update_counter = 0
            # 动态调整射击间隔，增加不可预测性
            self.shoot_update_interval = random.randint(20, 50)
        
        # 控制AI更新频率
        self.ai_update_counter += 1
        if self.ai_update_counter >= self.ai_update_interval:
            if self.terminal <= 0:
                self.random_turn()
                # 动态调整AI更新间隔
                self.ai_update_interval = random.randint(30, 60)
            self.ai_update_counter = 0
        
        # 正常移动
        super().update()
        # 减少terminal值，但不是每帧都更新
        if self.ai_update_counter % 2 == 0:  # 每两帧更新一次terminal
            self.terminal -= self.speed


class Wall(BaseSprite):

    def __init__(self, image_name, screen):
        super().__init__(image_name, screen)
        self.type = None
        self.life = 2

    def update(self):
        pass

    def boom(self):
        # 使用声音缓存
        if Settings.BOOM_MUSIC not in SOUND_CACHE:
            SOUND_CACHE[Settings.BOOM_MUSIC] = pygame.mixer.Sound(Settings.BOOM_MUSIC)
        SOUND_CACHE[Settings.BOOM_MUSIC].play()
        
        # 使用图像缓存播放爆炸动画
        for boom in Settings.BOOMS:
            if boom not in IMAGE_CACHE:
                IMAGE_CACHE[boom] = pygame.image.load(boom)
            self.image = IMAGE_CACHE[boom]
            # 只更新精灵组，不直接更新显示，由主循环统一管理更新
            # pygame.display.update(self.rect)
            
        super().kill()

    def kill(self):
        self.life -= 1
        if not self.life:
            # 直接调用boom方法，避免使用线程导致的内存泄漏
            self.boom()


# Compatibility: provide a PlayerTank alias/class expected by legacy code
class PlayerTank(TankSprite):
    """
    PlayerTank is a thin compatibility subclass used by older codepaths
    (e.g. `tank_war.py`). It behaves like a generic TankSprite and accepts
    the same constructor signature (image_name, screen).
    """
    def __init__(self, image_name, screen):
        super().__init__(image_name, screen)
        # default to enemy-like behavior unless caller customizes
        self.type = Settings.ENEMY
