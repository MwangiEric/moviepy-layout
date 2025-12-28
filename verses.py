import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io, os, requests, math, time, random
import numpy as np
from moviepy.editor import VideoClip, vfx

# ============================================================================
# STREAMLIT SETUP
# ============================================================================
st.set_page_config(page_title="Still Mind Studio", page_icon="✨", layout="wide")

# ============================================================================
# CREATIVE COLOR PALETTES - GREEN, NAVY BLUE, WHITE, GREY
# ============================================================================
COLORS = {
    "Emerald Depths": {
        "bg": [(10, 30, 50, 255), (15, 45, 75, 255)],  # Deep navy to blue
        "accent": (76, 175, 80, 255),  # Bright green
        "text": (255, 255, 255, 255),  # White
        "secondary": (200, 220, 200, 255),  # Light green
        "highlight": (255, 215, 0, 255)  # Gold highlight
    },
    "Ocean Wisdom": {
        "bg": [(15, 40, 65, 255), (25, 55, 90, 255)],  # Ocean blues
        "accent": (100, 200, 220, 255),  # Cyan
        "text": (240, 248, 255, 255),  # Alice blue
        "secondary": (180, 230, 240, 255),  # Light cyan
        "highlight": (255, 200, 100, 255)  # Peach
    },
    "Forest Sanctuary": {
        "bg": [(20, 35, 30, 255), (30, 55, 45, 255)],  # Dark green gradient
        "accent": (120, 180, 120, 255),  # Sage green
        "text": (245, 245, 245, 255),  # Off-white
        "secondary": (210, 225, 210, 255),  # Light sage
        "highlight": (255, 225, 150, 255)  # Cream
    },
    "Misty Mountains": {
        "bg": [(40, 50, 65, 255), (60, 70, 85, 255)],  # Grey-blue mountains
        "accent": (140, 200, 140, 255),  // Misty green
        "text": (255, 255, 255, 255),
        "secondary": (220, 220, 220, 255),  // Light grey
        "highlight": (255, 180, 120, 255)  // Sunset orange
    }
}

SIZES = {
    "TikTok (9:16)": (1080, 1920),
    "Instagram (1:1)": (1080, 1080),
    "Story (16:9)": (1920, 1080)
}

BACKGROUNDS = ["Gradient", "Stars", "Bubbles", "Geometric", "Waves", "Particles"]

ANIMATIONS = ["None", "Typewriter", "Fade In", "Slide Up", "Zoom In", "Word by Word", "Glow Pulse"]

# ============================================================================
# SMART FONT LOADING
# ============================================================================
def load_font_safe(size, bold=False):
    """Try multiple fonts before falling back."""
    font_variants = []
    
    if bold:
        font_variants = [
            "arialbd.ttf", "Arial-Bold.ttf", "Helvetica-Bold.ttf",
            "DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf",
            "Montserrat-Bold.ttf", "Roboto-Bold.ttf"
        ]
    else:
        font_variants = [
            "arial.ttf", "Arial.ttf", "Helvetica.ttf",
            "DejaVuSans.ttf", "LiberationSans-Regular.ttf",
            "Montserrat-Regular.ttf", "Roboto-Regular.ttf"
        ]
    
    # Try system font paths
    font_paths = [
        "",  # Current directory
        "/usr/share/fonts/truetype/",
        "/usr/local/share/fonts/",
        "C:/Windows/Fonts/",
        "/Library/Fonts/"
    ]
    
    for font_path in font_paths:
        for variant in font_variants:
            full_path = os.path.join(font_path, variant)
            try:
                if os.path.exists(full_path):
                    return ImageFont.truetype(full_path, size)
            except:
                continue
    
    return ImageFont.load_default(size)

