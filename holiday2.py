import os
import random
import pygame as pg

# ゲーム定数
MAX_SHOTS = 10  # 最大弾数
ALIEN_ODDS = 22  # エイリアン出現確率
BOMB_ODDS = 60  # ボム落下確率
ALIEN_RELOAD = 12  # エイリアンリロードフレーム数
SHOT_RELOAD = 12
SCREENRECT = pg.Rect(0, 0, 640, 480)
SCORE = 0
INVINCIBILITY_DURATION = 10000  # 無敵モード持続時間（10秒）
main_dir = os.path.split(os.path.abspath(__file__))[0]

# 画像と音声の読み込み用関数
def load_image(file):
    """画像を読み込んで準備する"""
    file_path = os.path.join(main_dir, "data", file)
    try:
        surface = pg.image.load(file_path)
    except pg.error:
        raise SystemExit(f'Could not load image "{file}" {pg.get_error()}')
    return surface.convert()


def load_sound(file):
    """音声を読み込む。pygameミキサーが無効な場合はNoneを返す"""
    if not pg.mixer:
        return None
    file_path = os.path.join(main_dir, "data", file)
    try:
        sound = pg.mixer.Sound(file_path)
        return sound
    except pg.error:
        print(f"Warning, unable to load, {file_path}")
    return None


