#!/usr/bin/env python3
"""
WSCHIMNEY - Wind and Seismic Load Analysis for Concrete Chimneys with Pile Foundations
Version: Rev.11 (Fixed Deflection)
Author: Professional Engineering Software
Date: 2024
"""

import numpy as np # pyright: ignore[reportMissingImports]
import pandas as pd # pyright: ignore[reportMissingModuleSource]
import math
import matplotlib.pyplot as plt # pyright: ignore[reportMissingModuleSource]
from scipy.interpolate import interp1d # pyright: ignore[reportMissingImports]
import ezdxf # pyright: ignore[reportMissingImports]
from ezdxf import units # pyright: ignore[reportMissingImports]
import warnings
import traceback
from typing import List, Tuple, Dict, Any, Optional
import sys
import os
from datetime import datetime

warnings.filterwarnings('ignore')

# ================================================================================
# 1. MATERIAL PROPERTIES AND DESIGN PARAMETERS
# ================================================================================

class MaterialProperties:
    """Define material properties for concrete and steel"""
    
    def __init__(self):
        # Concrete grades (MPa)
        self.concrete_grades = {
            "C25": {"fck": 25, "fctm": 2.6, "Ecm": 31000},
            "C30": {"fck": 30, "fctm": 2.9, "Ecm": 33000},
            "C35": {"fck": 35, "fctm": 3.2, "Ecm": 34000},
            "C40": {"fck": 40, "fctm": 3.5, "Ecm": 35000},
            "C45": {"fck": 45, "fctm": 3.8, "Ecm": 36000},
            "C50": {"fck": 50, "fctm": 4.1, "Ecm": 37000}
        }
        
        # Steel grades (MPa)
        self.steel_grades = {
            "420": {"fyk": 420, "Es": 200000},
            "500": {"fyk": 500, "Es": 200000},
            "550": {"fyk": 550, "Es": 200000}
        }
        
        # Safety factors (Eurocode)
        self.gamma_c = 1.5  # Concrete
        self.gamma_s = 1.15  # Steel
        self.gamma_g = 1.35  # Permanent loads
        self.gamma_q = 1.5   # Variable loads

# ================================================================================
# 2. CHIMNEY GEOMETRY
# ================================================================================

class ChimneyGeometry:
    """Define chimney geometry and properties"""
    
    def __init__(self, height: float, top_diameter: float, bottom_diameter: float, 
                 wall_thickness: float, openings: List[Dict] = None):
        self.height = height
        self.top_diameter = top_diameter
        self.bottom_diameter = bottom_diameter
        self.wall_thickness = wall_thickness
        self.openings = openings or []
        
    def diameter_at_height(self, z: float) -> float:
        """Get diameter at given height (linear interpolation)"""
        if z < 0 or z > self.height:
            raise ValueError(f"Height {z}m is outside chimney range (0-{self.height}m)")
        
        # Linear interpolation
        return self.bottom_diameter - (self.bottom_diameter - self.top_diameter) * (z / self.height)
    
    def area_at_height(self, z: float) -> float:
        """Get cross-sectional area at given height"""
        d = self.diameter_at_height(z)
        t = self.wall_thickness
        return math.pi * d * t  # Approximate for thin walls
    
    def moment_of_inertia_at_height(self, z: float) -> float:
        """Get moment of inertia at given height"""
        d = self.diameter_at_height(z)
        t = self.wall_thickness
        # For thin-walled cylinder
        return (math.pi / 8) * d**3 * t
    
    def weight_per_unit_height(self, z: float, concrete_density: float = 25) -> float:
        """Calculate weight per meter height at given elevation"""
        area = self.area_at_height(z)
        return area * concrete_density * 9.81 / 1000  # kN/m

# ================================================================================
# 3. WIND LOAD CALCULATION (Eurocode 1-4)
# ================================================================================

class WindLoadAnalysis:
    """Calculate wind loads according to Eurocode 1-4"""
    
    def __init__(self, basic_wind_speed: float, terrain_category: str = "II", 
                 chimney_height: float = 50.0, country: str = "UK"):
        self.vb0 = basic_wind_speed  # Basic wind speed (m/s)
        self.terrain_category = terrain_category
        self.height = chimney_height
        self.country = country
        
        # Terrain factors
        self.terrain_factors = {
            "0": {"z0": 0.003, "zmin": 1},
            "I": {"z0": 0.01, "zmin": 1},
            "II": {"z0": 0.05, "zmin": 2},
            "III": {"z0": 0.3, "zmin": 5},
            "IV": {"z0": 1.0, "zmin": 10}
        }
        
        # Importance factors (based on consequence class)
        self.importance_factors = {
            "CC1": 0.8,   # Low consequence
            "CC2": 1.0,   # Medium consequence
            "CC3": 1.2    # High consequence
        }
        
        # Orography factor (assume 1.0 for flat terrain)
        self.co = 1.0
        
    def mean_wind_speed(self, z: float) -> float:
        """Calculate mean wind speed at height z"""
        terrain = self.terrain_factors.get(self.terrain_category, self.terrain_factors["II"])
        z0 = terrain["z0"]
        zmin = terrain["zmin"]
        
        if z < zmin:
            z = zmin
            
        # Terrain roughness factor
        kr = 0.19 * (z0 / 0.05) ** 0.07
        cr = kr * math.log(max(z, z0) / z0) if z0 > 0 else 1.0
        
        return self.vb0 * self.co * cr
    
    def peak_velocity_pressure(self, z: float, importance_class: str = "CC2") -> float:
        """Calculate peak velocity pressure at height z"""
        vm = self.mean_wind_speed(z)
        
        # Turbulence intensity
        terrain = self.terrain_factors.get(self.terrain_category, self.terrain_factors["II"])
        z0 = terrain["z0"]
        zmin = terrain["zmin"]
        
        if z < zmin:
            z = zmin
            
        k1 = 1.0  # Turbulence factor
        if z > 0 and z0 > 0 and self.co * math.log(max(z, z0) / z0) > 0:
            Iv = k1 / (self.co * math.log(max(z, z0) / z0))
        else:
            Iv = 0.15  # Default value
        
        # Importance factor
        gamma = self.importance_factors.get(importance_class, 1.0)
        
        # Air density (kg/m³)
        rho = 1.25
        
        # Peak velocity pressure
        qp = (1 + 7 * Iv) * 0.5 * rho * vm**2 * gamma
        
        return qp
    
    def wind_force_on_segment(self, z_center: float, segment_height: float, 
                            diameter: float, force_coefficient: float = 1.0) -> float:
        """Calculate wind force on a chimney segment"""
        qp = self.peak_velocity_pressure(z_center)
        
        # Reference area
        A_ref = diameter * segment_height
        
        # Wind force
        Fw = qp * A_ref * force_coefficient / 1000  # Convert to kN
        
        return Fw
    
    def wind_moment_at_base(self, chimney: ChimneyGeometry, num_segments: int = 20) -> float:
        """Calculate total wind moment at chimney base"""
        segment_height = chimney.height / num_segments
        total_moment = 0.0
        
        for i in range(num_segments):
            z_center = (i + 0.5) * segment_height
            diameter = chimney.diameter_at_height(z_center)
            force = self.wind_force_on_segment(z_center, segment_height, diameter)
            moment_arm = z_center
            total_moment += force * moment_arm
            
        return total_moment
    
    def wind_shear_at_base(self, chimney: ChimneyGeometry, num_segments: int = 20) -> float:
        """Calculate total wind shear at chimney base"""
        segment_height = chimney.height / num_segments
        total_shear = 0.0
        
        for i in range(num_segments):
            z_center = (i + 0.5) * segment_height
            diameter = chimney.diameter_at_height(z_center)
            force = self.wind_force_on_segment(z_center, segment_height, diameter)
            total_shear += force
            
        return total_shear

# ================================================================================
# 4. SEISMIC LOAD ANALYSIS (Eurocode 8)
# ================================================================================

class SeismicLoadAnalysis:
    """Calculate seismic loads according to Eurocode 8"""
    
    def __init__(self, ag: float, soil_type: str, importance_class: str = "II", 
                 behavior_factor: float = 2.0, damping_ratio: float = 0.05):
        self.ag = ag  # Design ground acceleration (g)
        self.soil_type = soil_type
        self.importance_class = importance_class
        self.behavior_factor = behavior_factor
        self.damping_ratio = damping_ratio
        
        # Soil factors
        self.soil_factors = {
            "A": {"S": 1.0, "TB": 0.15, "TC": 0.4, "TD": 2.0},
            "B": {"S": 1.2, "TB": 0.15, "TC": 0.5, "TD": 2.0},
            "C": {"S": 1.15, "TB": 0.20, "TC": 0.6, "TD": 2.0},
            "D": {"S": 1.35, "TB": 0.20, "TC": 0.8, "TD": 2.0},
            "E": {"S": 1.4, "TB": 0.15, "TC": 0.5, "TD": 2.0}
        }
        
        # Importance factors
        self.importance_factors_ec8 = {
            "I": 0.8,   # Low importance
            "II": 1.0,  # Normal importance
            "III": 1.2, # High importance
            "IV": 1.4   # Very high importance
        }
        
        # Convert ag from g to m/s²
        self.ag_ms2 = ag * 9.81
        
    def design_spectrum(self, T: float) -> float:
        """Get spectral acceleration for given period"""
        soil = self.soil_factors.get(self.soil_type, self.soil_factors["C"])
        S = soil["S"]
        TB = soil["TB"]
        TC = soil["TC"]
        TD = soil["TD"]
        
        importance_factor = self.importance_factors_ec8.get(self.importance_class, 1.0)
        ag_design = self.ag_ms2 * importance_factor
        
        if T <= TB:
            Sd = ag_design * S * (1 + (T/TB) * (2.5 - 1))
        elif T <= TC:
            Sd = ag_design * S * 2.5
        elif T <= TD:
            Sd = ag_design * S * 2.5 * (TC/T)
        else:
            Sd = ag_design * S * 2.5 * (TC * TD / T**2)
            
        return Sd / self.behavior_factor
    
    def fundamental_period(self, chimney: ChimneyGeometry) -> float:
        """Estimate fundamental period of chimney"""
        # Empirical formula for cantilever chimney
        H = chimney.height
        D_top = chimney.top_diameter
        D_base = chimney.bottom_diameter
        
        # Average diameter
        D_avg = (D_top + D_base) / 2
        
        # Approximate period (seconds) - Improved formula for tall chimneys
        if H > 150:
            # Special handling for very tall chimneys
            T = 0.000015 * H**2 / (D_avg if D_avg > 0 else 1.0)
        else:
            T = 0.000023 * H**2 / (D_avg if D_avg > 0 else 1.0)
        
        return max(T, 0.1)  # Minimum period
    
    def base_shear(self, chimney: ChimneyGeometry, total_weight: float) -> float:
        """Calculate seismic base shear"""
        T = self.fundamental_period(chimney)
        Sd = self.design_spectrum(T)
        
        # Base shear (kN)
        Fb = Sd * total_weight / 9.81
        
        return Fb
    
    def seismic_moment_at_base(self, chimney: ChimneyGeometry, total_weight: float) -> float:
        """Calculate seismic moment at base"""
        Fb = self.base_shear(chimney, total_weight)
        
        # Simplified: assume triangular distribution
        M_seismic = 0.67 * Fb * chimney.height
        
        return M_seismic

