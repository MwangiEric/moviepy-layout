import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io, os, requests, math, time
from moviepy.editor import VideoClip, CompositeVideoClip, AudioFileClip, VideoFileClip, vfx
import numpy as np

# --- 0. STREAMLIT CONFIGURATION ---
st.set_page_config(page_title="💎 Verse Studio Premium", page_icon="✝️", layout="wide")

# --- 0.1. CLEANUP FUNCTION (Runs on session end/exit) ---
def cleanup_temp_files():
    files_to_delete = [f for f in os.listdir('.') if f.startswith('cached_media_') or (f.endswith('.mp4') and f.startswith('final_video_'))]
    for f in files_to_delete:
        try: os.remove(f)
        except Exception as e: print(f"Error cleaning up file {f}: {e}")

# --- 1. CORE CONSTANTS & MEDIA CONFIGURATION ---
W, H = 1080, 1920 
MARGIN = 100
DEFAULT_VERSE_TEXT = "God is our refuge and strength, an ever-present help in trouble." 
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"
LOGO_SIZE = 100

DESIGN_CONFIG = {
    "palettes": {
        "Galilee Morning (Light)": {"bg": ["#faf9f6", "#e0e4d5"], "accent": "#c4891f", "text_primary": "#183028", "text_secondary": "#5a5a5a"},
        "Mount Zion Dusk (Light)": {"bg": ["#f4ebde", "#d6c7a9"], "accent": "#987919", "text_primary": "#292929", "text_secondary": "#555555"},
        "Deep Slate (Dark)": {"bg": ["#0f1e1e", "#254141"], "accent": "#fcbf49", "text_primary": "#f0f0f0", "text_secondary": "#cccccc"},
        "Urban Night (Dark)": {"bg": ["#202020", "#363636"], "accent": "#f7c59f", "text_primary": "#f1fafb", "text_secondary": "#dddddd"}
    },
    "bg_animations": ["None", "Cross Orbit (Geometric)", "Wave Flow (Abstract)", "Floating Circles (Abstract)"],
    "text_animations": ["None", "Glow Pulse", "Typewriter Effect", "Fade-in Opacity"],
    "aspect_ratios": {"Reel / Story (9:16)": (1080, 1920), "Square Post (1:1)": (1080, 1080)},
    "video_qualities": {"Draft (6s / 12 FPS)": (6, 12), "Standard (6s / 24 FPS)": (6, 24), "High Quality (10s / 24 FPS)": (10, 24)}
}

MEDIA_CONFIG = {
    "audio": {
        "None": None,
        "Advertising Music (New)": "https://ik.imagekit.io/ericmwangi/advertising-music-308403.mp4?updatedAt=1764101548797", 
        "Ambient Strings (Placeholder)": "temp_audio_strings.mp3"
    },
    "video_bg": {
        "None (Use Animated/Image)": None,
        "Ocean Waves (New)": "https://ik.imagekit.io/ericmwangi/oceanbg.mp4?updatedAt=1764372632493",
    }
}

LOGO_PLACEMENTS = {"Bottom Right": (1, 1), "Bottom Left": (0, 1), "Top Right": (1, 0), "Hidden": None}

FULL_BIBLE_BOOKS = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel", 
    "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther", "Job", "Psalm", "Proverbs", 
    "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", 
    "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi",
    "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians", 
    "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus", "Philemon", 
    "Hebrews", "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation"
]

BIBLE_STRUCTURE = {
    "Genesis": {1: 31, 2: 25, 3: 24}, 
    "Psalm": {1: 6, 46: 11, 121: 8, 23: 6}, 
    "John": {3: 36, 14: 31},
    "Romans": {8: 39},
    "Matthew": {5: 48, 6: 34, 7: 29},
    "Revelation": {21: 27, 22: 21}
}
BOOK_NAMES = FULL_BIBLE_BOOKS

PALETTE_NAMES = list(DESIGN_CONFIG["palettes"].keys())
ASPECT_RATIOS = DESIGN_CONFIG["aspect_ratios"]
VIDEO_QUALITIES = DESIGN_CONFIG["video_qualities"]
TEXT_ANIMATIONS = DESIGN_CONFIG["text_animations"]
BG_ANIMATIONS = DESIGN_CONFIG["bg_animations"]

# --- 2. HELPER FUNCTIONS ---
def hex_to_rgb(hex_color):
    if hex_color.startswith('#'): hex_color = hex_color[1:]
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_text_size(font, text):
    if not text: return 0, 0
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def smart_wrap_text(text: str, font, max_width: int) -> list:
    words = text.split()
    if not words: return [""]
    lines, current_line = [], words[0]
    for word in words[1:]:
        if get_text_size(font, current_line + " " + word)[0] <= max_width:
            current_line += " " + word
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    return lines

