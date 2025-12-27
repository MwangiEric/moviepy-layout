import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io, os, requests, math, time
import numpy as np
from moviepy.editor import VideoClip, CompositeVideoClip, vfx

# ============================================================================
# STREAMLIT SETUP
# ============================================================================
st.set_page_config(page_title="Verse Studio", page_icon="✝️", layout="wide")

# ============================================================================
# SIMPLE CONFIGURATION
# ============================================================================
COLORS = {
    "Still Mind Green": {
        "bg": [(20, 40, 60, 255), (30, 60, 90, 255)],
        "accent": (76, 175, 80, 255),
        "text": (255, 255, 255, 255)
    },
    "Galilee Morning": {
        "bg": [(250, 249, 246, 255), (224, 228, 213, 255)],
        "accent": (196, 137, 31, 255),
        "text": (24, 48, 40, 255)
    },
    "Deep Slate": {
        "bg": [(15, 30, 30, 255), (35, 65, 65, 255)],
        "accent": (252, 191, 73, 255),
        "text": (240, 240, 240, 255)
    }
}

SIZES = {
    "TikTok": (1080, 1920),
    "Square": (1080, 1080)
}

BACKGROUNDS = ["Gradient", "Abstract", "Particles", "Geometric"]

BIBLE_BOOKS = ["Psalm", "Matthew", "John", "Romans", "Ephesians", "Philippians", "James"]

# ============================================================================
# SMART FONT SIZING
# ============================================================================
def calculate_font_size(text, target_size, min_size, max_width, max_height):
    """Dynamically adjust font size based on text length."""
    # Try to load arial font
    try:
        font = ImageFont.truetype("arial.ttf", target_size)
    except:
        font = ImageFont.load_default()
    
    # Start with target size and reduce until it fits
    for size in range(target_size, min_size - 1, -2):
        try:
            font = ImageFont.truetype("arial.ttf", size)
        except:
            font = ImageFont.load_default()
        
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
        total_height = len(lines) * line_height * 1.2
        
        if total_height <= max_height:
            return size, lines, font
    
    # If we get here, use minimum size
    try:
        font = ImageFont.truetype("arial.ttf", min_size)
    except:
        font = ImageFont.load_default()
    
    return min_size, [text], font

# ============================================================================
# BACKGROUND GENERATORS
# ============================================================================
def create_background(width, height, style, colors, time_offset=0):
    """Create different background styles."""
    img = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(img)
    
    color1, color2 = colors["bg"]
    
    if style == "Gradient":
        # Simple gradient
        for y in range(height):
            ratio = y / height
            r = int((1-ratio) * color1[0] + ratio * color2[0])
            g = int((1-ratio) * color1[1] + ratio * color2[1])
            b = int((1-ratio) * color1[2] + ratio * color2[2])
            a = int((1-ratio) * color1[3] + ratio * color2[3])
            draw.line([(0, y), (width, y)], fill=(r, g, b, a))
    
    elif style == "Abstract":
        # Abstract moving shapes
        for i in range(5):
            offset = int(time_offset * 100) % 1000
            size = 100 + int(50 * math.sin(time_offset + i))
            x = int(width * (0.2 * i) + offset % 300)
            y = int(height * 0.5 + 100 * math.cos(time_offset + i))
            
            # Draw abstract shape
            draw.ellipse([x, y, x+size, y+size], 
                        outline=colors["accent"], 
                        width=3)
            
            # Smaller inner shape
            draw.ellipse([x+20, y+20, x+size-20, y+size-20], 
                        outline=colors["accent"], 
                        width=2)
    
    elif style == "Particles":
        # Particle effect
        for i in range(50):
            x = int(width * (0.5 + 0.4 * math.sin(time_offset + i * 0.2)))
            y = int(height * (0.5 + 0.4 * math.cos(time_offset + i * 0.3)))
            size = 2 + int(3 * math.sin(time_offset + i * 0.5))
            
            # Random opacity
            opacity = int(150 + 100 * math.sin(time_offset + i))
            particle_color = colors["accent"][:3] + (opacity,)
            
            draw.ellipse([x-size, y-size, x+size, y+size], 
                        fill=particle_color)
    
    elif style == "Geometric":
        # Geometric patterns
        for i in range(10):
            x = int(width * (0.1 + 0.08 * i) + time_offset * 10 % 200)
            y = int(height * 0.3 + 50 * math.sin(time_offset + i))
            
            # Draw geometric shape
            points = []
            for j in range(6):
                angle = 2 * math.pi * j / 6 + time_offset
                px = x + 40 * math.cos(angle)
                py = y + 40 * math.sin(angle)
                points.append((px, py))
            
            if len(points) > 2:
                draw.polygon(points, outline=colors["accent"], width=2)
    
    return img

