import os
import time
import math
import random
import urllib.parse
import urllib.request
import urllib.error
from typing import Optional, List, Dict, Callable
from PIL import Image, ImageDraw, ImageFilter
from openai import OpenAI
from character_consistency import CharacterProfile, build_scene_prompt

def _fetch_url_to_file(url: str, output_path: str, timeout: int = 15) -> bool:
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MagicTale/1.0"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            if len(data) > 4000:
                with open(output_path, "wb") as f:
                    f.write(data)
                return True
    except Exception:
        pass
    return False

def _try_pollinations(prompt_text: str, character: CharacterProfile, page_number: int, story_id: str, output_path: str) -> bool:
    seed = (abs(hash(f"{character.name}_{story_id}")) + page_number * 317) % 9999999
    concise_prompt = (
        f"{character.name} the {character.species_or_type}, wearing {character.clothing}, "
        f"{prompt_text}, children's book illustration, vibrant watercolor, clean lines, no text"
    )
    encoded = urllib.parse.quote(concise_prompt[:220])
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&seed={seed}&nologo=true"
    
    if _fetch_url_to_file(url, output_path, timeout=14):
        return True
    
    simple_encoded = urllib.parse.quote(f"children storybook illustration, {prompt_text}"[:160])
    fallback_url = f"https://image.pollinations.ai/prompt/{simple_encoded}?width=512&height=512&nologo=true"
    return _fetch_url_to_file(fallback_url, output_path, timeout=12)

