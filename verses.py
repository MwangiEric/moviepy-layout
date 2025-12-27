import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io, os, requests, math, time
from moviepy.editor import VideoClip, CompositeVideoClip, VideoFileClip, vfx
import numpy as np

# ============================================================================
# DESIGN CONFIGURATION (Non-coders can modify this section)
# ============================================================================
DESIGN_CONFIG = {
    # Color Themes using RGBA (Red, Green, Blue, Alpha)
    "palettes": {
        "Galilee Morning": {
            "bg": [(250, 249, 246, 255), (224, 228, 213, 255)],  # Light cream to sage
            "accent": (196, 137, 31, 255),  # Gold
            "text_primary": (24, 48, 40, 255),  # Dark green
            "text_secondary": (90, 90, 90, 255)  # Gray
        },
        "Still Mind Green": {
            "bg": [(10, 40, 50, 255), (20, 60, 70, 255)],  # Dark teal gradient
            "accent": (76, 175, 80, 255),  # Bright green
            "text_primary": (240, 240, 240, 255),  # White
            "text_secondary": (200, 200, 200, 255)  # Light gray
        },
        "Deep Blue": {
            "bg": [(10, 20, 40, 255), (20, 40, 80, 255)],  # Dark blue gradient
            "accent": (100, 200, 255, 255),  # Sky blue
            "text_primary": (240, 240, 240, 255),
            "text_secondary": (180, 200, 220, 255)
        },
        "Urban Night": {
            "bg": [(32, 32, 32, 255), (54, 54, 54, 255)],
            "accent": (247, 197, 159, 255),
            "text_primary": (241, 250, 251, 255),
            "text_secondary": (221, 221, 221, 255)
        }
    },
    
    # Layout Templates (x, y positions as percentages of width/height)
    "layouts": {
        "TikTok/Reel (9:16)": {
            "size": (1080, 1920),
            "hook": {"x": 0.5, "y": 0.25, "align": "center"},
            "verse": {"x": 0.5, "y": 0.5, "align": "center", "max_width": 0.8},
            "reference": {"x": 0.5, "y": 0.75, "align": "center"},
            "brand_text": {"x": 100, "y": 800, "font_size": 60, "align": "left"},
            "logo": {"x": 0.9, "y": 0.1, "size": 100}
        },
        "Instagram Square": {
            "size": (1080, 1080),
            "hook": {"x": 0.5, "y": 0.3, "align": "center"},
            "verse": {"x": 0.5, "y": 0.5, "align": "center", "max_width": 0.85},
            "reference": {"x": 0.5, "y": 0.7, "align": "center"},
            "brand_text": {"x": 50, "y": 1000, "font_size": 40, "align": "left"},
            "logo": {"x": 0.95, "y": 0.95, "size": 80}
        }
    },
    
    # Font Settings
    "fonts": {
        "hook": {"size": 70, "min_size": 40, "max_size": 90},
        "verse": {"size": 130, "min_size": 60, "max_size": 150},
        "reference": {"size": 40, "min_size": 20, "max_size": 50},
        "brand": {"size": 60, "min_size": 40, "max_size": 80}
    },
    
    # Video Settings (Fixed)
    "video": {
        "duration": 6,    # 6 seconds
        "fps": 12         # 12 FPS
    },
    
    # Gradient Directions
    "gradients": ["Vertical", "Horizontal", "Diagonal"],
    
    # Working Animations (only show implemented ones)
    "animations": {
        "background": ["None", "Cross Orbit", "Floating Circles"],
        "text": ["None", "Fade-in", "Glow Pulse"]  # Typewriter removed - not implemented
    },
    
    # Brand Configuration
    "brand": {
        "name": "Still Mind",
        "text_color": (76, 175, 80, 255)  # Green
    }
}

