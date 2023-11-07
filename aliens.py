

import random
import os

import pygame as pg

# see if we can load more than standard BMP
if not pg.image.get_extended():
    raise SystemExit("Sorry, extended image module required")

# game constants
MAX_SHOTS = 2  # most player bullets onscreen
ALIEN_ODDS = 22  # chances a new alien appears
BOMB_ODDS = 60  # chances a new bomb will drop
ALIEN_RELOAD = 12  # frames between new aliens
SHOT_RELOAD = 12
SCREENRECT = pg.Rect(0, 0, 640, 480)
SCORE = 0
INVINCIBILITY_DURATION = 10000  # 10 seconds
INVINCIBLE = False
INVINCIBILITY_END_TICK = 0

main_dir = os.path.split(os.path.abspath(__file__))[0]

def load_image(file):
    """Loads an image and prepares it for rendering."""
    file_path = os.path.join(main_dir, "data", file)
    """
    画像を読み込んでゲーム用に準備するメソッド。
    ファイルのパスを受け取り、Surfaceオブジェクトを返す。
    """
    file = os.path.join(main_dir, "data", file)

    try:
        surface = pg.image.load(file_path)
    except pg.error:
        raise SystemExit(f'Could not load image "{file_path}" {pg.get_error()}')
    return surface.convert()

def load_sound(file):
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
    facing = 1  # Add this line. Default facing direction is right (1).

    def __init__(self):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
        self.rect = self.image.get_rect(midbottom=SCREENRECT.midbottom)
        self.reloading = 0
        self.invincible = False
        self.invincibility_end_tick = 0
        self.invincible = False  # 追加された行
        self.invincibility_end_tick = 0  # 追加された行

    def move(self, direction):
        if direction: 
            self.rect.move_ip(direction*self.speed, 0)
            self.rect = self.rect.clamp(SCREENRECT)
            if direction < 0:
                self.image = self.images[1]
                self.facing = -1  # Update the facing attribute
            else:
                self.image = self.images[0]
                self.facing = 1  # Update the facing attribute

    def activate_invincibility(self, duration):
        self.invincible = True
        self.invincibility_end_tick = pg.time.get_ticks() + duration
   
    
    def gunpos(self):
        pos = self.facing < 0 and self.rect.topright or self.rect.topleft
        return pos[0] + self.gun_offset+66 , pos[1] - 1

    def update(self):
        self.reloading = max(0, self.reloading-1)

        if self.invincible and pg.time.get_ticks() > self.invincibility_end_tick:
            self.invincible = False
    

class Alien(pg.sprite.Sprite):
    speed = 13
    animcycle = 12
    images = []

    def __init__(self):
        pg.sprite.Sprite.__init__(self, self.containers)
        self.image = self.images[0]
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
        self.rect = actor.rect.centerx, actor.rect.centery
        self.life = self.defaultlife

    def update(self):
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

def main(winstyle=0):
    # Initialize pygame
    pg.init()
    # pygameの初期化
    if pg.get_sdl_version()[0] == 2:
        pg.mixer.pre_init(44100, 32, 2, 1024)

    pg.init()


    # Set the display mode
    winstyle = 0
    bestdepth = pg.display.mode_ok(SCREENRECT.size, winstyle, 32)
    screen = pg.display.set_mode(SCREENRECT.size, winstyle, bestdepth)
    img = load_image("player1.gif")
    Player.images = [img, pg.transform.flip(img, 1, 0)]
    img = load_image('explosion1.gif')
    Explosion.images = [img, pg.transform.flip(img, 1, 1)]
    Alien.images = [load_image('alien1.gif'), load_image('alien2.gif'), load_image('alien3.gif')]
    Bomb.images = [load_image('bomb.gif')]
    Shot.images = [load_image('shot.gif')]

    # Decorate the game window
    icon = pg.transform.scale(Alien.images[0], (32, 32))
    pg.display.set_icon(icon)
    pg.display.set_caption('Pygame Aliens')
    pg.mouse.set_visible(0)


    bgdtile = load_image("background.gif")
    background = pg.Surface(SCREENRECT.size)
    for x in range(0, SCREENRECT.width, bgdtile.get_width()):
        background.blit(bgdtile, (x, 0))
    screen.blit(background, (0, 0))
    pg.display.flip()

    # Initialize game groups
    aliens = pg.sprite.Group()
    shots = pg.sprite.Group()
    bombs = pg.sprite.Group()
    all = pg.sprite.RenderUpdates()
    lastalien = pg.sprite.GroupSingle()

    Player.containers = all
    Alien.containers = aliens, all, lastalien
    Shot.containers = shots, all
    Bomb.containers = bombs, all
    Explosion.containers = all
    Score.containers = all


    global SCORE

    alienreload = ALIEN_RELOAD
    kills = 0
    clock = pg.time.Clock()

    pg.mouse.set_visible(1)

    # Instantiate our player
    player = Player()
    Alien()  # Note: this 'wakes' the alien group
    if pg.font:
        all.add(Score())

    while player.alive():

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

        # Clear/erase the last drawn sprites
        all.clear(screen, background)

        # Update all the sprites
        all.update()

        # Handle player input

    global SCORE
    player = Player()
    Alien()  # Note: this 'wakes' the alien group
    if pg.font:
        all.add(Score())

    while player.alive():

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

        # Clear/erase the last drawn sprites
        all.clear(screen, background)

        # Update all the sprites
        all.update()

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

        if not player.invincible:  # Add this condition
            for alien in pg.sprite.spritecollide(player, aliens, 1):
                Bomb(alien)
                Explosion(alien)
                Explosion(player)
                SCORE = SCORE + 1
                player.kill()

        for alien in pg.sprite.groupcollide(shots, aliens, 1, 1).keys():
            Bomb(alien)
            Explosion(alien)
            SCORE = SCORE + 1

        for alien in pg.sprite.spritecollide(player, aliens, 1):
            if pg.mixer:
                boom_sound.play()

            Explosion(alien)
            SCORE = SCORE + 1

        if not player.invincible:  # Add this condition
            for bomb in pg.sprite.spritecollide(player, bombs, 1):
                Explosion(player)
                Explosion(bomb)
                player.kill()

        for alien in pg.sprite.groupcollide(shots, aliens, 1, 1).keys():
            Bomb(alien)
            Explosion(alien)
            SCORE = SCORE + 1

        # Draw the scene
        dirty = all.draw(screen)
        pg.display.update(dirty)


        if not player.invincible:  # Add this condition
            for bomb in pg.sprite.spritecollide(player, bombs, 1):
                Explosion(player)
                Explosion(bomb)
                player.kill()

        for alien in pg.sprite.groupcollide(shots, aliens, 1, 1).keys():
            Bomb(alien)
            Explosion(alien)
            SCORE = SCORE + 1

        # Draw the scene
        dirty = all.draw(screen)
        pg.display.update(dirty)
        clock.tick(40)

    if pg.mixer:
        pg.mixer.music.fadeout(1000)
    pg.time.wait(1000)
    pg.quit()

if __name__ == "__main__":
    main()
    pg.quit()
