import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io, os, requests, math, time
import numpy as np
from moviepy.editor import VideoClip, CompositeVideoClip, vfx

# ============================================================================
# STREAMLIT SETUP
# ============================================================================
st.set_page_config(page_title="Still Mind", page_icon="✝️", layout="wide")

# ============================================================================
# THEME CONFIGURATION - GREEN & DARK BLUE
# ============================================================================
COLORS = {
    "Still Mind": {
        "bg": [(10, 30, 50, 255), (20, 50, 80, 255)],  # Dark blue gradient
        "accent": (76, 175, 80, 255),  # Bright green
        "text": (255, 255, 255, 255),  # White text
        "secondary": (180, 220, 180, 255)  # Light green
    },
    "Ocean Deep": {
        "bg": [(10, 40, 70, 255), (20, 60, 100, 255)],
        "accent": (0, 200, 200, 255),  # Cyan
        "text": (255, 255, 255, 255),
        "secondary": (180, 240, 240, 255)
    },
    "Forest Night": {
        "bg": [(10, 30, 20, 255), (20, 50, 30, 255)],
        "accent": (100, 200, 100, 255),  # Forest green
        "text": (240, 240, 240, 255),
        "secondary": (200, 220, 200, 255)
    }
}

SIZES = {
    "TikTok": (1080, 1920),
    "Square": (1080, 1080)
}

BACKGROUNDS = ["Gradient", "Abstract", "Particles", "Geometric"]

BIBLE_BOOKS = ["Psalm", "Matthew", "John", "Romans", "Ephesians", "Philippians", "James"]

# ============================================================================
# IMPROVED FONT LOADING
# ============================================================================
def load_font_safe(size, bold=False, italic=False):
    """Try multiple font files before falling back to default."""
    font_paths = []
    
    if bold and italic:
        font_paths.extend([
            "arialbi.ttf", "Arial-BoldItalic.ttf", "Helvetica-BoldOblique.ttf",
            "DejaVuSans-BoldOblique.ttf", "LiberationSans-BoldItalic.ttf"
        ])
    elif bold:
        font_paths.extend([
            "arialbd.ttf", "Arial-Bold.ttf", "Helvetica-Bold.ttf",
            "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf"
        ])
    elif italic:
        font_paths.extend([
            "ariali.ttf", "Arial-Italic.ttf", "Helvetica-Oblique.ttf",
            "DejaVuSans-Oblique.ttf", "LiberationSans-Italic.ttf"
        ])
    else:
        font_paths.extend([
            "arial.ttf", "Arial.ttf", "Helvetica.ttf",
            "DejaVuSans.ttf", "LiberationSans-Regular.ttf"
        ])
    
    # Also try common font directories
    font_dirs = [
        "/usr/share/fonts/truetype/",
        "/usr/local/share/fonts/",
        "C:/Windows/Fonts/",
        "/Library/Fonts/"
    ]
    
    for font_dir in font_dirs:
        if os.path.exists(font_dir):
            for font_file in os.listdir(font_dir):
                if font_file.lower().endswith('.ttf'):
                    # Check if it's a generic sans-serif font
                    lower_name = font_file.lower()
                    if any(x in lower_name for x in ['arial', 'helvetica', 'dejavu', 'liberation']):
                        font_paths.append(os.path.join(font_dir, font_file))
    
    for font_path in font_paths:
        try:
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, size)
        except:
            continue
    
    # Only use default as absolute last resort
    return ImageFont.load_default(size)

# ============================================================================
# SMART FONT SIZING (LARGER DEFAULTS)
# ============================================================================
def calculate_font_size(text, target_size, min_size, max_width, max_height):
    """Dynamically adjust font size based on text length - with larger defaults."""
    # Start with target size
    for size in range(target_size, min_size - 1, -3):
        font = load_font_safe(size)
        
        # Simple word wrap calculation
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
        
        # Calculate total height
        line_height = font.getbbox("A")[3] - font.getbbox("A")[1]
        total_height = len(lines) * line_height * 1.3  # Increased spacing
        
        if total_height <= max_height:
            return size, lines, font
    
    # If we get here, use minimum size
    return min_size, [text], load_font_safe(min_size)

