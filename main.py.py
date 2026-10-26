"""
BEYOND 1896
"Change the Past, Shape Tomorrow."

A Pygame historical adventure.
Optional title artwork: keep beyond_1896_title.png beside this Python file.
If the artwork is missing, the game uses its built-in illustrated background.

Setup:
    python -m pip install pygame
    python beyond_1896.py

Controls:
    Menu/Story/Dialogue/Quiz: mouse clicks or SPACE / ENTER
    Character select: click a character, then CONFIRM
    Map: WASD or arrow keys to move; E to interact with nearby characters/markers
    Archive: A to open/close; ESC to return
    ESC: return to menu (from map) or back from a panel
"""

import math
import random
import sys
import os
import pygame
import asyncio

pygame.init()

# ----------------------------- CONFIG ----------------------------------------
W, H = 1000, 650
FPS = 60
TITLE = "BEYOND 1896"
TAGLINE = "Change the Past, Shape Tomorrow."

screen = pygame.display.set_mode((W, H))
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()

# Optional cinematic title artwork, loaded from beside this Python file.
TITLE_IMAGE = None
try:
    _title_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "beyond_1896_title.png")
    if os.path.exists(_title_path):
        TITLE_IMAGE = pygame.image.load(_title_path).convert()
        TITLE_IMAGE = pygame.transform.smoothscale(TITLE_IMAGE, (W, H))
except (pygame.error, OSError):
    TITLE_IMAGE = None

# Vintage palette
INK = (48, 31, 24)
DARK = (27, 24, 25)
DARK_BROWN = (53, 35, 28)
BROWN = (104, 66, 42)
LEATHER = (130, 83, 48)
GOLD = (222, 177, 91)
PALE_GOLD = (245, 214, 145)
PAPER = (226, 201, 151)
LIGHT_PAPER = (242, 224, 185)
FADED = (173, 139, 91)
RED = (132, 48, 35)
GREEN = (67, 94, 60)
WHITE = (255, 245, 222)
GREY = (115, 99, 81)

FONT_CACHE = {}
def font(size, bold=False, serif=False):
    key = (size, bold, serif)
    if key not in FONT_CACHE:
        candidates = ["georgia", "timesnewroman", "palatinolinotype"] if serif else ["arial", "dejavusans"]
        chosen = None
        for name in candidates:
            chosen = pygame.font.SysFont(name, size, bold=bold)
            if chosen:
                break
        FONT_CACHE[key] = chosen or pygame.font.Font(None, size)
    return FONT_CACHE[key]

def draw_text(surface, text, x, y, size=22, color=INK, bold=False, center=False, serif=False):
    img = font(size, bold, serif).render(str(text), True, color)
    rect = img.get_rect()
    if center:
        rect.center = (int(x), int(y))
    else:
        rect.topleft = (int(x), int(y))
    surface.blit(img, rect)
    return rect

def wrap_text(text, fnt, max_width):
    words = str(text).split()
    lines, line = [], ""
    for word in words:
        test = word if not line else line + " " + word
        if fnt.size(test)[0] <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines

def paragraph(surface, text, rect, size=20, color=INK, line_gap=5, bold=False, serif=False):
    fnt = font(size, bold, serif)
    y = rect.y
    for para in str(text).split("\n"):
        for line in wrap_text(para, fnt, rect.width):
            surface.blit(fnt.render(line, True, color), (rect.x, y))
            y += fnt.get_linesize() + line_gap
        y += 3
    return y

def panel(surface, rect, fill=PAPER, border=GOLD, radius=12, width=3):
    pygame.draw.rect(surface, fill, rect, border_radius=radius)
    pygame.draw.rect(surface, border, rect, width, border_radius=radius)
    # subtle inner frame
    inner = rect.inflate(-12, -12)
    if inner.width > 0 and inner.height > 0:
        pygame.draw.rect(surface, FADED, inner, 1, border_radius=max(2, radius-4))

def button(surface, rect, label, hovered=False, size=21):
    fill = (88, 53, 35) if not hovered else (118, 77, 42)
    pygame.draw.rect(surface, fill, rect, border_radius=9)
    pygame.draw.rect(surface, GOLD if hovered else FADED, rect, 2, border_radius=9)
    pygame.draw.rect(surface, (35, 26, 23), rect.inflate(-7, -7), 1, border_radius=6)
    draw_text(surface, label, rect.centerx, rect.centery, size, LIGHT_PAPER, center=True, serif=True)

def draw_vignette(surface):
    overlay = pygame.Surface((W, H), pygame.SRCALPHA)
    # edge shading in bands
    for i in range(9):
        alpha = 8 + i * 2
        pygame.draw.rect(overlay, (20, 10, 8, alpha),
                         (i*7, i*5, W-i*14, H-i*10), width=9, border_radius=24)
    surface.blit(overlay, (0, 0))

