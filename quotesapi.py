import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io, os, requests, math, time, json
import numpy as np
from moviepy.editor import VideoClip, vfx
from groq import Groq
import random

# ============================================================================
# STREAMLIT SETUP
# ============================================================================
st.set_page_config(page_title="Wisdom Studio", page_icon="🧠", layout="wide")

# ============================================================================
# API CONFIGURATION
# ============================================================================
# Get Groq API key from Streamlit secrets or environment
try:
    GROQ_API_KEY = st.secrets["groq_key"]
except:
    GROQ_API_KEY = os.getenv("groq_key", "")
    if not GROQ_API_KEY:
        st.error("Please set GROQ_API_KEY in Streamlit secrets or environment")
        st.stop()

# Initialize Groq client
client = Groq(api_key=GROQ_API_KEY)

# ============================================================================
# THEME CONFIGURATION
# ============================================================================
THEMES = {
    "Philosophy": {
        "bg": [(40, 20, 40, 255), (60, 30, 60, 255)],  # Purple tones
        "accent": (200, 150, 255, 255),  # Light purple
        "text": (255, 255, 255, 255)
    },
    "Stoicism": {
        "bg": [(30, 40, 50, 255), (50, 60, 80, 255)],  # Steel blue
        "accent": (200, 200, 200, 255),  # Silver
        "text": (255, 255, 255, 255)
    },
    "Psychology": {
        "bg": [(50, 40, 30, 255), (80, 60, 40, 255)],  # Earth tones
        "accent": (255, 200, 150, 255),  # Peach
        "text": (255, 255, 255, 255)
    },
    "Wisdom": {
        "bg": [(20, 40, 30, 255), (40, 80, 60, 255)],  # Sage green
        "accent": (180, 220, 180, 255),  # Light green
        "text": (255, 255, 255, 255)
    }
}

SIZES = {
    "TikTok (9:16)": (1080, 1920),
    "Instagram (1:1)": (1080, 1080),
    "Story (9:16)": (1080, 1920)
}

BACKGROUND_STYLES = ["Minimal", "Abstract", "Geometric", "Nature", "Textured"]

# ============================================================================
# GROQ AI FUNCTIONS
# ============================================================================
def get_ai_quote(topic, category=None):
    """Get a relevant quote from Groq AI based on topic."""
    
    # Build the prompt based on category
    if category:
        prompt = f"""For the topic "{topic}", provide a relevant {category} quote that is insightful and meaningful.
        
        Return ONLY a JSON object with this exact structure:
        {{
            "quote": "The actual quote text here",
            "author": "Author name",
            "category": "{category}",
            "explanation": "A brief 2-3 sentence explanation of why this quote is relevant to the topic",
            "keywords": ["keyword1", "keyword2", "keyword3"],
            "style_suggestion": "Minimal, Abstract, Geometric, Nature, or Textured"
        }}
        
        Make the quote authentic to the {category} tradition."""
    else:
        prompt = f"""For the topic "{topic}", provide the most insightful quote you can find from philosophy, stoicism, or psychology.
        
        Choose the category that best fits the topic.
        
        Return ONLY a JSON object with this exact structure:
        {{
            "quote": "The actual quote text here",
            "author": "Author name",
            "category": "Philosophy, Stoicism, or Psychology",
            "explanation": "A brief 2-3 sentence explanation of why this quote is relevant to the topic",
            "keywords": ["keyword1", "keyword2", "keyword3"],
            "style_suggestion": "Minimal, Abstract, Geometric, Nature, or Textured"
        }}
        
        Make the quote profound and thought-provoking."""
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a wisdom curator who finds the most insightful quotes from philosophy, stoicism, and psychology."},
                {"role": "user", "content": prompt}
            ],
            model="mixtral-8x7b-32768",
            temperature=0.7,
            max_tokens=500
        )
        
        # Parse JSON from response
        result_text = response.choices[0].message.content.strip()
        
        # Clean up the response to ensure valid JSON
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        
        result = json.loads(result_text)
        return result
        
    except Exception as e:
        st.error(f"AI Error: {str(e)}")
        # Return a fallback quote
        return {
            "quote": "The unexamined life is not worth living.",
            "author": "Socrates",
            "category": "Philosophy",
            "explanation": "This quote reminds us that self-reflection and conscious living are essential to finding meaning.",
            "keywords": ["wisdom", "reflection", "meaning"],
            "style_suggestion": "Minimal"
        }