@st.cache_data
def create_gradient(w, h, c1_hex, c2_hex):
    img = Image.new("RGBA", (w, h))
    draw = ImageDraw.Draw(img)
    c1_rgb, c2_rgb = hex_to_rgb(c1_hex), hex_to_rgb(c2_hex)
    for x in range(w):
        ratio = x / w
        rgb = tuple(int((1-ratio)*c1_rgb[i] + ratio*c2_rgb[i]) for i in range(3))
        draw.line([(x, 0), (x, h)], fill=(*rgb, 255))
    return img

def draw_rounded_rect(draw, xy, radius=40, fill=None):
    x1, y1, x2, y2 = [int(v) for v in xy]
    radius = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
    draw.pieslice([x1, y1, x1+2*radius, y1+2*radius], 180, 270, fill=fill)
    draw.pieslice([x2-2*radius, y1, x2, y1+2*radius], 270, 360, fill=fill)
    draw.pieslice([x2-2*radius, y2-2*radius, x2, y2], 0, 90, fill=fill)
    draw.pieslice([x1, y2-2*radius, x1+2*radius, y2], 90, 180, fill=fill)
    draw.rectangle([x1+radius, y1, x2-radius, y2], fill=fill)
    draw.rectangle([x1, y1+radius, x1+radius, y2-radius], fill=fill)
    draw.rectangle([x2-radius, y1+radius, x2, y2-radius], fill=fill)
    draw.rectangle([x1, y2-radius, x2, y2], fill=fill)

@st.cache_data(ttl=3600)
def download_font(font_name):
    path = f"{font_name}.ttf"
    if not os.path.exists(path):
        url = ""
        if font_name == "Poppins-Bold":
            url = "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Bold.ttf"
        elif font_name == "Roboto-Regular":
            url = "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Regular.ttf"
        if not url: return None
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            with open(path, "wb") as f: f.write(r.content)
        except Exception as e:
            st.error(f"Failed to download font '{font_name}'. Error: {e}")
            return None
    return path

FONT_PATH_BOLD = download_font("Poppins-Bold")
FONT_PATH_REGULAR = download_font("Roboto-Regular")

# --- 3. SESSION STATE INITIALIZATION ---
def initialize_session_state():
    default_quality = list(VIDEO_QUALITIES.keys())[0]
    defaults = {
        'aspect_ratio_name': list(ASPECT_RATIOS.keys())[0],
        'color_theme': PALETTE_NAMES[0],
        'bg_anim': BG_ANIMATIONS[1],
        'txt_anim': TEXT_ANIMATIONS[1],
        'quality_name': default_quality,
        'book': "Psalm",
        'chapter': 46,
        'verse_num': 1,
        'hook': "Need strength today?",
        'audio_track': list(MEDIA_CONFIG["audio"].keys())[0],
        'video_bg_selection': list(MEDIA_CONFIG["video_bg"].keys())[0],
        'logo_placement': list(LOGO_PLACEMENTS.keys())[0],
        'hook_font_size': 120,
        'verse_font_size': 210,
        'ref_font_size': 80
    }
    for key, val in defaults.items():
        if key not in st.session_state: st.session_state[key] = val

initialize_session_state()

# --- 4. TEXT & OVERLAY GENERATION ---
HOOK_FONT = VERSE_FONT = REF_FONT = ImageFont.load_default()

