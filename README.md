# MagicTale AI — Children's Storybook Creator

An end-to-end full-stack AI web application that automatically generates an illustrated five-page children's storybook from a single user prompt, with graphically consistent characters, professional story structure, and downloadable publication-ready PDF.

---

## Features

- **Single-Prompt Generation**: Provide one creative premise (e.g., *"Create a five-page children's story about a brave young character discovering a hidden magical garden."*) and the system creates the entire five-page illustrated book.
- **Narrative Story Arc**: Automatically produces a structured five-page storybook following standard children's picture book pacing:
  - Page 1: Beginning (world & character introduction)
  - Page 2: Discovery (intriguing mystery or encounter)
  - Page 3: Adventure (journey into the unknown)
  - Page 4: Challenge (gentle conflict or problem to solve)
  - Page 5: Satisfying Ending (warm resolution & lesson learned)
- **Character Consistency Engine**: Generates a unified character profile with locked facial features, hairstyle, skin tone, clothing, and palette, prepended to all scene illustration prompts to preserve visual continuity across all 5 pages.
- **Multi-Provider Visual Pipeline**: Supports OpenAI DALL-E 3 for live generation, free AI visual fallbacks, and curated offline canvases.
- **Publication-Ready PDF Generation**: Uses ReportLab to generate landscape-format children's storybook PDFs with title cover, high-resolution illustrations, typography, page numbers, and decorative borders.
- **Interactive Web Interface**: Streamlit UI featuring generation progress indicators, page-by-page reader, 5-page gallery preview, and direct PDF download button.
- **FastAPI REST Backend**: Modular API endpoints for story creation, individual illustration generation, and PDF assembly.

---

## Architecture and Project Structure

```
storybook-agent/
├── app.py                      # Streamlit frontend user interface
├── backend.py                  # FastAPI REST API server
├── character_consistency.py    # Character profile generator & visual consistency engine
├── story_generator.py          # 5-stage story generation with Pydantic validation
├── image_generator.py          # Illustration generator (DALL-E 3 / Free AI / Canvas)
├── pdf_generator.py            # ReportLab landscape storybook PDF generator
├── requirements.txt            # Python dependencies
├── .env.example                # Sample environment configuration
├── README.md                   # Documentation and instructions
├── generated/                  # Generated assets, images, and compiled PDFs
└── assets/                     # Static UI assets and banners
```

---

## Installation & Setup

### Prerequisites
- Python 3.10 or higher
- Git (optional)

### 1. Clone or Open the Workspace
```bash
cd storybook-agent
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` and set your OpenAI API key:
```env
OPENAI_API_KEY=your_actual_openai_api_key_here
PORT=8000
HOST=127.0.0.1
BACKEND_URL=http://127.0.0.1:8000
```

> **Note on Demo Mode:** If an OpenAI API key is not supplied or if quota is exceeded, the application seamlessly activates the built-in Demo Engine and AI Visual Engine.

---

## Running the Application

### Option A: Running with Full FastAPI Backend & Streamlit Frontend

1. **Start the FastAPI Backend** (in terminal 1):
```bash
python backend.py
```
or:
```bash
uvicorn backend:app --host 127.0.0.1 --port 8000 --reload
```
The FastAPI documentation will be available at: `http://127.0.0.1:8000/docs`

2. **Launch the Streamlit User Interface** (in terminal 2):
```bash
streamlit run app.py
```
The web application will open in your browser at: `http://localhost:8501`

---

## REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check and OpenAI key configuration status |
| `POST` | `/api/generate-story` | Generates 5-page story structure and character profile |
| `POST` | `/api/generate-image` | Generates a single scene illustration |
| `POST` | `/api/generate-pdf` | Compiles story and illustrations into a ReportLab PDF |
| `POST` | `/api/generate-storybook` | Full pipeline: story + 5 illustrations + PDF |
| `GET` | `/api/download-pdf/{filename}` | Download generated PDF file |
| `GET` | `/generated/{path}` | Direct static access to generated image files |

---

## Verification & Testing

To test the complete workflow:
1. Open the web interface at `http://localhost:8501`.
2. Enter a prompt (e.g. *"Create a five-page children's story about a brave young character discovering a hidden magical garden."*).
3. Click **✨ Generate Storybook**.
4. Observe the 4-step progress indicator.
5. Review the character profile and ensure all 5 illustrations maintain character attributes.
6. Verify the 5 connected story stages (Beginning, Discovery, Adventure, Challenge, Ending).
7. Click **📥 Download Illustrated PDF** and open the generated PDF to inspect layout, typography, and image placement.
