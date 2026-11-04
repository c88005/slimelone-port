import json
import pygame
import random
import math


class Slimelone:
    def __init__(self, scale=1, texturePath = "images/", soundPath = "sounds/"):
        self.width = 1280#*scale
        self.height = 720#*scale
        self.scale = scale
        self.clickCD = False
        self.attackCD = False

        self.running = True
        self.texturePath = texturePath
        self.soundPath = soundPath
        self.textures = {}

        self.seed = random.randint(-2147483647,2147483647)
        self.random = random.Random(self.seed)

        self.nextBrightnessChange = 20000
        self.lastBrightnessChange = pygame.time.get_ticks()
        self.brightness = 0
        self.brightnessUpdated = False

        self.night = 0
        self.nightStage = 0
        self.nightSecretStage = 0
        self.daysPassed = 0
        self.musicPlaying = False

        self.mobLastSpawn = pygame.time.get_ticks()
        self.ver = "0.01"
        self.map = {
                    "Seed":self.seed,
                    "ObjectAddQueue":[],
                    "BackgroundName":"bg",
                    "Objects":[],
                    "StaticObjects":[],
                    "Entities":[],
                    "Bushes":0
                    }
        self.buttons = [FenceButton(-548, 321), ClubButton(-374, 320)]

        self.screen = pygame.display.set_mode((self.width, self.height))
        self.clock = pygame.time.Clock()

        self.update()

    def loadSequence(self):
        pygame.display.set_caption("Slimelone (" + self.ver + ")")
        self.textures = self.loadTextures()
        pygame.mixer.init()

    def mapCreate(self):
        self.map["Entities"].append(Player(0, 0))
        self.map["Objects"].append(Object(self.random.randint(-300,300),self.random.randint(-300,300),"rock", (0,0)))
        self.map["StaticObjects"].append(Pond(522, -290))
        for _ in range(5):
            self.map["StaticObjects"].append(Bush(random.randint(-510,510), random.randint(-320,320)))

    def update(self):
        self.loadSequence()
        self.mapCreate()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            mouse = pygame.mouse
            buttons = mouse.get_pressed()
            mx, my = mouse.get_pos()

            if pygame.time.get_ticks() - self.lastBrightnessChange >= self.nextBrightnessChange:
                if self.night == 0:
                    if self.nightStage + 1 >= 3:
                        self.night = 1
                    self.nightStage += 1
                    self.changeBrightness(-30)
                    self.lastBrightnessChange = pygame.time.get_ticks()
                elif self.night == 1:
                    if self.nightStage - 1 <= 0:
                        self.night = 0
                        self.daysPassed += 1
                    self.nightStage -= 1
                    self.changeBrightness(30)
                    self.lastBrightnessChange = pygame.time.get_ticks()
            if self.nightStage >= 2:
                self.playMusic("night.mp3", 1.5)
            else:self.stopMusic()
            if self.nightStage >= 3:
                if pygame.time.get_ticks() - self.mobLastSpawn > self.nextBrightnessChange/2-15:
                    self.mobLastSpawn = pygame.time.get_ticks()
                    for _ in range(self.random.randint(1, int(self.daysPassed*1.5+1))):
                        self.map["Entities"].append(Mob(self.random.randint(int(-self.width*1.25/2), int(-self.width*1.25/2)), self.random.randint(int(-self.height*1.25/2), int(-self.height*1.25/2))))
            self.drawImage(self.map["BackgroundName"], 0, 0)
            for staticObject in self.map["StaticObjects"]:
                staticObject.update(self.map)
                self.drawImage(staticObject.textureName, staticObject.x, staticObject.y)

                texture = self.textures[staticObject.textureName]
                rect = texture.get_rect()
                if buttons[0] and not self.clickCD:
                    if self.checkHover(mx, my, staticObject.x, staticObject.y, rect[2], rect[3], False):
                        if staticObject.removeOnClick: self.map["StaticObjects"].remove(staticObject)
                        staticObject.clicked(self.map, self.random, self.soundPath)

            for nonStaticObject in self.map["Objects"]:
                nonStaticObject.update(self.map)
                self.drawImage(nonStaticObject.textureName, nonStaticObject.x, nonStaticObject.y)

                texture = self.textures[nonStaticObject.textureName]
                rect = texture.get_rect()
                if buttons[0] and not self.clickCD:
                    if self.checkHover(mx, my, nonStaticObject.x, nonStaticObject.y, rect[2], rect[3], False):
                        if nonStaticObject.removeOnClick: self.map["Objects"].remove(nonStaticObject)
                        nonStaticObject.clicked(self.map, self.random, self.soundPath)

            self.drawImage("darkness", 0, 0)

            for entity in self.map["Entities"]:
                entity.update(self.map, self.textures)
                self.drawImage(entity.textureName, entity.x, entity.y)
                if entity.hasBat:
                    newBat = self.rotateAtCenter(self.textures["bat"], entity.batAngle)
                    self.drawSurface(newBat, entity.x, entity.y)
                    entity.batRect = newBat.get_rect()
                if entity.dead:
                    self.map["Entities"].remove(entity)

                if isinstance(entity, Player):
                    if (entity.playerDead or entity.health <= 0):
                        self.reset()
                    if buttons[2]:
                        entity.tX = mx - self.width / 2
                        entity.tY = self.height / 2 - my
                    if self.nightStage >= 2:
                        self.drawImage("light", entity.x, entity.y)

                    if buttons[1] and entity.hasBat:
                        hit = entity.checkClubHit(Mob, "Entities", self.map, self.textures)
                        entity.batAngle = math.sin(pygame.time.get_ticks()/100)*50
                        if hit != None:
                            if hit[0]:
                                entity.attack(hit[1])

            self.drawImage("inv", -3, 491)
            self.drawImage("bushesCollected", -467, 265)
            self.drawText(str(self.map["Bushes"]), -300, 272)
            for button in self.buttons:
                self.drawImage(button.textureName, button.x, button.y)

                texture = self.textures[button.textureName]
                rect = texture.get_rect()
                if buttons[0] and not self.clickCD:
                    if self.checkHover(mx, my, button.x, button.y, rect[2], rect[3], False):
                        if button.removeOnClick: self.map["StaticObjects"].remove(button)
                        button.clicked(self.map, self.random, self.soundPath)

            if not self.brightnessUpdated:
                self.brightnessUpdated = True
                self.updateBrightness()

            for futureObject in self.map["ObjectAddQueue"]:
                if pygame.time.get_ticks() - futureObject[1] >= futureObject[2]:
                    self.map["ObjectAddQueue"].remove(futureObject)
                    self.map[futureObject[3]].append(futureObject[0])

            self.drawText(str(self.clock.get_fps()), -300, 222)
            self.clickCD = buttons[0]
            self.attackCD = buttons[1]
            pygame.display.flip()
            self.clock.tick(60)

    def rotateAtCenter(self, image, angle):
        rotated_image = pygame.transform.rotate(image, angle)
        return rotated_image

    def reset(self):
        self.seed = random.randint(-2147483647, 2147483647)
        self.random = random.Random(self.seed)

        self.nextBrightnessChange = 20000
        self.lastBrightnessChange = pygame.time.get_ticks()
        self.brightness = 0
        self.brightnessUpdated = False

        self.night = 0
        self.nightStage = 0
        self.nightSecretStage = 0
        self.daysPassed = 0
        self.musicPlaying = False

        self.mobLastSpawn = pygame.time.get_ticks()
        self.map = {
            "Seed": self.seed,
            "ObjectAddQueue": [],
            "BackgroundName": "bg",
            "Objects": [],
            "StaticObjects": [],
            "Entities": [],
            "Bushes": 0
        }
        self.mapCreate()

    def saveMap(self, name):
        with open(name+".json", "w") as saveFile:
            saveFile.write(json.dumps(self.map))
            saveFile.close()

    def loadMap(self, name):
        with open(name+".json", "r") as saveFile:
            self.map = json.load(saveFile)
            saveFile.close()

    def changeBrightness(self, value):
        self.brightness -= value
        if self.brightness > 100: self.brightness = 100
        elif self.brightness < 0: self.brightness = 0
        self.brightnessUpdated = False

    def updateBrightness(self):
        newBrightness = self.brightness/100 * 255
        if newBrightness > 255: newBrightness = 255
        elif newBrightness < 0: newBrightness = 0
        self.textures["darkness"].set_alpha(newBrightness)

    def drawImage(self, imageName, x, y):
        texture = self.textures[imageName]
        rect = texture.get_rect()
        self.screen.blit(texture, (self.width/2+(x*self.scale)-rect[2]/2, self.height/2-(y*self.scale)-rect[3]/2))

    def drawSurface(self, surface, x, y):
        rect = surface.get_rect()
        self.screen.blit(surface, (self.width/2+(x*self.scale)-rect[2]/2, self.height/2-(y*self.scale)-rect[3]/2))

    def drawText(self, value, x, y):
        pygame.font.init()
        my_font = pygame.font.SysFont("sans", int(30*self.scale))
        text_surface = my_font.render(value, True, "#000000")
        rect = text_surface.get_rect()
        self.screen.blit(text_surface, (self.width/2+(x*self.scale), self.height/2-(y*self.scale)-rect[3]/4))

    def checkHover(self, mx, my, x, y, w, h, drawBox=False):
        x = self.width/2+(x*self.scale)-w/2
        y = self.height/2-(y*self.scale)-h/2
        if drawBox:
            pygame.draw.rect(self.screen, "#FFFFFF", (x, y, w, h))
            pygame.draw.circle(self.screen, "#FF0000", (x, y), 5)
            pygame.draw.circle(self.screen, "#FF0000", (x+w, y), 5)
            pygame.draw.circle(self.screen, "#FF0000", (x, y+h), 5)
            pygame.draw.circle(self.screen, "#FF0000", (x+w, y+h), 5)
            pygame.draw.circle(self.screen, "#0000FF", (mx, my), 5)

        if x <= mx <= x+w and y <= my <= y+h:
            return True
        return False

    def playSound(self, soundName, volume):
        sound = pygame.mixer.Sound(self.soundPath + soundName)
        sound.set_volume(volume)
        sound.play()
        return sound

    def playMusic(self, musicName, volume):
        if not self.musicPlaying:
            self.musicPlaying = True
            pygame.mixer.music.load(self.soundPath + musicName)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play()

    def stopMusic(self):
        self.musicPlaying = False
        pygame.mixer.music.fadeout(1000)

    def textureLoader(self, texture, sizeX=1.0, sizeY=1.0, transparency=0.0):
        newTexture = pygame.image.load(texture)
        rect = newTexture.get_rect()
        surface = pygame.transform.scale(newTexture, [rect[2]*sizeX*self.scale, rect[3]*sizeY*self.scale]).convert_alpha()
        surface.set_alpha(int(255-transparency*255))
        return surface

    def loadTextures(self):
        return {
            "darkness":pygame.Surface((self.width, self.height)),
            "bat":self.textureLoader(self.texturePath+"bat.png", 0.15, 0.15),
            "batAttack":self.textureLoader(self.texturePath+"batAttack.png", 0.3, 0.3),
            "bg":self.textureLoader(self.texturePath+"bg.png", 1.5, 1.5),
            "bush":self.textureLoader(self.texturePath+"bush.png", 0.15, 0.15),
            "bushesCollected":self.textureLoader(self.texturePath+"bushesCollected.png", 0.45, 0.45),
            "craftBat":self.textureLoader(self.texturePath+"craftBat.png", 0.3, 0.3),
            "craftFence":self.textureLoader(self.texturePath+"craftFence.png", 0.3, 0.3),
            "cursor":self.textureLoader(self.texturePath+"cursor.png", 0.1, 0.1),
            "fence":self.textureLoader(self.texturePath+"fence.png", 0.15, 0.15),
            "fence0":self.textureLoader(self.texturePath+"fence0.png", 0.15, 0.15),
            "fence1":self.textureLoader(self.texturePath+"fence1.png", 0.15, 0.15),
            "inv":self.textureLoader(self.texturePath+"inv.png", 1.2, 1.2),
            "light":self.textureLoader(self.texturePath+"light.png", 0.3, 0.3, 0.6),
            "pond0":self.textureLoader(self.texturePath+"pond0.png", 0.35, 0.35),
            "pond1":self.textureLoader(self.texturePath+"pond1.png", 0.35, 0.35),
            "rock":self.textureLoader(self.texturePath+"rock.png", 0.3, 0.3),
            "slime":self.textureLoader(self.texturePath+"slime.png", 0.12, 0.12),
            "slime0":self.textureLoader(self.texturePath+"slime0.png", 0.12, 0.12),
            "slime1":self.textureLoader(self.texturePath+"slime1.png", 0.2, 0.2),
        }

