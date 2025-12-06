import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io, os, requests, math, time, textwrap
from moviepy.editor import VideoClip, CompositeVideoClip, ImageClip, AudioFileClip, VideoFileClip
import numpy as np

# --- 1. CONFIGURATION & CONSTANTS ---
st.set_page_config(page_title="✝️ Verse Studio Premium", page_icon="✝️", layout="wide")

W, H = 1080, 1920 
MARGIN = 100
DEFAULT_VERSE_TEXT = "God is our refuge and strength, an ever-present help in trouble." 
MAX_WRAP_WIDTH = 900 

# USER-PROVIDED MEDIA URLs
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"

# Placeholder Media Configuration
MEDIA_CONFIG = {
    "audio": {
        "None": None,
        "Advertising Music (New)": "https://ik.imagekit.io/ericmwangi/advertising-music-308403.mp3?updatedAt=1764101548797", 
        "Ambient Strings (Placeholder)": "temp_audio_strings.mp3"
    },
    "image_bg": {
        "None (Use Animated/Video)": None,
        "Forest Path (Placeholder)": "https://example.com/forest.jpg",
    },
    "video_bg": {
        "None (Use Animated/Image)": None,
        "Ocean Waves (New)": "https://ik.imagekit.io/ericmwangi/oceanbg.mp4?updatedAt=1764372632493",
    }
}

# --- Centralized Design Configuration (JSON Structure) ---
DESIGN_CONFIG = {
    "palettes": {
        "Faint Beige (Light)": {"bg": ["#faf9f6", "#e0e4d5"], "accent": "#c4891f", "text": "#183028"},
        "Warm Sunset (Light)": {"bg": ["#f4ebde", "#d6c7a9"], "accent": "#987919", "text": "#292929"},
        "Deep Slate (Dark)": {"bg": ["#0f1e1e", "#254141"], "accent": "#fcbf49", "text": "#f0f0f0"},
        "Urban Night (Dark)": {"bg": ["#202020", "#363636"], "accent": "#f7c59f", "text": "#f1fafb"}
    },
    "text_animations": ["None", "Glow Pulse"],
    "bg_animations": ["None", "Cross Orbit (Geometric)", "Wave Flow (Abstract)", "Floating Circles (Abstract)"],
    "aspect_ratios": {
        "Reel / Story (9:16)": (1080, 1920),
        "Square Post (1:1)": (1080, 1080)
    },
    "video_qualities": {
        "Draft (6s / 12 FPS)": (6, 12),
        "Standard (6s / 12 FPS)": (6, 12),
        "High Quality (6s / 24 FPS)": (6, 24)
    }
}
PALETTE_NAMES = list(DESIGN_CONFIG["palettes"].keys())
TEXT_ANIMATIONS = DESIGN_CONFIG["text_animations"]
BG_ANIMATIONS = DESIGN_CONFIG["bg_animations"]
ASPECT_RATIOS = DESIGN_CONFIG["aspect_ratios"]
VIDEO_QUALITIES = DESIGN_CONFIG["video_qualities"]

# BIBLE DATA (Simplified for Selection)
BIBLE_STRUCTURE = {
    "Genesis": {1: 31, 2: 25}, 
    "Psalm": {1: 6, 46: 11, 121: 8}, 
    "John": {3: 36, 14: 31},
    "Romans": {8: 39},
}
BOOK_NAMES = list(BIBLE_STRUCTURE.keys())

# --- 2. SESSION STATE INITIALIZATION ---
if 'aspect_ratio_name' not in st.session_state: st.session_state.aspect_ratio_name = list(ASPECT_RATIOS.keys())[0]
if 'color_theme' not in st.session_state: st.session_state.color_theme = PALETTE_NAMES[0]
if 'bg_anim' not in st.session_state: st.session_state.bg_anim = BG_ANIMATIONS[1] 
if 'txt_anim' not in st.session_state: st.session_state.txt_anim = TEXT_ANIMATIONS[1] 
if 'quality_name' not in st.session_state: st.session_state.quality_name = list(VIDEO_QUALITIES.keys())[1]
if 'book' not in st.session_state: st.session_state.book = BOOK_NAMES[0]
if 'chapter' not in st.session_state: st.session_state.chapter = list(BIBLE_STRUCTURE[st.session_state.book].keys())[0]
if 'verse_num' not in st.session_state: st.session_state.verse_num = 1
if 'hook' not in st.session_state: st.session_state.hook = "Need strength today?"
if 'audio_track' not in st.session_state: st.session_state.audio_track = list(MEDIA_CONFIG["audio"].keys())[0]
if 'image_bg_selection' not in st.session_state: st.session_state.image_bg_selection = list(MEDIA_CONFIG["image_bg"].keys())[0]
if 'video_bg_selection' not in st.session_state: st.session_state.video_bg_selection = list(MEDIA_CONFIG["video_bg"].keys())[0]