# ================================================================================
# 5. PILE FOUNDATION DESIGN
# ================================================================================

class PileFoundation:
    """Design pile foundation for chimney"""
    
    def __init__(self, soil_properties: Dict, pile_type: str = "bored"):
        self.soil_properties = soil_properties
        self.pile_type = pile_type
        
        # Pile capacity factors
        self.pile_factors = {
            "bored": {"alpha": 0.5, "beta": 0.3, "Nq": 30},
            "driven": {"alpha": 0.7, "beta": 0.5, "Nq": 40},
            "micropile": {"alpha": 0.8, "beta": 0.4, "Nq": 50}
        }
        
    def single_pile_capacity(self, diameter: float, length: float, 
                           soil_layers: List[Dict]) -> Tuple[float, float]:
        """Calculate ultimate capacity of single pile"""
        factors = self.pile_factors.get(self.pile_type, self.pile_factors["bored"])
        alpha = factors["alpha"]
        beta = factors["beta"]
        Nq = factors["Nq"]
        
        # Shaft resistance
        Qs = 0.0
        remaining_length = length
        
        for layer in soil_layers:
            if remaining_length <= 0:
                break
                
            layer_length = min(remaining_length, layer.get("thickness", 0))
            if layer_length <= 0:
                continue
                
            # Shaft friction
            if "cu" in layer:  # Clay
                adhesion = alpha * layer["cu"]
            elif "sigma_v" in layer:  # Sand
                adhesion = beta * layer["sigma_v"]
            else:
                adhesion = 0
                
            Qs += math.pi * diameter * layer_length * adhesion
            
            remaining_length -= layer_length
        
        # Base resistance
        if soil_layers:
            bottom_layer = soil_layers[-1]
            Ab = math.pi * diameter**2 / 4
            
            if "cu" in bottom_layer:  # Clay
                Nc = 9.0
                Qb = Nc * bottom_layer["cu"] * Ab
            elif "sigma_v" in bottom_layer:  # Sand
                sigma_v = bottom_layer.get("sigma_v", 100)
                Qb = Ab * sigma_v * Nq
            else:
                Qb = 0
        else:
            Qb = 0
        
        Q_ult = Qs + Qb
        
        # Allowable capacity (FS = 2.5)
        Q_all = Q_ult / 2.5 if Q_ult > 0 else 0
        
        return Q_all, Q_ult
    
    def required_piles(self, total_load: float, moment: float, 
                     pile_diameter: float, pile_length: float,
                     soil_layers: List[Dict], arrangement: str = "circular",
                     foundation_diameter: float = None) -> Dict:
        """Calculate required number and arrangement of piles"""
        
        # Single pile capacity
        Q_all, Q_ult = self.single_pile_capacity(pile_diameter, pile_length, soil_layers)
        
        if Q_all <= 0:
            raise ValueError("Pile capacity calculation failed. Check soil parameters.")
        
        # Estimate number based on vertical load
        n_min = max(1, math.ceil(total_load / Q_all))
        
        # Consider moment effect
        n_piles = n_min
        
        if arrangement == "circular" and foundation_diameter:
            # Piles in circular arrangement
            radius = foundation_diameter / 2
            # Initial guess
            n_piles = max(n_min, 6)  # Minimum 6 piles for circular arrangement
            
            # Check moment capacity
            for n in range(n_piles, n_piles + 10):
                # Calculate moment capacity
                moment_capacity = 0
                for i in range(n):
                    angle = 2 * math.pi * i / n
                    r = radius
                    moment_capacity += Q_all * r
                
                if moment_capacity >= moment * 1.5:  # FS for moment
                    n_piles = n
                    break
        
        # Final arrangement
        if arrangement == "circular":
            optimal_n = self.optimal_circular_arrangement(n_piles, foundation_diameter)
        else:
            optimal_n = n_piles
        
        # Calculate pile loads
        pile_loads = self.calculate_pile_loads(total_load, moment, optimal_n, 
                                             foundation_diameter, arrangement)
        
        # Check all piles within capacity
        if pile_loads:
            max_pile_load = max(pile_loads)
            if max_pile_load > Q_all:
                # Increase number of piles
                scale_factor = max_pile_load / Q_all
                optimal_n = math.ceil(optimal_n * scale_factor)
                pile_loads = self.calculate_pile_loads(total_load, moment, optimal_n,
                                                     foundation_diameter, arrangement)
        
        return {
            "number_of_piles": optimal_n,
            "pile_diameter": pile_diameter,
            "pile_length": pile_length,
            "single_pile_capacity": Q_all,
            "pile_loads": pile_loads,
            "max_pile_load": max(pile_loads) if pile_loads else 0,
            "safety_factor": Q_all / (max(pile_loads) if pile_loads else 1),
            "total_load": total_load
        }
    
    def optimal_circular_arrangement(self, n_piles: int, diameter: float) -> int:
        """Find optimal number of piles for circular arrangement"""
        # Common optimal numbers for circular patterns
        optimal_numbers = [6, 8, 12, 16, 20, 24]
        
        for n in optimal_numbers:
            if n >= n_piles:
                return n
        
        return optimal_numbers[-1]
    
    def calculate_pile_loads(self, total_load: float, moment: float, n_piles: int,
                           foundation_diameter: float, arrangement: str) -> List[float]:
        """Calculate load on each pile"""
        if n_piles <= 0:
            return []
            
        if arrangement == "circular" and foundation_diameter:
            radius = foundation_diameter / 2
            
            # Initialize pile loads with vertical component
            vertical_load_per_pile = total_load / n_piles
            
            # Calculate moment-induced loads
            pile_locations = []
            for i in range(n_piles):
                angle = 2 * math.pi * i / n_piles
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                pile_locations.append((x, y))
            
            # Simplified: assume moment in one direction
            if pile_locations:
                max_distance = max(abs(x) for x, y in pile_locations)
                if max_distance == 0:
                    max_distance = 1
            else:
                max_distance = 1
            
            pile_loads = []
            for x, y in pile_locations:
                # Moment contribution (simplified)
                moment_load = (moment * abs(x)) / (n_piles * max_distance) if n_piles > 0 and max_distance > 0 else 0
                total_pile_load = vertical_load_per_pile + moment_load
                pile_loads.append(max(total_pile_load, 0))
            
            return pile_loads
        
        return [total_load / n_piles] * n_piles if n_piles > 0 else []

# ================================================================================
# 6. REINFORCEMENT DESIGN
# ================================================================================

class ReinforcementDesign:
    """Design reinforcement for chimney wall"""
    
    def __init__(self, material_props: MaterialProperties):
        self.materials = material_props
        
    def chimney_wall_reinforcement(self, axial_load: float, moment: float, 
                                 diameter: float, thickness: float,
                                 concrete_grade: str = "C35", 
                                 steel_grade: str = "500") -> Dict:
        """Design reinforcement for chimney wall section"""
        
        # Material properties
        concrete_props = self.materials.concrete_grades.get(concrete_grade, self.materials.concrete_grades["C35"])
        steel_props = self.materials.steel_grades.get(steel_grade, self.materials.steel_grades["500"])
        
        fck = concrete_props["fck"]
        fyk = steel_props["fyk"]
        
        # Design strengths
        fcd = fck / self.materials.gamma_c
        fyd = fyk / self.materials.gamma_s
        
        # Section properties
        D = diameter
        t = thickness
        
        # Effective depth
        d_eff = max(t - 0.05, 0.01)  # Assuming 50mm cover, minimum 10mm
        
        # Effective width (approximation)
        b_eff = math.pi * D  # Circumference
        
        # Required reinforcement for moment
        M_ed = abs(moment)
        
        # Avoid division by zero
        denominator = fcd * b_eff * d_eff**2
        if denominator > 0:
            K = M_ed / denominator
        else:
            K = 0
        
        if K > 0.208:  # Over-reinforced
            # Need compression reinforcement
            K_lim = 0.208
            M_lim = K_lim * fcd * b_eff * d_eff**2
            M2 = M_ed - M_lim
            
            # Compression reinforcement
            d_prime = 0.05  # Cover to compression steel
            if fyd * (d_eff - d_prime) > 0:
                A_s2 = M2 / (fyd * (d_eff - d_prime))
            else:
                A_s2 = 0
            
            # Tension reinforcement for balanced section
            z_lim = d_eff * (0.5 + math.sqrt(max(0.25 - K_lim/0.9, 0)))
            if fyd * z_lim > 0:
                A_s1_lim = M_lim / (fyd * z_lim)
            else:
                A_s1_lim = 0
            
            A_s_req = A_s1_lim + A_s2
        else:
            # Singly reinforced
            z = d_eff * (0.5 + math.sqrt(max(0.25 - K/0.9, 0)))
            z = min(z, 0.95 * d_eff)
            
            if fyd * z > 0:
                A_s_req = M_ed / (fyd * z)
            else:
                A_s_req = 0
        
        # Add reinforcement for axial load
        N_ed = abs(axial_load)
        if fyd > 0:
            A_s_axial = max(0, N_ed / fyd)
        else:
            A_s_axial = 0
        
        # Total required area
        A_s_total = A_s_req + A_s_axial
        
        # Minimum reinforcement
        A_c = math.pi * D * t  # Wall area
        A_s_min = max(0.002 * A_c, A_s_total * 0.5)  # 0.2% minimum
        
        A_s_total = max(A_s_total, A_s_min)
        
        # Reinforcement ratio
        rho = A_s_total / A_c * 0.01 if A_c > 0 else 0
        
        # Bar selection
        bar_diameter = self.select_bar_diameter(A_s_total, rho)
        
        return {
            "total_area": A_s_total,
            "minimum_area": A_s_min,
            "reinforcement_ratio": rho * 100,  # Percentage
            "bar_diameter": bar_diameter,
            "bars_per_meter": A_s_total / (math.pi * (bar_diameter/1000)**2 / 4) if bar_diameter > 0 else 0,
            "concrete_grade": concrete_grade,
            "steel_grade": steel_grade
        }
    
    def select_bar_diameter(self, area_required: float, rho: float) -> float:
        """Select appropriate bar diameter"""
        # Common bar diameters (mm)
        bar_sizes = [10, 12, 16, 20, 25, 32, 40]
        
        # Area per bar
        for dia in bar_sizes:
            area_per_bar = math.pi * (dia/1000)**2 / 4
            if area_per_bar * 0.8 <= area_required / 10:  # 10 bars as reference
                return dia
        
        return bar_sizes[-1]  # Return largest if none suitable