# ============================================================================
# BACKGROUND GENERATORS
# ============================================================================
def create_background(width, height, style, colors, time_offset=0):
    """Create different background styles."""
    img = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(img)
    
    color1, color2 = colors["bg"]
    
    if style == "Gradient":
        # Enhanced gradient with more colors
        for y in range(height):
            ratio = y / height
            # Add some variation for visual interest
            variation = math.sin(y / 100 + time_offset) * 0.1
            ratio = max(0, min(1, ratio + variation))
            
            r = int((1-ratio) * color1[0] + ratio * color2[0])
            g = int((1-ratio) * color1[1] + ratio * color2[1])
            b = int((1-ratio) * color1[2] + ratio * color2[2])
            a = int((1-ratio) * color1[3] + ratio * color2[3])
            draw.line([(0, y), (width, y)], fill=(r, g, b, a))
    
    elif style == "Abstract":
        # Green-themed abstract shapes
        for i in range(8):
            offset = int(time_offset * 80) % 1000
            size = 120 + int(60 * math.sin(time_offset + i))
            x = int(width * (0.15 * i) + offset % 400)
            y = int(height * 0.5 + 150 * math.cos(time_offset * 1.5 + i))
            
            # Draw abstract green shape
            opacity = int(100 + 100 * math.sin(time_offset + i))
            shape_color = colors["accent"][:3] + (opacity,)
            
            draw.ellipse([x, y, x+size, y+size], 
                        outline=shape_color, 
                        width=4)
    
    elif style == "Particles":
        # Green particle effect
        for i in range(80):
            x = int(width * (0.5 + 0.45 * math.sin(time_offset + i * 0.15)))
            y = int(height * (0.5 + 0.45 * math.cos(time_offset + i * 0.2)))
            size = 3 + int(4 * math.sin(time_offset + i * 0.3))
            
            # Green particles with varying opacity
            opacity = int(180 + 70 * math.sin(time_offset * 2 + i))
            particle_color = colors["accent"][:3] + (opacity,)
            
            draw.ellipse([x-size, y-size, x+size, y+size], 
                        fill=particle_color)
    
    elif style == "Geometric":
        # Geometric green patterns
        for i in range(12):
            x = int(width * (0.1 + 0.07 * i) + time_offset * 15 % 300)
            y = int(height * 0.4 + 80 * math.sin(time_offset * 2 + i))
            
            # Draw geometric shape
            points = []
            sides = 6 + i % 3
            for j in range(sides):
                angle = 2 * math.pi * j / sides + time_offset
                px = x + 60 * math.cos(angle)
                py = y + 60 * math.sin(angle)
                points.append((px, py))
            
            if len(points) > 2:
                opacity = int(150 + 100 * math.sin(time_offset + i))
                outline_color = colors["accent"][:3] + (opacity,)
                draw.polygon(points, outline=outline_color, width=3)
    
    return img

