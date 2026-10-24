import json
import os
from typing import List, Optional
from pydantic import BaseModel, Field
from openai import OpenAI
from character_consistency import (
    CharacterProfile,
    generate_character_profile,
    get_master_prompt
)

class StoryPage(BaseModel):
    page_number: int = Field(..., ge=1, le=5)
    stage: str
    title: str
    text: str
    scene_description: str
    continuation_notes: str

class Storybook(BaseModel):
    title: str
    theme: str
    target_age: str = "4-8 years"
    character: CharacterProfile
    pages: List[StoryPage]
    is_demo_mode: bool = False
    mode_label: str = "Live OpenAI API"
    error_message: Optional[str] = None

def create_fallback_story(prompt: str, character: CharacterProfile, target_age: str, reason: str = "") -> Storybook:
    cname = character.name
    spec = character.species_or_type
    low = prompt.lower()
    
    if "garden" in low or "magical" in low:
        title = f"{cname} and the Secret Whispering Garden"
        theme = "Curiosity, wonder, and caring for nature"
        p1 = StoryPage(
            page_number=1,
            stage="Beginning",
            title="Beyond the Cobblestone Path",
            text=f"Every morning, little {cname} walked past the tall stone wall at the edge of town. Birds sang cheerfully in the ancient oak trees, but today, something twinkled behind the ivy. A gentle breeze rustled the green leaves, carrying the sweetest scent of honeysuckle and warm cinnamon. {cname} paused, eyes wide with curiosity, wondering what mysteries lay hidden just behind the old grey stones.",
            scene_description=f"{cname} standing on a sun-dappled cobblestone path near an ancient mossy stone wall covered in green ivy, gazing with wonder at a golden glimmer behind the leaves.",
            continuation_notes=f"Introduces {cname} and the mysterious glimmer in the wall."
        )
        p2 = StoryPage(
            page_number=2,
            stage="Discovery",
            title="The Carved Wooden Arch",
            text=f"Brushing the leafy vines aside, {cname} gasped in delight. A tiny wooden door stood revealed, carved with dancing flowers and sleeping moons. The round brass handle was warm to the touch. With a soft click, the door swung open, unveiling a hidden world where luminous blossoms glowed in shades of turquoise, peach, and lavender, glowing softly beneath the shade of silver weeping willows.",
            scene_description=f"{cname} gently pushing open a miniature carved wooden archway in the stone wall, face illuminated by magical glowing pastel flowers.",
            continuation_notes=f"{cname} steps through the archway into the magical garden."
        )
        p3 = StoryPage(
            page_number=3,
            stage="Adventure",
            title="The Humming Brook",
            text=f"{cname} tiptoed along stepping stones shaped like giant water lilies. Floating dragonflies with wings like stained glass twirled over a sparkling sapphire brook that hummed a peaceful lullaby. Tiny glass butterflies fluttered around {cname}, playfully leading the way deeper into the enchanted grove, where giant mushrooms glowed like friendly nightlights under the emerald canopy.",
            scene_description=f"{cname} happily stepping across giant lilypad stones across a crystalline bubbling creek with translucent dragonflies and glowing mushrooms all around.",
            continuation_notes=f"{cname} journeys deeper into the heart of the garden."
        )
        p4 = StoryPage(
            page_number=4,
            stage="Challenge",
            title="The Thirsty Golden Blossom",
            text=f"At the garden center stood the Great Star Lily, the heart of the sanctuary. But its golden petals were drooping, and the crystal fountain beside it was blocked by tangled river pebbles. {cname} knelt down gently, rolling up their sleeves. Patiently and carefully, stone by stone, {cname} cleared the quiet fountain until pure crystalline water gushed forth once more.",
            scene_description=f"{cname} carefully lifting round pebbles from a mossy stone fountain basin to help a giant drooping golden flower drink glowing water.",
            continuation_notes=f"{cname} resolves the blockage and brings life back to the centerpiece blossom."
        )
        p5 = StoryPage(
            page_number=5,
            stage="Satisfying Ending",
            title="A Garden of Eternal Friends",
            text=f"The Star Lily burst into dazzling golden light, showering sparkling dew across the whole garden. The little creatures cheered in musical chirps, and the flowers leaned forward in gratitude. {cname} smiled warmly, keeping the garden's secret safe in their heart. Whenever the world felt noisy, {cname} knew true magic was always blooming just behind the quiet garden door.",
            scene_description=f"{cname} smiling joyfully in the center of the radiant illuminated garden surrounded by sparkling friendly creatures and fully bloomed golden flowers.",
            continuation_notes=f"Concludes with heartwarming harmony and {cname}'s quiet confidence."
        )
    else:
        title = f"{cname}'s Great Adventure"
        theme = "Courage, kindness, and exploration"
        p1 = StoryPage(
            page_number=1,
            stage="Beginning",
            title="A Bright New Day",
            text=f"The golden morning sun poured through the treetops as {cname} woke up with excitement bubbling in their chest. Today was not an ordinary day; a mysterious breeze carried a folded parchment map right to the front porch. With a cheerful grin and a heart full of curiosity, {cname} packed a small lunch and set out on a grand expedition.",
            scene_description=f"{cname} standing on the wooden porch of a cozy cottage, holding an illustrated adventure map under warm morning sunlight.",
            continuation_notes=f"Introduces {cname} receiving the treasure map and starting the trip."
        )
        p2 = StoryPage(
            page_number=2,
            stage="Discovery",
            title="The Whistling Forest",
            text=f"Following the winding dotted trail, {cname} arrived at the edge of the Whistling Forest. The trees were tall and emerald green, swaying in harmony like cheerful dancers. Among the mossy roots, sparkling crystal pebbles marked a winding trail that no one in the village had ever seen before. {cname} took a deep breath and stepped boldly forward.",
            scene_description=f"{cname} standing at the entrance to a bright sunlit forest where crystal pebbles glitter along a whimsical path.",
            continuation_notes=f"{cname} enters the uncharted territory."
        )
        p3 = StoryPage(
            page_number=3,
            stage="Adventure",
            title="The Bridge of Whispers",
            text=f"Deep in the woods, a suspension bridge made of woven silver vines stretched over a singing gorge. Colorful birds with sapphire feathers soared alongside {cname}, chirping encouragement. Each careful step resonated like a musical chime. High above the forest floor, {cname} felt like they were flying among the soft white clouds and gentle breezes.",
            scene_description=f"{cname} carefully crossing a safe, whimsical rope bridge woven with blooming vines high in the green forest canopy with bright blue birds.",
            continuation_notes=f"{cname} braves the high crossing to reach the other ridge."
        )
        p4 = StoryPage(
            page_number=4,
            stage="Challenge",
            title="The Lost Key of the Mountain",
            text=f"Across the gorge, an ancient stone gate guarded the highest hilltop. But its heavy iron lock was stuck, overgrown with thick thorny brambles. Rather than forcing it, {cname} gently untangled the thorns and hummed the melody learned from the singing birds. Recognizing the tune of kindness, the ancient lock clicked open with a soft metallic sparkle.",
            scene_description=f"{cname} gently clearing away thorny vines from an ornate ancient brass lock on a mossy stone gateway, smiling kindly.",
            continuation_notes=f"{cname} uses gentleness and harmony to unlock the gate."
        )
        p5 = StoryPage(
            page_number=5,
            stage="Satisfying Ending",
            title="The View from the Summit",
            text=f"Beyond the gate lay the most breathtaking view {cname} had ever seen: rolling green hills dotted with wildflowers, a sparkling lake reflecting the rainbow sky, and friendly forest animals gathered to welcome them. {cname} sat on the warm summit rock, knowing that true bravery is simply taking that first step with kindness in your heart.",
            scene_description=f"{cname} sitting peacefully on top of a scenic mountain overlooking rolling green hills and a rainbow-lit horizon, surrounded by friendly woodland animals.",
            continuation_notes=f"Satisfying celebration and triumph."
        )

    return Storybook(
        title=title,
        theme=theme,
        target_age=target_age,
        character=character,
        pages=[p1, p2, p3, p4, p5],
        is_demo_mode=True,
        mode_label="Demo Mode (Intelligent Story Engine)",
        error_message=reason if reason else None
    )