class StaticObject:
    def __init__(self, x, y, textureName):
        self.x = x
        self.y = y
        self.textureName = textureName
        self.removeOnClick = False

    def update(self, map):
        pass

    def playSound(self, soundName, volume, soundPath):
        sound = pygame.mixer.Sound(soundPath + soundName)
        sound.set_volume(volume)
        sound.play()
        return sound

    def clicked(self, map, random, soundPath="sounds/"):
        pass

    def AABBCollision(self, a_x, a_y, a_w, a_h, b_x, b_y, b_w, b_h):
        return (a_x < b_x + b_w and
                a_x + a_w > b_x and
                a_y < b_y + b_h and
                a_y + a_h > b_y)

class FenceButton(StaticObject):
    def __init__(self, x, y):
        super().__init__(x, y, "craftFence")

    def clicked(self, map, random, soundPath="sounds/"):
        if map["Bushes"] >= 2:
            map["Bushes"] -= 2
            for entity in map["Entities"]:
                if isinstance(entity, Player):
                    map["Objects"].append(Fence(entity.x, entity.y))

class ClubButton(StaticObject):
    def __init__(self, x, y):
        super().__init__(x, y, "craftBat")

    def clicked(self, map, random, soundPath="sounds/"):
        if map["Bushes"] >= 8:
            for entity in map["Entities"]:
                if isinstance(entity, Player):
                    if not entity.hasBat:
                        map["Bushes"] -= 8
                        entity.hasBat = True

