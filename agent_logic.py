import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# 1. Configuration
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ Error: GOOGLE_API_KEY not found in .env")
else:
    genai.configure(api_key=api_key)

def get_commander_decision(drones, zones, hubs, user_override=""):
    """
    Sends the current map state to Gemini and asks for tactical decisions.
    Now supports Human-in-the-Loop overrides.
    """
    
    # 2. Prepare the Situation Report
    situation_text = f"""
    Current Map Status:
    - Active Red Zones (Emergencies): {zones}
    - Refuel Hubs: {hubs}
    - Drone Squad Status: {drones}
    """

    # Inject Human Command if present
    if user_override:
        situation_text += f"\n\n🚨 URGENT PRIORITY ORDER FROM HUMAN COMMANDER: {user_override}\n(You MUST adjust your strategy to follow this order, even if it contradicts standard rules.)"

    # 3. The System Prompt
    system_instruction = """
    You are the Autonomous Disaster Relief Commander.
    
    GOAL: Clear Red Zones efficiently. Keep Drones alive.
    
    STANDARD RULES (Apply unless overridden):
    1. If Drone Fuel < 20 -> MUST return to nearest Hub.
    2. If Drone is Idle -> Send to nearest Red Zone.
    3. Conflict Resolution -> Do not send multiple drones to the same target unless necessary.
    
    OUTPUT FORMAT:
    Return strictly a JSON object with this structure:
    {
        "reasoning": "A brief tactical explanation of your moves (e.g. 'Alpha is refueling, Beta taking the fire')",
        "moves": {
            "DroneID_1": [x, y],
            "DroneID_2": [x, y]
        }
    }
    """

    # 4. Call Gemini
    try:
        # We use the generic model. You can change this to 'gemini-2.0-flash' if available.
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # specific instruction to force JSON since we aren't using json_mode config
        full_prompt = system_instruction + "\n" + situation_text + "\n\nReply ONLY with the JSON."
        
        response = model.generate_content(full_prompt)
        
        # Debug: Print raw response to terminal to see what AI is thinking
        # print(f"🤖 RAW AI: {response.text}") 

        # 5. Clean and Parse JSON
        # This handles cases where AI adds ```json ... ``` markdown
        clean_text = response.text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
            
        decision_plan = json.loads(clean_text)
        return decision_plan
        
    except Exception as e:
        print(f"❌ AI COMMANDER ERROR: {e}")
        # Return empty object so app doesn't crash
        return {}