# ================================================================================
# 7. SERVICEABILITY CHECKS - FIXED DEFLECTION CALCULATION
# ================================================================================

class ServiceabilityChecks:
    """Perform serviceability limit state checks"""
    
    def __init__(self, materials: MaterialProperties):
        self.materials = materials
        
    def deflection_check(self, chimney: ChimneyGeometry, wind_load: WindLoadAnalysis,
                        wind_moment: float) -> Tuple[bool, float, float]:
        """Check chimney deflection under wind load - CORRECTED"""
        
        # Maximum allowable deflection (H/300)
        delta_max = chimney.height / 300
        
        # Get material properties
        E = self.materials.concrete_grades["C35"]["Ecm"]  # MPa
        E = E * 1000  # Convert to kN/m²
        
        # Calculate deflection using numerical integration
        # For a cantilever with distributed wind load
        num_segments = 50
        segment_height = chimney.height / num_segments
        
        # Calculate total wind force and its distribution
        total_force = 0.0
        forces = []
        heights = []
        
        for i in range(num_segments):
            z_center = (i + 0.5) * segment_height
            diameter = chimney.diameter_at_height(z_center)
            force = wind_load.wind_force_on_segment(z_center, segment_height, diameter)
            total_force += force
            forces.append(force)
            heights.append(z_center)
        
        # Calculate deflection at top using moment-area method
        # For cantilever: delta = integral(M*x/EI dx) from 0 to H
        delta_top = 0.0
        
        for i in range(num_segments):
            z = heights[i]
            # Moment at this location from all forces above
            M = 0.0
            for j in range(i, num_segments):
                M += forces[j] * (heights[j] - z)
            
            # Moment of inertia at this height
            I = chimney.moment_of_inertia_at_height(z)
            
            # Curvature contribution
            if E * I > 0:
                # Distance from this point to top
                distance_to_top = chimney.height - z
                # Deflection contribution using double integration
                delta_top += (M * distance_to_top * segment_height) / (E * I)
        
        # Additional correction for tip deflection
        # Using PL³/3EI for equivalent concentrated load at centroid
        I_base = chimney.moment_of_inertia_at_height(0)
        if E * I_base > 0:
            equivalent_height = 0.67 * chimney.height  # Centroid of triangular load
            delta_equivalent = (total_force * equivalent_height * chimney.height**2) / (3 * E * I_base)
            # Use the larger of the two calculations
            delta_top = max(delta_top, delta_equivalent)
        
        return delta_top <= delta_max, delta_top, delta_max
    
    def crack_width_check(self, axial_load: float, moment: float,
                         reinforcement: Dict, diameter: float, 
                         thickness: float, exposure_class: str = "XC3") -> Tuple[bool, float, float]:
        """Check crack width"""
        
        # Maximum allowable crack width (mm)
        max_crack_widths = {
            "XC1": 0.4,   # Dry environment
            "XC2": 0.3,   # Wet, rarely dry
            "XC3": 0.3,   # Moderate humidity
            "XC4": 0.2,   # Cyclic wet/dry,
            "XD1": 0.2,   # Chloride exposure
            "XS1": 0.2    # Sea water
        }
        
        w_max = max_crack_widths.get(exposure_class, 0.3)
        
        # Simplified crack width calculation
        # Using Eurocode 2 formula
        A_s = reinforcement.get("total_area", 0)
        bar_dia = reinforcement.get("bar_diameter", 0) / 1000  # Convert to m
        A_c = math.pi * diameter * thickness
        
        if A_s <= 0 or bar_dia <= 0:
            return True, 0, w_max  # No reinforcement, no cracking
        
        # Stress in reinforcement
        fyd = self.materials.steel_grades["500"]["fyk"] / self.materials.gamma_s
        sigma_s = min(abs(axial_load) / A_s, fyd) if A_s > 0 else 0
        
        # Crack width (simplified)
        kt = 0.4  # Long-term loading
        eps_sm = sigma_s / 200000  # Strain
        
        # Bar spacing
        if A_s > 0:
            s = (math.pi * diameter) / (A_s / (math.pi * (bar_dia/2)**2))
        else:
            s = 0.2  # Default spacing
        
        # Crack width
        w_k = 1.7 * kt * eps_sm * s
        
        return w_k * 1000 <= w_max, w_k * 1000, w_max

# ================================================================================
# 8. COST ESTIMATION
# ================================================================================

class CostEstimation:
    """Estimate construction costs"""
    
    def __init__(self, location: str = "Europe"):
        self.location = location
        # Unit costs (EUR)
        self.unit_costs = {
            "concrete": {
                "C25": 120,   # EUR/m³
                "C30": 130,
                "C35": 140,
                "C40": 150,
                "C45": 165,
                "C50": 180
            },
            "reinforcement": {
                "420": 800,   # EUR/ton
                "500": 850,
                "550": 900
            },
            "piling": {
                "bored": 250,     # EUR/m³
                "driven": 200,
                "micropile": 300
            },
            "formwork": 50,       # EUR/m²
            "labor": 80,         # EUR/hour
            "equipment": 2000    # EUR/day
        }
        
    def estimate_total_cost(self, chimney: ChimneyGeometry, piles: Dict,
                          reinforcement: Dict, construction_time: float = 90) -> Dict:
        """Estimate total construction cost"""
        
        # 1. Concrete volume for chimney
        concrete_volume = 0
        num_segments = 20
        segment_height = chimney.height / num_segments
        
        for i in range(num_segments):
            z_center = (i + 0.5) * segment_height
            d = chimney.diameter_at_height(z_center)
            area = math.pi * d * chimney.wall_thickness
            concrete_volume += area * segment_height
        
        # 2. Reinforcement weight
        reinforcement_weight = reinforcement.get("total_area", 0) * chimney.height * 7850  # kg
        
        # 3. Piling cost
        pile_volume = piles.get("number_of_piles", 0) * math.pi * (piles.get("pile_diameter", 0)/2)**2 * piles.get("pile_length", 0)
        
        # 4. Calculate costs
        concrete_grade = reinforcement.get("concrete_grade", "C35")
        steel_grade = reinforcement.get("steel_grade", "500")
        pile_type = "bored"  # Default
        
        # Get unit cost, use default if not found
        concrete_unit_cost = self.unit_costs["concrete"].get(concrete_grade, 140)
        steel_unit_cost = self.unit_costs["reinforcement"].get(steel_grade, 850)
        piling_unit_cost = self.unit_costs["piling"].get(pile_type, 250)
        
        # Calculate surface area for formwork
        avg_diameter = (chimney.bottom_diameter + chimney.top_diameter) / 2
        formwork_area = math.pi * avg_diameter * chimney.height
        
        costs = {
            "concrete": concrete_volume * concrete_unit_cost,
            "reinforcement": (reinforcement_weight / 1000) * steel_unit_cost,
            "piling": pile_volume * piling_unit_cost,
            "formwork": formwork_area * self.unit_costs["formwork"],
            "labor": construction_time * 8 * 5 * self.unit_costs["labor"],  # 8h/day, 5 workers
            "equipment": (construction_time / 30) * self.unit_costs["equipment"]  # Monthly
        }
        
        total_cost = sum(costs.values())
        
        # Add contingencies (20%)
        contingency = total_cost * 0.2
        total_with_contingency = total_cost + contingency
        
        return {
            "itemized_costs": costs,
            "contingency": contingency,
            "total_cost": total_with_contingency,
            "concrete_volume": concrete_volume,
            "reinforcement_weight": reinforcement_weight,
            "pile_volume": pile_volume,
            "formwork_area": formwork_area
        }

# ================================================================================
# 9. REPORT GENERATION
# ================================================================================

class ReportGenerator:
    """Generate comprehensive design report"""
    
    def __init__(self, project_name: str = "Chimney Design Project"):
        self.project_name = project_name
        self.report_sections = []
        
    def add_section(self, title: str, content: str):
        """Add a section to the report"""
        self.report_sections.append({"title": title, "content": content})
    
    def generate_report(self, filename: str = "chimney_design_report.txt"):
        """Generate and save the report"""
        
        report = f"""
{'='*80}
{self.project_name.upper():^80}
{'='*80}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*80}

"""
        
        for section in self.report_sections:
            report += f"\n{section['title']}\n{'-'*len(section['title'])}\n"
            report += section['content'] + "\n"
        
        # Save to file
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(f"✓ Report generated: {filename}")
        except Exception as e:
            print(f"✗ Error saving report: {e}")
        
        return report

# ================================================================================
# 10. VISUALIZATION
# ================================================================================

