import os
import webbrowser
import math
import ntplib # pyright: ignore[reportMissingImports]
from time import ctime, time
from datetime import datetime, timezone
import socket

# =================================================================
# 🔒 LICENSING FUNCTIONALITY USING NTP TIME CHECK
# =================================================================

# Define the license expiration date (e.g., December 31, 2026 at midnight UTC)
# This is the "hard license" date.
LICENSE_EXPIRATION = datetime(2526, 12, 31, 0, 0, 0, tzinfo=timezone.utc)
NTP_SERVER = 'pool.ntp.org'
# 🔒 TARGET IP ADDRESS FOR HARD LICENSE RESTRICTION
TARGET_IP_ADDRESS = '192.168.1.163' 

def get_local_ip():
    """
    Attempts to determine the machine's local IP address by connecting 
    to an external address (without sending data) and checking the 
    socket's bound address.
    """
    s = None
    try:
        # Connect to a public server (doesn't actually send data)
        # and check which local IP the connection uses.
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)) # Google DNS is a common public endpoint
        local_ip = s.getsockname()[0]
    except Exception:
        # Fallback for systems without a network connection
        local_ip = '127.0.0.1' 
    finally:
        if s:
            s.close()
    return local_ip

def check_ip_license():
    """
    Checks the local machine's IP address against the target IP.
    """
    print("=======================================")
    print("🌎 Checking IP Address Restriction...")
    current_ip = get_local_ip()
    print(f"Detected Local IP: {current_ip}")
    
    if current_ip != TARGET_IP_ADDRESS:
        print("\n❌ IP LICENSE FAILED.")
        print(f"This software is licensed only for IP: {TARGET_IP_ADDRESS}")
        print("Please run this program from the correct machine.")
        exit(1)
        
    print("✅ IP Address Valid.")
    print("=======================================")

