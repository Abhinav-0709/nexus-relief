import math

class ReliefMap:
    def __init__(self, grid_size=10):
        self.grid_size = grid_size
        self.red_zones = []
        self.drones = [
            {'id': 'Alpha', 'pos': (0, 0), 'fuel': 100, 'status': 'IDLE'},
            {'id': 'Beta', 'pos': (9, 9), 'fuel': 100, 'status': 'IDLE'},
            {'id': 'Gamma', 'pos': (5, 0), 'fuel': 100, 'status': 'IDLE'}
        ]
        self.hubs = [(0, 0), (9, 9), (0, 9), (9, 0)]
        
        # --- NEW: Performance Metrics ---
        self.stats = {
            "total_moves": 0,
            "total_fuel_consumed": 0,
            "zones_cleared": 0,
            "refuel_count": 0
        }

    def add_zone(self, x, y, severity=5):
        if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
            self.red_zones.append({'coords': (x, y), 'severity': severity})
            return f"Zone added at ({x}, {y})"
        return "Coordinates out of bounds."

    def move_drone(self, drone_id, target_x, target_y):
        drone = next((d for d in self.drones if d['id'] == drone_id), None)
        if not drone: return "Drone not found"
        
        if drone['fuel'] <= 0:
            return f"{drone_id} is out of fuel!"

        # Calculate Movement
        dx = target_x - drone['pos'][0]
        dy = target_y - drone['pos'][1]
        
        step_x = 1 if dx > 0 else -1 if dx < 0 else 0
        step_y = 1 if dy > 0 else -1 if dy < 0 else 0
        
        # Update Position
        new_x, new_y = drone['pos']
        moved = False
        
        # Only move if not already there
        if step_x != 0:
            new_x += step_x
            moved = True
        elif step_y != 0:
            new_y += step_y
            moved = True
            
        if moved:
            drone['pos'] = (new_x, new_y)
            drone['fuel'] -= 5
            
            # Update Stats
            self.stats["total_moves"] += 1
            self.stats["total_fuel_consumed"] += 5
        
        # Check for Zone Clear
        for zone in self.red_zones:
            if zone['coords'] == drone['pos']:
                self.red_zones.remove(zone)
                self.stats["zones_cleared"] += 1
                return f"✅ {drone_id} EXTINGUISHED fire at {drone['pos']}!"
                
        # Check for Refuel
        if drone['pos'] in self.hubs and drone['fuel'] < 100:
            drone['fuel'] = 100
            self.stats["refuel_count"] += 1
            return f"⛽ {drone_id} refueled at Hub."

        return f"{drone_id} moved to {drone['pos']}. Fuel: {drone['fuel']}"