# ============================================================================
# CREATIVE BACKGROUNDS WITH DECORATIONS
# ============================================================================
def create_background(width, height, style, colors, time_offset=0):
    """Create backgrounds with decorations like stars, etc."""
    img = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(img)
    
    color1, color2 = colors["bg"]
    
    if style == "Gradient":
        # Beautiful gradient
        for y in range(height):
            ratio = y / height
            # Add subtle wave effect
            wave = math.sin(y / 100 + time_offset) * 0.05
            ratio = max(0, min(1, ratio + wave))
            
            r = int((1-ratio) * color1[0] + ratio * color2[0])
            g = int((1-ratio) * color1[1] + ratio * color2[1])
            b = int((1-ratio) * color1[2] + ratio * color2[2])
            a = int((1-ratio) * color1[3] + ratio * color2[3])
            draw.line([(0, y), (width, y)], fill=(r, g, b, a))
    
    elif style == "Stars":
        # Starry night with twinkling stars
        for y in range(height):
            ratio = y / height
            r = int((1-ratio) * color1[0] + ratio * color2[0])
            g = int((1-ratio) * color1[1] + ratio * color2[1])
            b = int((1-ratio) * color1[2] + ratio * color2[2])
            a = int((1-ratio) * color1[3] + ratio * color2[3])
            draw.line([(0, y), (width, y)], fill=(r, g, b, a))
        
        # Add stars
        for i in range(100):
            x = random.randint(0, width)
            y = random.randint(0, height)
            size = random.randint(1, 3)
            
            # Twinkle effect
            twinkle = int(150 + 100 * math.sin(time_offset * 3 + i))
            star_color = colors["highlight"][:3] + (twinkle,)
            
            draw.ellipse([x-size, y-size, x+size, y+size], fill=star_color)
            
            # Add occasional shooting stars
            if i < 3:
                trail_length = 20 + int(10 * math.sin(time_offset + i))
                for j in range(trail_length):
                    offset = j * 3
                    trail_opacity = int(100 * (1 - j/trail_length))
                    trail_color = colors["highlight"][:3] + (trail_opacity,)
                    draw.point((x - offset, y + offset), fill=trail_color)
    
    elif style == "Bubbles":
        # Floating bubbles
        for y in range(height):
            ratio = y / height
            r = int((1-ratio) * color1[0] + ratio * color2[0])
            g = int((1-ratio) * color1[1] + ratio * color2[1])
            b = int((1-ratio) * color1[2] + ratio * color2[2])
            a = int((1-ratio) * color1[3] + ratio * color2[3])
            draw.line([(0, y), (width, y)], fill=(r, g, b, a))
        
        # Floating bubbles
        for i in range(30):
            x = int(width * 0.5 + 400 * math.sin(time_offset + i * 0.5))
            y = int(height * 0.5 + 300 * math.cos(time_offset * 1.2 + i))
            size = 30 + int(20 * math.sin(time_offset * 2 + i))
            
            # Bubble color with transparency
            bubble_opacity = int(80 + 40 * math.sin(time_offset + i))
            bubble_color = colors["accent"][:3] + (bubble_opacity,)
            
            draw.ellipse([x-size, y-size, x+size, y+size], 
                        outline=bubble_color, width=2)
            
            # Bubble highlight
            highlight_color = colors["highlight"][:3] + (150,)
            draw.ellipse([x-size//3, y-size//3, x, y], 
                        fill=highlight_color)
    
    elif style == "Geometric":
        # Geometric patterns
        for y in range(height):
            ratio = y / height
            r = int((1-ratio) * color1[0] + ratio * color2[0])
            g = int((1-ratio) * color1[1] + ratio * color2[1])
            b = int((1-ratio) * color1[2] + ratio * color2[2])
            a = int((1-ratio) * color1[3] + ratio * color2[3])
            draw.line([(0, y), (width, y)], fill=(r, g, b, a))
        
        # Geometric shapes
        for i in range(15):
            center_x = width * (0.2 + 0.6 * (i % 5) / 4)
            center_y = height * (0.2 + 0.6 * (i // 5) / 2)
            
            shape_size = 60 + int(30 * math.sin(time_offset + i))
            
            # Rotate shapes
            rotation = time_offset * 50 + i * 30
            
            # Draw different shapes
            if i % 3 == 0:
                # Triangle
                points = []
                for j in range(3):
                    angle = math.radians(rotation + j * 120)
                    x = center_x + shape_size * math.cos(angle)
                    y = center_y + shape_size * math.sin(angle)
                    points.append((x, y))
                draw.polygon(points, outline=colors["accent"], width=3)
            elif i % 3 == 1:
                # Square
                half = shape_size // 2
                draw.rectangle([center_x-half, center_y-half, 
                              center_x+half, center_y+half], 
                             outline=colors["accent"], width=3)
            else:
                # Hexagon
                points = []
                for j in range(6):
                    angle = math.radians(rotation + j * 60)
                    x = center_x + shape_size * math.cos(angle)
                    y = center_y + shape_size * math.sin(angle)
                    points.append((x, y))
                draw.polygon(points, outline=colors["accent"], width=3)
    
    elif style == "Waves":
        # Wave pattern
        for y in range(height):
            ratio = y / height
            wave = math.sin(y / 80 + time_offset) * 0.1
            ratio = max(0, min(1, ratio + wave))
            
            r = int((1-ratio) * color1[0] + ratio * color2[0])
            g = int((1-ratio) * color1[1] + ratio * color2[1])
            b = int((1-ratio) * color1[2] + ratio * color2[2])
            a = int((1-ratio) * color1[3] + ratio * color2[3])
            draw.line([(0, y), (width, y)], fill=(r, g, b, a))
        
        # Add wave lines
        for i in range(5):
            wave_y = height * (0.2 + 0.15 * i)
            amplitude = 20 + 10 * math.sin(time_offset + i)
            
            points = []
            for x in range(0, width, 10):
                y_pos = wave_y + amplitude * math.sin(x / 100 + time_offset)
                points.append((x, y_pos))
            
            if len(points) > 1:
                wave_color = colors["accent"][:3] + (150,)
                draw.line(points, fill=wave_color, width=2, joint="curve")
    
    elif style == "Particles":
        # Particle system
        for y in range(height):
            ratio = y / height
            r = int((1-ratio) * color1[0] + ratio * color2[0])
            g = int((1-ratio) * color1[1] + ratio * color2[1])
            b = int((1-ratio) * color1[2] + ratio * color2[2])
            a = int((1-ratio) * color1[3] + ratio * color2[3])
            draw.line([(0, y), (width, y)], fill=(r, g, b, a))
        
        # Particles
        for i in range(120):
            angle = time_offset * 2 + i * 0.1
            distance = 100 + 50 * math.sin(time_offset + i * 0.2)
            x = width * 0.5 + distance * math.cos(angle)
            y = height * 0.5 + distance * math.sin(angle * 1.5)
            
            size = 2 + int(3 * math.sin(time_offset * 3 + i))
            
            particle_opacity = int(180 + 70 * math.sin(time_offset * 4 + i))
            particle_color = colors["accent"][:3] + (particle_opacity,)
            
            draw.ellipse([x-size, y-size, x+size, y+size], 
                        fill=particle_color)
    
    return img

# ============================================================================
# TEXT ANIMATIONS
# ============================================================================
def draw_animation_text(draw, text_lines, font, x, y, line_height, animation_type, progress, colors):
    """Draw text with various animations."""
    
    if animation_type == "Typewriter":
        # Typewriter effect
        full_text = " ".join(text_lines)
        total_chars = len(full_text)
        visible_chars = int(total_chars * progress)
        visible_text = full_text[:visible_chars]
        
        # Build visible lines
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
        
        # Draw visible lines
        current_y = y
        for line in visible_lines:
            bbox = font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            draw.text(((1080 - line_width) // 2, current_y), 
                     line, font=font, fill=colors["text"])
            current_y += line_height
        
        # Blinking cursor
        if progress < 1.0 and int(time.time() * 2) % 2 == 0:
            if visible_lines:
                last_line = visible_lines[-1]
                bbox = font.getbbox(last_line)
                cursor_x = (1080 - bbox[2]) // 2 + bbox[2] + 8
                cursor_y = current_y - line_height + 15
                draw.line([(cursor_x, cursor_y), (cursor_x, cursor_y + line_height - 25)], 
                         fill=colors["accent"], width=4)
        
        return current_y
    
    elif animation_type == "Fade In":
        # Fade in animation
        current_y = y
        for line in text_lines:
            bbox = font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            
            # Calculate opacity for each line (staggered)
            line_progress = min(1.0, progress * 1.5 - (current_y - y) / (len(text_lines) * line_height) * 0.5)
            opacity = int(255 * line_progress)
            text_color = colors["text"][:3] + (opacity,)
            
            draw.text(((1080 - line_width) // 2, current_y), 
                     line, font=font, fill=text_color)
            current_y += line_height
        
        return current_y
    
    elif animation_type == "Slide Up":
        # Slide up animation
        current_y = y
        for line in text_lines:
            bbox = font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            
            # Slide from below
            slide_offset = (1 - progress) * 100
            draw_y = current_y - slide_offset
            
            draw.text(((1080 - line_width) // 2, draw_y), 
                     line, font=font, fill=colors["text"])
            current_y += line_height
        
        return current_y
    
    elif animation_type == "Zoom In":
        # Zoom in animation
        current_y = y
        for i, line in enumerate(text_lines):
            bbox = font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            
            # Zoom effect
            scale = 0.5 + progress * 0.5
            scaled_size = int(font.size * scale)
            
            # Create scaled font
            try:
                scaled_font = ImageFont.truetype("arial.ttf", scaled_size)
            except:
                scaled_font = font
            
            bbox_scaled = scaled_font.getbbox(line)
            line_width_scaled = bbox_scaled[2] - bbox_scaled[0]
            
            # Center position with scaling
            draw_x = (1080 - line_width_scaled) // 2
            draw_y = current_y - (line_height * (1 - scale)) / 2
            
            draw.text((draw_x, draw_y), line, font=scaled_font, fill=colors["text"])
            current_y += line_height
        
        return current_y
    
    elif animation_type == "Word by Word":
        # Word by word reveal
        full_text = " ".join(text_lines)
        words = full_text.split()
        visible_words = int(len(words) * progress)
        
        # Build visible text
        visible_text = " ".join(words[:visible_words])
        
        # Split into lines
        visible_lines = []
        current_line = ""
        
        for word in words[:visible_words]:
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
        
        # Draw visible lines
        current_y = y
        for line in visible_lines:
            bbox = font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            draw.text(((1080 - line_width) // 2, current_y), 
                     line, font=font, fill=colors["text"])
            current_y += line_height
        
        return current_y
    
    elif animation_type == "Glow Pulse":
        # Glowing text with pulse
        current_y = y
        
        # Pulse intensity
        pulse = 0.7 + 0.3 * math.sin(progress * 10)
        
        for line in text_lines:
            bbox = font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            
            # Draw glow effect
            glow_color = colors["highlight"][:3] + (int(100 * pulse),)
            
            # Multiple glow layers
            for offset in [(-2, -2), (2, 2), (-2, 2), (2, -2)]:
                draw.text(((1080 - line_width) // 2 + offset[0], 
                          current_y + offset[1]), 
                         line, font=font, fill=glow_color)
            
            # Main text
            draw.text(((1080 - line_width) // 2, current_y), 
                     line, font=font, fill=colors["text"])
            current_y += line_height
        
        return current_y
    
    else:
        # No animation (static)
        current_y = y
        for line in text_lines:
            bbox = font.getbbox(line)
            line_width = bbox[2] - bbox[0]
            draw.text(((1080 - line_width) // 2, current_y), 
                     line, font=font, fill=colors["text"])
            current_y += line_height
        
        return current_y

# ============================================================================
# IMAGE GENERATION WITH DECORATIONS
# ============================================================================
def create_image(size_name, color_name, text_source, book, chapter, verse, custom_text, hook, animation_type, bg_style):
    """Create the verse/quote image with decorations."""
    width, height = SIZES[size_name]
    colors = COLORS[color_name]
    
    # Background with decorations
    image = create_background(width, height, bg_style, colors)
    draw = ImageDraw.Draw(image)
    
    # Get text content based on source
    if text_source == "Bible Verse":
        verse_text = get_verse(book, chapter, verse)
        reference = f"{book} {chapter}:{verse}"
    else:
        verse_text = custom_text
        reference = "— Inspiration"
    
    # Calculate smart font size
    text_box_width = 900
    text_box_x = (width - text_box_width) // 2
    
    # Smart font sizing
    verse_font_size = 140
    verse_font = load_font_safe(verse_font_size)
    
    # Wrap text
    words = verse_text.split()
    verse_lines = []
    current_line = ""
    
    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = verse_font.getbbox(test_line)
        if bbox[2] - bbox[0] <= text_box_width - 60:
            current_line = test_line
        else:
            if current_line:
                verse_lines.append(current_line)
            current_line = word
    
    if current_line:
        verse_lines.append(current_line)
    
    # Reduce font size if too many lines
    while len(verse_lines) > 6 and verse_font_size > 80:
        verse_font_size -= 5
        verse_font = load_font_safe(verse_font_size)
        
        # Re-wrap
        verse_lines = []
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            bbox = verse_font.getbbox(test_line)
            if bbox[2] - bbox[0] <= text_box_width - 60:
                current_line = test_line
            else:
                if current_line:
                    verse_lines.append(current_line)
                current_line = word
        
        if current_line:
            verse_lines.append(current_line)
    
    # Calculate box dimensions
    verse_line_height = verse_font.getbbox("A")[3] - verse_font.getbbox("A")[1]
    verse_height = len(verse_lines) * verse_line_height * 1.4
    
    box_padding = 80
    box_height = verse_height + (box_padding * 2)
    box_y = (height - box_height) // 2
    
    # DRAW TRANSPARENT BLACK BOX WITH DECORATIONS
    box_color = (0, 0, 0, 120)  # More transparent black
    draw.rectangle([text_box_x, box_y, text_box_x + text_box_width, box_y + box_height], 
                  fill=box_color)
    
    # Add decorative corners
    corner_size = 40
    corner_color = colors["accent"][:3] + (180,)
    
    # Top-left corner
    draw.line([(text_box_x, box_y), (text_box_x + corner_size, box_y)], 
              fill=corner_color, width=4)
    draw.line([(text_box_x, box_y), (text_box_x, box_y + corner_size)], 
              fill=corner_color, width=4)
    
    # Top-right corner
    draw.line([(text_box_x + text_box_width - corner_size, box_y), 
               (text_box_x + text_box_width, box_y)], 
              fill=corner_color, width=4)
    draw.line([(text_box_x + text_box_width, box_y), 
               (text_box_x + text_box_width, box_y + corner_size)], 
              fill=corner_color, width=4)
    
    # Bottom-left corner
    draw.line([(text_box_x, box_y + box_height - corner_size), 
               (text_box_x, box_y + box_height)], 
              fill=corner_color, width=4)
    draw.line([(text_box_x, box_y + box_height), 
               (text_box_x + corner_size, box_y + box_height)], 
              fill=corner_color, width=4)
    
    # Bottom-right corner
    draw.line([(text_box_x + text_box_width - corner_size, box_y + box_height), 
               (text_box_x + text_box_width, box_y + box_height)], 
              fill=corner_color, width=4)
    draw.line([(text_box_x + text_box_width, box_y + box_height - corner_size), 
               (text_box_x + text_box_width, box_y + box_height)], 
              fill=corner_color, width=4)
    
    # Add floating decorations around box
    for i in range(8):
        angle = math.radians(i * 45)
        distance = 80
        deco_x = text_box_x + text_box_width // 2 + distance * math.cos(angle)
        deco_y = box_y + box_height // 2 + distance * math.sin(angle)
        
        # Different decoration types
        if i % 3 == 0:
            # Star
            star_size = 6
            draw.ellipse([deco_x-star_size, deco_y-star_size, 
                         deco_x+star_size, deco_y+star_size], 
                        fill=colors["highlight"])
        elif i % 3 == 1:
            # Small circle
            circle_size = 4
            draw.ellipse([deco_x-circle_size, deco_y-circle_size, 
                         deco_x+circle_size, deco_y+circle_size], 
                        fill=colors["accent"])
        else:
            # Tiny diamond
            diamond_size = 5
            points = [
                (deco_x, deco_y - diamond_size),
                (deco_x + diamond_size, deco_y),
                (deco_x, deco_y + diamond_size),
                (deco_x - diamond_size, deco_y)
            ]
            draw.polygon(points, fill=colors["secondary"])
    
    # Load fonts
    hook_font = load_font_safe(90, bold=True)
    ref_font = load_font_safe(52, bold=True)
    
    # Draw hook ABOVE the box
    if hook:
        bbox = hook_font.getbbox(hook)
        hook_width = bbox[2] - bbox[0]
        hook_x = (width - hook_width) // 2
        hook_y = box_y - 120
        
        # Hook with decorative underline
        draw.text((hook_x, hook_y), hook, font=hook_font, fill=colors["accent"])
        
        # Decorative underline
        underline_y = hook_y + bbox[3] + 10
        underline_length = hook_width + 40
        underline_x = hook_x - 20
        
        # Wavy underline
        for i in range(0, underline_length, 5):
            wave = 3 * math.sin(i / 20)
            draw.line([(underline_x + i, underline_y + wave), 
                      (underline_x + i + 2, underline_y + wave)], 
                     fill=colors["highlight"], width=2)
    
    # Draw verse with animation
    verse_y = box_y + box_padding
    verse_y = draw_animation_text(draw, verse_lines, verse_font, 
                                  text_box_x, verse_y, verse_line_height * 1.4, 
                                  animation_type, 1.0, colors)
    
    # Draw reference BELOW the box with decoration
    bbox = ref_font.getbbox(reference)
    ref_width = bbox[2] - bbox[0]
    ref_x = text_box_x + text_box_width - ref_width - 40
    ref_y = box_y + box_height + 70
    
    # Reference with decorative background
    ref_bg_color = colors["accent"][:3] + (180,)
    draw.rectangle([ref_x - 20, ref_y - 15, 
                    ref_x + ref_width + 20, ref_y + bbox[3] + 15], 
                  fill=ref_bg_color, outline=colors["highlight"], width=2)
    
    draw.text((ref_x, ref_y), reference, font=ref_font, fill=colors["text"])
    
    # Add "Still Mind" brand with decoration
    brand_font = load_font_safe(75, bold=True)
    brand_text = "Still Mind"
    brand_bbox = brand_font.getbbox(brand_text)
    brand_x = 70
    brand_y = 70
    
    # Brand with shadow
    shadow_color = (0, 0, 0, 150)
    draw.text((brand_x + 3, brand_y + 3), brand_text, font=brand_font, fill=shadow_color)
    draw.text((brand_x, brand_y), brand_text, font=brand_font, fill=colors["accent"])
    
    # Add decorative leaf next to brand
    leaf_points = [
        (brand_x + brand_bbox[2] + 20, brand_y + 15),
        (brand_x + brand_bbox[2] + 40, brand_y),
        (brand_x + brand_bbox[2] + 50, brand_y + 25),
        (brand_x + brand_bbox[2] + 40, brand_y + 40),
        (brand_x + brand_bbox[2] + 20, brand_y + 30)
    ]
    draw.polygon(leaf_points, fill=colors["accent"])
    
    return image, verse_text

# ============================================================================
# VIDEO GENERATION
# ============================================================================
def create_video(size_name, color_name, text_source, book, chapter, verse, custom_text, hook, animation_type, bg_style):
    """Create animated video."""
    width, height = SIZES[size_name]
    colors = COLORS[color_name]
    duration = 6
    fps = 12
    
    # Get text content
    if text_source == "Bible Verse":
        verse_text = get_verse(book, chapter, verse)
        reference = f"{book} {chapter}:{verse}"
    else:
        verse_text = custom_text
        reference = "— Inspiration"
    
    # Font setup
    verse_font_size = 140
    verse_font = load_font_safe(verse_font_size)
    
    # Wrap text for video
    words = verse_text.split()
    verse_lines = []
    current_line = ""
    
    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = verse_font.getbbox(test_line)
        if bbox[2] - bbox[0] <= 840:
            current_line = test_line
        else:
            if current_line:
                verse_lines.append(current_line)
            current_line = word
    
    if current_line:
        verse_lines.append(current_line)
    
    # Video frame generator
    def make_frame(t):
        # Create animated background
        img = create_background(width, height, bg_style, colors, t)
        draw = ImageDraw.Draw(img)
        
        # Calculate text box
        text_box_width = 900
        text_box_x = (width - text_box_width) // 2
        verse_line_height = verse_font.getbbox("A")[3] - verse_font.getbbox("A")[1]
        verse_height = len(verse_lines) * verse_line_height * 1.4
        
        box_padding = 80
        box_height = verse_height + (box_padding * 2)
        box_y = (height - box_height) // 2
        
        # Draw transparent box
        box_color = (0, 0, 0, 120)
        draw.rectangle([text_box_x, box_y, text_box_x + text_box_width, box_y + box_height], 
                      fill=box_color)
        
        # Draw hook (appears early)
        if hook and t > 0.5:
            hook_font = load_font_safe(90, bold=True)
            bbox = hook_font.getbbox(hook)
            hook_width = bbox[2] - bbox[0]
            hook_x = (width - hook_width) // 2
            hook_y = box_y - 120
            
            # Hook fade in
            hook_opacity = min(1.0, (t - 0.5) / 0.3)
            hook_color = colors["accent"][:3] + (int(255 * hook_opacity),)
            draw.text((hook_x, hook_y), hook, font=hook_font, fill=hook_color)
        
        # Draw verse with animation
        verse_y = box_y + box_padding
        
        # Calculate animation progress
        if animation_type == "None":
            verse_progress = 1.0
        else:
            verse_progress = min(1.0, t / (duration * 0.7))
        
        verse_y = draw_animation_text(draw, verse_lines, verse_font, 
                                      text_box_x, verse_y, verse_line_height * 1.4, 
                                      animation_type, verse_progress, colors)
        
        # Draw reference (appears late)
        if t > duration * 0.7:
            ref_font = load_font_safe(52, bold=True)
            bbox = ref_font.getbbox(reference)
            ref_width = bbox[2] - bbox[0]
            ref_x = text_box_x + text_box_width - ref_width - 40
            ref_y = box_y + box_height + 70
            
            # Reference fade in
            ref_opacity = min(1.0, (t - duration * 0.7) / 0.3)
            ref_bg_color = colors["accent"][:3] + (int(180 * ref_opacity),)
            draw.rectangle([ref_x - 20, ref_y - 15, 
                            ref_x + ref_width + 20, ref_y + bbox[3] + 15], 
                          fill=ref_bg_color)
            
            draw.text((ref_x, ref_y), reference, font=ref_font, fill=colors["text"])
        
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
st.title("✨ Still Mind Studio")

# Sidebar
with st.sidebar:
    st.header("🎨 Design")
    size = st.selectbox("Layout", list(SIZES.keys()))
    color = st.selectbox("Color Theme", list(COLORS.keys()))
    bg_style = st.selectbox("Background Style", BACKGROUNDS)
    
    st.header("📝 Content Type")
    text_source = st.radio("Text Source", ["Bible Verse", "Custom Quote"])
    
    if text_source == "Bible Verse":
        book = st.selectbox("Book", ["Psalm", "Matthew", "John", "Romans", 
                                    "Ephesians", "Philippians", "James", 
                                    "Proverbs", "Isaiah", "Genesis"])
        col1, col2 = st.columns(2)
        with col1:
            chapter = st.number_input("Chapter", 1, 150, 46)
        with col2:
            verse_num = st.number_input("Verse", 1, 176, 1)
        custom_text = ""
    else:
        book = "Custom"
        chapter = 1
        verse_num = 1
        custom_text = st.text_area("Your Quote", 
                                   "Peace begins with a smile. Travel light, live light, spread the light.", 
                                   height=100)
    
    hook = st.text_input("Hook / Title", "Find Your Inner Peace")
    
    st.header("🎬 Animation")
    animation_type = st.selectbox("Text Animation", ANIMATIONS)

# Main area
col1, col2 = st.columns([2, 1])

with col1:
    # Generate preview
    image, display_text = create_image(size, color, text_source, book, chapter, verse_num, custom_text, hook, animation_type, bg_style)
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
            with st.spinner("Creating video..."):
                video_data = create_video(size, color, text_source, book, chapter, verse_num, custom_text, hook, animation_type, bg_style)
                
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
    
    if text_source == "Bible Verse":
        reference = f"{book} {chapter}:{verse_num}"
    else:
        reference = "Daily Inspiration"
    
    # Smart hashtags
    if text_source == "Bible Verse":
        book_hashtags = {
            "Psalm": "#Psalms #Wisdom #Worship",
            "Matthew": "#Gospel #Jesus #Teachings",
            "John": "#Gospel #Love #EternalLife",
            "Romans": "#Faith #Grace #Salvation",
            "Ephesians": "#Church #Unity #Blessings",
            "Philippians": "#Joy #Contentment #Hope",
            "James": "#FaithWorks #Wisdom #PracticalFaith",
            "Proverbs": "#Wisdom #Proverbs #LifeLessons",
            "Isaiah": "#Prophet #Hope #Salvation",
            "Genesis": "#Beginnings #Creation #Faith"
        }
        hashtags = book_hashtags.get(book, "#BibleVerse #Scripture")
    else:
        hashtags = "#Quote #Inspiration #Mindfulness #DailyMotivation"
    
    caption = f"""{hook}

"{display_text[:200]}{'...' if len(display_text) > 200 else ''}"

📖 {reference}

{hashtags}
#StillMind #Mindful"""
    
    st.text_area("Social Media Caption", caption, height=200)
    
    if st.button("📋 Copy Caption", use_container_width=True):
        st.code(caption)
        st.success("Ready to paste!")
    
    st.divider()
    
    # Design info
    st.caption(f"**Theme:** {color}")
    st.caption(f"**Layout:** {size}")
    st.caption(f"**Background:** {bg_style}")
    st.caption(f"**Animation:** {animation_type}")
    
    if text_source == "Bible Verse":
        st.caption(f"**Verse:** {reference}")
    else:
        st.caption("**Source:** Custom Quote")

# Auto-cleanup
for file in os.listdir("."):
    if file.startswith("video_") and file.endswith(".mp4"):
        try:
            if time.time() - os.path.getctime(file) > 300:
                os.remove(file)
        except:
            pass

# Footer
st.divider()
st.caption("Still Mind Studio | Transparent Designs | Creative Decorations | Multiple Animations")