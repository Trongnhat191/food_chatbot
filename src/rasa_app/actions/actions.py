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
        # Lấy toàn bộ câu chat của người dùng (bao gồm cả phần "cho 4 người")
        query = tracker.latest_message.get('text').lower() 
        pref = tracker.get_slot("preference")
        
        # Gọi engine - Engine bây giờ đã có prompt mới để xử lý số người
        full_text = get_rag_recipe(query, pref)
        
        if not full_text:
            dispatcher.utter_message(text="Rất tiếc, mình chưa tìm thấy thông tin này.")
            return []

        if '|' in full_text:
            steps = [s.strip() for s in full_text.split('|') if s.strip()]
            
            # Logic kiểm tra xem tất cả (giữ nguyên của Minh)
            keywords_show_all = ["hết", "tất cả", "toàn bộ", "full"]
            if any(word in query for word in keywords_show_all):
                full_recipe = "\n".join([f"• {s}" for s in steps])
                dispatcher.utter_message(text=f"Vâng, đây là công thức đã được điều chỉnh phù hợp:\n\n{full_recipe}")
                return [SlotSet("recipe_steps", steps), SlotSet("current_step_index", 0)]

            # Hiện bước 1
            dispatcher.utter_message(text=f"Tìm thấy rồi! Đây là bước đầu tiên:\n{steps[0]}")
            dispatcher.utter_message(text="Bạn gõ 'tiếp' để xem bước sau hoặc 'hiện hết' nhé.")
            return [SlotSet("recipe_steps", steps), SlotSet("current_step_index", 0)]
        
        dispatcher.utter_message(text=f"Dưới đây là một số gợi ý cho bạn:\n{full_text}")
        return [SlotSet("recipe_steps", None)]

class ActionShowFullRecipe(Action):
    def name(self) -> Text: return "action_show_full_recipe"

    def run(self, dispatcher, tracker, domain):
        steps = tracker.get_slot("recipe_steps")
        if not steps:
            dispatcher.utter_message(text="Bạn chưa chọn món nào để xem toàn bộ công thức cả.")
            return []
        
        full_recipe = "\n".join([f"• {s}" for s in steps])
        dispatcher.utter_message(text=f"Đây là toàn bộ quy trình:\n{full_recipe}")
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