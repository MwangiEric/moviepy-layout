import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io, os, math, json
import numpy as np
from moviepy.editor import VideoClip
import requests

st.set_page_config(page_title="Still Mind", page_icon="✨", layout="centered")

# Flat Design Themes
THEMES = {
    "Purple Minimal": {
        "bg": (88, 86, 214),
        "panel": (51, 65, 85),
        "text": (248, 250, 252),
        "accent": (255, 107, 107)
    },
    "Ocean Blue": {
        "bg": (34, 211, 238),
        "panel": (30, 41, 59),
        "text": (240, 249, 255),
        "accent": (251, 191, 36)
    },
    "Forest Green": {
        "bg": (52, 211, 153),
        "panel": (34, 60, 50),
        "text": (236, 253, 245),
        "accent": (251, 191, 36)
    },
    "Sunset Orange": {
        "bg": (251, 146, 60),
        "panel": (55, 65, 81),
        "text": (254, 252, 232),
        "accent": (236, 72, 153)
    }
}

BIBLE_BOOKS = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", 
               "Judges", "Ruth", "1 Samuel", "2 Samuel", "1 Kings", "2 Kings", 
               "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther", "Job", 
               "Psalm", "Proverbs", "Ecclesiastes", "Song of Solomon", "Isaiah", 
               "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", 
               "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", 
               "Haggai", "Zechariah", "Malachi", "Matthew", "Mark", "Luke", "John", 
               "Acts", "Romans", "1 Corinthians", "2 Corinthians", "Galatians", 
               "Ephesians", "Philippians", "Colossians", "1 Thessalonians", 
               "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus", "Philemon", 
               "Hebrews", "James", "1 Peter", "2 Peter", "1 John", "2 John", 
               "3 John", "Jude", "Revelation"]

def load_font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                pass
    return ImageFont.load_default()

def wrap_text(text, font, max_w):
    words = text.split()
    lines = []
    current = []
    
    for word in words:
        test = ' '.join(current + [word])
        try:
            w = font.getbbox(test)[2]
        except:
            w = font.getsize(test)[0]
        
        if w <= max_w:
            current.append(word)
        else:
            if current:
                lines.append(' '.join(current))
            current = [word]
    
    if current:
        lines.append(' '.join(current))
    
    return lines

def draw_circle_pattern(draw, w, h, color, count=8):
    for i in range(count):
        angle = (i / count) * (2 * math.pi)
        x = w/2 + (w * 0.4) * math.cos(angle)
        y = h/2 + (h * 0.35) * math.sin(angle)
        size = 60 + (i % 3) * 20
        
        for j in range(3):
            s = size * (1 + j * 0.3)
            alpha = int(40 / (j + 1))
            c = color + (alpha,)
            draw.ellipse([x-s, y-s, x+s, y+s], fill=c)

