"""
STILL MIND - Complete Social Media Quote Generator
BATCH EDITION: Framework + Style Trinity + Groq Strategy
"""

import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, random, io, json, time, datetime
import numpy as np
import imageio.v3 as iio
from groq import Groq
from collections import OrderedDict

# ============================================
# 1. STYLE DEFINITIONS (The Trinity)
# ============================================
STYLE_TRINITY = {
    "Midnight Aura": {
        "bg": (13, 27, 42),
        "accent": (129, 236, 236), # Teal
        "glow": (27, 67, 50),
        "rain_alpha": 80
    },
    "Kenyan Forest": {
        "bg": (10, 25, 20),
        "accent": (255, 255, 255), # White
        "glow": (45, 106, 79),
        "rain_alpha": 100
    },
    "Cyber Hustle": {
        "bg": (20, 20, 20),
        "accent": (255, 107, 107), # Coral Red
        "glow": (60, 20, 20),
        "rain_alpha": 60
    }
}

# ============================================
# 2. UNIFIED PRODUCTION ENGINE
# ============================================
class ImageGenerator:
    def __init__(self):
        self.font_path = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"

    def _draw_procedural_bg(self, size, t, style_name):
        """Generates the creative animated gradient backdrop based on style."""
        w, h = size
        style = STYLE_TRINITY[style_name]
        base = Image.new("RGB", size, style["bg"])
        draw = ImageDraw.Draw(base)
        
        # Draw moving 'Aura' orbs
        for i in range(2):
            ox = w//2 + math.cos(t * 0.4 + i) * 180
            oy = h//2 + math.sin(t * 0.2 + i) * 250
            radius = 550 + math.sin(t) * 60
            draw.ellipse([ox-radius, oy-radius, ox+radius, oy+radius], fill=style["glow"])
            
        return base.filter(ImageFilter.GaussianBlur(radius=70))

    def generate_frame(self, quote, author, hook, t, style_name, size=(1080, 1920)):
        w, h = size
        style = STYLE_TRINITY[style_name]
        
        # 1. Background & Rain
        img = self._draw_procedural_bg(size, t, style_name).convert("RGBA")
        draw = ImageDraw.Draw(img)
        
        random.seed(42) 
        for i in range(25):
            rx = random.randint(0, w)
            ry = ((t * (550 + (i%5)*120)) + random.randint(0, h)) % h
            draw.line([(rx, ry), (rx, ry + 30)], fill=style["accent"] + (style["rain_alpha"],), width=2)

        # 2. Centered Card (Floating)
        cw, ch = 900, 750
        cx, cy = (w - cw)//2, (h // 2) - 350 + math.sin(t*2.2)*18
        
        # Broken Border
        thick, gap = 6, 130
        color = style["accent"] + (255,)
        draw.line([(cx, cy + gap), (cx, cy + ch), (cx + cw, cy + ch), (cx + cw, cy + gap)], fill=color, width=thick)
        draw.line([(cx + cw, cy + ch - gap), (cx + cw, cy)], fill=color, width=thick)
        draw.line([(cx, cy), (cx + cw - gap, cy)], fill=color, width=thick)

        # 3. Typography
        try:
            f_h = ImageFont.truetype(self.font_path, 42)
            f_q = ImageFont.truetype(self.font_path, 52)
        except:
            f_h = f_q = ImageFont.load_default()

        # Hook Text
        draw.text((cx, cy - 80), hook.upper(), font=f_h, fill=color)

        # Quote Body
        visible = int(t * 22)
        draw.multiline_text((cx+70, cy+150), quote[:visible], font=f_q, fill=(255,255,255), spacing=15)
        
        return img.convert("RGB")

    def export_batch(self, quote, author, hook):
        """Renders all three styles in parallel."""
        results = {}
        for style_name in STYLE_TRINITY.keys():
            frames = []
            for i in range(72): # 6 seconds @ 12fps
                frames.append(np.array(self.generate_frame(quote, author, hook, i/12, style_name)))
            
            buf = io.BytesIO()
            iio.imwrite(buf, frames, format='mp4', fps=12, codec='libx264')
            buf.seek(0)
            results[style_name] = buf
        return results

# ============================================
# 3. STREAMLIT INTERFACE
# ============================================
def main():
    st.set_page_config(page_title="Still Mind Batch Studio", layout="wide")
    
    # Initialization
    if 'gen' not in st.session_state:
        st.session_state.gen = ImageGenerator()
        st.session_state.groq = Groq(api_key=st.secrets["groq_key"])

    st.title("🎬 Still Mind: Style Trinity Studio")
    st.markdown("Generate 3 unique visual identities for your quote in one click.")

    with st.sidebar:
        st.header("Content Input")
        topic = st.text_input("Topic", "Hustle Culture")
        quote = st.text_area("The Wisdom", "Work in silence, let the results make the noise.")
        author = st.text_input("Author", "Still Mind Nairobi")
        
        generate = st.button("🔥 GENERATE STYLE TRINITY", use_container_width=True)

    if generate:
        with st.spinner("🧠 AI Strategizing & Rendering Batch..."):
            # 1. Groq Strategy
            prompt = f"Generate a 3-word scroll-stopper hook for this quote: {quote}. Mix English and Sheng. Return JSON: {{'hook': '...'}}"
            res = st.session_state.groq.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="mixtral-8x7b-32768",
                response_format={"type": "json_object"}
            )
            hook = json.loads(res.choices[0].message.content)['hook']
            
            # 2. Render all 3 styles
            batch = st.session_state.gen.export_batch(quote, author, hook)
            st.session_state.current_batch = batch
            st.session_state.current_hook = hook

    # Display Results in Grid
    if 'current_batch' in st.session_state:
        cols = st.columns(3)
        styles = list(STYLE_TRINITY.keys())
        
        for i, col in enumerate(cols):
            style_name = styles[i]
            with col:
                st.subheader(style_name)
                st.video(st.session_state.current_batch[style_name])
                st.download_button(f"📥 Download {style_name}", 
                                 st.session_state.current_batch[style_name], 
                                 f"{style_name.lower().replace(' ','_')}.mp4")

if __name__ == "__main__":
    main()