def draw_grain(surface, count=160):
    # Deterministic-looking tiny flecks, refreshed slowly by frame counter
    random.seed(pygame.time.get_ticks() // 120)
    for _ in range(count):
        x, y = random.randrange(W), random.randrange(H)
        col = random.choice([(255, 224, 157, 18), (30, 17, 10, 22), (255, 245, 214, 12)])
        fleck = pygame.Surface((2, 2), pygame.SRCALPHA)
        fleck.fill(col)
        surface.blit(fleck, (x, y))

def draw_sky_scene(surface, sunset=False):
    surface.fill((47, 37, 38))
    top = (37, 35, 49) if not sunset else (70, 57, 70)
    mid = (137, 83, 55) if not sunset else (204, 129, 73)
    bottom = (211, 157, 91) if not sunset else (237, 184, 111)
    for y in range(H):
        t = y / H
        if t < .62:
            q = t / .62
            c = tuple(int(top[i]*(1-q) + mid[i]*q) for i in range(3))
        else:
            q = (t-.62)/.38
            c = tuple(int(mid[i]*(1-q) + bottom[i]*q) for i in range(3))
        pygame.draw.line(surface, c, (0, y), (W, y))
    # moon/sun
    if sunset:
        pygame.draw.circle(surface, (248, 210, 133), (790, 180), 62)
        pygame.draw.circle(surface, (238, 171, 100), (790, 180), 78, 2)
    else:
        pygame.draw.circle(surface, (235, 215, 174), (790, 115), 28)
    # far hills and rooftops
    pygame.draw.polygon(surface, (62, 49, 44), [(0, 370),(120,280),(220,350),(330,270),(450,360),(580,290),(710,365),(850,275),(1000,360),(1000,650),(0,650)])
    for x in range(-40, W+80, 145):
        base = random.Random(x+9).randint(385, 460)
        wid = random.Random(x+20).randint(95, 145)
        pygame.draw.rect(surface, (49, 35, 31), (x, base, wid, H-base))
        pygame.draw.polygon(surface, (35, 29, 28), [(x-9,base),(x+wid//2,base-45),(x+wid+8,base)])
        for wx in range(x+17, x+wid-10, 29):
            pygame.draw.rect(surface, (210, 143, 73), (wx, base+24, 10, 18))
    # road perspective
    pygame.draw.polygon(surface, (95, 67, 49), [(390, 390),(610,390),(850,H),(150,H)])
    for x in range(0, W, 90):
        pygame.draw.line(surface, (133, 93, 59), (500, 400), (x, H), 1)
    for y in range(455, H, 45):
        pygame.draw.line(surface, (133, 93, 59), (260, y), (740, y), 1)

def draw_school(surface):
    surface.fill((40, 32, 31))
    # old classroom/hall
    pygame.draw.rect(surface, (74, 49, 36), (0, 0, W, H))
    pygame.draw.polygon(surface, (37, 30, 28), [(0,0),(500,120),(1000,0)])
    pygame.draw.polygon(surface, (111, 73, 47), [(0,70),(500,160),(1000,70),(1000,100),(500,190),(0,100)])
    # floorboards
    pygame.draw.polygon(surface, (116, 76, 48), [(0, 400),(W,400),(W,H),(0,H)])
    for y in range(420,H,35):
        pygame.draw.line(surface, (77, 48, 34), (0,y),(W,y),2)
    for x in range(-200, W+200, 100):
        pygame.draw.line(surface, (77, 48, 34), (500,400),(x,H),2)
    # windows
    for x in (95, 745):
        pygame.draw.rect(surface, (31, 29, 32), (x, 100, 160, 220), 12)
        pygame.draw.rect(surface, (174, 116, 67), (x+8,108,144,204))
        pygame.draw.line(surface, (74, 46, 34), (x+80,108),(x+80,312),8)
        pygame.draw.line(surface, (74, 46, 34), (x+8,218),(x+152,218),8)
    # bookcase
    pygame.draw.rect(surface, (52, 32, 24), (355, 115, 290, 250))
    for y in (190, 265, 340):
        pygame.draw.rect(surface, (112, 69, 38), (365,y,270,9))
        x = 372
        while x < 625:
            bw = random.Random(x+y).randint(12, 24)
            pygame.draw.rect(surface, random.choice([RED, GREEN, BROWN, DARK_BROWN]), (x,y-48,bw,47))
            pygame.draw.line(surface, GOLD, (x+4,y-39),(x+bw-4,y-39),1)
            x += bw+3

def draw_book(surface, x, y, scale=1.0, glow=False):
    w, h = int(210*scale), int(145*scale)
    if glow:
        glow_surf = pygame.Surface((int(w*2.3), int(h*2.3)), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, (255, 187, 70, 35), glow_surf.get_rect())
        surface.blit(glow_surf, (x-w*.65,y-h*.65))
    rect = pygame.Rect(x,y,w,h)
    pygame.draw.ellipse(surface, (24,17,13), rect.move(12,15))
    pygame.draw.polygon(surface, (63, 39, 25), [(x,y+15),(x+w*.52,y),(x+w,y+15),(x+w,y+h),(x+w*.5,y+h-12),(x,y+h)])
    pygame.draw.polygon(surface, (143, 93, 49), [(x+8,y+15),(x+w*.5,y+28),(x+w-8,y+15),(x+w-8,y+h-12),(x+w*.5,y+h-25),(x+8,y+h-12)])
    pygame.draw.line(surface, GOLD, (x+w*.5,y+28),(x+w*.5,y+h-25),3)
    pygame.draw.rect(surface, GOLD, (x+22,y+34,w-44,h-62),2)
    draw_text(surface, "PHILIPPINE", x+w*.5, y+52, max(10,int(14*scale)), LIGHT_PAPER, center=True, serif=True)
    draw_text(surface, "HISTORY", x+w*.5, y+74, max(12,int(20*scale)), LIGHT_PAPER, bold=True, center=True, serif=True)
    pygame.draw.circle(surface, GOLD, (int(x+w*.5),int(y+h-42)), int(8*scale), 1)

def draw_person(surface, x, y, kind="student", facing=1, selected=False, scale=1.0):
    # Stylized full-body sprites drawn with simple shapes; coordinates are feet
    s = scale
    px, py = int(x), int(y)
    if selected:
        pygame.draw.ellipse(surface, (237, 181, 78), (px-int(24*s),py-int(7*s),int(48*s),int(14*s)),2)
    skin = (193, 137, 95)
    if kind == "bonifacio":
        shirt, pants, hair = (199, 179, 139), (57, 44, 35), (35, 26, 22)
    elif kind == "npc":
        shirt, pants, hair = (115, 78, 48), (65, 46, 35), (39, 28, 21)
    elif kind == "boy":
        shirt, pants, hair = (210, 207, 183), (47, 49, 53), (30, 25, 23)
    else:
        shirt, pants, hair = (188, 190, 166), (61, 50, 48), (31, 23, 22)
    # legs and shoes
    pygame.draw.line(surface, pants, (px-int(7*s),py-int(30*s)),(px-int(9*s),py), max(3,int(7*s)))
    pygame.draw.line(surface, pants, (px+int(7*s),py-int(30*s)),(px+int(10*s),py), max(3,int(7*s)))
    pygame.draw.ellipse(surface, DARK, (px-int(19*s),py-int(4*s),int(16*s),int(7*s)))
    pygame.draw.ellipse(surface, DARK, (px+int(3*s),py-int(4*s),int(16*s),int(7*s)))
    # body
    pygame.draw.polygon(surface, shirt, [(px-int(11*s),py-int(66*s)),(px+int(11*s),py-int(66*s)),(px+int(16*s),py-int(30*s)),(px-int(16*s),py-int(30*s))])
    # arms
    pygame.draw.line(surface, skin, (px-int(10*s),py-int(61*s)),(px-int(17*s),py-int(38*s)),max(3,int(5*s)))
    pygame.draw.line(surface, skin, (px+int(10*s),py-int(61*s)),(px+int(17*s),py-int(38*s)),max(3,int(5*s)))
    # neck/head/hair
    pygame.draw.rect(surface, skin, (px-int(4*s),py-int(73*s),int(8*s),int(10*s)))
    pygame.draw.ellipse(surface, skin, (px-int(12*s),py-int(92*s),int(24*s),int(25*s)))
    pygame.draw.ellipse(surface, hair, (px-int(13*s),py-int(96*s),int(26*s),int(16*s)))
    pygame.draw.rect(surface, hair, (px-int(13*s),py-int(88*s),int(5*s),int(20*s)))
    pygame.draw.rect(surface, hair, (px+int(8*s),py-int(88*s),int(5*s),int(20*s)))
    # eyes
    pygame.draw.circle(surface, INK, (px-int(5*s),py-int(81*s)), max(1,int(1.5*s)))
    pygame.draw.circle(surface, INK, (px+int(5*s),py-int(81*s)), max(1,int(1.5*s)))
    if kind == "bonifacio":
        pygame.draw.line(surface, RED, (px-int(12*s),py-int(68*s)),(px+int(12*s),py-int(60*s)),max(2,int(5*s)))
        pygame.draw.ellipse(surface, hair, (px-int(12*s),py-int(94*s),int(24*s),int(7*s)))

def draw_philippine_flag(surface, x, y, width=104, height=62):
    """Draw a small Philippine flag with its white triangle, sun, and three stars."""
    x, y, width, height = int(x), int(y), int(width), int(height)
    pygame.draw.rect(surface, (42, 28, 20), (x-4, y-4, width+8, height+8), border_radius=4)
    pygame.draw.rect(surface, (245, 245, 232), (x, y, width, height))
    pygame.draw.rect(surface, (0, 56, 168), (x, y, width, height//2))
    pygame.draw.rect(surface, (206, 17, 38), (x, y+height//2, width, height-height//2))
    pygame.draw.polygon(surface, (255, 255, 245),
                        [(x, y), (x+int(width*.48), y+height//2), (x, y+height)])
    cx, cy = x+int(width*.19), y+height//2
    pygame.draw.circle(surface, (255, 196, 0), (cx, cy), max(3, height//9))
    for i in range(8):
        a = i * math.pi / 4
        pygame.draw.line(surface, (255, 196, 0),
                         (cx+math.cos(a)*height*.11, cy+math.sin(a)*height*.11),
                         (cx+math.cos(a)*height*.18, cy+math.sin(a)*height*.18), 2)
    for sx, sy in [(x+int(width*.08), y+int(height*.18)),
                   (x+int(width*.08), y+int(height*.82)),
                   (x+int(width*.39), y+int(height*.50))]:
        pygame.draw.polygon(surface, (255, 196, 0),
            [(sx, sy-3), (sx+1, sy-1), (sx+3, sy), (sx+1, sy+1),
             (sx, sy+3), (sx-1, sy+1), (sx-3, sy), (sx-1, sy-1)])
    pygame.draw.rect(surface, GOLD, (x, y, width, height), 2)

def draw_map_background(surface):
    """Aged parchment map inspired by hand-drawn maps from the 1890s."""
    base = (202, 177, 128)
    surface.fill(base)
    for y in range(0, H, 12):
        for x in range(0, W, 12):
            shade = random.Random(x * 13 + y * 7).randint(-8, 8)
            pygame.draw.rect(surface, tuple(max(0, min(255, c + shade)) for c in base), (x, y, 12, 12))

    ink, faded_ink = (91, 57, 35), (135, 91, 54)
    water = (143, 164, 151)
    coast = [(770,0),(W,0),(W,H),(825,H),(850,570),(820,475),(840,390),(795,320),(820,230),(780,160)]
    pygame.draw.polygon(surface, water, coast)
    pygame.draw.lines(surface, faded_ink, False, coast[9:] + coast[:1], 3)
    for yy in range(35, H, 42):
        xx = 865 + (yy % 3) * 8
        pygame.draw.arc(surface, (111,139,130), (xx,yy,35,13), 0.3, 2.6, 1)
        pygame.draw.arc(surface, (111,139,130), (xx+28,yy+12,28,10), 0.3, 2.6, 1)

    paths = [((80,530),(180,440),(330,410),(470,330),(630,300),(770,240)),
             ((170,110),(260,220),(330,410),(420,520),(580,560)),
             ((470,330),(520,180),(620,110))]
    for pts in paths:
        pygame.draw.lines(surface, (173,130,77), False, pts, 22)
        pygame.draw.lines(surface, (218,190,145), False, pts, 2)
        pygame.draw.lines(surface, faded_ink, False, pts, 1)

    for x,y in [(70,90),(125,275),(250,75),(310,555),(420,100),(690,470),(705,160),(590,400),(190,360),(535,470),(90,600)]:
        pygame.draw.circle(surface, (111,118,77), (x,y), 18)
        pygame.draw.circle(surface, ink, (x,y), 18, 1)
        pygame.draw.circle(surface, (132,132,84), (x-5,y-5), 10, 1)
        pygame.draw.line(surface, ink, (x,y+10), (x,y+22), 2)

    for x,y in [(180,160),(355,205),(490,455),(630,190),(610,530),(250,480),(710,355)]:
        pygame.draw.rect(surface, (169,124,77), (x,y,64,44))
        pygame.draw.rect(surface, ink, (x,y,64,44), 2)
        roof = [(x-8,y+3),(x+32,y-24),(x+72,y+3)]
        pygame.draw.polygon(surface, (117,72,43), roof)
        pygame.draw.polygon(surface, ink, roof, 2)
        pygame.draw.rect(surface, (220,187,128), (x+9,y+12,12,15))
        pygame.draw.rect(surface, ink, (x+9,y+12,12,15), 1)
        pygame.draw.rect(surface, (89,58,39), (x+38,y+17,13,27))

    pygame.draw.rect(surface, ink, (10,10,W-20,H-20), 4)
    pygame.draw.rect(surface, (224,199,151), (17,17,W-34,H-34), 2)
    pygame.draw.rect(surface, faded_ink, (24,24,W-48,H-48), 1)
    # Compass rose
    cx, cy = 914, 75
    pygame.draw.circle(surface, ink, (cx,cy), 24, 1)
    pygame.draw.polygon(surface, ink, [(cx,cy-19),(cx-5,cy),(cx+5,cy)])
    pygame.draw.polygon(surface, (231,210,166), [(cx,cy+19),(cx-5,cy),(cx+5,cy)])
    draw_text(surface, "N", cx, cy-34, 13, ink, center=True, bold=True)

# ----------------------------- STORY DATA ------------------------------------
QUESTIONS = [
    ("Why was the Katipunan created?",
     ["To extend Spanish colonial rule", "To seek Philippine independence", "To collect hospital fees"], 1,
     "The Katipunan was a secret revolutionary society formed to pursue freedom from Spanish colonial rule."),
    ("When was the Katipunan founded?",
     ["August 30, 1896", "June 12, 1898", "July 7, 1892"], 2,
     "The Katipunan was founded on July 7, 1892, in Tondo, Manila."),
    ("Who was a principal founder of the Katipunan?",
     ["Ferdinand Magellan", "Miguel López de Legazpi", "Andres Bonifacio"], 2,
     "Andres Bonifacio was one of the principal founders and became a leading figure of the movement."),
    ("What does KKK refer to in this historical context?",
     ["A foreign trading company", "Kataastaasan, Kagalanggalangang Katipunan ng mga Anak ng Bayan", "A colonial tax office"], 1,
     "The initials refer to the Katipunan, a Filipino revolutionary society. It is unrelated to the similarly abbreviated American organization."),
    ("Which action best reflects unity and dignity?",
     ["Treating neighbors as inferior", "Helping only the wealthy", "Cooperating and respecting others"], 2,
     "The Katipunan's teachings emphasized honorable conduct, solidarity, and concern for fellow Filipinos."),
    ("What was the Katipunan's central goal?",
     ["Control over all Asian countries", "Build a new Spanish royal palace", "Philippine independence"], 2,
     "Its revolutionary goal was to end Spanish colonial rule and achieve independence."),
    ("What major struggle did the Katipunan help launch?",
     ["The Philippine Revolution of 1896", "The Second World War", "Magellan's voyage in 1521"], 0,
     "The discovery of the Katipunan in 1896 helped precipitate the Philippine Revolution against Spain."),
    ("Who wrote the Kartilya ng Katipunan?",
     ["José Rizal", "A Spanish governor", "Emilio Jacinto"], 2,
     "Emilio Jacinto wrote the Kartilya ng Katipunan, a guide to the society's principles and conduct."),
    ("Which lesson can help shape a better future?",
     ["Erase every hardship from history", "Assume one person can fix everything alone", "Work together for dignity and accountable institutions"], 2,
     "Collective action, fairness, and accountable institutions can help communities address shared problems."),
    ("What is one reason to study the Philippine Revolution today?",
     ["To understand sacrifices and learn from history", "To repeat every decision without question", "To forget the people who came before us"], 0,
     "History helps people understand past choices, honor those who struggled for change, and make more thoughtful decisions today.")
]

ARCHIVE_ENTRIES = [
    ("The Katipunan", "The Kataastaasan, Kagalanggalangang Katipunan ng mga Anak ng Bayan was a secret revolutionary society founded in 1892 to seek independence from Spain."),
    ("Andres Bonifacio", "Andres Bonifacio was a principal founder and leader of the Katipunan. He helped organize resistance to Spanish colonial rule."),
    ("Emilio Jacinto", "Emilio Jacinto, often called the Brains of the Katipunan, wrote the Kartilya, which set out ethical principles for members."),
    ("The Kartilya", "The Kartilya ng Katipunan taught moral conduct, equality, love of country, and respect for fellow people."),
    ("The Revolution of 1896", "The Philippine Revolution against Spain broke out in 1896. The discovery of the Katipunan was a key turning point."),
    ("A note about dates", "The Katipunan was founded on July 7, 1892. August 30, 1896, is associated with the uprising at San Juan del Monte."),
    ("Unity and service", "The story's fictional student connects past struggles to present-day questions about fairness, public services, and community responsibility."),
]

NPCS = [
    {"name":"Andres Bonifacio","kind":"bonifacio","pos":(480,330),"question":0,
     "dialogue":"The Katipunan was created to unite Filipinos in the struggle for freedom. We sought an organization that would awaken the spirit of independence in our people."},
    {"name":"Katipunero","kind":"npc","pos":(620,300),"question":1,
     "dialogue":"We meet in secret because the colonial authorities could punish those who challenged their rule. Remember the year our society was founded."},
    {"name":"Town Teacher","kind":"npc","pos":(330,410),"question":2,
     "dialogue":"Many people contributed to the movement. Learn the names of those who organized it and helped it grow."},
    {"name":"Messenger","kind":"npc","pos":(260,220),"question":3,
     "dialogue":"Our initials stand for the Katipunan's long Filipino name. It represented a society committed to the nation's cause."},
    {"name":"Community Elder","kind":"npc","pos":(180,440),"question":4,
     "dialogue":"A movement needs more than courage. Its members must also act with dignity and care for one another."},
    {"name":"Revolutionary Guide","kind":"npc","pos":(520,180),"question":5,
     "dialogue":"Keep the goal in mind: the movement was not formed to gain a palace or conquer other nations."},
    {"name":"History Keeper","kind":"npc","pos":(630,110),"question":6,
     "dialogue":"The discovery of the Katipunan in 1896 helped set a much larger struggle in motion."},
    {"name":"Young Writer","kind":"npc","pos":(420,520),"question":7,
     "dialogue":"The Katipunan's teachings gave members guidance on how to live and serve. Do you remember who wrote the Kartilya?"},
    {"name":"Village Organizer","kind":"npc","pos":(250,480),"question":8,
     "dialogue":"The past reminds us that lasting change takes people working together, not one person acting alone."},
    {"name":"Archive Guardian","kind":"npc","pos":(710,355),"question":9,
     "dialogue":"History is not only a list of dates. It helps us understand sacrifices and choose what kind of future we want."},
]

# ----------------------------- GAME STATE ------------------------------------
state = "menu"
previous_state = "map"
selected_character = "girl"
character_confirmed = False
story_index = 0
score = 0
answered = set()
unlocked_archive = set()
dialogue_npc = None
quiz_index = None
quiz_choice = None
quiz_feedback = None
quiz_feedback_timer = 0
player_x, player_y = 450, 400
player_speed = 3.0
map_message = "Explore the village. Walk near a character or marker and press E."
map_message_timer = 0
visited_npcs = set()
frame = 0

# clickable regions
start_rect = pygame.Rect(370, 330, 260, 48)
archive_rect = pygame.Rect(370, 390, 260, 44)
quit_rect = pygame.Rect(370, 446, 260, 42)
girl_rect = pygame.Rect(285, 220, 170, 230)
boy_rect = pygame.Rect(545, 220, 170, 230)
confirm_rect = pygame.Rect(390, 490, 220, 48)
continue_rect = pygame.Rect(710, 560, 220, 48)
close_rect = pygame.Rect(820, 25, 145, 42)
answer_rects = [pygame.Rect(170, 345+i*58, 660, 46) for i in range(3)]
archive_item_rects = [pygame.Rect(95, 145+i*58, 810, 48) for i in range(len(ARCHIVE_ENTRIES))]

def begin_story():
    global state, story_index, score, answered, unlocked_archive, visited_npcs, player_x, player_y
    state = "story"
    story_index = 0
    score = 0
    answered = set()
    unlocked_archive = set()
    visited_npcs = set()
    player_x, player_y = 450, 400

def start_map():
    global state, player_x, player_y
    state = "map"
    player_x, player_y = 450, 400

def nearest_npc():
    best, dist = None, 99999
    for npc in NPCS:
        d = math.hypot(player_x - npc["pos"][0], player_y - npc["pos"][1])
        if d < dist:
            best, dist = npc, d
    return best, dist

def open_npc(npc):
    global state, dialogue_npc, quiz_index
    dialogue_npc = npc
    quiz_index = npc["question"]
    if quiz_index in answered:
        state = "dialogue_done"
    else:
        state = "dialogue"

def open_archive():
    global previous_state, state
    previous_state = state
    state = "archive"

def draw_title():
    # Use the supplied cinematic artwork when available; otherwise use the
    # original code-drawn sunset as a fallback.
    if TITLE_IMAGE is not None:
        screen.blit(TITLE_IMAGE, (0, 0))
        shade = pygame.Surface((W, 92), pygame.SRCALPHA)
        shade.fill((20, 10, 8, 155))
        screen.blit(shade, (0, H-92))
    else:
        draw_sky_scene(screen)
        shade = pygame.Surface((600, 365), pygame.SRCALPHA)
        shade.fill((26, 20, 19, 200))
        screen.blit(shade, (200, 95))
        panel(screen, pygame.Rect(200, 95, 600, 365), (47, 32, 26), GOLD, 14, 3)
        for i in range(16):
            a = i * math.pi/8
            x1, y1 = 500+math.cos(a)*50, 170+math.sin(a)*26
            x2, y2 = 500+math.cos(a)*74, 170+math.sin(a)*39
            pygame.draw.line(screen, GOLD, (x1,y1),(x2,y2),2)
        draw_text(screen, "BEYOND", 500, 220, 65, PALE_GOLD, bold=True, center=True, serif=True)
        draw_text(screen, "1896", 500, 280, 66, PALE_GOLD, bold=True, center=True, serif=True)
        draw_text(screen, f"“{TAGLINE}”", 500, 335, 22, LIGHT_PAPER, center=True, serif=True)

    # Keep menu buttons along the bottom, away from the artwork's title.
    start_rect.update(180, 552, 230, 48)
    archive_rect.update(425, 552, 230, 48)
    quit_rect.update(670, 552, 150, 48)
    button(screen, start_rect, "START GAME", start_rect.collidepoint(pygame.mouse.get_pos()), 20)
    button(screen, archive_rect, "HISTORY ARCHIVE", archive_rect.collidepoint(pygame.mouse.get_pos()), 17)
    button(screen, quit_rect, "QUIT", quit_rect.collidepoint(pygame.mouse.get_pos()), 18)
    if TITLE_IMAGE is None:
        draw_text(screen, "A HISTORICAL ADVENTURE", 500, 500, 17, PALE_GOLD, center=True, serif=True)
    draw_vignette(screen)


def draw_character_select():
    draw_sky_scene(screen, True)
    panel(screen, pygame.Rect(150, 90, 700, 500), (61, 42, 31), GOLD, 14, 3)
    draw_text(screen, "CHOOSE YOUR CHARACTER", 500, 135, 32, LIGHT_PAPER, bold=True, center=True, serif=True)
    # portrait cards
    for rect, name, kind in [(girl_rect,"GIRL","girl"),(boy_rect,"BOY","boy")]:
        chosen = selected_character == kind
        panel(screen, rect, (93, 62, 42) if chosen else (48, 36, 31), GOLD if chosen else FADED, 12, 4 if chosen else 2)
        # stylized portrait
        pygame.draw.rect(screen, (115, 77, 50), (rect.x+18,rect.y+18,rect.width-36,rect.height-72), border_radius=7)
        pygame.draw.rect(screen, (44, 34, 30), (rect.x+25,rect.y+25,rect.width-50,rect.height-86), 2)
        # draw larger bust
        cx, cy = rect.centerx, rect.y+rect.height-75
        pygame.draw.ellipse(screen, (40,27,23), (cx-48,cy-110,96,105))
        pygame.draw.ellipse(screen, (190,137,98), (cx-29,cy-100,58,65))
        pygame.draw.ellipse(screen, (30,22,19), (cx-32,cy-111,64,35))
        pygame.draw.polygon(screen, (190,190,166) if kind=="girl" else (211,207,183),
                            [(cx-35,cy-39),(cx+35,cy-39),(cx+57,cy+5),(cx-57,cy+5)])
        pygame.draw.polygon(screen, (60,49,47),(cx-57,cy+5),(cx+57,cy+5),(cx+75,cy+35),(cx-75,cy+35)) if False else None
        draw_text(screen, name, rect.centerx, rect.bottom-28, 24, LIGHT_PAPER, bold=True, center=True, serif=True)
        if chosen:
            draw_text(screen, "SELECTED", rect.centerx, rect.y-12, 15, PALE_GOLD, bold=True, center=True)
    button(screen, confirm_rect, "CONFIRM", confirm_rect.collidepoint(pygame.mouse.get_pos()), 22)
    draw_text(screen, "Choose a character to begin your journey.", 500, 555, 17, LIGHT_PAPER, center=True)

STORY_PAGES = [
    ("A FAMILY'S STRUGGLE",
     "You are a student whose family has been struggling to make ends meet. Your father works construction for a minimum wage, doing everything he can to support the family."),
    ("A DIFFICULT SEASON",
     "When your mother becomes seriously ill and needs an operation, the hospital expenses are more than your family can afford. You borrow money from relatives and seek help from local government offices."),
    ("THE DAY EVERYTHING CHANGED",
     "Your father keeps working to pay the debts. One afternoon, an accident at his worksite takes his life. Grief fills your home, but you try to keep moving forward."),
    ("THE MYSTERIOUS BOOK",
     "Late one evening, you walk through your school's quiet hallway, thinking about history and asking yourself whether fairer, more accountable institutions could make life better for families like yours."),
    ("BEYOND THE PAGES",
     "You find a dusty, damaged book about Philippine history. Its pages begin turning by themselves. One word glows on the page: KKK. A flash of light fills the hall—and the world disappears."),
    ("WELCOME TO 1892",
     "You awaken in a place you do not recognize. A message appears: “FIND OUT WHY THE KATIPUNAN WAS CREATED.” Your journey through history begins now.")
]

def draw_story():
    if story_index < 3:
        draw_school(screen)
        # desk and student silhouette
        pygame.draw.rect(screen, (76,47,31), (110, 410, 780, 18))
        pygame.draw.rect(screen, (57,36,27), (150,428,20,125))
        pygame.draw.rect(screen, (57,36,27), (830,428,20,125))
        if story_index == 0:
            draw_person(screen, 500, 405, selected_character, scale=1.65)
        elif story_index == 1:
            draw_person(screen, 400, 405, selected_character, scale=1.65)
            draw_book(screen, 585, 390, .8, True)
        else:
            # empty, dim hall and father's work helmet
            pygame.draw.ellipse(screen, (186,139,69), (460, 350, 80, 30), 3)
            pygame.draw.arc(screen, (186,139,69), (460,330,80,48), math.pi, 2*math.pi, 3)
            for i in range(5):
                pygame.draw.line(screen, (220,171,89), (500,350),(500+math.cos(i*1.2)*150,350+math.sin(i*1.2)*100),1)
    elif story_index == 3:
        draw_school(screen)
        draw_person(screen, 285, 420, selected_character, scale=1.55)
    elif story_index == 4:
        draw_school(screen)
        draw_book(screen, 395, 270, 1.05, True)
        # glow rays
        for i in range(24):
            a = frame*.018 + i*math.pi/12
            pygame.draw.line(screen, (231,176,75), (500,340),
                             (500+math.cos(a)*220,340+math.sin(a)*180), 2)
        draw_person(screen, 265, 490, selected_character, scale=1.4)
    else:
        draw_sky_scene(screen)
        # magical portal
        portal = pygame.Surface((400,500), pygame.SRCALPHA)
        for r in range(160,20,-12):
            alpha = max(5, 60 - (160-r)//3)
            pygame.draw.ellipse(portal,(255,196,90,alpha),(200-r,250-r,2*r,2*r),5)
        screen.blit(portal,(300,80))
        draw_person(screen,500,500,selected_character,scale=1.5)
        draw_text(screen,"1892",500,130,56,PALE_GOLD,bold=True,center=True,serif=True)
    # story caption
    rect = pygame.Rect(60, 465, 880, 140)
    panel(screen, rect, (35,27,24), GOLD, 12, 2)
    title, body = STORY_PAGES[story_index]
    draw_text(screen,title,85,482,23,PALE_GOLD,bold=True,serif=True)
    paragraph(screen,body,pygame.Rect(85,515,820,65),18,LIGHT_PAPER,3)
    button(screen, continue_rect, "CONTINUE  ▶", continue_rect.collidepoint(pygame.mouse.get_pos()), 20)
    draw_text(screen, f"{story_index+1} / {len(STORY_PAGES)}", 70, 620, 15, LIGHT_PAPER)

def draw_map():
    draw_map_background(screen)
    # map title ribbon
    panel(screen, pygame.Rect(25,25,310,58), (53,37,27), GOLD, 8, 2)
    draw_text(screen,"SAN PEDRO • 1892",45,37,22,LIGHT_PAPER,bold=True,serif=True)
    draw_text(screen,"Move: WASD / Arrows     Interact: E",35,602,17,LIGHT_PAPER)
    draw_text(screen,f"POINTS: {score}",820,35,20,PALE_GOLD,bold=True)
    # NPCs
    for npc in NPCS:
        x,y = npc["pos"]
        done = npc["question"] in answered
        color = GREEN if done else GOLD
        pygame.draw.circle(screen,(40,30,23),(x,y-33),23)
        pygame.draw.circle(screen,color,(x,y-33),20,3)
        draw_person(screen,x,y,npc["kind"],scale=0.78)
        draw_text(screen,npc["name"],x,y+7,13,WHITE,center=True,bold=True)
        if not done:
            pygame.draw.circle(screen,(240,199,87),(x+21,y-59),10)
            draw_text(screen,"!",x+21,y-60,15,INK,bold=True,center=True)
    # player
    draw_person(screen,player_x,player_y,selected_character,selected=True,scale=0.88)
    # nearest prompt
    npc, dist = nearest_npc()
    if npc and dist < 88:
        prompt = pygame.Rect(290, 530, 420, 48)
        panel(screen,prompt,(44,31,25),GOLD,8,2)
        draw_text(screen,f"Press E to talk to {npc['name']}",500,554,18,LIGHT_PAPER,center=True)
    if map_message_timer > 0:
        panel(screen,pygame.Rect(260,90,480,45),(42,30,24),GOLD,8,2)
        draw_text(screen,map_message,500,112,17,LIGHT_PAPER,center=True)
    # quest progress
    panel(screen,pygame.Rect(800,85,170,105),(49,35,26),FADED,8,2)
    draw_text(screen,"MISSION",885,105,16,PALE_GOLD,bold=True,center=True)
    draw_text(screen,f"Questions: {len(answered)}/10",885,134,15,LIGHT_PAPER,center=True)
    draw_text(screen,"A = History Archive",885,160,13,LIGHT_PAPER,center=True)
    # Philippine flag badge in the lower-right corner of the map.
    draw_philippine_flag(screen, 858, 535, 92, 55)
    draw_text(screen, "PILIPINAS", 904, 598, 12, INK, bold=True, center=True)
    draw_vignette(screen)

def draw_dialogue(done=False):
    draw_map_background(screen)
    npc = dialogue_npc
    if npc:
        draw_person(screen,500,420,npc["kind"],scale=2.1)
        draw_text(screen,npc["name"],500,90,34,PALE_GOLD,bold=True,center=True,serif=True)
        rect = pygame.Rect(90,430,820,165)
        panel(screen,rect,(38,28,24),GOLD,12,3)
        body = "You have already answered this character's question. Explore the village to find another clue." if done else npc["dialogue"]
        paragraph(screen,body,pygame.Rect(120,465,760,88),22,LIGHT_PAPER,5)
        if done:
            label = "BACK TO MAP"
        else:
            label = "ANSWER QUESTION  ▶"
        button(screen,continue_rect,label,continue_rect.collidepoint(pygame.mouse.get_pos()),18)
    draw_vignette(screen)

def draw_quiz():
    # paper-like quiz screen
    screen.fill((62,43,30))
    for y in range(H):
        col = (int(93+24*y/H),int(64+19*y/H),int(40+10*y/H))
        pygame.draw.line(screen,col,(0,y),(W,y))
    # paper texture
    panel(screen,pygame.Rect(90,45,820,560),LIGHT_PAPER,(105,67,39),12,4)
    pygame.draw.rect(screen,(181,140,84),(107,62,786,526),2,border_radius=8)
    q = QUESTIONS[quiz_index]
    draw_text(screen,f"HISTORICAL QUESTION  {quiz_index+1}/10",500,95,19,BROWN,bold=True,center=True)
    qrect = pygame.Rect(145,130,710,100)
    paragraph(screen,q[0],qrect,30,INK,4,True,True)
    for i, ans in enumerate(q[1]):
        rect = answer_rects[i]
        chosen = quiz_choice == i
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        fill = (222,204,160) if not chosen else (193,171,120)
        if quiz_feedback is not None and i == q[2]:
            fill = (158,184,131)
        pygame.draw.rect(screen,fill,rect,border_radius=8)
        pygame.draw.rect(screen,GOLD if hovered or chosen else FADED,rect,2,border_radius=8)
        draw_text(screen, "ABC"[i]+".",rect.x+22,rect.centery,20,BROWN,bold=True,center=True)
        draw_text(screen,ans,rect.x+48,rect.centery,19,INK,center=False)
    draw_text(screen,f"POINTS: {score}",140,555,18,BROWN,bold=True)
    if quiz_feedback is not None:
        feedback_rect = pygame.Rect(145,520,710,60)
        panel(screen,feedback_rect,(232,215,174),GREEN if quiz_feedback else RED,8,2)
        msg = "Correct! +10 points. " if quiz_feedback else "Not quite. "
        draw_text(screen,msg + " " + q[3],feedback_rect.x+14,feedback_rect.y+10,15,INK)
        button(screen,pygame.Rect(690,565,150,35),"CONTINUE",pygame.mouse.get_pos() and pygame.Rect(690,565,150,35).collidepoint(pygame.mouse.get_pos()),15)
    else:
        draw_text(screen,"Choose the best answer.",500,570,16,BROWN,center=True)

def draw_archive():
    draw_school(screen)
    # archive shelves foreground
    panel(screen,pygame.Rect(55,45,890,560),(46,31,24),GOLD,12,3)
    draw_text(screen,"HISTORY ARCHIVE",500,82,34,PALE_GOLD,bold=True,center=True,serif=True)
    draw_text(screen,"Spend 5 points to unlock an entry. Unlocked entries stay available.",500,113,16,LIGHT_PAPER,center=True)
    for i, entry in enumerate(ARCHIVE_ENTRIES):
        rect = archive_item_rects[i]
        is_open = i in unlocked_archive
        is_free = i == 0 or i == 1
        can_unlock = score >= 5
        fill = (106,75,48) if is_open else (67,48,35)
        pygame.draw.rect(screen,fill,rect,border_radius=7)
        pygame.draw.rect(screen,GOLD if is_open else FADED,rect,2,border_radius=7)
        prefix = "✓" if is_open else ("FREE" if is_free else "🔒 5 pts")
        draw_text(screen,entry[0],rect.x+16,rect.y+10,18,LIGHT_PAPER,bold=True)
        draw_text(screen,prefix,rect.right-88,rect.y+12,14,PALE_GOLD,center=True)
        if is_open:
            # show a concise excerpt in the same row
            excerpt = entry[1]
            fnt = font(13)
            lines = wrap_text(excerpt,fnt,rect.width-30)
            draw_text(screen,lines[0] if lines else "",rect.x+16,rect.y+30,13,(244,225,188))
    button(screen,close_rect,"CLOSE  (ESC)",close_rect.collidepoint(pygame.mouse.get_pos()),16)
    draw_text(screen,f"AVAILABLE POINTS: {score}",500,580,18,PALE_GOLD,bold=True,center=True)

def draw_final():
    draw_sky_scene(screen, True)
    # flag-inspired sunset silhouette
    pygame.draw.line(screen,(32,27,25),(140,170),(140,555),7)
    pygame.draw.polygon(screen,(151,44,34),[(145,180),(300,180),(300,230),(145,230)])
    pygame.draw.polygon(screen,(230,220,185),[(145,230),(300,230),(260,275),(145,275)])
    pygame.draw.circle(screen,GOLD,(170,218),9)
    panel(screen,pygame.Rect(260,80,620,490),(44,30,26),GOLD,14,3)
    draw_text(screen,"MISSION COMPLETE",570,125,35,PALE_GOLD,bold=True,center=True,serif=True)
    draw_text(screen,f"{score} / 100",570,200,54,LIGHT_PAPER,bold=True,center=True,serif=True)
    draw_text(screen,f"Questions answered: {len(answered)} / 10",570,248,20,LIGHT_PAPER,center=True)
    draw_text(screen,f"Archive entries unlocked: {len(unlocked_archive)}",570,278,18,LIGHT_PAPER,center=True)
    paragraph(screen,"You return to the future with a deeper understanding of the people who struggled for freedom. History cannot erase every hardship, but it can teach us to work together, protect dignity, and demand responsible institutions.",pygame.Rect(335,320,470,100),18,LIGHT_PAPER,4)
    draw_text(screen,"OUR HISTORY LIVES IN THE CHOICES WE MAKE TODAY.",570,442,17,PALE_GOLD,bold=True,center=True,serif=True)
    button(screen,pygame.Rect(390,490,180,45),"PLAY AGAIN",pygame.mouse.get_pos() and pygame.Rect(390,490,180,45).collidepoint(pygame.mouse.get_pos()),17)
    button(screen,pygame.Rect(590,490,180,45),"MAIN MENU",pygame.mouse.get_pos() and pygame.Rect(590,490,180,45).collidepoint(pygame.mouse.get_pos()),17)
    draw_vignette(screen)

# ----------------------------- ASYNC MAIN LOOP -------------------------------
async def main():
    global running, frame, map_message_timer, state, story_index
    global quiz_choice, quiz_feedback, quiz_feedback_timer, score
    global player_x, player_y, selected_character, map_message
    running = True
    while running:
        dt = clock.tick(FPS)
        frame += 1
        if map_message_timer > 0:
            map_message_timer -= dt

        mouse = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if state == "archive":
                        state = previous_state
                    elif state in ("dialogue","dialogue_done","quiz"):
                        state = "map"
                    elif state == "map":
                        state = "menu"
                    elif state in ("story","character"):
                        state = "menu"
                    elif state == "final":
                        state = "menu"
                if state == "map" and event.key == pygame.K_e:
                    npc, dist = nearest_npc()
                    if npc and dist < 88:
                        open_npc(npc)
                    else:
                        map_message = "Walk closer to a character marked with !, then press E."
                        map_message_timer = 2200
                if state == "story" and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    story_index += 1
                    if story_index >= len(STORY_PAGES):
                        start_map()
                elif state == "dialogue" and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    state = "quiz"
                    quiz_choice = None
                    quiz_feedback = None
                elif state == "dialogue_done" and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    state = "map"
                elif state == "quiz" and quiz_feedback is None and event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    quiz_choice = event.key - pygame.K_1
                    q = QUESTIONS[quiz_index]
                    is_correct = quiz_choice == q[2]
                    quiz_feedback = is_correct
                    if quiz_index not in answered:
                        answered.add(quiz_index)
                        if is_correct:
                            score += 10
                    if len(answered) == 10:
                        # let the explanation be read before the final screen
                        quiz_feedback_timer = pygame.time.get_ticks()
                elif state == "quiz" and quiz_feedback is not None and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    if len(answered) >= 10:
                        state = "final"
                    else:
                        state = "map"
                    quiz_feedback = None
                elif state == "map":
                    keys = pygame.key.get_pressed()
                    if event.key == pygame.K_a:
                        open_archive()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if state == "menu":
                    if start_rect.collidepoint(event.pos):
                        state = "character"
                    elif archive_rect.collidepoint(event.pos):
                        open_archive()
                    elif quit_rect.collidepoint(event.pos):
                        running = False
                elif state == "character":
                    if girl_rect.collidepoint(event.pos):
                        selected_character = "girl"
                    elif boy_rect.collidepoint(event.pos):
                        selected_character = "boy"
                    elif confirm_rect.collidepoint(event.pos):
                        begin_story()
                elif state == "story":
                    if continue_rect.collidepoint(event.pos):
                        story_index += 1
                        if story_index >= len(STORY_PAGES):
                            start_map()
                elif state == "dialogue":
                    if continue_rect.collidepoint(event.pos):
                        state = "quiz"
                        quiz_choice = None
                        quiz_feedback = None
                elif state == "dialogue_done":
                    if continue_rect.collidepoint(event.pos):
                        state = "map"
                elif state == "quiz":
                    if quiz_feedback is None:
                        for i, rect in enumerate(answer_rects):
                            if rect.collidepoint(event.pos):
                                quiz_choice = i
                                q = QUESTIONS[quiz_index]
                                quiz_feedback = quiz_choice == q[2]
                                if quiz_index not in answered:
                                    answered.add(quiz_index)
                                    if quiz_feedback:
                                        score += 10
                                break
                    else:
                        next_rect = pygame.Rect(690,565,150,35)
                        if next_rect.collidepoint(event.pos) or continue_rect.collidepoint(event.pos):
                            if len(answered) >= 10:
                                state = "final"
                            else:
                                state = "map"
                            quiz_feedback = None
                elif state == "map":
                    if close_rect.collidepoint(event.pos):
                        open_archive()
                elif state == "archive":
                    if close_rect.collidepoint(event.pos):
                        state = previous_state
                    else:
                        for i, rect in enumerate(archive_item_rects):
                            if rect.collidepoint(event.pos):
                                if i in unlocked_archive:
                                    pass
                                elif i in (0,1):
                                    unlocked_archive.add(i)
                                elif score >= 5:
                                    score -= 5
                                    unlocked_archive.add(i)
                                else:
                                    map_message = "You need 5 points to unlock that archive entry."
                                    map_message_timer = 2400
                elif state == "final":
                    if pygame.Rect(390,490,180,45).collidepoint(event.pos):
                        begin_story()
                    elif pygame.Rect(590,490,180,45).collidepoint(event.pos):
                        state = "menu"

        # continuous map movement
        if state == "map":
            keys = pygame.key.get_pressed()
            dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
            dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
            if dx or dy:
                mag = math.hypot(dx,dy)
                player_x += dx/mag*player_speed
                player_y += dy/mag*player_speed
                player_x = max(35,min(755,player_x))
                player_y = max(115,min(585,player_y))
            # interact is handled on key press, not held
            # ESC and archive keys are handled above

        # draw current state
        if state == "menu":
            draw_title()
        elif state == "character":
            draw_character_select()
        elif state == "story":
            draw_story()
        elif state == "map":
            draw_map()
        elif state == "dialogue":
            draw_dialogue(False)
        elif state == "dialogue_done":
            draw_dialogue(True)
        elif state == "quiz":
            draw_quiz()
        elif state == "archive":
            draw_archive()
        elif state == "final":
            draw_final()

        # E interaction needs KEYDOWN and is handled separately below via event state.
        # Footer controls are shown unobtrusively.
        pygame.display.flip()
        await asyncio.sleep(0)  # Let the browser process input and render frames.

        # To keep interaction responsive, process E from a short key-state edge tracker.
        # The edge tracker is updated once per frame after rendering.
        if state == "map":
            pass

    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())