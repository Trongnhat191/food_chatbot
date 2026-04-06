from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import sys
import os

# Đảm bảo import được các module trong src/
sys.path.append(os.path.join(os.getcwd(), "src"))
from chat.engine import get_rag_recipe

class ActionRecipeSearch(Action):
    def name(self) -> Text: return "action_recipe_search"

    def run(self, dispatcher, tracker, domain):
        query = tracker.latest_message.get('text')
        pref = tracker.get_slot("preference")

        # Hướng A & C: Gọi RAG với sở thích
        full_text = get_rag_recipe(query, pref)
        
        if not full_text:
            dispatcher.utter_message(text="Rất tiếc, mình chưa tìm thấy công thức này.")
            return []

        # Hướng B: Tách steps từ dấu gạch đứng '|'
        steps = [s.strip() for s in full_text.split('|') if s.strip()]
        
        if steps:
            dispatcher.utter_message(text=f"Tìm thấy rồi! {steps[0]}")
            return [SlotSet("recipe_steps", steps), SlotSet("current_step_index", 0)]
        
        dispatcher.utter_message(text=full_text)
        return []

class ActionNextStep(Action):
    def name(self) -> Text: return "action_next_step"

    def run(self, dispatcher, tracker, domain):
        steps = tracker.get_slot("recipe_steps")
        idx = int(tracker.get_slot("current_step_index") or 0)

        if not steps:
            dispatcher.utter_message(text="Bạn hãy chọn một món ăn trước nhé.")
            return []

        if idx + 1 < len(steps):
            new_idx = idx + 1
            dispatcher.utter_message(text=f"Tiếp theo, {steps[new_idx]}")
            return [SlotSet("current_step_index", new_idx)]
        
        dispatcher.utter_message(text="Bạn đã hoàn thành món ăn rồi! Chúc ngon miệng.")
        return [SlotSet("recipe_steps", None), SlotSet("current_step_index", 0)]
    
class ActionPrevStep(Action):
    def name(self) -> Text: return "action_prev_step"

    def run(self, dispatcher, tracker, domain):
        steps = tracker.get_slot("recipe_steps")
        idx = int(tracker.get_slot("current_step_index") or 0)

        if not steps:
            dispatcher.utter_message(text="Bạn chưa chọn món ăn nào cả.")
            return []

        if idx > 0:
            new_idx = idx - 1
            dispatcher.utter_message(text=f"Quay lại bước {new_idx + 1}: {steps[new_idx]}")
            return [SlotSet("current_step_index", new_idx)]
        else:
            dispatcher.utter_message(text="Đây đã là bước đầu tiên rồi.")
            return []    