def generate_social_post(quote_data):
    """Generate a TikTok/Instagram social media post."""
    
    prompt = f"""Create an engaging social media post for this {quote_data['category']} quote:
    
    "{quote_data['quote']}"
    - {quote_data['author']}
    
    The post should include:
    1. A catchy hook/question
    2. The quote
    3. A brief insight (1 sentence)
    4. 3-5 relevant hashtags
    
    Format it nicely for TikTok/Instagram."""
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You create viral social media content for wisdom quotes."},
                {"role": "user", "content": prompt}
            ],
            model="mixtral-8x7b-32768",
            temperature=0.8,
            max_tokens=300
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        # Fallback social post
        return f"""💭 {quote_data['category']} Wisdom

"{quote_data['quote'][:100]}..."

📚 {quote_data['author']}

#Wisdom #Quote #{quote_data['category']} #Mindfulness #Growth"""

# ============================================================================
# FONT LOADING
# ============================================================================
def load_font_safe(size, bold=False):
    """Load font with fallbacks."""
    font_paths = []
    
    if bold:
        font_paths.extend([
            "arialbd.ttf", "Arial-Bold.ttf", "Helvetica-Bold.ttf",
            "DejaVuSans-Bold.ttf"
        ])
    else:
        font_paths.extend([
            "arial.ttf", "Arial.ttf", "Helvetica.ttf",
            "DejaVuSans.ttf"
        ])
    
    for font_path in font_paths:
        try:
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, size)
        except:
            continue
    
    return ImageFont.load_default(size)

# ============================================================================
# SMART TEXT WRAPPING
# ============================================================================
def wrap_text(text, font, max_width):
    """Wrap text to fit within max width."""
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

def calculate_font_size(text, target_size, min_size, max_width):
    """Find optimal font size for text."""
    for size in range(target_size, min_size - 1, -2):
        font = load_font_safe(size)
        lines = wrap_text(text, font, max_width)
        
        # Check if any line is too long (safety check)
        ok = True
        for line in lines:
            bbox = font.getbbox(line)
            if bbox[2] - bbox[0] > max_width + 10:
                ok = False
                break
        
        if ok:
            return size, lines, font
    
    return min_size, [text], load_font_safe(min_size)

