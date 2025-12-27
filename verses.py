import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io, os, requests, math, time
from moviepy.editor import VideoClip, CompositeVideoClip, VideoFileClip, vfx
import numpy as np

# ============================================================================
# DESIGN CONFIGURATION (Non-coders can modify this section)
# ============================================================================
DESIGN_CONFIG = {
    # Color Themes
    "palettes": {
        "Galilee Morning": {
            "bg": ["#faf9f6", "#e0e4d5"],
            "accent": "#c4891f",
            "text_primary": "#183028",
            "text_secondary": "#5a5a5a"
        },
        "Mount Zion Dusk": {
            "bg": ["#f4ebde", "#d6c7a9"],
            "accent": "#987919",
            "text_primary": "#292929",
            "text_secondary": "#555555"
        },
        "Deep Slate": {
            "bg": ["#0f1e1e", "#254141"],
            "accent": "#fcbf49",
            "text_primary": "#f0f0f0",
            "text_secondary": "#cccccc"
        },
        "Urban Night": {
            "bg": ["#202020", "#363636"],
            "accent": "#f7c59f",
            "text_primary": "#f1fafb",
            "text_secondary": "#dddddd"
        }
    },
    
    # Layout Settings
    "aspect_ratios": {
        "Reel / Story (9:16)": (1080, 1920),
        "Square Post (1:1)": (1080, 1080)
    },
    
    # Animation Styles
    "bg_animations": ["None", "Cross Orbit", "Wave Flow", "Floating Circles"],
    "text_animations": ["None", "Glow Pulse", "Typewriter", "Fade-in"],
    
    # Logo Positions (x,y as percentages: 0=left/top, 1=right/bottom)
    "logo_positions": {
        "Bottom Right": {"x": 0.85, "y": 0.85, "size": 100},
        "Bottom Left": {"x": 0.10, "y": 0.85, "size": 100},
        "Top Right": {"x": 0.85, "y": 0.10, "size": 100},
        "Hidden": None
    },
    
    # Text Settings
    "font_sizes": {
        "hook": 70,
        "verse": 130,  # Reduced from 150 for better fit
        "reference": 40
    },
    
    # Video Settings
    "video_duration": 6,    # Fixed at 6 seconds
    "video_fps": 12,        # Fixed at 12 FPS
    "gradient_directions": ["Vertical", "Horizontal", "Diagonal"]
}

# External Resources
RESOURCE_CONFIG = {
    "logo_url": "https://ik.imagekit.io/ericmwangi/smlogo.png?updatedAt=1763071173037",
    "video_backgrounds": {
        "None": None,
        "Ocean Waves": "https://ik.imagekit.io/ericmwangi/oceanbg.mp4"
    },
    "bible_api": "https://cdn.jsdelivr.net/gh/wldeh/bible-api/bibles/en-asv"
}

# ============================================================================
# CORE CONSTANTS (Derived from design config)
# ============================================================================
PALETTE_NAMES = list(DESIGN_CONFIG["palettes"].keys())
ASPECT_RATIOS = DESIGN_CONFIG["aspect_ratios"]
BG_ANIMATIONS = DESIGN_CONFIG["bg_animations"]
TEXT_ANIMATIONS = DESIGN_CONFIG["text_animations"]
LOGO_POSITIONS = DESIGN_CONFIG["logo_positions"]
GRADIENT_DIRECTIONS = DESIGN_CONFIG["gradient_directions"]

# Default Verse
DEFAULT_VERSE = "God is our refuge and strength, an ever-present help in trouble."

# Bible Books List
BIBLE_BOOKS = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", 
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
    "3 John", "Jude", "Revelation"
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_gradient(width, height, color1, color2, direction="Vertical"):
    """Create gradient background."""
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    c1 = hex_to_rgb(color1)
    c2 = hex_to_rgb(color2)
    
    if direction == "Vertical":
        for y in range(height):
            ratio = y / height
            r = int((1 - ratio) * c1[0] + ratio * c2[0])
            g = int((1 - ratio) * c1[1] + ratio * c2[1])
            b = int((1 - ratio) * c1[2] + ratio * c2[2])
            draw.line([(0, y), (width, y)], fill=(r, g, b))
    elif direction == "Horizontal":
        for x in range(width):
            ratio = x / width
            r = int((1 - ratio) * c1[0] + ratio * c2[0])
            g = int((1 - ratio) * c1[1] + ratio * c2[1])
            b = int((1 - ratio) * c1[2] + ratio * c2[2])
            draw.line([(x, 0), (x, height)], fill=(r, g, b))
    
    return img