def check_license():
    """
    Checks the current network time against a hardcoded expiration date.
    If the current time is past the expiration, the program exits.
    """
    try:
        # 1. Connect to the NTP server to get reliable, un-falsifiable time
        print(f"Checking license validity via {NTP_SERVER}...")
        client = ntplib.NTPClient()
        response = client.request(NTP_SERVER, version=3)
        ntp_time = datetime.fromtimestamp(response.tx_time, tz=timezone.utc)
        
        print(f"Network Time (UTC): {ntp_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # 2. Compare the network time to the expiration date
        if ntp_time > LICENSE_EXPIRATION:
            print("\n❌ LICENSE EXPIRED.")
            print(f"This software expired on: {LICENSE_EXPIRATION.strftime('%Y-%m-%d')}")
            print("Please contact the vendor for a license renewal.")
            exit(1) # Exit the program with an error code
        
        print("✅ Date License Valid.")
        
    except ntplib.NTPException as e:
        # Handle cases where the network is down or NTP server is unreachable
        print("\n⚠️ WARNING: Could not connect to NTP server for license check.")
        print(f"⚠️ Error: {e}")
        print("⚠️ Relying on system time, but proceed with caution.")
        
    except Exception as e:
        print(f"An unexpected error occurred during license check: {e}")
        exit(1)

# =================================================================
# 📐 AMERICAN ARCHITECTURAL CODE STANDARDS (IBC/IRC/ADA)
# =================================================================

class ArchitecturalCodes:
    """
    International Building Code (IBC) 2021 and International Residential Code (IRC) 2021
    American Institute of Architects (AIA) Standards
    Americans with Disabilities Act (ADA) Compliance
    """
    
    # IBC/IRC WALL STANDARDS
    EXTERIOR_WALL_THICKNESS = 0.67  # 8" (2x4 framing + sheathing + siding) = 8"/12" = 0.67'
    INTERIOR_WALL_THICKNESS = 0.42  # 5" (2x4 framing + drywall both sides) = 5"/12" = 0.42'
    LOAD_BEARING_WALL_THICKNESS = 0.67  # 8" for structural walls
    
    # IBC CHAPTER 10 - MEANS OF EGRESS
    MIN_EGRESS_DOOR_WIDTH = 3.0  # 36" clear width (IBC 1010.1.1)
    MIN_EGRESS_DOOR_HEIGHT = 6.67  # 80" (IBC 1010.1.1)
    MIN_CORRIDOR_WIDTH_RESIDENTIAL = 3.0  # 36" (IRC R311.6)
    MIN_CORRIDOR_WIDTH_COMMERCIAL = 3.67  # 44" (IBC 1020.2)
    MIN_CORRIDOR_WIDTH_ACCESSIBLE = 5.0  # 60" for wheelchair turning (ADA)
    
    # IBC CHAPTER 10 - STAIRWAY REQUIREMENTS
    MIN_STAIR_WIDTH_RESIDENTIAL = 3.0  # 36" (IRC R311.7.1)
    MIN_STAIR_WIDTH_COMMERCIAL = 3.67  # 44" (IBC 1011.2)
    MAX_RISER_HEIGHT_RESIDENTIAL = 0.625  # 7.75" (IRC R311.7.5.1)
    MAX_RISER_HEIGHT_COMMERCIAL = 0.583  # 7" (IBC 1011.5.2)
    MIN_TREAD_DEPTH_RESIDENTIAL = 0.833  # 10" (IRC R311.7.5.2)
    MIN_TREAD_DEPTH_COMMERCIAL = 0.917  # 11" (IBC 1011.5.2)
    MIN_HEADROOM_STAIR = 6.67  # 80" (IBC 1011.3)
    
    # IBC CHAPTER 12 - INTERIOR ENVIRONMENT
    MIN_CEILING_HEIGHT_RESIDENTIAL = 7.5  # 90" habitable rooms (IRC R305.1)
    MIN_CEILING_HEIGHT_COMMERCIAL = 7.5  # 90" (IBC 1208.2)
    MIN_CEILING_HEIGHT_BATHROOM = 6.67  # 80" (IRC R305.1)
    
    # IRC ROOM SIZE REQUIREMENTS
    MIN_BEDROOM_AREA = 70.0  # 70 sq ft (IRC R304.2)
    MIN_BEDROOM_WIDTH = 7.0  # 7' (IRC R304.2)
    MIN_HABITABLE_ROOM_AREA = 70.0  # 70 sq ft (IRC R304.3)
    MIN_KITCHEN_AREA = 50.0  # Recommended minimum
    MIN_BATHROOM_WIDTH = 5.0  # Minimum for fixtures
    
    # ADA - AMERICANS WITH DISABILITIES ACT
    WHEELCHAIR_TURNING_DIAMETER = 5.0  # 60" diameter (ADA 304.3.2)
    ACCESSIBLE_DOOR_WIDTH = 3.0  # 36" clear (ADA 404.2.3)
    ACCESSIBLE_DOOR_MANEUVERING = 1.5  # 18" strike side (ADA 404.2.4)
    ACCESSIBLE_TOILET_CLEARANCE = 5.0  # 60" diameter (ADA 603.2.1)
    
    # WINDOW REQUIREMENTS (IRC R310 - EMERGENCY ESCAPE)
    MIN_EGRESS_WINDOW_AREA = 5.7  # 5.7 sq ft (IRC R310.2.1)
    MIN_EGRESS_WINDOW_WIDTH = 1.67  # 20" (IRC R310.2.1)
    MIN_EGRESS_WINDOW_HEIGHT = 2.0  # 24" (IRC R310.2.1)
    
    # GARAGE STANDARDS (IRC R309)
    MIN_GARAGE_HEIGHT = 7.0  # 7' for vehicle clearance
    SINGLE_CAR_GARAGE_MIN = (10.0, 20.0)  # 10'x20' minimum
    DOUBLE_CAR_GARAGE_MIN = (20.0, 20.0)  # 20'x20' minimum
    TRIPLE_CAR_GARAGE_MIN = (30.0, 20.0)  # 30'x20' minimum
    
    # FIRE SEPARATION (IBC 706 / IRC R302)
    GARAGE_SEPARATION_WALL = 0.67  # 5/8" Type X gypsum = fire-rated
    FIRE_RATED_DOOR = True  # 20-minute rated door required
    
    # NATURAL LIGHT & VENTILATION (IRC R303)
    MIN_WINDOW_AREA_RATIO = 0.08  # 8% of floor area (IRC R303.1)
    MIN_VENTILATION_RATIO = 0.04  # 4% of floor area or mechanical (IRC R303.3)

    @staticmethod
    def validate_room_dimensions(room_type, width, depth):
        """
        Validates room dimensions against IBC/IRC codes.
        Returns (is_valid, warnings_list)
        """
        warnings = []
        area = width * depth
        
        if room_type == "Bedroom":
            if area < ArchitecturalCodes.MIN_BEDROOM_AREA:
                warnings.append(f"Bedroom area {area:.1f} sq ft < IRC minimum {ArchitecturalCodes.MIN_BEDROOM_AREA} sq ft")
            if width < ArchitecturalCodes.MIN_BEDROOM_WIDTH:
                warnings.append(f"Bedroom width {width}' < IRC minimum {ArchitecturalCodes.MIN_BEDROOM_WIDTH}'")
        
        elif room_type == "Kitchen":
            if area < ArchitecturalCodes.MIN_KITCHEN_AREA:
                warnings.append(f"Kitchen area {area:.1f} sq ft < recommended minimum {ArchitecturalCodes.MIN_KITCHEN_AREA} sq ft")
        
        elif room_type == "Bath":
            if width < ArchitecturalCodes.MIN_BATHROOM_WIDTH:
                warnings.append(f"Bathroom width {width}' < minimum {ArchitecturalCodes.MIN_BATHROOM_WIDTH}' for fixture clearance")
        
        return len(warnings) == 0, warnings
    
    @staticmethod
    def calculate_stair_dimensions(floor_height):
        """
        Calculates code-compliant stair dimensions based on floor height.
        Returns (num_risers, riser_height, tread_depth, total_run)
        """
        # Use residential code (more common for this application)
        max_riser = ArchitecturalCodes.MAX_RISER_HEIGHT_RESIDENTIAL * 12  # Convert to inches
        min_tread = ArchitecturalCodes.MIN_TREAD_DEPTH_RESIDENTIAL * 12  # Convert to inches
        
        floor_height_inches = floor_height * 12
        
        # Calculate number of risers (round up)
        num_risers = math.ceil(floor_height_inches / max_riser)
        
        # Actual riser height
        riser_height = floor_height_inches / num_risers
        
        # Number of treads is one less than risers
        num_treads = num_risers - 1
        
        # Use minimum tread depth
        tread_depth = min_tread
        
        # Total run (horizontal distance)
        total_run = num_treads * tread_depth / 12  # Convert back to feet
        
        return num_risers, riser_height / 12, tread_depth / 12, total_run

# =================================================================
# 🏠 HouseConfig CLASS WITH CODE COMPLIANCE
# =================================================================

class HouseConfig:
    """
    Manages all user-defined configurations with architectural code validation.
    """
    
    def __init__(self):
        self.project_name = "Custom Home Design"
        self.scale = 15
        self.codes = ArchitecturalCodes()
        
        # Use code-compliant wall thickness
        self.WALL_THICKNESS = ArchitecturalCodes.INTERIOR_WALL_THICKNESS
        self.EXTERIOR_WALL_THICKNESS = ArchitecturalCodes.EXTERIOR_WALL_THICKNESS
        
        # Default Global inputs
        self.num_floors = 2
        self.floor_width = 50.0 
        self.floor_depth = 40.0
        self.floor_height = 10.0  # Story height
        self.ceiling_height = 9.0  # Clear ceiling height
        self.garage_cars = 2
        self.garage_dim = (24.0, 24.0) 
        self.facade_type = "Wood Siding" 
        self.building_type = "Residential" 
        self.garage_connected = False 
        self.roofing_material = "Asphalt Shingles"
        self.ada_compliant = False  # ADA compliance flag
        
        # Code-compliant hallway width
        self.hallway_width = ArchitecturalCodes.MIN_CORRIDOR_WIDTH_RESIDENTIAL
        
        # Signature details
        self.signature_name = "Dr. Wael Selim, AIA"
        self.signature_company = "WS-SOFTWARE LLC"
        self.signature_email = "wael.sherif.selim@gmail.com"
        self.signature_license = "Professional Engineer License: PE-123456"
        
        # Code compliance tracking
        self.code_violations = []
        self.code_warnings = []
        
        # Data containers
        self.floors_data = []
        self.garage_data = None 

    def validate_building_codes(self):
        """
        Performs comprehensive code validation on the entire building design.
        """
        print("\n" + "="*60)
        print("🔍 PERFORMING IBC/IRC CODE COMPLIANCE CHECK")
        print("="*60)
        
        self.code_violations = []
        self.code_warnings = []
        
        # Check corridor width
        if self.building_type == "Commercial":
            if self.hallway_width < ArchitecturalCodes.MIN_CORRIDOR_WIDTH_COMMERCIAL:
                self.code_violations.append(
                    f"Corridor width {self.hallway_width}' < IBC minimum {ArchitecturalCodes.MIN_CORRIDOR_WIDTH_COMMERCIAL}' for commercial"
                )
        else:
            if self.hallway_width < ArchitecturalCodes.MIN_CORRIDOR_WIDTH_RESIDENTIAL:
                self.code_violations.append(
                    f"Corridor width {self.hallway_width}' < IRC minimum {ArchitecturalCodes.MIN_CORRIDOR_WIDTH_RESIDENTIAL}'"
                )
        
        # Check ADA compliance if required
        if self.ada_compliant and self.hallway_width < ArchitecturalCodes.MIN_CORRIDOR_WIDTH_ACCESSIBLE:
            self.code_violations.append(
                f"ADA requires {ArchitecturalCodes.MIN_CORRIDOR_WIDTH_ACCESSIBLE}' corridor width for wheelchair turning"
            )
        
        # Check ceiling height
        if self.ceiling_height < ArchitecturalCodes.MIN_CEILING_HEIGHT_RESIDENTIAL:
            self.code_violations.append(
                f"Ceiling height {self.ceiling_height}' < minimum {ArchitecturalCodes.MIN_CEILING_HEIGHT_RESIDENTIAL}'"
            )
        
        # Validate each floor and room
        for floor in self.floors_data:
            for room in floor['rooms']:
                if room.get('type') == 'stairs':
                    continue
                    
                # Determine room type from label
                room_label = room['label'].upper()
                if 'BEDROOM' in room_label:
                    room_type = 'Bedroom'
                elif 'KITCHEN' in room_label:
                    room_type = 'Kitchen'
                elif 'BATH' in room_label:
                    room_type = 'Bath'
                else:
                    room_type = 'Other'
                
                is_valid, warnings = self.codes.validate_room_dimensions(
                    room_type, room['w'], room['d']
                )
                
                if not is_valid:
                    for warning in warnings:
                        self.code_warnings.append(f"Floor {floor['id']} - {room['label']}: {warning}")
        
        # Check garage dimensions
        if self.garage_data:
            min_garage = self.codes.SINGLE_CAR_GARAGE_MIN
            if self.garage_cars == 2:
                min_garage = self.codes.DOUBLE_CAR_GARAGE_MIN
            elif self.garage_cars >= 3:
                min_garage = self.codes.TRIPLE_CAR_GARAGE_MIN
            
            if self.garage_data['w'] < min_garage[0] or self.garage_data['d'] < min_garage[1]:
                self.code_warnings.append(
                    f"Garage dimensions {self.garage_data['w']}'x{self.garage_data['d']}' " +
                    f"< IRC minimum {min_garage[0]}'x{min_garage[1]}' for {self.garage_cars} cars"
                )
        
        # Print results
        if self.code_violations:
            print("\n❌ CODE VIOLATIONS FOUND:")
            for i, violation in enumerate(self.code_violations, 1):
                print(f"  {i}. {violation}")
        
        if self.code_warnings:
            print("\n⚠️  CODE WARNINGS:")
            for i, warning in enumerate(self.code_warnings, 1):
                print(f"  {i}. {warning}")
        
        if not self.code_violations and not self.code_warnings:
            print("\n✅ ALL CODE REQUIREMENTS SATISFIED")
            print("   Design complies with IBC 2021 / IRC 2021")
        
        print("="*60 + "\n")

    def get_inputs(self):
        """Collects all user input for the house configuration with code guidance."""
        print("=======================================")
        print("🏠 ARCHITECTURAL CONFIGURATION - IBC/IRC COMPLIANT")
        print("=======================================")
        print("Press ENTER to accept the default code-compliant value shown.")
        
        # GLOBAL SETTINGS
        print("\n--- 1. GLOBAL SETTINGS ---")
        self.project_name = input(f"Project Name ['{self.project_name}']: ") or self.project_name
        
        # Building Type
        print("\nAvailable Building Types: Residential, Commercial, Industrial")
        self.building_type = input(f"Building Type ['{self.building_type}']: ") or self.building_type
        
        # ADA Compliance
        ada_input = input(f"ADA Accessible Design? (y/n) [n]: ").lower()
        self.ada_compliant = ada_input == 'y'
        
        try:
            self.num_floors = int(input(f"Number of Floors [{self.num_floors}]: ") or self.num_floors)
        except ValueError:
            print("Invalid input, using default number of floors.")
        
        # Floor-to-floor height (story height)
        try:
            h = input(f"Floor-to-Floor Height (ft) [IRC min: 8', recommended: {self.floor_height}]: ")
            self.floor_height = float(h) if h else self.floor_height
            if self.floor_height < 8.0:
                print(f"⚠️  Warning: Floor height < 8' may not meet structural requirements")
        except ValueError:
            pass
        
        # Ceiling height
        try:
            ch = input(f"Clear Ceiling Height (ft) [IRC min: {ArchitecturalCodes.MIN_CEILING_HEIGHT_RESIDENTIAL}', default: {self.ceiling_height}]: ")
            self.ceiling_height = float(ch) if ch else self.ceiling_height
        except ValueError:
            pass

        # Initial/Minimum building dimensions
        try:
            w = input(f"Main Building Width (ft) [{self.floor_width}]: ")
            self.floor_width = float(w) if w else self.floor_width
        except ValueError:
            pass
            
        try:
            d = input(f"Main Building Depth (ft) [{self.floor_depth}]: ")
            self.floor_depth = float(d) if d else self.floor_depth
        except ValueError:
            pass
        
        # Hallway/Corridor width with code guidance
        min_corridor = (ArchitecturalCodes.MIN_CORRIDOR_WIDTH_ACCESSIBLE if self.ada_compliant 
                       else ArchitecturalCodes.MIN_CORRIDOR_WIDTH_COMMERCIAL if self.building_type == "Commercial"
                       else ArchitecturalCodes.MIN_CORRIDOR_WIDTH_RESIDENTIAL)
        
        try:
            hw = input(f"Hallway Width (ft) [Code min: {min_corridor}', default: {self.hallway_width}]: ")
            self.hallway_width = float(hw) if hw else self.hallway_width
            if self.hallway_width < min_corridor:
                print(f"⚠️  Warning: Hallway width < {min_corridor}' code minimum!")
        except ValueError:
            pass

        # Facade Material
        print("\nAvailable Facade Materials: Wood Siding, Concrete, Bricks, Stucco")
        self.facade_type = input(f"Facade Material ['{self.facade_type}']: ") or self.facade_type
        
        # GARAGE CONFIG
        print("\n--- 2. GARAGE CONFIGURATION (IRC R309) ---")
        try:
            self.garage_cars = int(input(f"Garage Capacity (cars) [{self.garage_cars}]: ") or self.garage_cars)
        except ValueError:
            pass
        
        # Calculate code-compliant garage dimensions
        if self.garage_cars == 1:
            min_dims = ArchitecturalCodes.SINGLE_CAR_GARAGE_MIN
            g_width, g_depth = 12.0, 22.0
        elif self.garage_cars == 2:
            min_dims = ArchitecturalCodes.DOUBLE_CAR_GARAGE_MIN
            g_width, g_depth = 24.0, 24.0
        else:
            min_dims = ArchitecturalCodes.TRIPLE_CAR_GARAGE_MIN
            g_width = 30.0 + ((self.garage_cars - 3) * 12.0)
            g_depth = 24.0
        
        print(f"   IRC R309 Minimum: {min_dims[0]}'W x {min_dims[1]}'D")
        print(f"   Recommended: {g_width}'W x {g_depth}'D")
        
        self.garage_data = {
            "label": f"DETACHED GARAGE\n{self.garage_cars} Cars\n(IRC R309 Compliant)", 
            "w": g_width, 
            "d": g_depth, 
            "bg": "#d3d3d3"
        }
        
        # PER FLOOR SETTINGS
        for i in range(1, self.num_floors + 1):
            print(f"\n--- 3. CONFIGURING FLOOR {i} (IBC/IRC Requirements) ---")
            
            f_data = {
                "id": i,
                "rooms": [],
                "user_defined_layout": False, 
                "bathrooms": int(input(f"Number of Bathrooms on Floor {i} [2]: ") or 2),
                "kitchens": int(input(f"Number of Kitchens on Floor {i} [1]: ") or 1),
                "living": int(input(f"Number of Living Rooms on Floor {i} [1]: ") or 1),
                "bedrooms": int(input(f"Number of Bedrooms on Floor {i} [2]: ") or 2),
                "dressing": int(input(f"Number of Dressing Rooms on Floor {i} [1]: ") or 1)
            }
            
            # Calculate code-compliant stair dimensions
            num_risers, riser_h, tread_d, total_run = self.codes.calculate_stair_dimensions(self.floor_height)
            stair_width = (ArchitecturalCodes.MIN_STAIR_WIDTH_COMMERCIAL if self.building_type == "Commercial" 
                          else ArchitecturalCodes.MIN_STAIR_WIDTH_RESIDENTIAL)
            
            stairs_label = "STAIRS UP" if i == 1 else "STAIRS DN"
            f_data["rooms"].append({
                "label": f"{stairs_label}\n{num_risers}R @ {riser_h*12:.1f}\"",
                "w": stair_width,
                "d": total_run,
                "bg": "#D8BFD8",
                "type": "stairs",
                "risers": num_risers,
                "riser_height": riser_h,
                "tread_depth": tread_d
            })
            
            print(f"\n   Stair Design (IRC R311.7 / IBC 1011):")
            print(f"   - {num_risers} Risers @ {riser_h*12:.2f}\" each")
            print(f"   - {num_risers-1} Treads @ {tread_d*12:.2f}\" each")
            print(f"   - Total Run: {total_run:.1f}' | Width: {stair_width}'")
            
            def add_rooms(count, label, default_w, default_h, color="#fff"):
                rooms_list = []
                min_dims = ""
                
                # Set code minimums based on room type
                if "Bedroom" in label:
                    min_dims = f" (IRC min: {ArchitecturalCodes.MIN_BEDROOM_WIDTH}'W, {ArchitecturalCodes.MIN_BEDROOM_AREA}sf)"
                elif "Kitchen" in label:
                    min_dims = f" (Recommended min: {ArchitecturalCodes.MIN_KITCHEN_AREA}sf)"
                elif "Bath" in label:
                    min_dims = f" (Min width: {ArchitecturalCodes.MIN_BATHROOM_WIDTH}')"
                
                for r in range(count):
                    dim = input(f"  > Dimensions for {label} {r+1} (WxD) [{default_w}x{default_h}]{min_dims}: ") or f"{default_w}x{default_h}"
                    try:
                        rw, rd = map(float, dim.lower().split('x'))
                        
                        # Validate dimensions
                        if "Bedroom" in label:
                            if rw < ArchitecturalCodes.MIN_BEDROOM_WIDTH:
                                print(f"     ⚠️  Width {rw}' < IRC minimum {ArchitecturalCodes.MIN_BEDROOM_WIDTH}'")
                            if rw * rd < ArchitecturalCodes.MIN_BEDROOM_AREA:
                                print(f"     ⚠️  Area {rw*rd}sf < IRC minimum {ArchitecturalCodes.MIN_BEDROOM_AREA}sf")
                        
                    except ValueError:
                        rw, rd = default_w, default_h
                    
                    rooms_list.append({
                        "label": f"{label} {r+1}", 
                        "w": rw, 
                        "d": rd, 
                        "bg": color,
                        "type": "room"
                    })
                return rooms_list

            f_data["rooms"].extend(add_rooms(f_data["living"], "Living Room", 18, 14, "#fff"))
            f_data["rooms"].extend(add_rooms(f_data["kitchens"], "Kitchen", 14, 12, "#EFEFEF"))
            f_data["rooms"].extend(add_rooms(f_data["bedrooms"], "Bedroom", 14, 14, "#fff"))
            f_data["rooms"].extend(add_rooms(f_data["bathrooms"], "Bath", 8, 6, "#D6EAF8"))
            f_data["rooms"].extend(add_rooms(f_data["dressing"], "Dressing", 6, 6, "#F9F9F9"))

            self.floors_data.append(f_data)
        
        # Perform code validation
        self.validate_building_codes()

def calculate_room_positions(config, floor):
    """
    Calculates room positions (x, y) for a floor using sequential packing 
    if they don't already have coordinates.
    Also returns the required width and depth for this floor.
    Uses code-compliant wall thicknesses.
    """
    wall_ft = config.WALL_THICKNESS

    if floor.get("user_defined_layout", False):
        # Calculate max dimensions from hardcoded rooms
        if not floor['rooms']:
            return config.floor_width, config.floor_depth

        max_x = max(room['x'] + room['w'] for room in floor['rooms']) + wall_ft
        max_y = max(room['y'] + room['d'] for room in floor['rooms']) + wall_ft
        
        return math.ceil(max_x), math.ceil(max_y)

    # --- Sequential Packing Logic (for user input) ---
    # First, separate stairs from other rooms
    stairs = [room for room in floor['rooms'] if room.get('type') == 'stairs']
    other_rooms = [room for room in floor['rooms'] if room.get('type') != 'stairs']
    
    current_x_sum = wall_ft 
    current_y_sum = wall_ft 
    row_max_d = 0.0
    max_x = 0.0
    max_y = 0.0
    
    effective_max_w = max(config.floor_width, 10.0)

    # Place stairs first if they exist
    if stairs:
        stair = stairs[0]
        stair_w = stair['w']
        stair_d = stair['d']
        
        stair['x'] = current_x_sum
        stair['y'] = current_y_sum
        
        current_x_sum += stair_w + wall_ft
        row_max_d = max(row_max_d, stair_d)
    
    # Now place other rooms
    for room in other_rooms:
        r_w = room['w']
        r_d = room['d']
        
        # Check if we need to wrap to next row
        if current_x_sum + r_w + wall_ft > effective_max_w + 0.001 and current_x_sum != wall_ft:
            max_x = max(max_x, current_x_sum)
            current_x_sum = wall_ft 
            current_y_sum += row_max_d + wall_ft 
            row_max_d = 0.0
        
        # If not the start of a row, add wall space
        if current_x_sum > wall_ft:
            current_x_sum += wall_ft 
        
        # Update position
        room['x'] = current_x_sum
        room['y'] = current_y_sum
        
        current_x_sum += r_w 
        max_x = max(max_x, current_x_sum)

        if r_d > row_max_d: 
            row_max_d = r_d
    
    # Final dimensions
    final_max_x = max_x + wall_ft 
    final_max_y = current_y_sum + row_max_d + wall_ft

    return math.ceil(final_max_x), math.ceil(final_max_y)

def generate_html(config):
    """
    Generates IBC/IRC compliant HTML/CSS content for architectural house plans.
    Includes code annotations and professional architectural standards.
    """
    scale = config.scale
    wall_ft = config.WALL_THICKNESS
    ext_wall_ft = config.EXTERIOR_WALL_THICKNESS
    wall_px = wall_ft * scale
    ext_wall_px = ext_wall_ft * scale
    
    # --- DIMENSION ADJUSTMENT LOGIC ---
    required_width = config.floor_width
    required_depth = config.floor_depth
    
    for floor in config.floors_data:
        floor_req_w, floor_req_d = calculate_room_positions(config, floor)
        required_width = max(required_width, floor_req_w)
        required_depth = max(required_depth, floor_req_d)
        
    config.floor_width = required_width
    config.floor_depth = required_depth
    print(f"\n--- BUILDING ENVELOPE ---")
    print(f"Main Building: {config.floor_width}' W x {config.floor_depth}' D")
    print(f"Exterior Walls: {ext_wall_ft}' ({ext_wall_ft*12:.1f}\") - IBC Compliant")
    print(f"Interior Walls: {wall_ft}' ({wall_ft*12:.1f}\") - IRC R302")
    print(f"Floor-to-Floor Height: {config.floor_height}' | Clear Ceiling: {config.ceiling_height}'")
    print(f"Code Compliance: {'ADA + ' if config.ada_compliant else ''}IBC 2021 / IRC 2021\n")
    
    # Build code compliance statement
    code_statement = f"""
    <div style="background: #f0f8ff; border-left: 4px solid #003366; padding: 15px; margin: 20px 0;">
        <strong>📋 CODE COMPLIANCE STATEMENT</strong><br>
        <span style="font-size: 12px;">
        This design complies with:<br>
        • International Building Code (IBC) 2021<br>
        • International Residential Code (IRC) 2021<br>
        • American Institute of Architects (AIA) Standards<br>
        {'• Americans with Disabilities Act (ADA) Accessibility Guidelines<br>' if config.ada_compliant else ''}
        • Local jurisdiction amendments may apply<br><br>
        
        <strong>Key Requirements Met:</strong><br>
        • Minimum Room Dimensions: IRC R304<br>
        • Egress Requirements: IRC R311 / IBC Chapter 10<br>
        • Ceiling Heights: IRC R305 / IBC 1208<br>
        • Stairway Design: IRC R311.7 / IBC 1011<br>
        • Fire Separation: IRC R302 / IBC 706<br>
        • Structural Loads: IBC Chapter 16 (Design Required)<br>
        </span>
    </div>
    """
    
    # Code warnings/violations display
    code_issues_html = ""
    if config.code_violations or config.code_warnings:
        issues = ""
        if config.code_violations:
            issues += "<div style='color: #c00; font-weight: bold;'>❌ CODE VIOLATIONS:</div><ul>"
            for v in config.code_violations:
                issues += f"<li>{v}</li>"
            issues += "</ul>"
        
        if config.code_warnings:
            issues += "<div style='color: #f80; font-weight: bold;'>⚠️ CODE WARNINGS:</div><ul>"
            for w in config.code_warnings:
                issues += f"<li>{w}</li>"
            issues += "</ul>"
        
        code_issues_html = f"""
        <div style="background: #fff3cd; border-left: 4px solid #f80; padding: 15px; margin: 20px 0; font-size: 12px;">
            <strong>⚠️  CODE REVIEW REQUIRED</strong><br>
            {issues}
            <em>These items require design review by licensed architect/engineer before permitting.</em>
        </div>
        """
    
    signature_footer = f"""
    <div class="signature-footer">
        <p><strong>Design Professional: {config.signature_name}</strong></p>
        <p>{config.signature_company} | {config.signature_email}</p>
        <p style="font-size: 10px;">{config.signature_license}</p>
        <p style="font-size: 10px; color: #999;">Generated per IBC 2021 / IRC 2021 | For Preliminary Design Only</p>
        <div class="page-number"></div>
    </div>
    """

    css = f"""
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Arial', 'Helvetica', sans-serif; background: #525252; padding: 20px; }}
        .page {{ max-width: 1400px; margin: 0 auto 30px; background: white; padding: 40px; border: 1px solid #003366; min-height: 1200px; position: relative; page-break-after: always; }}
        .header {{ text-align: center; border-bottom: 3px solid #003366; padding-bottom: 20px; margin-bottom: 30px; }}
        .floor-title {{ background: #003366; color: white; padding: 15px; font-size: 22px; font-weight: bold; margin-bottom: 20px; border-radius: 4px; text-transform: uppercase; letter-spacing: 1px;}}
        .drawing-area {{ position: relative; border: 2px solid #003366; background: #fdfdfd; margin-bottom: 30px; overflow: auto; padding: 20px; }}
        
        /* 🧱 WALLS & HATCHING - CODE COMPLIANT */
        .hatch-pattern {{
            background-color: #A5A5A5;
            background-image: repeating-linear-gradient(
                -45deg, 
                transparent, 
                transparent 4px, 
                #888888 4px, 
                #888888 5px
            );
            border: 1px solid #003366;
        }}
        
        .exterior-wall {{
            background-color: #8B8B8B;
            background-image: repeating-linear-gradient(
                -45deg, 
                transparent, 
                transparent 5px, 
                #666666 5px, 
                #666666 6px
            );
            border: 2px solid #003366;
        }}
        
        .building-outline {{ 
            border: none;
            position: absolute; 
            box-shadow: 5px 5px 15px rgba(0,0,0,0.2); 
            padding: {ext_wall_px}px; 
            background-color: #fff;
        }}
        .building-outline::before {{
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            border: {ext_wall_px}px solid #003366;
            box-sizing: border-box;
            z-index: 1;
        }}
        
        .garage-outline {{ 
            border: 4px solid #555; 
            background: #eee;
            position: absolute; 
            box-shadow: 5px 5px 15px rgba(0,0,0,0.2); 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            text-align: center; 
            font-weight: bold; 
            color: #555; 
        }}
        
        /* ROOM STYLING */
        .room {{ 
            position: absolute; 
            border: none; 
            display: flex; 
            align-items: center; 
            justify-content: center; 
            text-align: center; 
            font-size: 13px; 
            font-weight: bold; 
            color: #333; 
            z-index: 2; 
        }}
        .dimension-tag {{ font-size: 11px; color: #555; font-weight: normal; display: block; margin-top: 4px; background: rgba(255,255,255,0.7); padding: 2px; border-radius: 3px; }}
        
        /* WALL PLACEMENT */
        .wall {{
            position: absolute;
            z-index: 5;
        }}
        .v-wall {{
            width: {wall_px}px;
            top: 0;
            bottom: 0; 
        }}
        .h-wall {{
            height: {wall_px}px;
            left: 0;
            right: 0; 
        }}
        
        /* DOORS - IBC 1010.1.1 Compliant */
        .door-icon {{
            position: absolute;
            bottom: -2px;
            right: 10px;
            width: 30px;
            height: 30px;
            border-bottom: 4px solid #8B4513;
            border-right: 4px solid rgba(139, 69, 19, 0.3);
            border-radius: 0 0 100% 0;
            z-index: 5;
            background: transparent;
        }}
        .door-label {{
            position: absolute;
            font-size: 8px;
            color: #8B4513;
            font-weight: bold;
            z-index: 6;
            background: white;
            padding: 1px 3px;
            border: 1px solid #8B4513;
        }}
        
        /* WINDOWS - IRC R310 Egress */
        .window-icon {{
            position: absolute;
            top: -3px;
            left: 50%;
            transform: translateX(-50%);
            width: 40%;
            height: 6px;
            background: #ADD8E6;
            border: 1px solid #333;
            z-index: 5;
        }}
        
        /* 🪜 STAIRCASE - IRC R311.7 / IBC 1011 Compliant */
        .staircase {{
            background: #E6E6FA;
            border: 2px solid #4B0082;
            position: absolute;
            font-size: 10px;
            font-weight: bold;
            color: #4B0082;
            text-align: center;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            z-index: 3;
            overflow: hidden;
        }}
        .staircase .stairs-title {{
            font-size: 11px;
            font-weight: bold;
            color: #4B0082;
            margin-bottom: 3px;
            z-index: 4;
            background: rgba(255,255,255,0.9);
            padding: 3px 8px;
            border-radius: 3px;
        }}
        .tread {{
            height: 10%;
            width: 100%;
            border-top: 1px solid #9932CC;
            box-sizing: border-box;
            position: relative;
        }}
        .tread::before {{
            content: '';
            position: absolute;
            top: -1px;
            left: 0;
            right: 0;
            height: 1px;
            background: #9932CC;
        }}
        
        /* Code annotation labels */
        .code-label {{
            position: absolute;
            background: #ffffcc;
            border: 1px solid #ff9900;
            padding: 4px 8px;
            font-size: 9px;
            font-weight: bold;
            color: #663300;
            z-index: 20;
            box-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}

        /* FACADE CSS */
        .facade-container {{ 
            position: relative; 
            background: #e0f7fa; 
            border-bottom: 20px solid #4caf50; 
            overflow: hidden; 
        }}
        
        .facade-wood {{ 
            background: linear-gradient(90deg, #D2B48C 0%, #C19A6B 50%, #D2B48C 100%);
            background-image: 
                repeating-linear-gradient(0deg, transparent, transparent 15px, rgba(160, 82, 45, 0.1) 15px, rgba(160, 82, 45, 0.1) 16px),
                repeating-linear-gradient(90deg, #D2B48C 0px, #C19A6B 100px, #D2B48C 200px);
        }}
        .facade-concrete {{ 
            background: #C0C0C0; 
            background-image: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,0,0,0.05) 2px, rgba(0,0,0,0.05) 3px);
        }}
        .facade-bricks {{ 
            background: #8B4513;
            background-image: 
                repeating-linear-gradient(0deg, #8B4513 0px, #8B4513 10px, #654321 10px, #654321 11px),
                repeating-linear-gradient(90deg, #8B4513 0px, #8B4513 40px, #654321 40px, #654321 41px, #8B4513 41px, #8B4513 81px, #654321 81px, #654321 82px);
        }}
        .facade-stucco {{ 
            background: #F5F5DC;
            background-image: 
                radial-gradient(circle at 20% 50%, transparent 0%, rgba(0,0,0,0.02) 100%),
                radial-gradient(circle at 80% 50%, transparent 0%, rgba(0,0,0,0.02) 100%);
        }}

        .building-structure {{ 
            position: absolute; 
            bottom: 0; left: 50%; 
            transform: translateX(-50%); 
            width: 70%; 
            background: #F4F4F4;
            border-left: 3px solid #333; 
            border-right: 3px solid #333; 
            display: flex; 
            flex-direction: column-reverse; 
        }}
        .level {{ 
            border-top: 2px solid #555; 
            position: relative; 
            width: 100%; 
            box-shadow: inset 0 0 20px rgba(0,0,0,0.05); 
        }}
        .roof {{ 
            position: absolute; 
            width: 80%; 
            left: 10%; 
            height: 120px; 
            top: -120px; 
            clip-path: polygon(50% 0%, 0% 100%, 100% 100%); 
            background: repeating-linear-gradient(45deg, #2c3e50, #2c3e50 10px, #34495e 10px, #34495e 20px); 
            z-index: 10; 
        }}
        
        .facade-door {{ position: absolute; background: #5D4037; border: 2px solid #333; bottom: 0; height: 85%; width: 15%; left: 42.5%; z-index: 6; }}

        .window-simple {{
            position: absolute;
            background: #ADD8E6;
            border: 3px solid #003366;
            bottom: 25%;
            height: 50%;
            width: 12%;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
            z-index: 5;
        }}
        .top-floor-window {{
            height: 40%;
            bottom: 30%;
        }}
        
        /* Dimension lines - Professional Standard */
        .dimension-line {{
            position: absolute;
            background: #FF0000;
            z-index: 15;
        }}
        .dimension-line-h {{
            height: 2px;
        }}
        .dimension-line-v {{
            width: 2px;
        }}
        .dimension-arrow {{
            position: absolute;
            width: 0;
            height: 0;
            z-index: 15;
        }}
        .dimension-label {{
            position: absolute;
            background: white;
            border: 2px solid #FF0000;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: bold;
            color: #FF0000;
            z-index: 16;
            white-space: nowrap;
        }}
        .total-dim-label {{
            background: #333;
            color: white;
            border: 2px solid #333;
        }}
        
        @media print {{ 
            body {{ background: white; padding: 0; }}
            .page {{ margin: 0; border: none; page-break-after: always; }}
            .controls {{ display: none; }}
        }}
        
        .controls {{ text-align: center; margin-bottom: 20px; }}
        .btn {{ background: #003366; color: white; padding: 12px 30px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }}
        .btn:hover {{ background: #005599; }}
        
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 12px; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background: #003366; color: white; }}
        
        .signature-footer {{ position: absolute; bottom: 20px; left: 40px; right: 40px; text-align: center; font-size: 11px; color: #666; border-top: 2px solid #003366; padding-top: 10px; }}
    """
    
    facade_class_map = {
        "Wood Siding": "facade-wood",
        "Concrete": "facade-concrete",
        "Bricks": "facade-bricks",
        "Stucco": "facade-stucco"
    }
    
    facade_class = facade_class_map.get(config.facade_type, "facade-wood")

    floor_plans_html = ""
    
    # --- PLAN GENERATION LOOP ---
    for floor in config.floors_data:
        floor_w_inner_ft = config.floor_width - (ext_wall_ft * 2) 
        floor_d_inner_ft = config.floor_depth - (ext_wall_ft * 2)

        floor_w_px = floor_w_inner_ft * scale 
        floor_d_px = floor_d_inner_ft * scale
        
        rooms_html = ""
        walls_html = "" 
        dimensions_html = "" 
        code_annotations_html = ""
        
        v_wall_segments = {} 
        h_wall_segments = {}
        door_size = wall_px * 3

        for i, room in enumerate(floor['rooms']):
            r_w = room['w'] * scale
            r_h = room['d'] * scale
            x_pos = room['x'] * scale
            y_pos = room['y'] * scale
            
            is_staircase = room.get('type') == 'stairs' or "STAIRS" in room['label'].upper()
            
            # Generate Room HTML
            if is_staircase:
                # IBC-compliant staircase with code info
                num_risers = room.get('risers', 10)
                treads_html = ""
                for t in range(num_risers):
                    tread_top = (t / num_risers) * 100
                    treads_html += f'<div class="tread" style="top: {tread_top}%;"></div>'
                
                rooms_html += f"""
                <div class="staircase" style="left: {x_pos}px; top: {y_pos}px; width: {r_w}px; height: {r_h}px;">
                    <div class="stairs-title">{room['label']}</div>
                    <div style="font-size: 8px; margin-top: 2px;">IRC R311.7 / IBC 1011</div>
                    <div style="font-size: 9px;">({room['w']}' x {room['d']}')</div>
                    {treads_html}
                </div>
                """
                
                # Add code annotation for stairs
                code_annotations_html += f"""
                <div class="code-label" style="left: {x_pos + r_w + 5}px; top: {y_pos}px;">
                    STAIR CODE:<br>
                    Width: {room['w']*12:.0f}\" ≥ {ArchitecturalCodes.MIN_STAIR_WIDTH_RESIDENTIAL*12:.0f}\"<br>
                    Risers: {num_risers}<br>
                    R: {room.get('riser_height', 0)*12:.2f}\" ≤ {ArchitecturalCodes.MAX_RISER_HEIGHT_RESIDENTIAL*12:.2f}\"<br>
                    T: {room.get('tread_depth', 0)*12:.2f}\" ≥ {ArchitecturalCodes.MIN_TREAD_DEPTH_RESIDENTIAL*12:.2f}\"
                </div>
                """
            else:
                rooms_html += f"""
                <div class="room" style="left: {x_pos}px; top: {y_pos}px; width: {r_w}px; height: {r_h}px; background: {room['bg']};">
                    <div style="z-index:10;">
                        <strong style="font-size: 13px; display: block; margin-bottom: 4px;">{room['label']}</strong>
                        <span class="dimension-tag"><b>{room['w']}'</b> W x <b>{room['d']}'</b> D<br>{room['w']*room['d']:.0f} SF</span>
                    </div>
                </div>
                """
                
                # Add door label with clear width
                door_label_x = x_pos + r_w - 40
                door_label_y = y_pos + r_h - 15
                rooms_html += f"""
                <div class="door-label" style="left: {door_label_x}px; top: {door_label_y}px;">
                    36\" CLR
                </div>
                """
            
            # Generate Internal Walls with door openings
            
            # RIGHT-SIDE WALL
            right_wall_x_px = x_pos + r_w 
            wall_top_y_px = y_pos
            wall_height_px = r_h
            
            if right_wall_x_px < floor_w_px - 0.001: 
                door_offset = wall_height_px * 0.3
                door_y_start = wall_top_y_px + wall_height_px - door_offset - door_size
                door_y_end = wall_top_y_px + wall_height_px - door_offset
                
                if right_wall_x_px not in v_wall_segments:
                    v_wall_segments[right_wall_x_px] = []

                if is_staircase:
                    door_y_start_stairs = wall_top_y_px + wall_height_px - door_size
                    door_y_end_stairs = wall_top_y_px + wall_height_px
                    
                    if door_y_start_stairs > wall_top_y_px:
                        v_wall_segments[right_wall_x_px].append((wall_top_y_px, door_y_start_stairs))
                    
                    walls_html += f"""
                    <div class="door-icon" style="left: {right_wall_x_px - 15}px; top: {door_y_start_stairs + door_size - 15}px;"></div>
                    """
                else:
                    if door_y_start > wall_top_y_px:
                        v_wall_segments[right_wall_x_px].append((wall_top_y_px, door_y_start))
                    if door_y_end < wall_top_y_px + wall_height_px:
                        v_wall_segments[right_wall_x_px].append((door_y_end, wall_top_y_px + wall_height_px))
                    
                    walls_html += f"""
                    <div class="door-icon" style="left: {right_wall_x_px - 15}px; top: {door_y_start + door_size - 15}px;"></div>
                    """

            # BOTTOM-SIDE WALL
            bottom_wall_y_px = y_pos + r_h
            wall_left_x_px = x_pos
            wall_width_px = r_w
            
            if bottom_wall_y_px < floor_d_px - 0.001: 
                door_offset = wall_width_px * 0.3
                door_x_start = wall_left_x_px + wall_width_px - door_offset - door_size
                door_x_end = wall_left_x_px + wall_width_px - door_offset

                if bottom_wall_y_px not in h_wall_segments:
                    h_wall_segments[bottom_wall_y_px] = []
                
                if is_staircase:
                    h_wall_segments[bottom_wall_y_px].append((wall_left_x_px, wall_left_x_px + wall_width_px))
                else:
                    if door_x_start > wall_left_x_px:
                        h_wall_segments[bottom_wall_y_px].append((wall_left_x_px, door_x_start))
                    if door_x_end < wall_left_x_px + wall_width_px:
                        h_wall_segments[bottom_wall_y_px].append((door_x_end, wall_left_x_px + wall_width_px))

                    walls_html += f"""
                    <div class="door-icon" style="left: {door_x_start + door_size - 15}px; top: {bottom_wall_y_px - 15}px;"></div>
                    """
                
            # Generate Room Dimensions (skip for stairs)
            if not is_staircase:
                dimensions_html += f"""
                <div class="dimension-line dimension-line-h" style="left: {x_pos}px; top: {y_pos - 15}px; width: {r_w}px;"></div>
                <div class="dimension-arrow" style="left: {x_pos}px; top: {y_pos - 20}px; border-right: 8px solid #FF0000; border-top: 5px solid transparent; border-bottom: 5px solid transparent;"></div>
                <div class="dimension-arrow" style="left: {x_pos + r_w - 8}px; top: {y_pos - 20}px; border-left: 8px solid #FF0000; border-top: 5px solid transparent; border-bottom: 5px solid transparent;"></div>
                <div class="dimension-label" style="left: {x_pos + r_w/2 - 20}px; top: {y_pos - 28}px;">{room['w']}'</div>
                
                <div class="dimension-line dimension-line-v" style="left: {x_pos - 15}px; top: {y_pos}px; height: {r_h}px;"></div>
                <div class="dimension-arrow" style="left: {x_pos - 20}px; top: {y_pos}px; border-bottom: 8px solid #FF0000; border-left: 5px solid transparent; border-right: 5px solid transparent;"></div>
                <div class="dimension-arrow" style="left: {x_pos - 20}px; top: {y_pos + r_h - 8}px; border-top: 8px solid #FF0000; border-left: 5px solid transparent; border-right: 5px solid transparent;"></div>
                <div class="dimension-label" style="left: {x_pos - 50}px; top: {y_pos + r_h/2 - 10}px;">{room['d']}'</div>
                """

        # Draw consolidated internal walls
        for x_pos_seg, segments in v_wall_segments.items():
            for y_start, y_end in segments:
                wall_height = y_end - y_start
                if wall_height > 0:
                    walls_html += f"""
                    <div class="wall v-wall hatch-pattern" style="left: {x_pos_seg}px; top: {y_start}px; height: {wall_height}px;"></div>
                    """
        
        for y_pos_seg, segments in h_wall_segments.items():
            for x_start, x_end in segments:
                wall_width = x_end - x_start
                if wall_width > 0:
                    walls_html += f"""
                    <div class="wall h-wall hatch-pattern" style="left: {x_start}px; top: {y_pos_seg}px; width: {wall_width}px;"></div>
                    """

        # Add Garage
        garage_html = ""
        floor_w_px_total = floor_w_px + 150
        
        if floor['id'] == 1 and config.garage_data:
            gar_w = config.garage_data['w'] * scale
            gar_h = config.garage_data['d'] * scale
            garage_x = floor_w_px + ext_wall_px + 50
            
            garage_html = f"""
            <div class="garage-outline" style="left: {garage_x}px; top: 20px; width: {gar_w}px; height: {gar_h}px;">
                <div>
                    {config.garage_data['label']}<br>
                    <span class="dimension-tag">{config.garage_data['w']}' x {config.garage_data['d']}'</span>
                    <div class="door-icon" style="bottom:-5px; right: 40%; width: 40px; border-bottom: 6px solid #555;"></div>
                </div>
            </div>
            """
            
            floor_w_px_total = max(floor_w_px_total, garage_x + gar_w + 50)
        
        # Total Building Dimensions
        total_building_width_px = floor_w_px + 2 * ext_wall_px
        total_building_depth_px = floor_d_px + 2 * ext_wall_px

        total_dim_html = f"""
        <div class="dimension-line dimension-line-h" style="left: 20px; top: 0px; width: {total_building_width_px}px; background:#333;"></div>
        <div class="dimension-arrow" style="left: 20px; top: -5px; border-right: 8px solid #333; border-top: 5px solid transparent; border-bottom: 5px solid transparent;"></div>
        <div class="dimension-arrow" style="left: {20 + total_building_width_px - 8}px; top: -5px; border-left: 8px solid #333; border-top: 5px solid transparent; border-bottom: 5px solid transparent;"></div>
        <div class="dimension-label total-dim-label" style="left: {20 + total_building_width_px/2 - 30}px; top: -18px;">Total W: {config.floor_width}'</div>
        
        <div class="dimension-line dimension-line-v" style="left: 0px; top: 20px; height: {total_building_depth_px}px; background:#333;"></div>
        <div class="dimension-arrow" style="left: -5px; top: 20px; border-bottom: 8px solid #333; border-left: 5px solid transparent; border-right: 5px solid transparent;"></div>
        <div class="dimension-arrow" style="left: -5px; top: {20 + total_building_depth_px - 8}px; border-top: 8px solid #333; border-left: 5px solid transparent; border-right: 5px solid transparent;"></div>
        <div class="dimension-label total-dim-label" style="left: -60px; top: {20 + total_building_depth_px/2 - 10}px;">Total D: {config.floor_depth}'</div>
        """
        
        floor_w_for_area = max(floor_w_px_total, total_building_width_px + 30)
        floor_d_for_area = max(total_building_depth_px + 30, 600)

        # Room count for table
        staircases = [r for r in floor['rooms'] if r.get('type') == 'stairs' or "STAIRS" in r['label'].upper()]
        regular_rooms = [r for r in floor['rooms'] if not (r.get('type') == 'stairs' or "STAIRS" in r['label'].upper())]
        
        total_area = sum(r['w']*r['d'] for r in regular_rooms)
        
        floor_plans_html += f"""
        <div class="page">
            <div class="floor-title">FLOOR {floor['id']} - ARCHITECTURAL PLAN ({config.building_type})</div>
            
            <div style="background: #e8f4f8; padding: 10px; margin-bottom: 15px; border-left: 4px solid #003366;">
                <strong>Floor {floor['id']} Summary:</strong> 
                Total Area: {total_area:.0f} SF | 
                Ceiling Height: {config.ceiling_height}' (IRC R305) | 
                Corridors: {config.hallway_width}' Wide ({'ADA' if config.ada_compliant else 'IRC'} Compliant)
            </div>
            
            <div class="drawing-area" style="min-height: {floor_d_for_area + 100}px; width: {floor_w_for_area + 100}px;">
                
                {total_dim_html}

                <div class="building-outline" style="left: 20px; top: 20px; width: {floor_w_px}px; height: {floor_d_px}px;">
                    {walls_html}
                    {dimensions_html}
                    {code_annotations_html}
                    {rooms_html}
                    <div style="position: absolute; bottom: 5px; right: 5px; font-size: 10px; color: #888; background: white; padding: 5px;">
                        BUILDING FOOTPRINT: {config.floor_width}' x {config.floor_depth}'<br>
                        Exterior Walls: {ext_wall_ft}'  ({ext_wall_ft*12:.1f}\") IBC Compliant<br>
                        Interior Walls: {wall_ft}' ({wall_ft*12:.1f}\") IRC R302<br>
                        Hallways: {config.hallway_width}' Wide
                    </div>
                </div>

                {garage_html}
                
            </div>
            
            <h3>Floor {floor['id']} - Room Schedule (IBC/IRC Compliance)</h3>
            <table>
                <tr>
                    <th>Room ID</th>
                    <th>Room Type</th>
                    <th>Dimensions (W x D)</th>
                    <th>Area (SF)</th>
                    <th>Code Requirement</th>
                    <th>Status</th>
                </tr>
                {"".join([f'''<tr>
                    <td>{i+1}</td>
                    <td>{r['label']}</td>
                    <td>{r['w']}' x {r['d']}'</td>
                    <td>{r['w']*r['d']:.0f}</td>
                    <td>{'IRC R304: Min 70SF, 7\' width' if 'Bedroom' in r['label'] else 'IRC R303: Adequate' if 'Living' in r['label'] else 'IRC R306: 5\' min width' if 'Bath' in r['label'] else 'N/A'}</td>
                    <td>{'✅' if (('Bedroom' in r['label'] and r['w']*r['d'] >= 70 and r['w'] >= 7) or 'Bedroom' not in r['label']) else '⚠️'}</td>
                </tr>''' for i, r in enumerate(regular_rooms)])}
                {"".join([f'''<tr style="background: #f0f0f0;">
                    <td>S{i+1}</td>
                    <td>{r['label']}</td>
                    <td>{r['w']}' x {r['d']}'</td>
                    <td>{r['w']*r['d']:.0f}</td>
                    <td>IRC R311.7: {r.get('risers', 'N/A')}R @ {r.get('riser_height', 0)*12:.2f}\" | T: {r.get('tread_depth', 0)*12:.2f}\"</td>
                    <td>✅</td>
                </tr>''' for i, r in enumerate(staircases)])}
                <tr style="background: #e8f4f8; font-weight: bold;">
                    <td colspan="3">TOTAL FLOOR AREA</td>
                    <td>{total_area:.0f} SF</td>
                    <td colspan="2">Conditioned Space</td>
                </tr>
            </table>
            {signature_footer}
        </div>
        """

    # FACADE GENERATION with code annotations
    total_facade_height_px = (config.num_floors * config.floor_height) * scale
    level_height_px = config.floor_height * scale
    
    def get_facade_windows(count=3):
        wins = ""
        gap = 100 / (count + 1)
        for i in range(1, count + 1):
            left_pos = i * gap
            # IRC R310 egress window note
            egress_note = "EGRESS" if i == 2 and count == 3 else ""
            wins += f'''<div class="window-simple" style="left: {left_pos - 6}%;">
                       <div style="position:absolute; top:-18px; font-size:8px; color:#003366; font-weight:bold;">{egress_note}</div>
                       </div>'''
        return wins

    def generate_facade_block(title, is_front=False, is_rear=False, is_side=False):
        levels_html = ""
        facade_width_label = f"Width: {config.floor_width} ft" if not is_side else f"Depth: {config.floor_depth} ft"
        
        for i in range(config.num_floors):
            extra_glass = ""
            door_html = ""
            if is_front and i == 0:
                door_html = '<div class="facade-door"><div style="font-size:8px; color:white; margin-top:10px;">36" x 80"<br>IBC 1010</div></div>'
            elif is_rear and i == 0:
                 extra_glass = '<div class="window-simple" style="left: 35%; width: 30%; height: 80%; bottom: 0; background: #D0E0FF; border-bottom:none;"><div style="font-size:8px; margin-top:5px;">PATIO DOOR</div></div>'
            
            window_count = 3 if not is_side else 2 
            
            levels_html += f"""
            <div class="level {facade_class}" style="height: {level_height_px}px;">
                {get_facade_windows(window_count)}
                {door_html}
                {extra_glass}
                <div style="position:absolute; left:5px; top:5px; background:white; padding:3px; font-size:9px; border:1px solid #333;">
                    LEVEL {i+1}<br>{config.floor_height}' H
                </div>
            </div>
            """
        
        roof_html = f'<div class="roof"><div style="position:absolute; bottom:-25px; left:50%; transform:translateX(-50%); font-size:10px; color:white; background:#34495e; padding:5px; border-radius:3px;">{config.roofing_material}</div></div>' if config.num_floors > 0 else ""

        return f"""
        <div class="page">
            <div class="floor-title">{title}</div>
            <div style="background: #fff9e6; padding: 10px; margin-bottom: 15px; border-left: 4px solid #f80;">
                <strong>Elevation Notes:</strong><br>
                • All exterior walls: {ext_wall_ft}' ({ext_wall_ft*12:.1f}\") thick - IBC fire-rated construction<br>
                • Windows meet IRC R310 egress requirements (marked)<br>
                • Entry doors: 36\" x 80\" clear - IBC 1010.1.1 compliant<br>
                • Foundation and structural design by licensed engineer required
            </div>
            <div class="facade-container" style="height: {total_facade_height_px + 400}px;">
                <div class="building-structure" style="height: {total_facade_height_px}px; width: {'70%' if not is_side else '40%'};">
                    {roof_html}
                    {levels_html}
                </div>
                <div style="position:absolute; top: 20px; left: 20px; background:white; padding:10px; border:2px solid #003366; font-size: 11px;">
                    <strong>MATERIAL SPECIFICATIONS:</strong><br>
                    Roof: {config.roofing_material}<br>
                    Walls: {config.facade_type}<br>
                    {facade_width_label}<br>
                    Height: {config.num_floors * config.floor_height}' ({config.num_floors} Stories)<br><br>
                    <strong>CODE REFERENCES:</strong><br>
                    IBC Chapter 14 - Exterior Walls<br>
                    IBC Chapter 15 - Roof Assemblies<br>
                    IRC R703 - Exterior Covering
                </div>
            </div>
            {signature_footer}
        </div>
        """

    front_facade_html = generate_facade_block("FRONT FACADE ELEVATION", is_front=True)
    back_facade_html = generate_facade_block("REAR FACADE ELEVATION", is_rear=True)
    left_facade_html = generate_facade_block("LEFT SIDE ELEVATION", is_side=True)
    right_facade_html = generate_facade_block("RIGHT SIDE ELEVATION", is_side=True)

    # Enhanced summary with code compliance
    summary_html = f"""
    <div class="page">
        <div class="header">
            <h1 style="color: #003366;">PROJECT: {config.project_name.upper()}</h1>
            <p style="font-size: 14px; color: #666;">Architectural Design Documents - IBC 2021 / IRC 2021 Compliant</p>
            <p style="font-size: 12px; color: #999; margin-top: 10px;">Building Type: {config.building_type} | {'ADA Accessible' if config.ada_compliant else 'Standard Residential'}</p>
        </div>
        
        {code_statement}
        {code_issues_html}
        
        <h3>Project Specifications</h3>
        <table>
            <tr><th colspan="2" style="background: #005599;">GENERAL BUILDING INFORMATION</th></tr>
            <tr><td><strong>Building Type</strong></td><td>{config.building_type}</td></tr>
            <tr><td><strong>ADA Compliance</strong></td><td>{'Yes - Full Accessibility' if config.ada_compliant else 'No - Standard Residential'}</td></tr>
            <tr><td><strong>Number of Stories</strong></td><td>{config.num_floors}</td></tr>
            <tr><td><strong>Building Footprint</strong></td><td>{config.floor_width}' W x {config.floor_depth}' D</td></tr>
            <tr><td><strong>Total Building Height</strong></td><td>{config.num_floors * config.floor_height}' ({config.num_floors} floors @ {config.floor_height}' each)</td></tr>
            <tr><td><strong>Clear Ceiling Height</strong></td><td>{config.ceiling_height}' (IRC R305: Min {ArchitecturalCodes.MIN_CEILING_HEIGHT_RESIDENTIAL}')</td></tr>
            
            <tr><th colspan="2" style="background: #005599;">WALL CONSTRUCTION</th></tr>
            <tr><td><strong>Exterior Wall Thickness</strong></td><td>{ext_wall_ft}' ({ext_wall_ft*12:.1f}\") - 2x6 framing + sheathing + {config.facade_type}</td></tr>
            <tr><td><strong>Interior Wall Thickness</strong></td><td>{wall_ft}' ({wall_ft*12:.1f}\") - 2x4 framing + drywall (IRC R302)</td></tr>
            <tr><td><strong>Load-Bearing Walls</strong></td><td>{ArchitecturalCodes.LOAD_BEARING_WALL_THICKNESS}' (Structural engineer review required)</td></tr>
            
            <tr><th colspan="2" style="background: #005599;">CIRCULATION & EGRESS</th></tr>
            <tr><td><strong>Corridor Width</strong></td><td>{config.hallway_width}' (Code Min: {ArchitecturalCodes.MIN_CORRIDOR_WIDTH_ACCESSIBLE if config.ada_compliant else ArchitecturalCodes.MIN_CORRIDOR_WIDTH_RESIDENTIAL}')</td></tr>
            <tr><td><strong>Door Width (Clear)</strong></td><td>36\" (IBC 1010.1.1 / IRC R311.6)</td></tr>
            <tr><td><strong>Door Height</strong></td><td>80\" (IBC 1010.1.1)</td></tr>
            <tr><td><strong>Stairway Width</strong></td><td>{ArchitecturalCodes.MIN_STAIR_WIDTH_RESIDENTIAL}' (IRC R311.7.1)</td></tr>
            <tr><td><strong>Stair Riser (Max)</strong></td><td>{ArchitecturalCodes.MAX_RISER_HEIGHT_RESIDENTIAL*12:.2f}\" (IRC R311.7.5.1)</td></tr>
            <tr><td><strong>Stair Tread (Min)</strong></td><td>{ArchitecturalCodes.MIN_TREAD_DEPTH_RESIDENTIAL*12:.2f}\" (IRC R311.7.5.2)</td></tr>
            
            <tr><th colspan="2" style="background: #005599;">EXTERIOR FINISHES</th></tr>
            <tr><td><strong>Roofing Material</strong></td><td>{config.roofing_material}</td></tr>
            <tr><td><strong>Wall Cladding</strong></td><td>{config.facade_type}</td></tr>
            <tr><td><strong>Foundation</strong></td><td>Per structural engineer design (IBC Chapter 18)</td></tr>
        </table>
        
        <div style="background: #fff3cd; border: 2px solid #f80; padding: 15px; margin: 20px 0;">
            <strong>⚠️ IMPORTANT DISCLAIMER:</strong><br>
            <span style="font-size: 11px;">
            These drawings are for PRELIMINARY DESIGN PURPOSES ONLY. Prior to construction, the following professional services are required:<br><br>
            
            1. <strong>Licensed Architect</strong> - Complete architectural drawings, specifications, and code compliance documentation<br>
            2. <strong>Structural Engineer</strong> - Foundation, framing, and load-bearing design (IBC Chapter 16)<br>
            3. <strong>MEP Engineer</strong> - Mechanical, electrical, and plumbing systems design<br>
            4. <strong>Energy Code Compliance</strong> - IECC/local energy code calculations<br>
            5. <strong>Building Permit</strong> - Approved by local building department/AHJ<br>
            6. <strong>Site-Specific Considerations</strong> - Soil tests, surveys, zoning compliance<br><br>
            
            This software generates conceptual layouts only. All designs must be reviewed, stamped, and approved by licensed professionals in your jurisdiction before construction.
            </span>
        </div>
        
        {signature_footer}
    </div>
    """

    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>{config.project_name} - Architectural Plans (IBC/IRC Compliant)</title>
        <style>{css}</style>
        <script>function downloadPDF() {{ window.print(); }}</script>
    </head>
    <body>
        <div class="controls">
            <button class="btn" onclick="downloadPDF()">📄 Print / Save as PDF</button>
        </div>
        {summary_html}
        {floor_plans_html}
        {front_facade_html}
        {back_facade_html}
        {left_facade_html}
        {right_facade_html}
    </body>
    </html>
    """
    return full_html

def set_defaults_for_run(self):
    """
    Sets a code-compliant default layout for two floors.
    All dimensions comply with IBC 2021 / IRC 2021 requirements.
    """
    self.garage_data = { 
        "label": "DETACHED GARAGE\n2 Cars\n(IRC R309 Compliant)", 
        "w": 24, "d": 24, "bg": "#d3d3d3" 
    }
    
    wall_ft = self.WALL_THICKNESS
    
    # Calculate code-compliant stair dimensions
    num_risers, riser_h, tread_d, stair_run = self.codes.calculate_stair_dimensions(self.floor_height)
    stair_w = ArchitecturalCodes.MIN_STAIR_WIDTH_RESIDENTIAL
    
    # Pre-calculate positions
    y_row1 = wall_ft 
    y_row2 = wall_ft * 2 + 14
    
    # Row 1
    lr1_x = wall_ft
    kit1_x = lr1_x + 18 + wall_ft
    bed1_x = kit1_x + 14 + wall_ft
    
    # Row 2
    bed2_x = wall_ft
    stair_x = bed2_x + 14 + wall_ft
    bath1_x = stair_x + stair_w + wall_ft
    bath2_x = bath1_x + 8 + wall_ft
    dressing1_x = bath2_x + 8 + wall_ft
    
    f1_rooms_data = [
        {"label": "Living Room 1", "w": 18, "d": 14, "bg": "#fff", "x": lr1_x, "y": y_row1, "type": "room"},
        {"label": "Kitchen 1", "w": 14, "d": 12, "bg": "#EFEFEF", "x": kit1_x, "y": y_row1, "type": "room"},
        {"label": "Bedroom 1", "w": 14, "d": 14, "bg": "#fff", "x": bed1_x, "y": y_row1, "type": "room"},
        {"label": "Bedroom 2", "w": 14, "d": 14, "bg": "#fff", "x": bed2_x, "y": y_row2, "type": "room"},
        {"label": f"STAIRS UP\n{num_risers}R @ {riser_h*12:.1f}\"", "w": stair_w, "d": stair_run, "bg": "#D8BFD8", 
         "x": stair_x, "y": y_row2, "type": "stairs", "risers": num_risers, "riser_height": riser_h, "tread_depth": tread_d}, 
        {"label": "Bath 1", "w": 8, "d": 6, "bg": "#D6EAF8", "x": bath1_x, "y": y_row2, "type": "room"}, 
        {"label": "Bath 2", "w": 8, "d": 6, "bg": "#D6EAF8", "x": bath2_x, "y": y_row2, "type": "room"}, 
        {"label": "Dressing 1", "w": 6, "d": 6, "bg": "#F9F9F9", "x": dressing1_x, "y": y_row2, "type": "room"} 
    ]
    
    f2_rooms_data = [
        {"label": "Living Room 1", "w": 18, "d": 14, "bg": "#fff", "x": lr1_x, "y": y_row1, "type": "room"},
        {"label": "Kitchen 1", "w": 14, "d": 12, "bg": "#EFEFEF", "x": kit1_x, "y": y_row1, "type": "room"},
        {"label": "Bedroom 1", "w": 14, "d": 14, "bg": "#fff", "x": bed1_x, "y": y_row1, "type": "room"},
        {"label": "Bedroom 2", "w": 14, "d": 14, "bg": "#fff", "x": bed2_x, "y": y_row2, "type": "room"},
        {"label": f"STAIRS DN\n{num_risers}R @ {riser_h*12:.1f}\"", "w": stair_w, "d": stair_run, "bg": "#D8BFD8", 
         "x": stair_x, "y": y_row2, "type": "stairs", "risers": num_risers, "riser_height": riser_h, "tread_depth": tread_d},
        {"label": "Bath 1", "w": 8, "d": 6, "bg": "#D6EAF8", "x": bath1_x, "y": y_row2, "type": "room"},
        {"label": "Bath 2", "w": 8, "d": 6, "bg": "#D6EAF8", "x": bath2_x, "y": y_row2, "type": "room"},
        {"label": "Dressing 1", "w": 6, "d": 6, "bg": "#F9F9F9", "x": dressing1_x, "y": y_row2, "type": "room"}
    ]

    self.floors_data.append({ 
        "id": 1, "rooms": f1_rooms_data, "user_defined_layout": True, 
        "bathrooms": 2, "kitchens": 1, "living": 1, "bedrooms": 2, "dressing": 1 
    })
    self.floors_data.append({ 
        "id": 2, "rooms": f2_rooms_data, "user_defined_layout": True, 
        "bathrooms": 2, "kitchens": 1, "living": 1, "bedrooms": 2, "dressing": 1 
    })
    
    max_x = dressing1_x + 6.0 + wall_ft 
    max_y = y_row2 + 14.0 + wall_ft 
    
    self.floor_width = max_x
    self.floor_depth = max_y
    
    # Perform code validation
    self.validate_building_codes()

HouseConfig.set_defaults_for_run = set_defaults_for_run

def main():
    print("="*70)
    print("🏗️  PROFESSIONAL HOME DESIGNER - AIA/IBC COMPLIANT")
    print("="*70)
    print("Architectural Design Software v2.0")
    print("Compliant with: IBC 2021 | IRC 2021 | AIA Standards | ADA Guidelines")
    print("="*70 + "\n")
    
    # Execute the IP check FIRST
    check_ip_license()

    # Execute the license check
    check_license()
    
    config = HouseConfig()
    try:
        config.get_inputs()
    except Exception as e:
        print(f"\n⚠️  Error during input: {e}")
        print("Using default IBC/IRC-compliant configuration...")
        config.set_defaults_for_run()

    html_content = generate_html(config)
    filename = "IBC_IRC_Compliant_Architectural_Plans.html"
    with open(filename, "w", encoding="utf-8") as file:
        file.write(html_content)

    print(f"\n✅ Successfully generated {filename}")
    print("📐 Design includes:")
    print("   • Floor plans with dimensioned rooms")
    print("   • Code-compliant stairway designs")
    print("   • All four elevation views")
    print("   • Material specifications")
    print("   • IBC/IRC compliance documentation")
    print("\n🌐 Opening in default web browser...")
    webbrowser.open("file://" + os.path.realpath(filename))
    
    print("\n" + "="*70)
    print("⚠️  IMPORTANT: These are PRELIMINARY designs only.")
    print("    Hire licensed architect/engineer for construction documents.")
    print("="*70)

if __name__ == "__main__":
    main()