# ============================================================================
# BACKGROUND GENERATORS (AI-ENHANCED)
# ============================================================================
def create_background(width, height, style, colors, keywords=None, time_offset=0):
    """Create background based on style and AI keywords."""
    img = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(img)
    
    color1, color2 = colors["bg"]
    
    if style == "Minimal":
        # Clean gradient with subtle texture
        for y in range(height):
            ratio = y / height
            # Add gentle wave
            wave = math.sin(y / 200 + time_offset) * 0.05
            ratio = max(0, min(1, ratio + wave))
            
            r = int((1-ratio) * color1[0] + ratio * color2[0])
            g = int((1-ratio) * color1[1] + ratio * color2[1])
            b = int((1-ratio) * color1[2] + ratio * color2[2])
            a = int((1-ratio) * color1[3] + ratio * color2[3])
            draw.line([(0, y), (width, y)], fill=(r, g, b, a))
    
    elif style == "Abstract":
        # Abstract shapes based on keywords
        for i in range(12):
            offset = int(time_offset * 60) % 800
            size = 80 + int(40 * math.sin(time_offset + i))
            x = int(width * (0.1 + 0.07 * i) + offset % 500)
            y = int(height * 0.5 + 100 * math.cos(time_offset * 1.3 + i))
            
            # Color variation based on keywords
            if keywords and "thought" in [k.lower() for k in keywords]:
                # Thinking/mind theme - circles
                draw.ellipse([x, y, x+size, y+size], 
                            outline=colors["accent"], width=3)
            elif keywords and "nature" in [k.lower() for k in keywords]:
                # Nature theme - organic shapes
                draw.ellipse([x, y, x+size*0.8, y+size], 
                            outline=colors["accent"], width=3)
            else:
                # Default abstract
                draw.rectangle([x, y, x+size, y+size], 
                             outline=colors["accent"], width=2)
    
    elif style == "Geometric":
        # Geometric patterns
        for i in range(20):
            x = int(width * (0.05 + 0.045 * i) + time_offset * 20 % 400)
            y = int(height * 0.3 + 60 * math.sin(time_offset * 2 + i))
            
            # Different shapes
            shape_type = i % 4
            if shape_type == 0:
                # Circle
                draw.ellipse([x-30, y-30, x+30, y+30], 
                            outline=colors["accent"], width=2)
            elif shape_type == 1:
                # Square
                draw.rectangle([x-25, y-25, x+25, y+25], 
                             outline=colors["accent"], width=2)
            elif shape_type == 2:
                # Triangle
                draw.polygon([(x, y-30), (x-26, y+15), (x+26, y+15)], 
                            outline=colors["accent"], width=2)
            else:
                # Diamond
                draw.polygon([(x, y-25), (x+25, y), (x, y+25), (x-25, y)], 
                            outline=colors["accent"], width=2)
    
    elif style == "Nature":
        # Nature-inspired background
        for i in range(15):
            x = int(width * (0.1 + 0.06 * i) + time_offset * 15 % 300)
            y = int(height * 0.6 + 80 * math.cos(time_offset + i))
            
            # Draw leaf/plant shapes
            for j in range(3):
                leaf_x = x + j * 15
                leaf_y = y + j * 10
                draw.ellipse([leaf_x-20, leaf_y-10, leaf_x+20, leaf_y+10], 
                            outline=colors["accent"], width=2)
    
    elif style == "Textured":
        # Textured background with dots
        dot_count = 200
        for _ in range(dot_count):
            x = random.randint(0, width)
            y = random.randint(0, height)
            size = random.randint(1, 4)
            opacity = random.randint(50, 150)
            dot_color = colors["accent"][:3] + (opacity,)
            draw.ellipse([x-size, y-size, x+size, y+size], fill=dot_color)
        
        # Add gradient overlay
        for y in range(height):
            ratio = y / height
            r = int((1-ratio) * color1[0] + ratio * color2[0])
            g = int((1-ratio) * color1[1] + ratio * color2[1])
            b = int((1-ratio) * color1[2] + ratio * color2[2])
            a = int((1-ratio) * color1[3] * 0.3 + ratio * color2[3] * 0.3)
            draw.line([(0, y), (width, y)], fill=(r, g, b, a))
    
    return img