# ============================================================================
# TEXT ANIMATION FUNCTIONS
# ============================================================================
def draw_typewriter_text(draw, text_lines, font, x, y, line_height, progress, colors):
    """Draw text with typewriter animation."""
    full_text = " ".join(text_lines)
    total_chars = len(full_text)
    visible_chars = int(total_chars * progress)
    
    visible_text = full_text[:visible_chars]
    words = visible_text.split()
    visible_lines = []
    current_line = ""
    
    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = font.getbbox(test_line)
        if bbox[2] - bbox[0] <= 900:
            current_line = test_line
        else:
            if current_line:
                visible_lines.append(current_line)
            current_line = word
    
    if current_line:
        visible_lines.append(current_line)
    
    current_y = y
    for line in visible_lines:
        bbox = font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        draw.text(((1080 - line_width) // 2, current_y), 
                 line, font=font, fill=colors["text"])
        current_y += line_height
    
    # Draw blinking cursor
    if progress < 1.0:
        if visible_lines:
            last_line = visible_lines[-1]
            bbox = font.getbbox(last_line)
            cursor_x = (1080 - bbox[2]) // 2 + bbox[2] + 8
            cursor_y = current_y - line_height + 15
            # Blinking effect
            if int(time.time() * 2) % 2 == 0:
                draw.line([(cursor_x, cursor_y), (cursor_x, cursor_y + line_height - 25)], 
                         fill=colors["accent"], width=4)
    
    return current_y

def draw_fade_text(draw, text_lines, font, x, y, line_height, progress, colors):
    """Draw text with fade-in animation."""
    # Smooth fade with easing
    ease_progress = 1 - (1 - progress) ** 2
    opacity = int(255 * ease_progress)
    text_color = colors["text"][:3] + (opacity,)
    
    current_y = y
    for line in text_lines:
        bbox = font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        draw.text(((1080 - line_width) // 2, current_y), 
                 line, font=font, fill=text_color)
        current_y += line_height
    
    return current_y

# ============================================================================
# IMAGE GENERATION WITH LARGER FONTS
# ============================================================================
def create_image(size_name, color_name, book, chapter, verse, hook, animation_type, bg_style):
    """Create the verse image with larger fonts."""
    width, height = SIZES[size_name]
    colors = COLORS[color_name]
    
    # Background
    image = create_background(width, height, bg_style, colors)
    draw = ImageDraw.Draw(image)
    
    # Text content
    verse_text = get_verse(book, chapter, verse)
    reference = f"{book} {chapter}:{verse}"
    
    # Calculate text box dimensions
    text_box_width = 900
    text_box_x = (width - text_box_width) // 2
    
    # LARGER font sizing for verse
    verse_size, verse_lines, verse_font = calculate_font_size(
        verse_text, 
        target_size=150,  # Increased from 130
        min_size=80,      # Increased from 60
        max_width=text_box_width - 60,
        max_height=height * 0.6
    )
    
    # Load other fonts (larger sizes)
    hook_font = load_font_safe(85, bold=True)  # Increased from 70
    ref_font = load_font_safe(48, bold=True)   # Increased from 40
    
    # Calculate verse box height
    verse_line_height = verse_font.getbbox("A")[3] - verse_font.getbbox("A")[1]
    verse_height = len(verse_lines) * verse_line_height * 1.4  # More spacing
    
    # Calculate total box dimensions
    box_padding = 70  # Increased padding
    box_height = verse_height + (box_padding * 2)
    box_y = (height - box_height) // 2
    
    # Draw semi-transparent background box
    box_color = (0, 0, 0, 160)  # Less opaque for better readability
    draw.rectangle([text_box_x, box_y, text_box_x + text_box_width, box_y + box_height], 
                  fill=box_color)
    
    # Draw hook ABOVE the box
    if hook:
        bbox = hook_font.getbbox(hook)
        hook_width = bbox[2] - bbox[0]
        hook_x = (width - hook_width) // 2
        hook_y = box_y - 100  # Further above
        
        # Add a subtle green background for hook
        hook_bg_color = colors["accent"][:3] + (220,)
        draw.rectangle([hook_x - 25, hook_y - 15, hook_x + hook_width + 25, hook_y + bbox[3] + 15], 
                      fill=hook_bg_color)
        
        draw.text((hook_x, hook_y), hook, font=hook_font, fill=colors["text"])
    
    # Draw verse inside box
    verse_y = box_y + box_padding
    
    if animation_type == "Typewriter":
        verse_y = draw_typewriter_text(draw, verse_lines, verse_font, 
                                      text_box_x, verse_y, verse_line_height * 1.4, 
                                      1.0, colors)
    elif animation_type == "Fade":
        verse_y = draw_fade_text(draw, verse_lines, verse_font, 
                                text_box_x, verse_y, verse_line_height * 1.4, 
                                1.0, colors)
    else:
        # Normal text
        current_y = verse_y
        for line in verse_lines:
            bbox = verse_font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            draw.text(((width - line_width) // 2, current_y), 
                     line, font=verse_font, fill=colors["text"])
            current_y += verse_line_height * 1.4
        verse_y = current_y
    
    # Draw reference BELOW the box (bottom right corner)
    bbox = ref_font.getbbox(reference)
    ref_width = bbox[2] - bbox[0]
    ref_x = text_box_x + text_box_width - ref_width - 30  # Right aligned with margin
    ref_y = box_y + box_height + 50  # Position below the box
    
    # Add green background for reference
    ref_bg_color = colors["accent"][:3] + (220,)
    draw.rectangle([ref_x - 15, ref_y - 10, ref_x + ref_width + 15, ref_y + bbox[3] + 10], 
                  fill=ref_bg_color)
    
    draw.text((ref_x, ref_y), reference, font=ref_font, fill=colors["text"])
    
    # Add "Still Mind" brand (top left, larger)
    brand_font = load_font_safe(70, bold=True)  # Increased from 60
    draw.text((60, 60), "Still Mind", font=brand_font, fill=colors["accent"])
    
    return image, verse_text

# ============================================================================
# VIDEO GENERATION
# ============================================================================
def create_video(size_name, color_name, book, chapter, verse, hook, animation_type, bg_style):
    """Create animated video with larger fonts."""
    width, height = SIZES[size_name]
    colors = COLORS[color_name]
    duration = 6
    fps = 12
    
    # Get verse text
    verse_text = get_verse(book, chapter, verse)
    reference = f"{book} {chapter}:{verse}"
    
    # Calculate smart font size for video
    text_box_width = 900
    verse_size, verse_lines, verse_font = calculate_font_size(
        verse_text, 
        target_size=150, 
        min_size=80,
        max_width=text_box_width - 60,
        max_height=height * 0.6
    )
    
    # Video frame generator
    def make_frame(t):
        # Create animated background
        img = create_background(width, height, bg_style, colors, t)
        draw = ImageDraw.Draw(img)
        
        # Calculate text box
        text_box_x = (width - text_box_width) // 2
        verse_line_height = verse_font.getbbox("A")[3] - verse_font.getbbox("A")[1]
        verse_height = len(verse_lines) * verse_line_height * 1.4
        
        box_padding = 70
        box_height = verse_height + (box_padding * 2)
        box_y = (height - box_height) // 2
        
        # Draw semi-transparent box
        box_color = (0, 0, 0, 160)
        draw.rectangle([text_box_x, box_y, text_box_x + text_box_width, box_y + box_height], 
                      fill=box_color)
        
        # Draw hook above box
        if hook:
            hook_font = load_font_safe(85, bold=True)
            bbox = hook_font.getbbox(hook)
            hook_width = bbox[2] - bbox[0]
            hook_x = (width - hook_width) // 2
            hook_y = box_y - 100
            
            # Animate hook background color
            hook_brightness = 0.8 + 0.2 * math.sin(t * 3)
            hook_bg_r = int(colors["accent"][0] * hook_brightness)
            hook_bg_g = int(colors["accent"][1] * hook_brightness)
            hook_bg_b = int(colors["accent"][2] * hook_brightness)
            hook_bg_color = (hook_bg_r, hook_bg_g, hook_bg_b, 220)
            
            draw.rectangle([hook_x - 25, hook_y - 15, hook_x + hook_width + 25, hook_y + bbox[3] + 15], 
                          fill=hook_bg_color)
            draw.text((hook_x, hook_y), hook, font=hook_font, fill=colors["text"])
        
        # Draw verse with animation
        verse_y = box_y + box_padding
        
        if animation_type == "Typewriter":
            progress = min(1.0, t / (duration * 0.8))
            verse_y = draw_typewriter_text(draw, verse_lines, verse_font, 
                                          text_box_x, verse_y, verse_line_height * 1.4, 
                                          progress, colors)
        
        elif animation_type == "Fade":
            progress = min(1.0, t / (duration * 0.5))
            verse_y = draw_fade_text(draw, verse_lines, verse_font, 
                                    text_box_x, verse_y, verse_line_height * 1.4, 
                                    progress, colors)
        
        else:
            # Static text
            current_y = verse_y
            for line in verse_lines:
                bbox = verse_font.getbbox(line)
                line_width = bbox[2] - bbox[0]
                draw.text(((width - line_width) // 2, current_y), 
                         line, font=verse_font, fill=colors["text"])
                current_y += verse_line_height * 1.4
            verse_y = current_y
        
        # Draw reference below box
        ref_font = load_font_safe(48, bold=True)
        bbox = ref_font.getbbox(reference)
        ref_width = bbox[2] - bbox[0]
        ref_x = text_box_x + text_box_width - ref_width - 30
        ref_y = box_y + box_height + 50
        
        # Fade in reference
        ref_opacity = int(220 * min(1.0, (t - duration * 0.7) / 0.3))
        if ref_opacity > 0:
            ref_bg_color = colors["accent"][:3] + (ref_opacity,)
            text_color = colors["text"][:3] + (255,)
            
            draw.rectangle([ref_x - 15, ref_y - 10, ref_x + ref_width + 15, ref_y + bbox[3] + 10], 
                          fill=ref_bg_color)
            draw.text((ref_x, ref_y), reference, font=ref_font, fill=text_color)
        
        # Convert to RGB for video
        return np.array(img.convert("RGB"))
    
    # Create and save video
    video = VideoClip(make_frame, duration=duration)
    video = video.set_fps(fps)
    
    temp_file = f"video_{int(time.time())}.mp4"
    video.write_videofile(temp_file, fps=fps, codec="libx264", verbose=False, logger=None)
    
    with open(temp_file, "rb") as f:
        video_bytes = f.read()
    
    os.remove(temp_file)
    return video_bytes

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def get_verse(book, chapter, verse):
    """Get verse text from API."""
    try:
        url = f"https://bible-api.com/{book}+{chapter}:{verse}"
        response = requests.get(url, timeout=3)
        data = response.json()
        text = data.get("text", "God is our refuge and strength.")
        return text.replace("\n", " ").strip()
    except:
        return "God is our refuge and strength, an ever-present help in trouble."

# ============================================================================
# STREAMLIT UI
# ============================================================================
st.title("🧠 Still Mind")

# Sidebar
with st.sidebar:
    st.header("🎨 Design")
    size = st.selectbox("Size", list(SIZES.keys()))
    color = st.selectbox("Colors", list(COLORS.keys()))
    bg_style = st.selectbox("Background", BACKGROUNDS)
    
    st.header("📖 Content")
    book = st.selectbox("Book", BIBLE_BOOKS)
    col1, col2 = st.columns(2)
    with col1:
        chapter = st.number_input("Chapter", 1, 150, 46)
    with col2:
        verse_num = st.number_input("Verse", 1, 176, 1)
    
    hook = st.text_input("Hook", "Find peace in His presence")
    
    st.header("🎬 Animation")
    animation_type = st.selectbox("Text Animation", ["None", "Typewriter", "Fade"])

# Main area
col1, col2 = st.columns([2, 1])

with col1:
    # Generate preview
    image, verse_text = create_image(size, color, book, chapter, verse_num, hook, animation_type, bg_style)
    st.image(image, use_column_width=True)
    
    # Download buttons
    col_a, col_b = st.columns(2)
    
    with col_a:
        img_bytes = io.BytesIO()
        image.save(img_bytes, format="PNG")
        st.download_button(
            "📥 Download PNG",
            data=img_bytes.getvalue(),
            file_name=f"stillmind_{book}_{chapter}_{verse_num}.png",
            mime="image/png",
            use_container_width=True
        )
    
    with col_b:
        if st.button("🎬 Create Video (6s)", use_container_width=True):
            with st.spinner("Making video..."):
                video_data = create_video(size, color, book, chapter, verse_num, hook, animation_type, bg_style)
                
                if video_data:
                    st.video(video_data)
                    
                    st.download_button(
                        "📥 Download MP4",
                        data=video_data,
                        file_name=f"stillmind_{book}_{chapter}_{verse_num}.mp4",
                        mime="video/mp4",
                        use_container_width=True
                    )

with col2:
    st.header("📱 Social Tools")
    
    reference = f"{book} {chapter}:{verse_num}"
    
    # Smart caption with hashtags based on book
    hashtags = {
        "Psalm": "#Psalms #Wisdom #Worship",
        "Matthew": "#Gospel #Jesus #Teachings",
        "John": "#Gospel #Love #EternalLife",
        "Romans": "#Faith #Grace #Salvation",
        "Ephesians": "#Church #Unity #Blessings",
        "Philippians": "#Joy #Contentment #Hope",
        "James": "#FaithWorks #Wisdom #PracticalFaith"
    }
    
    caption = f"""{hook}

"{verse_text[:180]}{'...' if len(verse_text) > 180 else ''}"

📖 {reference}

{hashtags.get(book, "#BibleVerse #Scripture")}
#StillMind"""
    
    st.text_area("Social Caption", caption, height=200)
    
    if st.button("📋 Copy", use_container_width=True):
        st.code(caption)
        st.success("Ready to paste!")
    
    st.divider()
    
    # Info
    st.caption(f"**Size:** {size}")
    st.caption(f"**Theme:** {color}")
    st.caption(f"**Background:** {bg_style}")
    st.caption(f"**Animation:** {animation_type}")
    st.caption(f"**Verse:** {reference}")

# Cleanup
for file in os.listdir("."):
    if file.startswith("video_") and file.endswith(".mp4"):
        try:
            if time.time() - os.path.getctime(file) > 300:
                os.remove(file)
        except:
            pass

# Footer
st.divider()
st.caption("Still Mind | Green & Blue Theme | Larger Fonts | Working Animations")