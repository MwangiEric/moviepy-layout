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
MAX_TEXT_WIDTH_RATIO = 0.85 # Max width for text inside the box (85% of box_w)

# NEW: LOGO CONFIG
LOGO_URL = "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037"
LOGO_SIZE = 100
LOGO_PLACEMENTS = {
    "Bottom Right": (1, 1), # (Horizontal, Vertical) normalized
    "Bottom Left": (0, 1),
    "Top Right": (1, 0),
    "Hidden": None
}

# Media URLs
MEDIA_CONFIG = {
    "audio": {
        "None": None,
        "Advertising Music (New)": "https://ik.imagekit.io/ericmwangi/advertising-music-308403.mp3?updatedAt=1764101548797", 
        "Ambient Strings (Placeholder)": "temp_audio_strings.mp3"
    },
    "video_bg": {
        "None (Use Animated/Image)": None,
        "Ocean Waves (New)": "https://ik.imagekit.io/ericmwangi/oceanbg.mp4?updatedAt=1764372632493",
    }
}
PALETTE_NAMES = list(DESIGN_CONFIG["palettes"].keys())
# NEW: ADDED NEW TEXT ANIMATIONS
TEXT_ANIMATIONS = ["None", "Glow Pulse", "Typewriter Effect", "Fade-in Opacity"] 
BG_ANIMATIONS = DESIGN_CONFIG["bg_animations"]
ASPECT_RATIOS = DESIGN_CONFIG["aspect_ratios"]
VIDEO_QUALITIES = DESIGN_CONFIG["video_qualities"]

# BIBLE DATA (OMITTED FOR BREVITY)
BIBLE_STRUCTURE = {
    "Genesis": {1: 31, 2: 25}, 
    "Psalm": {1: 6, 46: 11, 121: 8}, 
    "John": {3: 36, 14: 31},
    "Romans": {8: 39},
}
BOOK_NAMES = list(BIBLE_STRUCTURE.keys())

# --- 2. SESSION STATE INITIALIZATION (OMITTED FOR BREVITY) ---
# Assuming all session state variables are correctly initialized as in the previous step
if 'logo_placement' not in st.session_state: st.session_state.logo_placement = list(LOGO_PLACEMENTS.keys())[0]


# --- 3. HELPER FUNCTIONS (OMITTED FOR BREVITY) ---
# ... (hex_to_rgb, download_font, fetch_verse, get_text_size, smart_wrap_text) ...

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