def create_flat_design(w, h, theme, book, chapter, verse, verse_text):
    colors = THEMES[theme]
    
    # Base
    img = Image.new("RGB", (w, h), colors["bg"])
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Pattern
    draw_circle_pattern(draw, w, h, colors["panel"][:3], 12)
    
    # Panel
    pw, ph = int(w * 0.8), int(h * 0.6)
    px, py = (w - pw) // 2, (h - ph) // 2
    
    draw.rounded_rectangle([px, py, px + pw, py + ph], 
                          radius=20, fill=colors["panel"] + (250,))
    
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)
    
    # Fonts
    title_font = load_font(int(h * 0.05), True)
    verse_font = load_font(int(h * 0.032), False)
    ref_font = load_font(int(h * 0.038), True)
    
    # Title
    title = "BE STILL"
    try:
        tw = title_font.getbbox(title)[2]
    except:
        tw = title_font.getsize(title)[0]
    
    tx = px + (pw - tw) // 2
    ty = py - int(h * 0.08)
    draw.text((tx, ty), title, font=title_font, fill=colors["accent"])
    
    # Verse
    lines = wrap_text(verse_text, verse_font, pw - int(w * 0.1))
    
    line_h = int(h * 0.045)
    text_y = py + int(ph * 0.3)
    
    for line in lines[:4]:
        try:
            lw = verse_font.getbbox(line)[2]
        except:
            lw = verse_font.getsize(line)[0]
        
        lx = px + (pw - lw) // 2
        draw.text((lx, text_y), line, font=verse_font, fill=colors["text"])
        text_y += line_h
    
    # Reference
    ref = f"{book} {chapter}:{verse}"
    try:
        rw = ref_font.getbbox(ref)[2]
        rh = ref_font.getbbox(ref)[3]
    except:
        rw, rh = ref_font.getsize(ref)
    
    rx = px + pw - rw - 30
    ry = py + ph + int(h * 0.05)
    
    pad = 15
    draw.rounded_rectangle([rx - pad, ry - pad//2, rx + rw + pad, ry + rh + pad//2],
                          radius=20, fill=colors["accent"])
    draw.text((rx, ry), ref, font=ref_font, fill=colors["bg"])
    
    return img

def create_video(w, h, theme, book, chapter, verse, verse_text):
    def make_frame(t):
        img = create_flat_design(w, h, theme, book, chapter, verse, verse_text)
        
        # Simple fade in
        if t < 1:
            arr = np.array(img).astype(float)
            arr = (arr * t).astype('uint8')
            return arr
        
        return np.array(img)
    
    clip = VideoClip(make_frame, duration=6)
    clip = clip.set_fps(30)
    
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as f:
        temp = f.name
    
    try:
        clip.write_videofile(temp, fps=30, codec="libx264", 
                           verbose=False, logger=None)
        with open(temp, 'rb') as f:
            return f.read()
    finally:
        if os.path.exists(temp):
            os.unlink(temp)

def generate_ready_post(book, chapter, verse, verse_text):
    """Generate ready-to-use social media post using Groq AI."""
    try:
        api_key = st.secrets.get("groq_key", "")
        if not api_key:
            return None, "Groq API key not found in secrets"
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""Create a compelling social media post for this Bible verse:

{book} {chapter}:{verse}
"{verse_text}"

Write:
1. A catchy hook/caption (2-3 sentences max)
2. 3-5 relevant hashtags

Keep it inspirational, relatable, and engaging. Make people want to share it."""

        data = {
            "model": "mixtral-8x7b-32768",
            "messages": [
                {"role": "system", "content": "You are a social media expert specializing in faith-based content that goes viral."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            return content, None
        else:
            return None, f"API Error: {response.status_code}"
            
    except Exception as e:
        return None, str(e)

# UI
st.title("Still Mind")

col1, col2, col3 = st.columns(3)

with col1:
    book = st.selectbox("Book", BIBLE_BOOKS, index=18)

with col2:
    chapter = st.number_input("Chapter", 1, 150, 46)

with col3:
    verse = st.number_input("Verse", 1, 176, 10)

theme = st.selectbox("Theme", list(THEMES.keys()))

verse_text = st.text_area("Verse Text", 
    "Be still, and know that I am God. I will be exalted among the nations, I will be exalted in the earth.",
    height=100)

col_a, col_b, col_c = st.columns(3)

with col_a:
    size = st.selectbox("Size", ["Instagram Post (1080x1080)", "Instagram Story (1080x1920)", 
                                  "YouTube (1920x1080)"])

w, h = (1080, 1080) if "Post" in size else (1080, 1920) if "Story" in size else (1920, 1080)

st.divider()

col_gen1, col_gen2, col_gen3 = st.columns(3)

with col_gen1:
    if st.button("Generate Image", type="primary"):
        with st.spinner("Generating..."):
            img = create_flat_design(w, h, theme, book, chapter, verse, verse_text)
            
            st.image(img, width=600)
            
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            
            st.download_button("Download PNG", buf.getvalue(), 
                             f"{book}_{chapter}_{verse}.png", "image/png")

with col_gen2:
    if st.button("Generate Video"):
        with st.spinner("Rendering..."):
            video = create_video(w, h, theme, book, chapter, verse, verse_text)
            
            st.video(video)
            
            st.download_button("Download MP4", video, 
                             f"{book}_{chapter}_{verse}.mp4", "video/mp4")

with col_gen3:
    if st.button("Ready Post (AI)"):
        with st.spinner("Creating post..."):
            post, error = generate_ready_post(book, chapter, verse, verse_text)
            
            if post:
                st.success("Post ready!")
                st.text_area("Copy this:", post, height=200)
            else:
                st.error(f"Error: {error}")