# ============================================================================
# TEXT ANIMATION FUNCTIONS
# ============================================================================
def draw_typewriter_text(draw, text_lines, font, x, y, line_height, progress, colors):
    """Draw text with typewriter animation."""
    # Calculate total characters
    full_text = " ".join(text_lines)
    total_chars = len(full_text)
    visible_chars = int(total_chars * progress)
    
    # Build visible text
    visible_text = full_text[:visible_chars]
    
    # Split into visible lines
    words = visible_text.split()
    visible_lines = []
    current_line = ""
    
    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = font.getbbox(test_line)
        if bbox[2] - bbox[0] <= 900:  # Max width
            current_line = test_line
        else:
            if current_line:
                visible_lines.append(current_line)
            current_line = word
    
    if current_line:
        visible_lines.append(current_line)
    
    # Draw visible lines
    current_y = y
    for line in visible_lines:
        bbox = font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        draw.text(((1080 - line_width) // 2, current_y), 
                 line, font=font, fill=colors["text"])
        current_y += line_height
    
    # Draw cursor
    if progress < 1.0:
        if visible_lines:
            last_line = visible_lines[-1]
            bbox = font.getbbox(last_line)
            cursor_x = (1080 - bbox[2]) // 2 + bbox[2] + 5
            cursor_y = current_y - line_height + 10
            draw.line([(cursor_x, cursor_y), (cursor_x, cursor_y + line_height - 20)], 
                     fill=colors["accent"], width=3)
    
    return current_y

def draw_fade_text(draw, text_lines, font, x, y, line_height, progress, colors):
    """Draw text with fade-in animation."""
    opacity = int(255 * progress)
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
# IMAGE GENERATION
# ============================================================================
def create_image(size_name, color_name, book, chapter, verse, hook, animation_type, bg_style):
    """Create the verse image with smart layout."""
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
    
    # Smart font sizing for verse
    verse_size, verse_lines, verse_font = calculate_font_size(
        verse_text, 
        target_size=130, 
        min_size=60,
        max_width=text_box_width - 40,
        max_height=height * 0.5
    )
    
    # Other fonts
    hook_font = ImageFont.truetype("arial.ttf", 70) if os.path.exists("arial.ttf") else ImageFont.load_default()
    ref_font = ImageFont.truetype("arial.ttf", 40) if os.path.exists("arial.ttf") else ImageFont.load_default()
    
    # Calculate verse box height
    verse_line_height = verse_font.getbbox("A")[3] - verse_font.getbbox("A")[1]
    verse_height = len(verse_lines) * verse_line_height * 1.2
    
    # Calculate total box dimensions
    box_padding = 60
    box_height = verse_height + (box_padding * 2)
    box_y = (height - box_height) // 2
    
    # Draw semi-transparent background box
    box_color = (0, 0, 0, 180)  # Semi-transparent black
    draw.rectangle([text_box_x, box_y, text_box_x + text_box_width, box_y + box_height], 
                  fill=box_color)
    
    # Draw hook ABOVE the box (not inside)
    if hook:
        bbox = hook_font.getbbox(hook)
        hook_width = bbox[2] - bbox[0]
        hook_x = (width - hook_width) // 2
        hook_y = box_y - 80  # Position above the box
        
        # Add a subtle background for hook
        draw.rectangle([hook_x - 20, hook_y - 10, hook_x + hook_width + 20, hook_y + bbox[3] + 10], 
                      fill=colors["accent"])
        
        draw.text((hook_x, hook_y), hook, font=hook_font, fill=colors["text"])
    
    # Draw verse inside box
    verse_y = box_y + box_padding
    
    if animation_type == "Typewriter":
        verse_y = draw_typewriter_text(draw, verse_lines, verse_font, 
                                      text_box_x, verse_y, verse_line_height * 1.2, 
                                      1.0, colors)
    elif animation_type == "Fade":
        verse_y = draw_fade_text(draw, verse_lines, verse_font, 
                                text_box_x, verse_y, verse_line_height * 1.2, 
                                1.0, colors)
    else:
        # Normal text
        current_y = verse_y
        for line in verse_lines:
            bbox = verse_font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            draw.text(((width - line_width) // 2, current_y), 
                     line, font=verse_font, fill=colors["text"])
            current_y += verse_line_height * 1.2
        verse_y = current_y
    
    # Draw reference BELOW the box (bottom right corner)
    bbox = ref_font.getbbox(reference)
    ref_width = bbox[2] - bbox[0]
    ref_x = text_box_x + text_box_width - ref_width - 20  # Right aligned
    ref_y = box_y + box_height + 40  # Position below the box
    
    # Add subtle background for reference
    draw.rectangle([ref_x - 10, ref_y - 5, ref_x + ref_width + 10, ref_y + bbox[3] + 5], 
                  fill=colors["accent"])
    
    draw.text((ref_x, ref_y), reference, font=ref_font, fill=colors["text"])
    
    # Add "Still Mind" brand (top left)
    brand_font = ImageFont.truetype("arial.ttf", 60) if os.path.exists("arial.ttf") else ImageFont.load_default()
    draw.text((50, 50), "Still Mind", font=brand_font, fill=(76, 175, 80, 255))
    
    return image, verse_text

# ============================================================================
# VIDEO GENERATION
# ============================================================================
def create_video(size_name, color_name, book, chapter, verse, hook, animation_type, bg_style):
    """Create animated video."""
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
        target_size=130, 
        min_size=60,
        max_width=text_box_width - 40,
        max_height=height * 0.5
    )
    
    # Video frame generator
    def make_frame(t):
        # Create animated background
        img = create_background(width, height, bg_style, colors, t)
        draw = ImageDraw.Draw(img)
        
        # Calculate text box
        text_box_x = (width - text_box_width) // 2
        verse_line_height = verse_font.getbbox("A")[3] - verse_font.getbbox("A")[1]
        verse_height = len(verse_lines) * verse_line_height * 1.2
        
        box_padding = 60
        box_height = verse_height + (box_padding * 2)
        box_y = (height - box_height) // 2
        
        # Draw semi-transparent box
        box_color = (0, 0, 0, 180)
        draw.rectangle([text_box_x, box_y, text_box_x + text_box_width, box_y + box_height], 
                      fill=box_color)
        
        # Draw hook above box
        if hook:
            hook_font = ImageFont.truetype("arial.ttf", 70) if os.path.exists("arial.ttf") else ImageFont.load_default()
            bbox = hook_font.getbbox(hook)
            hook_width = bbox[2] - bbox[0]
            hook_x = (width - hook_width) // 2
            hook_y = box_y - 80
            
            draw.rectangle([hook_x - 20, hook_y - 10, hook_x + hook_width + 20, hook_y + bbox[3] + 10], 
                          fill=colors["accent"])
            draw.text((hook_x, hook_y), hook, font=hook_font, fill=colors["text"])
        
        # Draw verse with animation
        verse_y = box_y + box_padding
        
        if animation_type == "Typewriter":
            progress = min(1.0, t / (duration * 0.8))  # Typewriter completes at 80% of video
            verse_y = draw_typewriter_text(draw, verse_lines, verse_font, 
                                          text_box_x, verse_y, verse_line_height * 1.2, 
                                          progress, colors)
        
        elif animation_type == "Fade":
            progress = min(1.0, t / (duration * 0.5))  # Fade completes at 50% of video
            verse_y = draw_fade_text(draw, verse_lines, verse_font, 
                                    text_box_x, verse_y, verse_line_height * 1.2, 
                                    progress, colors)
        
        else:
            # Static text
            current_y = verse_y
            for line in verse_lines:
                bbox = verse_font.getbbox(line)
                line_width = bbox[2] - bbox[0]
                draw.text(((width - line_width) // 2, current_y), 
                         line, font=verse_font, fill=colors["text"])
                current_y += verse_line_height * 1.2
            verse_y = current_y
        
        # Draw reference below box
        ref_font = ImageFont.truetype("arial.ttf", 40) if os.path.exists("arial.ttf") else ImageFont.load_default()
        bbox = ref_font.getbbox(reference)
        ref_width = bbox[2] - bbox[0]
        ref_x = text_box_x + text_box_width - ref_width - 20
        ref_y = box_y + box_height + 40
        
        # Fade in reference
        ref_opacity = int(255 * min(1.0, (t - duration * 0.7) / 0.3))
        if ref_opacity > 0:
            ref_color = colors["accent"][:3] + (ref_opacity,)
            text_color = colors["text"][:3] + (ref_opacity,)
            
            draw.rectangle([ref_x - 10, ref_y - 5, ref_x + ref_width + 10, ref_y + bbox[3] + 5], 
                          fill=ref_color)
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
        return data.get("text", "God is our refuge and strength.").replace("\n", " ")
    except:
        return "God is our refuge and strength, an ever-present help in trouble."

# ============================================================================
# STREAMLIT UI
# ============================================================================
st.title("🧠 Still Mind - Verse Studio")

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
            file_name=f"verse_{book}_{chapter}_{verse_num}.png",
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
                        file_name=f"verse_{book}_{chapter}_{verse_num}.mp4",
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

"{verse_text[:150]}{'...' if len(verse_text) > 150 else ''}"

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
    st.caption(f"**Colors:** {color}")
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
st.caption("Still Mind Verse Studio | Smart Font Sizing | Working Animations | Abstract Backgrounds")