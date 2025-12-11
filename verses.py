import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io, os, requests, math, time
from moviepy.editor import VideoClip, CompositeVideoClip, AudioFileClip, VideoFileClip, vfx
import numpy as np

# --- 0. STREAMLIT CONFIGURATION ---
st.set_page_config(page_title="💎 Verse Studio Premium", page_icon="✝️", layout="wide")

# --- 0.1. CLEANUP FUNCTION (Runs on session end/exit) ---
def cleanup_temp_files():
    """Removes temporary files created during media caching."""
    files_to_delete = [f for f in os.listdir('.') if f.startswith('cached_media_') or f.endswith('.mp4') and f.startswith('final_video_')]
    for f in files_to_delete:
        try:
            os.remove(f)
            # print(f"Cleaned up: {f}")
        except Exception as e:
            print(f"Error cleaning up file {f}: {e}")

# Register cleanup function to run when the script finishes (if supported by Streamlit environment)
# st.runtime.get_instance().on_script_stop(cleanup_temp_files) # Note: This line might need adaptation based on your specific Streamlit environment setup.

# --- 1. CORE CONSTANTS & MEDIA CONFIGURATION ---

W, H = 1080, 1920 
MARGIN = 100
DEFAULT_VERSE_TEXT = "God is our refuge and strength, an ever-present help in trouble." 
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"
LOGO_SIZE = 100

# Centralized Design Configuration
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
    # Default is now Draft (12 FPS)
    "video_qualities": {"Draft (6s / 12 FPS)": (6, 12), "Standard (6s / 24 FPS)": (6, 24), "High Quality (10s / 24 FPS)": (10, 24)}
}

# Media URLs
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

LOGO_PLACEMENTS = {
    "Bottom Right": (1, 1), 
    "Bottom Left": (0, 1),
    "Top Right": (1, 0),
    "Hidden": None
}

# Full Bible Book List (Simplified for placeholder use)
FULL_BIBLE_BOOKS = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel", 
    "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther", "Job", "Psalm", "Proverbs", 
    "Ecclesiastes", "Song of Solomon", "Isaiah", "Jeremiah", "Lamentations", "Ezekiel", "Daniel", "Hosea", "Joel", 
    "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi",
    "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians", 
    "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus", "Philemon", 
    "Hebrews", "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation"
]

# BIBLE DATA structure for chapter/verse counts (expanded to include new default books)
BIBLE_STRUCTURE = {
    "Genesis": {1: 31, 2: 25, 3: 24}, 
    "Psalm": {1: 6, 46: 11, 121: 8, 23: 6}, 
    "John": {3: 36, 14: 31},
    "Romans": {8: 39},
    "Matthew": {5: 48, 6: 34, 7: 29},
    "Revelation": {21: 27, 22: 21}
}
BOOK_NAMES = FULL_BIBLE_BOOKS # Use the full list now, but the fetcher still relies on BIBLE_STRUCTURE for counts.

PALETTE_NAMES = list(DESIGN_CONFIG["palettes"].keys())
ASPECT_RATIOS = DESIGN_CONFIG["aspect_ratios"]
VIDEO_QUALITIES = DESIGN_CONFIG["video_qualities"]
TEXT_ANIMATIONS = DESIGN_CONFIG["text_animations"]
BG_ANIMATIONS = DESIGN_CONFIG["bg_animations"]


# --- 2. CORE HELPER FUNCTIONS (Caching, Geometry, Color, Fonts) ---
# (NOTE: These functions remain unchanged as they were correct and necessary)

def hex_to_rgb(hex_color):
    if hex_color.startswith('#'): hex_color = hex_color[1:]
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

@st.cache_data
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
    """Draws a rounded rectangle using PIL shapes."""
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
        if font_name == "Poppins-Bold":
            url = "https://github.com/google/fonts/raw/main/ofl/poppins/static/Poppins-Bold.ttf"
        elif font_name == "Roboto-Regular":
            url = "https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf"
        else:
            return None 
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

