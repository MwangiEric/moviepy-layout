import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io, os, requests, math, time
import numpy as np
from moviepy.editor import VideoClip

# ============================================================================
# MASTER THEME (Green, Navy Blue, White, Grey)
# ============================================================================
st.set_page_config(page_title="Still Mind Studio", layout="wide")

THEME = {
    "navy": (10, 25, 45, 255),       # Deep Navy
    "grey_dawn": (100, 110, 120, 255),# Dawn Grey
    "forest": (46, 125, 50, 255),    # Deep Green
    "white": (255, 255, 255, 255),
    "river": (20, 40, 70, 180)       # Translucent Navy
}

# ============================================================================
# ANIMATION ENGINES
# ============================================================================

def draw_nature_elements(draw, w, h, t):
    """Draws Birds and their reflections."""
    if t < 1.0: return
    
    for i in range(5):
        # Flying Path
        bx = (t * 240) + (i * 70) - 150
        by = h * 0.22 + (math.sin(t + i) * 20)
        
        # Wing Flap
        flap = math.sin(t * 14 + i) * 12
        
        # 1. Sky Bird (White)
        draw.line([(bx, by), (bx - 15, by - 8 + flap)], fill=(255,255,255,200), width=2)
        draw.line([(bx, by), (bx + 15, by - 8 + flap)], fill=(255,255,255,200), width=2)
        
        # 2. River Reflection (Greyish-White, Shimmering)
        ref_y = h - by + 200 # Reflected position
        if ref_y > h * 0.6: # Only draw if on the water
            shimmer = math.sin(t * 20 + i) * 5
            draw.line([(bx + shimmer, ref_y), (bx - 12 + shimmer, ref_y + 5 - flap/2)], fill=(200,200,200,60), width=1)
            draw.line([(bx + shimmer, ref_y), (bx + 12 + shimmer, ref_y + 5 - flap/2)], fill=(200,200,200,60), width=1)

def draw_recursive_tree(draw, x, y, angle, length, depth, t, max_depth, color):
    """Procedural Green Tree Growth."""
    trigger = max(0, min(1, (t - (max_depth - depth) * 0.3) / 1.8))
    if trigger <= 0: return
    
    # Wind sway logic
    sway = math.sin(t * 1.5 + depth) * (0.1 / max(1, depth-1))
    curr_len = length * trigger
    
    x2 = x + int(math.cos(angle + sway) * curr_len)
    y2 = y + int(math.sin(angle + sway) * curr_len)
    
    # Use grey for trunk (bottom), green for leaves (top)
    color_shift = THEME["grey_dawn"] if depth > 4 else color
    draw.line([(x, y), (x2, y2)], fill=color_shift[:3] + (int(220 * trigger),), width=depth*2)
    
    draw_recursive_tree(draw, x2, y2, angle - 0.4, length * 0.72, depth - 1, t, max_depth, color)
    draw_recursive_tree(draw, x2, y2, angle + 0.4, length * 0.72, depth - 1, t, max_depth, color)

# ============================================================================
# MAIN COMPOSITOR
# ============================================================================

def create_master_frame(w, h, book, chapter, verse_num, hook, t=0, is_video=False):
    # 1. Background Interpolation (Navy to Grey-Green)
    prog = t / 6.0
    bg_color = tuple(int(THEME["navy"][i] + (THEME["grey_dawn"][i] - THEME["navy"][i]) * prog) for i in range(3))
    img = Image.new("RGBA", (w, h), bg_color)
    draw = ImageDraw.Draw(img)

    # 2. Sunrise / Glow
    sun_y = h * 0.65 - (prog * 320)
    for r in range(120, 0, -20):
        alpha = int(60 * (1 - r/120))
        draw.ellipse([w//2-r, sun_y-r, w//2+r, sun_y+r], fill=(255, 255, 255, alpha))

    # 3. Flowing Navy River
    river_pts = []
    for ys in range(int(h * 0.6), h, 10):
        perspective = (ys - h*0.6) * 1.3
        drift = w//2 + math.sin(ys * 0.012 - t * 4) * 50
        river_pts.append((drift - perspective, ys))
    
    # Close polygon
    right_pts = [(w//2 + math.sin(ys * 0.012 - t * 4) * 50 + (ys - h*0.6) * 1.3, ys) for ys in range(int(h * 0.6), h, 10)]
    draw.polygon(river_pts + right_pts[::-1], fill=THEME["river"])

    # 4. Birds & Reflections
    draw_nature_elements(draw, w, h, t)

    # 5. Growing Green Trees
    draw_recursive_tree(draw, 200, h-20, -math.pi/2, 170, 8, t, 8, THEME["forest"])
    draw_recursive_tree(draw, w-200, h-20, -math.pi/2, 150, 7, t, 7, THEME["forest"])

    # 6. FROSTED GLASS BOX (Grey/Transparent)
    bx_w, bx_h = 900, 550
    x1, y1 = (w - bx_w)//2, (h - bx_h)//2 - 100
    x2, y2 = x1 + bx_w, y1 + bx_h
    
    # Glass blur
    glass = img.crop((x1, y1, x2, y2)).filter(ImageFilter.GaussianBlur(15))
    img.paste(glass, (x1, y1))
    draw.rectangle([x1, y1, x2, y2], fill=(40, 45, 50, 160), outline=(255,255,255,40), width=2)

    # 7. Typewriter Text (White)
    verse_text = "The Lord is my shepherd; I shall not want. He makes me lie down in green pastures."
    type_prog = min(1.0, t / 4.5) if is_video else 1.0
    visible = verse_text[:int(len(verse_text) * type_prog)]
    
    try: font = ImageFont.truetype("DejaVuSans.ttf", 48)
    except: font = ImageFont.load_default(size=45)

    # Wrapping
    lines, curr = [], ""
    for word in visible.split():
        if font.getbbox(curr + " " + word)[2] < bx_w - 100: curr += " " + word
        else: lines.append(curr); curr = word
    lines.append(curr)

    curr_y = y1 + 80
    for line in lines:
        draw.text((x1 + 50, curr_y), line, font=font, fill=(255,255,255,255))
        curr_y += 70

    # Header Hook
    draw.text((x1, y1 - 90), hook.upper(), font=font, fill=THEME["white"])

    return img

# ============================================================================
# STREAMLIT UI
# ============================================================================
st.sidebar.title("Still Mind: Master Nature")
hook = st.sidebar.text_input("Hook", "Morning Peace")
t_scrub = st.slider("Time Scrub", 0.0, 6.0, 0.0)

W, H = 1080, 1920 # Vertical TikTok Size

# Live Preview
frame = create_master_frame(W, H, "Psalm", 23, 1, hook, t=t_scrub)
st.image(frame, use_container_width=True)

if st.button("🎬 Render Final Meditation"):
    with st.spinner("Simulating river ripples and bird reflections..."):
        def make_frame(t):
            return np.array(create_master_frame(W, H, "Ps", 23, 1, hook, t, 6, True).convert("RGB"))
        
        clip = VideoClip(make_frame, duration=6).set_fps(15)
        clip.write_videofile("still_mind_final.mp4", codec="libx264", logger=None)
        st.video("still_mind_final.mp4")