# External Resources
RESOURCE_CONFIG = {
    "logo_url": "https://ik.imagekit.io/ericmwangi/smlogo.png",
    "video_backgrounds": {
        "None": None,
        "Ocean Waves": "https://ik.imagekit.io/ericmwangi/oceanbg.mp4"
    },
    "bible_api": "https://bible-api.com"
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def create_gradient(width, height, color1, color2, direction="Vertical"):
    """Create gradient background with RGBA support."""
    img = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(img)
    
    if direction == "Vertical":
        for y in range(height):
            ratio = y / height
            r = int((1 - ratio) * color1[0] + ratio * color2[0])
            g = int((1 - ratio) * color1[1] + ratio * color2[1])
            b = int((1 - ratio) * color1[2] + ratio * color2[2])
            a = int((1 - ratio) * color1[3] + ratio * color2[3])
            draw.line([(0, y), (width, y)], fill=(r, g, b, a))
    
    elif direction == "Horizontal":
        for x in range(width):
            ratio = x / width
            r = int((1 - ratio) * color1[0] + ratio * color2[0])
            g = int((1 - ratio) * color1[1] + ratio * color2[1])
            b = int((1 - ratio) * color1[2] + ratio * color2[2])
            a = int((1 - ratio) * color1[3] + ratio * color2[3])
            draw.line([(x, 0), (x, height)], fill=(r, g, b, a))
    
    elif direction == "Diagonal":
        # Simple diagonal gradient from top-left to bottom-right
        for y in range(height):
            for x in range(width):
                # Distance from top-left (0,0) to bottom-right (width,height)
                dist = math.sqrt((x/width)**2 + (y/height)**2) / math.sqrt(2)
                r = int((1 - dist) * color1[0] + dist * color2[0])
                g = int((1 - dist) * color1[1] + dist * color2[1])
                b = int((1 - dist) * color1[2] + dist * color2[2])
                a = int((1 - dist) * color1[3] + dist * color2[3])
                draw.point((x, y), fill=(r, g, b, a))
    
    return img

def wrap_text(text, font, max_width):
    """Wrap text to fit within max_width."""
    words = text.split()
    if not words:
        return []
    
    lines = []
    current_line = words[0]
    
    for word in words[1:]:
        test_line = f"{current_line} {word}"
        bbox = font.getbbox(test_line)
        text_width = bbox[2] - bbox[0]
        
        if text_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word
    
    lines.append(current_line)
    return lines

def calculate_font_size(text, font_name, max_width, max_height, layout_name):
    """Auto-scale font size to fit within bounds."""
    config = DESIGN_CONFIG["fonts"][font_name]
    target_size = config["size"]
    min_size = config["min_size"]
    max_size = config["max_size"]
    
    # Try to load arial or use default
    try:
        test_font = ImageFont.truetype("arial.ttf", target_size)
    except:
        test_font = ImageFont.load_default()
    
    # Start with target size
    for size in range(target_size, min_size - 1, -5):
        try:
            test_font = ImageFont.truetype("arial.ttf", size)
        except:
            test_font = ImageFont.load_default()
        
        # Wrap text with this font size
        lines = wrap_text(text, test_font, max_width)
        
        # Calculate total height
        line_height = test_font.getbbox("A")[3] - test_font.getbbox("A")[1]
        total_height = len(lines) * (line_height * 1.2)  # 20% spacing
        
        if total_height <= max_height:
            return size, lines, test_font
    
    # If we get here, use minimum size
    try:
        final_font = ImageFont.truetype("arial.ttf", min_size)
    except:
        final_font = ImageFont.load_default()
    
    lines = wrap_text(text, final_font, max_width)
    return min_size, lines, final_font

def is_color_light(rgb_color):
    """Check if a color is light (for contrast safety)."""
    r, g, b, a = rgb_color
    # Calculate relative luminance
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return luminance > 0.6  # Adjust threshold as needed

def get_contrasting_text_color(background_color):
    """Return black or white text color based on background brightness."""
    if is_color_light(background_color):
        return (0, 0, 0, 255)  # Black for light backgrounds
    else:
        return (255, 255, 255, 255)  # White for dark backgrounds

@st.cache_data(ttl=3600)
def fetch_verse(book, chapter, verse):
    """Fetch verse text from API."""
    try:
        url = f"{RESOURCE_CONFIG['bible_api']}/{book}+{chapter}:{verse}"
        response = requests.get(url, timeout=5)
        data = response.json()
        return data.get("text", "God is our refuge and strength.").replace("\n", " ")
    except:
        return "God is our refuge and strength, an ever-present help in trouble."

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

# Cache for generated static images
_image_cache = {}

def get_cached_image(key):
    """Get cached image or generate new one."""
    if key in _image_cache:
        return _image_cache[key].copy()
    return None

def set_cached_image(key, image):
    """Cache generated image."""
    _image_cache[key] = image.copy()
    return image

# ============================================================================
# IMAGE GENERATION (With caching)
# ============================================================================
def generate_static_image(layout_name, palette_name, book, chapter, verse_num, hook, gradient_dir):
    """Generate and cache static image."""
    # Create cache key
    cache_key = f"{layout_name}_{palette_name}_{book}_{chapter}_{verse_num}_{hook}_{gradient_dir}"
    
    # Check cache first
    cached = get_cached_image(cache_key)
    if cached:
        return cached
    
    # Get layout and palette
    layout = DESIGN_CONFIG["layouts"][layout_name]
    palette = DESIGN_CONFIG["palettes"][palette_name]
    width, height = layout["size"]
    
    # Create gradient background
    base = create_gradient(width, height, palette["bg"][0], palette["bg"][1], gradient_dir)
    draw = ImageDraw.Draw(base)
    
    # Load fonts with fallback
    try:
        hook_font = ImageFont.truetype("arial.ttf", DESIGN_CONFIG["fonts"]["hook"]["size"])
        verse_font = ImageFont.truetype("arial.ttf", DESIGN_CONFIG["fonts"]["verse"]["size"])
        ref_font = ImageFont.truetype("arial.ttf", DESIGN_CONFIG["fonts"]["reference"]["size"])
        brand_font = ImageFont.truetype("arial.ttf", DESIGN_CONFIG["fonts"]["brand"]["size"])
    except:
        hook_font = ImageFont.load_default()
        verse_font = ImageFont.load_default()
        ref_font = ImageFont.load_default()
        brand_font = ImageFont.load_default()
    
    # Fetch verse
    verse_text = fetch_verse(book, chapter, verse_num)
    reference = f"{book} {chapter}:{verse_num}"
    
    # Calculate positions
    max_text_width = int(width * layout["verse"]["max_width"])
    
    # Auto-scale verse text
    verse_size, verse_lines, verse_font = calculate_font_size(
        verse_text, "verse", max_text_width, height * 0.3, layout_name
    )
    
    # Wrap hook text
    hook_lines = wrap_text(hook, hook_font, max_text_width)
    
    # Draw hook text
    if hook_lines:
        total_hook_height = 0
        for i, line in enumerate(hook_lines):
            bbox = hook_font.getbbox(line)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = layout["hook"]["x"]
            y = layout["hook"]["y"]
            
            if isinstance(x, float):
                x_pos = int(width * x) - (text_width // 2 if layout["hook"]["align"] == "center" else 0)
            else:
                x_pos = x
            
            if isinstance(y, float):
                y_pos = int(height * y) + (i * text_height * 1.2)
            else:
                y_pos = y + (i * text_height * 1.2)
            
            draw.text((x_pos, y_pos), line, font=hook_font, fill=palette["accent"])
            total_hook_height += text_height * 1.2
    
    # Draw verse text with auto-scaling
    current_y = int(height * 0.4)  # Start below hook
    for i, line in enumerate(verse_lines):
        bbox = verse_font.getbbox(line)
        text_width = bbox[2] - bbox[0]
        
        x = layout["verse"]["x"]
        if isinstance(x, float):
            x_pos = int(width * x) - (text_width // 2 if layout["verse"]["align"] == "center" else 0)
        else:
            x_pos = x
        
        # Use contrasting text color for readability
        text_color = get_contrasting_text_color(palette["bg"][0])
        draw.text((x_pos, current_y), line, font=verse_font, fill=text_color)
        
        text_height = bbox[3] - bbox[1]
        current_y += int(text_height * 1.2)
    
    # Draw reference
    ref_bbox = ref_font.getbbox(reference)
    ref_width = ref_bbox[2] - ref_bbox[0]
    
    x = layout["reference"]["x"]
    y = layout["reference"]["y"]
    
    if isinstance(x, float):
        x_pos = int(width * x) - (ref_width // 2 if layout["reference"]["align"] == "center" else 0)
    else:
        x_pos = x
    
    if isinstance(y, float):
        y_pos = int(height * y)
    else:
        y_pos = y
    
    draw.text((x_pos, y_pos), reference, font=ref_font, fill=palette["text_secondary"])
    
    # Draw brand name "Still Mind"
    brand_config = layout.get("brand_text")
    if brand_config:
        x_pos = brand_config["x"]
        y_pos = brand_config["y"]
        
        try:
            brand_size = brand_config.get("font_size", 60)
            brand_font = ImageFont.truetype("arial.ttf", brand_size)
        except:
            brand_font = ImageFont.load_default()
        
        brand_color = DESIGN_CONFIG["brand"]["text_color"]
        draw.text((x_pos, y_pos), DESIGN_CONFIG["brand"]["name"], font=brand_font, fill=brand_color)
    
    # Add logo if position is defined
    logo_config = layout.get("logo")
    if logo_config:
        logo_img = download_logo(RESOURCE_CONFIG["logo_url"])
        if logo_img:
            logo_size = logo_config["size"]
            logo_img = logo_img.resize((logo_size, logo_size))
            
            x = logo_config["x"]
            y = logo_config["y"]
            
            if isinstance(x, float):
                logo_x = int(width * x - logo_size // 2)
            else:
                logo_x = x
            
            if isinstance(y, float):
                logo_y = int(height * y - logo_size // 2)
            else:
                logo_y = y
            
            # Create circular mask for logo
            mask = Image.new("L", (logo_size, logo_size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse([(0, 0), (logo_size, logo_size)], fill=255)
            
            base.paste(logo_img, (logo_x, logo_y), mask)
    
    # Cache the result
    set_cached_image(cache_key, base)
    return base

# ============================================================================
# VIDEO GENERATION (Uses cached static image)
# ============================================================================
def generate_video(layout_name, palette_name, book, chapter, verse_num, hook,
                   bg_anim, gradient_dir, video_bg_name):
    """Generate video using cached static image for performance."""
    
    layout = DESIGN_CONFIG["layouts"][layout_name]
    palette = DESIGN_CONFIG["palettes"][palette_name]
    width, height = layout["size"]
    duration = DESIGN_CONFIG["video"]["duration"]
    fps = DESIGN_CONFIG["video"]["fps"]
    
    # Generate or get cached static image
    static_image = generate_static_image(layout_name, palette_name, book, 
                                        chapter, verse_num, hook, gradient_dir)
    
    # Convert static image for video (PIL to numpy)
    static_frame = np.array(static_image)
    
    # Create base clip (video background or gradient)
    video_path = None
    if video_bg_name != "None":
        video_url = RESOURCE_CONFIG["video_backgrounds"][video_bg_name]
        video_path = cache_video(video_url)
    
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
        def make_gradient_frame(t):
            img = create_gradient(width, height, palette["bg"][0], palette["bg"][1], gradient_dir)
            
            # Add background animation
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
                    
                    draw.line([(x1, y1), (x2, y2)], fill=palette["accent"], width=5)
                    
                elif bg_anim == "Floating Circles":
                    for i in range(3):
                        x = center_x + int(150 * math.sin(t + i))
                        y = center_y + int(100 * math.cos(t * 1.5 + i))
                        size = 30 + 20 * math.sin(t * 2 + i)
                        draw.ellipse([(x-size, y-size), (x+size, y+size)], 
                                    outline=palette["accent"], width=3)
            
            return np.array(img)
        
        base_clip = VideoClip(make_gradient_frame, duration=duration)
        base_clip = base_clip.set_fps(fps)
    
    # Create text overlay clip (uses cached static image)
    def make_text_frame(t):
        # For simple videos, just use the static image
        # If we had text animations, we'd modify it here
        return static_frame
    
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
        logger=None,
        preset='fast'  # Faster encoding
    )
    
    # Read file to bytes
    with open(filename, 'rb') as f:
        video_bytes = f.read()
    
    # Cleanup
    os.remove(filename)
    
    return video_bytes

# ============================================================================
# CAPTION GENERATOR
# ============================================================================
def generate_caption(hook, verse_text, reference, add_emoji=True, add_cta=True, hashtag_level=2):
    """Generate social media caption with options."""
    
    # Base caption
    caption_parts = []
    
    if hook:
        caption_parts.append(hook)
    
    if verse_text:
        # Truncate long verses
        if len(verse_text) > 200:
            verse_text = verse_text[:197] + "..."
        caption_parts.append(f'"{verse_text}"')
    
    caption_parts.append(f"📖 {reference}")
    
    # Add call to action
    if add_cta:
        cta_options = [
            "Share this with someone who needs hope today.",
            "Tag someone who needs to see this.",
            "Save this for when you need encouragement.",
            "Double tap if this spoke to you.",
        ]
        caption_parts.append(np.random.choice(cta_options))
    
    # Add emojis
    if add_emoji:
        emojis = ["✨", "🙏", "❤️", "🕊️", "⭐", "🔥", "💫"]
        caption = " ".join(caption_parts)
        # Add 1-3 random emojis at the end
        num_emojis = np.random.randint(1, 4)
        caption += " " + " ".join(np.random.choice(emojis, num_emojis))
    else:
        caption = "\n\n".join(caption_parts)
    
    # Add hashtags based on level
    hashtags = []
    
    if hashtag_level >= 1:
        hashtags.extend(["#BibleVerse", "#DailyVerse", "#Scripture"])
    
    if hashtag_level >= 2:
        hashtags.extend(["#Faith", "#Hope", "#Encouragement", "#GodIsGood"])
    
    if hashtag_level >= 3:
        hashtags.extend(["#Christian", "#Inspiration", "#WordOfGod", "#Jesus"])
    
    if hashtags:
        caption += "\n\n" + " ".join(hashtags)
    
    return caption

# ============================================================================
# STREAMLIT UI
# ============================================================================
st.set_page_config(page_title="Still Mind - Verse Studio", page_icon="✝️", layout="wide")

# Automatic cleanup of old files
for filename in os.listdir('.'):
    if filename.startswith('cached_') and time.time() - os.path.getctime(filename) > 3600:
        try:
            os.remove(filename)
        except:
            pass

st.title("🧠 Still Mind - Verse Studio")

# Sidebar for controls
with st.sidebar:
    st.header("🎨 Design")
    
    # Layout selection
    layout_names = list(DESIGN_CONFIG["layouts"].keys())
    layout = st.selectbox("Layout", layout_names)
    
    # Color theme
    palette_names = list(DESIGN_CONFIG["palettes"].keys())
    palette = st.selectbox("Color Theme", palette_names)
    
    # Gradient direction
    gradient = st.selectbox("Gradient Direction", DESIGN_CONFIG["gradients"])
    
    st.header("📖 Content")
    
    # Bible selection
    book = st.selectbox("Book", [
        "Genesis", "Exodus", "Psalm", "Proverbs", "Isaiah", 
        "Matthew", "Mark", "Luke", "John", "Romans", 
        "1 Corinthians", "Ephesians", "Philippians", "Colossians",
        "1 Thessalonians", "2 Timothy", "Hebrews", "James", "1 Peter", "Revelation"
    ])
    
    col1, col2 = st.columns(2)
    with col1:
        chapter = st.number_input("Chapter", min_value=1, max_value=150, value=46)
    with col2:
        verse = st.number_input("Verse", min_value=1, max_value=176, value=1)
    
    hook = st.text_input("Hook Text", value="Need strength today?")
    
    st.header("⚙️ Animation")
    
    # Only show implemented animations
    bg_animation = st.selectbox("Background Animation", DESIGN_CONFIG["animations"]["background"])
    video_background = st.selectbox("Video Background", list(RESOURCE_CONFIG["video_backgrounds"].keys()))

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    # Generate and display preview
    preview_image = generate_static_image(
        layout, palette, book, chapter, verse, 
        hook, gradient
    )
    
    st.image(preview_image, use_column_width=True, caption=f"{layout} | {palette}")
    
    # Download buttons
    col_a, col_b = st.columns(2)
    
    with col_a:
        # PNG Download
        img_bytes = io.BytesIO()
        preview_image.save(img_bytes, format='PNG')
        st.download_button(
            "📥 Download PNG",
            data=img_bytes.getvalue(),
            file_name=f"stillmind_{book}_{chapter}_{verse}.png",
            mime="image/png",
            use_container_width=True
        )
    
    with col_b:
        # Video Generation
        if st.button("🎬 Generate Video (6s)", use_container_width=True):
            with st.spinner("Creating video (using cached image for speed)..."):
                video_data = generate_video(
                    layout, palette, book, chapter, verse,
                    hook, bg_animation, gradient, video_background
                )
                
                if video_data:
                    st.video(video_data)
                    
                    st.download_button(
                        "📥 Download MP4",
                        data=video_data,
                        file_name=f"stillmind_{book}_{chapter}_{verse}.mp4",
                        mime="video/mp4",
                        use_container_width=True
                    )

with col2:
    st.header("📱 Social Tools")
    
    # Fetch verse for caption
    verse_text = fetch_verse(book, chapter, verse)
    reference = f"{book} {chapter}:{verse}"
    
    # Caption generator options
    st.subheader("Caption Generator")
    
    add_emoji = st.checkbox("Add Emojis", value=True)
    add_cta = st.checkbox("Add Call-to-Action", value=True)
    hashtag_level = st.slider("Hashtag Level", 1, 3, 2)
    
    # Generate caption
    caption = generate_caption(hook, verse_text, reference, add_emoji, add_cta, hashtag_level)
    
    st.text_area("Copy & Paste This Caption", caption, height=300)
    
    # Quick copy button
    if st.button("📋 Copy to Clipboard", use_container_width=True):
        st.code(caption)
        st.success("Caption copied to clipboard!")
    
    st.divider()
    
    # Layout info
    st.caption(f"**Layout:** {layout}")
    st.caption(f"**Theme:** {palette}")
    st.caption(f"**Verse:** {reference}")
    
    # Cache info
    cache_size = len(_image_cache)
    st.caption(f"🔄 {cache_size} images cached for fast video generation")

# Footer
st.divider()
st.caption("Still Mind Verse Studio | Designed for TikTok & Instagram | RGBA Color System")