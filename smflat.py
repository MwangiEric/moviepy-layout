import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io, os, math, time, random, textwrap
import numpy as np
from moviepy.editor import VideoClip

# ============================================================================
# COMPREHENSIVE EMOTIONAL THEME SYSTEM
# ============================================================================
st.set_page_config(
    page_title="Still Mind: Emotional Studio",
    page_icon="💖",
    layout="wide",
    initial_sidebar_state="expanded"
)

EMOTIONAL_THEMES = {
    "Morning Calm": {
        "mood": "Peaceful",
        "bg": (230, 240, 245, 255),       # Soft blue sky
        "primary": (76, 175, 80, 255),    # Emerald green
        "accent": (100, 150, 200, 255),   # Trust blue
        "surface": (255, 255, 255, 230),  # White overlay
        "text": (25, 50, 70, 255),        # Dark blue text
        "character_skin": (255, 224, 189, 255),
        "character_clothes": (41, 128, 185, 255)
    },
    "Sunset Hope": {
        "mood": "Hopeful",
        "bg": (255, 107, 107, 255),       # Sunset pink
        "primary": (255, 217, 61, 255),   # Golden yellow
        "accent": (255, 152, 0, 255),     # Sunrise orange
        "surface": (255, 250, 230, 230),  # Warm cream overlay
        "text": (70, 40, 20, 255),        # Dark brown text
        "character_skin": (255, 204, 153, 255),
        "character_clothes": (216, 67, 21, 255)
    },
    "Night Strength": {
        "mood": "Strong",
        "bg": (10, 12, 26, 255),          # Deep indigo
        "primary": (100, 149, 237, 255),  # Cornflower blue
        "accent": (255, 235, 59, 255),    # Bright yellow
        "surface": (30, 35, 60, 200),     # Dark overlay
        "text": (255, 255, 255, 230),     # White text
        "character_skin": (200, 170, 150, 255),
        "character_clothes": (44, 62, 80, 255)
    },
    "Desert Journey": {
        "mood": "Resilient",
        "bg": (255, 213, 128, 255),       # Desert sand
        "primary": (78, 52, 46, 255),     # Deep brown
        "accent": (216, 67, 21, 255),     # Burnt orange
        "surface": (255, 255, 255, 200),  # Light overlay
        "text": (40, 30, 20, 255),        # Dark brown text
        "character_skin": (245, 222, 179, 255),
        "character_clothes": (139, 69, 19, 255)
    }
}