class Object(StaticObject):
    def __init__(self, x, y, textureName, hitbox):
        super().__init__(x, y, textureName)
        self.hitbox = hitbox

class Fence(Object):
    def __init__(self, x, y):
        super().__init__(x, y, "fence", (0,0))
        self.texture0 = "fence0"
        self.texture1 = "fence1"
        self.health = 3

    def update(self, map):
        if self.health > 0:
            if self.health == 3: self.textureName = "fence"
            if self.health == 2: self.textureName = "fence0"
            if self.health == 1: self.textureName = "fence1"
        else:
            map["Objects"].remove(self)

class Bush(StaticObject):
    def __init__(self, x, y):
        super().__init__(x, y, "bush")
        self.removeOnClick = True

    def clicked(self, map, random, soundPath="sounds/"):
        map["ObjectAddQueue"].append([Bush(random.randint(-510,510), random.randint(-320,320)), pygame.time.get_ticks(), 2000, "StaticObjects"])
        self.playSound("bush.mp3", 0.5, soundPath)
        map["Bushes"] += 1

class Entity(Object):
    def __init__(self, x, y, textureName, hitbox):
        super().__init__(x, y, textureName, hitbox)
        self.health = 1
        self.moveSpeed = 5
        self.hasBat = False
        self.batAngle = 0
        self.aiEnabled = False
        self.targetClass = None
        self.target = None
        self.moving = False
        self.lastAttacked = 0
        self.damage = 1
        self.attackCooldown = 1000
        self.dead = False
        self.batRect = None

    def setDead(self):
        self.aiEnabled = False
        self.dead = True

    def attack(self, target):
        if target != None:
            if pygame.time.get_ticks() - self.lastAttacked >= self.attackCooldown:
                self.lastAttacked = pygame.time.get_ticks()
                target.health -= 1

    def checkStuckInObject(self, objectClass, location, map, textures):
        for obj in map[location]:
            if isinstance(obj, objectClass):
                rectA = textures[self.textureName].get_rect()
                rectB = textures[obj.textureName].get_rect()
                if self.AABBCollision(self.x, self.y, rectA[2], rectA[3], obj.x, obj.y, rectB[2], rectB[3]):
                    return self.AABBCollision(self.x, self.y, rectA[2], rectA[3], obj.x, obj.y, rectB[2], rectB[3]), obj

    def update(self, map, textures):
        if self.health > 0:
            if self.aiEnabled and self.targetClass != None:
                if self.target == None:
                    for entity in map["Entities"]:
                        if isinstance(entity, self.targetClass):
                            self.target = entity
                else:
                    obj = self.checkStuckInObject(Fence, "Objects", map, textures)
                    player = self.checkStuckInObject(self.targetClass, "Entities", map, textures)
                    if obj != None:
                        if not obj[0]:
                            self.move(self.target.x, self.target.y)

                        else:
                            self.attack(obj[1])
                    else:
                        self.move(self.target.x, self.target.y)

                    if player != None:
                        if player[0]:
                            self.attack(player[1])
        else:
            self.setDead()

    def move(self, tX, tY):
        if not ((self.x > tX-2 and self.x < tX+2) and (self.y > tY-2 and self.y < tY+2)):
            self.moving = True
            angle = math.atan2(tY - self.y, tX - self.x)
            nx = math.cos(angle) * self.moveSpeed,
            ny = math.sin(angle) * self.moveSpeed,
            self.x += nx[0]
            self.y += ny[0]
        else:
            self.moving = False

