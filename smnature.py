import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io, os, requests, math, time, random
import numpy as np
from moviepy.editor import VideoClip

# ============================================================================
# MASTER THEME (Green, Navy Blue, White, Grey)
# ============================================================================
st.set_page_config(page_title="Still Mind Studio", layout="wide")

THEME = {
    "navy": (10, 25, 45, 255),       # Deep Navy
    "navy_light": (30, 50, 80, 255),  # Light Navy for gradients
    "grey_dawn": (100, 110, 120, 255), # Dawn Grey
    "grey_light": (140, 150, 160, 255),
    "forest": (46, 125, 50, 255),    # Deep Green
    "forest_light": (76, 175, 80, 255), # Light Green
    "white": (255, 255, 255, 255),
    "white_trans": (255, 255, 255, 180),
    "river": (20, 40, 70, 180),      # Translucent Navy
    "river_light": (40, 80, 120, 220)
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def safe_coords(x, y, size, width, height):
    """Ensure coordinates are valid for drawing."""
    x1 = max(0, int(x - size))
    y1 = max(0, int(y - size))
    x2 = min(width - 1, int(x + size))
    y2 = min(height - 1, int(y + size))
    
    # Ensure x1 < x2 and y1 < y2
    if x1 >= x2:
        x1, x2 = min(x1, x2), max(x1, x2)
        if x1 == x2:
            x2 += 1
    if y1 >= y2:
        y1, y2 = min(y1, y2), max(y1, y2)
        if y1 == y2:
            y2 += 1
    
    return [x1, y1, x2, y2]

def interpolate_color(color1, color2, progress):
    """Smooth color transition."""
    return tuple(int(color1[i] + (color2[i] - color1[i]) * progress) for i in range(4))

def load_font_safe(size, bold=False):
    """Load font with fallbacks."""
    try:
        if bold:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        else:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except:
        try:
            if bold:
                return ImageFont.truetype("arialbd.ttf", size)
            else:
                return ImageFont.truetype("arial.ttf", size)
        except:
            return ImageFont.load_default(size)

@st.cache_data(ttl=3600)
def fetch_verse(book, chapter, verse):
    """Fetch Bible verse with caching."""
    try:
        url = f"https://bible-api.com/{book}+{chapter}:{verse}"
        response = requests.get(url, timeout=5)
        data = response.json()
        text = data.get("text", "The Lord is my shepherd; I shall not want.").strip().replace("\n", " ")
        return text
    except:
        return "The Lord is my shepherd; I shall not want. He makes me lie down in green pastures."

# ============================================================================
# ENHANCED NATURE ANIMATIONS
# ============================================================================
def draw_birds_and_reflections(draw, w, h, t):
    """Draw flying birds with reflections."""
    for i in range(4):
        # Flying path with variation
        base_x = (t * 200) % (w + 300) - 150
        bird_x = base_x + (i * 80) + math.sin(t * 3 + i) * 30
        bird_y = h * 0.25 + (math.sin(t * 2 + i * 0.5) * 40)
        
        # Wing flap animation
        flap_speed = 14 + i * 2
        flap = math.sin(t * flap_speed) * 10
        
        # Draw bird (white with alpha)
        bird_color = THEME["white_trans"]
        wing_length = 12
        
        # Bird body (simple V shape)
        draw.line([(bird_x, bird_y), (bird_x - wing_length, bird_y - 5 + flap)], 
                 fill=bird_color, width=3)
        draw.line([(bird_x, bird_y), (bird_x + wing_length, bird_y - 5 + flap)], 
                 fill=bird_color, width=3)
        
        # Bird reflection on water
        reflection_y = h - bird_y + 180  # Reflection position
        if reflection_y > h * 0.6:  # Only draw if in water area
            # Water distortion effect
            distortion = math.sin(t * 8 + i) * 15
            ref_opacity = 60 - i * 10  # Fade reflections in distance
            
            reflection_color = (200, 210, 220, ref_opacity)
            draw.line([(bird_x + distortion, reflection_y), 
                      (bird_x - wing_length + distortion, reflection_y + 3 - flap/2)], 
                     fill=reflection_color, width=1)
            draw.line([(bird_x + distortion, reflection_y), 
                      (bird_x + wing_length + distortion, reflection_y + 3 - flap/2)], 
                     fill=reflection_color, width=1)

def draw_fractal_tree(draw, x, y, angle, length, depth, t, max_depth, color):
    """Draw organic tree with growth animation."""
    if depth <= 0:
        return
    
    # Calculate growth progress
    time_per_branch = 0.3
    delay = (max_depth - depth) * time_per_branch
    growth_progress = max(0, min(1, (t - delay) / 2.0))
    
    if growth_progress <= 0:
        return
    
    # Natural wind sway (stronger at tips)
    wind_strength = 0.8 + 0.4 * math.sin(t * 0.5)
    sway = math.sin(t * 1.8 + depth * 0.7) * (0.15 / max(1, depth - 1)) * wind_strength
    
    # Animated length
    current_length = length * growth_progress
    
    # Calculate branch end
    x2 = x + math.cos(angle + sway) * current_length
    y2 = y + math.sin(angle + sway) * current_length
    
    # Determine color (trunk vs leaves)
    if depth > 4:  # Trunk/branches
        branch_color = THEME["grey_dawn"][:3] + (int(200 * growth_progress),)
        thickness = depth * 2
    else:  # Leaves/twigs
        # Add seasonal color variation
        seasonal_shift = int(30 * math.sin(t * 0.3 + depth))
        leaf_color = (
            min(255, color[0] + seasonal_shift),
            min(255, color[1] + seasonal_shift),
            min(255, color[2]),
            int(180 * growth_progress)
        )
        branch_color = leaf_color
        thickness = max(1, depth * 1.5)
    
    # Draw the branch
    draw.line([(int(x), int(y)), (int(x2), int(y2))], 
             fill=branch_color, width=int(thickness))
    
    # Recursive branches with variation
    if depth > 1:
        # Left branch
        left_angle = angle - (0.42 + 0.1 * math.sin(t + depth))
        left_length = current_length * (0.7 + 0.1 * math.cos(t + depth))
        draw_fractal_tree(draw, x2, y2, left_angle, left_length, 
                         depth - 1, t, max_depth, color)
        
        # Right branch
        right_angle = angle + (0.42 + 0.1 * math.cos(t + depth))
        right_length = current_length * (0.7 + 0.1 * math.sin(t + depth))
        draw_fractal_tree(draw, x2, y2, right_angle, right_length, 
                         depth - 1, t, max_depth, color)
        
        # Occasionally add third branch for fuller trees
        if depth > 3 and random.random() > 0.6:
            middle_angle = angle + (0.1 * math.sin(t * 2))
            middle_length = current_length * 0.5
            draw_fractal_tree(draw, x2, y2, middle_angle, middle_length, 
                             depth - 2, t, max_depth, color)

def draw_river_with_reflections(draw, w, h, t):
    """Draw flowing river with reflections."""
    river_points = []
    
    # Generate left bank points
    for y in range(int(h * 0.5), h + 20, 20):
        # River width variation
        width_variation = math.sin(y * 0.01 - t * 3) * 60
        
        # Perspective effect (river narrows as it goes up)
        perspective = (y - h * 0.5) * 1.5
        
        left_x = w//2 - 200 - perspective + width_variation
        river_points.append((int(left_x), int(y)))
    
    # Generate right bank points (in reverse)
    right_points = []
    for y in range(int(h * 0.5), h + 20, 20):
        width_variation = math.sin(y * 0.01 - t * 3 + math.pi) * 60
        perspective = (y - h * 0.5) * 1.5
        right_x = w//2 + 200 + perspective + width_variation
        right_points.append((int(right_x), int(y)))
    
    # Combine points for polygon (close the shape)
    all_points = river_points + right_points[::-1]
    
    if len(all_points) > 2:
        # Draw river with gradient opacity
        for i in range(3):
            river_color = interpolate_color(
                THEME["river"],
                THEME["river_light"],
                i / 3
            )
            
            # Offset each layer for depth
            offset_points = [(x + i * 3, y + i * 2) for x, y in all_points]
            draw.polygon(offset_points, fill=river_color)
    
    # Add river highlights (sun reflection)
    highlight_y = int(h * 0.75)
    highlight_width = 100 + int(50 * math.sin(t * 2))
    
    for i in range(3):
        highlight_opacity = 30 - i * 10
        highlight_points = [
            (w//2 - highlight_width, highlight_y + i * 10),
            (w//2 + highlight_width, highlight_y + i * 10),
            (w//2 + highlight_width//2, highlight_y + 30 + i * 10),
            (w//2 - highlight_width//2, highlight_y + 30 + i * 10)
        ]
        draw.polygon(highlight_points, 
                    fill=(255, 255, 255, highlight_opacity))

def draw_clouds(draw, w, h, t):
    """Draw subtle clouds."""
    for i in range(3):
        cloud_x = w * (0.2 + i * 0.3) + t * 20
        cloud_y = h * 0.15 + math.sin(t + i) * 20
        
        # Draw cloud as overlapping circles
        for j in range(5):
            offset_x = cloud_x + j * 40 + math.sin(t * 0.5 + j) * 20
            offset_y = cloud_y + math.cos(t * 0.7 + j) * 15
            size = 60 + math.sin(t * 0.3 + j) * 20
            
            bbox = safe_coords(offset_x, offset_y, size, w, h)
            if bbox[0] < bbox[2] and bbox[1] < bbox[3]:
                draw.ellipse(bbox, fill=(255, 255, 255, 40))

# ============================================================================
# MAIN COMPOSITION ENGINE
# ============================================================================
def create_master_frame(w, h, book, chapter, verse_num, hook, t=0, is_video=False, duration=6):
    """Create the complete composition."""
    # Time progress for animations
    time_progress = t / duration if duration > 0 else 0
    
    # 1. Background with Dawn Progression
    if time_progress < 0.5:
        # Night to dawn
        dawn_progress = time_progress * 2
        bg_color = interpolate_color(THEME["navy"], THEME["grey_dawn"], dawn_progress)
    else:
        # Dawn to morning
        morning_progress = (time_progress - 0.5) * 2
        bg_color = interpolate_color(THEME["grey_dawn"], THEME["navy_light"], morning_progress)
    
    img = Image.new("RGBA", (w, h), bg_color)
    draw = ImageDraw.Draw(img)
    
    # 2. Sunrise/Sunset Glow
    if is_video or time_progress > 0:
        sun_y = h * 0.65 - (time_progress * 320)
        sun_color = interpolate_color(
            (255, 255, 255, 100),  # Night white
            (255, 220, 100, 200),  # Sunrise gold
            time_progress
        )
        
        # Draw glow layers
        for r in range(120, 0, -20):
            alpha = int(60 * (1 - r/120) * time_progress)
            bbox = safe_coords(w//2, sun_y, r, w, h)
            if bbox[0] < bbox[2] and bbox[1] < bbox[3]:
                draw.ellipse(bbox, fill=(255, 255, 255, alpha))
        
        # Sun/Moon body
        sun_size = 40 + int(20 * time_progress)
        bbox = safe_coords(w//2, sun_y, sun_size, w, h)
        if bbox[0] < bbox[2] and bbox[1] < bbox[3]:
            draw.ellipse(bbox, fill=sun_color)
    
    # 3. Draw Nature Elements
    draw_clouds(draw, w, h, t)
    draw_river_with_reflections(draw, w, h, t)
    draw_birds_and_reflections(draw, w, h, t)
    
    # 4. Growing Trees
    tree_color = interpolate_color(THEME["forest"], THEME["forest_light"], time_progress)
    draw_fractal_tree(draw, 200, h-20, -math.pi/2, 170, 8, t, 8, tree_color)
    draw_fractal_tree(draw, w-200, h-20, -math.pi/2, 150, 7, t, 7, tree_color)
    
    # 5. FROSTED GLASS TEXT BOX
    box_width = 900
    box_height = 550
    box_x = (w - box_width) // 2
    box_y = (h - box_height) // 2 - 100
    
    # Create frosted glass effect
    glass_region = img.crop((
        max(0, box_x - 20),
        max(0, box_y - 20),
        min(w, box_x + box_width + 20),
        min(h, box_y + box_height + 20)
    ))
    
    if glass_region.width > 0 and glass_region.height > 0:
        glass_region = glass_region.filter(ImageFilter.GaussianBlur(15))
        img.paste(glass_region, (box_x - 20, box_y - 20))
    
    # Glass overlay with border
    draw.rectangle([box_x, box_y, box_x + box_width, box_y + box_height], 
                  fill=(40, 45, 50, 160), 
                  outline=(255, 255, 255, 40), 
                  width=2)
    
    # Decorative corners
    corner_size = 6
    for cx, cy in [(box_x, box_y), (box_x + box_width, box_y), 
                   (box_x, box_y + box_height), (box_x + box_width, box_y + box_height)]:
        # Diamond shape corners
        points = [
            (cx, cy - corner_size),
            (cx + corner_size, cy),
            (cx, cy + corner_size),
            (cx - corner_size, cy)
        ]
        draw.polygon(points, fill=THEME["forest_light"])
    
    # 6. TYPERWRITER TEXT ANIMATION
    verse_text = fetch_verse(book, chapter, verse_num)
    
    if is_video:
        typewriter_duration = 4.5
        type_progress = min(1.0, t / typewriter_duration)
        visible_text = verse_text[:int(len(verse_text) * type_progress)]
    else:
        type_progress = 1.0
        visible_text = verse_text
    
    # Load font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 48)
    except:
        font = load_font_safe(48)
    
    # Text wrapping
    max_text_width = box_width - 100
    words = visible_text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = font.getbbox(test_line) if hasattr(font, 'getbbox') else font.getsize(test_line)
        text_width = bbox[2] - bbox[0] if hasattr(font, 'getbbox') else bbox[0]
        
        if text_width <= max_text_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    # Draw text lines
    line_height = 70
    text_y = box_y + 80
    
    for line in lines:
        if hasattr(font, 'getbbox'):
            bbox = font.getbbox(line)
            text_width = bbox[2] - bbox[0]
        else:
            text_width = font.getsize(line)[0]
        
        text_x = box_x + (box_width - text_width) // 2
        
        # Text shadow for readability
        draw.text((text_x + 2, text_y + 2), line, 
                 font=font, fill=(0, 0, 0, 150))
        
        # Main text
        text_alpha = int(255 * type_progress) if is_video else 255
        draw.text((text_x, text_y), line, 
                 font=font, fill=THEME["white"][:3] + (text_alpha,))
        
        text_y += line_height
    
    # 7. HEADER HOOK
    if hook:
        hook_font = load_font_safe(52, bold=True)
        if hasattr(hook_font, 'getbbox'):
            hook_bbox = hook_font.getbbox(hook.upper())
            hook_width = hook_bbox[2] - hook_bbox[0]
        else:
            hook_width = hook_font.getsize(hook.upper())[0]
        
        hook_x = box_x + (box_width - hook_width) // 2
        hook_y = box_y - 90
        
        hook_alpha = int(255 * min(1.0, t / 1.0)) if is_video else 255
        
        draw.text((hook_x, hook_y), hook.upper(), 
                 font=hook_font, fill=THEME["white"][:3] + (hook_alpha,))
    
    # 8. REFERENCE
    ref_font = load_font_safe(38, bold=True)
    reference = f"{book} {chapter}:{verse_num}"
    
    if hasattr(ref_font, 'getbbox'):
        ref_bbox = ref_font.getbbox(reference)
        ref_width = ref_bbox[2] - ref_bbox[0]
    else:
        ref_width = ref_font.getsize(reference)[0]
    
    ref_x = box_x + box_width - ref_width - 40
    ref_y = box_y + box_height + 40
    
    ref_alpha = int(255 * max(0, min(1.0, (t - 4) / 1))) if is_video else 255
    
    if ref_alpha > 0:
        # Reference background
        draw.rectangle([ref_x - 15, ref_y - 10, 
                       ref_x + ref_width + 15, 
                       ref_y + (ref_bbox[3] - ref_bbox[1]) + 10 if hasattr(ref_font, 'getbbox') else ref_y + 40],
                      fill=THEME["forest"][:3] + (ref_alpha // 2,))
        
        # Reference text
        draw.text((ref_x, ref_y), reference,
                 font=ref_font,
                 fill=THEME["white"][:3] + (ref_alpha,))
    
    return img

# ============================================================================
# VIDEO GENERATION
# ============================================================================
def create_meditation_video(w, h, book, chapter, verse, hook, duration=8):
    """Create animated meditation video."""
    fps = 24
    
    def make_frame(t):
        img = create_master_frame(w, h, book, chapter, verse, hook, t, True, duration)
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
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

# ============================================================================
# STREAMLIT UI
# ============================================================================
st.title("🌿 Still Mind Nature Studio")
st.markdown("### Create serene nature-themed scripture meditations")

# Sidebar controls
with st.sidebar:
    st.header("🌅 Nature Settings")
    
    hook = st.text_input("Header Text", "MORNING PEACE")
    
    st.header("📖 Scripture Selection")
    book = st.selectbox("Book", ["Psalm", "Isaiah", "Matthew", "John", "Romans", "Philippians", "James"], index=0)
    
    col1, col2 = st.columns(2)
    with col1:
        chapter = st.number_input("Chapter", 1, 150, 23)
    with col2:
        verse = st.number_input("Verse", 1, 176, 1)
    
    st.header("🎬 Animation Controls")
    time_scrubber = st.slider("Animation Time", 0.0, 8.0, 0.0, 0.1)
    
    st.header("📐 Size Format")
    size_option = st.selectbox("Choose Size", 
                              ["TikTok (1080x1920)", "Instagram (1080x1080)", "Stories (1080x1350)"])
    
    if "1080x1080" in size_option:
        W, H = 1080, 1080
    elif "1080x1350" in size_option:
        W, H = 1080, 1350
    else:
        W, H = 1080, 1920

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    # Preview section
    st.subheader("🌿 Live Preview")
    
    with st.spinner("Creating nature scene..."):
        preview_img = create_master_frame(W, H, book, chapter, verse, hook, time_scrubber, False, 8)
    
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
            file_name=f"still_mind_{book}_{chapter}_{verse}.png",
            mime="image/png",
            use_container_width=True
        )
    
    with col_btn2:
        # Generate video
        if st.button("🎬 Create Meditation Video (8s)", use_container_width=True):
            with st.spinner("Animating river, birds, and growing trees..."):
                video_data = create_meditation_video(W, H, book, chapter, verse, hook, 8)
                
                if video_data:
                    st.video(video_data)
                    
                    # Video download button
                    st.download_button(
                        label="📥 Download MP4",
                        data=video_data,
                        file_name=f"still_mind_meditation_{book}_{chapter}_{verse}.mp4",
                        mime="video/mp4",
                        use_container_width=True
                    )

with col2:
    # Info panel
    st.subheader("🌳 Scene Details")
    
    st.write("**Active Elements:**")
    st.success("✓ Flowing River with Reflections")
    st.success("✓ Flying Birds with Water Reflections")
    st.success("✓ Growing Fractal Trees")
    st.success("✓ Sunrise/Sunset Progression")
    st.success("✓ Frosted Glass Text Box")
    st.success("✓ Typewriter Text Animation")
    
    st.metric("Image Size", f"{W} × {H}")
    st.metric("Animation Time", f"{time_scrubber:.1f}s")
    
    st.divider()
    
    # Verse info
    verse_text = fetch_verse(book, chapter, verse)
    st.write("**Selected Verse:**")
    st.info(f"{book} {chapter}:{verse}")
    
    st.write("**Preview:**")
    st.caption(verse_text[:120] + "..." if len(verse_text) > 120 else verse_text)
    
    st.divider()
    
    # Social media caption
    st.subheader("📱 Social Share")
    
    caption = f"""{hook}

"{verse_text[:100]}..."

🌿 {book} {chapter}:{verse}

#StillMind #NatureMeditation #ScriptureInNature #Peace #Mindfulness #BibleVerse"""

    st.text_area("Social Media Caption", caption, height=150)
    
    if st.button("📋 Copy Caption", use_container_width=True):
        st.code(caption)
        st.success("Copied to clipboard!")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #2E7D32; font-size: 0.9rem;'>
    <p>🌿 Still Mind Nature Studio • Psalm 23:2 • "He makes me lie down in green pastures"</p>
</div>
""", unsafe_allow_html=True)

# Cleanup temporary files
for file in os.listdir("."):
    if file.startswith("temp_video_") and file.endswith(".mp4"):
        try:
            os.remove(file)
        except:
            pass