import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io, os, requests, math, time
import numpy as np
from moviepy.editor import VideoClip

# ============================================================================
# SETTINGS & PREMIUM THEMES
# ============================================================================
st.set_page_config(page_title="Still Mind Full Studio", page_icon="✝️", layout="wide")

COLORS = {
    "Still Mind (Green/Blue)": {
        "bg": [(10, 30, 50, 255), (20, 50, 80, 255)],
        "accent": (76, 175, 80, 255),
        "text": (255, 255, 255, 255),
        "glow": (76, 175, 80, 150)
    }
}

BIBLE_BOOKS = ["Psalm", "Matthew", "John", "Romans", "Ephesians", "Philippians", "James", "Proverbs", "Isaiah", "Lamentations"]

# ============================================================================
# PREMIUM DECORATIONS (GLOW & BRACKETS)
# ============================================================================
def draw_premium_decorations(draw, x1, y1, x2, y2, accent_color, t=0):
    """Draws the rectangle with pulsing corner brackets and glow layers."""
    # 1. Main Semi-Transparent Box
    draw.rectangle([x1, y1, x2, y2], fill=(0, 0, 0, 180))
    
    # 2. Pulsing Glow Calculation (Breathes 3 times in 6 seconds)
    pulse = 0.6 + 0.4 * abs(math.sin(t * 2)) 
    glow_color = accent_color[:3] + (int(120 * pulse),)
    
    b_len = 50 
    b_width = 4
    
    def draw_bracket(ax, ay, bx, by, cx, cy, width, color):
        draw.line([(ax, ay), (bx, by)], fill=color, width=width)
        draw.line([(bx, by), (cx, cy)], fill=color, width=width)

    # 3. Layered Glow Brackets
    for layer in range(3, 0, -1):
        current_width = b_width + (layer * 5)
        current_color = glow_color if layer > 1 else accent_color
        
        # Corners
        draw_bracket(x1, y1 + b_len, x1, y1, x1 + b_len, y1, current_width, current_color)
        draw_bracket(x2 - b_len, y1, x2, y1, x2, y1 + b_len, current_width, current_color)
        draw_bracket(x1, y2 - b_len, x1, y2, x1 + b_len, y2, current_width, current_color)
        draw_bracket(x2 - b_len, y2, x2, y2, x2, y2 - b_len, current_width, current_color)

    # 4. Thin Interior Frame
    draw.rectangle([x1+15, y1+15, x2-15, y2-15], outline=accent_color[:3]+(40,), width=1)

# ============================================================================
# TYPEWRITER ANIMATION LOGIC
# ============================================================================
def get_animated_text(full_text, t, duration=4.0):
    """Returns a substring of text based on time 't'."""
    # duration = how many seconds to complete typing
    char_count = len(full_text)
    progress = min(1.0, t / duration)
    visible_chars = int(char_count * progress)
    return full_text[:visible_chars]

# ============================================================================
# UTILITIES & FONTS
# ============================================================================
@st.cache_data(ttl=3600)
def fetch_verse(book, chapter, verse):
    try:
        url = f"https://bible-api.com/{book}+{chapter}:{verse}"
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            return r.json().get("text", "").strip().replace("\n", " ")
    except: pass
    return "The Lord is my shepherd; I shall not want."

def load_font_safe(size, bold=False):
    try:
        # Standard Streamlit Cloud / Linux paths
        paths = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"]
        for p in paths:
            if os.path.exists(p): return ImageFont.truetype(p, size)
    except: pass
    return ImageFont.load_default()

def wrap_and_size(text, target_size, max_w, max_h):
    """Calculates lines and final font size for wrapping."""
    for size in range(target_size, 30, -5):
        font = load_font_safe(size)
        lines, current = [], ""
        for word in text.split():
            test = f"{current} {word}".strip()
            if font.getbbox(test)[2] - font.getbbox(test)[0] <= max_w:
                current = test
            else:
                lines.append(current); current = word
        lines.append(current)
        if (len(lines) * size * 1.5) <= max_h:
            return size, lines, font
    return 30, [text], load_font_safe(30)

