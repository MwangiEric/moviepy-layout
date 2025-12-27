import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io, os, requests, math, time, hashlib
import numpy as np
from moviepy.editor import VideoClip, CompositeVideoClip, vfx

# ============================================================================
# STREAMLIT CONFIGURATION
# ============================================================================
st.set_page_config(page_title="Still Mind - Verse Studio", page_icon="✝️", layout="wide")

# ============================================================================
# DESIGN CONFIGURATION (Easy for non-coders to edit)
# ============================================================================
DESIGN_CONFIG = {
    # Color Palettes using RGBA
    "palettes": {
        "Still Mind Green": {
            "bg": [(20, 40, 60, 255), (30, 60, 90, 255)],  # Dark blue gradient
            "accent": (76, 175, 80, 255),  # Green accent
            "text_primary": (255, 255, 255, 255),
            "text_secondary": (200, 220, 200, 255)
        },
        "Galilee Morning": {
            "bg": [(250, 249, 246, 255), (224, 228, 213, 255)],
            "accent": (196, 137, 31, 255),
            "text_primary": (24, 48, 40, 255),
            "text_secondary": (90, 90, 90, 255)
        },
        "Deep Slate": {
            "bg": [(15, 30, 30, 255), (35, 65, 65, 255)],
            "accent": (252, 191, 73, 255),
            "text_primary": (240, 240, 240, 255),
            "text_secondary": (204, 204, 204, 255)
        }
    },
    
    # Layout Configurations
    "layouts": {
        "TikTok (9:16)": {
            "size": (1080, 1920),
            "text_area": {"x": 0.5, "y": 0.45, "width": 0.8},
            "brand": {"x": 100, "y": 800, "size": 60},
            "logo": {"x": 0.9, "y": 0.9, "size": 100}
        },
        "Instagram (1:1)": {
            "size": (1080, 1080),
            "text_area": {"x": 0.5, "y": 0.5, "width": 0.85},
            "brand": {"x": 50, "y": 1000, "size": 40},
            "logo": {"x": 0.95, "y": 0.95, "size": 80}
        }
    },
    
    # Font Sizes (auto-scaling will adjust these)
    "fonts": {
        "hook": {"target": 70, "min": 40, "max": 90},
        "verse": {"target": 130, "min": 60, "max": 150},
        "reference": {"target": 40, "min": 20, "max": 50}
    },
    
    # Video Settings
    "video": {"duration": 6, "fps": 12},
    
    # Simple options
    "gradients": ["Vertical", "Horizontal", "Diagonal"],
    "decorations": ["None", "Halo Glow", "Floating Dots"]
}

# Resource URLs
RESOURCES = {
    "logo": "https://ik.imagekit.io/ericmwangi/smlogo.png",
    "fonts": {
        "aubrey": "https://github.com/google/fonts/raw/main/ofl/aubrey/Aubrey-Regular.ttf",
        "playfair": "https://github.com/google/fonts/raw/main/ofl/playfairdisplay/PlayfairDisplay-Bold.ttf",
        "inter": "https://github.com/google/fonts/raw/main/ofl/inter/Inter-Regular.ttf"
    }
}

# ============================================================================
# FONT MANAGEMENT SYSTEM
# ============================================================================
@st.cache_resource
def download_font(url, font_name):
    """Download and cache font file."""
    cache_dir = "font_cache"
    os.makedirs(cache_dir, exist_ok=True)
    
    font_path = os.path.join(cache_dir, f"{font_name}.ttf")
    
    if not os.path.exists(font_path):
        try:
            response = requests.get(url, timeout=10)
            with open(font_path, "wb") as f:
                f.write(response.content)
        except Exception as e:
            st.warning(f"Could not download {font_name}: {e}")
            return None
    
    return font_path

def safe_load_font(font_path, size):
    """Safely load font with multiple fallbacks."""
    try:
        if font_path and os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)
        # Try common system fonts
        for system_font in ["Arial.ttf", "Helvetica.ttf", "DejaVuSans.ttf", "LiberationSans-Regular.ttf"]:
            try:
                return ImageFont.truetype(system_font, size)
            except:
                continue
    except Exception:
        pass
    
    # Final fallback to default
    return ImageFont.load_default(size)

# Download fonts once
AUBREY_PATH = download_font(RESOURCES["fonts"]["aubrey"], "aubrey")
PLAYFAIR_PATH = download_font(RESOURCES["fonts"]["playfair"], "playfair")
INTER_PATH = download_font(RESOURCES["fonts"]["inter"], "inter")