class Visualization:
    """Create visualization of chimney and foundation"""
    
    def plot_chimney_elevation(self, chimney: ChimneyGeometry, save_path: str = None):
        """Plot chimney elevation"""
        
        try:
            fig, ax = plt.subplots(figsize=(10, 12))
            
            # Create chimney profile
            heights = np.linspace(0, chimney.height, 100)
            diameters = [chimney.diameter_at_height(h) for h in heights]
            
            # Plot outer surface
            ax.plot(diameters, heights, 'b-', linewidth=2, label='Outer Surface')
            ax.plot([-d for d in diameters], heights, 'b-', linewidth=2)
            
            # Plot inner surface
            inner_diameters = [max(d - 2*chimney.wall_thickness, 0.1) for d in diameters]
            ax.plot(inner_diameters, heights, 'r--', linewidth=1, label='Inner Surface')
            ax.plot([-d for d in inner_diameters], heights, 'r--', linewidth=1)
            
            # Fill between
            ax.fill_betweenx(heights, diameters, inner_diameters, 
                            alpha=0.3, color='blue', label='Wall Thickness')
            ax.fill_betweenx(heights, [-d for d in diameters], 
                            [-d for d in inner_diameters], alpha=0.3, color='blue')
            
            # Formatting
            ax.set_xlabel('Diameter (m)')
            ax.set_ylabel('Height (m)')
            ax.set_title('Chimney Elevation')
            ax.grid(True, alpha=0.3)
            ax.axvline(x=0, color='k', linestyle='-', linewidth=0.5)
            ax.legend()
            ax.set_aspect('equal', adjustable='box')
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"✓ Elevation plot saved: {save_path}")
            
            plt.show()
            plt.close(fig)
            
        except Exception as e:
            print(f"✗ Error creating elevation plot: {e}")
    
    def plot_foundation_plan(self, pile_coords: List[Tuple], pile_diameter: float,
                           chimney_diameter: float, foundation_diameter: float,
                           save_path: str = None):
        """Plot foundation plan view"""
        
        try:
            fig, ax = plt.subplots(figsize=(10, 10))
            
            # Plot foundation
            foundation_circle = plt.Circle((0, 0), foundation_diameter/2, 
                                          fill=False, linestyle='-', 
                                          linewidth=2, color='orange', 
                                          label='Foundation')
            ax.add_artist(foundation_circle)
            
            # Plot chimney
            chimney_circle = plt.Circle((0, 0), chimney_diameter/2, 
                                       fill=False, linestyle='--', 
                                       linewidth=2, color='red', 
                                       label='Chimney')
            ax.add_artist(chimney_circle)
            
            # Plot piles
            for i, (x, y) in enumerate(pile_coords, 1):
                pile = plt.Circle((x, y), pile_diameter/2, 
                                 fill=True, color='green', alpha=0.7)
                ax.add_artist(pile)
                
                # Add pile number
                ax.text(x, y, f'P{i}', ha='center', va='center', 
                       color='white', fontweight='bold', fontsize=8)
            
            # Formatting
            ax.set_xlabel('X Coordinate (m)')
            ax.set_ylabel('Y Coordinate (m)')
            ax.set_title('Foundation Plan View')
            ax.grid(True, alpha=0.3)
            ax.set_aspect('equal', adjustable='box')
            ax.legend()
            
            # Set limits
            limit = foundation_diameter * 0.6
            ax.set_xlim(-limit, limit)
            ax.set_ylim(-limit, limit)
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"✓ Foundation plan saved: {save_path}")
            
            plt.show()
            plt.close(fig)
            
        except Exception as e:
            print(f"✗ Error creating foundation plan: {e}")
            
        except Exception as e:
            print(f"✗ Error creating elevation plot: {e}")
    
    def plot_foundation_plan(self, pile_coords: List[Tuple], pile_diameter: float,
                           chimney_diameter: float, foundation_diameter: float,
                           save_path: str = None):
        """Plot foundation plan view"""
        
        try:
            fig, ax = plt.subplots(figsize=(10, 10))
            
            # Plot foundation
            foundation_circle = plt.Circle((0, 0), foundation_diameter/2, 
                                          fill=False, linestyle='-', 
                                          linewidth=2, color='orange', 
                                          label='Foundation')
            ax.add_artist(foundation_circle)
            
            # Plot chimney
            chimney_circle = plt.Circle((0, 0), chimney_diameter/2, 
                                       fill=False, linestyle='--', 
                                       linewidth=2, color='red', 
                                       label='Chimney')
            ax.add_artist(chimney_circle)
            
            # Plot piles
            for i, (x, y) in enumerate(pile_coords):
                pile = plt.Circle((x, y), pile_diameter/2, 
                                 fill=True, color='green', alpha=0.7)
                ax.add_artist(pile)
                
                # Add pile number
                ax.text(x, y, f'P{i+1}', ha='center', va='center', 
                       color='white', fontweight='bold', fontsize=8)
            
            # Formatting
            ax.set_xlabel('X Coordinate (m)')
            ax.set_ylabel('Y Coordinate (m)')
            ax.set_title('Foundation Plan View')
            ax.grid(True, alpha=0.3)
            ax.set_aspect('equal', adjustable='box')
            ax.legend()
            
            # Set limits
            limit = foundation_diameter * 0.6
            ax.set_xlim(-limit, limit)
            ax.set_ylim(-limit, limit)
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                print(f"✓ Foundation plan saved: {save_path}")
            
            plt.show()
            plt.close(fig)
            
        except Exception as e:
            print(f"✗ Error creating foundation plan: {e}")

# ================================================================================
# 11. DESIGN SUMMARY AND DATA EXPORT TO EXCEL
# ================================================================================

def generate_design_summary(chimney: ChimneyGeometry, wind_analysis: WindLoadAnalysis,
                          seismic_analysis: SeismicLoadAnalysis, pile_design: Dict,
                          reinforcement: Dict, serviceability: Dict, 
                          cost_estimation: Dict) -> pd.DataFrame:
    """
    Generate a comprehensive design summary report as a DataFrame
    """
    try:
        # Calculate additional design values
        total_load = pile_design.get('total_load', 0)
        wind_moment = wind_analysis.wind_moment_at_base(chimney)
        seismic_moment = seismic_analysis.seismic_moment_at_base(chimney, total_load)
        
        # Get serviceability values with defaults
        deflection = serviceability.get('deflection', 0)
        max_deflection = serviceability.get('max_deflection', 1e6)
        crack_width = serviceability.get('crack_width', 0)
        max_crack = serviceability.get('max_crack', 1e6)
        
        # Collect all design data
        design_summary_data = {
            'Parameter': [
                'Chimney Height', 
                'Chimney Diameter (Top)', 
                'Chimney Diameter (Bottom)',
                'Wall Thickness',
                'Total Load (kN)',
                'Wind Load (kN)',
                'Wind Moment (kNm)',
                'Seismic Load (kN)',
                'Seismic Moment (kNm)',
                'Number of Piles',
                'Pile Diameter (mm)',
                'Pile Length (m)',
                'Max Pile Load (kN)',
                'Reinforcement Area (mm²/m)',
                'Reinforcement Ratio (%)',
                'Concrete Grade',
                'Steel Grade',
                'Deflection (mm)',
                'Max Allowable Deflection (mm)',
                'Crack Width (mm)',
                'Max Crack Width (mm)',
                'Estimated Cost (EUR)',
                'Concrete Volume (m³)',
                'Reinforcement Weight (ton)',
                'Pile Volume (m³)'
            ],
            'Value': [
                f"{chimney.height:.2f}",
                f"{chimney.top_diameter:.2f}", 
                f"{chimney.bottom_diameter:.2f}",
                f"{chimney.wall_thickness:.2f}",
                f"{total_load:.0f}",
                f"{wind_analysis.wind_shear_at_base(chimney):.0f}",
                f"{wind_moment:.0f}",
                f"{seismic_analysis.base_shear(chimney, total_load):.0f}",
                f"{seismic_moment:.0f}",
                f"{pile_design.get('number_of_piles', 0)}",
                f"{pile_design.get('pile_diameter', 0) * 1000:.0f}",
                f"{pile_design.get('pile_length', 0):.1f}",
                f"{pile_design.get('max_pile_load', 0):.1f}",
                f"{reinforcement.get('total_area', 0) * 1e6:.0f}",
                f"{reinforcement.get('reinforcement_ratio', 0):.2f}",
                f"{reinforcement.get('concrete_grade', 'C35')}",
                f"{reinforcement.get('steel_grade', '500')}",
                f"{deflection * 1000:.1f}",
                f"{max_deflection * 1000:.1f}",
                f"{crack_width:.2f}",
                f"{max_crack:.2f}",
                f"{cost_estimation.get('total_cost', 0):,.0f}",
                f"{cost_estimation.get('concrete_volume', 0):.1f}",
                f"{cost_estimation.get('reinforcement_weight', 0)/1000:.1f}",
                f"{cost_estimation.get('pile_volume', 0):.1f}"
            ],
            'Unit': [
                'm', 'm', 'm', 'm', 'kN', 'kN', 'kNm', 'kN', 'kNm', 
                '-', 'mm', 'm', 'kN', 'mm²/m', '%', '-', '-', 'mm', 'mm', 'mm', 'mm', 'EUR', 'm³', 'ton', 'm³'
            ],
            'Status': [
                'OK', 'OK', 'OK', 'OK',
                'OK' if total_load > 0 else 'CHECK',
                'OK', 'OK', 'OK', 'OK',
                'OK' if pile_design.get('number_of_piles', 0) > 0 else 'CHECK',
                'OK', 'OK',
                'OK' if pile_design.get('max_pile_load', 0) < pile_design.get('single_pile_capacity', 1e6) else 'OVERLOAD',
                'OK' if reinforcement.get('total_area', 0) > reinforcement.get('minimum_area', 0) else 'UNDER',
                'OK' if 0.2 <= reinforcement.get('reinforcement_ratio', 0) <= 4.0 else 'CHECK',
                'OK', 'OK',
                'OK' if deflection <= max_deflection else 'EXCEEDED',
                'OK',
                'OK' if crack_width <= max_crack else 'EXCEEDED',
                'OK',
                'OK',
                'OK',
                'OK',
                'OK'
            ]
        }
        
        # Ensure all arrays have the same length
        lengths = {key: len(value) for key, value in design_summary_data.items()}
        if len(set(lengths.values())) > 1:
            print(f"Warning: Array lengths differ: {lengths}")
            # Find the minimum length
            min_length = min(lengths.values())
            # Truncate all arrays to the minimum length
            for key in design_summary_data.keys():
                design_summary_data[key] = design_summary_data[key][:min_length]
        
        # Create DataFrame
        df_design_summary = pd.DataFrame(design_summary_data)
        
        # Format DataFrame
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        pd.set_option('display.colheader_justify', 'center')
        
        print("\n" + "="*100)
        print("DESIGN SUMMARY REPORT")
        print("="*100)
        print(df_design_summary.to_string(index=False))
        print("="*100)
        
        return df_design_summary
        
    except Exception as e:
        print(f"Error generating design summary: {e}")
        print(traceback.format_exc())
        # Return empty DataFrame with correct structure
        return pd.DataFrame(columns=['Parameter', 'Value', 'Unit', 'Status'])

# ================================================================================
# 12. DETAILED EXCEL EXPORT
# ================================================================================

