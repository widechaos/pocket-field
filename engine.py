"""Local semantic selection of original outdoor activity cards."""
import os
import threading
from pathlib import Path

from sentence_transformers import SentenceTransformer

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"


def card(key, title, description, minutes, movement, places, steps, bring="Nothing"):
    return dict(id=key, title=title, description=description, minutes=minutes,
                movement=movement, places=places, steps=steps, bring=bring)


CARDS = [
    card("sound-map", "Make a sound map", "Listen to birds, wind and distant city sounds in a quiet outdoor spot. Map what you hear without identifying species.", 5, "still", ["park", "urban", "balcony"], ["Find a comfortable outdoor spot and put your screen away.", "Listen for a nearby sound, a distant sound, and one that changes.", "Draw three marks on paper in the directions they came from."], "Paper and pencil, optional"),
    card("color-five", "Find five greens", "Notice leaf colors and shades of green in plants. An easy visual nature observation, sitting or standing.", 5, "still", ["park", "balcony"], ["Choose one plant or a patch of leaves you can see.", "Find five different shades, from yellow-green to deep green.", "Choose a favorite shade. Leave the plant exactly as you found it."]),
    card("cloud-story", "Give a cloud a story", "Watch clouds move across the sky and imagine shapes. Quiet daydreaming outdoors with no walking needed.", 10, "still", ["park", "urban", "balcony"], ["Sit comfortably where you can see the sky without looking at the sun.", "Choose one cloud and give its shape a name.", "Watch it change, then invent its next chapter."]),
    card("shadow-sketch", "Sketch a moving shadow", "Draw the shadow of a leaf, railing or tree. Outdoor sketching, patterns and light, with pencil and paper.", 10, "still", ["park", "urban", "balcony"], ["Find a small shadow on a surface you may use.", "Sketch its outline on paper without touching the object.", "Wait a few minutes and add a second outline."], "Paper and pencil"),
    card("texture-walk", "Walk a texture trail", "A short easy walk noticing brick, bark, stone and pavement patterns. Explore city textures visually without collecting anything.", 10, "walk", ["park", "urban"], ["Pick a familiar, permitted path and put your phone away.", "Notice one smooth surface, one rough surface and one repeating pattern.", "Return by the same path and recall your three textures."]),
    card("bird-watch", "Watch one bird", "Observe a bird's behavior, posture and movement quietly from a distance. Birdwatching without species identification or feeding.", 10, "still", ["park", "balcony"], ["Settle in a permitted outdoor spot away from nesting birds.", "Watch one bird from a distance: how does it move or pause?", "Remember three observations. No bird today? Watch the trees instead."]),
    card("leaf-lines", "Follow a leaf's lines", "Look closely at leaf shapes, veins and edges without picking leaves. A tiny plant study, still and quiet.", 5, "still", ["park", "balcony"], ["Choose a reachable leaf on a plant you can observe without disturbing it.", "Trace its lines with your eyes, from stem to edge.", "Describe the shape in three words, then look away."]),
    card("friend-stroll", "Take a question for a walk", "An easy walk with a friend and a playful conversation. Social outdoor time with no screen prompts after starting.", 20, "walk", ["park", "urban"], ["Invite a friend for a short walk on a familiar path.", "Ask: what small thing surprised you this week?", "Listen, trade stories, and turn back halfway through."]),
    card("solo-stroll", "Walk without a destination", "A gentle solo wander on a familiar path. Notice your surroundings instead of optimizing routes or checking a phone.", 20, "walk", ["park", "urban"], ["Choose a familiar permitted path and a turnaround point.", "Walk at your own comfortable pace and notice something you usually pass.", "Turn back halfway through. Let one detail stay with you."]),
    card("garden-check", "Meet a garden's changes", "Observe your own garden or balcony plants. Notice new growth, dry soil and leaf changes; no pesticide or watering prescription.", 10, "still", ["balcony", "park"], ["Look at one plant you own or may observe.", "Notice one new shoot, one leaf change and the soil's appearance.", "Make a one-line note of what changed; check care needs separately."], "Paper and pencil, optional"),
    card("tiny-sketch", "Draw a tiny landscape", "Make a small pencil sketch of a park, courtyard or balcony view. Creative outdoor art without taking photos.", 20, "still", ["park", "urban", "balcony"], ["Sit at a comfortable outdoor spot with a view.", "Draw only five lines that capture the scene.", "Add one detail you would not have noticed from a photograph."], "Paper and pencil"),
    card("city-tree", "Find your neighborhood tree", "Take a short walk to observe a tree on a familiar street. Notice urban nature without identifying or collecting plants.", 10, "walk", ["urban", "park"], ["Choose a familiar nearby street or path with a tree.", "Look at its outline from a permitted walkway, without crossing hazards.", "Notice how it changes the space around it, then head home."]),
    card("horizon", "Find the furthest thing", "A quiet outdoor visual observation from a seat. Compare nearby and distant shapes and look away from a screen.", 5, "still", ["park", "urban", "balcony"], ["Sit comfortably outside with a view.", "Notice the closest object, then the furthest shape you can make out.", "Find something in between. Keep your gaze away from the sun."]),
    card("pattern-poem", "Write a three-line field note", "Write an outdoor poem about one sound, one color and one movement. Creative writing in nature on paper.", 10, "still", ["park", "urban", "balcony"], ["Settle outside with a scrap of paper.", "Write one line for a sound, one for a color, one for movement.", "Leave the note unfinished if you like. Put the pencil down and stay a little."], "Paper and pencil"),
    card("weather-notice", "Notice air in motion", "Observe a breeze moving leaves or fabric. Quiet nature watching outdoors without a weather forecast.", 5, "still", ["park", "urban", "balcony"], ["Find a comfortable outdoor place.", "Notice a leaf or piece of fabric moving with the air.", "Look for another object moving differently. Stay still for a moment."]),
    card("revisit", "Visit the same spot twice", "A longer easy walk observing changes in light, people and nature. Compare a familiar scene before and after a loop.", 30, "walk", ["park", "urban"], ["Pick a familiar short loop and a starting landmark.", "Notice three details at the landmark, then walk your loop comfortably.", "Return and see which details changed. Stop when you choose."]),
]