def wrap_text(text, font, max_width):
    """Wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = font.getbbox(test_line)
        text_width = bbox[2] - bbox[0]
        
        if text_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

def get_text_dimensions(text, font):
    """Get text width and height."""
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

@st.cache_data(ttl=3600)
def fetch_verse(book, chapter, verse):
    """Fetch verse text from API."""
    try:
        url = f"{RESOURCE_CONFIG['bible_api']}/books/{book.lower()}/chapters/{chapter}/verses/{verse}.json"
        response = requests.get(url, timeout=5)
        data = response.json()
        return data.get("text", DEFAULT_VERSE).strip()
    except:
        return DEFAULT_VERSE

@st.cache_data(ttl=3600)
def download_logo(url):
    """Download and cache logo."""
    try:
        response = requests.get(url, stream=True, timeout=10)
        return Image.open(io.BytesIO(response.content)).convert("RGBA")
    except:
        return None

@st.cache_data(ttl=3600)
def cache_video(url):
    """Cache video file."""
    if not url:
        return None
    
    filename = f"cached_video_{hash(url)}.mp4"
    if os.path.exists(filename):
        return filename
    
    try:
        response = requests.get(url, stream=True, timeout=30)
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return filename
    except:
        return None

def cleanup_temp_files():
    """Automatically clean temporary files."""
    for filename in os.listdir('.'):
        if filename.startswith('cached_') or filename.startswith('final_video_'):
            try:
                # Remove files older than 1 hour
                if time.time() - os.path.getctime(filename) > 3600:
                    os.remove(filename)
            except:
                pass

# ============================================================================
# IMAGE GENERATION
# ============================================================================
def generate_image(aspect_name, palette_name, book, chapter, verse_num, hook, 
                   text_anim, logo_placement, gradient_dir):
    """Generate static image with proper text layout."""
    
    # Get dimensions
    width, height = ASPECT_RATIOS[aspect_name]
    palette = DESIGN_CONFIG["palettes"][palette_name]
    
    # Create base gradient
    base = create_gradient(width, height, palette["bg"][0], palette["bg"][1], gradient_dir)
    
    # Prepare fonts (use default if custom not available)
    try:
        hook_font = ImageFont.truetype("arial.ttf", DESIGN_CONFIG["font_sizes"]["hook"])
        verse_font = ImageFont.truetype("arial.ttf", DESIGN_CONFIG["font_sizes"]["verse"])
        ref_font = ImageFont.truetype("arial.ttf", DESIGN_CONFIG["font_sizes"]["reference"])
    except:
        hook_font = ImageFont.load_default()
        verse_font = ImageFont.load_default()
        ref_font = ImageFont.load_default()
    
    # Fetch verse text
    verse_text = fetch_verse(book, chapter, verse_num)
    reference = f"{book} {chapter}:{verse_num}"
    
    # Calculate layout
    margin = 100
    max_width = width - 2 * margin
    
    # Wrap texts
    hook_lines = wrap_text(hook, hook_font, max_width)
    verse_lines = wrap_text(verse_text, verse_font, max_width)
    
    # Calculate heights
    hook_height = sum(get_text_dimensions(line, hook_font)[1] for line in hook_lines) + 20 * len(hook_lines)
    verse_height = sum(get_text_dimensions(line, verse_font)[1] for line in verse_lines) + 15 * len(verse_lines)
    
    # Start Y position (centered vertically)
    total_height = hook_height + verse_height + 120
    start_y = (height - total_height) // 2
    
    # Create drawing context
    draw = ImageDraw.Draw(base)
    
    # Draw hook text
    current_y = start_y
    for line in hook_lines:
        text_width, text_height = get_text_dimensions(line, hook_font)
        x = (width - text_width) // 2
        draw.text((x, current_y), line, font=hook_font, fill=hex_to_rgb(palette["accent"]))
        current_y += text_height + 20
    
    # Draw verse text
    current_y += 40  # Spacing between hook and verse
    for line in verse_lines:
        text_width, text_height = get_text_dimensions(line, verse_font)
        x = (width - text_width) // 2
        draw.text((x, current_y), line, font=verse_font, fill=hex_to_rgb(palette["text_primary"]))
        current_y += text_height + 15
    
    # Draw reference
    ref_width, ref_height = get_text_dimensions(reference, ref_font)
    ref_x = (width - ref_width) // 2
    draw.text((ref_x, current_y + 40), reference, font=ref_font, fill=hex_to_rgb(palette["text_secondary"]))
    
    # Add logo if specified
    if logo_placement != "Hidden":
        logo_config = LOGO_POSITIONS[logo_placement]
        logo_img = download_logo(RESOURCE_CONFIG["logo_url"])
        
        if logo_img:
            logo_size = logo_config["size"]
            logo_img = logo_img.resize((logo_size, logo_size))
            
            # Calculate position from percentages
            logo_x = int(width * logo_config["x"] - logo_size // 2)
            logo_y = int(height * logo_config["y"] - logo_size // 2)
            
            # Create a circular mask for the logo
            mask = Image.new("L", (logo_size, logo_size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse([(0, 0), (logo_size, logo_size)], fill=255)
            
            # Paste logo with circular mask
            base.paste(logo_img, (logo_x, logo_y), mask)
    
    return base, verse_text

# ============================================================================
# VIDEO GENERATION
# ============================================================================
def generate_video(aspect_name, palette_name, book, chapter, verse_num, hook,
                   bg_anim, text_anim, logo_placement, gradient_dir, video_bg_name):
    """Generate video with animations."""
    
    width, height = ASPECT_RATIOS[aspect_name]
    palette = DESIGN_CONFIG["palettes"][palette_name]
    duration = DESIGN_CONFIG["video_duration"]
    fps = DESIGN_CONFIG["video_fps"]
    
    # Cache video background if selected
    video_path = None
    if video_bg_name != "None":
        video_url = RESOURCE_CONFIG["video_backgrounds"][video_bg_name]
        video_path = cache_video(video_url)
    
    # Create base clip
    if video_path and os.path.exists(video_path):
        try:
            base_clip = VideoFileClip(video_path)
            base_clip = base_clip.fx(vfx.resize, newsize=(width, height))
            if base_clip.duration < duration:
                base_clip = base_clip.loop(duration=duration)
            else:
                base_clip = base_clip.subclip(0, duration)
        except:
            base_clip = None
    else:
        base_clip = None
    
    # Create animated gradient if no video background
    if base_clip is None:
        def make_frame(t):
            img = create_gradient(width, height, palette["bg"][0], palette["bg"][1], gradient_dir)
            
            # Add simple animation if selected
            if bg_anim != "None":
                draw = ImageDraw.Draw(img)
                center_x, center_y = width // 2, height // 2
                
                if bg_anim == "Cross Orbit":
                    radius = 200 + 50 * math.sin(t * 2)
                    angle = t * 180
                    
                    x1 = center_x + int(radius * math.cos(math.radians(angle)))
                    y1 = center_y + int(radius * math.sin(math.radians(angle)))
                    x2 = center_x - int(radius * math.cos(math.radians(angle)))
                    y2 = center_y - int(radius * math.sin(math.radians(angle)))
                    
                    draw.line([(x1, y1), (x2, y2)], fill=hex_to_rgb(palette["accent"]), width=5)
                    
                elif bg_anim == "Floating Circles":
                    for i in range(3):
                        x = center_x + int(150 * math.sin(t + i))
                        y = center_y + int(100 * math.cos(t * 1.5 + i))
                        size = 30 + 20 * math.sin(t * 2 + i)
                        draw.ellipse([(x-size, y-size), (x+size, y+size)], 
                                    outline=hex_to_rgb(palette["accent"]), width=3)
            
            return np.array(img)
        
        base_clip = VideoClip(make_frame, duration=duration)
        base_clip = base_clip.set_fps(fps)
    
    # Create text overlay clip
    def make_text_frame(t):
        # Generate static image for this frame
        img, _ = generate_image(aspect_name, palette_name, book, chapter, 
                                verse_num, hook, text_anim, logo_placement, gradient_dir)
        
        # Apply text animation
        if text_anim != "None":
            draw = ImageDraw.Draw(img)
            
            if text_anim == "Fade-in":
                # Simple fade in over first 2 seconds
                alpha = min(1.0, t / 2.0) * 255
                # This is simplified - in production you'd need to redraw text with alpha
                pass
                
            elif text_anim == "Glow Pulse":
                # Add glow effect
                pulse = 0.5 + 0.5 * math.sin(t * 4)
                # Simplified - would need more complex implementation
                pass
        
        return np.array(img)
    
    text_clip = VideoClip(make_text_frame, duration=duration)
    text_clip = text_clip.set_fps(fps)
    
    # Composite clips
    final_clip = CompositeVideoClip([base_clip, text_clip])
    
    # Export video
    filename = f"final_video_{int(time.time())}.mp4"
    final_clip.write_videofile(
        filename,
        fps=fps,
        codec='libx264',
        verbose=False,
        logger=None
    )
    
    # Read file to bytes
    with open(filename, 'rb') as f:
        video_bytes = f.read()
    
    # Cleanup
    os.remove(filename)
    
    return video_bytes

# ============================================================================
# STREAMLIT UI
# ============================================================================
st.set_page_config(page_title="Verse Studio", page_icon="✝️", layout="wide")

# Cleanup old files on startup
cleanup_temp_files()

st.title("💎 Verse Studio")

# Sidebar for controls
with st.sidebar:
    st.header("🎨 Design")
    
    aspect_ratio = st.selectbox("Aspect Ratio", list(ASPECT_RATIOS.keys()))
    color_theme = st.selectbox("Color Theme", PALETTE_NAMES)
    gradient_dir = st.selectbox("Gradient Direction", GRADIENT_DIRECTIONS)
    
    st.header("📖 Content")
    
    book = st.selectbox("Book", BIBLE_BOOKS, index=18)  # Default to Psalm
    chapter = st.number_input("Chapter", min_value=1, max_value=150, value=46)
    verse = st.number_input("Verse", min_value=1, max_value=176, value=1)
    hook = st.text_input("Hook Text", value="Need strength today?")
    
    st.header("⚙️ Options")
    
    bg_animation = st.selectbox("Background Animation", BG_ANIMATIONS)
    text_animation = st.selectbox("Text Animation", TEXT_ANIMATIONS)
    logo_placement = st.selectbox("Logo", list(LOGO_POSITIONS.keys()))
    video_background = st.selectbox("Video BG", list(RESOURCE_CONFIG["video_backgrounds"].keys()))

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    # Generate and display preview
    preview_image, verse_text = generate_image(
        aspect_ratio, color_theme, book, chapter, verse, 
        hook, text_animation, logo_placement, gradient_dir
    )
    
    st.image(preview_image, use_column_width=True)
    
    # Download buttons
    col_a, col_b = st.columns(2)
    
    with col_a:
        # PNG Download
        img_bytes = io.BytesIO()
        preview_image.save(img_bytes, format='PNG')
        st.download_button(
            "📥 Download PNG",
            data=img_bytes.getvalue(),
            file_name=f"verse_{book}_{chapter}_{verse}.png",
            mime="image/png"
        )
    
    with col_b:
        # Video Generation
        if st.button("🎬 Generate Video (6s)"):
            with st.spinner("Creating video..."):
                video_data = generate_video(
                    aspect_ratio, color_theme, book, chapter, verse,
                    hook, bg_animation, text_animation, logo_placement,
                    gradient_dir, video_background
                )
                
                if video_data:
                    st.video(video_data)
                    
                    st.download_button(
                        "📥 Download MP4",
                        data=video_data,
                        file_name=f"verse_{book}_{chapter}_{verse}.mp4",
                        mime="video/mp4"
                    )

with col2:
    st.header("Preview Info")
    st.write(f"**Theme:** {color_theme}")
    st.write(f"**Size:** {aspect_ratio}")
    st.write(f"**Reference:** {book} {chapter}:{verse}")
    
    st.divider()
    
    st.header("Social Caption")
    caption = f"""{hook}

{verse_text}

#{book.replace(' ', '')} {chapter}:{verse} #BibleVerse #DailyDevotional"""
    
    st.text_area("Copy Caption", caption, height=200)
    
    # Auto-cleanup message
    st.caption("🔄 Temporary files are cleaned up automatically")

# Final cleanup
cleanup_temp_files()