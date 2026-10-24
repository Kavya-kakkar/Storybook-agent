import os
import uuid
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from character_consistency import CharacterProfile, generate_character_profile
from story_generator import Storybook, generate_story
from image_generator import generate_all_story_illustrations
from pdf_generator import generate_pdf, sanitize_filename

st.set_page_config(
    page_title="MagicTale AI — Children's Storybook Creator",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700;800&family=Quicksand:wght@500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Quicksand', sans-serif;
    }
    
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
    }
    
    .main-title-container {
        background: linear-gradient(135deg, #FFF5EB 0%, #E8F5E9 50%, #E3F2FD 100%);
        padding: 2.2rem 2.5rem;
        border-radius: 20px;
        border: 2px solid #E0E7FF;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.03);
    }
    
    .title-text {
        font-family: 'Outfit', sans-serif;
        font-size: 2.6rem;
        font-weight: 800;
        color: #1E293B;
        margin: 0;
        letter-spacing: -0.5px;
    }
    
    .subtitle-text {
        font-size: 1.15rem;
        color: #64748B;
        margin-top: 0.5rem;
        margin-bottom: 0;
    }
    
    .character-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 6px solid #4F46E5;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    
    .stage-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        background-color: #EEF2FF;
        color: #4F46E5;
        margin-bottom: 0.5rem;
    }
    
    .page-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 16px rgba(0,0,0,0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .page-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.08);
    }
    
    .story-text-box {
        font-size: 1.05rem;
        line-height: 1.8;
        color: #334155;
        padding: 1rem;
        background-color: #F8FAFC;
        border-radius: 10px;
        border-left: 3px solid #CBD5E1;
    }
    
    .stButton>button {
        border-radius: 12px;
        font-weight: 700;
        padding: 0.6rem 1.5rem;
        transition: all 0.2s ease;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

if "storybook" not in st.session_state:
    st.session_state.storybook = None
if "image_results" not in st.session_state:
    st.session_state.image_results = []
if "pdf_path" not in st.session_state:
    st.session_state.pdf_path = None
if "story_id" not in st.session_state:
    st.session_state.story_id = None

@st.cache_data(ttl=30)
def check_backend_health():
    try:
        r = requests.get("http://127.0.0.1:8000/health", timeout=1.5)
        if r.status_code == 200:
            return "Online (FastAPI :8000)", "green"
        return "Unhealthy", "orange"
    except Exception:
        return "Offline (Local Engine Active)", "blue"


with st.sidebar:
    st.markdown("### ⚙️ Engine Settings")
    
    active_env_key = (os.getenv("OPEN_ROUTER_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")).strip()
    if active_env_key:
        provider_name = "OpenRouter" if active_env_key.startswith("sk-or-") else "OpenAI"
        st.success(f"🔑 {provider_name} API key active from .env", icon="✅")
    else:
        st.caption("No API key in .env. The Smart Story & Visual Engine will create full illustrated storybooks.")
    
    user_api_key = st.text_input(
        "Override API Key (Optional)",
        value="",
        type="password",
        placeholder="Leave blank to use .env key",
        help="Only enter a key here if you want to override the one in your .env file. Never paste secrets into shared environments."
    )
    
    target_age = st.selectbox(
        "Target Age Group",
        options=["3-5 years (Preschool)", "5-8 years (Early Reader)", "8-12 years (Middle Grade)"],
        index=1
    )
    
    backend_status, backend_color = check_backend_health()
    st.markdown(f"**Backend Status:** :{backend_color}[● {backend_status}]")
    
    st.markdown("---")
    st.markdown("### 💡 Quick Prompt Inspiration")
    example_prompts = [
        "A brave young character discovering a hidden magical garden.",
        "A curious little bunny named Barnaby who finds a lost clockwork pocket watch in the clover.",
        "An adventurous boy named Leo who builds a flying pedal cart to visit cloud castles.",
        "A gentle young girl named Maya who teaches a shy baby river dragon how to blow rainbow bubbles."
    ]
    
    for ex in example_prompts:
        if st.button(ex[:36] + "...", key=f"ex_{abs(hash(ex))}", use_container_width=True):
            st.session_state["prompt_input"] = ex

st.markdown("""
<div class="main-title-container">
    <div style="font-size: 2.2rem; margin-bottom: 0.2rem;">✨📖🎨</div>
    <h1 class="title-text">MagicTale AI — Children's Storybook Creator</h1>
    <p class="subtitle-text">Turn a single imaginative spark into a five-page illustrated children's storybook with consistent characters and downloadable PDF.</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])

with col1:
    default_prompt = st.session_state.get(
        "prompt_input",
        "Create a five-page children's story about a brave young character discovering a hidden magical garden."
    )
    prompt_input = st.text_area(
        "Enter your story idea or premise:",
        value=default_prompt,
        height=100,
        placeholder="e.g. A young girl discovering a secret whispering garden with glowing flowers..."
    )

with col2:
    st.markdown("<br/>", unsafe_allow_html=True)
    generate_btn = st.button("✨ Generate Storybook", type="primary", use_container_width=True)
    st.caption("Includes 5 story stages, consistent character illustrations, and printable PDF.")

if generate_btn:
    if not prompt_input.strip():
        st.error("Please enter a story idea before generating.")
    else:
        st.session_state.storybook = None
        st.session_state.image_results = []
        st.session_state.pdf_path = None
        
        story_id = str(uuid.uuid4())[:8]
        st.session_state.story_id = story_id
        output_dir = os.path.join("generated", story_id)
        os.makedirs(output_dir, exist_ok=True)
        
        progress_bar = st.progress(0.0)
        status_box = st.status("🌟 Crafting your magical storybook...", expanded=True)
        
        try:
            status_box.write("Step 1/4: Analyzing prompt & anchoring character consistency profile...")
            progress_bar.progress(0.15)
            
            clean_age = target_age.split(" ")[0]
            env_key = (os.getenv("OPEN_ROUTER_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")).strip()
            api_key_to_use = user_api_key.strip() if user_api_key.strip() else (env_key or None)

            storybook = generate_story(
                prompt=prompt_input,
                target_age=clean_age,
                api_key=api_key_to_use
            )
            st.session_state.storybook = storybook
            
            status_box.write(f"✓ Character locked: **{storybook.character.name}** ({storybook.character.species_or_type})")
            status_box.write(f"✓ Story scripted: *{storybook.title}* ({len(storybook.pages)} pages)")
            progress_bar.progress(0.35)

            status_box.write("Step 2/4: Generating consistent scene illustrations (Pages 1 to 5)...")
            
            def on_image_step(curr, total, msg):
                frac = 0.35 + (curr / total) * 0.45
                progress_bar.progress(min(frac, 0.85))
                status_box.write(f"🎨 {msg}")

            image_results = generate_all_story_illustrations(
                pages=storybook.pages,
                character=storybook.character,
                output_dir=output_dir,
                story_id=story_id,
                api_key=api_key_to_use,
                progress_callback=on_image_step
            )
            st.session_state.image_results = image_results
            progress_bar.progress(0.85)

            status_box.write("Step 3/4: Rendering ReportLab publication-ready PDF...")
            pdf_dir = os.path.join("generated", "pdfs")
            image_paths = [res["image_path"] for res in image_results]
            pdf_path = generate_pdf(storybook, image_paths, pdf_dir)
            st.session_state.pdf_path = pdf_path
            
            progress_bar.progress(1.0)
            status_box.update(label="🎉 Storybook generated successfully!", state="complete", expanded=False)
            st.balloons()
            
        except Exception as err:
            status_box.update(label="❌ Generation encountered an issue", state="error")
            st.error(f"Error during generation: {str(err)}")

if st.session_state.storybook and st.session_state.pdf_path:
    sb: Storybook = st.session_state.storybook
    images = st.session_state.image_results
    pdf_file = st.session_state.pdf_path
    
    st.markdown("---")
    
    top_col1, top_col2 = st.columns([2, 1])
    with top_col1:
        st.markdown(f"## 📖 {sb.title}")
        st.markdown(f"**Theme:** {sb.theme} &bull; **Audience:** {sb.target_age}")
        if sb.is_demo_mode:
            st.info(f"ℹ️ **{sb.mode_label}**: Full story and illustrations rendered seamlessly. For live DALL-E 3 & GPT-4o, add a valid OpenAI API key in the sidebar.")
        else:
            st.success(f"✨ **Mode:** {sb.mode_label}")
            
    with top_col2:
        if os.path.exists(pdf_file):
            with open(pdf_file, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="📥 Download Illustrated PDF",
                data=pdf_bytes,
                file_name=os.path.basename(pdf_file),
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
            st.caption(f"File: {os.path.basename(pdf_file)} ({len(pdf_bytes) // 1024} KB)")

    with st.expander("👤 Main Character Profile & Visual Anchor Details", expanded=False):
        c = sb.character
        c_col1, c_col2 = st.columns(2)
        with c_col1:
            st.markdown(f"**Name:** {c.name}")
            st.markdown(f"**Age / Type:** {c.age} &bull; {c.species_or_type}")
            st.markdown(f"**Facial Features:** {c.face}")
            st.markdown(f"**Hairstyle / Fur:** {c.hairstyle}")
        with c_col2:
            st.markdown(f"**Skin Tone / Scales:** {c.skin_tone}")
            st.markdown(f"**Clothing:** {c.clothing}")
            st.markdown(f"**Color Palette:** {c.colors}")
            st.markdown(f"**Distinctive Features:** {c.distinctive_features}")
        st.markdown(f"**Artistic Style Rule:** `{c.art_style}`")

    st.markdown("### 📚 Five-Page Illustrated Preview")
    
    view_tab1, view_tab2 = st.tabs(["📑 Storybook Reader (Page by Page)", "🖼️ All 5 Pages (Gallery View)"])
    
    with view_tab1:
        page_index = st.radio(
            "Select Page:",
            options=list(range(1, 6)),
            format_func=lambda i: f"Page {i}: {sb.pages[i-1].title}",
            horizontal=True
        )
        curr_page = sb.pages[page_index - 1]
        curr_img_path = images[page_index - 1]["image_path"] if page_index - 1 < len(images) else None
        curr_img_prov = images[page_index - 1].get("provider", "Engine") if page_index - 1 < len(images) else "Engine"

        v_col1, v_col2 = st.columns([1, 1], gap="large")
        with v_col1:
            if curr_img_path and os.path.exists(curr_img_path):
                st.image(curr_img_path, use_container_width=True, caption=f"Page {curr_page.page_number} Illustration [{curr_img_prov}]")
            else:
                st.warning("Illustration preview not available.")
        with v_col2:
            st.markdown(f"<span class='stage-badge'>{curr_page.stage}</span>", unsafe_allow_html=True)
            st.markdown(f"### {curr_page.title}")
            st.markdown(f"<div class='story-text-box'>{curr_page.text}</div>", unsafe_allow_html=True)
            st.markdown("<br/>", unsafe_allow_html=True)
            st.markdown(f"**Visual Prompt:** *{curr_page.scene_description}*")
            st.markdown(f"**Continuity Note:** {curr_page.continuation_notes}")

    with view_tab2:
        for idx, page in enumerate(sb.pages):
            img_path = images[idx]["image_path"] if idx < len(images) else None
            img_prov = images[idx].get("provider", "Engine") if idx < len(images) else "Engine"
            
            with st.container():
                st.markdown(f"""
                <div class="page-card">
                    <span class="stage-badge">{page.stage} • Page {page.page_number} of 5</span>
                    <h3 style="margin-top: 0.3rem;">{page.title}</h3>
                </div>
                """, unsafe_allow_html=True)
                
                g_col1, g_col2 = st.columns([1, 1], gap="medium")
                with g_col1:
                    if img_path and os.path.exists(img_path):
                        st.image(img_path, use_container_width=True, caption=f"Page {page.page_number} • {img_prov}")
                with g_col2:
                    st.markdown(f"<div class='story-text-box'>{page.text}</div>", unsafe_allow_html=True)
                    st.caption(f"Scene prompt: {page.scene_description}")
                st.markdown("<br/>", unsafe_allow_html=True)
