import os
import json
import re
from pydantic import BaseModel
from openai import OpenAI

class CharacterProfile(BaseModel):
    name: str
    species_or_type: str = "human child"
    age: str = "7 years old"
    face: str
    hairstyle: str
    skin_tone: str
    clothing: str
    colors: str
    distinctive_features: str
    art_style: str = "whimsical children's storybook illustration, soft warm watercolor and textured gouache, storybook aesthetic, vibrant friendly colors, clean lines, high quality"

def get_master_prompt(profile: CharacterProfile) -> str:
    parts = [
        f"Main character: {profile.name}, a {profile.age} {profile.species_or_type}.",
        f"Facial details: {profile.face}.",
        f"Hair: {profile.hairstyle}.",
        f"Skin tone/Fur: {profile.skin_tone}.",
        f"Clothing: {profile.clothing} in {profile.colors}.",
        f"Key distinctive features: {profile.distinctive_features}."
    ]
    return " ".join(parts)

def build_scene_prompt(profile: CharacterProfile, scene_description: str) -> str:
    master_char = get_master_prompt(profile)
    negative_rules = "No text, no letters, no typography, no watermarks, no speech bubbles, no distorted anatomy, maintain exact character identity and clothing."
    return f"{master_char} Action and setting: {scene_description}. Artistic style: {profile.art_style}. {negative_rules}"

def extract_fallback_character(prompt: str, target_age: str = "4-8 years") -> CharacterProfile:
    low = prompt.lower()
    name_match = re.search(r"named\s+([A-Za-z]+)", prompt, re.IGNORECASE)
    
    if "rabbit" in low or "bunny" in low:
        cname = name_match.group(1).capitalize() if name_match else "Barnaby"
        return CharacterProfile(
            name=cname,
            species_or_type="fluffy anthropomorphic bunny",
            age="young",
            face="round cheerful face with twitching pink nose, long floppy velvet ears, bright hazel eyes",
            hairstyle="soft honey-brown fur tuft between ears",
            skin_tone="warm caramel and cream fur",
            clothing="emerald green knitted vest over a pale linen shirt with tiny wooden buttons",
            colors="emerald green, cream, honey brown, soft terracotta",
            distinctive_features="oversized brass compass necklace and one ear slightly flopped over",
            art_style="whimsical storybook watercolor illustration, cozy children's picture book style, rich vibrant textures, clean outlines"
        )
    if "dragon" in low:
        cname = name_match.group(1).capitalize() if name_match else "Pip"
        return CharacterProfile(
            name=cname,
            species_or_type="gentle baby dragon",
            age="little dragon",
            face="wide curious amber eyes, small rounded snout, friendly beaming smile",
            hairstyle="tiny soft lavender crest running down back",
            skin_tone="soft mint-green scales with pastel turquoise underbelly",
            clothing="a cozy mustard-yellow scarf wrapped snugly around neck",
            colors="mint green, turquoise, mustard yellow, lavender",
            distinctive_features="tiny rounded wings with shimmering star patterns and two tiny pearl horns",
            art_style="charming children's book illustration, gouache and watercolor texture, warm gentle colors, no text"
        )
    if "bear" in low:
        cname = name_match.group(1).capitalize() if name_match else "Bruno"
        return CharacterProfile(
            name=cname,
            species_or_type="gentle little brown bear",
            age="young cub",
            face="round friendly bear face with warm dark brown eyes and a button nose",
            hairstyle="short fluffy chocolate brown fur with round fuzzy ears",
            skin_tone="warm honey-brown and caramel coat",
            clothing="red and blue plaid flannel shirt with rolled-up cuffs",
            colors="warm chocolate, honey brown, red, navy",
            distinctive_features="a tiny carved wooden acorn charm in pocket",
            art_style="whimsical picture book illustration, textured watercolor, soft glowing sunlight, clean character outlines"
        )
    if "fox" in low:
        cname = name_match.group(1).capitalize() if name_match else "Rusty"
        return CharacterProfile(
            name=cname,
            species_or_type="clever little red fox",
            age="young fox",
            face="pointed cheerful snout with bright amber eyes and a white chin",
            hairstyle="fluffy russet-orange fur tuft with white-tipped bushy tail",
            skin_tone="vibrant copper-orange and soft cream coat",
            clothing="cozy forest-green knitted sweater with wooden toggle buttons",
            colors="copper orange, cream, forest green, warm gold",
            distinctive_features="white-tipped bushy tail and bright curious eyes",
            art_style="whimsical storybook watercolor illustration, vibrant warm tones, clean outlines"
        )
    if "cat" in low or "kitten" in low:
        cname = name_match.group(1).capitalize() if name_match else "Milo"
        return CharacterProfile(
            name=cname,
            species_or_type="curious striped kitten",
            age="little kitten",
            face="wide sparkling green eyes, twitching white whiskers, perky pink ears",
            hairstyle="soft ginger and white tabby fur",
            skin_tone="warm ginger and cream striped coat",
            clothing="small teal bandana tied neatly around neck",
            colors="ginger orange, white, teal, golden yellow",
            distinctive_features="striped tail with white tip and expressive oversized eyes",
            art_style="charming picture book watercolor illustration, soft warm textures, clean outlines"
        )
    if "dog" in low or "puppy" in low:
        cname = name_match.group(1).capitalize() if name_match else "Toby"
        return CharacterProfile(
            name=cname,
            species_or_type="playful golden puppy",
            age="young pup",
            face="happy smiling muzzle with shiny black nose and floppy golden ears",
            hairstyle="fluffy golden fur with soft wavy texture",
            skin_tone="golden wheat and warm cream coat",
            clothing="bright red adventurer's vest with small brass pocket clips",
            colors="golden wheat, warm cream, bright red, navy blue",
            distinctive_features="ever-wagging tail and a tiny bronze paw badge on collar",
            art_style="whimsical picture book illustration, rich watercolor texture, warm joyful lighting"
        )
    if "boy" in low or "prince" in low or "brother" in low or "leo" in low:
        cname = name_match.group(1).capitalize() if name_match else "Leo"
        return CharacterProfile(
            name=cname,
            species_or_type="young adventurous boy",
            age="7 years old",
            face="expressive round face, rosy sun-kissed cheeks, big sparkling hazel eyes, warm adventurous smile",
            hairstyle="messy curly chestnut brown hair with a playful cowlick",
            skin_tone="warm olive skin tone",
            clothing="mustard-yellow hooded windbreaker, navy blue rolled-up trousers, sturdy brown hiking boots",
            colors="mustard yellow, navy blue, chestnut brown, forest green",
            distinctive_features="small constellation of freckles across the bridge of his nose and an orange canvas satchel",
            art_style="whimsical picture book illustration, soft textured watercolor, glowing warm lighting, clean character silhouettes"
        )
    char_name = name_match.group(1).capitalize() if name_match else "Lily"
    return CharacterProfile(
        name=char_name,
        species_or_type="curious young girl",
        age="7 years old",
        face="bright round curious face with expressive sparkling emerald green eyes and friendly rosy cheeks",
        hairstyle="two bouncy dark brown pigtails tied with bright sunshine-yellow ribbons",
        skin_tone="warm golden-fair complexion",
        clothing="soft sky-blue denim overalls over a sunny yellow striped long-sleeve cotton shirt, red canvas sneakers",
        colors="sky blue, sunshine yellow, crimson red, earthy olive",
        distinctive_features="a small brass magnifying glass on a cord around her neck and cheerful freckles on her cheeks",
        art_style="whimsical picture book illustration, rich watercolor and digital gouache, warm magical atmosphere, distinct storybook character"
    )