def export_all_design_to_excel(chimney: ChimneyGeometry, wind_analysis: WindLoadAnalysis,
                             seismic_analysis: SeismicLoadAnalysis, pile_design: Dict,
                             reinforcement: Dict, serviceability: Dict, 
                             cost_estimation: Dict, filename: str = None) -> str:
    """
    Export all design calculations and results to Excel with multiple sheets
    """
    try:
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"chimney_design_detailed_{timestamp}.xlsx"
        
        # Create Excel writer
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # 1. Design Summary Sheet
            df_summary = generate_design_summary(chimney, wind_analysis, seismic_analysis, 
                                               pile_design, reinforcement, serviceability, cost_estimation)
            df_summary.to_excel(writer, sheet_name='Design Summary', index=False)
            
            # 2. Chimney Geometry Sheet
            geometry_data = {
                'Height (m)': [chimney.height],
                'Top Diameter (m)': [chimney.top_diameter],
                'Bottom Diameter (m)': [chimney.bottom_diameter],
                'Wall Thickness (m)': [chimney.wall_thickness],
                'Volume (m³)': [cost_estimation.get('concrete_volume', 0)],
                'Surface Area (m²)': [cost_estimation.get('formwork_area', 0)]
            }
            df_geometry = pd.DataFrame(geometry_data)
            df_geometry.to_excel(writer, sheet_name='Chimney Geometry', index=False)
            
            # 3. Load Analysis Sheet
            total_load = pile_design.get('total_load', 0)
            load_data = {
                'Load Type': ['Dead Load', 'Wind Load', 'Seismic Load', 'Design Load'],
                'Shear (kN)': [
                    total_load,
                    wind_analysis.wind_shear_at_base(chimney),
                    seismic_analysis.base_shear(chimney, total_load),
                    max(wind_analysis.wind_shear_at_base(chimney), 
                        seismic_analysis.base_shear(chimney, total_load))
                ],
                'Moment (kNm)': [
                    0,
                    wind_analysis.wind_moment_at_base(chimney),
                    seismic_analysis.seismic_moment_at_base(chimney, total_load),
                    max(wind_analysis.wind_moment_at_base(chimney),
                        seismic_analysis.seismic_moment_at_base(chimney, total_load))
                ]
            }
            df_loads = pd.DataFrame(load_data)
            df_loads.to_excel(writer, sheet_name='Load Analysis', index=False)
            
            # 4. Pile Foundation Sheet
            pile_data = {
                'Parameter': ['Number of Piles', 'Pile Diameter (mm)', 'Pile Length (m)', 
                            'Single Pile Capacity (kN)', 'Max Pile Load (kN)', 'Safety Factor'],
                'Value': [
                    pile_design.get('number_of_piles', 0),
                    pile_design.get('pile_diameter', 0) * 1000,
                    pile_design.get('pile_length', 0),
                    pile_design.get('single_pile_capacity', 0),
                    pile_design.get('max_pile_load', 0),
                    pile_design.get('safety_factor', 0)
                ],
                'Status': [
                    'OK' if pile_design.get('number_of_piles', 0) > 0 else 'CHECK',
                    'OK',
                    'OK',
                    'OK',
                    'OK' if pile_design.get('max_pile_load', 0) < pile_design.get('single_pile_capacity', 1e6) else 'OVERLOAD',
                    'OK' if pile_design.get('safety_factor', 0) > 1.0 else 'CHECK'
                ]
            }
            df_piles = pd.DataFrame(pile_data)
            df_piles.to_excel(writer, sheet_name='Pile Foundation', index=False)
            
            # 5. Reinforcement Sheet
            reinforcement_data = {
                'Parameter': ['Total Area (mm²/m)', 'Minimum Area (mm²/m)', 
                            'Reinforcement Ratio (%)', 'Bar Diameter (mm)', 
                            'Bars per Meter', 'Concrete Grade', 'Steel Grade'],
                'Value': [
                    reinforcement.get('total_area', 0) * 1e6,
                    reinforcement.get('minimum_area', 0) * 1e6,
                    reinforcement.get('reinforcement_ratio', 0),
                    reinforcement.get('bar_diameter', 0),
                    reinforcement.get('bars_per_meter', 0),
                    reinforcement.get('concrete_grade', 'C35'),
                    reinforcement.get('steel_grade', '500')
                ],
                'Status': [
                    'OK' if reinforcement.get('total_area', 0) > reinforcement.get('minimum_area', 0) else 'UNDER',
                    'OK',
                    'OK' if 0.2 <= reinforcement.get('reinforcement_ratio', 0) <= 4.0 else 'CHECK',
                    'OK',
                    'OK',
                    'OK',
                    'OK'
                ]
            }
            df_reinforcement = pd.DataFrame(reinforcement_data)
            df_reinforcement.to_excel(writer, sheet_name='Reinforcement', index=False)
            
            # 6. Serviceability Sheet
            serviceability_data = {
                'Check': ['Deflection', 'Crack Width'],
                'Value': [
                    f"{serviceability.get('deflection', 0) * 1000:.1f} mm",
                    f"{serviceability.get('crack_width', 0):.2f} mm"
                ],
                'Limit': [
                    f"{serviceability.get('max_deflection', 0) * 1000:.1f} mm",
                    f"{serviceability.get('max_crack', 0):.2f} mm"
                ],
                'Status': [
                    'OK' if serviceability.get('deflection', 1e6) <= serviceability.get('max_deflection', 0) else 'EXCEEDED',
                    'OK' if serviceability.get('crack_width', 1e6) <= serviceability.get('max_crack', 0) else 'EXCEEDED'
                ]
            }
            df_service = pd.DataFrame(serviceability_data)
            df_service.to_excel(writer, sheet_name='Serviceability', index=False)
            
            # 7. Cost Estimation Sheet
            costs = cost_estimation.get('itemized_costs', {})
            cost_data = {
                'Item': ['Concrete', 'Reinforcement', 'Piling', 'Formwork', 'Labor', 'Equipment', 'Subtotal', 'Contingency (20%)', 'Total'],
                'Cost (EUR)': [
                    costs.get('concrete', 0),
                    costs.get('reinforcement', 0),
                    costs.get('piling', 0),
                    costs.get('formwork', 0),
                    costs.get('labor', 0),
                    costs.get('equipment', 0),
                    sum(costs.values()) if costs else 0,
                    cost_estimation.get('contingency', 0),
                    cost_estimation.get('total_cost', 0)
                ],
                'Percentage (%)': [
                    f"{(costs.get('concrete', 0) / max(cost_estimation.get('total_cost', 1), 1) * 100):.1f}",
                    f"{(costs.get('reinforcement', 0) / max(cost_estimation.get('total_cost', 1), 1) * 100):.1f}",
                    f"{(costs.get('piling', 0) / max(cost_estimation.get('total_cost', 1), 1) * 100):.1f}",
                    f"{(costs.get('formwork', 0) / max(cost_estimation.get('total_cost', 1), 1) * 100):.1f}",
                    f"{(costs.get('labor', 0) / max(cost_estimation.get('total_cost', 1), 1) * 100):.1f}",
                    f"{(costs.get('equipment', 0) / max(cost_estimation.get('total_cost', 1), 1) * 100):.1f}",
                    f"{(sum(costs.values()) if costs else 0) / max(cost_estimation.get('total_cost', 1), 1) * 100:.1f}",
                    f"{(cost_estimation.get('contingency', 0) / max(cost_estimation.get('total_cost', 1), 1) * 100):.1f}",
                    "100.0"
                ]
            }
            df_costs = pd.DataFrame(cost_data)
            df_costs.to_excel(writer, sheet_name='Cost Estimation', index=False)
            
            # 8. Material Quantities Sheet
            quantities_data = {
                'Material': ['Concrete', 'Reinforcement Steel', 'Piles'],
                'Quantity': [
                    f"{cost_estimation.get('concrete_volume', 0):.1f} m³",
                    f"{cost_estimation.get('reinforcement_weight', 0)/1000:.1f} ton",
                    f"{cost_estimation.get('pile_volume', 0):.1f} m³"
                ],
                'Unit Cost': [
                    f"€{costs.get('concrete', 0) / max(cost_estimation.get('concrete_volume', 1), 1) if cost_estimation.get('concrete_volume', 0) > 0 else 0:.0f}/m³",
                    f"€{costs.get('reinforcement', 0) / max((cost_estimation.get('reinforcement_weight', 0)/1000), 1) if cost_estimation.get('reinforcement_weight', 0) > 0 else 0:.0f}/ton",
                    f"€{costs.get('piling', 0) / max(cost_estimation.get('pile_volume', 1), 1) if cost_estimation.get('pile_volume', 0) > 0 else 0:.0f}/m³"
                ],
                'Total Cost': [
                    f"€{costs.get('concrete', 0):,.0f}",
                    f"€{costs.get('reinforcement', 0):,.0f}",
                    f"€{costs.get('piling', 0):,.0f}"
                ]
            }
            df_quantities = pd.DataFrame(quantities_data)
            df_quantities.to_excel(writer, sheet_name='Material Quantities', index=False)
            
            # 9. Design Parameters Sheet
            design_params = {
                'Parameter': [
                    'Basic Wind Speed (m/s)', 'Seismic Acceleration (g)', 
                    'Soil Type', 'Importance Class', 'Terrain Category',
                    'Concrete Density (kN/m³)', 'Steel Density (kN/m³)'
                ],
                'Value': [
                    wind_analysis.vb0, seismic_analysis.ag,
                    seismic_analysis.soil_type, seismic_analysis.importance_class,
                    wind_analysis.terrain_category, '25', '78.5'
                ]
            }
            df_params = pd.DataFrame(design_params)
            df_params.to_excel(writer, sheet_name='Design Parameters', index=False)
        
        print(f"✓ Detailed design exported to Excel: {filename}")
        print(f"  Sheets created: 9")
        
        return filename
        
    except Exception as e:
        print(f"✗ Error exporting to Excel: {e}")
        print(traceback.format_exc())
        return None

# ================================================================================
# 13. CAD DRAWING GENERATION (DXF) - FIXED VERSION
# ================================================================================