def generate_story(prompt: str, target_age: str = "4-8 years", api_key: Optional[str] = None) -> Storybook:
    active_key = (api_key or os.getenv("OPEN_ROUTER_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")).strip()
    character = generate_character_profile(prompt, target_age, active_key if active_key else None)
    
    if not active_key:
        return create_fallback_story(prompt, character, target_age, "No API key provided.")

    try:
        is_openrouter = active_key.startswith("sk-or-")
        base_url = "https://openrouter.ai/api/v1" if is_openrouter else None
        model_name = "openai/gpt-4o-mini" if is_openrouter else "gpt-4o-mini"
        mode_label = "Live OpenRouter API (openai/gpt-4o-mini)" if is_openrouter else "Live OpenAI API (gpt-4o-mini)"
        client = OpenAI(api_key=active_key, base_url=base_url, timeout=35.0)
        system_prompt = (
            "You are an acclaimed children's author. Write an illustrated five-page children's storybook. "
            "Constraints:\n"
            "1. Exactly 5 pages, strictly labeled page_number 1 to 5.\n"
            "2. Story arc: Page 1=Beginning, Page 2=Discovery, Page 3=Adventure, Page 4=Challenge, Page 5=Satisfying Ending.\n"
            "3. Each page text must be 50 to 80 words, age-appropriate, evocative, and rhythmic.\n"
            "4. scene_description must describe the visual action and setting clearly while maintaining the character's fixed visual identity.\n"
            "5. Return pure JSON with keys: title, theme, pages (array of 5 objects with page_number, stage, title, text, scene_description, continuation_notes)."
        )
        char_desc = get_master_prompt(character)
        user_prompt = f"Story concept: {prompt}\nTarget age group: {target_age}\nCharacter anchor: {char_desc}"

        response = client.chat.completions.create(
            model=model_name,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.75
        )
        raw_json = response.choices[0].message.content
        data = json.loads(raw_json)
        
        pages_raw = data.get("pages", [])
        if len(pages_raw) != 5:
            return create_fallback_story(prompt, character, target_age, "AI generated invalid page count. Switched to balanced story mode.")

        parsed_pages = []
        stages = ["Beginning", "Discovery", "Adventure", "Challenge", "Satisfying Ending"]
        for idx, p in enumerate(pages_raw):
            page_obj = StoryPage(
                page_number=idx + 1,
                stage=p.get("stage", stages[idx]),
                title=p.get("title", f"Page {idx + 1}"),
                text=p.get("text", "").strip(),
                scene_description=p.get("scene_description", "").strip(),
                continuation_notes=p.get("continuation_notes", f"Transition to stage {idx + 2}")
            )
            parsed_pages.append(page_obj)

        return Storybook(
            title=data.get("title", f"{character.name}'s Journey"),
            theme=data.get("theme", "Exploration and Discovery"),
            target_age=target_age,
            character=character,
            pages=parsed_pages,
            is_demo_mode=False,
            mode_label=mode_label
        )
    except Exception as e:
        return create_fallback_story(prompt, character, target_age, f"API error: {str(e)}")