HOOK_FONT = VERSE_FONT = REF_FONT = ImageFont.load_default() 
try:
    if FONT_PATH_BOLD: HOOK_FONT = ImageFont.truetype(FONT_PATH_BOLD, 80)
    if FONT_PATH_REGULAR: 
        VERSE_FONT = ImageFont.truetype(FONT_PATH_REGULAR, 110) 
        REF_FONT = ImageFont.truetype(FONT_PATH_REGULAR, 48)
except Exception: pass

@st.cache_data(ttl=1800)
def fetch_verse(book_name: str, chapter: int, verse_num: int) -> str:
    book_lower = book_name.lower().replace('psalm', 'ps')
    url = f"https://cdn.jsdelivr.net/gh/wldeh/bible-api/bibles/en-asv/books/{book_lower}/chapters/{chapter}/verses/{verse_num}.json"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return r.json().get("text", "").strip() or DEFAULT_VERSE_TEXT
    except: 
        return DEFAULT_VERSE_TEXT

@st.cache_data(ttl=3600, show_spinner=False)
def cache_media(url: str, file_ext: str) -> str:
    if not url: return None
    temp_path = f"cached_media_{hash(url)}.{file_ext}"
    if os.path.exists(temp_path): return temp_path
    
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(temp_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): f.write(chunk)
        return temp_path
    except Exception as e:
        st.error(f"Failed to cache media from URL: {url}. Error: {e}")
        return None

@st.cache_data(ttl=3600)
def download_logo(logo_url):
    try:
        response = requests.get(logo_url, stream=True, timeout=10)
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content)).convert("RGBA")
    except Exception: return None


# --- 3. SESSION STATE INITIALIZATION ---

def initialize_session_state():
    # Set default video quality to the first option (Draft / 12 FPS)
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
        'logo_placement': list(LOGO_PLACEMENTS.keys())[0]
    }
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

initialize_session_state()


# --- 4. CORE DRAWING LOGIC (With Dynamic Layout & Animation Refinements) ---