def create_cad_drawing(plan_coords: List[Tuple], pile_coords: List[Tuple], 
                      pile_diameter: float, chimney_diameter: float, 
                      foundation_diameter: float, foundation_thickness: float,
                      drawing_scale: float = 20, filename: str = "chimney_design.dxf") -> bool:
    """
    Create a professional CAD drawing (DXF format) of the chimney foundation with piles
    
    Parameters:
    - plan_coords: List of (x, y) coordinates for chimney plan
    - pile_coords: List of (x, y) coordinates for pile centers
    - pile_diameter: Diameter of each pile in meters
    - chimney_diameter: Diameter of chimney at base in meters
    - foundation_diameter: Diameter of foundation slab in meters
    - foundation_thickness: Thickness of foundation slab in meters
    - drawing_scale: Scale factor for the drawing (1 unit = 1 meter * scale)
    - filename: Output DXF filename
    
    Returns:
    - True if successful, False otherwise
    """
    try:
        # Create a new DXF document
        doc = ezdxf.new('R2010')
        doc.units = units.M
        
        # Add layers with different colors
        layer_defs = [
            ('CHIMNEY', 1),      # Red
            ('FOUNDATION', 2),   # Yellow
            ('PILES', 3),        # Green
            ('DIMENSIONS', 4),   # Cyan
            ('TEXT', 5),         # Magenta
            ('CENTERLINE', 6),   # Blue
            ('GRID', 7)          # White
        ]
        
        for layer_name, color in layer_defs:
            if layer_name not in doc.layers:
                doc.layers.new(name=layer_name, dxfattribs={'color': color})
        
        # Get the modelspace
        msp = doc.modelspace()
        
        # Set scale factor
        sc = drawing_scale
        
        # Draw chimney plan (top view)
        if plan_coords:
            # Ensure polygon is closed
            if len(plan_coords) > 2 and plan_coords[0] != plan_coords[-1]:
                plan_coords.append(plan_coords[0])
            
            scaled_coords = [(x * sc, y * sc) for x, y in plan_coords]
            # Add closed polygon
            msp.add_lwpolyline(scaled_coords, dxfattribs={'layer': 'CHIMNEY', 'closed': True})
        
        # Draw foundation outline (circular foundation)
        foundation_radius = foundation_diameter / 2
        foundation_points = []
        for angle in np.linspace(0, 2*np.pi, 100):
            x = foundation_radius * np.cos(angle) * sc
            y = foundation_radius * np.sin(angle) * sc
            foundation_points.append((x, y))
        
        # Close the circle
        if foundation_points and foundation_points[0] != foundation_points[-1]:
            foundation_points.append(foundation_points[0])
        
        msp.add_lwpolyline(foundation_points, dxfattribs={'layer': 'FOUNDATION', 'closed': True})
        
        # Draw piles
        for i, (pile_x, pile_y) in enumerate(pile_coords, 1):
            # Scale coordinates
            px = pile_x * sc
            py = pile_y * sc
            pd = pile_diameter * sc
            
            # Draw pile circle
            msp.add_circle((px, py), pd/2, dxfattribs={'layer': 'PILES'})
            
            # Add pile number - using set_pos() correctly
            text_content = f"P{i}"
            text = msp.add_text(
                text_content,
                dxfattribs={
                    'layer': 'TEXT',
                    'height': 0.3 * sc,
                    'color': 5  # Magenta
                }
            )
            # Correct method to set text position
            text.dxf.insert = (px, py)
            text.dxf.halign = 1  # Center alignment
            text.dxf.valign = 2  # Middle alignment
            
            # Add pile diameter annotation
            dia_text = msp.add_text(
                f"Ø{pile_diameter*1000:.0f}mm",
                dxfattribs={
                    'layer': 'TEXT',
                    'height': 0.2 * sc,
                    'color': 5
                }
            )
            dia_text.dxf.insert = (px, py - 0.4 * sc)
            dia_text.dxf.halign = 1  # Center alignment
            dia_text.dxf.valign = 3  # Top alignment
            
            # Add center mark
            msp.add_line((px - 0.2*sc, py), (px + 0.2*sc, py), 
                        dxfattribs={'layer': 'CENTERLINE'})
            msp.add_line((px, py - 0.2*sc), (px, py + 0.2*sc), 
                        dxfattribs={'layer': 'CENTERLINE'})
        
        # Draw centerlines
        msp.add_line((-foundation_radius*sc, 0), (foundation_radius*sc, 0), 
                    dxfattribs={'layer': 'CENTERLINE'})
        msp.add_line((0, -foundation_radius*sc), (0, foundation_radius*sc), 
                    dxfattribs={'layer': 'CENTERLINE'})
        
        # Add dimensions
        # Foundation diameter dimension lines
        dim_y = foundation_radius * sc + 1 * sc
        msp.add_line((-foundation_radius*sc, dim_y), 
                    (foundation_radius*sc, dim_y), 
                    dxfattribs={'layer': 'DIMENSIONS'})
        
        # Add vertical dimension lines
        msp.add_line((-foundation_radius*sc, dim_y - 0.2*sc), 
                    (-foundation_radius*sc, dim_y + 0.2*sc), 
                    dxfattribs={'layer': 'DIMENSIONS'})
        msp.add_line((foundation_radius*sc, dim_y - 0.2*sc), 
                    (foundation_radius*sc, dim_y + 0.2*sc), 
                    dxfattribs={'layer': 'DIMENSIONS'})
        
        # Add dimension text for foundation
        dim_text = f"Foundation Ø{foundation_diameter:.2f}m"
        text = msp.add_text(
            dim_text,
            dxfattribs={
                'layer': 'TEXT',
                'height': 0.3 * sc,
                'color': 4
            }
        )
        text.dxf.insert = (0, dim_y + 0.5*sc)
        text.dxf.halign = 1  # Center alignment
        
        # Add chimney diameter dimension
        chim_dim_y = -foundation_radius*sc - 1*sc
        msp.add_line((-chimney_diameter*sc/2, chim_dim_y), 
                    (chimney_diameter*sc/2, chim_dim_y), 
                    dxfattribs={'layer': 'DIMENSIONS'})
        
        # Add vertical dimension lines for chimney
        msp.add_line((-chimney_diameter*sc/2, chim_dim_y - 0.2*sc), 
                    (-chimney_diameter*sc/2, chim_dim_y + 0.2*sc), 
                    dxfattribs={'layer': 'DIMENSIONS'})
        msp.add_line((chimney_diameter*sc/2, chim_dim_y - 0.2*sc), 
                    (chimney_diameter*sc/2, chim_dim_y + 0.2*sc), 
                    dxfattribs={'layer': 'DIMENSIONS'})
        
        # Add dimension text for chimney
        chim_text = f"Chimney Ø{chimney_diameter:.2f}m"
        text = msp.add_text(
            chim_text,
            dxfattribs={
                'layer': 'TEXT',
                'height': 0.3 * sc,
                'color': 4
            }
        )
        text.dxf.insert = (0, chim_dim_y - 0.5*sc)
        text.dxf.halign = 1  # Center alignment
        
        # Add foundation thickness note
        thick_text = f"Foundation thickness: {foundation_thickness:.2f}m"
        text = msp.add_text(
            thick_text,
            dxfattribs={
                'layer': 'TEXT',
                'height': 0.25 * sc,
                'color': 4
            }
        )
        text.dxf.insert = (-foundation_radius*sc, -foundation_radius*sc - 2*sc)
        
        # Add title block
        title_y = -foundation_radius*sc - 3*sc
        title = msp.add_text(
            "CHIMNEY FOUNDATION PLAN",
            dxfattribs={
                'layer': 'TEXT',
                'height': 0.6 * sc,
                'color': 7
            }
        )
        title.dxf.insert = (0, title_y)
        title.dxf.halign = 1  # Center alignment
        
        # Add scale information
        scale_text = f"Scale: 1:{int(1/sc)}" if sc != 1 else "Scale: 1:1"
        scale_txt = msp.add_text(
            scale_text,
            dxfattribs={
                'layer': 'TEXT',
                'height': 0.3 * sc,
                'color': 7
            }
        )
        scale_txt.dxf.insert = (-foundation_radius*sc, title_y - 1*sc)
        
        # Add pile information
        pile_dia_txt = msp.add_text(
            f"Pile Diameter: {pile_diameter*1000:.0f} mm",
            dxfattribs={
                'layer': 'TEXT',
                'height': 0.3 * sc,
                'color': 7
            }
        )
        pile_dia_txt.dxf.insert = (-foundation_radius*sc, title_y - 1.5*sc)
        
        pile_count_txt = msp.add_text(
            f"Number of Piles: {len(pile_coords)}",
            dxfattribs={
                'layer': 'TEXT',
                'height': 0.3 * sc,
                'color': 7
            }
        )
        pile_count_txt.dxf.insert = (-foundation_radius*sc, title_y - 2*sc)
        
        # Add date
        date_txt = msp.add_text(
            f"Drawing Date: {datetime.now().strftime('%Y-%m-%d')}",
            dxfattribs={
                'layer': 'TEXT',
                'height': 0.25 * sc,
                'color': 7
            }
        )
        date_txt.dxf.insert = (foundation_radius*sc - 3*sc, title_y - 1*sc)
        date_txt.dxf.halign = 2  # Right alignment
        
        # Add legend
        legend_x = foundation_radius*sc + 2*sc
        legend_y = foundation_radius*sc
        
        legend_items = [
            ("CHIMNEY", 1),
            ("FOUNDATION", 2),
            ("PILES", 3),
            ("DIMENSIONS", 4),
            ("CENTERLINE", 6)
        ]
        
        for i, (item, color) in enumerate(legend_items):
            legend_text = msp.add_text(
                item,
                dxfattribs={
                    'layer': 'TEXT',
                    'height': 0.25 * sc,
                    'color': color
                }
            )
            legend_text.dxf.insert = (legend_x, legend_y - i*0.4*sc)
        
        # Add border
        border_margin = 1 * sc
        border_points = [
            (-foundation_radius*sc - border_margin, foundation_radius*sc + border_margin),
            (foundation_radius*sc + border_margin, foundation_radius*sc + border_margin),
            (foundation_radius*sc + border_margin, -foundation_radius*sc - border_margin - 4*sc),
            (-foundation_radius*sc - border_margin, -foundation_radius*sc - border_margin - 4*sc),
            (-foundation_radius*sc - border_margin, foundation_radius*sc + border_margin)
        ]
        msp.add_lwpolyline(border_points, dxfattribs={'layer': 'GRID', 'closed': True})
        
        # Save the DXF file
        doc.saveas(filename)
        print(f"✓ CAD drawing saved as: {filename}")
        print(f"  Drawing scale: 1:{int(sc)}")
        print(f"  Total piles drawn: {len(pile_coords)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error creating DXF file: {e}")
        print(traceback.format_exc())
        return False

