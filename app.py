import streamlit as st
import pydeck as pdk
import pandas as pd
import time
from simulation import ReliefMap
from agent_logic import get_commander_decision

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="Nexus Relief Ops")

# 2. Initialize Session State (Memory)
if 'map_state' not in st.session_state:
    st.session_state.map_state = ReliefMap()
    # Add initial test zones
    st.session_state.map_state.add_zone(2, 2)
    st.session_state.map_state.add_zone(8, 8)

if 'mission_logs' not in st.session_state:
    st.session_state.mission_logs = []

world = st.session_state.map_state

# 3. Sidebar - Command Center
st.sidebar.header("🛰️ Satellite Command")

# --- Mission Log (Persisted) ---
if st.session_state.mission_logs:
    st.sidebar.markdown("### 📜 Mission Log")
    # Show last 3 logs to keep it clean
    for msg in st.session_state.mission_logs[:3]:
        st.sidebar.info(msg)
    
    if st.sidebar.button("Clear Logs"):
        st.session_state.mission_logs = []
        st.rerun()

st.sidebar.markdown("---")

# --- Tool: Report New Incident ---
st.sidebar.subheader("📍 Report Incident")
new_zone_input = st.sidebar.text_input("Coordinates (x,y)", placeholder="e.g., 5,5")
if st.sidebar.button("Dispatch Alert"):
    try:
        x, y = map(int, new_zone_input.split(','))
        log = st.session_state.map_state.add_zone(x, y)
        st.sidebar.warning(log)
        st.rerun()
    except ValueError:
        st.sidebar.error("Invalid Format. Use x,y (e.g., 5,5)")

st.sidebar.markdown("---")

# --- Human-in-the-Loop Override ---
st.sidebar.subheader("📡 Override Channel")
human_order = st.sidebar.text_input("Message to Squad:", placeholder="e.g., Alpha, ignore fire and refuel!")

# --- Main AI Loop ---
if st.sidebar.button("Execute AI Turn", type="primary"):
    with st.spinner("Commander AI is analyzing tactics..."):
        # 1. Gather Data
        current_drones = st.session_state.map_state.drones
        current_zones = st.session_state.map_state.red_zones
        hubs = st.session_state.map_state.hubs
        
        # 2. Ask the Brain (Layer 3)
        # We pass the human_order to the AI
        plan = get_commander_decision(current_drones, current_zones, hubs, user_override=human_order)
        
        if not plan:
            st.sidebar.error("⚠️ Radio Silence (AI Error). Check Terminal.")
        else:
            # EXTRACT DATA from JSON
            reasoning = plan.get("reasoning", "No commentary provided.")
            moves = plan.get("moves", {})

            # 3. Execute Moves (Layer 2)
            turn_logs = []
            for drone_id, target in moves.items():
                result = st.session_state.map_state.move_drone(drone_id, target[0], target[1])
                turn_logs.append(result)
            
            # 4. Save to History
            timestamp = time.strftime("%H:%M:%S")
            log_entry = f"**[{timestamp}] 🧠 COMMANDER:** {reasoning}\n"
            for action in turn_logs:
                log_entry += f"- {action}\n"
            
            # Insert at top
            st.session_state.mission_logs.insert(0, log_entry)
            
            # Force refresh to update map
            st.rerun()

# 4. Main Interface - Map Visualization
st.title("Nexus Relief: Autonomous Drone Network")

# Data Prep for PyDeck
df_drones = pd.DataFrame([d['pos'] + (d['id'],) for d in world.drones], columns=['x', 'y', 'id'])
df_zones = pd.DataFrame([z['coords'] for z in world.red_zones], columns=['x', 'y'])
df_hubs = pd.DataFrame(world.hubs, columns=['x', 'y'])

# Grid to Lat/Lon Configuration
BASE_LAT = 37.7749
BASE_LON = -122.4194
SCALE = 0.005

def grid_to_latlon(df):
    if df.empty: return df
    df['lat'] = BASE_LAT + (df['y'] * SCALE)
    df['lon'] = BASE_LON + (df['x'] * SCALE)
    return df

# Apply conversion
df_drones = grid_to_latlon(df_drones)
df_zones = grid_to_latlon(df_zones)
df_hubs = grid_to_latlon(df_hubs)

# PyDeck Layers
layers = []

# Layer 1: Hubs (Blue Squares)
if not df_hubs.empty:
    layers.append(pdk.Layer(
        "ScatterplotLayer",
        df_hubs,
        get_position='[lon, lat]',
        get_color=[0, 0, 255, 140],
        get_radius=200,
        pickable=True,
        auto_highlight=True
    ))

# Layer 2: Red Zones (Red Pulses)
if not df_zones.empty:
    layers.append(pdk.Layer(
        "ScatterplotLayer",
        df_zones,
        get_position='[lon, lat]',
        get_color=[255, 0, 0, 200],
        get_radius=300,
        pickable=True,
        auto_highlight=True
    ))

# Layer 3: Drones (Green Dots)
if not df_drones.empty:
    layers.append(pdk.Layer(
        "ScatterplotLayer",
        df_drones,
        get_position='[lon, lat]',
        get_color=[0, 255, 0, 255],
        get_radius=150,
        pickable=True,
        auto_highlight=True
    ))
    
    # Layer 4: Drone Labels (Text)
    # Offset text slightly above the dot
    df_drones['lat_text'] = df_drones['lat'] + (0.5 * SCALE)
    layers.append(pdk.Layer(
        "TextLayer",
        df_drones,
        pickable=False,
        get_position='[lon, lat_text]',
        get_text='id',
        get_color=[0, 0, 0],
        get_size=15,
        get_alignment_baseline="'bottom'",
        get_background_color=[255, 255, 255, 200], # White background for readability
        background=True 
    ))

# Render Map
st.pydeck_chart(pdk.Deck(
    map_style=None,
    initial_view_state=pdk.ViewState(
        latitude=BASE_LAT + (5 * SCALE),
        longitude=BASE_LON + (5 * SCALE),
        zoom=11,
        pitch=0,
    ),
    layers=layers,
    tooltip={"text": "{id}"}
))

# 5. Live Telemetry Dashboard
st.markdown("---")
st.subheader("📊 Mission Analytics")

m1, m2, m3, m4 = st.columns(4)
stats = st.session_state.map_state.stats

with m1:
    st.metric("Zones Cleared", stats["zones_cleared"], delta_color="normal")
with m2:
    st.metric("Fuel Consumed", f"{stats['total_fuel_consumed']} L", delta="-5" if stats["total_fuel_consumed"] > 0 else "0")
with m3:
    st.metric("Total Manuevers", stats["total_moves"])
with m4:
    st.metric("Refuel Stops", stats["refuel_count"])

st.caption(f"System Online | Active Drones: {len(world.drones)} | Grid Size: 10x10")