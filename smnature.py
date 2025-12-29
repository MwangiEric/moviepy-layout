import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io, os, math, numpy as np
from moviepy.editor import VideoClip
import random

# ============================================================================
# ANIMATED FLAT DESIGN - EMOTIONAL CONNECTION
# ============================================================================
st.set_page_config(page_title="Emotional Flat Animation", layout="wide")

# Simple palette that creates emotional responses
EMOTIONAL_COLORS = {
    "Calm": {
        "bg": (230, 240, 245, 255),  # Soft blue
        "primary": (76, 175, 80, 255),  # Peaceful green
        "accent": (100, 150, 200, 255),  # Trust blue
        "text": (50, 50, 50, 255)  # Dark for readability
    },
    "Hope": {
        "bg": (255, 250, 230, 255),  # Warm cream
        "primary": (255, 193, 7, 255),  # Golden yellow
        "accent": (255, 152, 0, 255),  # Sunrise orange
        "text": (60, 40, 20, 255)
    },
    "Strength": {
        "bg": (25, 35, 45, 255),  # Deep navy
        "primary": (244, 67, 54, 255),  # Bold red
        "accent": (255, 235, 59, 255),  # Bright yellow
        "text": (255, 255, 255, 255)  # White for contrast
    }
}

# ============================================================================
# EMOTIONAL ANIMATIONS PEOPLE RELATE TO
# ============================================================================

def animate_breathing_circle(draw, x, y, t, colors, emotion="Calm"):
    """A breathing circle that mimics calm breathing patterns."""
    if emotion == "Calm":
        # Slow, deep breaths
        breath_rate = 0.5
        min_size = 40
        max_size = 60
    elif emotion == "Anxious":
        # Quick, shallow breaths
        breath_rate = 3.0
        min_size = 30
        max_size = 50
    else:
        # Normal breathing
        breath_rate = 1.0
        min_size = 35
        max_size = 55
    
    # Breathing pattern
    breath = math.sin(t * breath_rate * 2 * math.pi) * 0.5 + 0.5
    size = min_size + (max_size - min_size) * breath
    
    # Draw breathing circle
    draw.ellipse([x-size, y-size, x+size, y+size], 
                outline=colors["primary"], width=3)
    
    # Pulsing center
    pulse_size = 8 + 4 * math.sin(t * 4)
    draw.ellipse([x-pulse_size, y-pulse_size, x+pulse_size, y+pulse_size], 
                fill=colors["primary"])

def animate_heartbeat(draw, x, y, t, colors):
    """Simple heartbeat animation."""
    # Heart shape (simplified flat design)
    beat = abs(math.sin(t * 5)) * 10  # Heartbeat effect
    size = 30 + beat
    
    # Flat heart shape
    points = [
        (x, y - size),
        (x + size, y),
        (x, y + size),
        (x - size, y)
    ]
    
    # Animate color with heartbeat
    if int(t * 5) % 2 == 0:  # Every other beat
        heart_color = colors["primary"]
    else:
        # Slightly darker for pulse effect
        heart_color = tuple(max(0, c-40) for c in colors["primary"][:3]) + (255,)
    
    draw.polygon(points, fill=heart_color)

def animate_flowing_line(draw, start_x, start_y, end_x, end_y, t, colors):
    """A line that flows like a river or breath."""
    # Draw flowing line segment by segment
    segments = 10
    segment_length = math.sqrt((end_x-start_x)**2 + (end_y-start_y)**2) / segments
    
    for i in range(segments):
        # Offset each segment for flowing effect
        flow_offset = math.sin(t * 2 + i) * 5
        
        seg_start_x = start_x + (end_x - start_x) * i / segments
        seg_start_y = start_y + (end_y - start_y) * i / segments + flow_offset
        seg_end_x = start_x + (end_x - start_x) * (i+1) / segments
        seg_end_y = start_y + (end_y - start_y) * (i+1) / segments + flow_offset
        
        # Alpha decreases towards end
        alpha = int(255 * (1 - i/segments))
        line_color = colors["primary"][:3] + (alpha,)
        
        draw.line([(seg_start_x, seg_start_y), (seg_end_x, seg_end_y)], 
                 fill=line_color, width=3)

def animate_growing_tree(draw, x, y, t, colors):
    """A tree that grows from the ground up."""
    growth_progress = min(1.0, t / 3)  # 3 seconds to fully grow
    
    # Trunk grows first
    trunk_height = 100 * growth_progress
    if growth_progress > 0:
        # Trunk
        draw.rectangle([x-8, y, x+8, y-trunk_height], 
                      fill=colors["accent"])
        
        # Leaves appear after trunk
        leaves_progress = max(0, (growth_progress - 0.3) / 0.7)
        if leaves_progress > 0:
            leaf_size = 30 * leaves_progress
            
            # Three main leaf clusters
            draw.ellipse([x-leaf_size, y-trunk_height-leaf_size, 
                         x+leaf_size, y-trunk_height+leaf_size], 
                        fill=colors["primary"])
            
            draw.ellipse([x-20-leaf_size, y-trunk_height+10-leaf_size, 
                         x-20+leaf_size, y-trunk_height+10+leaf_size], 
                        fill=colors["primary"])
            
            draw.ellipse([x+20-leaf_size, y-trunk_height+10-leaf_size, 
                         x+20+leaf_size, y-trunk_height+10+leaf_size], 
                        fill=colors["primary"])