# ================================================================================
# 14. USER INPUT FUNCTIONS
# ================================================================================

def get_user_input():
    """Get design parameters from user"""
    
    print("\n" + "="*80)
    print("CHIMNEY DESIGN PARAMETERS INPUT")
    print("="*80)
    
    # Default values
    default_params = {
        "chimney_height": 50.0,
        "top_diameter": 3.0,
        "bottom_diameter": 5.0,
        "wall_thickness": 0.3,
        "basic_wind_speed": 28.0,
        "seismic_acceleration": 0.15,
        "soil_type": "C",
        "pile_diameter": 0.6,
        "pile_length": 15.0,
        "concrete_grade": "C35",
        "steel_grade": "500",
        "importance_class": "CC2"
    }
    
    print("\nEnter design parameters (press Enter to use default values):")
    
    params = {}
    
    # Chimney geometry
    try:
        params["chimney_height"] = float(input(f"Chimney height (m) [{default_params['chimney_height']}]: ") or default_params["chimney_height"])
        params["top_diameter"] = float(input(f"Top diameter (m) [{default_params['top_diameter']}]: ") or default_params["top_diameter"])
        params["bottom_diameter"] = float(input(f"Bottom diameter (m) [{default_params['bottom_diameter']}]: ") or default_params["bottom_diameter"])
        params["wall_thickness"] = float(input(f"Wall thickness (m) [{default_params['wall_thickness']}]: ") or default_params["wall_thickness"])
        
        # Validate inputs
        if params["chimney_height"] <= 0:
            raise ValueError("Chimney height must be positive")
        if params["top_diameter"] <= 0 or params["bottom_diameter"] <= 0:
            raise ValueError("Diameters must be positive")
        if params["wall_thickness"] <= 0:
            raise ValueError("Wall thickness must be positive")
        if params["bottom_diameter"] < params["top_diameter"]:
            print("Warning: Bottom diameter is smaller than top diameter. Adjusting...")
            params["bottom_diameter"] = params["top_diameter"] * 1.2
            
    except ValueError as e:
        print(f"Input error: {e}. Using default values.")
        params["chimney_height"] = default_params["chimney_height"]
        params["top_diameter"] = default_params["top_diameter"]
        params["bottom_diameter"] = default_params["bottom_diameter"]
        params["wall_thickness"] = default_params["wall_thickness"]
    
    # Load parameters
    try:
        params["basic_wind_speed"] = float(input(f"Basic wind speed (m/s) [{default_params['basic_wind_speed']}]: ") or default_params["basic_wind_speed"])
        params["seismic_acceleration"] = float(input(f"Seismic acceleration (g) [{default_params['seismic_acceleration']}]: ") or default_params["seismic_acceleration"])
        
        if params["basic_wind_speed"] < 0:
            raise ValueError("Wind speed must be positive")
        if params["seismic_acceleration"] < 0:
            raise ValueError("Seismic acceleration must be positive")
            
    except ValueError as e:
        print(f"Input error: {e}. Using default values.")
        params["basic_wind_speed"] = default_params["basic_wind_speed"]
        params["seismic_acceleration"] = default_params["seismic_acceleration"]
    
    # Soil and foundation
    print("\nSoil types: A, B, C, D, E (C = dense sand or stiff clay)")
    params["soil_type"] = input(f"Soil type [{default_params['soil_type']}]: ") or default_params["soil_type"]
    params["soil_type"] = params["soil_type"].upper()
    
    try:
        params["pile_diameter"] = float(input(f"Pile diameter (m) [{default_params['pile_diameter']}]: ") or default_params["pile_diameter"])
        params["pile_length"] = float(input(f"Pile length (m) [{default_params['pile_length']}]: ") or default_params["pile_length"])
        
        if params["pile_diameter"] <= 0:
            raise ValueError("Pile diameter must be positive")
        if params["pile_length"] <= 0:
            raise ValueError("Pile length must be positive")
            
    except ValueError as e:
        print(f"Input error: {e}. Using default values.")
        params["pile_diameter"] = default_params["pile_diameter"]
        params["pile_length"] = default_params["pile_length"]
    
    # Material properties
    print("\nConcrete grades: C25, C30, C35, C40, C45, C50")
    params["concrete_grade"] = input(f"Concrete grade [{default_params['concrete_grade']}]: ") or default_params["concrete_grade"]
    params["concrete_grade"] = params["concrete_grade"].upper()
    
    print("\nSteel grades: 420, 500, 550")
    params["steel_grade"] = input(f"Steel grade [{default_params['steel_grade']}]: ") or default_params["steel_grade"]
    
    # Importance class
    print("\nImportance classes: CC1 (low), CC2 (medium), CC3 (high)")
    params["importance_class"] = input(f"Importance class [{default_params['importance_class']}]: ") or default_params["importance_class"]
    params["importance_class"] = params["importance_class"].upper()
    
    return params

def display_input_summary(params: Dict):
    """Display a summary of input parameters"""
    
    print("\n" + "="*80)
    print("INPUT PARAMETERS SUMMARY")
    print("="*80)
    
    summary = f"""
CHIMNEY GEOMETRY:
  Height: {params['chimney_height']} m
  Top diameter: {params['top_diameter']} m
  Bottom diameter: {params['bottom_diameter']} m
  Wall thickness: {params['wall_thickness']} m

LOAD PARAMETERS:
  Basic wind speed: {params['basic_wind_speed']} m/s
  Seismic acceleration: {params['seismic_acceleration']} g
  Soil type: {params['soil_type']}

FOUNDATION PARAMETERS:
  Pile diameter: {params['pile_diameter']} m
  Pile length: {params['pile_length']} m

MATERIAL PROPERTIES:
  Concrete grade: {params['concrete_grade']}
  Steel grade: {params['steel_grade']}
  Importance class: {params['importance_class']}
"""
    
    print(summary)
    
    confirm = input("\nProceed with design? (y/n): ").lower()
    return confirm == 'y'

# ================================================================================
# 15. MAIN DESIGN FUNCTION
# ================================================================================