def get_font(font_type, size):
    """Get appropriate font based on type."""
    if font_type == "hook":
        return safe_load_font(AUBREY_PATH, size)
    elif font_type == "verse":
        return safe_load_font(PLAYFAIR_PATH, size)
    else:  # reference
        return safe_load_font(INTER_PATH, size)

# ============================================================================
# CORE UTILITY FUNCTIONS
# ============================================================================
def create_gradient(width, height, color1, color2, direction="Vertical"):
    """Create gradient background - SIMPLIFIED VERSION."""
    img = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(img)
    
    if direction == "Vertical":
        for y in range(height):
            ratio = y / height
            r = int((1-ratio) * color1[0] + ratio * color2[0])
            g = int((1-ratio) * color1[1] + ratio * color2[1])
            b = int((1-ratio) * color1[2] + ratio * color2[2])
            a = int((1-ratio) * color1[3] + ratio * color2[3])
            draw.line([(0, y), (width, y)], fill=(r, g, b, a))
    
    elif direction == "Horizontal":
        for x in range(width):
            ratio = x / width
            r = int((1-ratio) * color1[0] + ratio * color2[0])
            g = int((1-ratio) * color1[1] + ratio * color2[1])
            b = int((1-ratio) * color1[2] + ratio * color2[2])
            a = int((1-ratio) * color1[3] + ratio * color2[3])
            draw.line([(x, 0), (x, height)], fill=(r, g, b, a))
    
    else:  # Diagonal
        for y in range(height):
            for x in range(width):
                ratio = (x + y) / (width + height)
                r = int((1-ratio) * color1[0] + ratio * color2[0])
                g = int((1-ratio) * color1[1] + ratio * color2[1])
                b = int((1-ratio) * color1[2] + ratio * color2[2])
                a = int((1-ratio) * color1[3] + ratio * color2[3])
                draw.point((x, y), fill=(r, g, b, a))
    
    return img

def calculate_font_size(text, font_type, max_width, max_height):
    """Smart font scaling to prevent overflow."""
    config = DESIGN_CONFIG["fonts"][font_type]
    target_size = config["target"]
    min_size = config["min"]
    
    # Start with target size and work down
    for size in range(target_size, min_size - 2, -2):
        font = get_font(font_type, size)
        
        # Simple word wrap
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = font.getbbox(test_line)
            text_width = bbox[2] - bbox[0]
            
            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(" ".join(current_line))
        
        # Check if fits vertically
        line_height = font.getbbox("A")[3] - font.getbbox("A")[1]
        total_height = len(lines) * line_height * 1.2
        
        if total_height <= max_height:
            return size, lines, font
    
    # Use minimum size as fallback
    font = get_font(font_type, min_size)
    return min_size, [text], font

def draw_rounded_box(draw, xy, radius=30, fill=None):
    """Draw rounded rectangle - SIMPLIFIED."""
    x1, y1, x2, y2 = xy
    
    # Draw rounded corners
    draw.ellipse([x1, y1, x1 + radius*2, y1 + radius*2], fill=fill)
    draw.ellipse([x2 - radius*2, y1, x2, y1 + radius*2], fill=fill)
    draw.ellipse([x1, y2 - radius*2, x1 + radius*2, y2], fill=fill)
    draw.ellipse([x2 - radius*2, y2 - radius*2, x2, y2], fill=fill)
    
    # Fill center
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    return xy

def draw_decoration(draw, box_xy, style, phase, color):
    """Simple decorative elements."""
    x1, y1, x2, y2 = box_xy
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    
    if style == "Halo Glow":
        glow_alpha = int(40 * (0.5 + 0.5 * math.sin(phase * 4)))
        glow_color = color[:3] + (glow_alpha,)
        for r in [10, 20, 30]:
            draw.rectangle([x1-r, y1-r, x2+r, y2+r], outline=glow_color)
    
    elif style == "Floating Dots":
        for i in range(6):
            angle = phase * 2 * math.pi + (i * math.pi / 3)
            radius = 80 + 20 * math.sin(phase * 3 + i)
            x = int(cx + radius * math.cos(angle))
            y = int(cy + radius * math.sin(angle))
            size = 4 + int(2 * math.sin(phase * 2 + i))
            draw.ellipse([x-size, y-size, x+size, y+size], fill=color)

def fetch_verse(book, chapter, verse):
    """Get verse text - SIMPLIFIED."""
    try:
        url = f"https://bible-api.com/{book}+{chapter}:{verse}"
        response = requests.get(url, timeout=5)
        data = response.json()
        text = data.get("verses", [{}])[0].get("text", "")
        return text.strip().replace("\n", " ")
    except:
        return "God is our refuge and strength, an ever-present help in trouble."