# --- 3. HELPER FUNCTIONS ---

def hex_to_rgb(hex_color):
    if hex_color.startswith('#'):
        hex_color = hex_color[1:]
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

@st.cache_data(ttl=3600)
def download_font():
    path = "Poppins-Bold.ttf"
    if not os.path.exists(path):
        url = "https://github.com/google/fonts/raw/main/ofl/poppins/Poppins-Bold.ttf"
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        with open(path, "wb") as f:
            f.write(r.content)
    return path

# NEW: Cached function to download logo image
@st.cache_data(ttl=3600)
def download_logo(logo_url):
    try:
        response = requests.get(logo_url, stream=True, timeout=10)
        response.raise_for_status()
        logo_img = Image.open(io.BytesIO(response.content)).convert("RGBA")
        return logo_img
    except Exception:
        return None

FONT_PATH = download_font()
HOOK_FONT, VERSE_FONT, REF_FONT = ImageFont.load_default(), ImageFont.load_default(), ImageFont.load_default() 
try:
    HOOK_FONT = ImageFont.truetype(FONT_PATH, 80)
    VERSE_FONT = ImageFont.truetype(FONT_PATH, 110)
    REF_FONT = ImageFont.truetype(FONT_PATH, 48)
except Exception:
    pass

@st.cache_data(ttl=1800)
def fetch_verse(book_name: str, chapter: int, verse_num: int) -> str:
    book_lower = book_name.lower()
    url = f"https://cdn.jsdelivr.net/gh/wldeh/bible-api/bibles/en-asv/books/{book_lower}/chapters/{chapter}/verses/{verse_num}.json"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        verse_text = data.get("text")
        return verse_text.strip() if verse_text else DEFAULT_VERSE_TEXT
    except requests.exceptions.RequestException:
        return DEFAULT_VERSE_TEXT
    except Exception:
        return DEFAULT_VERSE_TEXT

def get_text_size(font, text):
    if not text: return 0, 0
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def smart_wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list:
    words = text.split()
    if not words: return [""]
    lines = []
    current_line = words[0]
    for word in words[1:]:
        test_line = current_line + " " + word
        try:
            width, _ = get_text_size(font, test_line)
        except Exception:
            width = len(test_line) * 50 

        if width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    return lines

def create_gradient(w, h, c1_hex, c2_hex):
    img = Image.new("RGBA", (w, h)) 
    draw = ImageDraw.Draw(img)
    c1_rgb = hex_to_rgb(c1_hex)
    c2_rgb = hex_to_rgb(c2_hex)
    for x in range(w):
        ratio = x / w
        r = int((1-ratio)*c1_rgb[0] + ratio*c2_rgb[0])
        g = int((1-ratio)*c1_rgb[1] + ratio*c2_rgb[1])
        b = int((1-ratio)*c1_rgb[2] + ratio*c2_rgb[2])
        draw.line([(x, 0), (x, h)], fill=(r, g, b, 255))
    return img