def design_chimney_foundation(
    chimney_height: float = 50.0,
    top_diameter: float = 3.0,
    bottom_diameter: float = 5.0,
    wall_thickness: float = 0.3,
    basic_wind_speed: float = 28.0,
    seismic_acceleration: float = 0.15,
    soil_type: str = "C",
    pile_diameter: float = 0.6,
    pile_length: float = 15.0,
    concrete_grade: str = "C35",
    steel_grade: str = "500",
    importance_class: str = "CC2"
) -> Dict[str, Any]:
    """
    Main function to design chimney foundation
    
    Returns:
    - Dictionary containing all design results
    """
    
    print("\n" + "="*80)
    print("CHIMNEY FOUNDATION DESIGN - WSCHIMNEY Rev.11")
    print("="*80)
    
    # Initialize components
    materials = MaterialProperties()
    
    # 1. Chimney Geometry
    chimney = ChimneyGeometry(
        height=chimney_height,
        top_diameter=top_diameter,
        bottom_diameter=bottom_diameter,
        wall_thickness=wall_thickness
    )
    
    print(f"\n1. CHIMNEY GEOMETRY")
    print(f"   Height: {chimney_height} m")
    print(f"   Top diameter: {top_diameter} m")
    print(f"   Bottom diameter: {bottom_diameter} m")
    print(f"   Wall thickness: {wall_thickness} m")
    
    # 2. Calculate total weight
    total_weight = 0
    num_segments = 20
    segment_height = chimney_height / num_segments
    
    for i in range(num_segments):
        z_center = (i + 0.5) * segment_height
        weight_per_m = chimney.weight_per_unit_height(z_center)
        total_weight += weight_per_m * segment_height
    
    print(f"\n2. LOAD CALCULATION")
    print(f"   Total weight: {total_weight:.0f} kN")
    
    # 3. Wind Load Analysis
    wind_analysis = WindLoadAnalysis(
        basic_wind_speed=basic_wind_speed,
        chimney_height=chimney_height
    )
    
    wind_moment = wind_analysis.wind_moment_at_base(chimney)
    wind_shear = wind_analysis.wind_shear_at_base(chimney)
    
    print(f"   Wind moment at base: {wind_moment:.0f} kNm")
    print(f"   Wind shear at base: {wind_shear:.0f} kN")
    
    # 4. Seismic Load Analysis
    seismic_analysis = SeismicLoadAnalysis(
        ag=seismic_acceleration,
        soil_type=soil_type
    )
    
    seismic_shear = seismic_analysis.base_shear(chimney, total_weight)
    seismic_moment = seismic_analysis.seismic_moment_at_base(chimney, total_weight)
    
    print(f"   Seismic shear: {seismic_shear:.0f} kN")
    print(f"   Seismic moment: {seismic_moment:.0f} kNm")
    
    # 5. Design loads (most critical combination)
    design_moment = max(wind_moment, seismic_moment)
    design_shear = max(wind_shear, seismic_shear)
    
    print(f"   Design moment: {design_moment:.0f} kNm")
    print(f"   Design shear: {design_shear:.0f} kN")
    
    # 6. Pile Foundation Design
    soil_layers = [
        {"type": "sand", "thickness": 5.0, "phi": 30, "sigma_v": 50},
        {"type": "clay", "thickness": 10.0, "cu": 75},
        {"type": "sand", "thickness": 10.0, "phi": 35, "sigma_v": 150}
    ]
    
    pile_designer = PileFoundation(soil_properties={"type": soil_type})
    
    foundation_diameter = bottom_diameter * 1.5
    try:
        pile_design = pile_designer.required_piles(
            total_load=total_weight,
            moment=design_moment,
            pile_diameter=pile_diameter,
            pile_length=pile_length,
            soil_layers=soil_layers,
            arrangement="circular",
            foundation_diameter=foundation_diameter
        )
    except Exception as e:
        print(f"Error in pile design: {e}")
        # Use minimum design
        pile_design = {
            "number_of_piles": 6,
            "pile_diameter": pile_diameter,
            "pile_length": pile_length,
            "single_pile_capacity": 1000,
            "max_pile_load": total_weight / 6,
            "safety_factor": 2.0,
            "total_load": total_weight
        }
    
    print(f"\n3. PILE FOUNDATION DESIGN")
    print(f"   Number of piles: {pile_design['number_of_piles']}")
    print(f"   Pile diameter: {pile_diameter * 1000:.0f} mm")
    print(f"   Pile length: {pile_length} m")
    print(f"   Single pile capacity: {pile_design.get('single_pile_capacity', 0):.0f} kN")
    print(f"   Max pile load: {pile_design.get('max_pile_load', 0):.0f} kN")
    print(f"   Safety factor: {pile_design.get('safety_factor', 0):.2f}")
    
    # 7. Reinforcement Design
    reinforcement_designer = ReinforcementDesign(materials)
    
    reinforcement = reinforcement_designer.chimney_wall_reinforcement(
        axial_load=total_weight,
        moment=design_moment,
        diameter=bottom_diameter,
        thickness=wall_thickness,
        concrete_grade=concrete_grade,
        steel_grade=steel_grade
    )
    
    print(f"\n4. REINFORCEMENT DESIGN")
    print(f"   Required area: {reinforcement['total_area'] * 1e6:.0f} mm²/m")
    print(f"   Minimum area: {reinforcement['minimum_area'] * 1e6:.0f} mm²/m")
    print(f"   Reinforcement ratio: {reinforcement['reinforcement_ratio']:.2f}%")
    print(f"   Bar diameter: {reinforcement['bar_diameter']} mm")
    print(f"   Bars per meter: {reinforcement['bars_per_meter']:.1f}")
    
    # 8. Serviceability Checks
    service_checker = ServiceabilityChecks(materials)
    
    deflection_ok, deflection, max_deflection = service_checker.deflection_check(
        chimney, wind_analysis, wind_moment
    )
    
    crack_ok, crack_width, max_crack = service_checker.crack_width_check(
        total_weight, design_moment, reinforcement,
        bottom_diameter, wall_thickness
    )
    
    print(f"\n5. SERVICEABILITY CHECKS")
    print(f"   Deflection: {deflection * 1000:.1f} mm (max: {max_deflection * 1000:.1f} mm) - {'OK' if deflection_ok else 'NOT OK'}")
    print(f"   Crack width: {crack_width:.2f} mm (max: {max_crack:.2f} mm) - {'OK' if crack_ok else 'NOT OK'}")
    
    # 9. Cost Estimation
    cost_estimator = CostEstimation()
    costs = cost_estimator.estimate_total_cost(
        chimney=chimney,
        piles=pile_design,
        reinforcement=reinforcement,
        construction_time=120  # days
    )
    
    print(f"\n6. COST ESTIMATION")
    print(f"   Concrete volume: {costs['concrete_volume']:.1f} m³")
    print(f"   Reinforcement: {costs['reinforcement_weight']/1000:.1f} tons")
    print(f"   Pile volume: {costs['pile_volume']:.1f} m³")
    print(f"   Total cost: €{costs['total_cost']:,.0f}")
    print(f"   (including 20% contingency)")
    
    # 10. Generate pile coordinates for CAD drawing
    pile_coords = []
    n_piles = pile_design['number_of_piles']
    pile_radius = foundation_diameter * 0.8 / 2  # Piles inside foundation
    
    for i in range(n_piles):
        angle = 2 * math.pi * i / n_piles
        x = pile_radius * math.cos(angle)
        y = pile_radius * math.sin(angle)
        pile_coords.append((x, y))
    
    # 11. Generate chimney plan coordinates
    chimney_points = []
    for angle in np.linspace(0, 2*math.pi, 36):
        x = (bottom_diameter / 2) * math.cos(angle)
        y = (bottom_diameter / 2) * math.sin(angle)
        chimney_points.append((x, y))
    
    # 12. Create CAD drawing
    cad_filename = f"chimney_foundation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.dxf"
    cad_success = create_cad_drawing(
        plan_coords=chimney_points,
        pile_coords=pile_coords,
        pile_diameter=pile_diameter,
        chimney_diameter=bottom_diameter,
        foundation_diameter=foundation_diameter,
        foundation_thickness=1.5,  # Assume 1.5m thick foundation
        drawing_scale=50,
        filename=cad_filename
    )
    
    # 13. Generate design summary
    df_summary = generate_design_summary(
        chimney=chimney,
        wind_analysis=wind_analysis,
        seismic_analysis=seismic_analysis,
        pile_design=pile_design,
        reinforcement=reinforcement,
        serviceability={
            "deflection": deflection, 
            "max_deflection": max_deflection,
            "crack_width": crack_width,
            "max_crack": max_crack
        },
        cost_estimation=costs
    )
    
    # 14. Export ALL design data to detailed Excel file
    excel_filename = export_all_design_to_excel(
        chimney=chimney,
        wind_analysis=wind_analysis,
        seismic_analysis=seismic_analysis,
        pile_design=pile_design,
        reinforcement=reinforcement,
        serviceability={
            "deflection": deflection, 
            "max_deflection": max_deflection,
            "crack_width": crack_width,
            "max_crack": max_crack
        },
        cost_estimation=costs
    )
    
    # 15. Generate report
    report_gen = ReportGenerator("Chimney Foundation Design Project")
    
    report_gen.add_section("Project Information", 
        f"Project: Chimney Foundation Design\n"
        f"Date: {datetime.now().strftime('%Y-%m-%d')}\n"
        f"Software: WSCHIMNEY Rev.11\n"
        f"Engineer: Design Software")
    
    report_gen.add_section("Design Parameters",
        f"Chimney Height: {chimney_height} m\n"
        f"Top Diameter: {top_diameter} m\n"
        f"Bottom Diameter: {bottom_diameter} m\n"
        f"Wall Thickness: {wall_thickness} m\n"
        f"Wind Speed: {basic_wind_speed} m/s\n"
        f"Seismic Acceleration: {seismic_acceleration}g\n"
        f"Concrete Grade: {concrete_grade}\n"
        f"Steel Grade: {steel_grade}")
    
    report_gen.add_section("Design Results",
        f"Total Weight: {total_weight:.0f} kN\n"
        f"Wind Moment: {wind_moment:.0f} kNm\n"
        f"Seismic Moment: {seismic_moment:.0f} kNm\n"
        f"Required Piles: {pile_design['number_of_piles']}\n"
        f"Pile Diameter: {pile_diameter * 1000:.0f} mm\n"
        f"Reinforcement Ratio: {reinforcement['reinforcement_ratio']:.2f}%\n"
        f"Estimated Cost: €{costs['total_cost']:,.0f}")
    
    report_filename = f"chimney_design_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    report_gen.generate_report(report_filename)
    
    # 16. Create visualizations
    viz = Visualization()
    
    # Create output directory for plots
    os.makedirs("output_plots", exist_ok=True)
    
    elevation_plot = f"output_plots/chimney_elevation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    viz.plot_chimney_elevation(chimney, elevation_plot)
    
    plan_plot = f"output_plots/foundation_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    viz.plot_foundation_plan(pile_coords, pile_diameter, bottom_diameter, 
                           foundation_diameter, plan_plot)
    
    print(f"\n" + "="*80)
    print("DESIGN COMPLETED SUCCESSFULLY!")
    print("="*80)
    print(f"Output files generated:")
    print(f"  1. CAD Drawing: {cad_filename}")
    print(f"  2. Detailed Excel Report: {excel_filename}")
    print(f"  3. Design Report: {report_filename}")
    print(f"  4. Elevation Plot: {elevation_plot}")
    print(f"  5. Foundation Plan: {plan_plot}")
    print("="*80)
    
    # Return all results
    return {
        "chimney": chimney,
        "total_weight": total_weight,
        "wind_moment": wind_moment,
        "seismic_moment": seismic_moment,
        "pile_design": pile_design,
        "reinforcement": reinforcement,
        "serviceability": {
            "deflection_ok": deflection_ok,
            "deflection": deflection,
            "max_deflection": max_deflection,
            "crack_ok": crack_ok,
            "crack_width": crack_width,
            "max_crack": max_crack
        },
        "costs": costs,
        "cad_file": cad_filename if cad_success else None,
        "excel_file": excel_filename,
        "report_file": report_filename,
        "plots": [elevation_plot, plan_plot]
    }

# ================================================================================
# 16. MAIN EXECUTION
# ================================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("WSCHIMNEY - CONCRETE CHIMNEY DESIGN SOFTWARE")
    print("Version: Rev.11 (Fixed)")
    print("="*80)
    
    try:
        # Ask user for input method
        print("\nChoose input method:")
        print("1. Use default parameters")
        print("2. Enter custom parameters")
        
        choice = input("\nEnter choice (1 or 2): ").strip()
        
        if choice == "2":
            # Get user input
            params = get_user_input()
            
            # Display summary and confirm
            if not display_input_summary(params):
                print("\nDesign cancelled by user.")
                sys.exit(0)
        else:
            # Use default parameters
            params = {
                "chimney_height": 50.0,
                "top_diameter": 3.0,
                "bottom_diameter": 5.0,
                "wall_thickness": 0.3,
                "basic_wind_speed": 28.0,
                "seismic_acceleration": 0.15,
                "soil_type": "C",
                "pile_diameter": 0.6,
                "pile_length": 15.0,
                "concrete_grade": "C35",
                "steel_grade": "500",
                "importance_class": "CC2"
            }
            print("\nUsing default parameters...")
        
        # Run the design
        results = design_chimney_foundation(**params)
        
        print("\nDesign completed successfully!")
        print(f"Summary of key results:")
        print(f"  • Total chimney weight: {results['total_weight']:.0f} kN")
        print(f"  • Required piles: {results['pile_design']['number_of_piles']} x {params['pile_diameter']*1000:.0f}mm")
        print(f"  • Reinforcement ratio: {results['reinforcement']['reinforcement_ratio']:.2f}%")
        print(f"  • Estimated cost: €{results['costs']['total_cost']:,.0f}")
        
        # Ask if user wants to run another design
        another = input("\nWould you like to run another design? (y/n): ").lower()
        if another == 'y':
            # Clear screen (platform independent)
            os.system('cls' if os.name == 'nt' else 'clear')
            
            # Restart the program
            print("\n" + "="*80)
            print("STARTING NEW DESIGN")
            print("="*80)
            
            # Recursively call main (simplified approach)
            params = get_user_input()
            if display_input_summary(params):
                results = design_chimney_foundation(**params)
            else:
                print("\nDesign cancelled by user.")
        
    except KeyboardInterrupt:
        print("\n\nDesign process interrupted by user.")
    except Exception as e:
        print(f"\n\nError in design process: {e}")
        print(traceback.format_exc())
        print("\nPlease check your input parameters and try again.")
    
    print("\n" + "="*80)
    print("Thank you for using WSCHIMNEY!")
    print("="*80)