# ============================================================================
# CORE COMPOSITION ENGINE
# ============================================================================
def create_frame(w, h, book, chapter, verse, hook, colors, t=0, is_video=False):
    img = Image.new("RGBA", (w, h))
    draw = ImageDraw.Draw(img)
    c1, c2 = colors["bg"]
    acc = colors["accent"]

    # 1. Background Gradient
    for y in range(h):
        ratio = (y / h) + (math.sin(t * 0.4) * 0.04)
        ratio = max(0, min(1, ratio))
        color = tuple(int((1-ratio)*c1[i] + ratio*c2[i]) for i in range(4))
        draw.line([(0, y), (w, y)], fill=color)

    # 2. Decorations: Drifting Dust
    for i in range(15):
        px = (w * (0.5 + 0.45 * math.sin(t * 0.3 + i)))
        py = (h * (0.5 + 0.45 * math.cos(t * 0.2 + i)))
        size = 2 + math.sin(t + i)
        draw.ellipse([px-size, py-size, px+size, py+size], fill=acc[:3]+(80,))

    # 3. Text Logic
    raw_verse = fetch_verse(book, chapter, verse)
    
    # If video, apply typewriter effect to the raw text before wrapping
    display_text = get_animated_text(raw_verse, t) if is_video else raw_verse
    
    # We use the full raw_verse to pre-calculate the container box size 
    # so the box doesn't jump as the text types in.
    v_size, _, v_font = wrap_and_size(raw_verse, 100, w-300, h*0.45)
    
    # Now wrap the currently visible display_text
    animated_lines = []
    current_line = ""
    for word in display_text.split():
        test = f"{current_line} {word}".strip()
        if v_font.getbbox(test)[2] - v_font.getbbox(test)[0] <= (w-300):
            current_line = test
        else:
            animated_lines.append(current_line); current_line = word
    animated_lines.append(current_line)

    line_h = v_size * 1.5
    # Box height is static based on the FINAL full verse
    final_v_size, final_v_lines, _ = wrap_and_size(raw_verse, 100, w-300, h*0.45)
    box_h = (len(final_v_lines) * line_h) + 140
    box_y = (h - box_h) // 2
    
    # 4. Draw Premium Pulsing Box
    draw_premium_decorations(draw, 100, box_y, w-100, box_y + box_h, acc, t)

    # 5. Draw Animated Verse Text
    curr_y = box_y + 80
    for line in animated_lines:
        tw = v_font.getbbox(line)[2] - v_font.getbbox(line)[0]
        draw.text(((w-tw)//2, curr_y), line, font=v_font, fill=(255,255,255))
        curr_y += line_h

    # Hook & Reference
    h_font = load_font_safe(75, True)
    r_font = load_font_safe(45, True)
    
    if hook:
        hw = h_font.getbbox(hook)[2] - h_font.getbbox(hook)[0]
        draw.text(((w-hw)//2, box_y - 130), hook.upper(), font=h_font, fill=acc)
        
    ref = f"— {book} {chapter}:{verse} —"
    rw = r_font.getbbox(ref)[2] - r_font.getbbox(ref)[0]
    # Reference only appears after typewriter is nearly done
    ref_opacity = 255 if not is_video else int(max(0, min(1, (t-3.5)/0.5)) * 255)
    draw.text(((w-rw)//2, box_y + box_h + 40), ref, font=r_font, fill=acc[:3]+(ref_opacity,))

    return img

# ============================================================================
# STREAMLIT UI
# ============================================================================
with st.sidebar:
    st.title("Studio Controls")
    aspect = st.selectbox("Format", ["TikTok/Reel", "Square"])
    hook = st.text_input("Top Hook", "Rest Your Soul")
    
    st.divider()
    sel_book = st.selectbox("Bible Book", BIBLE_BOOKS)
    col_c, col_v = st.columns(2)
    sel_chapter = col_c.number_input("Chapter", 1, 150, 46)
    sel_verse = col_v.number_input("Verse", 1, 176, 1)

W, H = (1080, 1920) if aspect == "TikTok/Reel" else (1080, 1080)
current_theme = COLORS["Still Mind (Green/Blue)"]

# Display Preview (Static)
st.subheader("Design Preview")
preview_img = create_frame(W, H, sel_book, sel_chapter, sel_verse, hook, current_theme, t=0, is_video=False)
st.image(preview_img, use_container_width=True)

col_render, col_save = st.columns(2)

with col_render:
    if st.button("🎬 Render Full Animated Video", use_container_width=True):
        with st.spinner("Processing Typewriter & Glow Layers..."):
            def make_frame(t):
                f = create_frame(W, H, sel_book, sel_chapter, sel_verse, hook, current_theme, t, is_video=True)
                return np.array(f.convert("RGB"))
            
            # 6 second video, typewriter finishes at 4s, ref fades in at 4s
            clip = VideoClip(make_frame, duration=6).set_fps(15)
            clip.write_videofile("still_mind_premium.mp4", codec="libx264", logger=None)
            st.video("still_mind_premium.mp4")

with col_save:
    buf = io.BytesIO()
    preview_img.save(buf, format='PNG')
    st.download_button("📥 Download Static Image", buf.getvalue(), "verse.png", use_container_width=True)