class Mob(Entity):
    def __init__(self, x, y, hitbox=(0,0)):
        super().__init__(x, y, "slime1", hitbox)
        self.moveSpeed = 5
        self.aiEnabled = True
        self.targetClass = Player

class Player(Entity):
    def __init__(self, x, y, hitbox=(0,0)):
        super().__init__(x, y, "slime", hitbox)
        self.attackCooldown = 500
        self.texture0 = "slime"
        self.texture1 = "slime0"
        self.lastTextureChange = pygame.time.get_ticks()
        self.textureSpeed = 500
        self.tX = 0
        self.tY = 0
        self.deathTime = 0
        self.playerDead = False
        self.timeUntilReset = 2500

    def checkClubHit(self, objectClass, location, map, textures):
        for obj in map[location]:
            if isinstance(obj, objectClass):
                rectA = self.batRect
                rectB = textures[obj.textureName].get_rect()
                if self.AABBCollision(self.x, self.y, rectA[2], rectA[3], obj.x, obj.y, rectB[2], rectB[3]):
                    return self.AABBCollision(self.x, self.y, rectA[2], rectA[3], obj.x, obj.y, rectB[2], rectB[3]), obj

    def setDead(self):
        self.playerDead = True
        self.deathTime = pygame.time.get_ticks()
        self.x = 100000
        self.y = 100000


    def update(self, map, textures):
        self.move(self.tX, self.tY)
        if self.health > 0:
            if self.moving:
                if pygame.time.get_ticks() - self.lastTextureChange >= self.textureSpeed:
                    self.lastTextureChange = pygame.time.get_ticks()
                    if self.textureName == "slime":
                        self.textureName = "slime0"
                    elif self.textureName == "slime0":
                        self.textureName = "slime"
        else:
            self.setDead()

class Pond(StaticObject):
    def __init__(self, x, y):
        super().__init__(x, y, "pond0")
        self.texture0 = "pond0"
        self.texture1 = "pond1"
        self.lastTextureChange = pygame.time.get_ticks()
        self.textureSpeed = 500

    def update(self, map):
        if pygame.time.get_ticks() - self.lastTextureChange >= self.textureSpeed:
            self.lastTextureChange = pygame.time.get_ticks()
            if self.textureName == "pond0": self.textureName = "pond1"
            elif self.textureName == "pond1": self.textureName = "pond0"



Slimelone()