# ============================================================================
# ADVANCED CHARACTER SYSTEM
# ============================================================================
def create_flat_character(draw, x, y, t, theme, character_type="meditating"):
    """Create animated flat characters with emotional expressions."""
    colors = theme
    sway = math.sin(t * 1.8) * 6  # Gentle body sway
    
    if character_type == "meditating":
        # Meditating person (breathing animation)
        breath_progress = (math.sin(t * 0.8) + 1) / 2
        
        # Body (simple oval)
        body_height = 120 + 10 * breath_progress
        draw.ellipse([x-40, y-body_height//2, x+40, y+body_height//2], 
                    fill=colors["character_clothes"])
        
        # Head with gentle nodding
        head_y = y - body_height//2 - 30 + math.sin(t * 0.5) * 3
        draw.ellipse([x-25, head_y-25, x+25, head_y+25], 
                    fill=colors["character_skin"])
        
        # Closed eyes (meditation)
        eye_y_offset = 2 if math.sin(t * 0.3) > 0 else 0
        draw.line([(x-10, head_y-eye_y_offset), (x-5, head_y-eye_y_offset)], 
                 fill=(50, 50, 50), width=2)
        draw.line([(x+5, head_y-eye_y_offset), (x+10, head_y-eye_y_offset)], 
                 fill=(50, 50, 50), width=2)
        
        # Slight smile
        mouth_y = head_y + 10
        mouth_curve = 5 * math.sin(t * 0.4)
        draw.arc([x-8, mouth_y-2, x+8, mouth_y+8], 
                 start=-mouth_curve, end=180+mouth_curve, 
                 fill=(50, 50, 50), width=2)
    
    elif character_type == "talking":
        # Talking person with gestures
        # Body with sway
        body_y = y + sway
        draw.rounded_rectangle([x-35, body_y-100, x+35, body_y], 
                              radius=15, fill=colors["character_clothes"])
        
        # Head with talking motion
        head_y = body_y - 130 + math.sin(t * 3) * 5
        draw.ellipse([x-30, head_y-30, x+30, head_y+30], 
                    fill=colors["character_skin"])
        
        # Blinking eyes
        blink = 1 if (t % 4) < 0.15 else 8
        draw.ellipse([x-12, head_y-5, x-6, head_y-5+blink], 
                    fill=(50, 50, 50))
        draw.ellipse([x+6, head_y-5, x+12, head_y-5+blink], 
                    fill=(50, 50, 50))
        
        # Talking mouth
        mouth_open = abs(math.sin(t * 12)) * 12
        draw.ellipse([x-8, head_y+10, x+8, head_y+10+mouth_open], 
                    fill=(50, 50, 50))
        
        # Pointing arm
        point_x = x + 60 + math.sin(t * 5) * 10
        point_y = body_y - 60 + math.cos(t * 5) * 10
        draw.line([(x+35, body_y-70), (point_x, point_y)], 
                 fill=colors["character_skin"], width=12)
        draw.ellipse([point_x-8, point_y-8, point_x+8, point_y+8], 
                    fill=colors["character_skin"])
    
    elif character_type == "praying":
        # Praying hands character
        # Body
        draw.rounded_rectangle([x-30, y-110, x+30, y], 
                              radius=12, fill=colors["character_clothes"])
        
        # Head
        head_y = y - 140
        draw.ellipse([x-25, head_y-25, x+25, head_y+25], 
                    fill=colors["character_skin"])
        
        # Closed eyes
        draw.line([(x-10, head_y), (x-4, head_y)], fill=(50, 50, 50), width=2)
        draw.line([(x+4, head_y), (x+10, head_y)], fill=(50, 50, 50), width=2)
        
        # Praying hands
        hand_x = x
        hand_y = y - 80
        for offset in [-15, 15]:
            draw.rounded_rectangle([hand_x+offset-8, hand_y-15, 
                                   hand_x+offset+8, hand_y+15], 
                                  radius=4, fill=colors["character_skin"])
    
    elif character_type == "celebrating":
        # Celebrating/joyful character
        # Jumping body
        jump = math.sin(t * 3) * 20
        body_y = y + jump
        
        draw.rounded_rectangle([x-35, body_y-100, x+35, body_y], 
                              radius=15, fill=colors["character_clothes"])
        
        # Head
        head_y = body_y - 130
        draw.ellipse([x-30, head_y-30, x+30, head_y+30], 
                    fill=colors["character_skin"])
        
        # Big smile
        draw.arc([x-15, head_y+5, x+15, head_y+25], 
                 start=0, end=180, fill=(50, 50, 50), width=3)
        
        # Raised arms
        arm_wave = math.sin(t * 5) * 15
        for side in [-1, 1]:
            draw.line([(x+side*30, body_y-70), 
                      (x+side*50, body_y-100+arm_wave)], 
                     fill=colors["character_skin"], width=10)
        
        # Star above head (celebration)
        star_y = head_y - 40
        for i in range(5):
            angle = i * 72 * math.pi / 180 + t
            point_x = x + 20 * math.cos(angle)
            point_y = star_y + 20 * math.sin(angle)
            next_angle = (i+2) * 72 * math.pi / 180 + t
            next_x = x + 20 * math.cos(next_angle)
            next_y = star_y + 20 * math.sin(next_angle)
            draw.line([(point_x, point_y), (next_x, next_y)], 
                     fill=colors["primary"], width=3)
    
    return draw

# ============================================================================
# EMOTIONAL ANIMATION ELEMENTS
# ============================================================================
def create_breathing_circle(draw, x, y, t, colors, emotion="calm"):
    """Animated breathing circle with emotional pacing."""
    if emotion == "calm":
        breath_rate = 0.5
        min_size = 40
        max_size = 60
    elif emotion == "anxious":
        breath_rate = 3.0
        min_size = 30
        max_size = 50
    else:
        breath_rate = 1.0
        min_size = 35
        max_size = 55
    
    breath_progress = (math.sin(t * breath_rate * 2 * math.pi) + 1) / 2
    size = min_size + (max_size - min_size) * breath_progress
    
    # Outer circle
    draw.ellipse([x-size, y-size, x+size, y+size], 
                outline=colors["primary"], width=4)
    
    # Inner pulse
    pulse_size = 10 + 6 * math.sin(t * 4)
    draw.ellipse([x-pulse_size, y-pulse_size, x+pulse_size, y+pulse_size], 
                fill=colors["primary"])
    
    return size

def create_heartbeat_animation(draw, x, y, t, colors):
    """Animated heartbeat with emotional impact."""
    beat_intensity = abs(math.sin(t * 6)) * 15
    
    # Heart shape (simplified)
    points = [
        (x, y - 30 - beat_intensity),  # Top
        (x + 25 + beat_intensity/2, y),  # Right
        (x, y + 20 + beat_intensity),  # Bottom
        (x - 25 - beat_intensity/2, y)   # Left
    ]
    
    # Pulsing color
    pulse_factor = 0.8 + 0.4 * math.sin(t * 10)
    heart_color = tuple(min(255, int(c * pulse_factor)) for c in colors["primary"][:3])
    
    draw.polygon(points, fill=heart_color)
    
    # Glow effect
    for glow in range(3):
        glow_size = beat_intensity * (glow + 1) / 3
        draw.polygon([(p[0], p[1] + glow*2) for p in points], 
                    outline=heart_color[:3] + (100 - glow*30,), width=2)
    
    return beat_intensity

def create_growing_tree(draw, x, y, t, colors):
    """Tree that grows over time, symbolizing growth."""
    growth_progress = min(1.0, t / 3)
    
    # Trunk
    trunk_height = 120 * growth_progress
    trunk_width = 15
    
    if growth_progress > 0:
        draw.rectangle([x-trunk_width//2, y, 
                       x+trunk_width//2, y-trunk_height], 
                      fill=colors["accent"])
    
    # Leaves (appear later)
    leaves_progress = max(0, (growth_progress - 0.3) / 0.7)
    
    if leaves_progress > 0:
        leaf_size = 35 * leaves_progress
        leaf_count = 3
        
        for i in range(leaf_count):
            angle = i * (2 * math.pi / leaf_count) + t * 0.5
            leaf_x = x + (trunk_height * 0.4) * math.cos(angle)
            leaf_y = y - trunk_height + (trunk_height * 0.4) * math.sin(angle)
            
            draw.ellipse([leaf_x-leaf_size, leaf_y-leaf_size,
                         leaf_x+leaf_size, leaf_y+leaf_size],
                        fill=colors["primary"])
    
    return trunk_height

def create_rising_sun(draw, width, height, t, colors):
    """Sunrise/sunset animation with emotional warmth."""
    rise_progress = min(1.0, t / 4)
    
    sun_y = height * 0.7 - (rise_progress * height * 0.4)
    sun_x = width * 0.3 + rise_progress * width * 0.4
    sun_size = 70
    
    # Sun body
    draw.ellipse([sun_x-sun_size, sun_y-sun_size,
                 sun_x+sun_size, sun_y+sun_size],
                fill=colors["primary"])
    
    # Rays (appear gradually)
    if rise_progress > 0.3:
        ray_count = 8
        ray_length = 50 * rise_progress
        
        for i in range(ray_count):
            angle = i * (2 * math.pi / ray_count) + t * 0.2
            start_x = sun_x + (sun_size + 5) * math.cos(angle)
            start_y = sun_y + (sun_size + 5) * math.sin(angle)
            end_x = start_x + ray_length * math.cos(angle)
            end_y = start_y + ray_length * math.sin(angle)
            
            draw.line([(start_x, start_y), (end_x, end_y)],
                     fill=colors["primary"], width=4)
    
    return sun_y

def create_flowing_lines(draw, width, height, t, colors):
    """Flowing lines representing breath, water, or grace."""
    line_count = 5
    
    for i in range(line_count):
        y_base = height * 0.3 + i * 50
        amplitude = 20 + i * 5
        frequency = 0.02 + i * 0.005
        
        points = []
        for x in range(0, width, 20):
            y = y_base + amplitude * math.sin(frequency * x + t * 2 + i)
            points.append((x, y))
        
        # Draw smooth line
        if len(points) > 1:
            for j in range(len(points)-1):
                draw.line([points[j], points[j+1]], 
                         fill=colors["primary"][:3] + (200 - i*40,), 
                         width=3)

def create_star_field(draw, width, height, t, colors):
    """Twinkling stars for night themes."""
    # Fixed star positions (consistent across frames)
    random.seed(42)  # Fixed seed for consistent star positions
    star_count = 80
    
    for i in range(star_count):
        star_x = random.randint(0, width)
        star_y = random.randint(0, int(height * 0.6))
        
        # Twinkle effect
        twinkle = abs(math.sin(t * 3 + i)) * 0.7 + 0.3
        star_size = 1 + int(3 * twinkle)
        star_alpha = int(255 * twinkle)
        
        draw.ellipse([star_x-star_size, star_y-star_size,
                     star_x+star_size, star_y+star_size],
                    fill=(255, 255, 255, star_alpha))

def create_desert_dunes(draw, width, height, t, colors):
    """Animated desert dunes with parallax effect."""
    # Background dunes (slow)
    for i in range(-1, 3):
        dune_x = (i * 800) + (t * 15)
        dune_y = height * 0.6
        dune_width = 900
        dune_height = height * 0.5
        
        # Dune shape
        points = [
            (dune_x, dune_y),
            (dune_x + dune_width * 0.3, dune_y - dune_height * 0.3),
            (dune_x + dune_width * 0.7, dune_y - dune_height * 0.2),
            (dune_x + dune_width, dune_y),
            (dune_x + dune_width, height),
            (dune_x, height)
        ]
        
        draw.polygon(points, fill=colors["accent"][:3] + (180,))
    
    # Foreground dunes (faster)
    for i in range(-1, 3):
        dune_x = (i * 900) - (t * 30)
        dune_y = height * 0.7
        
        # Simpler dune shape
        draw.ellipse([dune_x-100, dune_y, dune_x+1000, height*1.3],
                    fill=colors["primary"][:3] + (200,))

# ============================================================================
# TEXT ANIMATION SYSTEM
# ============================================================================
def animate_text_typewriter(draw, text, x, y, t, font, colors, duration=3):
    """Typewriter text animation with emotional pacing."""
    progress = min(1.0, t / duration)
    visible_chars = int(len(text) * progress)
    visible_text = text[:visible_chars]
    
    # Draw text
    draw.text((x, y), visible_text, font=font, fill=colors["text"])
    
    # Blinking cursor
    if progress < 1.0 and int(t * 2) % 2 == 0:
        cursor_x = x + font.getbbox(visible_text)[2] - font.getbbox(visible_text)[0] + 5
        cursor_y = y + font.getbbox(visible_text)[3] - font.getbbox(visible_text)[1]
        draw.line([(cursor_x, y), (cursor_x, cursor_y)], 
                 fill=colors["primary"], width=3)
    
    return visible_text

def animate_text_fade(draw, text, x, y, t, font, colors, duration=2):
    """Fade-in text animation."""
    progress = min(1.0, t / duration)
    alpha = int(255 * progress)
    
    # Draw text with fade
    draw.text((x, y), text, font=font, 
             fill=colors["text"][:3] + (alpha,))
    
    return progress

def animate_text_word_by_word(draw, text, x, y, t, font, colors, word_delay=0.3):
    """Word-by-word text reveal."""
    words = text.split()
    words_shown = min(len(words), int(t / word_delay))
    visible_text = " ".join(words[:words_shown])
    
    draw.text((x, y), visible_text, font=font, fill=colors["text"])
    
    return words_shown

# ============================================================================
# MAIN COMPOSITION ENGINE
# ============================================================================
def create_emotional_composition(width, height, theme_name, character_type, 
                                verse_text, hook_text, t=0, is_video=False):
    """Create complete emotional composition."""
    colors = EMOTIONAL_THEMES[theme_name]
    
    # Create base image
    img = Image.new("RGBA", (width, height), colors["bg"])
    draw = ImageDraw.Draw(img)
    
    # Background animations based on theme
    if "Night" in theme_name:
        create_star_field(draw, width, height, t, colors)
        # Crescent moon
        moon_x = width * 0.8
        moon_y = height * 0.2
        moon_size = 60
        draw.ellipse([moon_x-moon_size, moon_y-moon_size,
                     moon_x+moon_size, moon_y+moon_size],
                    fill=colors["primary"])
        # Moon crescent effect
        draw.ellipse([moon_x-moon_size*0.7, moon_y-moon_size*1.1,
                     moon_x+moon_size*0.3, moon_y+moon_size*0.9],
                    fill=colors["bg"])
    
    elif "Desert" in theme_name:
        create_desert_dunes(draw, width, height, t, colors)
        # Sun
        sun_x = width * 0.8
        sun_y = height * 0.15
        sun_size = 80
        draw.ellipse([sun_x-sun_size, sun_y-sun_size,
                     sun_x+sun_size, sun_y+sun_size],
                    fill=colors["primary"])
    
    elif "Sunset" in theme_name:
        create_rising_sun(draw, width, height, t, colors)
        create_flowing_lines(draw, width, height, t, colors)
    
    else:  # Morning Calm
        create_breathing_circle(draw, width//2, height//2 - 100, t, colors, "calm")
        create_flowing_lines(draw, width, height, t, colors)
    
    # Character
    character_x = width // 2
    character_y = height - 300
    create_flat_character(draw, character_x, character_y, t, colors, character_type)
    
    # Floating scripture panel (safe zone)
    panel_width = min(900, width - 100)
    panel_height = 500
    panel_x = (width - panel_width) // 2
    panel_y = 250 + math.sin(t * 1.5) * 10  # Gentle floating
    
    # Panel background
    draw.rounded_rectangle([panel_x, panel_y, 
                           panel_x + panel_width, panel_y + panel_height],
                          radius=35, fill=colors["surface"])
    
    # Panel border
    draw.rounded_rectangle([panel_x, panel_y, 
                           panel_x + panel_width, panel_y + panel_height],
                          radius=35, outline=colors["primary"], width=4)
    
    # Load fonts
    try:
        title_font = ImageFont.truetype("arialbd.ttf", 52)
        verse_font = ImageFont.truetype("arial.ttf", 42)
        ref_font = ImageFont.truetype("arial.ttf", 36)
    except:
        title_font = ImageFont.load_default(52)
        verse_font = ImageFont.load_default(42)
        ref_font = ImageFont.load_default(36)
    
    # Hook/title
    if hook_text:
        title_bbox = title_font.getbbox(hook_text.upper())
        title_x = panel_x + (panel_width - (title_bbox[2] - title_bbox[0])) // 2
        title_y = panel_y - 90
        
        draw.text((title_x, title_y), hook_text.upper(), 
                 font=title_font, fill=colors["primary"])
    
    # Verse text with wrapping
    verse_lines = textwrap.wrap(verse_text, width=40)
    line_height = 55
    verse_start_y = panel_y + 80
    
    for i, line in enumerate(verse_lines):
        if is_video:
            # Animate line by line
            line_delay = 0.5
            line_alpha = int(255 * min(1.0, max(0, (t - i * line_delay) / 1)))
            line_color = colors["text"][:3] + (line_alpha,)
        else:
            line_color = colors["text"]
        
        line_bbox = verse_font.getbbox(line)
        line_x = panel_x + (panel_width - (line_bbox[2] - line_bbox[0])) // 2
        line_y = verse_start_y + i * line_height
        
        draw.text((line_x, line_y), line, font=verse_font, fill=line_color)
    
    # Reference (appears last in video)
    reference = "— Psalm 46:10 —"
    ref_bbox = ref_font.getbbox(reference)
    ref_x = panel_x + (panel_width - (ref_bbox[2] - ref_bbox[0])) // 2
    ref_y = panel_y + panel_height + 60
    
    if is_video:
        ref_alpha = int(255 * max(0, min(1.0, (t - 3) / 1)))
        ref_color = colors["primary"][:3] + (ref_alpha,)
    else:
        ref_color = colors["primary"]
    
    draw.text((ref_x, ref_y), reference, font=ref_font, fill=ref_color)
    
    # Brand watermark
    brand_font = ImageFont.load_default(28)
    draw.text((30, 30), "STILL MIND EMOTIONAL", 
             font=brand_font, fill=colors["text"][:3] + (150,))
    
    return img

# ============================================================================
# VIDEO GENERATION
# ============================================================================
def create_emotional_video(width, height, theme_name, character_type, 
                          verse_text, hook_text):
    """Create emotional animation video."""
    duration = 7  # seconds
    fps = 24
    
    def make_frame(t):
        img = create_emotional_composition(
            width, height, theme_name, character_type,
            verse_text, hook_text, t, True
        )
        return np.array(img.convert("RGB"))
    
    clip = VideoClip(make_frame, duration=duration)
    clip = clip.set_fps(fps)
    
    # Create temporary file
    import tempfile
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    temp_path = temp_file.name
    
    try:
        clip.write_videofile(
            temp_path,
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            verbose=False,
            logger=None
        )
        
        with open(temp_path, 'rb') as f:
            video_bytes = f.read()
        
        return video_bytes
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

# ============================================================================
# STREAMLIT UI
# ============================================================================
st.title("💖 Still Mind: Emotional Animation Studio")
st.markdown("### Create emotionally resonant scripture animations")

# Custom CSS
st.markdown("""
<style>
    .stButton > button {
        background: linear-gradient(90deg, #4CAF50, #2196F3);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 10px;
        font-weight: bold;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .stSelectbox > div > div {
        background-color: white;
    }
    .stTextArea > div > div > textarea {
        font-size: 1.1rem;
        line-height: 1.5;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("🎨 Emotional Settings")
    
    # Theme selection
    theme_option = st.selectbox(
        "Emotional Theme",
        list(EMOTIONAL_THEMES.keys()),
        help="Choose the emotional tone for your animation"
    )
    
    # Character selection
    character_option = st.selectbox(
        "Character Pose",
        ["meditating", "talking", "praying", "celebrating"],
        format_func=lambda x: x.title(),
        help="Choose how the character expresses the emotion"
    )
    
    st.header("📝 Content")
    
    # Hook/Title
    hook_text = st.text_input(
        "Title/Hook",
        "BE STILL AND KNOW",
        help="Short, powerful text that appears above the verse"
    )
    
    # Verse text
    verse_text = st.text_area(
        "Scripture Verse",
        "Be still, and know that I am God. I will be exalted among the nations, I will be exalted in the earth.",
        height=120,
        help="The main scripture text (will be automatically wrapped)"
    )
    
    # Bible reference
    bible_books = ["Psalm", "Matthew", "John", "Isaiah", "Romans", 
                   "Philippians", "James", "Proverbs", "Ecclesiastes"]
    col1, col2, col3 = st.columns(3)
    with col1:
        book = st.selectbox("Book", bible_books)
    with col2:
        chapter = st.number_input("Chapter", 1, 150, 46)
    with col3:
        verse = st.number_input("Verse", 1, 176, 10)
    
    st.header("🎬 Animation")
    
    # Time scrubber
    time_scrubber = st.slider(
        "Animation Preview Time",
        0.0, 7.0, 0.0, 0.1,
        help="Drag to preview different moments in the animation"
    )
    
    # Size selection
    size_option = st.selectbox(
        "Output Size",
        ["TikTok (1080x1920)", "Instagram (1080x1080)", "Stories (1080x1350)"]
    )
    
    if "1920" in size_option:
        WIDTH, HEIGHT = 1080, 1920
    elif "1350" in size_option:
        WIDTH, HEIGHT = 1080, 1350
    else:
        WIDTH, HEIGHT = 1080, 1080

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    # Preview section
    st.subheader("🎭 Live Preview")
    
    with st.spinner(f"Creating {theme_option.lower()} scene..."):
        preview_img = create_emotional_composition(
            WIDTH, HEIGHT, theme_option, character_option,
            verse_text, hook_text, time_scrubber, False
        )
    
    st.image(preview_img, use_column_width=True)
    
    # Action buttons
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        # Download PNG
        img_buffer = io.BytesIO()
        preview_img.save(img_buffer, format='PNG', optimize=True, quality=95)
        
        st.download_button(
            label="📥 Download PNG",
            data=img_buffer.getvalue(),
            file_name=f"emotional_{theme_option.lower().replace(' ', '_')}.png",
            mime="image/png",
            use_container_width=True
        )
    
    with col_btn2:
        # Generate video
        if st.button("🎬 Create Emotional Video (7s)", use_container_width=True):
            with st.spinner("Animating emotions..."):
                video_data = create_emotional_video(
                    WIDTH, HEIGHT, theme_option, character_option,
                    verse_text, hook_text
                )
                
                if video_data:
                    st.video(video_data)
                    
                    # Video download button
                    st.download_button(
                        label="📥 Download MP4",
                        data=video_data,
                        file_name=f"emotional_{theme_option.lower().replace(' ', '_')}.mp4",
                        mime="video/mp4",
                        use_container_width=True
                    )

with col2:
    # Info panel
    st.subheader("💡 Emotional Guide")
    
    theme_info = EMOTIONAL_THEMES[theme_option]
    st.write(f"**Mood:** {theme_info['mood']}")
    
    st.write("**Theme Elements:**")
    if "Night" in theme_option:
        st.success("✓ Twinkling Stars")
        st.success("✓ Crescent Moon")
        st.success("✓ Deep Colors")
    elif "Desert" in theme_option:
        st.success("✓ Animated Dunes")
        st.success("✓ Warm Sun")
        st.success("✓ Earth Tones")
    elif "Sunset" in theme_option:
        st.success("✓ Rising Sun")
        st.success("✓ Flowing Lines")
        st.success("✓ Warm Colors")
    else:
        st.success("✓ Breathing Circle")
        st.success("✓ Flowing Lines")
        st.success("✓ Calm Colors")
    
    st.write(f"**Character:** {character_option.title()}")
    
    st.metric("Output Size", f"{WIDTH} × {HEIGHT}")
    
    st.divider()
    
    # Emotional impact guide
    st.subheader("🎯 Emotional Impact")
    
    impact_guide = {
        "meditating": "Calms the mind, reduces anxiety",
        "talking": "Creates connection, feels personal",
        "praying": "Inspires reverence, spiritual focus",
        "celebrating": "Uplifts mood, creates joy"
    }
    
    st.info(f"**{character_option.title()}** effect: {impact_guide[character_option]}")
    
    st.divider()
    
    # Social media caption
    st.subheader("📱 Social Share")
    
    emotion_hashtags = {
        "Morning Calm": "#Calm #Peace #Mindfulness #Meditation",
        "Sunset Hope": "#Hope #Sunset #NewBeginnings #Optimism",
        "Night Strength": "#Strength #Night #Courage #Resilience",
        "Desert Journey": "#Journey #Desert #Growth #Perseverance"
    }
    
    caption = f"""{hook_text}

"{verse_text[:80]}..."

— {book} {chapter}:{verse} —

{emotion_hashtags.get(theme_option, '#Faith #Inspiration')}
#StillMind #EmotionalDesign #Scripture"""
    
    st.text_area("Social Media Caption", caption, height=150)
    
    if st.button("📋 Copy Caption", use_container_width=True):
        st.code(caption)
        st.success("Copied to clipboard!")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem;'>
    <p>💖 Still Mind Emotional Studio • Create animations that touch hearts • Psalm 46:10</p>
</div>
""", unsafe_allow_html=True)

# Cleanup
for file in os.listdir("."):
    if file.startswith("temp_") and file.endswith(".mp4"):
        try:
            if time.time() - os.path.getctime(file) > 300:
                os.remove(file)
        except:
            pass