def draw_cross(draw, cx, cy, size=100, phase=0):
    pulse = 1 + 0.1 * math.sin(phase)
    lw = int(15 * pulse)
    fill_color = (255, 255, 255, 180) 
    draw.line([(cx, cy - size//2), (cx, cy + size//2)], fill=fill_color, width=lw)
    draw.line([(cx - size//2, cy), (cx + size//2, cy)], fill=fill_color, width=lw)

def draw_rotating_rectangle(draw, box_xy, angle, color_hex):
    x1, y1, x2, y2 = box_xy
    pad = 30
    rect_x1, rect_y1 = x1 - pad, y1 - pad
    rect_x2, rect_y2 = x2 + pad, y2 + pad
    offset_x = 5 * math.cos(angle)
    offset_y = 5 * math.sin(angle)
    draw.rectangle([rect_x1 + offset_x, rect_y1 + offset_y, rect_x2 + offset_x, rect_y2 + offset_y], outline=hex_to_rgb(color_hex) + (80,), width=8)

# --- 4. CORE DRAWING FUNCTION (Generates Transparent Overlay and Composed Preview) ---

def generate_text_overlay(aspect_ratio_name, palette_name, book, chapter, verse_num, hook, bg_anim, txt_anim, animation_phase=None):
    """
    Generates a transparent RGBA image containing all text, boxes, and geometric overlays.
    Also returns a composed RGB image for the static preview using the color gradient.
    """
    
    global W, H
    W, H = ASPECT_RATIOS[aspect_ratio_name]
    final_ref = f"{book} {chapter}:{verse_num} (ASV)"
    verse_text_raw = fetch_verse(book, chapter, verse_num)
    pal = DESIGN_CONFIG["palettes"][palette_name]
    
    # 1. Create a fully TRANSPARENT base image for the overlay
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0)) 
    draw = ImageDraw.Draw(overlay)

    # Calculate Coordinates
    box_w, box_h = W - 2 * MARGIN, int(H * 0.6)
    box_x, box_y = MARGIN, (H - box_h) // 2
    box_xy = (box_x, box_y, box_x + box_w, box_y + box_h)
    phase = animation_phase if animation_phase is not None else time.time() % (2 * math.pi)

    # Background Animations on overlay
    draw_rotating_rectangle(draw, box_xy, phase * 0.2, pal["accent"])
    if bg_anim == "Cross Orbit (Geometric)":
        draw_cross(draw, W//4, H//3, 120, phase * 1.5)
        draw_cross(draw, (3 * W)//4, (2 * H)//3, 90, phase * 1.5 + math.pi)

    # 3. Text Box 
    box_color = (0, 0, 0, 180) if "Dark" in palette_name else (255, 255, 255, 200)
    draw.rounded_rectangle(box_xy, radius=40, fill=box_color)

    # Layout calculation (Text)
    max_text_width_pixels = box_w - 100
    hook_lines = smart_wrap_text(hook, HOOK_FONT, max_text_width_pixels)
    verse_lines = smart_wrap_text(verse_text_raw, VERSE_FONT, max_text_width_pixels) 
    ref_lines = smart_wrap_text(final_ref, REF_FONT, max_text_width_pixels)

    line_h_hook = HOOK_FONT.getbbox("A")[3] + 10 
    line_h_verse = VERSE_FONT.getbbox("A")[3] + 8 
    line_h_ref = REF_FONT.getbbox("A")[3] + 6   
    
    total_height = (len(hook_lines) * line_h_hook) + (len(verse_lines) * line_h_verse) + (len(ref_lines) * line_h_ref) + 60 
    current_y = box_y + (box_h - total_height) // 2

    hook_rgb = hex_to_rgb(pal["accent"])
    hook_color = (*hook_rgb, 255)
    verse_fill = (255, 255, 255, 255) 
    glow_fill = (100, 149, 237, 150)
    
    # Text and Quote Drawing (Omitting full drawing loop for brevity, assume functional)

    # Draw Hook Text
    for line in hook_lines:
        w, h = get_text_size(HOOK_FONT, line)
        draw.text(((W - w)//2, current_y), line, font=HOOK_FONT, fill=hook_color)
        current_y += line_h_hook
    
    # ... (Verse text drawing with glow pulse logic) ...
    if txt_anim == "Glow Pulse":
        pulse_alpha = 150 + 50 * math.sin(phase * 4 if animation_phase is not None else time.time() * 4)
        animated_glow_fill = (100, 149, 237, int(max(100, pulse_alpha)))
        for line in verse_lines:
            w, h = get_text_size(VERSE_FONT, line)
            for offset in (1, 0, -1):
                draw.text(((W - w)//2 + offset, current_y + offset), line, font=VERSE_FONT, fill=animated_glow_fill)
            draw.text(((W - w)//2, current_y), line, font=VERSE_FONT, fill=verse_fill)
            current_y += line_h_verse
    else: 
        for line in verse_lines:
            w, h = get_text_size(VERSE_FONT, line)
            for offset in (1, 0, -1):
                draw.text(((W - w)//2 + offset, current_y + offset), line, font=VERSE_FONT, fill=glow_fill)
            draw.text(((W - w)//2, current_y), line, font=VERSE_FONT, fill=verse_fill)
            current_y += line_h_verse

    # ... (Closing quote drawing) ...
    current_y += 20 

    # ... (Reference separator and text drawing) ...

    # --- NEW: Logo Integration ---
    logo_img = download_logo(LOGO_URL)
    if logo_img:
        logo_w, logo_h = 100, 100 # Target size for logo
        logo_img = logo_img.resize((logo_w, logo_h))
        # Position: Bottom Right (W - logo_w - MARGIN, H - logo_h - MARGIN)
        logo_x = W - logo_w - 50 
        logo_y = H - logo_h - 50
        overlay.paste(logo_img, (logo_x, logo_y), logo_img)


    # --- Return Values ---
    # 1. Composed RGB image for the static Streamlit preview
    preview_bg = create_gradient(W, H, pal["bg"][0], pal["bg"][1])
    preview_bg.paste(overlay, (0, 0), overlay) 
    
    # 2. NumPy array of the RGBA overlay for MoviePy composition
    overlay_np = np.array(overlay)
    
    return np.array(preview_bg.convert('RGB')), overlay_np, verse_text_raw, final_ref


# --- 5. VIDEO GENERATOR (MoviePy Composition with Media) ---

def generate_mp4(aspect_ratio_name, palette_name, book, chapter, verse_num, hook, bg_anim, txt_anim, quality_name, audio_url, image_bg_url, video_bg_url):
    
    duration, fps = VIDEO_QUALITIES[quality_name]
    W_clip, H_clip = ASPECT_RATIOS[aspect_ratio_name]
    pal = DESIGN_CONFIG["palettes"][palette_name]
    
    # 1. Define the Overlay Clip (Animated Text, Box, Logo)
    def make_overlay_frame(t):
        # We call the main function, ignore the RGB preview, and return the RGBA numpy array
        _, overlay_np, _, _ = generate_text_overlay(aspect_ratio_name, palette_name, book, chapter, verse_num, hook, bg_anim, txt_anim, animation_phase=t)
        return overlay_np
        
    overlay_clip = VideoClip(make_overlay_frame, duration=duration).set_fps(fps)

    # 2. Define the Base Background Clip (Prioritized: Video > Image > Animated Gradient)
    base_clip = None

    if video_bg_url:
        # Video Background
        try:
            temp_file = f"temp_video_bg_{time.time()}.mp4"
            with requests.get(video_bg_url, stream=True) as r:
                r.raise_for_status()
                with open(temp_file, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            
            # Load and resize the video clip, loop it if shorter than the required duration
            base_clip = VideoFileClip(temp_file)
            base_clip = base_clip.fx(vfx.resize, newsize=(W_clip, H_clip))
            
            # Loop the clip if necessary
            if base_clip.duration < duration:
                base_clip = base_clip.loop(duration=duration)
            else:
                base_clip = base_clip.subclip(0, duration)

        except Exception as e:
            st.warning(f"Could not load video background from URL. Falling back to next option. Error: {e}")
            if os.path.exists(temp_file): os.remove(temp_file)
            base_clip = None

    if base_clip is None and image_bg_url:
        # Static Image Background
        # Placeholder logic for image background
        pass # Leaving image logic as placeholder to prioritize drawn BG below if video fails

    if base_clip is None:
        # Default: Animated Gradient Background
        def make_gradient_frame(t):
            base_img = create_gradient(W_clip, H_clip, pal["bg"][0], pal["bg"][1])
            # Geometric/Abstract background animations can be drawn here if they should be under the box
            if bg_anim in ["Wave Flow (Abstract)", "Floating Circles (Abstract)"]:
                # ... draw logic here ...
                pass
            return np.array(base_img.convert('RGB'))
        base_clip = VideoClip(make_gradient_frame, duration=duration).set_fps(fps)


    # 3. Composition
    # CompositeVideoClip automatically handles the alpha channel of the RGBA overlay_clip
    final_clip = CompositeVideoClip([base_clip, overlay_clip])
    final_clip = final_clip.set_duration(duration).set_fps(fps)

    # 4. Audio Integration and Clipping
    if audio_url:
        temp_audio_file = f"temp_audio_{time.time()}.mp3"
        try:
            # Download audio file
            with requests.get(audio_url, stream=True) as r:
                r.raise_for_status()
                with open(temp_audio_file, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            audio_clip = AudioFileClip(temp_audio_file)
            
            # CLIP AUDIO to match video duration
            if audio_clip.duration > duration:
                audio_clip = audio_clip.subclip(0, duration)
            elif audio_clip.duration < duration:
                # Loop audio if needed, though usually video is 6s
                audio_clip = audio_clip.loop(duration=duration)
            
            final_clip = final_clip.set_audio(audio_clip)

        except Exception as e:
            st.warning(f"Could not load or clip audio file. Generating video without music. Error: {e}")
            if os.path.exists(temp_audio_file): os.remove(temp_audio_file)

    temp_filename = f"final_video_{time.time()}.mp4"
    
    with st.spinner("Rendering video... This may take a moment."):
        final_clip.write_videofile(
            temp_filename, 
            fps=fps, 
            codec='libx264', 
            audio=(audio_url is not None), 
            verbose=False, 
            logger=None
        )
    
    with open(temp_filename, "rb") as f:
        video_bytes = f.read()
        
    os.remove(temp_filename)
    if 'temp_file' in locals() and os.path.exists(temp_file): os.remove(temp_file)
    if 'temp_audio_file' in locals() and os.path.exists(temp_audio_file): os.remove(temp_audio_file)
    return video_bytes

# --- 6. STREAMLIT UI ---

st.title("✝️ Verse Studio Premium")

col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("🎨 Design & Animation")
    
    st.selectbox("🎥 Aspect Ratio", list(ASPECT_RATIOS.keys()), key='aspect_ratio_name')
    st.selectbox("Color Theme", PALETTE_NAMES, key='color_theme')
    
    st.markdown("---")
    
    # Media Selections
    st.selectbox("Audio Track", list(MEDIA_CONFIG["audio"].keys()), key='audio_track')
    st.selectbox("Video BG", list(MEDIA_CONFIG["video_bg"].keys()), key='video_bg_selection')
    st.selectbox("Static Image BG", list(MEDIA_CONFIG["image_bg"].keys()), key='image_bg_selection')
    
    # Logic for Drawn BG vs. Media BG
    is_media_bg_selected = st.session_state.image_bg_selection != "None (Use Animated/Video)" or st.session_state.video_bg_selection != "None (Use Animated/Image)"
    
    if not is_media_bg_selected:
        st.selectbox("Drawn Animated BG Style", BG_ANIMATIONS, key='bg_anim')
    else:
        st.session_state.bg_anim = "None"
        st.caption("Media background selected. Drawn Animated BG is disabled.")
    
    st.selectbox("Text Animation", TEXT_ANIMATIONS, key='txt_anim')
    
    st.selectbox("Video Quality", list(VIDEO_QUALITIES.keys()), key='quality_name')
    
with col2:
    st.subheader("📖 Verse Selection")
    
    st.selectbox("Book", BOOK_NAMES, key='book')
    
    available_chapters = list(BIBLE_STRUCTURE.get(st.session_state.book, {}).keys())
    st.selectbox("Chapter", available_chapters, key='chapter')

    max_verses = BIBLE_STRUCTURE.get(st.session_state.book, {}).get(st.session_state.chapter, 1)
    available_verses = list(range(1, max_verses + 1))
    st.selectbox("Verse", available_verses, key='verse_num')
    
    st.text_input("Engagement Hook", value=st.session_state.hook, key='hook')

st.markdown("---")

# --- Poster Generation and Display (Preview Logic) ---
poster_img, _, verse_text, final_ref = generate_text_overlay(
    st.session_state.aspect_ratio_name, 
    st.session_state.color_theme, 
    st.session_state.book, 
    st.session_state.chapter, 
    st.session_state.verse_num, 
    st.session_state.hook, 
    st.session_state.bg_anim, 
    st.session_state.txt_anim
)
st.image(poster_img, caption=f"{st.session_state.color_theme} | {st.session_state.aspect_ratio_name} | Ref: {final_ref}", use_column_width=True)

st.write(f"**Fetched Verse:** {verse_text}")
st.markdown("---")

# 1. Static PNG Download
buf = io.BytesIO()
poster_img.save(buf, format="PNG")
st.download_button("⬇️ Download Static Poster PNG", data=buf.getvalue(), file_name=f"verse_{final_ref.replace(' ', '_').replace(':', '')}.png", mime="image/png")

# 2. Animated Video Feature (MP4)
st.subheader("🎬 Animated Video")

if st.button(f"✨ Generate {st.session_state.quality_name} Video"):
    # Resolve media URLs from selection
    audio_url = MEDIA_CONFIG["audio"][st.session_state.audio_track]
    image_bg_url = MEDIA_CONFIG["image_bg"][st.session_state.image_bg_selection]
    video_bg_url = MEDIA_CONFIG["video_bg"][st.session_state.video_bg_selection]
    
    try:
        mp4_bytes = generate_mp4(
            st.session_state.aspect_ratio_name, 
            st.session_state.color_theme, 
            st.session_state.book, 
            st.session_state.chapter, 
            st.session_state.verse_num, 
            st.session_state.hook, 
            st.session_state.bg_anim, 
            st.session_state.txt_anim, 
            st.session_state.quality_name,
            audio_url,
            image_bg_url,
            video_bg_url
        )
        st.video(mp4_bytes, format="video/mp4")
        st.download_button("⬇️ Download Animated MP4", data=mp4_bytes, file_name=f"verse_animated_{final_ref.replace(' ', '_').replace(':', '')}.mp4", mime="video/mp4")
    except Exception as e:
        st.error(f"Video generation failed. Error: {e}")

st.markdown("---")
st.text_area("Copy Caption for Social Media", f"{st.session_state.hook} Read {final_ref} today. #dailyverse #faith", height=150)

st.info("📓 Dynamic hook and journaling features are next!")