def animate_rising_sun(draw, width, height, t, colors):
    """Sunrise animation symbolizing hope."""
    rise_progress = min(1.0, t / 4)  # 4 seconds to rise
    
    sun_y = height * 0.8 - (rise_progress * height * 0.5)
    sun_size = 60
    
    # Sun
    draw.ellipse([width//2-sun_size, sun_y-sun_size, 
                 width//2+sun_size, sun_y+sun_size], 
                fill=colors["primary"])
    
    # Sun rays (appear as sun rises)
    if rise_progress > 0.5:
        ray_count = 8
        ray_length = 40
        
        for i in range(ray_count):
            angle = (i / ray_count) * 2 * math.pi
            start_x = width//2 + (sun_size+5) * math.cos(angle)
            start_y = sun_y + (sun_size+5) * math.sin(angle)
            end_x = start_x + ray_length * math.cos(angle) * rise_progress
            end_y = start_y + ray_length * math.sin(angle) * rise_progress
            
            draw.line([(start_x, start_y), (end_x, end_y)], 
                     fill=colors["primary"], width=3)

def animate_emotional_text(draw, text, x, y, t, font, colors, emotion="Calm"):
    """Text animation that matches emotional tone."""
    words = text.split()
    
    if emotion == "Calm":
        # Words appear slowly, one by one
        word_delay = 0.3
        words_to_show = min(len(words), int(t / word_delay))
        visible_text = " ".join(words[:words_to_show])
        
    elif emotion == "Hope":
        # Words appear with a gentle fade in
        word_progress = min(1.0, t / 2)
        visible_chars = int(len(text) * word_progress)
        visible_text = text[:visible_chars]
        
    elif emotion == "Strength":
        # Words appear all at once but with impact
        if t > 0.5:
            visible_text = text
            # Add a slight shake effect
            shake_x = x + random.randint(-2, 2)
            shake_y = y + random.randint(-1, 1)
        else:
            visible_text = ""
            shake_x, shake_y = x, y
        x, y = shake_x, shake_y
    
    else:
        # Default typewriter
        visible_chars = int(len(text) * min(1.0, t / 3))
        visible_text = text[:visible_chars]
    
    # Draw text
    draw.text((x, y), visible_text, font=font, fill=colors["text"])

def create_emotional_scene(width, height, emotion, verse, t, is_video=False):
    """Create an emotionally resonant animated scene."""
    colors = EMOTIONAL_COLORS[emotion]
    
    # Create image
    img = Image.new("RGBA", (width, height), colors["bg"])
    draw = ImageDraw.Draw(img)
    
    # Font
    try:
        font = ImageFont.truetype("arial.ttf", 48)
    except:
        font = ImageFont.load_default(48)
    
    # Different animations based on emotion
    if emotion == "Calm":
        # Breathing animation in center
        animate_breathing_circle(draw, width//2, height//2, t, colors)
        
        # Flowing lines around
        animate_flowing_line(draw, width//2-100, height//2-50, 
                           width//2+100, height//2-50, t, colors)
        
        # Calm text animation
        text_x = width//2 - len(verse)*10  # Rough centering
        text_y = height//2 + 100
        animate_emotional_text(draw, verse, text_x, text_y, t, font, colors, "Calm")
    
    elif emotion == "Hope":
        # Sunrise animation
        animate_rising_sun(draw, width, height, t, colors)
        
        # Growing tree
        animate_growing_tree(draw, width//2, height-50, t, colors)
        
        # Hopeful text animation
        text_x = 100
        text_y = 100
        animate_emotional_text(draw, verse, text_x, text_y, t, font, colors, "Hope")
    
    elif emotion == "Strength":
        # Heartbeat animation
        animate_heartbeat(draw, width//2, height//2, t, colors)
        
        # Strong, bold lines
        for i in range(3):
            line_y = height//2 + 80 + i*40
            line_wave = math.sin(t*3 + i) * 20
            draw.line([(100, line_y + line_wave), (width-100, line_y + line_wave)], 
                     fill=colors["primary"], width=5)
        
        # Strong text animation
        text_x = 100
        text_y = height - 150
        animate_emotional_text(draw, verse, text_x, text_y, t, font, colors, "Strength")
    
    return img

# ============================================================================
# STREAMLIT UI
# ============================================================================
st.title("💓 Emotional Flat Animation Studio")
st.markdown("### Animations that create emotional connections")

# Emotion selection
emotion = st.selectbox("Choose Emotional Tone", ["Calm", "Hope", "Strength"])

# Verse input
verse = st.text_area("Inspirational Verse", 
                    "Be still, and know that I am God.")

# Time control
time_slider = st.slider("Animation Time", 0.0, 5.0, 0.0, 0.1)

# Create and display
W, H = 1080, 1080
scene = create_emotional_scene(W, H, emotion, verse, time_slider)
st.image(scene, use_container_width=True)

# Video generation
if st.button("🎬 Create Emotional Animation (5s)"):
    def make_frame(t):
        return np.array(create_emotional_scene(W, H, emotion, verse, t, True).convert("RGB"))
    
    clip = VideoClip(make_frame, duration=5).set_fps(24)
    clip.write_videofile("emotional_animation.mp4", codec="libx264", logger=None)
    st.video("emotional_animation.mp4")