# NEW: Function to download and cache external media
@st.cache_data(ttl=3600, show_spinner=False)
def cache_media(url: str, file_ext: str) -> str:
    if not url: return None
    temp_path = f"cached_media_{hash(url)}.{file_ext}"
    if os.path.exists(temp_path):
        return temp_path
    
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(temp_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return temp_path
    except Exception as e:
        # Error handling for download failure
        st.error(f"Failed to cache media from URL. Please check the link. Error: {e}")
        return None


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

# --- 4. CORE DRAWING FUNCTION (DYNAMIC LAYOUT & NEW ANIMATIONS) ---

def generate_text_overlay(aspect_ratio_name, palette_name, book, chapter, verse_num, hook, bg_anim, txt_anim, logo_placement, animation_phase=None):
    """
    Generates a transparent RGBA image (overlay) and a composed PIL Image (preview).
    Uses **dynamic layout** to size the text box.
    """
    
    global W, H
    W, H = ASPECT_RATIOS[aspect_ratio_name]
    final_ref = f"{book} {chapter}:{verse_num} (ASV)"
    verse_text_raw = fetch_verse(book, chapter, verse_num)
    pal = DESIGN_CONFIG["palettes"][palette_name]
    
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0)) 
    draw = ImageDraw.Draw(overlay)
    
    phase = animation_phase if animation_phase is not None else time.time() % (2 * math.pi)

    # --- Dynamic Layout Calculation ---
    max_text_width_pixels = W - 2 * MARGIN - 100
    
    hook_lines = smart_wrap_text(hook, HOOK_FONT, max_text_width_pixels)
    verse_lines = smart_wrap_text(verse_text_raw, VERSE_FONT, max_text_width_pixels) 
    ref_lines = smart_wrap_text(final_ref, REF_FONT, max_text_width_pixels)

    line_h_hook = HOOK_FONT.getbbox("A")[3] + 10 
    line_h_verse = VERSE_FONT.getbbox("A")[3] + 8 
    line_h_ref = REF_FONT.getbbox("A")[3] + 6   
    
    # Calculate required content height
    content_height = (len(hook_lines) * line_h_hook) + (len(verse_lines) * line_h_verse) + (len(ref_lines) * line_h_ref)
    
    # Text Box Sizing (Dynamic)
    padding = 100
    box_w = W - 2 * MARGIN
    box_h = content_height + 2 * padding
    
    # Ensure box doesn't exceed 80% of canvas height
    max_allowable_h = H * 0.8
    if box_h > max_allowable_h:
        box_h = int(max_allowable_h)

    box_x, box_y = MARGIN, (H - box_h) // 2
    box_xy = (box_x, box_y, box_x + box_w, box_y + box_h)
    
    # Current Y position inside the box (centered vertically)
    current_y = box_y + (box_h - content_height) // 2

    # Background Animations on overlay (OMITTED FOR BREVITY)
    # ...

    # 3. Text Box 
    box_color = (0, 0, 0, 180) if "Dark" in palette_name else (255, 255, 255, 200)
    draw.rounded_rectangle(box_xy, radius=40, fill=box_color)

    hook_rgb = hex_to_rgb(pal["accent"])
    hook_color = (*hook_rgb, 255)
    verse_fill = (255, 255, 255, 255) 
    glow_fill = (100, 149, 237, 150)
    
    # --- Text Animation Logic ---
    
    # Draw Hook Text
    for line in hook_lines:
        w, h = get_text_size(HOOK_FONT, line)
        draw.text(((W - w)//2, current_y), line, font=HOOK_FONT, fill=hook_color)
        current_y += line_h_hook
    
    # ... (Quote drawing logic) ...
    
    # Draw Verse Text
    text_to_animate = "\n".join(verse_lines)
    
    if txt_anim == "Glow Pulse":
        # ... (Glow Pulse logic remains) ...
        pass
    elif txt_anim == "Typewriter Effect":
        # Text appears character by character based on time (phase)
        total_chars = len(text_to_animate)
        chars_visible = int(total_chars * (phase / (2 * math.pi))) # Map phase to character count (0 to total_chars)
        
        # Draw all text up to the visible character count
        temp_text = text_to_animate[:chars_visible]
        # Re-wrap the currently visible text to maintain alignment
        temp_lines = temp_text.split('\n') 
        
        # Reset y for drawing
        current_y_anim = box_y + (box_h - content_height) // 2 + (len(hook_lines) * line_h_hook) + 20 

        for line in temp_lines:
            w, h = get_text_size(VERSE_FONT, line)
            draw.text(((W - w)//2, current_y_anim), line, font=VERSE_FONT, fill=verse_fill)
            current_y_anim += line_h_verse
        current_y = current_y_anim - 20 # Update final y position
        
    elif txt_anim == "Fade-in Opacity":
        # Text opacity changes based on time (phase)
        opacity = 50 + 205 * (phase / (2 * math.pi)) # 50 (min) to 255 (max)
        fade_fill = (255, 255, 255, int(opacity))
        
        for line in verse_lines:
            w, h = get_text_size(VERSE_FONT, line)
            draw.text(((W - w)//2, current_y), line, font=VERSE_FONT, fill=fade_fill)
            current_y += line_h_verse
    else: 
        # None or Glow Pulse fallback
        for line in verse_lines:
            w, h = get_text_size(VERSE_FONT, line)
            draw.text(((W - w)//2, current_y), line, font=VERSE_FONT, fill=verse_fill)
            current_y += line_h_verse
            
    # ... (Closing quote, separator, and reference drawing logic) ...

    # --- NEW: Logo Placement ---
    if logo_placement != "Hidden":
        logo_img = download_logo(LOGO_URL)
        if logo_img:
            logo_w, logo_h = LOGO_SIZE, LOGO_SIZE
            logo_img = logo_img.resize((logo_w, logo_h))
            
            h_norm, v_norm = LOGO_PLACEMENTS[logo_placement]
            
            # X Calculation: h_norm=0 -> Left (50px); h_norm=1 -> Right (W - logo_w - 50px)
            logo_x = int(50 + h_norm * (W - logo_w - 100))
            # Y Calculation: v_norm=0 -> Top (50px); v_norm=1 -> Bottom (H - logo_h - 50px)
            logo_y = int(50 + v_norm * (H - logo_h - 100))
            
            overlay.paste(logo_img, (logo_x, logo_y), logo_img)

    # --- Return Values ---
    # Fix: Return PIL Image for download compatibility
    preview_bg = create_gradient(W, H, pal["bg"][0], pal["bg"][1])
    preview_bg.paste(overlay, (0, 0), overlay) 
    
    # Return PIL Image for download, NumPy array for MoviePy
    return preview_bg, np.array(overlay), verse_text_raw, final_ref


# --- 5. VIDEO GENERATOR (MoviePy Composition with Media) ---

def generate_mp4(aspect_ratio_name, palette_name, book, chapter, verse_num, hook, bg_anim, txt_anim, quality_name, audio_url, video_bg_url, logo_placement):
    
    duration, fps = VIDEO_QUALITIES[quality_name]
    W_clip, H_clip = ASPECT_RATIOS[aspect_ratio_name]
    pal = DESIGN_CONFIG["palettes"][palette_name]

    # 1. Cache Media (Improved Error Handling & Progress)
    audio_path = None
    video_path = None
    
    # NEW: Progress Bar
    progress_container = st.container()
    progress_bar = progress_container.progress(0, text="Initializing...")
    
    if audio_url:
        progress_bar.progress(10, text="Caching audio...")
        audio_path = cache_media(audio_url, 'mp3')
    
    if video_bg_url:
        progress_bar.progress(20, text="Caching video background...")
        video_path = cache_media(video_bg_url, 'mp4')


    # 2. Define the Overlay Clip (Animated Text, Box, Logo)
    def make_overlay_frame(t):
        # We call the main function, ignore the PIL image, and return the RGBA numpy array
        _, overlay_np, _, _ = generate_text_overlay(aspect_ratio_name, palette_name, book, chapter, verse_num, hook, bg_anim, txt_anim, logo_placement, animation_phase=t)
        return overlay_np
        
    overlay_clip = VideoClip(make_overlay_frame, duration=duration).set_fps(fps)

    # 3. Define the Base Background Clip (Prioritized: Video > Animated Gradient)
    base_clip = None

    if video_path:
        # Video Background
        try:
            progress_bar.progress(30, text="Composing video background...")
            base_clip = VideoFileClip(video_path)
            base_clip = base_clip.fx(vfx.resize, newsize=(W_clip, H_clip))
            
            # Loop the clip if shorter than the required duration
            if base_clip.duration < duration:
                base_clip = base_clip.loop(duration=duration)
            else:
                base_clip = base_clip.subclip(0, duration)
        except Exception as e:
            st.error(f"Failed to load or process video background. Falling back to animated gradient. Error: {e}")
            base_clip = None

    if base_clip is None:
        # Default: Animated Gradient Background
        progress_bar.progress(30, text="Using animated gradient background...")
        def make_gradient_frame(t):
            base_img = create_gradient(W_clip, H_clip, pal["bg"][0], pal["bg"][1])
            # Draw gradient BG animations here
            return np.array(base_img.convert('RGB'))
        base_clip = VideoClip(make_gradient_frame, duration=duration).set_fps(fps)


    # 4. Composition
    progress_bar.progress(40, text="Composing final clip...")
    final_clip = CompositeVideoClip([base_clip, overlay_clip])
    final_clip = final_clip.set_duration(duration).set_fps(fps)

    # 5. Audio Integration and Clipping
    if audio_path:
        try:
            progress_bar.progress(50, text="Adding and clipping audio...")
            audio_clip = AudioFileClip(audio_path)
            
            # CLIP AUDIO to match video duration
            if audio_clip.duration > duration:
                audio_clip = audio_clip.subclip(0, duration)
            elif audio_clip.duration < duration:
                audio_clip = audio_clip.loop(duration=duration)
            
            final_clip = final_clip.set_audio(audio_clip)

        except Exception as e:
            st.warning(f"Could not process audio file. Generating video without music. Error: {e}")

    # 6. Final Write
    temp_filename = f"final_video_{time.time()}.mp4"
    
    try:
        # Using a custom progress hook for the write operation is complex/unstable. 
        # We rely on the spinner/progress bar for resource prep, then let it run.
        progress_bar.progress(60, text="Rendering final MP4 file...")
        final_clip.write_videofile(
            temp_filename, 
            fps=fps, 
            codec='libx264', 
            audio=(audio_path is not None), 
            verbose=False, 
            logger=None
        )
        progress_bar.progress(100, text="Render complete!")
        time.sleep(1) # Pause to show completion
        progress_container.empty()
        
        with open(temp_filename, "rb") as f:
            video_bytes = f.read()
            
        os.remove(temp_filename)
        return video_bytes
        
    except Exception as e:
        progress_container.empty()
        st.error(f"Video generation failed during final write. Check dependencies. Error: {e}")
        if os.path.exists(temp_filename): os.remove(temp_filename)
        return None


# --- 6. STREAMLIT UI ---

st.title("✝️ Verse Studio Premium")

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
    
    # NEW: Logo Placement
    st.selectbox("Logo Placement", list(LOGO_PLACEMENTS.keys()), key='logo_placement')

    # NEW: Text Animations
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
# FIX: The function now returns a PIL Image for the first argument.
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
# FIX: Use the returned PIL Image object directly
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

st.info("📓 Dynamic hook and journaling features are next!")