class Selector:
    def __init__(self):
        cache = os.environ.get("POCKET_FIELD_CACHE")
        self.model = SentenceTransformer(MODEL_ID, revision=REVISION, device="cpu",
            cache_folder=cache, local_files_only=os.environ.get("HF_HUB_OFFLINE") == "1",
            trust_remote_code=False)
        self.vectors = self.model.encode([c["description"] for c in CARDS], normalize_embeddings=True)
        self.lock = threading.Lock()

    def select(self, query, minutes=10, movement="any", place="any"):
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Tell me what you feel like doing outside.")
        query = query.strip()
        if len(query) > 600 or len(self.model.tokenizer.encode(query)) > 256:
            raise ValueError("Keep your request short: at most 600 characters and 256 model tokens.")
        if not isinstance(minutes, int) or isinstance(minutes, bool) or minutes not in (5, 10, 20, 30):
            raise ValueError("Choose 5, 10, 20 or 30 minutes.")
        if movement not in ("any", "still", "walk") or place not in ("any", "park", "urban", "balcony"):
            raise ValueError("Choose one of the available settings.")
        candidates = [(i, c) for i, c in enumerate(CARDS) if c["minutes"] <= minutes
            and (movement == "any" or movement == c["movement"])
            and (place == "any" or place in c["places"])]
        if not candidates:
            return dict(matches=[], reason="No card fits those settings. Try more time or staying still.")
        with self.lock:
            vector = self.model.encode(query, normalize_embeddings=True)
        ranked = sorted([(float(vector @ self.vectors[i]), c) for i, c in candidates],
                        key=lambda item: item[0], reverse=True)
        if ranked[0][0] < 0.20:
            return dict(matches=[], reason="I could not match that to an outdoor activity. Try listening, sketching, plants or a gentle walk.")
        return dict(matches=[dict(c, score=round(score, 4)) for score, c in ranked[:3]],
                    reason="Semantic matches within your time, place and movement settings.")


def text_card(c):
    return (f"POCKET FIELD\n{c['title']}\n{c['minutes']} minutes · {c['movement']}\n"
            f"Bring: {c['bring']}\n\n" + "\n".join(f"{i}. {s}" for i, s in enumerate(c["steps"], 1))
            + "\n\nChoose a familiar permitted place and conditions that are comfortable for you.\n"
            + "No route, weather, medical or species-identification advice.\n\nClose the screen. The rest happens outside.\n")
