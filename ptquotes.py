import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, io, json, requests, time
import numpy as np
import imageio.v3 as iio
from groq import Groq

# ============================================
# 1. BRAND & STYLE CONFIGURATION
# ============================================
LOGO_URL = "https://parenteenkenya.co.ke/wp-content/uploads/2024/09/cropped-Parenteen-Kenya-Logo-rec.png"
CLINICIAN = "Jane Kariuki"
QUALIFICATION = "Clinical Psychologist"

STYLE_TRINITY = {
    "The Bridge (Navy)": {
        "bg": (28, 49, 68), "accent": (144, 190, 109), "text": (255, 255, 255), "glow": (43, 85, 126)
    },
    "Safe Space (Coral)": {
        "bg": (255, 250, 245), "accent": (249, 130, 108), "text": (40, 40, 40), "glow": (255, 218, 210)
    },
    "Evening Clarity (Sage)": {
        "bg": (45, 55, 45), "accent": (255, 209, 102), "text": (255, 255, 255), "glow": (30, 60, 50)
    }
}

# ============================================
# 2. CORE PRODUCTION ENGINE
# ============================================
class ContentEngine:
    def __init__(self):
        try:
            resp = requests.get(LOGO_URL)
            self.logo = Image.open(io.BytesIO(resp.content)).convert("RGBA")
        except:
            self.logo = Image.new("RGBA", (100, 100), (0,0,0,0))

    def generate_frame(self, quote, hook, t, style_name, size=(1080, 1920)):
        w, h = size
        style = STYLE_TRINITY[style_name]
        img = Image.new("RGB", size, style["bg"])
        draw = ImageDraw.Draw(img, "RGBA")

        # A. Breathing Pacer Animation (4s Cycle)
        # Follows Box Breathing rhythm for therapeutic effect
        breath = (math.sin(t * (math.pi / 2)) + 1) / 2
        pacer_r = 300 + (breath * 120)
        draw.ellipse([w//2-pacer_r, h//2-pacer_r, w//2+pacer_r, h//2+pacer_r], 
                     fill=style["glow"] + (50,))

        # B. Kinetic Logo (Subtle Parallax)
        float_y = int(math.sin(t * 2.5) * 12)
        logo_w = 480
        aspect = self.logo.height / self.logo.width
        logo_h = int(logo_w * aspect)
        logo_img = self.logo.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
        img.paste(logo_img, (w//2 - logo_w//2, 200 + float_y), logo_img)

        # C. Kinetic Typography Logic
        # Typewriter reveal effect
        visible_chars = int(len(quote) * min(t/3.5, 1.0)) 
        current_text = quote[:visible_chars]
        
        # Simple Font Rendering (System Default)
        # In production, use ImageFont.truetype("path/to/font.ttf", size)
        draw.text((120, 580), hook.upper(), fill=style["accent"])
        draw.multiline_text((120, 720), current_text, fill=style["text"], spacing=30)

        # D. Professional Branding Footer
        footer_y = h - 250
        draw.line([(w//2-180, footer_y), (w//2+180, footer_y)], fill=style["accent"], width=5)
        draw.text((w//2-160, footer_y + 40), f"{CLINICIAN} | {QUALIFICATION}", fill=style["accent"])
        draw.text((w//2-120, footer_y + 100), "parenteenkenya.co.ke", fill=style["text"])

        return img

    def make_video(self, quote, hook, style_name):
        frames = []
        fps, duration = 12, 6 
        for i in range(fps * duration):
            frames.append(np.array(self.generate_frame(quote, hook, i/fps, style_name)))
        
        buf = io.BytesIO()
        iio.imwrite(buf, frames, format='mp4', fps=fps, codec='libx264')
        buf.seek(0)
        return buf

# ============================================
# 3. STREAMLIT APP WITH GROQ SECRETS
# ============================================
def main():
    st.set_page_config(page_title="ParenTeen Content Studio", page_icon="🌿")
    
    if 'engine' not in st.session_state:
        st.session_state.engine = ContentEngine()
    
    # Check for Groq Key in secrets
    try:
        groq_client = Groq(api_key=st.secrets["groq_key"])
    except:
        st.error("Error: 'groq_key' not found in Streamlit Secrets.")
        st.stop()

    st.title("🌿 ParenTeen Kenya Studio")
    st.subheader(f"Social Media Generator for Jane Kariuki")

    with st.sidebar:
        st.header("Content Strategy")
        topic = st.selectbox("Post Theme", 
                            ["Academic Anxiety", "Digital Boundaries", "Parental Connection", "Teen Independence"])
        
        if st.button("✨ Generate AI Insights (Groq)"):
            with st.spinner("Jane's AI assistant is thinking..."):
                prompt = f"""
                You are a clinical psychologist for ParenTeen Kenya. 
                Generate a 3-word scroll-stopping hook and a short therapeutic insight (max 18 words) for {topic}. 
                The tone should be professional yet warm. 
                Return strictly JSON: {{"hook": "...", "quote": "..."}}
                """
                res = groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="mixtral-8x7b-32768",
                    response_format={"type": "json_object"}
                )
                data = json.loads(res.choices[0].message.content)
                st.session_state.hook = data['hook']
                st.session_state.quote = data['quote']

    col1, col2 = st.columns([1, 1])

    with col1:
        h_val = st.text_input("Title/Hook", value=st.session_state.get('hook', 'HEAR THEM OUT'))
        q_val = st.text_area("Insight/Quote", value=st.session_state.get('quote', 'Connection is the best filter for the world.'))
        s_val = st.selectbox("Visual Style", list(STYLE_TRINITY.keys()))
        render = st.button("🎬 Render Production Video", use_container_width=True)

    with col2:
        if render:
            with st.spinner("Applying animations & branding..."):
                video_data = st.session_state.engine.make_video(q_val, h_val, s_val)
                st.video(video_data)
                st.download_button("📥 Download MP4", video_data, f"parenteen_{topic.lower()}.mp4")

if __name__ == "__main__":
    main()