def generate_character_profile(prompt: str, target_age: str = "4-8 years", api_key: str | None = None) -> CharacterProfile:
    active_key = (api_key or os.getenv("OPEN_ROUTER_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")).strip()
    if not active_key:
        return extract_fallback_character(prompt, target_age)
    try:
        base_url = "https://openrouter.ai/api/v1" if active_key.startswith("sk-or-") else None
        model_name = "openai/gpt-4o-mini" if active_key.startswith("sk-or-") else "gpt-4o-mini"
        client = OpenAI(api_key=active_key, base_url=base_url, timeout=25.0)
        system_instruction = (
            "You are a master character designer for children's illustrated storybooks. "
            "Given a story prompt, design ONE single memorable main character. "
            "The design must be concrete, distinctive, and easily replicable across 5 illustrations. "
            "Return JSON matching the schema precisely: name, species_or_type, age, face, hairstyle, skin_tone, clothing, colors, distinctive_features, art_style."
        )
        response = client.chat.completions.create(
            model=model_name,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Create character profile for: {prompt}. Target age: {target_age}"}
            ],
            temperature=0.7
        )
        data = json.loads(response.choices[0].message.content)
        return CharacterProfile(
            name=data.get("name", "Pip"),
            species_or_type=data.get("species_or_type", "young child"),
            age=data.get("age", "7 years old"),
            face=data.get("face", "cheerful round face with bright eyes"),
            hairstyle=data.get("hairstyle", "neat wavy brown hair"),
            skin_tone=data.get("skin_tone", "warm fair skin"),
            clothing=data.get("clothing", "bright yellow raincoat and navy boots"),
            colors=data.get("colors", "yellow, navy blue, red"),
            distinctive_features=data.get("distinctive_features", "red star badge on pocket"),
            art_style=data.get("art_style", "whimsical children's picture book illustration, textured watercolor, vibrant colors, clean edges")
        )
    except Exception:
        return extract_fallback_character(prompt, target_age)