# ============================================================================
# IMAGE GENERATION WITH CACHING
# ============================================================================
class ImageCache:
    """Simple cache for generated images."""
    def __init__(self, max_size=10):
        self.cache = {}
        self.max_size = max_size
    
    def get_key(self, *args):
        """Create cache key from arguments."""
        key_str = str(args)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key):
        """Get cached image."""
        if key in self.cache:
            # Update access time
            self.cache[key]["access_time"] = time.time()
            return self.cache[key]["image"].copy()
        return None
    
    def set(self, key, image):
        """Cache image."""
        if len(self.cache) >= self.max_size:
            # Remove oldest
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k]["access_time"])
            del self.cache[oldest_key]
        
        self.cache[key] = {
            "image": image.copy(),
            "access_time": time.time()
        }
        return image

# Global cache instance
image_cache = ImageCache()

def generate_static_image(layout_name, palette_name, book, chapter, verse_num, 
                         hook, decoration_style, gradient_dir):
    """Generate image with smart text layout and caching."""
    
    # Create cache key
    cache_key = image_cache.get_key(
        layout_name, palette_name, book, chapter, verse_num,
        hook, decoration_style, gradient_dir
    )
    
    # Check cache first
    cached = image_cache.get(cache_key)
    if cached:
        return cached
    
    # Get configuration
    layout = DESIGN_CONFIG["layouts"][layout_name]
    palette = DESIGN_CONFIG["palettes"][palette_name]
    width, height = layout["size"]
    
    # 1. Create background
    background = create_gradient(width, height, 
                                palette["bg"][0], palette["bg"][1], 
                                gradient_dir)
    draw = ImageDraw.Draw(background)
    
    # 2. Get text content
    verse_text = fetch_verse(book, chapter, verse_num)
    reference = f"{book} {chapter}:{verse_num}"
    
    # 3. Calculate text area
    text_config = layout["text_area"]
    text_area_width = int(width * text_config["width"])
    text_x = int(width * text_config["x"] - text_area_width // 2)
    text_y = int(height * text_config["y"])
    
    # 4. Auto-scale verse text
    max_text_width = text_area_width - 40  # 20px padding each side
    max_text_height = height * 0.6
    
    verse_size, verse_lines, verse_font = calculate_font_size(
        verse_text, "verse", max_text_width, max_text_height
    )
    
    # 5. Calculate content dimensions
    hook_font = get_font("hook", DESIGN_CONFIG["fonts"]["hook"]["target"])
    ref_font = get_font("reference", DESIGN_CONFIG["fonts"]["reference"]["target"])
    
    # Get line heights
    hook_line_height = hook_font.getbbox("A")[3] - hook_font.getbbox("A")[1]
    verse_line_height = verse_font.getbbox("A")[3] - verse_font.getbbox("A")[1]
    ref_line_height = ref_font.getbbox("A")[3] - ref_font.getbbox("A")[1]
    
    # Calculate total height
    total_height = 0
    if hook:
        total_height += hook_line_height + 20
    total_height += len(verse_lines) * verse_line_height * 1.2
    total_height += ref_line_height + 40
    
    # 6. Draw semi-transparent background box
    box_padding = 40
    box_height = total_height + (box_padding * 2)
    box_y = text_y - box_height // 2
    
    box_color = (0, 0, 0, 180)  # Semi-transparent black
    box_xy = draw_rounded_box(draw, 
        (text_x, box_y, text_x + text_area_width, box_y + box_height),
        radius=30, fill=box_color
    )
    
    # 7. Draw text
    current_y = box_y + box_padding
    
    # Hook
    if hook:
        hook_width = hook_font.getbbox(hook)[2]
        hook_x = text_x + (text_area_width - hook_width) // 2
        draw.text((hook_x, current_y), hook, font=hook_font, fill=palette["accent"])
        current_y += hook_line_height + 20
    
    # Verse
    for line in verse_lines:
        line_width = verse_font.getbbox(line)[2]
        line_x = text_x + (text_area_width - line_width) // 2
        draw.text((line_x, current_y), line, font=verse_font, fill=palette["text_primary"])
        current_y += verse_line_height * 1.2
    
    # Reference
    ref_width = ref_font.getbbox(reference)[2]
    ref_x = text_x + (text_area_width - ref_width) // 2
    draw.text((ref_x, current_y + 20), reference, font=ref_font, fill=palette["text_secondary"])
    
    # 8. Add decorations
    draw_decoration(draw, box_xy, decoration_style, 0, palette["accent"])
    
    # 9. Add "Still Mind" brand
    brand_config = layout.get("brand")
    if brand_config:
        brand_font = get_font("hook", brand_config["size"])
        draw.text((brand_config["x"], brand_config["y"]), 
                 "Still Mind", font=brand_font, fill=palette["accent"])
    
    # 10. Add logo
    logo_config = layout.get("logo")
    if logo_config and logo_config.get("size", 0) > 0:
        try:
            response = requests.get(RESOURCES["logo"], timeout=10)
            logo_img = Image.open(io.BytesIO(response.content)).convert("RGBA")
            logo_size = logo_config["size"]
            logo_img = logo_img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # Sharpen
            logo_img = logo_img.filter(ImageFilter.SHARPEN)
            
            # Position
            logo_x = int(width * logo_config["x"] - logo_size // 2)
            logo_y = int(height * logo_config["y"] - logo_size // 2)
            
            # Circular mask
            mask = Image.new("L", (logo_size, logo_size), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse([(0, 0), (logo_size, logo_size)], fill=255)
            
            background.paste(logo_img, (logo_x, logo_y), mask)
        except:
            pass  # Skip logo if can't load
    
    # Cache and return
    image_cache.set(cache_key, background)
    return background

# ============================================================================
# VIDEO GENERATION (SIMPLIFIED AND FIXED)
# ============================================================================
def generate_video_frame(t, background_rgb, static_image_rgba, palette, decoration_style, box_xy):
    """Generate a single video frame - FIXED for RGB output."""
    
    # Create a copy of the background
    frame = background_rgb.copy()
    
    # Convert static image to RGBA array
    static_rgba = np.array(static_image_rgba)
    
    # Extract alpha channel and normalize
    alpha = static_rgba[..., 3] / 255.0
    
    # For each pixel, blend based on alpha
    for y in range(frame.shape[0]):
        for x in range(frame.shape[1]):
            if alpha[y, x] > 0:
                # Blend: background * (1-alpha) + foreground * alpha
                frame[y, x] = (
                    frame[y, x] * (1 - alpha[y, x]) + 
                    static_rgba[y, x, :3] * alpha[y, x]
                ).astype(np.uint8)
    
    # Convert back to PIL for drawing decorations
    frame_pil = Image.fromarray(frame)
    draw = ImageDraw.Draw(frame_pil)
    
    # Add animated decorations if any
    if decoration_style != "None":
        phase = t / DESIGN_CONFIG["video"]["duration"]
        draw_decoration(draw, box_xy, decoration_style, phase, palette["accent"])
    
    return np.array(frame_pil)

def generate_video(layout_name, palette_name, book, chapter, verse_num, 
                   hook, decoration_style, gradient_dir):
    """Generate 6-second video at 12 FPS."""
    
    # Get configuration
    layout = DESIGN_CONFIG["layouts"][layout_name]
    palette = DESIGN_CONFIG["palettes"][palette_name]
    width, height = layout["size"]
    duration = DESIGN_CONFIG["video"]["duration"]
    fps = DESIGN_CONFIG["video"]["fps"]
    
    # Generate static image (cached)
    static_image = generate_static_image(
        layout_name, palette_name, book, chapter, verse_num,
        hook, decoration_style, gradient_dir
    )
    
    # Calculate box position for decorations
    text_config = layout["text_area"]
    text_area_width = int(width * text_config["width"])
    text_x = int(width * text_config["x"] - text_area_width // 2)
    text_y = int(height * text_config["y"])
    
    # Estimate box height
    verse_text = fetch_verse(book, chapter, verse_num)
    verse_size, verse_lines, _ = calculate_font_size(
        verse_text, "verse", text_area_width - 40, height * 0.6
    )
    
    # Simple box estimate
    box_height = len(verse_lines) * 100 + 200
    box_xy = (text_x, text_y - box_height//2, 
              text_x + text_area_width, text_y + box_height//2)
    
    # Create animated background
    def make_background_frame(t):
        """Create animated gradient background."""
        bg_img = create_gradient(width, height, 
                                palette["bg"][0], palette["bg"][1], 
                                gradient_dir)
        
        # Add subtle animation to gradient
        if gradient_dir != "None":
            draw = ImageDraw.Draw(bg_img)
            phase = t * 2
            
            # Add subtle moving elements
            for i in range(3):
                x = int(width * 0.5 + 200 * math.sin(phase + i))
                y = int(height * 0.5 + 150 * math.cos(phase * 1.5 + i))
                radius = 50 + 20 * math.sin(phase * 3 + i)
                color = palette["accent"][:3] + (30,)  # Very transparent
                draw.ellipse([x-radius, y-radius, x+radius, y+radius], 
                            outline=color, width=2)
        
        return np.array(bg_img.convert("RGB"))
    
    # Create background clip
    background_clip = VideoClip(make_background_frame, duration=duration)
    background_clip = background_clip.set_fps(fps)
    
    # Create final video
    def make_final_frame(t):
        """Create final frame with overlay."""
        # Get background at time t
        bg_rgb = make_background_frame(t)
        
        # Generate frame with overlay
        frame = generate_video_frame(t, bg_rgb, static_image, palette, 
                                    decoration_style, box_xy)
        
        return frame
    
    # Create and render video
    final_clip = VideoClip(make_final_frame, duration=duration)
    final_clip = final_clip.set_fps(fps)
    
    # Export
    temp_file = f"video_{int(time.time())}.mp4"
    
    try:
        final_clip.write_videofile(
            temp_file,
            fps=fps,
            codec="libx264",
            preset="fast",
            verbose=False,
            logger=None,
            ffmpeg_params=["-pix_fmt", "yuv420p"]  # Ensure compatibility
        )
        
        with open(temp_file, "rb") as f:
            video_bytes = f.read()
        
        os.remove(temp_file)
        return video_bytes
        
    except Exception as e:
        st.error(f"Video error: {str(e)}")
        return None

# ============================================================================
# STREAMLIT UI
# ============================================================================
st.title("🧠 Still Mind - Verse Studio")

# Sidebar
with st.sidebar:
    st.header("🎨 Design")
    
    layout = st.selectbox("Layout", list(DESIGN_CONFIG["layouts"].keys()))
    palette = st.selectbox("Color Theme", list(DESIGN_CONFIG["palettes"].keys()))
    gradient = st.selectbox("Gradient", DESIGN_CONFIG["gradients"])
    decoration = st.selectbox("Decoration", DESIGN_CONFIG["decorations"])
    
    st.header("📖 Content")
    
    book = st.selectbox("Book", ["Psalm", "Matthew", "John", "Romans", 
                                "Ephesians", "Philippians", "James"])
    col1, col2 = st.columns(2)
    with col1:
        chapter = st.number_input("Chapter", 1, 150, 46)
    with col2:
        verse = st.number_input("Verse", 1, 176, 1)
    
    hook = st.text_input("Hook", "Find strength in stillness")

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    # Generate preview
    with st.spinner("Generating preview..."):
        preview = generate_static_image(
            layout, palette, book, chapter, verse, 
            hook, decoration, gradient
        )
    
    st.image(preview, use_column_width=True)
    
    # Download buttons
    col_a, col_b = st.columns(2)
    
    with col_a:
        img_bytes = io.BytesIO()
        preview.save(img_bytes, format="PNG")
        st.download_button(
            "📥 Download PNG",
            data=img_bytes.getvalue(),
            file_name=f"stillmind_{book}_{chapter}_{verse}.png",
            mime="image/png",
            use_container_width=True
        )
    
    with col_b:
        if st.button("🎬 Generate Video (6s)", use_container_width=True, type="primary"):
            with st.spinner("Rendering video..."):
                video_data = generate_video(
                    layout, palette, book, chapter, verse,
                    hook, decoration, gradient
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
    
    # Generate caption
    verse_text = fetch_verse(book, chapter, verse)
    reference = f"{book} {chapter}:{verse}"
    
    # Simple caption
    caption = f"""💭 {hook}

"{verse_text[:150]}{'...' if len(verse_text) > 150 else ''}"

📖 {reference}

#StillMind #BibleVerse #DailyDevotional"""
    
    st.text_area("📋 Social Media Caption", caption, height=200)
    
    # Quick copy
    if st.button("📋 Copy Caption", use_container_width=True):
        st.code(caption)
        st.success("Ready to paste!")
    
    st.divider()
    
    # Info
    st.caption(f"**Layout:** {layout}")
    st.caption(f"**Theme:** {palette}")
    st.caption(f"**Verse:** {reference}")
    st.caption(f"**Cache:** {len(image_cache.cache)} images")

# Cleanup old files
for f in os.listdir("."):
    if f.startswith("video_") and f.endswith(".mp4"):
        try:
            if time.time() - os.path.getctime(f) > 300:  # 5 minutes old
                os.remove(f)
        except:
            pass

# Footer
st.divider()
st.caption("Still Mind Verse Studio | Simple & Powerful | Aubrey Font | RGBA Colors")