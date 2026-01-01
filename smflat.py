import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io, os, math
import numpy as np
from moviepy.editor import VideoClip
import requests

st.set_page_config(page_title="Still Mind", page_icon="✨", layout="centered")

# Green, Navy, White, Grey theme
COLORS = {
    "bg": (26, 54, 93),      # Navy Blue
    "panel": (52, 73, 94),   # Grey Blue
    "text": (248, 250, 252), # White
    "accent": (46, 204, 113), # Green
    "grey": (149, 165, 166)  # Grey
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

# Bible verse database
VERSES = {
    ("Psalm", 46, 10): "Be still, and know that I am God. I will be exalted among the nations, I will be exalted in the earth.",
    ("John", 14, 27): "Peace I leave with you; my peace I give you. I do not give to you as the world gives. Do not let your hearts be troubled and do not be afraid.",
    ("Philippians", 4, 6): "Do not be anxious about anything, but in every situation, by prayer and petition, with thanksgiving, present your requests to God.",
    ("Matthew", 11, 28): "Come to me, all you who are weary and burdened, and I will give you rest.",
    ("Isaiah", 41, 10): "So do not fear, for I am with you; do not be dismayed, for I am your God. I will strengthen you and help you.",
    ("Proverbs", 3, 5): "Trust in the Lord with all your heart and lean not on your own understanding.",
    ("Romans", 8, 28): "And we know that in all things God works for the good of those who love him, who have been called according to his purpose.",
    ("Jeremiah", 29, 11): "For I know the plans I have for you, declares the Lord, plans to prosper you and not to harm you, plans to give you hope and a future.",
}

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

def draw_circle_pattern(draw, w, h, count=8):
    for i in range(count):
        angle = (i / count) * (2 * math.pi)
        x = w/2 + (w * 0.4) * math.cos(angle)
        y = h/2 + (h * 0.35) * math.sin(angle)
        size = 60 + (i % 3) * 20
        
        for j in range(3):
            s = size * (1 + j * 0.3)
            alpha = int(40 / (j + 1))
            c = COLORS["panel"] + (alpha,)
            draw.ellipse([x-s, y-s, x+s, y+s], fill=c)

def create_flat_design(w, h, book, chapter, verse, verse_text, t=0, is_video=False):
    # Base
    img = Image.new("RGB", (w, h), COLORS["bg"])
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Pattern
    draw_circle_pattern(draw, w, h, 12)
    
    # Panel
    pw, ph = int(w * 0.8), int(h * 0.6)
    px, py = (w - pw) // 2, (h - ph) // 2
    
    draw.rounded_rectangle([px, py, px + pw, py + ph], 
                          radius=20, fill=COLORS["panel"] + (250,))
    
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
    draw.text((tx, ty), title, font=title_font, fill=COLORS["accent"])
    
    # Typewriter effect for video
    if is_video:
        chars_visible = int(len(verse_text) * min(1.0, t / 4.0))
        display_text = verse_text[:chars_visible]
    else:
        display_text = verse_text
    
    # Verse
    lines = wrap_text(display_text, verse_font, pw - int(w * 0.1))
    
    line_h = int(h * 0.045)
    text_y = py + int(ph * 0.3)
    
    for line in lines[:4]:
        try:
            lw = verse_font.getbbox(line)[2]
        except:
            lw = verse_font.getsize(line)[0]
        
        lx = px + (pw - lw) // 2
        draw.text((lx, text_y), line, font=verse_font, fill=COLORS["text"])
        text_y += line_h
    
    # Reference (fade in after typewriter)
    ref_alpha = 255 if not is_video else int(255 * max(0, min(1, (t - 4) / 1)))
    
    if ref_alpha > 0:
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
                              radius=20, fill=COLORS["accent"])
        draw.text((rx, ry), ref, font=ref_font, fill=COLORS["bg"])
    
    return img

def create_video(w, h, book, chapter, verse, verse_text):
    def make_frame(t):
        return np.array(create_flat_design(w, h, book, chapter, verse, verse_text, t, True))
    
    clip = VideoClip(make_frame, duration=6)
    clip = clip.set_fps(15)
    
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as f:
        temp = f.name
    
    try:
        clip.write_videofile(temp, fps=15, codec="libx264", 
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
            "model": "llama3-8b-8192",
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
            return None, f"API Error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return None, str(e)

def get_verse_text(book, chapter, verse):
    """Get verse text from database or return default."""
    key = (book, chapter, verse)
    return VERSES.get(key, "Enter your verse text here...")

# UI
st.title("Still Mind")

col1, col2, col3 = st.columns(3)

with col1:
    book = st.selectbox("Book", BIBLE_BOOKS, index=18)

with col2:
    chapter = st.number_input("Chapter", 1, 150, 46, key="chapter_input")

with col3:
    verse = st.number_input("Verse", 1, 176, 10, key="verse_input")

# Auto-update verse text when selection changes
verse_text = get_verse_text(book, chapter, verse)
verse_text = st.text_area("Verse Text", verse_text, height=100, key="verse_text_area")

size = st.selectbox("Size", ["Instagram Post (1080x1080)", "Instagram Story (1080x1920)", 
                              "YouTube (1920x1080)"])

w, h = (1080, 1080) if "Post" in size else (1080, 1920) if "Story" in size else (1920, 1080)

st.divider()

col_gen1, col_gen2, col_gen3 = st.columns(3)

with col_gen1:
    if st.button("Generate Image", type="primary"):
        with st.spinner("Generating..."):
            img = create_flat_design(w, h, book, chapter, verse, verse_text)
            
            st.image(img, width=600)
            
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            
            st.download_button("Download PNG", buf.getvalue(), 
                             f"{book}_{chapter}_{verse}.png", "image/png")

with col_gen2:
    if st.button("Generate Video"):
        with st.spinner("Rendering..."):
            video = create_video(w, h, book, chapter, verse, verse_text)
            
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