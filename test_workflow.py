import os
import sys
from character_consistency import (
    CharacterProfile,
    generate_character_profile,
    build_scene_prompt,
    get_master_prompt
)
from story_generator import Storybook, generate_story
from image_generator import generate_all_story_illustrations
from pdf_generator import generate_pdf

def run_all_tests():
    prompt = "Create a five-page children's story about a brave young character discovering a hidden magical garden."
    
    char = generate_character_profile(prompt, "4-8 years", api_key=None)
    assert char.name, "Character must have a name"
    assert char.face, "Character must have face description"
    assert char.clothing, "Character must have clothing description"
    master_desc = get_master_prompt(char)
    assert len(master_desc) > 30, "Master prompt must be descriptive"

    storybook = generate_story(prompt, "4-8 years", api_key=None)
    assert len(storybook.pages) == 5, f"Expected 5 pages, got {len(storybook.pages)}"
    
    expected_stages = ["Beginning", "Discovery", "Adventure", "Challenge", "Satisfying Ending"]
    for idx, page in enumerate(storybook.pages):
        assert page.page_number == idx + 1, f"Page number should be {idx + 1}"
        assert page.stage == expected_stages[idx], f"Stage mismatch on page {idx + 1}"
        assert len(page.text.split()) >= 40, f"Page {idx + 1} text too short"
        assert len(page.scene_description) > 10, f"Page {idx + 1} missing scene prompt"
        
        scene_prompt = build_scene_prompt(storybook.character, page.scene_description)
        assert storybook.character.name in scene_prompt, "Scene prompt must reference main character"

    test_output_dir = os.path.join("generated", "test_run")
    os.makedirs(test_output_dir, exist_ok=True)
    
    img_results = generate_all_story_illustrations(
        pages=storybook.pages,
        character=storybook.character,
        output_dir=test_output_dir,
        story_id="test_run",
        api_key=None
    )
    assert len(img_results) == 5, "Must generate exactly 5 illustrations"
    for r in img_results:
        assert r["success"] is True, f"Illustration failed: {r}"
        assert os.path.exists(r["image_path"]), f"Image file missing: {r['image_path']}"
        assert os.path.getsize(r["image_path"]) > 1000, f"Image file empty or too small: {r['image_path']}"

    pdf_dir = os.path.join("generated", "pdfs")
    image_paths = [r["image_path"] for r in img_results]
    pdf_path = generate_pdf(storybook, image_paths, pdf_dir)
    
    assert os.path.exists(pdf_path), "PDF was not created"
    pdf_size = os.path.getsize(pdf_path)
    assert pdf_size > 10000, f"PDF file size too small: {pdf_size} bytes"

    with open(pdf_path, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-", "Generated file is not a valid PDF"

    print("ALL TESTS PASSED SUCCESSFULLY!")
    print(f"Generated PDF: {pdf_path} (Size: {pdf_size} bytes)")

if __name__ == "__main__":
    run_all_tests()