# (NOTE: The logic inside generate_text_overlay remains the same as the previous polished version)
def generate_text_overlay(aspect_ratio_name, palette_name, book, chapter, verse_num, hook, bg_anim, txt_anim, logo_placement, animation_phase=None):
    """Generates the transparent RGBA overlay and the composed PIL Image preview."""
    
    global W, H
    W, H = ASPECT_RATIOS[aspect_ratio_name]
    final_ref = f"{book} {chapter}:{verse_num} (ASV)"
    verse_text_raw = fetch_verse(book, chapter, verse_num)
    pal = DESIGN_CONFIG["palettes"][palette_name]
    
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0)) 
    draw = ImageDraw.Draw(overlay)
    
    phase = (animation_phase / (2 * math.pi)) % 1 if animation_phase is not None else 0

    # --- Dynamic Layout Calculation ---
    max_text_width_pixels = W - 2 * MARGIN - 100
    
    hook_lines = smart_wrap_text(hook, HOOK_FONT, max_text_width_pixels)
    verse_lines = smart_wrap_text(verse_text_raw, VERSE_FONT, max_text_width_pixels) 
    ref_lines = smart_wrap_text(final_ref, REF_FONT, max_text_width_pixels)

    line_h_hook = HOOK_FONT.getbbox("A")[3] + 10 
    line_h_verse = VERSE_FONT.getbbox("A")[3] + 8 
    line_h_ref = REF_FONT.getbbox("A")[3] + 6   
    
    content_height = (len(hook_lines) * line_h_hook) + (len(verse_lines) * line_h_verse) + (len(ref_lines) * line_h_ref) + 120
    
    padding = 50
    box_w = W - 2 * MARGIN
    box_h = content_height + 2 * padding
    
    max_allowable_h = H * 0.8
    if box_h > max_allowable_h: box_h = int(max_allowable_h)

    box_x = MARGIN
    box_center_y = int(H * 0.45)
    box_y = box_center_y - (box_h // 2)
    box_xy = (box_x, box_y, box_x + box_w, box_y + box_h)
    
    current_y = box_y + (box_h - content_height) // 2

    # Text Box Drawing
    box_color = (0, 0, 0, 180) if "Dark" in palette_name else (255, 255, 255, 200)
    draw_rounded_rect(draw, box_xy, radius=40, fill=box_color)

    # --- Text Drawing Logic ---
    hook_color = (*hex_to_rgb(pal["accent"]), 255)
    verse_fill = (255, 255, 255, 255) 
    
    # Draw Hook Text
    for line in hook_lines:
        w, h = get_text_size(HOOK_FONT, line)
        draw.text(((W - w)//2, current_y), line, font=HOOK_FONT, fill=hook_color)
        current_y += line_h_hook
    
    current_y += 40 

    # --- Verse Text Drawing with Premium Animations ---
    
    if txt_anim == "Typewriter Effect":
        full_text = " ".join(verse_lines)
        total_chars = len(full_text)
        chars_visible = int(total_chars * min(1.0, phase / 0.9))

        temp_lines = []
        words = full_text.split()
        current_line_anim = ""
        char_count = 0
        
        for word in words:
            test_line = (current_line_anim + " " + word).strip()
            
            if char_count + len(word) > chars_visible and char_count < chars_visible:
                remaining_chars = chars_visible - char_count
                if remaining_chars > 0:
                    current_line_anim = test_line[:remaining_chars].strip()
                if current_line_anim: temp_lines.append(current_line_anim)
                break
            
            if get_text_size(VERSE_FONT, test_line)[0] <= max_text_width_pixels:
                current_line_anim = test_line
                char_count += len(word) + (1 if current_line_anim else 0)
            else:
                temp_lines.append(current_line_anim)
                current_line_anim = word
                char_count += len(word)
        else:
            if current_line_anim: temp_lines.append(current_line_anim)

        y_anim = current_y
        for line in temp_lines:
            w, h = get_text_size(VERSE_FONT, line)
            draw.text(((W - w)//2, y_anim), line, font=VERSE_FONT, fill=verse_fill)
            y_anim += line_h_verse
        
        if phase > 0.05 and int(phase * 10) % 2 == 0:
            last_line = temp_lines[-1] if temp_lines else ""
            cursor_x = (W - get_text_size(VERSE_FONT, last_line)[0]) // 2 + get_text_size(VERSE_FONT, last_line)[0] + 5
            draw.line([(cursor_x, y_anim - line_h_verse + 5), (cursor_x, y_anim - 15)], fill=verse_fill, width=5)
        
    elif txt_anim == "Fade-in Opacity":
        opacity = int(50 + 205 * min(1.0, phase / 0.5))
        fade_fill = (255, 255, 255, opacity)
        y_anim = current_y
        for line in verse_lines:
            w, h = get_text_size(VERSE_FONT, line)
            draw.text(((W - w)//2, y_anim), line, font=VERSE_FONT, fill=fade_fill)
            y_anim += line_h_verse
            
    else: 
        y_anim = current_y
        for line in verse_lines:
            w, h = get_text_size(VERSE_FONT, line)
            draw.text(((W - w)//2, y_anim), line, font=VERSE_FONT, fill=verse_fill)
            y_anim += line_h_verse

    current_y = y_anim 

    current_y += 40 
    ref_color = (*hex_to_rgb(pal["text_secondary"]), 255)
    w, h = get_text_size(REF_FONT, final_ref)
    draw.text(((W - w)//2, current_y), final_ref, font=REF_FONT, fill=ref_color)
    
    # --- Logo Placement with Polish ---
    if logo_placement != "Hidden":
        logo_img = download_logo(LOGO_URL)
        if logo_img:
            logo_w, logo_h = LOGO_SIZE, LOGO_SIZE
            logo_img = logo_img.resize((logo_w, logo_h))
            
            h_norm, v_norm = LOGO_PLACEMENTS[logo_placement]
            
            logo_x = int(50 + h_norm * (W - logo_w - 100))
            logo_y = int(50 + v_norm * (H - logo_h - 100))
            
            draw.ellipse([logo_x - 10, logo_y - 10, logo_x + logo_w + 10, logo_y + logo_h + 10], fill=(255, 255, 255, 50)) 
            
            overlay.paste(logo_img, (logo_x, logo_y), logo_img)

    # --- Return Values ---
    preview_bg = create_gradient(W, H, pal["bg"][0], pal["bg"][1])
    preview_bg.paste(overlay, (0, 0), overlay) 
    
    return preview_bg, np.array(overlay), verse_text_raw, final_ref


# --- 5. VIDEO GENERATION LOGIC ---

def generate_mp4(aspect_ratio_name, palette_name, book, chapter, verse_num, hook, bg_anim, txt_anim, quality_name, audio_url, video_bg_url, logo_placement):
    
    duration, fps = VIDEO_QUALITIES[quality_name]
    W_clip, H_clip = ASPECT_RATIOS[aspect_ratio_name]
    
    progress_container = st.container()
    progress_bar = progress_container.progress(0, text="Initializing...")
    
    # 1. Media Caching (Uses st.cache_data)
    progress_bar.progress(10, text="Caching external media...")
    audio_path = cache_media(audio_url, 'mp4') if audio_url else None
    video_path = cache_media(video_bg_url, 'mp4') if video_bg_url else None
    
    # 2. Base Clip Creation
    base_clip = None
    
    if video_path:
        try:
            progress_bar.progress(30, text="Composing video background...")
            base_clip = VideoFileClip(video_path)
            base_clip = base_clip.fx(vfx.resize, newsize=(W_clip, H_clip)).subclip(0, duration)
            if base_clip.duration < duration:
                 base_clip = base_clip.loop(duration=duration)
        except Exception as e:
            st.warning(f"Failed to process video background. Using animated gradient. Error: {e}")
            base_clip = None

    if base_clip is None:
        progress_bar.progress(30, text="Generating premium animated gradient...")
        pal = DESIGN_CONFIG["palettes"][palette_name]
        
        def make_gradient_frame(t):
            base_img = create_gradient(W_clip, H_clip, pal["bg"][0], pal["bg"][1])
            return np.array(base_img.convert('RGB'))
        base_clip = VideoClip(make_gradient_frame, duration=duration).set_fps(fps)

    # 3. Animated Overlay Clip
    progress_bar.progress(50, text="Creating animated text overlay...")
    overlay_clip = VideoClip(lambda t: generate_text_overlay(aspect_ratio_name, palette_name, book, chapter, verse_num, hook, bg_anim, txt_anim, logo_placement, animation_phase=t)[1], duration=duration).set_fps(fps)
    
    # 4. Composition
    final_clip = CompositeVideoClip([base_clip, overlay_clip])
    final_clip = final_clip.set_duration(duration).set_fps(fps)

    # 5. Audio Integration 
    if audio_path:
        try:
            progress_bar.progress(70, text="Adding and clipping audio...")
            # NOTE: MoviePy uses AudioFileClip, fixed typo in import above
            audio_clip = AudioFileClip(audio_path) 
            audio_clip = audio_clip.subclip(0, duration)
            final_clip = final_clip.set_audio(audio_clip)

        except Exception as e:
            st.warning(f"Could not process audio file. Generating video without music. Error: {e}")

    # 6. Final Write
    temp_filename = f"final_video_{time.time()}.mp4"
    
    try:
        progress_bar.progress(85, text="Rendering final MP4 file (This might take time)...")
        final_clip.write_videofile(
            temp_filename, 
            fps=fps, 
            codec='libx264', 
            audio=(audio_path is not None), 
            verbose=False, 
            logger=None
        )
        
        progress_bar.progress(100, text="Render complete! ✨")
        time.sleep(1) 
        progress_container.empty()
        
        with open(temp_filename, "rb") as f: video_bytes = f.read()
        os.remove(temp_filename)
        return video_bytes
        
    except Exception as e:
        progress_container.empty()
        st.error(f"Video generation failed during final write. Check FFmpeg/dependency setup. Error: {e}")
        return None


# --- 6. STREAMLIT UI ---

st.title("💎 Verse Studio Premium")

col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("🎨 Design & Animation")
    
    st.selectbox("🎥 Aspect Ratio", list(ASPECT_RATIOS.keys()), key='aspect_ratio_name')
    st.selectbox("Color Theme", PALETTE_NAMES, key='color_theme')
    
    st.markdown("---")
    
    st.selectbox("Audio Track", list(MEDIA_CONFIG["audio"].keys()), key='audio_track')
    st.selectbox("Video BG", list(MEDIA_CONFIG["video_bg"].keys()), key='video_bg_selection')
    
    is_media_bg_selected = st.session_state.video_bg_selection != "None (Use Animated/Image)"
    
    if not is_media_bg_selected:
        st.selectbox("Drawn Animated BG Style", BG_ANIMATIONS, index=1, key='bg_anim')
    else:
        st.session_state.bg_anim = "None"
        st.caption("Video background selected. Drawn Animated BG is disabled.")
    
    st.selectbox("Logo Placement", list(LOGO_PLACEMENTS.keys()), key='logo_placement')

    st.selectbox("Text Animation", TEXT_ANIMATIONS, key='txt_anim')
    
    st.selectbox("Video Quality", list(VIDEO_QUALITIES.keys()), key='quality_name')
    
with col2:
    st.subheader("📖 Verse Selection")
    
    # Use the full list of books
    st.selectbox("Book", BOOK_NAMES, key='book')
    
    # Determine max verses based on the BIBLE_STRUCTURE, defaulting to a high number if the book isn't detailed.
    max_verses = BIBLE_STRUCTURE.get(st.session_state.book, {}).get(st.session_state.chapter, 31) 
    
    # Use the available chapter keys, defaulting to a list if not structured
    available_chapters = list(BIBLE_STRUCTURE.get(st.session_state.book, {1: 31}).keys())
    st.selectbox("Chapter", available_chapters, key='chapter')

    # Ensure verse selection dynamically updates based on the max_verses for the selected chapter
    max_verses_in_chapter = BIBLE_STRUCTURE.get(st.session_state.book, {}).get(st.session_state.chapter, 31)
    available_verses = list(range(1, max_verses_in_chapter + 1))
    st.selectbox("Verse", available_verses, key='verse_num')
    
    st.text_input("Engagement Hook", value=st.session_state.hook, key='hook')

st.markdown("---")

# --- Poster Generation and Display (Preview Logic) ---
pil_poster_img, _, verse_text, final_ref = generate_text_overlay(
    st.session_state.aspect_ratio_name, 
    st.session_state.color_theme, 
    st.session_state.book, 
    st.session_state.chapter, 
    st.session_state.verse_num, 
    st.session_state.hook, 
    st.session_state.bg_anim, 
    st.session_state.txt_anim,
    st.session_state.logo_placement
)
st.image(pil_poster_img, caption=f"{st.session_state.color_theme} | {st.session_state.aspect_ratio_name} | Ref: {final_ref}", use_column_width=True)

st.write(f"**Fetched Verse:** {verse_text}")
st.markdown("---")

# 1. Static PNG Download
buf = io.BytesIO()
pil_poster_img.save(buf, format="PNG") 
st.download_button("⬇️ Download Static Poster PNG", data=buf.getvalue(), file_name=f"verse_{final_ref.replace(' ', '_').replace(':', '')}.png", mime="image/png")

# 2. Animated Video Feature (MP4)
st.subheader("🎬 Animated Video")

if st.button(f"✨ Generate {st.session_state.quality_name} Video"):
    # Resolve media URLs from selection
    audio_url = MEDIA_CONFIG["audio"][st.session_state.audio_track]
    video_bg_url = MEDIA_CONFIG["video_bg"][st.session_state.video_bg_selection]
    
    video_bytes = generate_mp4(
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
        video_bg_url,
        st.session_state.logo_placement
    )
    
    if video_bytes:
        st.video(video_bytes, format="video/mp4")
        st.download_button("⬇️ Download Animated MP4", data=video_bytes, file_name=f"verse_animated_{final_ref.replace(' ', '_').replace(':', '')}.mp4", mime="video/mp4")

st.markdown("---")
st.text_area("Copy Caption for Social Media", f"{st.session_state.hook} Read {final_ref} today. #dailyverse #faith", height=150)

st.info("💡 Next Steps: Add user file uploads and subtle audio volume controls.")

# --- Cleanup Button (for manual trigger) ---
if st.button("🧹 Cleanup Cached Media and Temp Files"):
    cleanup_temp_files()
    st.success("Cleaned up temporary media files!")
