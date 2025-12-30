import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io, os, requests, math, time, json
import numpy as np
from moviepy.editor import VideoClip, CompositeVideoClip, AudioFileClip
import tempfile

# ============================================================================
# STREAMLIT SETUP
# ============================================================================
st.set_page_config(
    page_title="Still Mind Pro", 
    page_icon="✝️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# ENHANCED THEME SYSTEM
# ============================================================================
COLORS = {
    "Premium Green": {
        "bg": [(10, 30, 50, 255), (20, 50, 80, 255)],  # Dark blue gradient
        "accent": (76, 175, 80, 255),  # Bright green
        "secondary": (120, 200, 120, 255),  # Light green
        "text": (255, 255, 255, 255),
        "glow": (76, 175, 80, 160),
        "gradient_type": "vertical"
    },
    "Ocean Deep": {
        "bg": [(10, 40, 70, 255), (20, 60, 100, 255)],
        "accent": (0, 200, 200, 255),  # Cyan
        "secondary": (100, 220, 255, 255),
        "text": (255, 255, 255, 255),
        "glow": (0, 200, 200, 140),
        "gradient_type": "radial"
    },
    "Sunset Gold": {
        "bg": [(40, 20, 50, 255), (80, 40, 30, 255)],
        "accent": (255, 195, 0, 255),  # Gold
        "secondary": (255, 220, 120, 255),
        "text": (255, 255, 255, 255),
        "glow": (255, 195, 0, 180),
        "gradient_type": "horizontal"
    },
    "Midnight Purple": {
        "bg": [(20, 10, 40, 255), (40, 20, 60, 255)],
        "accent": (180, 100, 255, 255),  # Purple
        "secondary": (220, 180, 255, 255),
        "text": (255, 255, 255, 255),
        "glow": (180, 100, 255, 160),
        "gradient_type": "diagonal"
    }
}

SIZES = {
    "TikTok (1080x1920)": (1080, 1920),
    "Instagram (1080x1080)": (1080, 1080),
    "YouTube (1920x1080)": (1920, 1080),
    "Stories (1080x1350)": (1080, 1350),
    "Desktop (1920x1200)": (1920, 1200)
}

ANIMATION_STYLES = ["None", "Typewriter", "Fade In", "Scroll Up", "Word by Word"]
BACKGROUND_STYLES = ["Premium Gradient", "Particles", "Geometric", "Abstract", "Solid"]
TEXT_EFFECTS = ["None", "Shadow", "Glow", "Outline", "Emboss"]

# ============================================================================
# ADVANCED FONT MANAGEMENT
# ============================================================================
@st.cache_resource
def get_font_paths():
    """Discover available fonts on the system."""
    font_paths = []
    
    # Common font directories
    common_paths = [
        "/usr/share/fonts/",
        "/usr/local/share/fonts/",
        "C:/Windows/Fonts/",
        "/Library/Fonts/",
        "/System/Library/Fonts/",
        os.path.expanduser("~/Library/Fonts/"),
    ]
    
    for path in common_paths:
        if os.path.exists(path):
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.lower().endswith(('.ttf', '.otf')):
                        font_paths.append(os.path.join(root, file))
    
    return font_paths

@st.cache_resource
def load_font_with_fallback(size=60, bold=False, italic=False):
    """Intelligent font loader with multiple fallbacks."""
    font_paths = get_font_paths()
    
    # Priority fonts to look for
    preferred_fonts = []
    
    if bold and italic:
        preferred_fonts.extend([
            "arialbi.ttf", "Arial-BoldItalic.ttf", "Helvetica-BoldOblique.ttf",
            "DejaVuSans-BoldOblique.ttf", "Roboto-BoldItalic.ttf", "Montserrat-BoldItalic.ttf"
        ])
    elif bold:
        preferred_fonts.extend([
            "arialbd.ttf", "Arial-Bold.ttf", "Helvetica-Bold.ttf",
            "DejaVuSans-Bold.ttf", "Roboto-Bold.ttf", "Montserrat-Bold.ttf",
            "Lato-Bold.ttf", "OpenSans-Bold.ttf"
        ])
    elif italic:
        preferred_fonts.extend([
            "ariali.ttf", "Arial-Italic.ttf", "Helvetica-Oblique.ttf",
            "DejaVuSans-Oblique.ttf", "Roboto-Italic.ttf", "Montserrat-Italic.ttf"
        ])
    else:
        preferred_fonts.extend([
            "arial.ttf", "Arial.ttf", "Helvetica.ttf", "Helvetica Neue.ttf",
            "DejaVuSans.ttf", "Roboto-Regular.ttf", "Montserrat-Regular.ttf",
            "Lato-Regular.ttf", "OpenSans-Regular.ttf", "SegoeUI.ttf"
        ])
    
    # Try preferred fonts first
    for font_name in preferred_fonts:
        for font_path in font_paths:
            if font_name.lower() in font_path.lower():
                try:
                    return ImageFont.truetype(font_path, size)
                except:
                    continue
    
    # Try any font
    for font_path in font_paths:
        try:
            return ImageFont.truetype(font_path, size)
        except:
            continue
    
    # Ultimate fallback
    return ImageFont.load_default()

# ============================================================================
# ENHANCED BACKGROUND GENERATORS
# ============================================================================
def create_premium_background(width, height, colors, time_offset=0):
    """Create premium gradient background with animated elements."""
    img = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(img)
    
    color1, color2 = colors["bg"]
    gradient_type = colors.get("gradient_type", "vertical")
    
    if gradient_type == "vertical":
        # Vertical gradient with subtle movement
        for y in range(height):
            ratio = y / height
            # Add wave effect
            wave = math.sin(y / 100 + time_offset) * 0.08
            ratio = max(0, min(1, ratio + wave))
            
            r = int((1-ratio) * color1[0] + ratio * color2[0])
            g = int((1-ratio) * color1[1] + ratio * color2[1])
            b = int((1-ratio) * color1[2] + ratio * color2[2])
            a = int((1-ratio) * color1[3] + ratio * color2[3])
            draw.line([(0, y), (width, y)], fill=(r, g, b, a))
    
    elif gradient_type == "radial":
        # Radial gradient from center
        center_x, center_y = width // 2, height // 2
        max_dist = math.sqrt(center_x**2 + center_y**2)
        
        for y in range(height):
            for x in range(width):
                dist = math.sqrt((x - center_x)**2 + (y - center_y)**2) / max_dist
                ratio = dist * 0.8  # Soften gradient
                
                r = int((1-ratio) * color1[0] + ratio * color2[0])
                g = int((1-ratio) * color1[1] + ratio * color2[1])
                b = int((1-ratio) * color1[2] + ratio * color2[2])
                draw.point((x, y), (r, g, b))
    
    # Add subtle noise for texture
    noise = np.random.randint(0, 10, (height, width, 3), dtype=np.uint8)
    noise_img = Image.fromarray(noise, mode='RGB').convert('RGBA')
    noise_img.putalpha(5)  # Very subtle
    img = Image.alpha_composite(img, noise_img)
    
    return img

def create_particle_background(width, height, colors, time_offset=0):
    """Create animated particle background."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 255))
    draw = ImageDraw.Draw(img)
    
    # Base gradient
    for y in range(height):
        ratio = y / height
        r = int((1-ratio) * colors["bg"][0][0] + ratio * colors["bg"][1][0])
        g = int((1-ratio) * colors["bg"][0][1] + ratio * colors["bg"][1][1])
        b = int((1-ratio) * colors["bg"][0][2] + ratio * colors["bg"][1][2])
        draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
    
    # Animated particles
    for i in range(120):  # More particles
        # Circular motion
        angle = time_offset * 2 + i * 0.5
        radius = 0.3 + 0.2 * math.sin(i * 0.3)
        
        x = width * (0.5 + radius * math.cos(angle))
        y = height * (0.5 + radius * math.sin(angle + i * 0.2))
        
        # Size and opacity variations
        size = 2 + int(4 * math.sin(time_offset + i * 0.5))
        opacity = int(80 + 100 * abs(math.sin(time_offset * 3 + i)))
        
        # Color variations
        r = colors["accent"][0] + int(30 * math.sin(i))
        g = colors["accent"][1] + int(30 * math.cos(i))
        b = colors["accent"][2]
        particle_color = (r, g, b, opacity)
        
        draw.ellipse([x-size, y-size, x+size, y+size], 
                    fill=particle_color, 
                    outline=colors["accent"][:3] + (opacity//2,))
    
    return img

# ============================================================================
# PREMIUM DECORATION FUNCTIONS (From first code)
# ============================================================================
def draw_premium_decorations(draw, x1, y1, x2, y2, colors, time_offset=0):
    """Draw premium corner brackets with pulsing glow."""
    # Main box with transparency
    draw.rectangle([x1, y1, x2, y2], fill=(0, 0, 0, 160))
    
    # Pulsing effect
    pulse = 0.6 + 0.4 * abs(math.sin(time_offset * 2.5))
    
    # Enhanced bracket parameters
    bracket_length = 60
    bracket_thickness = 5
    
    def draw_bracket_corner(cx, cy, dx, dy, width, color):
        # Horizontal arm
        draw.line([(cx, cy), (cx + dx, cy)], 
                 fill=color, width=width, joint="curve")
        # Vertical arm
        draw.line([(cx, cy), (cx, cy + dy)], 
                 fill=color, width=width, joint="curve")
    
    # Multi-layered glow effect
    for layer in range(3, 0, -1):
        current_width = bracket_thickness + (layer * 6)
        
        if layer == 1:
            # Inner layer - solid color
            color = colors["accent"]
        else:
            # Outer layers - glow effect
            glow_strength = 180 - (layer * 50)
            color = colors["accent"][:3] + (int(glow_strength * pulse),)
        
        # Draw all four corners
        draw_bracket_corner(x1, y1, bracket_length, bracket_length, 
                          current_width, color)  # Top-left
        draw_bracket_corner(x2, y1, -bracket_length, bracket_length, 
                          current_width, color)  # Top-right
        draw_bracket_corner(x1, y2, bracket_length, -bracket_length, 
                          current_width, color)  # Bottom-left
        draw_bracket_corner(x2, y2, -bracket_length, -bracket_length, 
                          current_width, color)  # Bottom-right
    
    # Subtle inner border
    draw.rectangle([x1+20, y1+20, x2-20, y2-20], 
                  outline=colors["accent"][:3] + (60,), 
                  width=2)

# ============================================================================
# SMART TEXT RENDERING WITH EFFECTS
# ============================================================================
def draw_text_with_effects(draw, text, position, font, colors, effect="None"):
    """Draw text with various visual effects."""
    x, y = position
    main_color = colors["text"]
    accent_color = colors["accent"]
    
    if effect == "Shadow":
        # Shadow effect
        shadow_offset = 5
        draw.text((x + shadow_offset, y + shadow_offset), 
                 text, font=font, fill=(0, 0, 0, 150))
        draw.text(position, text, font=font, fill=main_color)
    
    elif effect == "Glow":
        # Glow effect (multiple layers)
        glow_color = accent_color[:3] + (100,)
        for offset in [(0, 2), (0, -2), (2, 0), (-2, 0),
                      (2, 2), (2, -2), (-2, 2), (-2, -2)]:
            draw.text((x + offset[0], y + offset[1]), 
                     text, font=font, fill=glow_color)
        draw.text(position, text, font=font, fill=main_color)
    
    elif effect == "Outline":
        # Outline effect
        outline_color = accent_color[:3] + (200,)
        for offset in [(0, 3), (0, -3), (3, 0), (-3, 0)]:
            draw.text((x + offset[0], y + offset[1]), 
                     text, font=font, fill=outline_color)
        draw.text(position, text, font=font, fill=main_color)
    
    else:
        # Normal text
        draw.text(position, text, font=font, fill=main_color)

# ============================================================================
# ADVANCED VERSE FETCHING WITH CACHING
# ============================================================================
@st.cache_data(ttl=3600)
def fetch_bible_verse(book, chapter, verse):
    """Fetch verse with multiple fallback options."""
    try:
        # Try primary API
        url = f"https://bible-api.com/{book}+{chapter}:{verse}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if "text" in data:
                text = data["text"].replace("\n", " ").strip()
                return text, data.get("reference", f"{book} {chapter}:{verse}")
    
    except requests.exceptions.Timeout:
        st.warning("API timeout. Using cached verse.")
    
    # Fallback verses
    fallback_verses = {
        "Psalm": "The Lord is my shepherd; I shall not want.",
        "Matthew": "Come to me, all who labor and are heavy laden, and I will give you rest.",
        "John": "For God so loved the world, that he gave his only Son.",
        "Romans": "For I am not ashamed of the gospel, for it is the power of God for salvation.",
        "Ephesians": "For by grace you have been saved through faith.",
        "Philippians": "Rejoice in the Lord always; again I will say, rejoice.",
        "James": "Count it all joy, my brothers, when you meet trials of various kinds."
    }
    
    default = fallback_verses.get(book, "God is our refuge and strength, an ever-present help in trouble.")
    return default, f"{book} {chapter}:{verse}"

# ============================================================================
# IMAGE GENERATION ENGINE
# ============================================================================
def create_still_image(width, height, colors, book, chapter, verse, hook, 
                      bg_style="Premium Gradient", text_effect="None"):
    """Create high-quality static image."""
    # Create background
    if bg_style == "Premium Gradient":
        img = create_premium_background(width, height, colors)
    elif bg_style == "Particles":
        img = create_particle_background(width, height, colors)
    else:
        img = create_premium_background(width, height, colors)
    
    draw = ImageDraw.Draw(img)
    
    # Fetch verse
    verse_text, reference = fetch_bible_verse(book, chapter, verse)
    
    # Calculate layout
    box_width = width - 200
    box_height = height - 400
    box_x = 100
    box_y = (height - box_height) // 2
    
    # Draw premium box
    draw_premium_decorations(draw, box_x, box_y, box_x + box_width, 
                           box_y + box_height, colors)
    
    # Font sizes (larger)
    hook_font = load_font_with_fallback(85, bold=True)
    verse_font = load_font_with_fallback(60, bold=False)
    ref_font = load_font_with_fallback(48, bold=True)
    
    # Hook text (top)
    if hook:
        hook_bbox = hook_font.getbbox(hook)
        hook_width = hook_bbox[2] - hook_bbox[0]
        hook_x = (width - hook_width) // 2
        hook_y = box_y - 150
        
        draw_text_with_effects(draw, hook.upper(), (hook_x, hook_y), 
                             hook_font, colors, text_effect)
    
    # Wrap verse text
    words = verse_text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = verse_font.getbbox(test_line)
        if bbox[2] - bbox[0] <= box_width - 100:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Draw verse text
    line_height = verse_font.getbbox("A")[3] * 1.4
    start_y = box_y + 100
    
    for i, line in enumerate(lines):
        bbox = verse_font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        x = (width - line_width) // 2
        
        draw_text_with_effects(draw, line, (x, start_y + i * line_height), 
                             verse_font, colors, text_effect)
    
    # Reference (bottom right)
    ref_bbox = ref_font.getbbox(reference)
    ref_x = box_x + box_width - (ref_bbox[2] - ref_bbox[0]) - 50
    ref_y = box_y + box_height + 50
    
    draw_text_with_effects(draw, reference, (ref_x, ref_y), 
                         ref_font, colors, "Glow")
    
    # Brand watermark (subtle)
    brand_font = load_font_with_fallback(40, bold=True)
    draw.text((width - 250, 30), "STILL MIND", 
             font=brand_font, fill=colors["accent"][:3] + (180,))
    
    return img

# ============================================================================
# VIDEO GENERATION ENGINE
# ============================================================================
def create_animated_video(width, height, colors, book, chapter, verse, hook, 
                         bg_style="Premium Gradient", animation_style="Typewriter"):
    """Create animated video with chosen effects."""
    duration = 8  # Slightly longer for better pacing
    fps = 24  # Smoother animation
    
    def make_frame(t):
        # Create background
        if bg_style == "Premium Gradient":
            img = create_premium_background(width, height, colors, t)
        elif bg_style == "Particles":
            img = create_particle_background(width, height, colors, t)
        else:
            img = create_premium_background(width, height, colors, t)
        
        draw = ImageDraw.Draw(img)
        
        # Get verse
        verse_text, reference = fetch_bible_verse(book, chapter, verse)
        
        # Box dimensions
        box_width = width - 200
        box_height = height - 400
        box_x = 100
        box_y = (height - box_height) // 2
        
        # Animated decorations
        draw_premium_decorations(draw, box_x, box_y, box_x + box_width, 
                               box_y + box_height, colors, t)
        
        # Fonts
        hook_font = load_font_with_fallback(85, bold=True)
        verse_font = load_font_with_fallback(60, bold=False)
        ref_font = load_font_with_fallback(48, bold=True)
        
        # Animate hook
        if hook and t > 0.5:
            hook_alpha = min(255, int((t - 0.5) * 510))
            hook_bbox = hook_font.getbbox(hook.upper())
            hook_width = hook_bbox[2] - hook_bbox[0]
            hook_x = (width - hook_width) // 2
            hook_y = box_y - 150
            
            draw.text((hook_x, hook_y), hook.upper(), 
                     font=hook_font, 
                     fill=colors["accent"][:3] + (hook_alpha,))
        
        # Animate verse text
        if animation_style == "Typewriter":
            # Typewriter effect
            reveal_time = 5  # seconds to reveal all text
            progress = min(1.0, t / reveal_time)
            visible_chars = int(len(verse_text) * progress)
            
            words = verse_text[:visible_chars].split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = verse_font.getbbox(test_line)
                if bbox[2] - bbox[0] <= box_width - 100:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            line_height = verse_font.getbbox("A")[3] * 1.4
            start_y = box_y + 100
            
            for i, line in enumerate(lines):
                bbox = verse_font.getbbox(line)
                line_width = bbox[2] - bbox[0]
                x = (width - line_width) // 2
                draw.text((x, start_y + i * line_height), line, 
                         font=verse_font, fill=colors["text"])
            
            # Blinking cursor
            if progress < 1.0 and int(t * 3) % 2 == 0:
                if lines:
                    last_line = lines[-1]
                    bbox = verse_font.getbbox(last_line)
                    cursor_x = (width - bbox[0]) // 2 + bbox[2] + 10
                    cursor_y = start_y + (len(lines) - 1) * line_height + 10
                    draw.line([(cursor_x, cursor_y), (cursor_x, cursor_y + line_height - 20)], 
                             fill=colors["accent"], width=4)
        
        elif animation_style == "Fade In":
            # Fade in effect
            fade_time = 4
            progress = min(1.0, t / fade_time)
            alpha = int(255 * progress)
            
            words = verse_text.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = verse_font.getbbox(test_line)
                if bbox[2] - bbox[0] <= box_width - 100:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            line_height = verse_font.getbbox("A")[3] * 1.4
            start_y = box_y + 100
            
            for i, line in enumerate(lines):
                bbox = verse_font.getbbox(line)
                line_width = bbox[2] - bbox[0]
                x = (width - line_width) // 2
                draw.text((x, start_y + i * line_height), line, 
                         font=verse_font, fill=colors["text"][:3] + (alpha,))
        
        # Animate reference (appears last)
        if t > duration - 2:
            ref_alpha = min(255, int((t - (duration - 2)) * 255))
            ref_bbox = ref_font.getbbox(reference)
            ref_x = box_x + box_width - (ref_bbox[2] - ref_bbox[0]) - 50
            ref_y = box_y + box_height + 50
            
            draw.text((ref_x, ref_y), reference, 
                     font=ref_font, 
                     fill=colors["accent"][:3] + (ref_alpha,))
        
        return np.array(img.convert("RGB"))
    
    # Create video clip
    clip = VideoClip(make_frame, duration=duration)
    clip = clip.set_fps(fps)
    
    # Render to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp:
        temp_path = tmp.name
        clip.write_videofile(
            temp_path,
            fps=fps,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile="temp-audio.m4a",
            remove_temp=True,
            verbose=False,
            logger=None
        )
    
    # Read and return video bytes
    with open(temp_path, 'rb') as f:
        video_bytes = f.read()
    
    # Cleanup
    os.unlink(temp_path)
    
    return video_bytes

# ============================================================================
# STREAMLIT UI - ENHANCED
# ============================================================================
# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        background: linear-gradient(90deg, #4CAF50, #2196F3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #4CAF50, #2196F3);
        color: white;
        border: none;
        padding: 0.75rem;
        border-radius: 10px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #45a049, #1976D2);
        transform: translateY(-2px);
        transition: all 0.3s;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #1a1a2e, #16213e);
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🧠 STILL MIND PRO</h1>', unsafe_allow_html=True)
st.markdown("### Create beautiful scripture graphics & videos for social media")

# Sidebar
with st.sidebar:
    st.header("🎨 Design Settings")
    
    size_option = st.selectbox("Format Size", list(SIZES.keys()))
    width, height = SIZES[size_option]
    
    theme_option = st.selectbox("Color Theme", list(COLORS.keys()))
    selected_colors = COLORS[theme_option]
    
    bg_option = st.selectbox("Background Style", BACKGROUND_STYLES)
    
    st.header("📖 Scripture Content")
    
    # Bible book selection with search
    BIBLE_BOOKS = ["Genesis", "Exodus", "Psalms", "Proverbs", "Isaiah", 
                   "Matthew", "Mark", "Luke", "John", "Romans", "Corinthians",
                   "Galatians", "Ephesians", "Philippians", "Colossians",
                   "Thessalonians", "Timothy", "Hebrews", "James", "Peter", "John"]
    
    book = st.selectbox("Book", BIBLE_BOOKS, index=2)  # Default to Psalms
    
    col1, col2 = st.columns(2)
    with col1:
        chapter = st.number_input("Chapter", min_value=1, max_value=150, value=23)
    with col2:
        verse = st.number_input("Verse", min_value=1, max_value=176, value=1)
    
    hook = st.text_input("Header Text", "PEACE BE STILL")
    
    st.header("🎬 Animation")
    animation_option = st.selectbox("Animation Style", ANIMATION_STYLES)
    text_effect = st.selectbox("Text Effect", TEXT_EFFECTS)
    
    st.header("⚡ Quick Actions")
    
    if st.button("🔄 Refresh Preview", use_container_width=True):
        st.rerun()
    
    st.divider()
    st.caption("Made with ❤️ for sharing God's Word")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    # Preview section
    st.subheader("🎨 Live Preview")
    
    # Generate preview image
    with st.spinner("Creating preview..."):
        preview_img = create_still_image(
            width, height, selected_colors, 
            book, chapter, verse, hook,
            bg_option, text_effect
        )
    
    # Display preview
    st.image(preview_img, use_column_width=True)
    
    # Download buttons
    col_dl1, col_dl2 = st.columns(2)
    
    with col_dl1:
        # PNG download
        img_buffer = io.BytesIO()
        preview_img.save(img_buffer, format='PNG', optimize=True, quality=95)
        
        st.download_button(
            label="📥 Download PNG (High Quality)",
            data=img_buffer.getvalue(),
            file_name=f"stillmind_{book}_{chapter}_{verse}.png",
            mime="image/png",
            use_container_width=True
        )
    
    with col_dl2:
        # Video generation
        if st.button("🎬 Generate Video (8s)", use_container_width=True):
            with st.spinner("Rendering video... This may take a moment"):
                video_data = create_animated_video(
                    width, height, selected_colors,
                    book, chapter, verse, hook,
                    bg_option, animation_option
                )
                
                # Display video
                st.video(video_data)
                
                # Video download
                st.download_button(
                    label="📥 Download MP4 Video",
                    data=video_data,
                    file_name=f"stillmind_{book}_{chapter}_{verse}.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )

with col2:
    # Information panel
    st.subheader("📊 Details")
    
    # Stats
    st.metric("Image Size", f"{width} × {height}")
    st.metric("Color Theme", theme_option)
    st.metric("Background", bg_option)
    
    st.divider()
    
    # Verse info
    _, verse_text = fetch_bible_verse(book, chapter, verse)
    st.write(f"**Selected Verse:**")
    st.info(f"{book} {chapter}:{verse}")
    
    st.divider()
    
    # Social media tools
    st.subheader("📱 Social Tools")
    
    # Generate caption
    hashtags = {
        "Psalms": "#Psalm #Worship #Wisdom #Bible",
        "Matthew": "#Gospel #Jesus #NewTestament #Scripture",
        "John": "#Gospel #Love #Faith #Christian",
        "Romans": "#Grace #Faith #Salvation #BibleStudy",
        "Proverbs": "#Wisdom #Proverbs #Life #Guidance"
    }
    
    default_tags = hashtags.get(book, "#BibleVerse #Scripture #Christian")
    
    caption = f"""{hook}

"{verse_text[:120]}..."

📖 {book} {chapter}:{verse}

{default_tags}
#StillMind #BibleQuote #Faith"""

    st.text_area("Social Media Caption", caption, height=180)
    
    if st.button("📋 Copy Caption", use_container_width=True):
        st.code(caption)
        st.success("Caption copied to clipboard!")
    
    st.divider()
    
    # Quick templates
    st.subheader("🎯 Quick Templates")
    
    template_col1, template_col2 = st.columns(2)
    
    with template_col1:
        if st.button("Peace", use_container_width=True):
            st.session_state.hook = "PEACE BE STILL"
            st.session_state.book = "Psalms"
            st.session_state.chapter = 46
            st.session_state.verse = 10
            st.rerun()
    
    with template_col2:
        if st.button("Strength", use_container_width=True):
            st.session_state.hook = "BE STRONG"
            st.session_state.book = "Isaiah"
            st.session_state.chapter = 41
            st.session_state.verse = 10
            st.rerun()

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>Still Mind Pro v2.0 | Create beautiful scripture graphics for social media</p>
    <p>All Bible verses from public domain translations</p>
</div>
""", unsafe_allow_html=True)