def _draw_sky(draw: ImageDraw.ImageDraw, width: int, height: int, page_num: int):
    sky_gradients = [
        ((255, 225, 195), (255, 245, 215), (185, 220, 245)),
        ((225, 205, 245), (195, 235, 235), (145, 185, 235)),
        ((175, 230, 255), (145, 215, 240), (105, 180, 235)),
        ((255, 185, 115), (235, 145, 155), (115, 105, 175)),
        ((125, 85, 165), (240, 155, 165), (255, 225, 135)),
    ]
    c_top, c_mid, c_bot = sky_gradients[(page_num - 1) % len(sky_gradients)]
    mid_y = int(height * 0.45)
    for y in range(height):
        if y < mid_y:
            t = y / mid_y
            r = int(c_top[0] * (1 - t) + c_mid[0] * t)
            g = int(c_top[1] * (1 - t) + c_mid[1] * t)
            b = int(c_top[2] * (1 - t) + c_mid[2] * t)
        else:
            t = (y - mid_y) / (height - mid_y)
            r = int(c_mid[0] * (1 - t) + c_bot[0] * t)
            g = int(c_mid[1] * (1 - t) + c_bot[1] * t)
            b = int(c_mid[2] * (1 - t) + c_bot[2] * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

def _draw_sun_or_moon(draw: ImageDraw.ImageDraw, page_num: int):
    if page_num == 5:
        mx, my = 640, 120
        for r in range(70, 20, -10):
            draw.ellipse([(mx - r, my - r), (mx + r, my + r)], fill=(255, 245, 180))
        draw.ellipse([(mx - 32, my - 32), (mx + 32, my + 32)], fill=(255, 255, 230))
        for sx, sy in [(120, 90), (220, 60), (340, 110), (480, 70), (580, 150), (700, 80)]:
            draw.text((sx, sy), "✦", fill=(255, 255, 200))
    elif page_num == 4:
        sx, sy = 620, 150
        for r in range(90, 30, -10):
            draw.ellipse([(sx - r, sy - r), (sx + r, sy + r)], fill=(255, 190, 110))
        draw.ellipse([(sx - 38, sy - 38), (sx + 38, sy + 38)], fill=(255, 235, 170))
    else:
        sx, sy = 640, 110
        for r in range(95, 30, -10):
            draw.ellipse([(sx - r, sy - r), (sx + r, sy + r)], fill=(255, 245, 160))
        draw.ellipse([(sx - 40, sy - 40), (sx + 40, sy + 40)], fill=(255, 255, 220))

def _draw_hills_and_terrain(draw: ImageDraw.ImageDraw, width: int, height: int, page_num: int):
    hill_palettes = [
        ((75, 155, 95), (55, 125, 75)),
        ((65, 145, 115), (45, 115, 90)),
        ((45, 140, 85), (30, 110, 65)),
        ((145, 110, 75), (105, 75, 50)),
        ((85, 75, 125), (60, 50, 95)),
    ]
    back_color, front_color = hill_palettes[(page_num - 1) % len(hill_palettes)]
    back_poly = [(0, 500), (140, 430), (300, 390), (460, 440), (620, 380), (768, 430), (768, 768), (0, 768)]
    draw.polygon(back_poly, fill=back_color)
    front_poly = [(0, 570), (180, 500), (380, 470), (560, 510), (768, 480), (768, 768), (0, 768)]
    draw.polygon(front_poly, fill=front_color)

def _draw_stage_elements(draw: ImageDraw.ImageDraw, page_num: int, scene: str):
    low = scene.lower()
    if page_num == 1 or "cottage" in low or "path" in low:
        path_points = [(180, 768), (280, 630), (340, 540), (380, 490), (400, 490), (370, 540), (320, 640), (280, 768)]
        draw.polygon(path_points, fill=(215, 195, 165))
        for x, y, r in [(190, 720, 12), (250, 640, 10), (310, 560, 8), (350, 510, 6)]:
            draw.ellipse([(x - r, y - r // 2), (x + r, y + r // 2)], fill=(185, 165, 135))
        for tx, ty, th in [(90, 370, 140), (660, 350, 160)]:
            draw.rectangle([(tx - 10, ty + 30), (tx + 10, ty + th)], fill=(110, 75, 45))
            draw.ellipse([(tx - 50, ty - 30), (tx + 50, ty + 50)], fill=(45, 130, 70))
        for fx, fy, c in [(80, 620, (255, 105, 140)), (130, 650, (255, 215, 70)), (630, 590, (140, 105, 240)), (690, 630, (255, 140, 90))]:
            draw.ellipse([(fx - 14, fy - 14), (fx + 14, fy + 14)], fill=c)
            draw.ellipse([(fx - 4, fy - 4), (fx + 4, fy + 4)], fill=(255, 255, 230))

    elif page_num == 2 or "door" in low or "arch" in low:
        ax, ay, aw, ah = 540, 320, 160, 240
        draw.rounded_rectangle([(ax - 15, ay - 15), (ax + aw + 15, ay + ah + 20)], radius=25, fill=(120, 125, 130))
        draw.rounded_rectangle([(ax, ay), (ax + aw, ay + ah)], radius=20, fill=(140, 95, 55))
        draw.ellipse([(ax + aw // 2 - 15, ay + ah // 2 - 15), (ax + aw // 2 + 15, ay + ah // 2 + 15)], fill=(255, 215, 80))
        for vy in range(ay - 10, ay + ah, 30):
            draw.ellipse([(ax - 22, vy), (ax - 2, vy + 20)], fill=(40, 135, 65))
            draw.ellipse([(ax + aw + 2, vy), (ax + aw + 22, vy + 20)], fill=(40, 135, 65))
        for gx, gy in [(ax - 40, ay + 60), (ax + aw + 40, ay + 110), (ax + 80, ay - 35)]:
            draw.ellipse([(gx - 8, gy - 8), (gx + 8, gy + 8)], fill=(255, 240, 140))

    elif page_num == 3 or "bridge" in low or "brook" in low or "creek" in low:
        river_points = [(450, 480), (510, 540), (560, 620), (620, 768), (768, 768), (768, 480)]
        draw.polygon(river_points, fill=(65, 155, 220))
        for rx, ry, rw in [(500, 520, 80), (540, 600, 100), (580, 680, 120)]:
            draw.line([(rx, ry), (rx + rw, ry)], fill=(120, 205, 255), width=3)
        bx, by, bw, bh = 480, 510, 130, 40
        draw.rectangle([(bx, by), (bx + bw, by + bh)], fill=(140, 95, 55))
        draw.line([(bx, by - 12), (bx + bw, by - 12)], fill=(100, 65, 35), width=4)
        for px in [bx, bx + bw // 2, bx + bw]:
            draw.line([(px, by - 14), (px, by + bh)], fill=(90, 60, 30), width=4)
        for lx, ly in [(640, 560), (700, 640), (580, 710)]:
            draw.ellipse([(lx - 16, ly - 8), (lx + 16, ly + 8)], fill=(35, 145, 75))
            draw.ellipse([(lx - 5, ly - 5), (lx + 5, ly + 5)], fill=(255, 175, 205))

    elif page_num == 4 or "fountain" in low or "challenge" in low:
        fx, fy, fw, fh = 540, 420, 150, 100
        draw.ellipse([(fx, fy), (fx + fw, fy + 40)], fill=(140, 145, 150))
        draw.ellipse([(fx + 10, fy + 5), (fx + fw - 10, fy + 35)], fill=(80, 175, 235))
        draw.rectangle([(fx + fw // 2 - 15, fy - 60), (fx + fw // 2 + 15, fy + 10)], fill=(120, 125, 130))
        draw.ellipse([(fx + fw // 2 - 35, fy - 75), (fx + fw // 2 + 35, fy - 50)], fill=(150, 155, 160))
        draw.ellipse([(fx + fw // 2 - 25, fy - 70), (fx + fw // 2 + 25, fy - 55)], fill=(90, 195, 255))
        for drop_y in range(fy - 50, fy + 15, 12):
            draw.ellipse([(fx + fw // 2 - 20, drop_y), (fx + fw // 2 - 14, drop_y + 6)], fill=(180, 230, 255))
            draw.ellipse([(fx + fw // 2 + 14, drop_y), (fx + fw // 2 + 20, drop_y + 6)], fill=(180, 230, 255))
        lx, ly = 540 + fw // 2, fy - 95
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            px = lx + int(24 * math.cos(rad))
            py = ly + int(24 * math.sin(rad))
            draw.ellipse([(px - 7, py - 7), (px + 7, py + 7)], fill=(255, 225, 80))
        draw.ellipse([(lx - 9, ly - 9), (lx + 9, ly + 9)], fill=(255, 255, 220))

    else:
        for angle in range(0, 180, 20):
            rad = math.radians(angle)
            ex = 384 + int(500 * math.cos(rad))
            ey = 400 - int(380 * math.sin(rad))
            draw.line([(384, 400), (ex, ey)], fill=(255, 240, 170), width=2)
        for sx, sy in [(160, 280), (280, 230), (520, 210), (620, 270), (384, 180), (220, 370), (560, 350)]:
            draw.ellipse([(sx - 5, sy - 5), (sx + 5, sy + 5)], fill=(255, 255, 220))
            draw.ellipse([(sx - 12, sy - 2), (sx + 12, sy + 2)], fill=(255, 255, 200))
            draw.ellipse([(sx - 2, sy - 12), (sx + 2, sy + 12)], fill=(255, 255, 200))

def _draw_character(draw: ImageDraw.ImageDraw, character: CharacterProfile, cx: int = 260, cy: int = 430):
    spec = character.species_or_type.lower()
    
    if "bunny" in spec or "rabbit" in spec:
        fur_color = (235, 205, 170)
        ear_inner = (245, 175, 185)
        vest_color = (40, 130, 75)
        for ex, rot in [(cx - 18, -10), (cx + 18, 12)]:
            draw.ellipse([(ex - 12, cy - 130), (ex + 12, cy - 45)], fill=fur_color)
            draw.ellipse([(ex - 6, cy - 120), (ex + 6, cy - 55)], fill=ear_inner)
        draw.ellipse([(cx - 38, cy - 20), (cx + 38, cy + 65)], fill=fur_color)
        draw.rectangle([(cx - 26, cy - 5), (cx + 26, cy + 50)], fill=vest_color)
        draw.ellipse([(cx - 3, cy + 12), (cx + 3, cy + 18)], fill=(255, 215, 80))
        draw.ellipse([(cx - 3, cy + 30), (cx + 3, cy + 36)], fill=(255, 215, 80))
        draw.ellipse([(cx - 34, cy - 65), (cx + 34, cy - 10)], fill=fur_color)
        draw.ellipse([(cx - 14, cy - 46), (cx - 4, cy - 34)], fill=(45, 30, 20))
        draw.ellipse([(cx + 4, cy - 46), (cx + 14, cy - 34)], fill=(45, 30, 20))
        draw.ellipse([(cx - 12, cy - 44), (cx - 8, cy - 40)], fill=(255, 255, 255))
        draw.ellipse([(cx + 6, cy - 44), (cx + 10, cy - 40)], fill=(255, 255, 255))
        draw.polygon([(cx - 5, cy - 30), (cx + 5, cy - 30), (cx, cy - 24)], fill=(235, 140, 160))
        draw.arc([(cx - 9, cy - 26), (cx + 9, cy - 18)], start=10, end=170, fill=(160, 80, 80), width=2)
        for wy in [-30, -25]:
            draw.line([(cx - 28, cy + wy), (cx - 8, cy + wy + 2)], fill=(120, 100, 90), width=1)
            draw.line([(cx + 8, cy + wy + 2), (cx + 28, cy + wy)], fill=(120, 100, 90), width=1)
        draw.ellipse([(cx - 28, cy + 55), (cx - 10, cy + 75)], fill=fur_color)
        draw.ellipse([(cx + 10, cy + 55), (cx + 28, cy + 75)], fill=fur_color)

    elif "dragon" in spec:
        scale_color = (95, 195, 155)
        belly_color = (155, 235, 215)
        scarf_color = (235, 185, 50)
        draw.polygon([(cx + 20, cy + 25), (cx + 65, cy + 35), (cx + 30, cy + 45)], fill=scale_color)
        draw.polygon([(cx - 35, cy - 20), (cx - 75, cy - 65), (cx - 45, cy + 10)], fill=(165, 215, 185))
        draw.polygon([(cx + 35, cy - 20), (cx + 75, cy - 65), (cx + 45, cy + 10)], fill=(165, 215, 185))
        draw.ellipse([(cx - 36, cy - 15), (cx + 36, cy + 65)], fill=scale_color)
        draw.ellipse([(cx - 20, cy + 5), (cx + 20, cy + 55)], fill=belly_color)
        draw.rounded_rectangle([(cx - 28, cy - 18), (cx + 28, cy - 4)], radius=8, fill=scarf_color)
        draw.rectangle([(cx + 10, cy - 6), (cx + 22, cy + 25)], fill=scarf_color)
        draw.ellipse([(cx - 32, cy - 60), (cx + 32, cy - 12)], fill=scale_color)
        draw.polygon([(cx - 16, cy - 58), (cx - 24, cy - 80), (cx - 10, cy - 62)], fill=(205, 175, 225))
        draw.polygon([(cx + 16, cy - 58), (cx + 24, cy - 80), (cx + 10, cy - 62)], fill=(205, 175, 225))
        draw.ellipse([(cx - 15, cy - 44), (cx - 3, cy - 30)], fill=(245, 165, 45))
        draw.ellipse([(cx + 3, cy - 44), (cx + 15, cy - 30)], fill=(245, 165, 45))
        draw.ellipse([(cx - 11, cy - 40), (cx - 7, cy - 34)], fill=(30, 20, 15))
        draw.ellipse([(cx + 7, cy - 40), (cx + 11, cy - 34)], fill=(30, 20, 15))
        draw.arc([(cx - 10, cy - 26), (cx + 10, cy - 18)], start=10, end=170, fill=(40, 110, 80), width=2)
        draw.ellipse([(cx - 26, cy + 55), (cx - 8, cy + 72)], fill=scale_color)
        draw.ellipse([(cx + 8, cy + 55), (cx + 26, cy + 72)], fill=scale_color)

    elif "fox" in spec:
        fur_color = (225, 115, 45)
        cream_color = (255, 245, 230)
        sweater_color = (45, 115, 65)
        draw.polygon([(cx + 25, cy + 20), (cx + 80, cy + 10), (cx + 50, cy + 50)], fill=fur_color)
        draw.polygon([(cx + 65, cy + 15), (cx + 80, cy + 10), (cx + 70, cy + 30)], fill=cream_color)
        for ex in [cx - 20, cx + 20]:
            draw.polygon([(ex - 12, cy - 55), (ex, cy - 90), (ex + 12, cy - 55)], fill=fur_color)
            draw.polygon([(ex - 6, cy - 58), (ex, cy - 82), (ex + 6, cy - 58)], fill=(60, 35, 20))
        draw.ellipse([(cx - 34, cy - 15), (cx + 34, cy + 60)], fill=fur_color)
        draw.rectangle([(cx - 24, cy - 5), (cx + 24, cy + 45)], fill=sweater_color)
        draw.ellipse([(cx - 32, cy - 58), (cx + 32, cy - 12)], fill=fur_color)
        draw.polygon([(cx - 22, cy - 25), (cx + 22, cy - 25), (cx, cy - 8)], fill=cream_color)
        draw.ellipse([(cx - 14, cy - 42), (cx - 4, cy - 30)], fill=(45, 30, 20))
        draw.ellipse([(cx + 4, cy - 42), (cx + 14, cy - 30)], fill=(45, 30, 20))
        draw.ellipse([(cx - 4, cy - 22), (cx + 4, cy - 14)], fill=(30, 20, 20))
        draw.arc([(cx - 8, cy - 16), (cx + 8, cy - 10)], start=10, end=170, fill=(120, 60, 40), width=2)
        draw.ellipse([(cx - 24, cy + 52), (cx - 8, cy + 68)], fill=(50, 35, 25))
        draw.ellipse([(cx + 8, cy + 52), (cx + 24, cy + 68)], fill=(50, 35, 25))

    elif "bear" in spec:
        fur_color = (135, 85, 45)
        snout_color = (195, 150, 110)
        shirt_color = (195, 55, 55)
        for ex in [cx - 26, cx + 26]:
            draw.ellipse([(ex - 14, cy - 75), (ex + 14, cy - 47)], fill=fur_color)
            draw.ellipse([(ex - 8, cy - 70), (ex + 8, cy - 52)], fill=snout_color)
        draw.ellipse([(cx - 42, cy - 15), (cx + 42, cy + 70)], fill=fur_color)
        draw.rectangle([(cx - 28, cy - 5), (cx + 28, cy + 55)], fill=shirt_color)
        draw.ellipse([(cx - 36, cy - 60), (cx + 36, cy - 10)], fill=fur_color)
        draw.ellipse([(cx - 18, cy - 32), (cx + 18, cy - 12)], fill=snout_color)
        draw.ellipse([(cx - 15, cy - 44), (cx - 5, cy - 32)], fill=(40, 25, 20))
        draw.ellipse([(cx + 5, cy - 44), (cx + 15, cy - 32)], fill=(40, 25, 20))
        draw.ellipse([(cx - 6, cy - 28), (cx + 6, cy - 18)], fill=(25, 15, 15))
        draw.arc([(cx - 8, cy - 22), (cx + 8, cy - 14)], start=10, end=170, fill=(80, 45, 30), width=2)
        draw.ellipse([(cx - 30, cy + 60), (cx - 10, cy + 78)], fill=fur_color)
        draw.ellipse([(cx + 10, cy + 60), (cx + 30, cy + 78)], fill=fur_color)

    elif "boy" in spec:
        skin_color = (240, 200, 160)
        hair_color = (95, 60, 35)
        jacket_color = (235, 175, 45)
        pants_color = (45, 65, 115)
        draw.ellipse([(cx - 32, cy - 10), (cx + 32, cy + 45)], fill=jacket_color)
        draw.rectangle([(cx - 22, cy + 40), (cx - 6, cy + 75)], fill=pants_color)
        draw.rectangle([(cx + 6, cy + 40), (cx + 22, cy + 75)], fill=pants_color)
        draw.ellipse([(cx - 26, cy + 70), (cx - 4, cy + 85)], fill=(110, 70, 40))
        draw.ellipse([(cx + 4, cy + 70), (cx + 26, cy + 85)], fill=(110, 70, 40))
        draw.ellipse([(cx - 28, cy - 58), (cx + 28, cy - 10)], fill=skin_color)
        for hx, hy in [(cx - 25, cy - 55), (cx - 15, cy - 65), (cx, cy - 68), (cx + 15, cy - 65), (cx + 25, cy - 55)]:
            draw.ellipse([(hx - 12, hy - 12), (hx + 12, hy + 12)], fill=hair_color)
        draw.ellipse([(cx - 14, cy - 40), (cx - 4, cy - 28)], fill=(45, 30, 25))
        draw.ellipse([(cx + 4, cy - 40), (cx + 14, cy - 28)], fill=(45, 30, 25))
        draw.ellipse([(cx - 12, cy - 38), (cx - 8, cy - 34)], fill=(255, 255, 255))
        draw.ellipse([(cx + 6, cy - 38), (cx + 10, cy - 34)], fill=(255, 255, 255))
        for fx in [cx - 8, cx - 4, cx + 4, cx + 8]:
            draw.ellipse([(fx - 1, cy - 28), (fx + 1, cy - 26)], fill=(195, 140, 100))
        draw.arc([(cx - 10, cy - 24), (cx + 10, cy - 15)], start=10, end=170, fill=(180, 80, 80), width=2)

    else:
        skin_color = (245, 205, 175)
        hair_color = (75, 45, 30)
        ribbon_color = (255, 215, 60)
        dress_color = (75, 135, 205)
        for px, py in [(cx - 36, cy - 38), (cx + 36, cy - 38)]:
            draw.ellipse([(px - 14, py - 18), (px + 14, py + 26)], fill=hair_color)
            draw.ellipse([(px - 6, py - 12), (px + 6, py + 2)], fill=ribbon_color)
        draw.ellipse([(cx - 30, cy - 10), (cx + 30, cy + 48)], fill=dress_color)
        draw.rectangle([(cx - 20, cy + 42), (cx - 6, cy + 74)], fill=(45, 85, 140))
        draw.rectangle([(cx + 6, cy + 42), (cx + 20, cy + 74)], fill=(45, 85, 140))
        draw.ellipse([(cx - 24, cy + 70), (cx - 4, cy + 84)], fill=(205, 55, 65))
        draw.ellipse([(cx + 4, cy + 70), (cx + 24, cy + 84)], fill=(205, 55, 65))
        draw.ellipse([(cx - 28, cy - 58), (cx + 28, cy - 10)], fill=skin_color)
        draw.ellipse([(cx - 26, cy - 65), (cx + 26, cy - 40)], fill=hair_color)
        draw.ellipse([(cx - 14, cy - 40), (cx - 4, cy - 28)], fill=(35, 75, 50))
        draw.ellipse([(cx + 4, cy - 40), (cx + 14, cy - 28)], fill=(35, 75, 50))
        draw.ellipse([(cx - 12, cy - 38), (cx - 8, cy - 34)], fill=(255, 255, 255))
        draw.ellipse([(cx + 6, cy - 38), (cx + 10, cy - 34)], fill=(255, 255, 255))
        draw.ellipse([(cx - 20, cy - 26), (cx - 12, cy - 20)], fill=(245, 160, 160))
        draw.ellipse([(cx + 12, cy - 26), (cx + 20, cy - 20)], fill=(245, 160, 160))
        draw.arc([(cx - 9, cy - 23), (cx + 9, cy - 15)], start=10, end=170, fill=(185, 75, 75), width=2)

def create_offline_canvas(character: CharacterProfile, page_num: int, title: str, output_path: str, scene: str = ""):
    width, height = 768, 768
    img = Image.new("RGB", (width, height), color=(245, 240, 230))
    draw = ImageDraw.Draw(img)
    
    _draw_sky(draw, width, height, page_num)
    _draw_sun_or_moon(draw, page_num)
    _draw_hills_and_terrain(draw, width, height, page_num)
    _draw_stage_elements(draw, page_num, scene)
    _draw_character(draw, character, cx=260, cy=460)
    
    badge_rect = [(24, 24), (320, 64)]
    draw.rounded_rectangle(badge_rect, radius=12, fill=(20, 25, 35, 180))
    clean_title = title.upper()[:24] if title else f"PAGE {page_num}"
    draw.text((38, 36), f"PAGE {page_num}  •  {clean_title}", fill=(255, 255, 255))
    
    img = img.filter(ImageFilter.SMOOTH)
    img.save(output_path, "JPEG", quality=92)

def generate_illustration(
    scene_description: str,
    character: CharacterProfile,
    page_number: int,
    page_title: str,
    output_path: str,
    story_id: str,
    api_key: Optional[str] = None,
) -> Dict:
    full_prompt = build_scene_prompt(character, scene_description)
    active_key = (api_key or os.getenv("OPEN_ROUTER_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")).strip()
    openai_error = None

    if active_key and not active_key.startswith("sk-or-"):
        try:
            client = OpenAI(api_key=active_key, timeout=45.0)
            res = client.images.generate(
                model="dall-e-3",
                prompt=full_prompt[:1000],
                size="1024x1024",
                quality="standard",
                n=1
            )
            img_url = res.data[0].url
            if _fetch_url_to_file(img_url, output_path, timeout=30):
                return {
                    "success": True,
                    "image_path": output_path,
                    "provider": "OpenAI DALL-E 3",
                    "page_number": page_number,
                    "error": None,
                    "prompt_used": full_prompt
                }
            else:
                openai_error = "OpenAI image download timed out"
        except Exception as e:
            openai_error = str(e)
    else:
        openai_error = "OpenRouter mode active (uses Visual Engine for illustration)"

    if _try_pollinations(scene_description, character, page_number, story_id, output_path):
        return {
            "success": True,
            "image_path": output_path,
            "provider": "AI Visual Engine (Pollinations Flux)",
            "page_number": page_number,
            "error": None,
            "prompt_used": scene_description
        }

    create_offline_canvas(character, page_number, page_title, output_path, scene_description)
    return {
        "success": True,
        "image_path": output_path,
        "provider": "Storybook Canvas Engine",
        "page_number": page_number,
        "error": openai_error,
        "prompt_used": full_prompt
    }

def generate_all_story_illustrations(
    pages: List,
    character: CharacterProfile,
    output_dir: str,
    story_id: str,
    api_key: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> List[Dict]:
    os.makedirs(output_dir, exist_ok=True)
    results = []

    for idx, page in enumerate(pages):
        page_num = page.page_number
        out_file = os.path.join(output_dir, f"page_{page_num}.jpg")
        if progress_callback:
            progress_callback(idx + 1, len(pages), f"Illustrating Page {page_num}: {page.title}")

        res = generate_illustration(
            scene_description=page.scene_description,
            character=character,
            page_number=page_num,
            page_title=page.title,
            output_path=out_file,
            story_id=story_id,
            api_key=api_key
        )
        results.append(res)
        if idx < len(pages) - 1:
            time.sleep(0.5)

    return results