# ============================================================================
# IMAGE GENERATION
# ============================================================================
def create_quote_image(size_name, theme_name, quote_data, bg_style):
    """Create image with quote and explanation."""
    width, height = SIZES[size_name]
    colors = THEMES[theme_name]
    
    # Use AI's style suggestion if available
    if "style_suggestion" in quote_data and quote_data["style_suggestion"] in BACKGROUND_STYLES:
        bg_style = quote_data["style_suggestion"]
    
    # Create background
    keywords = quote_data.get("keywords", [])
    image = create_background(width, height, bg_style, colors, keywords)
    draw = ImageDraw.Draw(image)
    
    # Text box dimensions
    text_box_width = 900
    text_box_x = (width - text_box_width) // 2
    
    # Load fonts with larger sizes
    quote_font_size, quote_lines, quote_font = calculate_font_size(
        f'"{quote_data["quote"]}"',
        target_size=140,
        min_size=70,
        max_width=text_box_width - 60
    )
    
    author_font = load_font_safe(48, bold=True)
    explanation_font = load_font_safe(36)
    category_font = load_font_safe(60, bold=True)
    
    # Calculate heights
    quote_line_height = quote_font.getbbox("A")[3] - quote_font.getbbox("A")[1]
    quote_height = len(quote_lines) * quote_line_height * 1.4
    
    # Add space for explanation
    explanation_text = quote_data["explanation"]
    explanation_lines = wrap_text(explanation_text, explanation_font, text_box_width - 40)
    explanation_line_height = explanation_font.getbbox("A")[3] - explanation_font.getbbox("A")[1]
    explanation_height = len(explanation_lines) * explanation_line_height * 1.3
    
    # Total content height
    total_content_height = quote_height + explanation_height + 140
    
    # Position elements
    box_padding = 80
    box_height = total_content_height + (box_padding * 2)
    box_y = (height - box_height) // 2
    
    # Draw semi-transparent box
    box_color = (0, 0, 0, 160)
    draw.rectangle([text_box_x, box_y, text_box_x + text_box_width, box_y + box_height], 
                  fill=box_color)
    
    # Draw category at top
    category_text = quote_data["category"]
    bbox = category_font.getbbox(category_text)
    cat_width = bbox[2] - bbox[0]
    cat_x = (width - cat_width) // 2
    cat_y = box_y - 80
    
    draw.text((cat_x, cat_y), category_text, font=category_font, fill=colors["accent"])
    
    # Draw quote
    current_y = box_y + box_padding
    for line in quote_lines:
        bbox = quote_font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        draw.text(((width - line_width) // 2, current_y), 
                 line, font=quote_font, fill=colors["text"])
        current_y += quote_line_height * 1.4
    
    # Draw author
    author_text = f"- {quote_data['author']}"
    bbox = author_font.getbbox(author_text)
    author_width = bbox[2] - bbox[0]
    author_x = (width - author_width) // 2
    draw.text((author_x, current_y + 40), author_text, font=author_font, fill=colors["accent"])
    
    current_y += 100
    
    # Draw explanation
    for line in explanation_lines:
        bbox = explanation_font.getbbox(line)
        line_width = bbox[2] - bbox[0]
        draw.text(((width - line_width) // 2, current_y), 
                 line, font=explanation_font, fill=(220, 220, 220, 255))
        current_y += explanation_line_height * 1.3
    
    # Add watermark
    watermark_font = load_font_safe(40)
    draw.text((width - 250, height - 60), "Wisdom Studio", font=watermark_font, fill=(255, 255, 255, 180))
    
    return image

# ============================================================================
# VIDEO GENERATION
# ============================================================================
def create_quote_video(size_name, theme_name, quote_data, bg_style):
    """Create animated video with quote."""
    width, height = SIZES[size_name]
    colors = THEMES[theme_name]
    duration = 8  # Longer for quotes
    fps = 24
    
    # Video frame generator
    def make_frame(t):
        # Animate background
        img = create_background(width, height, bg_style, colors, 
                               quote_data.get("keywords", []), t)
        draw = ImageDraw.Draw(img)
        
        # Text box dimensions
        text_box_width = 900
        text_box_x = (width - text_box_width) // 2
        
        # Calculate font sizes
        quote_font_size, quote_lines, quote_font = calculate_font_size(
            f'"{quote_data["quote"]}"',
            target_size=140,
            min_size=70,
            max_width=text_box_width - 60
        )
        
        author_font = load_font_safe(48, bold=True)
        category_font = load_font_safe(60, bold=True)
        
        # Animate quote reveal (typewriter effect)
        quote_line_height = quote_font.getbbox("A")[3] - quote_font.getbbox("A")[1]
        
        # Calculate box height
        quote_height = len(quote_lines) * quote_line_height * 1.4
        box_padding = 80
        box_height = quote_height + (box_padding * 2) + 100
        box_y = (height - box_height) // 2
        
        # Draw semi-transparent box
        box_opacity = int(160 * min(1.0, t * 2))
        box_color = (0, 0, 0, box_opacity)
        draw.rectangle([text_box_x, box_y, text_box_x + text_box_width, box_y + box_height], 
                      fill=box_color)
        
        # Fade in category
        if t > 0.5:
            category_text = quote_data["category"]
            bbox = category_font.getbbox(category_text)
            cat_width = bbox[2] - bbox[0]
            cat_x = (width - cat_width) // 2
            cat_y = box_y - 80
            
            cat_opacity = int(255 * min(1.0, (t - 0.5) / 0.3))
            cat_color = colors["accent"][:3] + (cat_opacity,)
            draw.text((cat_x, cat_y), category_text, font=category_font, fill=cat_color)
        
        # Typewriter effect for quote
        current_y = box_y + box_padding
        full_quote = " ".join(quote_lines)
        total_chars = len(full_quote)
        reveal_chars = int(total_chars * min(1.0, (t - 0.8) / 3.0))
        
        if reveal_chars > 0:
            revealed_text = full_quote[:reveal_chars]
            # Split revealed text into lines
            words = revealed_text.split()
            revealed_lines = []
            current_line = ""
            
            for word in words:
                test_line = f"{current_line} {word}".strip()
                bbox = quote_font.getbbox(test_line)
                if bbox[2] - bbox[0] <= text_box_width - 60:
                    current_line = test_line
                else:
                    if current_line:
                        revealed_lines.append(current_line)
                    current_line = word
            
            if current_line:
                revealed_lines.append(current_line)
            
            # Draw revealed lines
            for line in revealed_lines:
                bbox = quote_font.getbbox(line)
                line_width = bbox[2] - bbox[0]
                draw.text(((width - line_width) // 2, current_y), 
                         line, font=quote_font, fill=colors["text"])
                current_y += quote_line_height * 1.4
            
            # Draw blinking cursor
            if reveal_chars < total_chars:
                if int(t * 3) % 2 == 0:
                    if revealed_lines:
                        last_line = revealed_lines[-1]
                        bbox = quote_font.getbbox(last_line)
                        cursor_x = (width - bbox[2]) // 2 + bbox[2] + 10
                        cursor_y = current_y - quote_line_height + 20
                        draw.line([(cursor_x, cursor_y), (cursor_x, cursor_y + quote_line_height - 40)], 
                                 fill=colors["accent"], width=4)
        
        # Fade in author at the end
        if t > duration * 0.7:
            author_text = f"- {quote_data['author']}"
            bbox = author_font.getbbox(author_text)
            author_width = bbox[2] - bbox[0]
            author_x = (width - author_width) // 2
            author_y = current_y + 40
            
            author_opacity = int(255 * min(1.0, (t - duration * 0.7) / 0.5))
            author_color = colors["accent"][:3] + (author_opacity,)
            draw.text((author_x, author_y), author_text, font=author_font, fill=author_color)
        
        return np.array(img.convert("RGB"))
    
    # Create and save video
    video = VideoClip(make_frame, duration=duration)
    video = video.set_fps(fps)
    
    temp_file = f"quote_video_{int(time.time())}.mp4"
    video.write_videofile(temp_file, fps=fps, codec="libx264", verbose=False, logger=None)
    
    with open(temp_file, "rb") as f:
        video_bytes = f.read()
    
    os.remove(temp_file)
    return video_bytes

# ============================================================================
# STREAMLIT UI
# ============================================================================
st.title("🧠 Wisdom Studio")
st.markdown("### AI-powered quotes from philosophy, stoicism & psychology")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Category selection
    category = st.selectbox(
        "Quote Category",
        ["Auto-select (AI chooses best)", "Philosophy", "Stoicism", "Psychology", "Wisdom"]
    )
    
    # Topic input
    topic = st.text_area(
        "What's on your mind?",
        placeholder="e.g., 'dealing with anxiety', 'finding purpose', 'handling criticism'...",
        height=100
    )
    
    st.header("🎨 Design")
    size = st.selectbox("Format", list(SIZES.keys()))
    bg_style = st.selectbox("Background Style", BACKGROUND_STYLES)
    
    # Theme selection
    if category == "Auto-select (AI chooses best)":
        theme = st.selectbox("Theme Color", list(THEMES.keys()))
    else:
        theme = category if category in THEMES else "Wisdom"
        st.info(f"Using {theme} theme")
    
    st.header("📱 Social")
    auto_social = st.checkbox("Generate social media post", True)

# Main area
col1, col2 = st.columns([2, 1])

with col1:
    if st.button("✨ Generate Wisdom", type="primary", use_container_width=True):
        if not topic.strip():
            st.error("Please enter a topic or question")
        else:
            with st.spinner("Consulting the great thinkers..."):
                # Get quote from AI
                if category == "Auto-select (AI chooses best)":
                    quote_data = get_ai_quote(topic)
                else:
                    quote_data = get_ai_quote(topic, category)
                
                # Store in session state
                st.session_state.quote_data = quote_data
                st.session_state.theme = theme
                st.session_state.size = size
                st.session_state.bg_style = bg_style
                
                # Generate social post
                if auto_social:
                    social_post = generate_social_post(quote_data)
                    st.session_state.social_post = social_post

# Display results if we have quote data
if "quote_data" in st.session_state:
    quote_data = st.session_state.quote_data
    
    # Display quote info
    st.subheader(f"📜 {quote_data['category']} Wisdom")
    
    col_a, col_b = st.columns([2, 1])
    
    with col_a:
        st.markdown(f"### \"{quote_data['quote']}\"")
        st.markdown(f"**— {quote_data['author']}**")
        st.markdown("---")
        st.markdown(f"**Insight:** {quote_data['explanation']}")
        
        # Show keywords
        if "keywords" in quote_data:
            st.markdown("**Keywords:** " + " • ".join(quote_data['keywords']))
    
    with col_b:
        st.info(f"**AI Style Suggestion:** {quote_data.get('style_suggestion', 'Minimal')}")
        
        # Generate image
        with st.spinner("Creating visual..."):
            image = create_quote_image(
                st.session_state.size,
                st.session_state.theme,
                quote_data,
                st.session_state.bg_style
            )
        
        st.image(image, use_container_width=True)
        
        # Download buttons
        col1, col2 = st.columns(2)
        
        with col1:
            img_bytes = io.BytesIO()
            image.save(img_bytes, format="PNG")
            st.download_button(
                "📥 Download Image",
                data=img_bytes.getvalue(),
                file_name=f"wisdom_{quote_data['category'].lower()}_{int(time.time())}.png",
                mime="image/png",
                use_container_width=True
            )
        
        with col2:
            if st.button("🎬 Create Video (8s)", use_container_width=True):
                with st.spinner("Animating wisdom..."):
                    video_data = create_quote_video(
                        st.session_state.size,
                        st.session_state.theme,
                        quote_data,
                        st.session_state.bg_style
                    )
                    
                    if video_data:
                        st.video(video_data)
                        
                        st.download_button(
                            "📥 Download Video",
                            data=video_data,
                            file_name=f"wisdom_{quote_data['category'].lower()}_{int(time.time())}.mp4",
                            mime="video/mp4",
                            use_container_width=True
                        )
    
    # Social media post
    if "social_post" in st.session_state:
        st.markdown("---")
        st.subheader("📱 Social Media Post")
        
        col_x, col_y = st.columns([3, 1])
        
        with col_x:
            st.text_area("Copy this post:", st.session_state.social_post, height=200)
        
        with col_y:
            if st.button("📋 Copy to Clipboard", use_container_width=True):
                st.code(st.session_state.social_post)
                st.success("Copied!")
            
            st.markdown("**Platform Tips:**")
            st.markdown("- **TikTok:** Add trending audio")
            st.markdown("- **Instagram:** Use carousel format")
            st.markdown("- **Twitter:** Thread the explanation")
    
    # New search option
    st.markdown("---")
    if st.button("🔍 Find Another Quote", use_container_width=True):
        # Clear session state
        for key in ['quote_data', 'social_post']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# Instructions if no quote yet
else:
    with col1:
        st.info("""
        **How to use Wisdom Studio:**
        
        1. **Enter a topic** - What wisdom are you seeking? (anxiety, success, relationships, etc.)
        2. **Choose a category** - Philosophy, Stoicism, Psychology, or let AI choose
        3. **Click "Generate Wisdom"** - AI will find the perfect quote
        4. **Customize the design** - Choose format and background style
        5. **Download & share** - Get images, videos, and social posts
        
        *Example topics:* "overcoming fear", "finding happiness", "dealing with change", "building resilience"
        """)
    
    with col2:
        # Example preview
        st.markdown("**Example Output:**")
        st.image("https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=400&h=600&fit=crop", 
                caption="AI-generated wisdom visualization", use_container_width=True)

# Footer
st.markdown("---")
st.caption("Wisdom Studio | AI-powered insights from philosophy, stoicism & psychology | Powered by Groq AI")

# Cleanup old files
for file in os.listdir("."):
    if file.startswith("quote_video_") and file.endswith(".mp4"):
        try:
            if time.time() - os.path.getctime(file) > 300:
                os.remove(file)
        except:
            pass