def generate_text_overlay(aspect_ratio_name, palette_name, book, chapter, verse_num, hook, bg_anim, txt_anim, logo_placement, animation_phase=None):
    global W, H
    W, H = ASPECT_RATIOS[aspect_ratio_name]
    final_ref = f"{book} {chapter}:{verse_num} (ASV)"
    verse_text_raw = DEFAULT_VERSE_TEXT
    pal = DESIGN_CONFIG["palettes"][palette_name]

    # Dynamic font sizes
    HOOK_FONT = ImageFont.truetype(FONT_PATH_BOLD, st.session_state.hook_font_size)
    VERSE_FONT = ImageFont.truetype(FONT_PATH_REGULAR, st.session_state.verse_font_size)
    REF_FONT = ImageFont.truetype(FONT_PATH_REGULAR, st.session_state.ref_font_size)

    overlay = Image.new("RGBA", (W, H), (0,0,0,0))
    draw = ImageDraw.Draw(overlay)

    max_text_width_pixels = W - 2*MARGIN - 100
    hook_lines = smart_wrap_text(hook, HOOK_FONT, max_text_width_pixels)
    verse_lines = smart_wrap_text(verse_text_raw, VERSE_FONT, max_text_width_pixels)
    ref_lines = smart_wrap_text(final_ref, REF_FONT, max_text_width_pixels)

    line_h_hook = HOOK_FONT.getbbox("A")[3] + 10
    line_h_verse = VERSE_FONT.getbbox("A")[3] + 8
    line_h_ref = REF_FONT.getbbox("A")[3] + 6

    content_height = len(hook_lines)*line_h_hook + len(verse_lines)*line_h_verse + len(ref_lines)*line_h_ref + 120
    padding = 50
    box_w, box_h = W-2*MARGIN, content_height+2*padding
    box_h = min(box_h, int(H*0.8))
    box_x, box_center_y = MARGIN, int(H*0.45)
    box_y = box_center_y - box_h//2
    box_xy = (box_x, box_y, box_x+box_w, box_y+box_h)
    current_y = box_y + (box_h-content_height)//2

    box_color = (0,0,0,180) if "Dark" in palette_name else (255,255,255,200)
    draw_rounded_rect(draw, box_xy, radius=40, fill=box_color)

    # Hook text
    hook_color = (*hex_to_rgb(pal["accent"]),255)
    for line in hook_lines:
        w,h = get_text_size(HOOK_FONT, line)
        draw.text(((W-w)//2, current_y), line, font=HOOK_FONT, fill=hook_color)
        current_y += line_h_hook
    current_y += 60

    # Verse text
    verse_fill = (255,255,255,255)
    for line in verse_lines:
        w,h = get_text_size(VERSE_FONT, line)
        draw.text(((W-w)//2, current_y), line, font=VERSE_FONT, fill=verse_fill)
        current_y += line_h_verse

    current_y += 60
    ref_color = (*hex_to_rgb(pal["text_secondary"]),255)
    w,h = get_text_size(REF_FONT, final_ref)
    draw.text(((W-w)//2, current_y), final_ref, font=REF_FONT, fill=ref_color)

    preview_bg = create_gradient(W,H,pal["bg"][0],pal["bg"][1])
    preview_bg.paste(overlay,(0,0),overlay)
    return preview_bg, np.array(overlay), verse_text_raw, final_ref

# --- 5. STREAMLIT UI ---
st.title("💎 Verse Studio Premium")
col1,col2 = st.columns([1,1.5])

with col1:
    st.subheader("🎨 Design & Animation")
    st.selectbox("🎥 Aspect Ratio", list(ASPECT_RATIOS.keys()), key='aspect_ratio_name')
    st.selectbox("Color Theme", PALETTE_NAMES, key='color_theme')
    st.markdown("---")
    st.selectbox("Audio Track", list(MEDIA_CONFIG["audio"].keys()), key='audio_track')
    st.selectbox("Video BG", list(MEDIA_CONFIG["video_bg"].keys()), key='video_bg_selection')
    is_media_bg_selected = st.session_state.video_bg_selection != "None (Use Animated/Image)"
    if not is_media_bg_selected: st.selectbox("Drawn Animated BG Style", BG_ANIMATIONS, index=1, key='bg_anim')
    else: st.session_state.bg_anim="None"; st.caption("Video background selected. Drawn Animated BG is disabled.")
    st.selectbox("Logo Placement", list(LOGO_PLACEMENTS.keys()), key='logo_placement')
    st.selectbox("Text Animation", TEXT_ANIMATIONS, key='txt_anim')
    st.selectbox("Video Quality", list(VIDEO_QUALITIES.keys()), key='quality_name')

    # --- NEW FONT SIZE SLIDERS ---
    st.markdown("### Text Sizes")
    st.session_state.hook_font_size = st.slider("Hook Font Size", 50, 250, st.session_state.hook_font_size)
    st.session_state.verse_font_size = st.slider("Verse Font Size", 80, 300, st.session_state.verse_font_size)
    st.session_state.ref_font_size = st.slider("Reference Font Size", 40, 150, st.session_state.ref_font_size)

with col2:
    st.subheader("📖 Verse Selection")
    st.selectbox("Book", BOOK_NAMES, key='book')
    available_chapters = list(BIBLE_STRUCTURE.get(st.session_state.book,{1:31}).keys())
    st.selectbox("Chapter", available_chapters, key='chapter')
    max_verses_in_chapter = BIBLE_STRUCTURE.get(st.session_state.book,{}).get(st.session_state.chapter,31)
    st.selectbox("Verse", list(range(1,max_verses_in_chapter+1)), key='verse_num')
    st.text_input("Engagement Hook", value=st.session_state.hook, key='hook')

st.markdown("---")
pil_poster_img, _, verse_text, final_ref = generate_text_overlay(
    st.session_state.aspect_ratio_name, st.session_state.color_theme,
    st.session_state.book, st.session_state.chapter, st.session_state.verse_num,
    st.session_state.hook, st.session_state.bg_anim, st.session_state.txt_anim,
    st.session_state.logo_placement
)
st.image(pil_poster_img, caption=f"{st.session_state.color_theme} | {st.session_state.aspect_ratio_name} | Ref: {final_ref}", use_column_width=True)
st.write(f"**Fetched Verse:** {verse_text}")
st.markdown("---")
buf = io.BytesIO()
pil_poster_img.save(buf, format="PNG") 
st.download_button("⬇️ Download Static Poster PNG", data=buf.getvalue(), file_name=f"verse_{final_ref.replace(' ','_').replace(':','')}.png", mime="image/png")
st.markdown("---")
st.text_area("Copy Caption for Social Media", f"{st.session_state.hook} Read {final_ref} today. #dailyverse #faith", height=150)
st.info("💡 Next Steps: Add user file uploads and subtle audio volume controls.")
if st.button("🧹 Cleanup Cached Media and Temp Files"):
    cleanup_temp_files(); st.success("Cleaned up temporary media files!")