class Player(pg.sprite.Sprite):
    speed = 10
    bounce = 24
    gun_offset = -11
    images = []
    facing = 1

    def __init__(self):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(midbottom=SCREENRECT.midbottom)
        self.reloading = 0
        self.origtop = self.rect.top
        self.facing = 1
        self.invincible = False
        self.invincibility_end_tick = 0

    def move(self, direction):
        if direction: 
            self.rect.move_ip(direction*self.speed, 0)
            self.rect = self.rect.clamp(SCREENRECT)
            if direction < 0:
                self.image = self.images[1]
            else:
                self.image = self.images[0]

    def gunpos(self):
        pos = self.rect.topleft
        return pos[0] + self.gun_offset, pos[1]
    
    def activate_invincibility(self, duration):
        self.invincible = True
        self.invincibility_end_tick = pg.time.get_ticks() + duration
        if self.invincible:
            if pg.time.get_ticks() > self.invincibility_end_tick:
                self.invincible = False
                self.image.set_alpha(255)  # 透明度を元に戻す
            else:
                self.image.set_alpha((pg.time.get_ticks() // 100) % 2 * 255)  # 点滅させる

    def gunpos(self):
        pos = self.facing < 0 and self.rect.topright or self.rect.topleft
        return pos[0] + self.gun_offset+66 , pos[1] - 1
    
    def update(self):
        self.reloading = max(0, self.reloading - 1)
        

class BigShot(pg.sprite.Sprite):
    """大きな弾を表すクラス。"""

    speed = -8  # 大きな弾の速度
    images = []

    def __init__(self, pos):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(midbottom=pos)

    def update(self):
        """大きな弾のアップデート。毎フレーム呼び出されます。"""
        self.reloading = max(0, self.reloading-1)
        self.rect.move_ip(0, self.speed)
        if self.invincible and pg.time.get_ticks() > self.invincibility_end_tick:
            self.invincible = False
        if self.rect.top <= 0:
            self.kill()

        
class Alien(pg.sprite.Sprite):
    speed = 13
    animcycle = 12
    images = []

    def __init__(self):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        #self.image = pg.transform.rotozoom(pg.image.load("ex05/data/alien1.gif"), 0.0, 1.0)
        self.rect = self.image.get_rect()
        self.rect.left = SCREENRECT.left
        self.facing = random.choice((1,-1)) * Alien.speed
        self.frame = 0

    def update(self):
        self.rect.move_ip(self.facing, 0)
        if not SCREENRECT.contains(self.rect):
            self.facing = -self.facing
            self.rect.top = self.rect.bottom + 1
            self.rect = self.rect.clamp(SCREENRECT)
        self.frame = self.frame + 1
        self.image = self.images[self.frame//self.animcycle%3]


class Explosion(pg.sprite.Sprite):
    defaultlife = 12
    animcycle = 3
    images = []

    def __init__(self, actor):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        #self.image = pg.transform.rotozoom(pg.image.load("ex05/data/explosion1.gif"), 0.0, 1.0)
        self.rect = self.image.get_rect(center=actor.rect.center)
        self.rect = actor.rect.centerx, actor.rect.centery
        self.life = self.defaultlife

    def update(self):
        """called every time around the game loop.

        Show the explosion surface for 'defaultlife'.
        Every game tick(update), we decrease the 'life'.

        
        Also we animate the explosion.
        """
        self.life = self.life - 1
        self.image = self.images[self.life//self.animcycle%2]
        if self.life <= 0:
            self.kill()


class Shot(pg.sprite.Sprite):
    speed = -9 
    images = []

    def __init__(self, pos):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(midbottom=pos)

    def update(self):
        self.rect.move_ip(0, self.speed)
        if self.rect.top <= 0 or self.rect.bottom >= SCREENRECT.height:
            self.kill()


class Bomb(pg.sprite.Sprite):
    speed = 9
    images = []

    def __init__(self, alien):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(midtop=alien.rect.midbottom)

    def update(self):
        self.rect.move_ip(0, self.speed)
        if self.rect.bottom >= SCREENRECT.height:
            self.kill()


class Score(pg.sprite.Sprite):
    def __init__(self):
        pg.sprite.Sprite.__init__(self)
        self.font = pg.font.Font(None, 20)
        self.font.set_italic(1)
        self.color = pg.Color('white')
        self.lastscore = -1
        self.update()
        self.rect = self.image.get_rect().move(10, 450)


    def update(self):
        if SCORE != self.lastscore:
            self.lastscore = SCORE
            msg = "Score: %d" % SCORE
            self.image = self.font.render(msg, 0, self.color)


class Firework(pg.sprite.Sprite):
    speed = -10
    images = []

    def __init__(self, pos):
        pg.sprite.Sprite.__init__(self, self.containers)
        if len(self.images) > 0:
            self.image = self.images[0]
             #self.image = pg.transform.rotozoom(pg.image.load("ex05/data/hanabi.png"), 0.0, 1.0)
            self.rect = self.image.get_rect(midbottom=pos)

    

    def update(self):
        self.rect.move_ip(0, self.speed)
        if self.rect.bottom <= 0:
            Explosion(self)
            self.kill()


def main(winstyle=0):
    # Initialize pygame
    pg.init()
    # Set the display mode
    bestdepth = pg.display.mode_ok(SCREENRECT.size, winstyle, 32)
    screen = pg.display.set_mode(SCREENRECT.size, winstyle, bestdepth)

    # Load images, assign to sprite classes
    img = load_image('player1.gif')
    Player.images = [img, pg.transform.flip(img, 1, 0)]
    img = load_image('explosion1.gif')
    Explosion.images = [img, pg.transform.flip(img, 1, 1)]
    Alien.images = [load_image('alien1.gif'), load_image('alien2.gif'), load_image('alien3.gif')]
    Bomb.images = [load_image('bomb.gif')]
    Shot.images = [load_image('shot.gif')]

    # Decorate the game window
    icon = pg.transform.scale(Alien.images[0], (32, 32))
    pg.display.set_icon(icon)
    pg.display.set_caption('holiday2')
    pg.mouse.set_visible(0)

    # Create the background
    bgdtile = load_image('background.gif')
    background = pg.Surface(SCREENRECT.size)
    for x in range(0, SCREENRECT.width, bgdtile.get_width()):
        background.blit(bgdtile, (x, 0))
    screen.blit(background, (0, 0))
    pg.display.flip()

    # Initialize game groups
    # load the sound effects
    boom_sound = load_sound("boom.wav")
    shoot_sound = load_sound("car_door.wav")
    if pg.mixer:
        music = os.path.join(main_dir, "data", "8-bit_Aggressive1.mp3")
        pg.mixer.music.load(music)
        pg.mixer.music.play(-1)

    # Initialize Game Groups
    aliens = pg.sprite.Group()
    shots = pg.sprite.Group()
    bombs = pg.sprite.Group()
    all = pg.sprite.RenderUpdates()
    lastalien = pg.sprite.GroupSingle()
    fireworks = pg.sprite.Group()

    # Assign default groups to each sprite class
    Player.containers = all
    Alien.containers = aliens, all, lastalien
    Shot.containers = shots, all
    Bomb.containers = bombs, all
    Explosion.containers = all
    Score.containers = all
    Firework.containers = fireworks, all

    # 画面の設定
    fullscreen = False
    winstyle = 0  # |FULLSCREEN
    bestdepth = pg.display.mode_ok(SCREENRECT.size, winstyle, 32)
    screen = pg.display.set_mode(SCREENRECT.size, winstyle, bestdepth)


    # create the background, tile the bgd image
    bgdtile = load_image("data/background.gif")
    background = pg.Surface(SCREENRECT.size)
    for x in range(0, SCREENRECT.width, bgdtile.get_width()):
        background.blit(bgdtile, (x, 0))
    screen.blit(background, (0, 0))
    pg.display.flip()

    # 画像の読み込みとスプライトクラスへの割り当て
    img = load_image("data/player1.gif")
    Player.images = [img, pg.transform.flip(img, 1, 0)]
    img = load_image("data/explosion1.gif")
    Explosion.images = [img, pg.transform.flip(img, 1, 1)]
    Alien.images = [load_image(im) for im in ("data/alien1.gif", "data/alien2.gif", "data/alien3.gif")]
    Bomb.images = [load_image("data/bomb.gif")]
    Shot.images = [load_image("data/shot.gif")]
    Firework.images = [load_image("data/hanabi.png")]

    # Create some starting values
    global SCORE
    alienreload = ALIEN_RELOAD
    clock = pg.time.Clock()

    # Unhide the mouse
    pg.mouse.set_visible(1)

    # Instantiate our player
    player = Player()
    Alien()  # Note: this 'wakes' the alien group
    if pg.font:
        all.add(Score())

    while player.alive():
        # Detect collisions
        if not player.invincible:
            for alien in pg.sprite.spritecollide(player, aliens, 1):
                Explosion(player)
                player.kill()
                break  # プレイヤーが死亡したらループを抜ける

            for bomb in pg.sprite.spritecollide(player, bombs, 1):
                Explosion(player)
                player.kill()
                break  # プレイヤーが死亡したらループを抜ける

        # Get input
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                return
            elif event.type == pg.KEYDOWN and event.key == pg.K_f:
                if not screen.get_flags() & pg.FULLSCREEN:
                    pg.display.set_mode(SCREENRECT.size, pg.FULLSCREEN)
                else:
                    pg.display.set_mode(SCREENRECT.size)
       
        keystate = pg.key.get_pressed()
        if keystate[pg.K_m]:
            player.activate_invincibility(INVINCIBILITY_DURATION)

        # 無敵状態ではない場合のみ衝突判定を行う
        if not player.invincible:
            for alien in pg.sprite.spritecollide(player, aliens, 1):
                Explosion(player)
                player.kill()
                break

            for bomb in pg.sprite.spritecollide(player, bombs, 1):
                Explosion(player)
                player.kill()
                break
        
        if keystate[pg.K_SPACE]:
            # shots(player, 0) を shots.add() に変更
            new_shot = Shot(player.gunpos())
            shots.add(new_shot)

        if keystate[pg.K_TAB]:
            # shots(player, 0) を shots.add() に変更
            new_shot = Shot(player.gunpos())
            shots.add(new_shot)

            # shots(player, 45) を shots.add() に変更
            new_shot = Shot(player.gunpos())
            new_shot.rect.x -= 15  # 左に11ピクセル移動
            new_shot.rect.y -= 1  # 上に1ピクセル移動
            shots.add(new_shot)

            # shots(player, -45) を shots.add() に変更
            new_shot = Shot(player.gunpos())
            new_shot.rect.x += 15  # 右に11ピクセル移動
            new_shot.rect.y -= 1  # 上に1ピクセル移動
            shots.add(new_shot)


        keystate = pg.key.get_pressed()
        # Handle player input
        # Handle player input
        direction = keystate[pg.K_RIGHT] - keystate[pg.K_LEFT]
        player.move(direction)
        firing = keystate[pg.K_SPACE]
        if not player.reloading and firing and len(shots) < MAX_SHOTS:
            Shot(player.gunpos())
            player.reloading = SHOT_RELOAD


        if keystate[pg.K_m]:  # 無敵モードを有効にするキーとして "m" を使用
            player.activate_invincibility(INVINCIBILITY_DURATION)
                  
        
        
    # Create new alien
        if alienreload:
            alienreload = alienreload - 1
        elif not int(random.random() * ALIEN_ODDS):
            Alien()
            alienreload = ALIEN_RELOAD

    # Drop bombs
        if lastalien and not int(random.random() * BOMB_ODDS):
            Bomb(lastalien.sprite)


        # Create fireworks (追加)
        #if not int(random.random() * 200):
        if not int(random.random() * ALIEN_ODDS):
            Firework((random.randint(0, SCREENRECT.width), SCREENRECT.bottom))
    
        # Detect collisions between aliens and players.
        for alien in pg.sprite.spritecollide(player, aliens, 1):
            # if pg.mixer:
            #     boom_sound.play()
        # Detect collisions
            if not player.invincible:  # Add this condition
                for alien in pg.sprite.spritecollide(player, aliens, 1):
                    Explosion(player)
                    player.kill()
                
                for bomb in pg.sprite.spritecollide(player, bombs, 1):
                    Explosion(player)
                    player.kill()

        for alien in pg.sprite.groupcollide(shots, aliens, 1, 1).keys():
            Bomb(alien)
            Explosion(alien)
            SCORE = SCORE + 1


        # See if shots hit the aliens.
        for alien in pg.sprite.groupcollide(aliens, shots, 1, 1).keys():
            # if pg.mixer:
            #     boom_sound.play()
            Explosion(alien)
            SCORE = SCORE + 1

        # See if alien boms hit the player.
        for bomb in pg.sprite.spritecollide(player, bombs, 1):
            # if pg.mixer:
            #     boom_sound.play()
            Explosion(player)
            Explosion(bomb)
            player.kill()

        # See if fireworks hit the aliens (追加)
        for alien in pg.sprite.groupcollide(aliens, fireworks, 1, 1).keys():
            # if pg.mixer:
            #     boom_sound.play()
            Explosion(alien)
            #Explosion(fireworks)
            SCORE = SCORE + 1

        # draw the scene
        if not player.invincible:
            for alien in pg.sprite.spritecollide(player, aliens, 1):
                Explosion(player)
                player.kill()
                break

            for bomb in pg.sprite.spritecollide(player, bombs, 1):
                Explosion(player)
                player.kill()
                break
        for alien in pg.sprite.groupcollide(shots, aliens, 1, 1).keys():
            Bomb(alien)
            Explosion(alien)
            SCORE = SCORE + 1
 
        # Draw the scene
        all.update()
        all.clear(screen, background)
        dirty = all.draw(screen)
        pg.display.update(dirty)
  
        # Cap the frame rate
        clock.tick(40)

    
    pg.quit()


if __name__ == "__main__":
    main()