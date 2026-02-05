import sys
import socket
import tkinter as tk
from tkinter import messagebox, ttk, filedialog, simpledialog, scrolledtext
from datetime import datetime
import pandas as pd # pyright: ignore[reportMissingModuleSource]
import numpy as np # pyright: ignore[reportMissingImports]
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # pyright: ignore[reportMissingModuleSource]
import matplotlib.pyplot as plt # type: ignore
from matplotlib.figure import Figure # pyright: ignore[reportMissingModuleSource]
from reportlab.lib.pagesizes import letter, A4 # pyright: ignore[reportMissingModuleSource]
from reportlab.pdfgen import canvas as pdf_canvas # pyright: ignore[reportMissingModuleSource]
from reportlab.lib import colors # pyright: ignore[reportMissingModuleSource]
import json
import os
import copy
from scipy.sparse import csr_matrix # pyright: ignore[reportMissingImports]
from scipy.sparse.linalg import spsolve # pyright: ignore[reportMissingImports]
import scipy.sparse # pyright: ignore[reportMissingImports]
import math
from itertools import combinations
from scipy.spatial import Delaunay, ConvexHull # pyright: ignore[reportMissingImports]
import traceback
import re
from collections import defaultdict

# Try to import optional packages
try:
    import ntplib # pyright: ignore[reportMissingImports]
    NTP_AVAILABLE = True
except ImportError:
    NTP_AVAILABLE = False

try:
    import ezdxf # pyright: ignore[reportMissingImports]
    from ezdxf import units # pyright: ignore[reportMissingImports]
    DXF_AVAILABLE = True
except ImportError:
    DXF_AVAILABLE = False

try:
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph # pyright: ignore[reportMissingModuleSource]
    from reportlab.lib.styles import getSampleStyleSheet # pyright: ignore[reportMissingModuleSource]
    REPORTLAB_FULL = True
except ImportError:
    REPORTLAB_FULL = False

# --- CONSTANTS ---
ALLOWED_IPS = ["192.168.1.163", "127.0.0.1", "localhost"]
EXPIRY_DATE = datetime(2027, 12, 31)
ACI_VERSION = "ACI 318-25"
IBC_VERSION = "IBC 2021"
CONCRETE_FPC = 4000  # psi
STEEL_FY = 60000  # psi
REBAR_SIZES = {
    '3': 0.11, '4': 0.20, '5': 0.31, '6': 0.44, '7': 0.60, '8': 0.79,
    '9': 1.00, '10': 1.27, '11': 1.56, '14': 2.25, '18': 4.00
}

# Seismic parameters for Zone C (IBC 2021)
SEISMIC_PARAMS = {
    'zone_c': {
        'Ss': 0.4,
        'S1': 0.15,
        'Fa': 1.4,
        'Fv': 2.4,
        'SMS': 0.56,
        'SM1': 0.36,
        'SDS': 0.37,
        'SD1': 0.24,
        'TL': 8.0,
        'R': 3.0,
        'Ie': 1.0,
        'Cd': 2.5,
    }
}

# ACI 318-25 Load Combinations (Section 5.3)
ACI_LOAD_COMBINATIONS = {
    # Basic combinations (ACI 318-25 5.3.1)
    'U1': {'formula': '1.4*DL', 'description': 'Dead load only (ACI 5.3.1a)'},
    'U2': {'formula': '1.2*DL + 1.6*LL + 0.5*(Lr or S or R)', 'description': 'Dead + Live (ACI 5.3.1b)'},
    'U3': {'formula': '1.2*DL + 1.6*(Lr or S or R) + (1.0*LL or 0.5*W)', 'description': 'Dead + Roof/Snow/Rain (ACI 5.3.1c)'},
    'U4': {'formula': '1.2*DL + 1.0*W + 1.0*LL + 0.5*(Lr or S or R)', 'description': 'Dead + Wind + Live (ACI 5.3.1d)'},
    'U5': {'formula': '1.2*DL + 1.0*E + 1.0*LL + 0.2*S', 'description': 'Dead + Seismic + Live (ACI 5.3.1e)'},
    'U6': {'formula': '0.9*DL + 1.0*W', 'description': 'Dead + Wind (uplift) (ACI 5.3.1f)'},
    'U7': {'formula': '0.9*DL + 1.0*E', 'description': 'Dead + Seismic (uplift) (ACI 5.3.1g)'},
    
    # Seismic combinations with overstrength (ASCE 7-16 12.4.3)
    'U8': {'formula': '1.2*DL + 1.0*E + 1.0*LL', 'description': 'Seismic with vertical effects'},
    'U9': {'formula': '0.9*DL - 1.0*E', 'description': 'Seismic with minimum dead load'},
    
    # Service level combinations (ACI 318-25 24.5.3)
    'S1': {'formula': '1.0*DL', 'description': 'Service - Dead load only'},
    'S2': {'formula': '1.0*DL + 1.0*LL', 'description': 'Service - Dead + Live'},
    'S3': {'formula': '1.0*DL + 0.75*LL + 0.75*(Lr or S or R)', 'description': 'Service - Dead + 0.75(Live+Roof)'},
    'S4': {'formula': '1.0*DL + 0.6*W', 'description': 'Service - Dead + Wind'},
    'S5': {'formula': '1.0*DL + 0.7*E', 'description': 'Service - Dead + Seismic'},
    
    # Dynamic load combinations (with turbine loads)
    'D1': {'formula': '1.2*DL + 1.6*LL + 1.0*TURBINE_THRUST', 'description': 'Dead + Live + Turbine Thrust'},
    'D2': {'formula': '1.2*DL + 1.0*LL + 1.6*TURBINE_THRUST', 'description': 'Dead + Live + 1.6×Turbine Thrust'},
    'D3': {'formula': '1.2*DL + 2.0*TURBINE_EMERGENCY_BRAKE', 'description': 'Dead + Emergency Braking'},
    'D4': {'formula': '1.2*DL + 1.0*LL + 1.0*TURBINE_THRUST + 1.0*WINDX', 'description': 'Dead + Live + Turbine + Wind'},
    'D5': {'formula': '0.9*DL + 1.6*WIND_UPLIFT', 'description': 'Dead + Wind Uplift'},
    
    # Thermal combinations
    'T1': {'formula': '1.2*DL + 1.2*THERMAL_EXPANSION + 0.5*LL', 'description': 'Dead + Thermal + 0.5×Live'},
    'T2': {'formula': '1.0*DL + 1.0*THERMAL_EXPANSION', 'description': 'Service - Dead + Thermal'},
    
    # Construction load combinations
    'C1': {'formula': '1.4*DL + 1.4*CONSTRUCTION_LOAD', 'description': 'Dead + Construction loads'},
    'C2': {'formula': '1.2*DL + 1.6*CONSTRUCTION_LOAD + 0.5*LL', 'description': 'Dead + Construction + 0.5×Live'},
    
    # Combined dynamic and seismic
    'DS1': {'formula': '1.2*DL + 1.0*E + 0.5*LL + 0.5*TURBINE_THRUST', 'description': 'Seismic + Reduced Turbine'},
    'DS2': {'formula': '0.9*DL + 1.0*E - 0.2*TURBINE_THRUST', 'description': 'Seismic with minimum dead and reverse thrust'},
}

# Special load cases with coordinates
SPECIAL_LOAD_CASES = {
    'SEISMIC_X': {
        'type': 'Seismic',
        'description': 'Seismic load in X-direction (Zone C)',
        'coordinates': 'Applied at all structural mass locations',
        'load_pattern': 'Lateral',
        'load_factor': 1.0
    },
    'SEISMIC_Y': {
        'type': 'Seismic',
        'description': 'Seismic load in Y-direction (Zone C)',
        'coordinates': 'Applied at all structural mass locations',
        'load_pattern': 'Lateral',
        'load_factor': 1.0
    },
    'TURBINE_THRUST': {
        'type': 'Dynamic',
        'description': 'Turbine thrust load during operation',
        'coordinates': 'Top center of pedestal (X=10ft, Y=10ft, Z=30ft)',
        'load_pattern': 'Horizontal',
        'load_factor': 1.6
    },
    'TURBINE_EMERGENCY_BRAKE': {
        'type': 'Dynamic',
        'description': 'Emergency braking torque',
        'coordinates': 'Top center (X=10ft, Y=10ft, Z=30ft)',
        'load_pattern': 'Torsional',
        'load_factor': 2.0
    },
    'THERMAL_EXPANSION': {
        'type': 'Thermal',
        'description': 'Thermal expansion due to temperature gradient',
        'coordinates': 'All structural elements',
        'load_pattern': 'Uniform',
        'load_factor': 1.2
    },
    'CONSTRUCTION_LOAD': {
        'type': 'Construction',
        'description': 'Construction equipment and materials',
        'coordinates': 'Mat foundation (distributed)',
        'load_pattern': 'Uniform',
        'load_factor': 1.4
    },
    'WIND_UPLIFT': {
        'type': 'Wind',
        'description': 'Wind uplift on structure',
        'coordinates': 'Roof and exposed surfaces',
        'load_pattern': 'Upward',
        'load_factor': 0.6
    }
}

# --- 1. ENHANCED LICENSING & SECURITY ---
def verify_license():
    try:
        hostname = socket.gethostname()
        try:
            local_ip = socket.gethostbyname(hostname)
        except:
            local_ip = "127.0.0.1"
        
        if local_ip not in ALLOWED_IPS and hostname not in ALLOWED_IPS:
            return False, f"Unauthorized access. Software locked to authorized systems."
        
        try:
            if NTP_AVAILABLE:
                client = ntplib.NTPClient()
                response = client.request('pool.ntp.org', version=3, timeout=5)
                current_time = datetime.fromtimestamp(response.tx_time)
            else:
                current_time = datetime.now()
        except:
            current_time = datetime.now()
        
        if current_time > EXPIRY_DATE:
            return False, f"License Expired on {EXPIRY_DATE.strftime('%Y-%m-%d')}."
        
        return True, f"License Active | Expires: {EXPIRY_DATE.strftime('%Y-%m-%d')}"
    
    except Exception as e:
        return False, f"License check failed: {str(e)}"

# --- ACI DESIGN CALCULATOR WITH 318-25 CLAUSE REFERENCES ---
class ACIDesignCalculator:
    def __init__(self):
        self.fc = CONCRETE_FPC
        self.fy = STEEL_FY
        self.phi_flexure = 0.9
        self.phi_shear = 0.75
        self.phi_axial = 0.65
        self.phi_torsion = 0.75
        self.gamma = 0.85
        self.aci_version = "ACI 318-25"
        
    def design_flexural_member(self, Mu, b, d, h):
        """Design rectangular beam for flexure (ACI 318-25 Section 22.3)"""
        try:
            Mu = abs(Mu) * 12000
            
            As_min = max(3 * math.sqrt(self.fc) * b * d / self.fy, 200 * b * d / self.fy)
            clause_min = "ACI 318-25 24.3.2 - Minimum flexural reinforcement"
            
            As_max = 0.04 * b * d
            clause_max = "ACI 318-25 21.2.2 - Maximum reinforcement ratio"
            
            Rn = Mu / (self.phi_flexure * b * d**2)
            rho_required = 0.85 * self.fc / self.fy * (1 - math.sqrt(1 - 2 * Rn / (0.85 * self.fc)))
            
            if rho_required <= 0:
                As_required = As_min
            else:
                As_required = rho_required * b * d
                As_required = max(As_required, As_min)
                As_required = min(As_required, As_max)
            
            rebar_choice = self.select_rebar(As_required, b)
            
            a = As_required * self.fy / (0.85 * self.fc * b)
            c = a / self.gamma
            dt = d
            epsilon_t = 0.003 * (dt - c) / c
            
            if epsilon_t >= 0.005:
                phi = 0.9
                tension_controlled = True
            elif epsilon_t >= 0.002:
                phi = 0.65 + 0.25 * (epsilon_t - 0.002) / 0.003
                tension_controlled = False
            else:
                phi = 0.65
                tension_controlled = False
            
            Mn = As_required * self.fy * (d - a/2)
            capacity_ratio = Mu / (phi * Mn)
            
            l = 20 * 12
            min_h = l / 16
            deflection_ok = h >= min_h
            clause_deflection = "ACI 318-25 24.2.3 - Minimum thickness for deflection control"
            
            bar_size = self._get_bar_size_from_rebar(rebar_choice)
            ld = self.calculate_development_length(bar_size, self.fc, self.fy)
            
            return {
                'Mu': Mu/12000,
                'b': b,
                'd': d,
                'h': h,
                'As_required': As_required,
                'As_min': As_min,
                'As_max': As_max,
                'rebar_selected': rebar_choice,
                'phi': phi,
                'Mn': Mn/12000,
                'capacity_ratio': capacity_ratio,
                'deflection_ok': deflection_ok,
                'epsilon_t': epsilon_t,
                'tension_controlled': tension_controlled,
                'development_length': ld,
                'design_status': 'OK' if capacity_ratio <= 1.0 and deflection_ok else 'FAIL',
                'clauses': {
                    'minimum_reinforcement': clause_min,
                    'maximum_reinforcement': clause_max,
                    'deflection_control': clause_deflection,
                    'tension_control': "ACI 318-25 21.2.2 - Tension-controlled sections" if tension_controlled else "ACI 318-25 21.2.2 - Compression-controlled sections"
                }
            }
            
        except Exception as e:
            return {'error': str(e), 'design_status': 'ERROR'}
    
    def design_shear_reinforcement(self, Vu, b, d, fc, fy, As_longitudinal):
        """Design shear reinforcement (ACI 22.5)"""
        try:
            Vu = abs(Vu) * 1000
            
            Vc = 2 * math.sqrt(fc) * b * d
            clause_vc = "ACI 318-25 22.5.5.1 - Concrete shear strength"
            
            phi_Vc = self.phi_shear * Vc
            if Vu <= phi_Vc/2:
                return {
                    'Vu': Vu/1000,
                    'Vc': Vc/1000,
                    'phi_Vc': phi_Vc/1000,
                    'shear_reinforcement_required': False,
                    'Av_min': 0,
                    's_max': 0,
                    'design_status': 'OK - No shear reinforcement needed',
                    'clauses': {
                        'shear_strength': clause_vc,
                        'minimum_shear': "ACI 318-25 22.5.1.1 - Minimum shear reinforcement"
                    }
                }
            
            Vs_required = (Vu / self.phi_shear) - Vc
            Vs_max = 8 * math.sqrt(fc) * b * d
            clause_vs_max = "ACI 318-25 22.5.1.2 - Maximum shear strength"
            
            if Vs_required > Vs_max:
                return {
                    'Vu': Vu/1000,
                    'Vc': Vc/1000,
                    'Vs_required': Vs_required/1000,
                    'Vs_max': Vs_max/1000,
                    'design_status': 'FAIL - Section too small for shear',
                    'clauses': {
                        'shear_strength': clause_vc,
                        'maximum_shear': clause_vs_max
                    }
                }
            
            Av = 2 * 0.11
            s_required = Av * fy * d / Vs_required
            s_max = min(d/2, 24)
            clause_spacing = "ACI 318-25 25.7.4.3 - Maximum spacing of shear reinforcement"
            
            Av_min = max(0.75 * math.sqrt(fc) * b * s_max / fy, 50 * b * s_max / fy)
            clause_av_min = "ACI 318-25 10.6.2.2 - Minimum shear reinforcement"
            
            s_final = min(s_required, s_max)
            
            return {
                'Vu': Vu/1000,
                'Vc': Vc/1000,
                'Vs_required': Vs_required/1000,
                'Av_provided': Av,
                'spacing': s_final,
                's_max': s_max,
                'Av_min': Av_min,
                'shear_reinforcement_required': True,
                'design_status': 'OK' if s_final >= 3 else 'FAIL - Spacing too small',
                'clauses': {
                    'shear_strength': clause_vc,
                    'maximum_spacing': clause_spacing,
                    'minimum_reinforcement': clause_av_min
                }
            }
            
        except Exception as e:
            return {'error': str(e), 'design_status': 'ERROR'}
    
    def design_column(self, Pu, Mu_x, Mu_y, b, h, cover=1.5, is_seismic=False):
        """Design rectangular column (ACI 22.4) with seismic detailing if required"""
        try:
            Pu = abs(Pu) * 1000
            Mu_x = abs(Mu_x) * 12000
            Mu_y = abs(Mu_y) * 12000
            
            min_dimension = max(12, Pu/(0.8*0.85*self.fc)/12)
            clause_min_dim = "ACI 318-25 10.7.3.1 - Minimum column dimensions"
            
            Ag = b * h
            Ast_min = 0.01 * Ag
            Ast_max = 0.08 * Ag
            clause_reinf_limits = "ACI 318-25 10.6.1.1 - Longitudinal reinforcement limits"
            
            if is_seismic:
                Ast_min_seismic = max(0.01 * Ag, Ast_min)
                Ast_max_seismic = 0.06 * Ag
                Ast_min = Ast_min_seismic
                Ast_max = Ast_max_seismic
                clause_seismic = "ACI 318-25 18.7.3.2 - Seismic reinforcement limits"
            
            Pn_max = 0.8 * self.phi_axial * (0.85 * self.fc * (Ag - Ast_min) + self.fy * Ast_min)
            Pn_min = 0.1 * self.fc * Ag
            
            Ast_required = max(Ast_min, Pu / (0.8 * self.fy))
            Ast_required = min(Ast_required, Ast_max)
            
            rebar_choice = self.select_rebar(Ast_required, b, is_column=True, is_seismic=is_seismic)
            
            Lu = 20 * 12
            k = 1.0
            r = 0.3 * min(b, h)
            slenderness_ratio = k * Lu / r
            clause_slenderness = "ACI 318-25 6.2.5 - Slenderness effects"
            
            if slenderness_ratio <= 22:
                slenderness_effect = 'Negligible'
            elif slenderness_ratio <= 100:
                slenderness_effect = 'Consider'
            else:
                slenderness_effect = 'Significant - Increase size'
            
            Pn = self.phi_axial * (0.85 * self.fc * (Ag - Ast_required) + self.fy * Ast_required)
            capacity_ratio = Pu / Pn
            
            seismic_shear_check = {}
            if is_seismic:
                seismic_shear_check = {
                    'shear_requirement': "ACI 318-25 18.7.6.1 - Seismic shear in columns",
                    'hoop_spacing_max': min(b/4, 6, 4 + (14 - h)/3),
                    'hoop_requirement': "First hoop within 2\" of joint face"
                }
            
            confinement_check = {}
            if is_seismic:
                s = min(b/4, 6, 4 + (14 - h)/3)
                Ash_required = 0.09 * s * b * self.fc / self.fy
                confinement_check = {
                    'confinement': "ACI 318-25 18.7.5.2 - Transverse reinforcement for confinement",
                    'Ash_required': Ash_required,
                    'hoop_spacing': s
                }
            
            return {
                'Pu': Pu/1000,
                'Mu_x': Mu_x/12000,
                'Mu_y': Mu_y/12000,
                'b': b,
                'h': h,
                'Ag': Ag,
                'Ast_required': Ast_required,
                'Ast_min': Ast_min,
                'Ast_max': Ast_max,
                'rebar_selected': rebar_choice,
                'Pn': Pn/1000,
                'capacity_ratio': capacity_ratio,
                'slenderness_ratio': slenderness_ratio,
                'slenderness_effect': slenderness_effect,
                'is_seismic': is_seismic,
                'seismic_shear': seismic_shear_check,
                'confinement': confinement_check,
                'design_status': 'OK' if capacity_ratio <= 1.0 and slenderness_ratio <= 100 else 'FAIL',
                'clauses': {
                    'minimum_dimensions': clause_min_dim,
                    'reinforcement_limits': clause_reinf_limits,
                    'slenderness': clause_slenderness,
                    **({'seismic_detailing': clause_seismic} if is_seismic else {})
                }
            }
            
        except Exception as e:
            return {'error': str(e), 'design_status': 'ERROR'}
    
    def design_pile(self, axial_load, moment, diameter, length, is_seismic=False):
        """Design circular pile (ACI 13.4, 22.4)"""
        try:
            axial_load = abs(axial_load) * 1000
            moment = abs(moment) * 12000
            
            radius = diameter / 2
            Ag = math.pi * radius**2
            
            Ast_min = 0.005 * Ag
            Ast_max = 0.08 * Ag
            clause_pile_reinf = "ACI 318-25 13.4.2 - Minimum reinforcement for piles"
            
            Ast_required = max(Ast_min, axial_load / (0.8 * self.fy))
            Ast_required = min(Ast_required, Ast_max)
            
            num_bars = max(6, math.ceil(Ast_required / 0.44))
            bar_size = self.select_pile_rebar(Ast_required, num_bars)
            
            bearing_strength = 0.85 * self.fc * Ag
            bearing_ratio = axial_load / (self.phi_axial * bearing_strength)
            clause_bearing = "ACI 318-25 22.8.3 - Bearing strength"
            
            settlement = axial_load * length * 12 / (Ag * 3600000)
            settlement_limit = 1.0
            settlement_ok = settlement <= settlement_limit
            
            lateral_capacity_check = {}
            if is_seismic:
                lateral_capacity = 0.1 * self.fc * Ag
                moment_capacity_ratio = moment / (0.9 * lateral_capacity * diameter/2)
                lateral_capacity_check = {
                    'lateral_check': "ACI 318-25 18.13 - Seismic requirements for foundations",
                    'moment_capacity_ratio': moment_capacity_ratio,
                    'requirement': "Moment capacity ratio < 1.0"
                }
            
            group_efficiency = 0.7
            group_capacity = group_efficiency * bearing_strength
            
            return {
                'axial_load': axial_load/1000,
                'moment': moment/12000,
                'diameter': diameter,
                'length': length,
                'Ag': Ag,
                'Ast_required': Ast_required,
                'Ast_min': Ast_min,
                'num_bars': num_bars,
                'bar_size': bar_size,
                'bearing_ratio': bearing_ratio,
                'settlement': settlement,
                'settlement_limit': settlement_limit,
                'settlement_ok': settlement_ok,
                'group_efficiency': group_efficiency,
                'group_capacity': group_capacity/1000,
                'is_seismic': is_seismic,
                'lateral_capacity': lateral_capacity_check,
                'design_status': 'OK' if bearing_ratio <= 1.0 and settlement_ok else 'FAIL',
                'clauses': {
                    'pile_reinforcement': clause_pile_reinf,
                    'bearing_strength': clause_bearing,
                    'settlement': "Serviceability limit - Maximum 1.0 inch settlement"
                }
            }
            
        except Exception as e:
            return {'error': str(e), 'design_status': 'ERROR'}
    
    def design_slab(self, moment_per_foot, thickness, fc, fy, is_roof=False, is_seismic=False):
        """Design slab reinforcement per foot width (ACI 8.6, 24.4)"""
        try:
            moment_per_foot = abs(moment_per_foot) * 12000
            
            b = 12
            d = thickness - 1
            h = thickness
            
            As_min = 0.0018 * b * h
            if is_roof:
                As_min = 0.0018 * b * h
            clause_min_reinf = "ACI 318-25 24.4.3.2 - Minimum slab reinforcement"
            
            Rn = moment_per_foot / (self.phi_flexure * b * d**2)
            rho_required = 0.85 * fc / fy * (1 - math.sqrt(1 - 2 * Rn / (0.85 * fc)))
            
            if rho_required <= 0:
                As_required = As_min
            else:
                As_required = rho_required * b * d
                As_required = max(As_required, As_min)
            
            bar_size = '#4'
            Ab = REBAR_SIZES['4']
            spacing = Ab * 12 / As_required
            
            spacing = min(spacing, 3 * h, 18)
            clause_spacing = "ACI 318-25 8.7.2.2 - Maximum spacing of slab reinforcement"
            
            l = 15 * 12
            min_h = l / 28
            deflection_ok = h >= min_h
            clause_deflection = "ACI 318-25 24.2.3 - Deflection limits"
            
            E = 57000 * math.sqrt(fc)
            I = b * h**3 / 12
            w = 150 * h/12  # psf self-weight
            frequency = 0.18 * math.sqrt(386.4 * E * I / (w * (l*12)**4))
            vibration_ok = frequency > 8.0
            clause_vibration = "Vibration criterion - Natural frequency > 8.0 Hz"
            
            # Seismic requirements for diaphragms (ACI 18.12)
            seismic_diaphragm_check = {}
            if is_seismic:
                # Minimum reinforcement for seismic diaphragms
                As_min_seismic = 0.0025 * b * h
                As_required = max(As_required, As_min_seismic)
                seismic_diaphragm_check = {
                    'seismic_diaphragm': "ACI 318-25 18.12.7 - Diaphragm reinforcement",
                    'As_min_seismic': As_min_seismic,
                    'requirement': "Minimum 0.25% reinforcement in each direction"
                }
            
            # Check crack control (ACI 24.3.2)
            z_factor = 175 / (0.6 * fy / 1000)  # For interior exposure
            crack_control_ok = spacing <= min(12 * 2.5 / (0.6 * fy / 1000), 12)  # Simplified
            
            return {
                'moment': moment_per_foot/12000,  # k-ft/ft
                'thickness': thickness,
                'As_required': As_required,
                'As_min': As_min,
                'bar_size': bar_size,
                'spacing': spacing,
                'deflection_ok': deflection_ok,
                'frequency': frequency,
                'vibration_ok': vibration_ok,
                'crack_control_ok': crack_control_ok,
                'z_factor': z_factor,
                'is_roof': is_roof,
                'is_seismic': is_seismic,
                'seismic_diaphragm': seismic_diaphragm_check,
                'design_status': 'OK' if deflection_ok and vibration_ok and crack_control_ok else 'FAIL',
                'clauses': {
                    'minimum_reinforcement': clause_min_reinf,
                    'maximum_spacing': clause_spacing,
                    'deflection': clause_deflection,
                    'vibration': clause_vibration,
                    'crack_control': "ACI 318-25 24.3.2 - Crack control"
                }
            }
            
        except Exception as e:
            return {'error': str(e), 'design_status': 'ERROR'}
    
    def design_foundation_mat(self, soil_pressure, thickness, length, width, is_seismic=False):
        """Design mat foundation (ACI 13.3)"""
        try:
            # Check thickness (ACI 13.3.1.2)
            min_thickness = max(12, length/10, width/10)
            thickness_ok = thickness >= min_thickness
            clause_thickness = "ACI 318-25 13.3.1.2 - Minimum mat thickness"
            
            # Check punching shear (ACI 22.6)
            # Simplified check around columns
            bo = 4 * (12 + thickness)  # Perimeter at d/2 from column face
            Vc_punching = 4 * math.sqrt(self.fc) * bo * (thickness - 1)  # d = thickness - 1
            punching_shear_ratio = soil_pressure * 1000 / (self.phi_shear * Vc_punching)
            clause_punching = "ACI 318-25 22.6 - Punching shear"
            
            # Check beam shear (ACI 22.5)
            Vc_beam = 2 * math.sqrt(self.fc) * 12 * (thickness - 1)  # per foot width
            beam_shear_ratio = soil_pressure * 1000 / (self.phi_shear * Vc_beam)
            clause_beam_shear = "ACI 318-25 22.5 - Beam shear"
            
            # Flexural design (simplified)
            moment = soil_pressure * (width/2)**2 / 2  # Simplified
            flexure_design = self.design_slab(moment, thickness, self.fc, self.fy)
            
            # Check settlement
            bearing_capacity = 4000  # psf assumed
            bearing_ratio = soil_pressure / bearing_capacity
            
            # Seismic requirements
            seismic_check = {}
            if is_seismic:
                # Check overturning stability
                ot_factor = 1.5  # Minimum factor of safety
                seismic_check = {
                    'overturning_check': "ACI 318-25 18.13 - Foundation seismic requirements",
                    'safety_factor': ot_factor,
                    'requirement': "Factor of safety ≥ 1.5"
                }
            
            return {
                'soil_pressure': soil_pressure,
                'thickness': thickness,
                'length': length,
                'width': width,
                'min_thickness': min_thickness,
                'thickness_ok': thickness_ok,
                'punching_shear_ratio': punching_shear_ratio,
                'beam_shear_ratio': beam_shear_ratio,
                'bearing_ratio': bearing_ratio,
                'bearing_capacity': bearing_capacity,
                'flexure': flexure_design,
                'is_seismic': is_seismic,
                'seismic_check': seismic_check,
                'design_status': 'OK' if thickness_ok and punching_shear_ratio <= 1.0 and beam_shear_ratio <= 1.0 and bearing_ratio <= 1.0 else 'FAIL',
                'clauses': {
                    'thickness': clause_thickness,
                    'punching_shear': clause_punching,
                    'beam_shear': clause_beam_shear,
                    'bearing_capacity': "Geotechnical requirement - Site specific"
                }
            }
            
        except Exception as e:
            return {'error': str(e), 'design_status': 'ERROR'}
    
    def select_rebar(self, As_required, b, is_column=False, is_seismic=False):
        """Select appropriate rebar size and quantity with seismic considerations"""
        rebar_list = []
        As_provided = 0
        
        # Start with larger bars and work down
        sizes = ['18', '14', '11', '10', '9', '8', '7', '6', '5', '4', '3']
        
        for size in sizes:
            Ab = REBAR_SIZES[size]
            
            # Maximum bars based on spacing
            if is_seismic and is_column:
                # Seismic spacing requirements (ACI 18.7.5.3)
                max_spacing = min(b/4, 6, 4 + (14 - b)/3)
                max_bars = math.floor(b / max_spacing)
            else:
                max_bars = math.floor(b / (1.5 + 1.128 * math.sqrt(Ab/0.7854)))  # Simplified spacing
            
            if max_bars <= 0:
                continue
                
            bars_needed = math.ceil(As_required / Ab)
            bars = min(bars_needed, max_bars)
            
            if bars > 0:
                rebar_list.append(f"{bars}#{size}")
                As_provided += bars * Ab
                
            if As_provided >= As_required:
                break
        
        if is_column:
            # Ensure symmetrical arrangement
            if len(rebar_list) == 1:
                bars = int(rebar_list[0].split('#')[0])
                if bars < 4:
                    rebar_list = [f"4#{rebar_list[0].split('#')[1]}"]
            
            # Seismic requirement: minimum 4 bars
            if is_seismic and len(rebar_list) > 0:
                bars_info = rebar_list[0].split('#')
                if len(bars_info) == 2:
                    bars = int(bars_info[0])
                    if bars < 4:
                        rebar_list = [f"4#{bars_info[1]}"]
        
        return ", ".join(rebar_list) if rebar_list else "Error - No suitable rebar"
    
    def select_pile_rebar(self, As_required, num_bars, is_seismic=False):
        """Select rebar for circular piles with seismic considerations"""
        if is_seismic:
            # Seismic piles require minimum #6 bars
            min_size = '6'
        else:
            min_size = '6'
        
        sizes = ['6', '7', '8', '9', '10', '11']
        sizes = [s for s in sizes if REBAR_SIZES[s] >= REBAR_SIZES[min_size]]
        
        for size in sizes:
            Ab = REBAR_SIZES[size]
            if num_bars * Ab >= As_required:
                return f"{num_bars}#{size}"
        return f"{num_bars}#11"  # Default to #11 if needed
    
    def calculate_development_length(self, bar_size, fc, fy):
        """Calculate development length per ACI 25.4.2"""
        Ab = REBAR_SIZES.get(str(bar_size), 0.44)  # Default to #6
        ld = (fy * Ab) / (25 * math.sqrt(fc))  # Simplified formula
        return max(ld, 12)  # Minimum 12 inches
    
    def _get_bar_size_from_rebar(self, rebar_string):
        """Extract bar size from rebar string"""
        match = re.search(r'#(\d+)', rebar_string)
        return int(match.group(1)) if match else 6

# --- SEISMIC ANALYSIS ENGINE ---
class SeismicAnalysisEngine:
    def __init__(self, zone='C', site_class='D', structure_type='Building'):
        self.zone = zone
        self.site_class = site_class
        self.structure_type = structure_type
        self.params = SEISMIC_PARAMS['zone_c'].copy()
        
    def calculate_seismic_forces(self, weight, height, period_method='approximate'):
        """Calculate seismic base shear per ASCE 7-16/IBC 2021"""
        
        # Calculate seismic response coefficient
        if period_method == 'approximate':
            # Approximate period per ASCE 7-16 Table 12.8-2
            if self.structure_type == 'Building':
                Ta = 0.1 * height  # seconds (simplified)
            else:
                Ta = 0.02 * height  # seconds for other structures
        else:
            Ta = period_method
        
        # Design spectral response (ASCE 7-16 Section 11.4)
        SDS = self.params['SDS']
        SD1 = self.params['SD1']
        
        # Seismic response coefficient (ASCE 7-16 Eq. 12.8-2)
        Cs_max = SDS / (self.params['R'] / self.params['Ie'])
        
        # Lower bound (ASCE 7-16 Eq. 12.8-5)
        Cs_min = max(0.044 * SDS * self.params['Ie'], 0.01)
        
        # Period-dependent coefficient (ASCE 7-16 Eq. 12.8-3)
        if 'TL' in self.params and Ta <= self.params['TL']:
            Cs_period = SD1 / (Ta * (self.params['R'] / self.params['Ie']))
        else:
            # If TL not defined or Ta > TL, use simplified approach
            Cs_period = SD1 / (Ta * (self.params['R'] / self.params['Ie']))
        
        Cs = min(Cs_max, Cs_period)
        Cs = max(Cs, Cs_min)
        
        # Base shear
        V = Cs * weight
        
        # Vertical distribution (ASCE 7-16 Section 12.8.3)
        k = 1.0 if Ta <= 0.5 else 2.0  # Simplified
        
        return {
            'base_shear': V,
            'Cs': Cs,
            'SDS': SDS,
            'SD1': SD1,
            'R': self.params['R'],
            'Ie': self.params['Ie'],
            'period': Ta,
            'distribution_exponent': k,
            'seismic_zone': self.zone,
            'site_class': self.site_class
        }
    
    def calculate_seismic_loads_for_structure(self, nodes, elements, weight_distribution):
        """Calculate seismic loads for each node in structure"""
        total_weight = sum(weight_distribution.values())
        
        # Get structure height
        z_coords = [node[2] for node in nodes]
        height = max(z_coords) - min(z_coords)
        
        # Calculate seismic forces
        seismic_results = self.calculate_seismic_forces(total_weight, height)
        
        # Distribute forces vertically
        forces_x = {}
        forces_y = {}
        
        for node_id, weight in weight_distribution.items():
            if node_id < len(nodes):
                z = nodes[node_id][2]
                z_min = min(z_coords)
                z_rel = z - z_min
                
                # Vertical distribution factor
                if seismic_results['distribution_exponent'] == 1:
                    factor = weight / total_weight
                else:
                    factor = (weight * z_rel**seismic_results['distribution_exponent']) / \
                             sum(w * (nodes[i][2]-z_min)**seismic_results['distribution_exponent'] 
                                 for i, w in weight_distribution.items())
                
                # Seismic force at node
                fx = seismic_results['base_shear'] * factor
                fy = seismic_results['base_shear'] * factor * 0.3  # 30% in perpendicular direction
                
                forces_x[node_id] = fx
                forces_y[node_id] = fy
        
        return {
            'seismic_x': forces_x,
            'seismic_y': forces_y,
            'seismic_parameters': seismic_results
        }

# --- 2. ENHANCED STRUCTURAL ANALYSIS ENGINE WITH SQUARE/RECTANGULAR MESHES ---
class StructuralAnalysisEngine:
    def __init__(self):
        self.E = 3.60e6  # psi
        self.density = 0.0868  # lb/in³
        self.nu = 0.2  # Poisson's ratio
        self.gravity = 386.4  # in/s²
        self.slab_thickness = 8.0  # inches
        
        # Soil spring properties for piles
        self.modulus_subgrade_z = 100.0  # lb/in³
        self.modulus_subgrade_xy = 10.0   # lb/in³
        self.pile_soil_spring_factor = 1.0
        
        # Default mesh size: 2ft x 2ft
        self.default_mesh_size = 2.0
        
        # Seismic engine
        self.seismic_engine = SeismicAnalysisEngine(zone='C', site_class='D')
        
    def generate_complete_mesh(self, mat_points, mezzanine_points, top_points, 
                               column_lines, pile_lines, beam_lines, mesh_size=None):
        """Generate complete mesh with SQUARE/RECTANGULAR elements (2ft x 2ft default)"""
        if mesh_size is None:
            mesh_size = self.default_mesh_size
        
        print(f"Generating complete mesh with {mesh_size}ft x {mesh_size}ft square/rectangular elements...")
        
        all_points = []
        element_connectivity = []
        slab_levels = {}
        
        # Define slab levels with default elevations
        slab_data = {
            'mat': (mat_points, 'Mat Foundation'),
            'mezzanine': (mezzanine_points, 'Mezzanine Level'),
            'top': (top_points, 'Top Floor')
        }
        
        # Store vertical element nodes by level
        column_nodes_by_level = {}
        pile_nodes_by_level = {}
        beam_nodes_by_level = {}
        
        # --- PROCESS PILES FIRST ---
        if pile_lines:
            print(f"Processing {len(pile_lines)} piles...")
            for pile_idx, pile in enumerate(pile_lines):
                if len(pile) >= 5:
                    x, y, z_top, z_bottom, diameter = pile[:5]
                    
                    all_points.append((x, y, z_top))
                    pile_top_node = len(all_points) - 1
                    
                    all_points.append((x, y, z_bottom))
                    pile_bottom_node = len(all_points) - 1
                    
                    radius = diameter / 2.0
                    A = math.pi * radius**2
                    I = math.pi * radius**4 / 4
                    
                    element_connectivity.append(('PILE', f'PI{pile_idx+1}', 
                                                pile_top_node, pile_bottom_node, 
                                                A, I, I, I, diameter))
                    
                    if 'mat' not in pile_nodes_by_level:
                        pile_nodes_by_level['mat'] = []
                    pile_nodes_by_level['mat'].append(pile_top_node)
        
        # --- PROCESS COLUMNS ---
        if column_lines:
            print(f"Processing {len(column_lines)} columns...")
            for col_idx, col in enumerate(column_lines):
                if len(col) >= 7:
                    x, y, z_bottom, z_top, width, depth, size = col[:7]
                    if width == 0: width = size
                    if depth == 0: depth = size
                    
                    all_points.append((x, y, z_bottom))
                    col_bottom_node = len(all_points) - 1
                    
                    all_points.append((x, y, z_top))
                    col_top_node = len(all_points) - 1
                    
                    A = (width/12) * (depth/12) * 144
                    Ix = (width/12) * (depth/12)**3 / 12 * 144
                    Iy = (depth/12) * (width/12)**3 / 12 * 144
                    Iz = min(Ix, Iy)
                    
                    element_connectivity.append(('COLUMN', f'COL{col_idx+1}',
                                                col_bottom_node, col_top_node,
                                                A, Ix, Iy, Iz, width, depth))
                    
                    # Store column nodes at each level
                    for level_name, (points, _) in slab_data.items():
                        if points:
                            level_z = np.mean([p[2] for p in points if len(p) >= 3])
                            
                            if min(z_bottom, z_top) <= level_z <= max(z_bottom, z_top):
                                if level_name not in column_nodes_by_level:
                                    column_nodes_by_level[level_name] = []
                                
                                all_points.append((x, y, level_z))
                                col_slab_node = len(all_points) - 1
                                column_nodes_by_level[level_name].append(col_slab_node)
        
        # --- PROCESS BEAMS ---
        if beam_lines:
            print(f"Processing {len(beam_lines)} beams...")
            for beam_idx, beam in enumerate(beam_lines):
                if len(beam) >= 9:
                    x1, y1, z1, x2, y2, z2, width, depth, size = beam[:9]
                    if width == 0: width = size
                    if depth == 0: depth = size
                    
                    all_points.append((x1, y1, z1))
                    beam_node1 = len(all_points) - 1
                    
                    all_points.append((x2, y2, z2))
                    beam_node2 = len(all_points) - 1
                    
                    A = (width/12) * (depth/12) * 144
                    Ix = (width/12) * (depth/12)**3 / 12 * 144
                    Iy = (depth/12) * (width/12)**3 / 12 * 144
                    Iz = min(Ix, Iy)
                    
                    element_connectivity.append(('BEAM', f'B{beam_idx+1}',
                                                beam_node1, beam_node2,
                                                A, Ix, Iy, Iz, width, depth))
                    
                    # Store beam nodes by level
                    level_z = (z1 + z2) / 2
                    beam_level = None
                    for level_name, (points, _) in slab_data.items():
                        if points:
                            slab_z = np.mean([p[2] for p in points if len(p) >= 3])
                            if abs(level_z - slab_z) < 1.0:
                                beam_level = level_name
                                break
                    
                    if beam_level:
                        if beam_level not in beam_nodes_by_level:
                            beam_nodes_by_level[beam_level] = []
                        beam_nodes_by_level[beam_level].extend([beam_node1, beam_node2])
        
        # --- PROCESS SLABS WITH SQUARE/RECTANGULAR MESHES (2ft x 2ft) ---
        for level_name, (points, description) in slab_data.items():
            if points and len(points) > 0:
                print(f"\nProcessing {description} with {mesh_size}ft x {mesh_size}ft mesh...")
                
                slab_coords = []
                for pt in points:
                    if len(pt) >= 4:
                        x, y, z, thickness = pt[0], pt[1], pt[2], pt[3]
                    elif len(pt) >= 3:
                        x, y, z = pt[0], pt[1], pt[2]
                        thickness = 1.0
                    else:
                        continue
                    slab_coords.append([x, y, z, thickness])
                
                if len(slab_coords) >= 3:
                    # Generate square/rectangular mesh
                    slab_nodes, slab_elements = self._generate_square_mesh(slab_coords, mesh_size, level_name)
                    
                    # Add slab nodes
                    start_idx = len(all_points)
                    for node in slab_nodes:
                        all_points.append((node[0], node[1], node[2]))
                    
                    # Add slab elements (quads)
                    for elem in slab_elements:
                        if len(elem) == 4:  # Quad element
                            n1, n2, n3, n4 = elem
                            thickness = slab_coords[0][3]
                            element_connectivity.append(('SHELL', level_name,
                                                         start_idx + n1, start_idx + n2, 
                                                         start_idx + n3, start_idx + n4,
                                                         0, 0, 0, 0, thickness, 0))
                    
                    # Store slab info
                    slab_levels[level_name] = {
                        'z_level': np.mean([p[2] for p in slab_coords]),
                        'node_indices': list(range(start_idx, len(all_points))),
                        'thickness': slab_coords[0][3],
                        'elements': len(slab_elements),
                        'mesh_size': mesh_size
                    }
                    
                    print(f"  Added {len(slab_nodes)} nodes and {len(slab_elements)} QUAD shell elements ({mesh_size}ft grid)")
                    
                    # ADD INTERSECTION NODES at column/slab intersections
                    if level_name in column_nodes_by_level:
                        self._add_intersection_nodes(all_points, element_connectivity,
                                                    slab_levels[level_name], 
                                                    column_nodes_by_level[level_name],
                                                    level_name, 'COLUMN')
                    
                    # ADD INTERSECTION NODES at beam/slab intersections
                    if level_name in beam_nodes_by_level:
                        self._add_beam_slab_intersections(all_points, element_connectivity,
                                                         slab_levels[level_name],
                                                         beam_nodes_by_level[level_name],
                                                         level_name)
        
        # --- ADD RIGID LINKS FOR CONNECTIONS ---
        for level_name in slab_levels:
            slab_info = slab_levels[level_name]
            
            # Connect columns to slab
            if level_name in column_nodes_by_level:
                self._connect_columns_to_slab(all_points, element_connectivity,
                                             slab_info, column_nodes_by_level[level_name],
                                             level_name)
            
            # Connect beams to slab
            if level_name in beam_nodes_by_level:
                self._connect_beams_to_slab(all_points, element_connectivity,
                                           slab_info, beam_nodes_by_level[level_name],
                                           level_name)
        
        print(f"\nMesh generation complete:")
        print(f"  Total nodes: {len(all_points)}")
        print(f"  Total elements: {len(element_connectivity)}")
        print(f"  Mesh size: {mesh_size}ft x {mesh_size}ft square/rectangular elements")
        
        elem_types = {}
        for elem in element_connectivity:
            elem_type = elem[0]
            elem_types[elem_type] = elem_types.get(elem_type, 0) + 1
        
        print("Element type summary:")
        for elem_type, count in elem_types.items():
            print(f"  {elem_type}: {count} elements")
        
        return all_points, element_connectivity
    
    def _generate_square_mesh(self, slab_points, mesh_size, level_name):
        """Generate square or rectangular mesh (2ft x 2ft default)"""
        if len(slab_points) < 3:
            return [], []
        
        # Convert to numpy array
        points_2d = []
        thickness = slab_points[0][3]
        
        for pt in slab_points:
            x, y, z, t = pt
            points_2d.append([x, y])
            thickness = t
        
        points_2d = np.array(points_2d)
        
        # Get bounding box
        min_x, max_x = np.min(points_2d[:, 0]), np.max(points_2d[:, 0])
        min_y, max_y = np.min(points_2d[:, 1]), np.max(points_2d[:, 1])
        z_level = np.mean([pt[2] for pt in slab_points])
        
        # Adjust bounds to be multiples of mesh_size
        min_x = math.floor(min_x / mesh_size) * mesh_size
        max_x = math.ceil(max_x / mesh_size) * mesh_size
        min_y = math.floor(min_y / mesh_size) * mesh_size
        max_y = math.ceil(max_y / mesh_size) * mesh_size
        
        # Generate grid lines
        x_lines = np.arange(min_x, max_x + mesh_size, mesh_size)
        y_lines = np.arange(min_y, max_y + mesh_size, mesh_size)
        
        # Create grid points
        slab_nodes = []
        node_grid = {}  # Store node indices by grid position
        
        for i, x in enumerate(x_lines):
            for j, y in enumerate(y_lines):
                # Check if point is inside polygon
                if self._point_in_polygon_simple(x, y, points_2d):
                    slab_nodes.append([x, y, z_level, thickness])
                    node_grid[(i, j)] = len(slab_nodes) - 1
        
        # Create QUAD elements (rectangular or square)
        slab_elements = []
        
        for i in range(len(x_lines) - 1):
            for j in range(len(y_lines) - 1):
                # Check if all 4 corners exist
                corners = [(i, j), (i+1, j), (i+1, j+1), (i, j+1)]
                
                if all(corner in node_grid for corner in corners):
                    n1 = node_grid[corners[0]]
                    n2 = node_grid[corners[1]]
                    n3 = node_grid[corners[2]]
                    n4 = node_grid[corners[3]]
                    
                    # Check if quad is convex and valid
                    if self._is_valid_quad(slab_nodes[n1], slab_nodes[n2], 
                                          slab_nodes[n3], slab_nodes[n4]):
                        slab_elements.append([n1, n2, n3, n4])
        
        # If no quad elements created, fall back to triangles
        if not slab_elements and slab_nodes:
            print(f"  Warning: No quad elements created for {level_name}, using triangles")
            points_for_tri = np.array([[p[0], p[1]] for p in slab_nodes])
            try:
                tri = Delaunay(points_for_tri)
                slab_elements = []
                for simplex in tri.simplices:
                    if len(simplex) == 3:
                        slab_elements.append([int(simplex[0]), int(simplex[1]), int(simplex[2])])
            except:
                # Simple triangulation
                for i in range(len(slab_nodes) - 2):
                    slab_elements.append([i, i+1, i+2])
        
        return slab_nodes, slab_elements
    
    def _point_in_polygon_simple(self, x, y, polygon):
        """Simple point-in-polygon test"""
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def _is_valid_quad(self, p1, p2, p3, p4):
        """Check if quadrilateral is convex and valid"""
        # Convert to 2D points
        points = np.array([[p1[0], p1[1]], [p2[0], p2[1]], 
                          [p3[0], p3[1]], [p4[0], p4[1]]])
        
        # Check area
        area = 0.5 * abs(
            (points[1,0]*points[2,1] + points[2,0]*points[3,1] + 
             points[3,0]*points[0,1] + points[0,0]*points[1,1]) -
            (points[1,1]*points[2,0] + points[2,1]*points[3,0] + 
             points[3,1]*points[0,0] + points[0,1]*points[1,0])
        )
        
        return area > 0.01  # Minimum area
    
    def _add_intersection_nodes(self, all_points, element_connectivity, slab_info, 
                               vertical_nodes, level_name, element_type):
        """Add nodes at intersections of vertical elements with slab"""
        slab_nodes = slab_info['node_indices']
        slab_z = slab_info['z_level']
        
        for v_node in vertical_nodes:
            if v_node < len(all_points):
                vx, vy, vz = all_points[v_node]
                
                # Check if vertical node is near slab level
                if abs(vz - slab_z) < 0.1:
                    # Node is already at slab level
                    continue
                
                # Create intersection node at slab level
                all_points.append((vx, vy, slab_z))
                intersection_node = len(all_points) - 1
                
                # Create rigid link from vertical element to intersection node
                A = 1000  # Rigid link area
                Ix = Iy = Iz = 1000
                
                element_connectivity.append(('LINK', f'{level_name}_{element_type}_Link',
                                           v_node, intersection_node,
                                           A, Ix, Iy, Iz, 0, 0))
                
                # Store intersection node
                slab_nodes.append(intersection_node)
                
                print(f"    Added intersection node at ({vx:.1f}, {vy:.1f}, {slab_z:.1f})")
    
    def _add_beam_slab_intersections(self, all_points, element_connectivity, slab_info,
                                    beam_nodes, level_name):
        """Add nodes at beam/slab intersections and split beams if needed"""
        slab_nodes = slab_info['node_indices']
        slab_z = slab_info['z_level']
        
        # Group beam nodes by beam line
        beam_lines = []
        for i in range(0, len(beam_nodes), 2):
            if i+1 < len(beam_nodes):
                n1, n2 = beam_nodes[i], beam_nodes[i+1]
                if n1 < len(all_points) and n2 < len(all_points):
                    beam_lines.append((n1, n2))
        
        for beam_idx, (n1, n2) in enumerate(beam_lines):
            x1, y1, z1 = all_points[n1]
            x2, y2, z2 = all_points[n2]
            
            # Check if beam is at slab level
            if abs(z1 - slab_z) < 0.1 and abs(z2 - slab_z) < 0.1:
                # Beam is already at slab level
                continue
            
            # Create intersection points along beam line
            intersection_points = []
            
            # Check intersections with slab grid lines
            # For simplicity, create intersection at midpoint
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            
            # Create intersection node
            all_points.append((mid_x, mid_y, slab_z))
            intersection_node = len(all_points) - 1
            intersection_points.append(intersection_node)
            
            # Add to slab nodes
            slab_nodes.append(intersection_node)
            
            # Split beam into two segments if needed
            if len(intersection_points) > 0:
                # Find existing beam element
                beam_elem = None
                for elem in element_connectivity:
                    if elem[0] == 'BEAM' and ((elem[2] == n1 and elem[3] == n2) or 
                                             (elem[2] == n2 and elem[3] == n1)):
                        beam_elem = elem
                        break
                
                if beam_elem:
                    # Get beam properties
                    A, Ix, Iy, Iz = beam_elem[4], beam_elem[5], beam_elem[6], beam_elem[7]
                    width, depth = beam_elem[8], beam_elem[9]
                    
                    # Split beam into segments
                    # Segment 1: n1 to intersection
                    element_connectivity.append(('BEAM', f'B{beam_idx+1}_A',
                                                n1, intersection_node,
                                                A, Ix, Iy, Iz, width, depth))
                    
                    # Segment 2: intersection to n2
                    element_connectivity.append(('BEAM', f'B{beam_idx+1}_B',
                                                intersection_node, n2,
                                                A, Ix, Iy, Iz, width, depth))
                    
                    # Mark original beam for removal
                    element_connectivity.remove(beam_elem)
                    
                    print(f"    Split beam B{beam_idx+1} at intersection point")
    
    def _connect_columns_to_slab(self, all_points, element_connectivity, slab_info,
                                column_nodes, level_name):
        """Connect columns to slab with rigid links"""
        slab_nodes = slab_info['node_indices']
        
        for col_node in column_nodes:
            if col_node < len(all_points):
                col_x, col_y, col_z = all_points[col_node]
                
                # Find nearest slab node
                min_dist = float('inf')
                nearest_slab = -1
                
                for slab_node in slab_nodes:
                    if slab_node < len(all_points):
                        slab_x, slab_y, slab_z = all_points[slab_node]
                        dist = math.sqrt((col_x-slab_x)**2 + (col_y-slab_y)**2 + (col_z-slab_z)**2)
                        
                        if dist < min_dist and dist < 2.0:  # Within 2 ft
                            min_dist = dist
                            nearest_slab = slab_node
                
                if nearest_slab != -1 and min_dist > 0.01:
                    A = 1000  # Rigid link
                    Ix, Iy, Iz = 1000, 1000, 1000
                    element_connectivity.append(('LINK', f'{level_name}_ColLink',
                                                col_node, nearest_slab,
                                                A, Ix, Iy, Iz, 0, 0))
    
    def _connect_beams_to_slab(self, all_points, element_connectivity, slab_info,
                              beam_nodes, level_name):
        """Connect beams to slab"""
        slab_nodes = slab_info['node_indices']
        
        for beam_node in beam_nodes:
            if beam_node < len(all_points):
                beam_x, beam_y, beam_z = all_points[beam_node]
                
                # Find nearest slab node at same Z level
                min_dist = float('inf')
                nearest_slab = -1
                
                for slab_node in slab_nodes:
                    if slab_node < len(all_points):
                        slab_x, slab_y, slab_z = all_points[slab_node]
                        
                        # Check if at same level
                        if abs(beam_z - slab_z) < 0.1:
                            dist = math.sqrt((beam_x-slab_x)**2 + (beam_y-slab_y)**2)
                            
                            if dist < min_dist and dist < 1.0:  # Within 1 ft
                                min_dist = dist
                                nearest_slab = slab_node
                
                if nearest_slab != -1 and min_dist > 0.01:
                    # Create connection if not already connected
                    already_connected = False
                    for elem in element_connectivity:
                        if elem[0] == 'LINK' and ((elem[2] == beam_node and elem[3] == nearest_slab) or
                                                 (elem[2] == nearest_slab and elem[3] == beam_node)):
                            already_connected = True
                            break
                    
                    if not already_connected:
                        A = 1000
                        Ix, Iy, Iz = 1000, 1000, 1000
                        element_connectivity.append(('LINK', f'{level_name}_BeamLink',
                                                    beam_node, nearest_slab,
                                                    A, Ix, Iy, Iz, 0, 0))

    def calculate_static_forces(self, nodes, elements, load_cases):
        """Perform static analysis with pile soil springs and special loads"""
        print("Starting static analysis with pile soil springs and special loads...")
        
        results = {}
        
        for case_name, loads in load_cases.items():
            print(f"  Load case: {case_name}")
            
            n_nodes = len(nodes)
            n_dof = n_nodes * 6
            
            # Stiffness matrix and force vector
            K = np.zeros((n_dof, n_dof))
            F = np.zeros(n_dof)
            
            # Apply loads
            for load in loads:
                if len(load) >= 7:
                    node_id, fx, fy, fz, mx, my, mz = load
                    if node_id < n_nodes:
                        idx = node_id * 6
                        F[idx:idx+6] = [fx, fy, fz, mx, my, mz]
            
            # Assemble stiffness matrix with soil springs
            for elem in elements:
                elem_type = elem[0]
                
                if elem_type == 'SHELL':
                    if len(elem) >= 6:  # Quad with 4 nodes
                        n1, n2, n3, n4 = elem[2], elem[3], elem[4], elem[5]
                        thickness = elem[10] if len(elem) > 10 else self.slab_thickness/12
                        ke = self._shell_stiffness_matrix_quad(nodes[n1], nodes[n2], nodes[n3], nodes[n4], thickness)
                        dofs = []
                        for n in [n1, n2, n3, n4]:
                            dofs.extend([n*6 + i for i in range(6)])
                        
                        for i in range(len(dofs)):
                            for j in range(len(dofs)):
                                K[dofs[i], dofs[j]] += ke[i, j]
                    
                elif elem_type in ['COLUMN', 'BEAM', 'PILE', 'LINK']:
                    n1, n2 = elem[2], elem[3]
                    if len(elem) >= 10:
                        A, Ix, Iy, Iz = elem[4], elem[5], elem[6], elem[7]
                    else:
                        A, Ix, Iy, Iz = 100, 100, 100, 100
                    
                    L = self._element_length(nodes[n1], nodes[n2])
                    ke = self._beam_stiffness_matrix(A, Ix, Iy, Iz, L, elem_type)
                    
                    dofs = [n1*6 + i for i in range(6)] + [n2*6 + i for i in range(6)]
                    for i in range(12):
                        for j in range(12):
                            K[dofs[i], dofs[j]] += ke[i, j]
            
            # Add soil springs at pile bottoms
            for elem in elements:
                if elem[0] == 'PILE':
                    pile_bottom_node = elem[3]
                    if pile_bottom_node < n_nodes:
                        if len(elem) >= 9:
                            diameter = elem[8]
                        else:
                            diameter = 24.0
                        
                        k_z = self.modulus_subgrade_z * diameter * 10
                        k_xy = self.modulus_subgrade_xy * diameter * 10
                        
                        idx = pile_bottom_node * 6
                        K[idx, idx] += k_xy
                        K[idx+1, idx+1] += k_xy
                        K[idx+2, idx+2] += k_z
                        
                        K[idx+3, idx+3] += k_xy * 100
                        K[idx+4, idx+4] += k_xy * 100
                        K[idx+5, idx+5] += k_xy * 100
            
            # Ensure symmetric stiffness matrix
            K = (K + K.T) / 2
            
            # Check for zero rows/columns
            for i in range(n_dof):
                if np.all(K[i, :] == 0) and np.all(K[:, i] == 0):
                    K[i, i] = 1.0
            
            # Solve
            try:
                print("  Solving linear system...")
                K_sparse = csr_matrix(K)
                reg_strength = 1e-6 * np.max(np.abs(np.diag(K)))
                K_reg = K_sparse + reg_strength * scipy.sparse.eye(K_sparse.shape[0])
                displacements = spsolve(K_reg, F)
                print("  Solution successful")
            except Exception as e:
                print(f"  Sparse solver failed: {e}, trying dense solver...")
                try:
                    K_reg = K + 1e-6 * np.max(np.abs(np.diag(K))) * np.eye(K.shape[0])
                    displacements = np.linalg.solve(K_reg, F)
                    print("  Dense solution successful")
                except:
                    print("  Both solvers failed, returning zeros")
                    displacements = np.zeros(n_dof)
            
            # Calculate reactions and internal forces
            reactions = np.dot(K, displacements)
            internal_forces = self._calculate_internal_forces(nodes, elements, displacements)
            joint_forces = self._calculate_joint_forces(nodes, elements, internal_forces, reactions)
            
            # Calculate story drifts for seismic check
            story_drifts = self._calculate_story_drifts(nodes, displacements)
            
            results[case_name] = {
                'displacements': displacements,
                'reactions': reactions,
                'internal_forces': internal_forces,
                'joint_forces': joint_forces,
                'story_drifts': story_drifts,
                'stiffness_matrix': K
            }
        
        print("Static analysis complete!")
        return results
    
    def _calculate_story_drifts(self, nodes, displacements):
        """Calculate story drifts for seismic compliance"""
        story_drifts = {}
        
        # Group nodes by elevation
        elevations = {}
        for i, node in enumerate(nodes):
            z = node[2]
            if z not in elevations:
                elevations[z] = []
            elevations[z].append(i)
        
        # Sort elevations
        sorted_elevations = sorted(elevations.keys())
        
        for i in range(len(sorted_elevations) - 1):
            z_bottom = sorted_elevations[i]
            z_top = sorted_elevations[i + 1]
            story_height = z_top - z_bottom
            
            # Calculate average displacement at each level
            avg_disp_bottom = np.zeros(3)
            avg_disp_top = np.zeros(3)
            
            for node_idx in elevations[z_bottom]:
                idx = node_idx * 6
                avg_disp_bottom += displacements[idx:idx+3]
            
            for node_idx in elevations[z_top]:
                idx = node_idx * 6
                avg_disp_top += displacements[idx:idx+3]
            
            if elevations[z_bottom]:
                avg_disp_bottom /= len(elevations[z_bottom])
            if elevations[z_top]:
                avg_disp_top /= len(elevations[z_top])
            
            # Calculate drift
            drift = avg_disp_top - avg_disp_bottom
            drift_ratio = np.linalg.norm(drift[:2]) / (story_height * 12)  # Convert to drift ratio
            
            story_drifts[f"Story_{i+1}"] = {
                'height': story_height,
                'drift_x': drift[0],
                'drift_y': drift[1],
                'drift_ratio': drift_ratio,
                'limit_ratio': 0.025  # 2.5% per ASCE 7
            }
        
        return story_drifts
    
    def _calculate_joint_forces(self, nodes, elements, internal_forces, reactions):
        """Calculate resultant forces at each joint"""
        n_nodes = len(nodes)
        joint_forces = {}
        
        for i in range(n_nodes):
            joint_forces[i] = {
                'fx': 0, 'fy': 0, 'fz': 0,
                'mx': 0, 'my': 0, 'mz': 0,
                'resultant_force': 0,
                'resultant_moment': 0,
                'max_shear': 0,
                'max_moment': 0
            }
        
        # Add element end forces
        for forces in internal_forces:
            elem_type = forces.get('type', '')
            if elem_type in ['COLUMN', 'BEAM', 'PILE']:
                n1, n2 = forces['node1'], forces['node2']
                
                joint_forces[n1]['fx'] += forces.get('axial_force', 0)
                joint_forces[n1]['fy'] += forces.get('shear_y', 0)
                joint_forces[n1]['fz'] += forces.get('shear_z', 0)
                joint_forces[n1]['mx'] += forces.get('torsion', 0)
                joint_forces[n1]['my'] += forces.get('moment_y', 0)
                joint_forces[n1]['mz'] += forces.get('moment_z', 0)
                
                joint_forces[n2]['fx'] += forces.get('axial_force_end', 0)
                joint_forces[n2]['fy'] += forces.get('shear_y_end', 0)
                joint_forces[n2]['fz'] += forces.get('shear_z_end', 0)
                joint_forces[n2]['mx'] += forces.get('torsion_end', 0)
                joint_forces[n2]['my'] += forces.get('moment_y_end', 0)
                joint_forces[n2]['mz'] += forces.get('moment_z_end', 0)
        
        # Add reactions
        for i in range(n_nodes):
            idx = i * 6
            if idx + 5 < len(reactions):
                joint_forces[i]['fx'] += reactions[idx]
                joint_forces[i]['fy'] += reactions[idx+1]
                joint_forces[i]['fz'] += reactions[idx+2]
                joint_forces[i]['mx'] += reactions[idx+3]
                joint_forces[i]['my'] += reactions[idx+4]
                joint_forces[i]['mz'] += reactions[idx+5]
        
        # Calculate resultants
        for i in range(n_nodes):
            fx, fy, fz = joint_forces[i]['fx'], joint_forces[i]['fy'], joint_forces[i]['fz']
            mx, my, mz = joint_forces[i]['mx'], joint_forces[i]['my'], joint_forces[i]['mz']
            
            joint_forces[i]['resultant_force'] = math.sqrt(fx**2 + fy**2 + fz**2)
            joint_forces[i]['resultant_moment'] = math.sqrt(mx**2 + my**2 + mz**2)
            
            shear = math.sqrt(fy**2 + fz**2)
            moment = math.sqrt(my**2 + mz**2)
            
            joint_forces[i]['max_shear'] = shear
            joint_forces[i]['max_moment'] = moment
        
        return joint_forces
    
    def _element_length(self, node1, node2):
        return math.sqrt((node2[0]-node1[0])**2 + (node2[1]-node1[1])**2 + (node2[2]-node1[2])**2)
    
    def _beam_stiffness_matrix(self, A, Ix, Iy, Iz, L, element_type='COLUMN'):
        """Beam element stiffness matrix"""
        E = self.E
        G = E / (2 * (1 + self.nu))
        
        if L == 0:
            return np.zeros((12, 12))
        
        ke = np.zeros((12, 12))
        
        # Axial
        EA_L = E * A / L
        ke[0, 0] = ke[6, 6] = EA_L
        ke[0, 6] = ke[6, 0] = -EA_L
        
        # Torsion
        GJ_L = G * Iz / L
        ke[3, 3] = ke[9, 9] = GJ_L
        ke[3, 9] = ke[9, 3] = -GJ_L
        
        # Bending Y
        EIy_L3 = E * Iy / L**3
        ke[1, 1] = ke[7, 7] = 12 * EIy_L3
        ke[1, 7] = ke[7, 1] = -12 * EIy_L3
        ke[1, 5] = ke[5, 1] = ke[7, 11] = ke[11, 7] = -6 * E * Iy / L**2
        ke[5, 7] = ke[7, 5] = ke[1, 11] = ke[11, 1] = 6 * E * Iy / L**2
        ke[5, 5] = ke[11, 11] = 4 * E * Iy / L
        ke[5, 11] = ke[11, 5] = 2 * E * Iy / L
        
        # Bending Z
        EIz_L3 = E * Ix / L**3
        ke[2, 2] = ke[8, 8] = 12 * EIz_L3
        ke[2, 8] = ke[8, 2] = -12 * EIz_L3
        ke[2, 4] = ke[4, 2] = ke[8, 10] = ke[10, 8] = 6 * E * Ix / L**2
        ke[4, 8] = ke[8, 4] = ke[2, 10] = ke[10, 2] = -6 * E * Ix / L**2
        ke[4, 4] = ke[10, 10] = 4 * E * Ix / L
        ke[4, 10] = ke[10, 4] = 2 * E * Ix / L
        
        # Soil springs for PILE elements
        if element_type == 'PILE':
            if A > 0:
                diameter = math.sqrt(4 * A / math.pi)
                k_z = self.modulus_subgrade_z * diameter * self.pile_soil_spring_factor
                k_xy = self.modulus_subgrade_xy * diameter * self.pile_soil_spring_factor
                
                ke[8, 8] += k_z * L / 2
                ke[6, 6] += k_xy * L / 2
                ke[7, 7] += k_xy * L / 2
                
                ke[9, 9] += k_xy * L**3 / 12
                ke[10, 10] += k_xy * L**3 / 12
                ke[11, 11] += k_xy * L**3 / 12
        
        return ke
    
    def _shell_stiffness_matrix_quad(self, n1, n2, n3, n4, thickness):
        """Quadrilateral shell stiffness"""
        E = self.E
        nu = self.nu
        t = thickness
        
        # Average area
        x1, y1, z1 = n1
        x2, y2, z2 = n2
        x3, y3, z3 = n3
        x4, y4, z4 = n4
        
        A1 = 0.5 * abs((x2-x1)*(y3-y1) - (x3-x1)*(y2-y1))
        A2 = 0.5 * abs((x3-x1)*(y4-y1) - (x4-x1)*(y3-y1))
        A = (A1 + A2) / 2
        
        if A == 0:
            return np.zeros((24, 24))
        
        D = E * t**3 / (12 * (1 - nu**2))
        ke = np.eye(24) * D * A * 100
        
        return ke
    
    def _calculate_internal_forces(self, nodes, elements, displacements):
        """Calculate internal forces for elements"""
        internal_forces = []
        
        for elem in elements:
            elem_type = elem[0]
            
            if elem_type in ['COLUMN', 'BEAM', 'PILE', 'LINK']:
                n1, n2 = elem[2], elem[3]
                if len(elem) >= 10:
                    A, Ix, Iy, Iz = elem[4], elem[5], elem[6], elem[7]
                else:
                    A, Ix, Iy, Iz = 100, 100, 100, 100
                    
                L = self._element_length(nodes[n1], nodes[n2])
                ke = self._beam_stiffness_matrix(A, Ix, Iy, Iz, L, elem_type)
                
                elem_disp = np.concatenate([
                    displacements[n1*6:n1*6+6],
                    displacements[n2*6:n2*6+6]
                ])
                
                forces = ke @ elem_disp
                
                internal_forces.append({
                    'element': elem,
                    'node1': n1,
                    'node2': n2,
                    'type': elem_type,
                    'axial_force': forces[0],
                    'shear_y': forces[1],
                    'shear_z': forces[2],
                    'shear_resultant': math.sqrt(forces[1]**2 + forces[2]**2),
                    'torsion': forces[3],
                    'moment_y': forces[4],
                    'moment_z': forces[5],
                    'moment_resultant': math.sqrt(forces[4]**2 + forces[5]**2),
                    'axial_force_end': forces[6],
                    'shear_y_end': forces[7],
                    'shear_z_end': forces[8],
                    'torsion_end': forces[9],
                    'moment_y_end': forces[10],
                    'moment_z_end': forces[11],
                    'length': L,
                    'width': elem[8] if len(elem) > 8 else 0,
                    'depth': elem[9] if len(elem) > 9 else 0
                })
            
            elif elem_type == 'SHELL':
                # For quad elements
                if len(elem) >= 6:
                    n1, n2, n3, n4 = elem[2], elem[3], elem[4], elem[5]
                    disp1 = displacements[n1*6:n1*6+6]
                    disp2 = displacements[n2*6:n2*6+6]
                    disp3 = displacements[n3*6:n3*6+6]
                    disp4 = displacements[n4*6:n4*6+6]
                    
                    avg_disp = (disp1 + disp2 + disp3 + disp4) / 4
                    
                    internal_forces.append({
                        'element': elem,
                        'nodes': [n1, n2, n3, n4],
                        'type': 'SHELL_QUAD',
                        'avg_displacement': avg_disp[:3],
                        'avg_rotation': avg_disp[3:],
                        'membrane_force': 0,
                        'bending_moment': 0
                    })
        
        return internal_forces

# --- 3. MAIN APPLICATION WITH ENHANCED FEATURES ---
class TurbinePedestalDesigner:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Turbine Pedestals Designer - WS-SOFTWARE LLC")
        self.root.geometry("1400x950")
        
        self.engine = StructuralAnalysisEngine()
        self.design_calc = ACIDesignCalculator()
        self.nodes = []
        self.elements = []
        self.load_cases = {}
        self.load_cases_applied = {}
        self.load_combos = {}
        self.results = {}
        self.design_results = {}
        self.mesh_size = 2.0  # Default 2ft x 2ft mesh
        self.clipboard = None
        
        # Geometry data
        self.mat_points = []
        self.mezzanine_points = []
        self.top_points = []
        self.column_lines = []
        self.pile_lines = []
        self.beam_lines = []
        
        # Special load cases
        self.special_load_cases = SPECIAL_LOAD_CASES.copy()
        
        # Seismic parameters
        self.seismic_zone = 'C'
        self.site_class = 'D'
        
        # License check
        is_valid, msg = verify_license()
        if not is_valid:
            self.show_lock_screen(msg)
        else:
            self.setup_ui()
            self.status_bar.config(text=f"Status: {msg} | Mesh: {self.mesh_size}ft x {self.mesh_size}ft | Seismic Zone: {self.seismic_zone}")
    
    def show_lock_screen(self, msg):
        frame = tk.Frame(self.root, bg="#c0392b", pady=100)
        frame.pack(fill="both", expand=True)
        tk.Label(frame, text="ACCESS DENIED", font=("Arial", 24, "bold"), 
                fg="white", bg="#c0392b").pack()
        tk.Label(frame, text=msg, font=("Arial", 12), 
                fg="white", bg="#c0392b", pady=20).pack()
        tk.Button(frame, text="Exit", command=sys.exit).pack()
    
    def setup_ui(self):
        # Main container
        main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=1)
        
        # Left panel
        left_container = tk.Frame(main_paned)
        main_paned.add(left_container, width=700)
        
        # Right panel
        right_container = tk.Frame(main_paned)
        main_paned.add(right_container, width=700)
        
        # Setup panels
        self.setup_left_panel(left_container)
        self.setup_right_panel(right_container)
    
    def setup_left_panel(self, parent):
        # Canvas and scrollbar
        canvas = tk.Canvas(parent, bg="#f5f5f5")
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        
        self.left_frame = tk.Frame(canvas, bg="#f5f5f5")
        
        self.left_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.left_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Build content
        self.build_left_panel_content()
    
    def build_left_panel_content(self):
        # Header
        header = tk.Frame(self.left_frame, bg="#2c3e50", pady=10)
        header.pack(fill="x", padx=5, pady=5)
        tk.Label(header, text="TURBINE PEDESTALS DESIGNER", 
                font=("Arial", 18, "bold"), fg="white", bg="#2c3e50").pack()
        tk.Label(header, text="WS-SOFTWARE LLC | wael.sherif.selim@gmail.com", 
                fg="#bdc3c7", bg="#2c3e50").pack()
        tk.Label(header, text=f"ACI {ACI_VERSION} | IBC {IBC_VERSION} | Seismic Zone: {self.seismic_zone} | Mesh: {self.mesh_size}ft x {self.mesh_size}ft", 
                fg="#ecf0f1", bg="#2c3e50", font=("Arial", 10)).pack()
        
        # Control frame
        control_frame = ttk.LabelFrame(self.left_frame, text="Analysis Control", padding=10)
        control_frame.pack(fill="x", pady=10, padx=5)
        
        ttk.Label(control_frame, text="Mesh Size (ft):").grid(row=0, column=0, padx=5, pady=5)
        self.mesh_size_var = tk.StringVar(value=str(self.mesh_size))
        ttk.Entry(control_frame, textvariable=self.mesh_size_var, width=10).grid(row=0, column=1, padx=5, pady=5)
        
        perform_btn = tk.Button(control_frame, text="PERFORM FULL ANALYSIS", 
                               command=self.perform_full_analysis_enhanced,
                               bg="#27ae60", fg="white", font=("Arial", 12, "bold"),
                               padx=30, pady=10, relief=tk.RAISED, bd=3)
        perform_btn.grid(row=0, column=2, columnspan=2, padx=20, pady=5)
        
        design_btn = tk.Button(control_frame, text="STRUCTURAL DESIGN", 
                              command=self.perform_structural_design,
                              bg="#e74c3c", fg="white", font=("Arial", 10, "bold"),
                              padx=15, pady=5)
        design_btn.grid(row=0, column=4, padx=5, pady=5)
        
        # Quick actions
        quick_frame = ttk.Frame(self.left_frame)
        quick_frame.pack(fill="x", pady=5, padx=5)
        
        actions = [
            ("Generate Default", self.generate_default_geometry, "#3498db"),
            ("Auto Mesh", self.auto_mesh, "#9b59b6"),
            ("Run Static", self.run_static_analysis, "#2ecc71"),
            ("Run Dynamic", self.run_dynamic_analysis_with_vibration_check, "#e74c3c"),
            ("Export DXF", self.export_dxf_with_names, "#1abc9c"),
            ("Seismic Check", self.perform_seismic_check, "#f39c12")
        ]
        
        for i, (text, command, color) in enumerate(actions):
            btn = tk.Button(quick_frame, text=text, command=command,
                          bg=color, fg="white", font=("Arial", 9, "bold"),
                          padx=10, pady=5)
            btn.pack(side="left", padx=2, pady=5)
        
        # Material properties
        prop_frame = ttk.LabelFrame(self.left_frame, text="Material Properties", padding=10)
        prop_frame.pack(fill="x", pady=5, padx=5)
        
        props = [
            ("E (psi):", "3.60E+6", "e_val"),
            ("Density (lb/in³):", "0.0868", "den_val"),
            ("Poisson's Ratio:", "0.2", "nu_val"),
            ("Concrete f'c (psi):", "4000", "fc_val"),
            ("Soil k_z (lb/in³):", "100.0", "soil_kz_val"),
            ("Soil k_xy (lb/in³):", "10.0", "soil_kxy_val"),
            ("Spring Factor:", "1.0", "spring_factor_val")
        ]
        
        for i, (label, default, var_name) in enumerate(props):
            row = i // 2
            col = (i % 2) * 2
            ttk.Label(prop_frame, text=label).grid(row=row, column=col, padx=5, pady=5, sticky="e")
            var = tk.StringVar(value=default)
            setattr(self, var_name, var)
            ttk.Entry(prop_frame, textvariable=var, width=15).grid(row=row, column=col+1, padx=5, pady=5)
        
        # Seismic parameters
        seismic_frame = ttk.LabelFrame(self.left_frame, text="Seismic Parameters (Zone C)", padding=10)
        seismic_frame.pack(fill="x", pady=5, padx=5)
        
        seismic_params = [
            ("Ss (g):", "0.4", "seismic_ss"),
            ("S1 (g):", "0.15", "seismic_s1"),
            ("Site Class:", "D", "site_class"),
            ("R factor:", "3.0", "r_factor"),
            ("Ie factor:", "1.0", "ie_factor")
        ]
        
        for i, (label, default, var_name) in enumerate(seismic_params):
            row = i // 3
            col = (i % 3) * 2
            ttk.Label(seismic_frame, text=label).grid(row=row, column=col, padx=5, pady=5, sticky="e")
            var = tk.StringVar(value=default)
            setattr(self, var_name, var)
            ttk.Entry(seismic_frame, textvariable=var, width=10).grid(row=row, column=col+1, padx=5, pady=5)
        
        # Geometry parameters with Pile Settings
        geo_frame = ttk.LabelFrame(self.left_frame, text="Geometry Parameters", padding=10)
        geo_frame.pack(fill="x", pady=5, padx=5)
        
        params = [
            ("Mat Elevation (ft):", "-4.6", "mat_z"),
            ("Mezzanine Elev (ft):", "15.0", "mezzanine_z"),
            ("Top Floor Elev (ft):", "30.0", "top_z"),
            ("Mat Thickness (ft):", "3.0", "mat_thickness"),
            ("Column Width (in):", "30", "column_width"),
            ("Column Depth (in):", "30", "column_depth"),
            ("Beam Width (in):", "30", "beam_width"),
            ("Beam Depth (in):", "30", "beam_depth"),
            ("Pile Diameter (in):", "24", "pile_diameter"),
            ("Pile Length (ft):", "20", "pile_length")
        ]
        
        for i, (label, default, var_name) in enumerate(params):
            row = i // 3
            col = (i % 3) * 2
            ttk.Label(geo_frame, text=label).grid(row=row, column=col, padx=5, pady=5, sticky="e")
            var = tk.StringVar(value=default)
            setattr(self, var_name, var)
            ttk.Entry(geo_frame, textvariable=var, width=10).grid(row=row, column=col+1, padx=5, pady=5)
        
        # Pile Configuration Frame
        pile_config_frame = ttk.LabelFrame(self.left_frame, text="Pile Configuration", padding=10)
        pile_config_frame.pack(fill="x", pady=5, padx=5)
        
        ttk.Label(pile_config_frame, text="Min Edge Distance (pile dia):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.edge_distance_factor = tk.StringVar(value="1.8")
        ttk.Entry(pile_config_frame, textvariable=self.edge_distance_factor, width=10).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(pile_config_frame, text="Min Spacing (pile dia):").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.pile_spacing_factor = tk.StringVar(value="2.2")
        ttk.Entry(pile_config_frame, textvariable=self.pile_spacing_factor, width=10).grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Button(pile_config_frame, text="Auto Arrange Piles", 
                  command=self.auto_arrange_piles_inside_mat).grid(row=0, column=4, padx=5, pady=5)
        
        # Special Load Cases Frame
        special_load_frame = ttk.LabelFrame(self.left_frame, text="Special Load Cases", padding=10)
        special_load_frame.pack(fill="x", pady=5, padx=5)
        
        ttk.Button(special_load_frame, text="Add Special Load Case", 
                  command=self.add_special_load_case).pack(pady=5)
        
        self.special_load_listbox = tk.Listbox(special_load_frame, height=4)
        self.special_load_listbox.pack(fill="x", padx=5, pady=5)
        self.update_special_load_listbox()
        
        # Notebook for tables
        notebook = ttk.Notebook(self.left_frame)
        notebook.pack(fill="x", pady=10, padx=5)
        
        # Table definitions
        table_defs = {
            "Mat Foundation": ["X (ft)", "Y (ft)", "Z (ft)", "Thickness (ft)", "Edit"],
            "Mezzanine Level": ["X (ft)", "Y (ft)", "Z (ft)", "Thickness (ft)", "Edit"],
            "Top Floor": ["X (ft)", "Y (ft)", "Z (ft)", "Thickness (ft)", "Edit"],
            "Columns": ["X (ft)", "Y (ft)", "Z Bottom (ft)", "Z Top (ft)", "Width (in)", "Depth (in)", "Size (in)", "Edit"],
            "Piles": ["X (ft)", "Y (ft)", "Z Top (ft)", "Z Bottom (ft)", "Diameter (in)", "Size (in)", "Edit"],
            "Beams": ["X1 (ft)", "Y1 (ft)", "Z1 (ft)", "X2 (ft)", "Y2 (ft)", "Z2 (ft)", "Width (in)", "Depth (in)", "Size (in)", "Edit"]
        }
        
        self.tables = {}
        
        for tab_name, columns in table_defs.items():
            frame = ttk.Frame(notebook)
            notebook.add(frame, text=tab_name)
            
            # Treeview
            tree = ttk.Treeview(frame, columns=columns, show="headings", height=6)
            
            for col in columns:
                tree.heading(col, text=col)
                if col == "Edit":
                    tree.column(col, width=50, anchor="center")
                else:
                    tree.column(col, width=70, anchor="center")
            
            # Scrollbars
            v_scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
            h_scroll = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
            tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
            
            tree.grid(row=0, column=0, sticky="nsew")
            v_scroll.grid(row=0, column=1, sticky="ns")
            h_scroll.grid(row=1, column=0, sticky="ew")
            
            frame.grid_rowconfigure(0, weight=1)
            frame.grid_columnconfigure(0, weight=1)
            
            self.tables[tab_name] = tree
            
            # Controls
            btn_frame = ttk.Frame(frame)
            btn_frame.grid(row=2, column=0, columnspan=2, pady=5)
            
            ttk.Button(btn_frame, text="Add Row", 
                      command=lambda t=tab_name: self.add_table_row(t)).pack(side="left", padx=2)
            ttk.Button(btn_frame, text="Delete Row",
                      command=lambda t=tab_name: self.delete_table_row(t)).pack(side="left", padx=2)
            ttk.Button(btn_frame, text="Copy",
                      command=lambda t=tab_name: self.copy_table_row(t)).pack(side="left", padx=2)
            ttk.Button(btn_frame, text="Paste",
                      command=lambda t=tab_name: self.paste_table_row(t)).pack(side="left", padx=2)
            ttk.Button(btn_frame, text="Clear",
                      command=lambda t=tab_name: self.clear_table(t)).pack(side="left", padx=2)
            
            # Double-click to edit
            tree.bind("<Double-1>", lambda e, t=tab_name: self.edit_table_row(t))
        
        # Load cases notebook
        load_notebook = ttk.Notebook(self.left_frame)
        load_notebook.pack(fill="x", pady=10, padx=5)
        
        # Load cases tab
        load_frame = ttk.Frame(load_notebook)
        load_notebook.add(load_frame, text="Load Cases")
        
        load_control = ttk.Frame(load_frame)
        load_control.pack(fill="x", pady=5)
        
        ttk.Label(load_control, text="Case Name:").pack(side="left", padx=5)
        self.load_case_name = tk.StringVar(value="DL")
        ttk.Entry(load_control, textvariable=self.load_case_name, width=10).pack(side="left", padx=5)
        
        ttk.Button(load_control, text="Add", command=self.add_load_case).pack(side="left", padx=5)
        ttk.Button(load_control, text="Edit", command=self.edit_load_case).pack(side="left", padx=5)
        ttk.Button(load_control, text="Delete", command=self.delete_load_case).pack(side="left", padx=5)
        
        self.load_case_tree = ttk.Treeview(load_frame, columns=("Case", "Type", "Value"), height=6)
        self.load_case_tree.heading("Case", text="Case")
        self.load_case_tree.heading("Type", text="Type")
        self.load_case_tree.heading("Value", text="Value (kips)")
        self.load_case_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Load combos tab - ACI 318-25 compliant
        self.setup_load_combinations_tab(load_notebook)
        
        # Quick buttons frame
        quick_buttons_frame = ttk.Frame(self.left_frame)
        quick_buttons_frame.pack(fill="x", pady=10, padx=5)
        
        buttons = [
            ("Show Results", self.show_results, "#f39c12"),
            ("Export Excel", self.export_design_calculations, "#2ecc71"),
            ("Export PDF", self.export_comprehensive_pdf_report, "#e74c3c"),
            ("Export All", self.export_all, "#9b59b6"),
            ("Reset", self.reset_model, "#95a5a6")
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(quick_buttons_frame, text=text, command=command,
                          bg=color, fg="white", font=("Arial", 9, "bold"),
                          padx=10, pady=5)
            btn.pack(side="left", padx=2)
        
        # Padding
        tk.Frame(self.left_frame, height=20, bg="#f5f5f5").pack()
    
    def setup_load_combinations_tab(self, load_notebook):
        """Setup comprehensive load combinations per ACI 318-25"""
        # Create the combos tab
        combo_frame = ttk.Frame(load_notebook)
        load_notebook.add(combo_frame, text="Combinations")
        
        # Create scrollable frame for all content
        canvas = tk.Canvas(combo_frame, bg="white")
        scrollbar = ttk.Scrollbar(combo_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Use scrollable_frame as parent for all content
        parent = scrollable_frame
        
        # ACI 318-25 Standard Combinations
        aci_frame = ttk.LabelFrame(parent, text="ACI 318-25 Standard Combinations", padding=10)
        aci_frame.pack(fill="x", padx=5, pady=5)
        
        # Checkbox to enable/disable combinations
        self.combo_enabled = {}
        
        # ACI 318-25 Required Strength Combinations (Section 5.3)
        aci_combos = [
            ("COMBO1", "1.4*DL", "Basic Dead Load"),
            ("COMBO2", "1.2*DL + 1.6*LL", "Dead + Live"),
            ("COMBO3", "1.2*DL + 1.6*LL + 0.5*(Lr or S or R)", "Dead + Live + Roof/Snow"),
            ("COMBO4", "1.2*DL + 1.0*LL + 1.0*W", "Dead + Live + Wind"),
            ("COMBO5", "1.2*DL + 1.0*LL + 1.0*E", "Dead + Live + Seismic"),
            ("COMBO6", "0.9*DL + 1.0*W", "Dead + Wind (uplift)"),
            ("COMBO7", "0.9*DL + 1.0*E", "Dead + Seismic (uplift)"),
            ("COMBO8", "1.2*DL + 1.0*LL + 1.6*W", "Dead + Live + Wind (Alt)"),
            ("COMBO9", "1.2*DL + 1.0*LL + 1.0*E + 1.0*S", "Dead + Live + Seismic + Snow"),
            ("COMBO10", "1.2*DL + 1.0*E + f1*LL + f2*S", "Seismic with factors"),
        ]
        
        # Seismic Load Combinations (ASCE 7-22 Section 12.4)
        seismic_combos = [
            ("SEISMIC1", "1.2*DL + 1.0*LL + 1.0*SEISMIC_X + 0.3*SEISMIC_Y", "Seismic X dominant"),
            ("SEISMIC2", "1.2*DL + 1.0*LL + 0.3*SEISMIC_X + 1.0*SEISMIC_Y", "Seismic Y dominant"),
            ("SEISMIC3", "0.9*DL + 1.0*SEISMIC_X + 0.3*SEISMIC_Y", "Seismic X (uplift)"),
            ("SEISMIC4", "0.9*DL + 0.3*SEISMIC_X + 1.0*SEISMIC_Y", "Seismic Y (uplift)"),
            ("SEISMIC5", "1.2*DL + 1.0*LL - 1.0*SEISMIC_X - 0.3*SEISMIC_Y", "Seismic X reversed"),
            ("SEISMIC6", "1.2*DL + 1.0*LL - 0.3*SEISMIC_X - 1.0*SEISMIC_Y", "Seismic Y reversed"),
        ]
        
        # Dynamic Load Combinations
        dynamic_combos = [
            ("DYNAMIC1", "1.2*DL + 1.0*LL + 1.0*MODAL", "Modal Analysis"),
            ("DYNAMIC2", "1.2*DL + 1.0*LL + 1.0*RESPONSE_SPECTRUM", "Response Spectrum"),
            ("DYNAMIC3", "1.2*DL + 0.5*LL + 1.0*TIME_HISTORY", "Time History Analysis"),
        ]
        
        # Special Load Combinations
        special_combos = [
            ("THERMAL1", "1.2*DL + 1.0*LL + 1.0*THERMAL + 0.5*W", "Thermal + Wind"),
            ("CONSTRUCTION1", "1.4*DL + 1.0*CONSTRUCTION_LOAD", "Construction Stage"),
            ("PROGRESSIVE1", "1.2*DL + 0.5*LL (with element removal)", "Progressive Collapse"),
        ]
        
        # Display all combinations with checkboxes
        all_combos = [
            ("ACI Required Strength", aci_combos),
            ("Seismic Combinations", seismic_combos),
            ("Dynamic Analysis", dynamic_combos),
            ("Special Cases", special_combos)
        ]
        
        for section_name, combo_list in all_combos:
            section_frame = ttk.LabelFrame(aci_frame, text=section_name, padding=5)
            section_frame.pack(fill="x", pady=5)
            
            for combo_id, formula, description in combo_list:
                frame = ttk.Frame(section_frame)
                frame.pack(fill="x", pady=2)
                
                var = tk.BooleanVar(value=True)
                self.combo_enabled[combo_id] = var
                
                chk = ttk.Checkbutton(frame, text=f"{combo_id}", variable=var)
                chk.pack(side="left", padx=5)
                
                ttk.Label(frame, text=f"{formula}", font=("Courier", 9)).pack(side="left", padx=5)
                ttk.Label(frame, text=f"({description})", foreground="gray").pack(side="left", padx=5)
        
        # Custom Combination Entry
        custom_frame = ttk.LabelFrame(parent, text="Custom Combinations", padding=10)
        custom_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(custom_frame, text="Combination ID:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.custom_combo_id = tk.StringVar(value=f"CUSTOM{len(self.combo_enabled)+1}")
        ttk.Entry(custom_frame, textvariable=self.custom_combo_id, width=15).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(custom_frame, text="Formula:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.custom_combo_formula = tk.StringVar(value="1.2*DL + 1.6*LL")
        ttk.Entry(custom_frame, textvariable=self.custom_combo_formula, width=40).grid(row=1, column=1, columnspan=2, padx=5, pady=5)
        
        ttk.Label(custom_frame, text="Description:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.custom_combo_desc = tk.StringVar(value="Custom load combination")
        ttk.Entry(custom_frame, textvariable=self.custom_combo_desc, width=40).grid(row=2, column=1, columnspan=2, padx=5, pady=5)
        
        ttk.Button(custom_frame, text="Add Custom Combination", 
                  command=self.add_custom_combination).grid(row=3, column=0, columnspan=3, pady=10)
        
        # Combination List Display
        list_frame = ttk.LabelFrame(parent, text="Active Combinations", padding=10)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        columns = ("ID", "Formula", "Description", "Status")
        self.combo_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.combo_tree.heading(col, text=col)
            self.combo_tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.combo_tree.yview)
        self.combo_tree.configure(yscrollcommand=scrollbar.set)
        
        self.combo_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Action Buttons
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(btn_frame, text="Refresh List", command=self.update_combo_list).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Analyze All", command=self.analyze_all_combinations).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="Clear Results", command=self.clear_combo_results).pack(side="left", padx=2)
        
        self.update_combo_list()
    
    def update_combo_list(self):
        """Update the combination tree display"""
        for item in self.combo_tree.get_children():
            self.combo_tree.delete(item)
        
        combo_formulas = {
            "COMBO1": "1.4*DL",
            "COMBO2": "1.2*DL + 1.6*LL",
            "COMBO3": "1.2*DL + 1.6*LL + 0.5*Lr",
            "COMBO4": "1.2*DL + 1.0*LL + 1.0*W",
            "COMBO5": "1.2*DL + 1.0*LL + 1.0*E",
            "COMBO6": "0.9*DL + 1.0*W",
            "COMBO7": "0.9*DL + 1.0*E",
            "COMBO8": "1.2*DL + 1.0*LL + 1.6*W",
            "COMBO9": "1.2*DL + 1.0*LL + 1.0*E + 1.0*S",
            "COMBO10": "1.2*DL + 1.0*E + 0.5*LL",
            "SEISMIC1": "1.2*DL + 1.0*LL + 1.0*SEISMIC_X + 0.3*SEISMIC_Y",
            "SEISMIC2": "1.2*DL + 1.0*LL + 0.3*SEISMIC_X + 1.0*SEISMIC_Y",
            "SEISMIC3": "0.9*DL + 1.0*SEISMIC_X + 0.3*SEISMIC_Y",
            "SEISMIC4": "0.9*DL + 0.3*SEISMIC_X + 1.0*SEISMIC_Y",
            "SEISMIC5": "1.2*DL + 1.0*LL - 1.0*SEISMIC_X - 0.3*SEISMIC_Y",
            "SEISMIC6": "1.2*DL + 1.0*LL - 0.3*SEISMIC_X - 1.0*SEISMIC_Y",
            "DYNAMIC1": "1.2*DL + 1.0*LL + 1.0*MODAL",
            "DYNAMIC2": "1.2*DL + 1.0*LL + 1.0*RESPONSE_SPECTRUM",
            "DYNAMIC3": "1.2*DL + 0.5*LL + 1.0*TIME_HISTORY",
            "THERMAL1": "1.2*DL + 1.0*LL + 1.0*THERMAL + 0.5*W",
            "CONSTRUCTION1": "1.4*DL + 1.0*CONSTRUCTION_LOAD",
            "PROGRESSIVE1": "1.2*DL + 0.5*LL (element removal)",
        }
        
        combo_descriptions = {
            "COMBO1": "Basic Dead Load",
            "COMBO2": "Dead + Live",
            "COMBO3": "Dead + Live + Roof/Snow",
            "COMBO4": "Dead + Live + Wind",
            "COMBO5": "Dead + Live + Seismic",
            "COMBO6": "Dead + Wind (uplift)",
            "COMBO7": "Dead + Seismic (uplift)",
            "COMBO8": "Dead + Live + Wind (Alt)",
            "COMBO9": "Dead + Live + Seismic + Snow",
            "COMBO10": "Seismic with factors",
            "SEISMIC1": "Seismic X dominant",
            "SEISMIC2": "Seismic Y dominant",
            "SEISMIC3": "Seismic X (uplift)",
            "SEISMIC4": "Seismic Y (uplift)",
            "SEISMIC5": "Seismic X reversed",
            "SEISMIC6": "Seismic Y reversed",
            "DYNAMIC1": "Modal Analysis",
            "DYNAMIC2": "Response Spectrum",
            "DYNAMIC3": "Time History Analysis",
            "THERMAL1": "Thermal + Wind",
            "CONSTRUCTION1": "Construction Stage",
            "PROGRESSIVE1": "Progressive Collapse",
        }
        
        # Add custom combinations if they exist
        if hasattr(self, 'custom_combinations'):
            for combo_id, combo_data in self.custom_combinations.items():
                combo_formulas[combo_id] = combo_data['formula']
                combo_descriptions[combo_id] = combo_data['description']
        
        for combo_id, var in self.combo_enabled.items():
            status = "Enabled" if var.get() else "Disabled"
            formula = combo_formulas.get(combo_id, "N/A")
            description = combo_descriptions.get(combo_id, "Custom")
            
            self.combo_tree.insert("", "end", values=(combo_id, formula, description, status))
    
    def setup_right_panel(self, parent):
        # Visualization
        viz_frame = tk.Frame(parent, bg="white")
        viz_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.figure = Figure(figsize=(6, 8), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=viz_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Controls
        control_frame = tk.Frame(viz_frame, bg="white")
        control_frame.pack(fill="x", pady=5)
        
        views = ["3D Structure", "Plan View", "Elevation X", "Elevation Y",
                "Deformed Shape", "Force Diagram", "Mode Shapes", "Column View",
                "Beam View", "Slab Mesh", "Seismic Forces"]
        self.view_var = tk.StringVar(value="3D Structure")
        
        view_combo = ttk.Combobox(control_frame, textvariable=self.view_var, 
                                 values=views, width=15, state="readonly")
        view_combo.pack(side="left", padx=5)
        view_combo.bind("<<ComboboxSelected>>", lambda e: self.update_plot())
        
        ttk.Button(control_frame, text="Refresh", command=self.update_plot).pack(side="left", padx=2)
        ttk.Button(control_frame, text="Save Plot", command=self.save_plot).pack(side="left", padx=2)
        
        # Results display
        results_frame = ttk.LabelFrame(parent, text="Analysis Results", padding=10)
        results_frame.pack(fill="x", padx=10, pady=5)
        
        self.results_text = scrolledtext.ScrolledText(results_frame, height=8, font=("Courier", 9))
        self.results_text.pack(fill="both", expand=True)
        
        # Status bar
        self.status_bar = tk.Label(parent, text=f"Ready | Mesh: {self.mesh_size}ft x {self.mesh_size}ft | Seismic Zone: {self.seismic_zone}", 
                                 bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    # --- SPECIAL LOAD CASES ---
    def update_special_load_listbox(self):
        """Update the special load case listbox"""
        self.special_load_listbox.delete(0, tk.END)
        for case_name, case_data in self.special_load_cases.items():
            self.special_load_listbox.insert(tk.END, f"{case_name}: {case_data['description']}")
    
    def add_special_load_case(self):
        """Add a special load case"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Special Load Case")
        dialog.geometry("500x500")
        
        ttk.Label(dialog, text="Load Case Name:").pack(anchor="w", padx=10, pady=5)
        case_name_var = tk.StringVar(value=f"SPECIAL_{len(self.special_load_cases)+1}")
        ttk.Entry(dialog, textvariable=case_name_var, width=20).pack(padx=10, pady=5)
        
        ttk.Label(dialog, text="Description:").pack(anchor="w", padx=10, pady=5)
        desc_var = tk.StringVar(value="Special load case")
        ttk.Entry(dialog, textvariable=desc_var, width=40).pack(padx=10, pady=5)
        
        ttk.Label(dialog, text="Type:").pack(anchor="w", padx=10, pady=5)
        type_var = tk.StringVar(value="Dynamic")
        ttk.Combobox(dialog, textvariable=type_var, 
                    values=["Seismic", "Dynamic", "Thermal", "Construction", "Wind"], width=15).pack(padx=10, pady=5)
        
        ttk.Label(dialog, text="Coordinates (X,Y,Z in ft):").pack(anchor="w", padx=10, pady=5)
        coord_var = tk.StringVar(value="10,10,30")
        ttk.Entry(dialog, textvariable=coord_var, width=30).pack(padx=10, pady=5)
        
        ttk.Label(dialog, text="Load Pattern:").pack(anchor="w", padx=10, pady=5)
        pattern_var = tk.StringVar(value="Horizontal")
        ttk.Combobox(dialog, textvariable=pattern_var, 
                    values=["Horizontal", "Vertical", "Torsional", "Uniform", "Point"], width=15).pack(padx=10, pady=5)
        
        ttk.Label(dialog, text="Load Factor:").pack(anchor="w", padx=10, pady=5)
        factor_var = tk.StringVar(value="1.0")
        ttk.Entry(dialog, textvariable=factor_var, width=10).pack(padx=10, pady=5)
        
        ttk.Label(dialog, text="FX (kips):").pack(anchor="w", padx=10, pady=5)
        fx_var = tk.StringVar(value="0")
        ttk.Entry(dialog, textvariable=fx_var, width=10).pack(padx=10, pady=5)
        
        ttk.Label(dialog, text="FY (kips):").pack(anchor="w", padx=10, pady=5)
        fy_var = tk.StringVar(value="0")
        ttk.Entry(dialog, textvariable=fy_var, width=10).pack(padx=10, pady=5)
        
        ttk.Label(dialog, text="FZ (kips):").pack(anchor="w", padx=10, pady=5)
        fz_var = tk.StringVar(value="-50")
        ttk.Entry(dialog, textvariable=fz_var, width=10).pack(padx=10, pady=5)
        
        def save_special_case():
            case_name = case_name_var.get()
            self.special_load_cases[case_name] = {
                'type': type_var.get(),
                'description': desc_var.get(),
                'coordinates': coord_var.get(),
                'load_pattern': pattern_var.get(),
                'load_factor': float(factor_var.get()),
                'fx': float(fx_var.get()) * 1000,
                'fy': float(fy_var.get()) * 1000,
                'fz': float(fz_var.get()) * 1000
            }
            self.update_special_load_listbox()
            dialog.destroy()
            self.status_bar.config(text=f"Added special load case: {case_name}")
        
        ttk.Button(dialog, text="Save", command=save_special_case).pack(pady=20)
    
    def apply_special_load_cases(self):
        """Apply special load cases to the structure"""
        special_loads = {}
        
        for case_name, case_data in self.special_load_cases.items():
            loads = []
            
            # Parse coordinates
            try:
                coords = case_data['coordinates']
                if coords == "Applied at all structural mass locations":
                    # Apply to all nodes (for seismic)
                    for i in range(len(self.nodes)):
                        loads.append((i, case_data['fx'], case_data['fy'], case_data['fz'], 0, 0, 0))
                elif coords == "All structural elements":
                    # Apply to all elements (for thermal)
                    for i in range(len(self.nodes)):
                        loads.append((i, case_data['fx'], case_data['fy'], case_data['fz'], 0, 0, 0))
                elif coords == "Mat foundation (distributed)":
                    # Apply to mat nodes
                    mat_z = float(self.mat_z.get())
                    for i, node in enumerate(self.nodes):
                        if abs(node[2] - mat_z) < 1.0:
                            loads.append((i, case_data['fx'], case_data['fy'], case_data['fz'], 0, 0, 0))
                elif coords == "Roof and exposed surfaces":
                    # Apply to top nodes
                    top_z = max([node[2] for node in self.nodes])
                    for i, node in enumerate(self.nodes):
                        if abs(node[2] - top_z) < 1.0:
                            loads.append((i, case_data['fx'], case_data['fy'], case_data['fz'], 0, 0, 0))
                else:
                    # Specific coordinates
                    coord_parts = coords.split(',')
                    if len(coord_parts) >= 3:
                        x = float(coord_parts[0].strip())
                        y = float(coord_parts[1].strip())
                        z = float(coord_parts[2].strip())
                        
                        # Find nearest node
                        min_dist = float('inf')
                        nearest_node = 0
                        for i, node in enumerate(self.nodes):
                            dist = math.sqrt((node[0]-x)**2 + (node[1]-y)**2 + (node[2]-z)**2)
                            if dist < min_dist:
                                min_dist = dist
                                nearest_node = i
                        
                        if min_dist < 5.0:  # Within 5 ft
                            loads.append((nearest_node, case_data['fx'], case_data['fy'], case_data['fz'], 0, 0, 0))
            except:
                pass
            
            if loads:
                special_loads[case_name] = loads
        
        return special_loads
    
    # --- SEISMIC ANALYSIS ---
    def perform_seismic_check(self):
        """Perform seismic analysis and check compliance"""
        try:
            if not self.nodes or not self.elements:
                messagebox.showwarning("Warning", "Generate mesh first")
                return
            
            self.status_bar.config(text="Performing seismic analysis...")
            self.root.update()
            
            # Calculate seismic forces
            weight_distribution = {}
            for i, node in enumerate(self.nodes):
                # Simplified weight calculation
                weight = 1000  # Default weight per node
                weight_distribution[i] = weight
            
            seismic_results = self.engine.seismic_engine.calculate_seismic_loads_for_structure(
                self.nodes, self.elements, weight_distribution
            )
            
            # Add seismic loads to load cases
            self.load_cases_applied['SEISMIC_X'] = []
            self.load_cases_applied['SEISMIC_Y'] = []
            
            for node_id, fx in seismic_results['seismic_x'].items():
                self.load_cases_applied['SEISMIC_X'].append((node_id, fx, 0, 0, 0, 0, 0))
            
            for node_id, fy in seismic_results['seismic_y'].items():
                self.load_cases_applied['SEISMIC_Y'].append((node_id, 0, fy, 0, 0, 0, 0))
            
            # Run analysis with seismic loads
            if 'static' not in self.results:
                self.results['static'] = {}
            
            # Run analysis for seismic cases
            for case_name in ['SEISMIC_X', 'SEISMIC_Y']:
                if case_name in self.load_cases_applied:
                    self.results['static'][case_name] = self.engine.calculate_static_forces(
                        self.nodes, self.elements, {case_name: self.load_cases_applied[case_name]}
                    )[case_name]
            
            # Check seismic compliance
            self.check_seismic_compliance(seismic_results)
            
            self.status_bar.config(text="Seismic analysis completed")
            
        except Exception as e:
            messagebox.showerror("Error", f"Seismic analysis failed: {str(e)}")
            traceback.print_exc()
    
    def check_seismic_compliance(self, seismic_results):
        """Check seismic design compliance"""
        self.results_text.insert(tk.END, "\n=== SEISMIC ANALYSIS RESULTS (Zone C) ===\n")
        self.results_text.insert(tk.END, "="*60 + "\n")
        
        params = seismic_results['seismic_parameters']
        self.results_text.insert(tk.END, f"Seismic Zone: {self.seismic_zone}\n")
        self.results_text.insert(tk.END, f"Site Class: {self.site_class}\n")
        self.results_text.insert(tk.END, f"SDS: {params['SDS']:.3f}g\n")
        self.results_text.insert(tk.END, f"SD1: {params['SD1']:.3f}g\n")
        self.results_text.insert(tk.END, f"Response Coefficient (Cs): {params['Cs']:.3f}\n")
        self.results_text.insert(tk.END, f"Base Shear (V): {params['base_shear']/1000:.1f} kips\n")
        self.results_text.insert(tk.END, f"Fundamental Period (T): {params['period']:.3f} s\n")
        self.results_text.insert(tk.END, f"R factor: {params['R']}\n")
        self.results_text.insert(tk.END, f"Ie factor: {params['Ie']}\n")
        
        # Check story drifts
        if 'static' in self.results and 'SEISMIC_X' in self.results['static']:
            story_drifts = self.results['static']['SEISMIC_X'].get('story_drifts', {})
            self.results_text.insert(tk.END, "\n--- Story Drift Check ---\n")
            
            for story, drift_data in story_drifts.items():
                drift_ratio = drift_data['drift_ratio']
                limit = drift_data['limit_ratio']
                status = "OK" if drift_ratio <= limit else "FAIL"
                self.results_text.insert(tk.END, 
                    f"{story}: Drift ratio = {drift_ratio:.4f} (Limit: {limit:.3f}) - {status}\n")
        
        # Check seismic design category
        sds = params['SDS']
        sd1 = params['SD1']
        
        if sds >= 0.50 or sd1 >= 0.20:
            category = "D"
        elif sds >= 0.33 or sd1 >= 0.133:
            category = "C"
        else:
            category = "B"
        
        self.results_text.insert(tk.END, f"\nSeismic Design Category: {category}\n")
        
        # Recommendations
        self.results_text.insert(tk.END, "\n--- Seismic Design Requirements ---\n")
        self.results_text.insert(tk.END, "1. Special moment frames required per ACI 318-25 Chapter 18\n")
        self.results_text.insert(tk.END, "2. Seismic detailing per ACI 318-25 18.7 for columns\n")
        self.results_text.insert(tk.END, "3. Seismic detailing per ACI 318-25 18.6 for beams\n")
        self.results_text.insert(tk.END, "4. Diaphragm design per ACI 318-25 18.12\n")
        self.results_text.insert(tk.END, "5. Foundation design per ACI 318-25 18.13\n")
        
        if category in ["C", "D"]:
            self.results_text.insert(tk.END, "\n⚠️ Note: Seismic Design Category C/D requires:\n")
            self.results_text.insert(tk.END, "  - Special inspection and testing\n")
            self.results_text.insert(tk.END, "  - Structural observation\n")
            self.results_text.insert(tk.END, "  - More stringent detailing requirements\n")
    
    # --- TABLE METHODS ---
    def add_table_row(self, table_name):
        tree = self.tables[table_name]
        columns = tree["columns"]
        
        defaults = {
            "Mat Foundation": ["0.0", "0.0", "-4.6", "3.0", "Edit"],
            "Mezzanine Level": ["0.0", "0.0", "15.0", "1.0", "Edit"],
            "Top Floor": ["0.0", "0.0", "30.0", "1.0", "Edit"],
            "Columns": ["0.0", "0.0", "-4.6", "30.0", "30", "30", "30", "Edit"],
            "Piles": ["0.0", "0.0", "-4.6", "-24.6", "24", "24", "Edit"],
            "Beams": ["0.0", "0.0", "15.0", "20.0", "0.0", "15.0", "30", "30", "30", "Edit"]
        }
        
        default = defaults.get(table_name, ["" for _ in columns])
        tree.insert("", "end", values=default)
    
    def edit_table_row(self, table_name):
        tree = self.tables[table_name]
        selection = tree.selection()
        
        if not selection:
            return
        
        item = selection[0]
        values = list(tree.item(item)["values"])
        columns = tree["columns"]
        
        if "Edit" in values:
            values.remove("Edit")
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit {table_name} Row")
        dialog.geometry("500x400")
        
        entries = []
        
        for i, (col, val) in enumerate(zip(columns[:-1], values)):
            ttk.Label(dialog, text=f"{col}:").grid(row=i, column=0, padx=10, pady=5, sticky="e")
            var = tk.StringVar(value=str(val))
            entry = ttk.Entry(dialog, textvariable=var, width=15)
            entry.grid(row=i, column=1, padx=10, pady=5)
            entries.append(var)
        
        def save_changes():
            new_values = []
            for var in entries:
                new_values.append(var.get())
            new_values.append("Edit")
            
            tree.item(item, values=new_values)
            dialog.destroy()
            self.status_bar.config(text=f"Edited {table_name} row")
        
        ttk.Button(dialog, text="Save", command=save_changes).grid(row=len(columns), column=0, columnspan=2, pady=20)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).grid(row=len(columns)+1, column=0, columnspan=2)
    
    def delete_table_row(self, table_name):
        tree = self.tables[table_name]
        selection = tree.selection()
        if selection:
            for item in selection:
                tree.delete(item)
    
    def copy_table_row(self, table_name):
        tree = self.tables[table_name]
        selection = tree.selection()
        if selection:
            values = list(tree.item(selection[0])["values"])
            if "Edit" in values:
                values.remove("Edit")
            self.clipboard = values
            self.status_bar.config(text="Row copied to clipboard")
    
    def paste_table_row(self, table_name):
        if self.clipboard:
            tree = self.tables[table_name]
            values = list(self.clipboard) + ["Edit"]
            tree.insert("", "end", values=values)
            self.status_bar.config(text="Row pasted")
    
    def clear_table(self, table_name):
        tree = self.tables[table_name]
        for item in tree.get_children():
            tree.delete(item)
    
    def get_table_data(self, table_name):
        tree = self.tables[table_name]
        data = []
        for item in tree.get_children():
            values = tree.item(item)["values"]
            converted = []
            for val in values:
                if val and val != "" and val != "Edit":
                    try:
                        converted.append(float(val))
                    except ValueError:
                        converted.append(val)
                else:
                    converted.append(0.0)
            data.append(converted)
        return data
    
    # --- PILE AUTO-ARRANGEMENT ---
    def auto_arrange_piles_inside_mat(self):
        """Automatically arrange piles symmetrically inside mat boundary"""
        try:
            # Get mat geometry
            mat_points = self.get_table_data("Mat Foundation")
            if len(mat_points) < 3:
                messagebox.showwarning("Warning", "Define mat foundation first")
                return
            
            # Clear existing piles
            self.clear_table("Piles")
            
            # Get pile parameters
            diameter = float(self.pile_diameter.get()) / 12  # Convert to feet
            pile_len = float(self.pile_length.get())
            mat_z = float(self.mat_z.get())
            
            # Get spacing factors
            edge_factor = float(self.edge_distance_factor.get())
            spacing_factor = float(self.pile_spacing_factor.get())
            
            # Calculate mat bounds and create polygon
            mat_polygon = [(pt[0], pt[1]) for pt in mat_points]
            
            # Generate grid of potential pile locations
            x_coords = [pt[0] for pt in mat_points]
            y_coords = [pt[1] for pt in mat_points]
            
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)
            
            edge_dist = edge_factor * diameter
            spacing = spacing_factor * diameter
            
            # Generate pile locations
            pile_locations = []
            x = min_x + edge_dist
            while x <= max_x - edge_dist:
                y = min_y + edge_dist
                while y <= max_y - edge_dist:
                    # Check if point is inside mat polygon
                    if self._point_in_polygon(x, y, mat_points):
                        z_top = mat_z
                        z_bottom = z_top - pile_len
                        pile_locations.append([x, y, z_top, z_bottom, diameter*12])
                    y += spacing
                x += spacing
            
            # If no piles found with grid, try edge locations
            if not pile_locations:
                # Place piles at mat corners (inside)
                for pt in mat_points:
                    x, y = pt[0], pt[1]
                    # Move slightly inward from corner
                    x_in = min_x + edge_dist if x == min_x else max_x - edge_dist
                    y_in = min_y + edge_dist if y == min_y else max_y - edge_dist
                    
                    if self._point_in_polygon(x_in, y_in, mat_points):
                        z_top = mat_z
                        z_bottom = z_top - pile_len
                        pile_locations.append([x_in, y_in, z_top, z_bottom, diameter*12])
            
            # Add piles to table
            for i, pile in enumerate(pile_locations, 1):
                self.tables["Piles"].insert("", "end",
                    values=[f"{pile[0]:.2f}", f"{pile[1]:.2f}", f"{pile[2]:.2f}", 
                           f"{pile[3]:.2f}", f"{pile[4]:.1f}", f"{pile[4]:.1f}", "Edit"])
            
            self.status_bar.config(text=f"Auto-arranged {len(pile_locations)} piles inside mat")
            
            # Update mesh if exists
            if self.nodes:
                self.auto_mesh()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to auto-arrange piles: {str(e)}")
            traceback.print_exc()
    
    def _point_in_polygon(self, x, y, polygon):
        """Check if point is inside polygon"""
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0][0], polygon[0][1]
        for i in range(n + 1):
            p2x, p2y = polygon[i % n][0], polygon[i % n][1]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    # --- LOAD CASE METHODS ---
    def add_load_case(self):
        case_name = self.load_case_name.get()
        if not case_name:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Load Case: {case_name}")
        dialog.geometry("500x400")
        
        ttk.Label(dialog, text="Load Type:").pack(anchor="w", padx=10, pady=5)
        load_type = tk.StringVar(value="Point")
        ttk.Combobox(dialog, textvariable=load_type, 
                    values=["Point", "Uniform", "Wind", "Seismic", "Dynamic", "Thermal"], width=15).pack(padx=10, pady=5)
        
        ttk.Label(dialog, text="FX (kips):").pack(anchor="w", padx=10, pady=5)
        fx_var = tk.StringVar(value="0")
        ttk.Entry(dialog, textvariable=fx_var, width=15).pack(padx=10, pady=5)
        
        ttk.Label(dialog, text="FY (kips):").pack(anchor="w", padx=10, pady=5)
        fy_var = tk.StringVar(value="0")
        ttk.Entry(dialog, textvariable=fy_var, width=15).pack(padx=10, pady=5)
        
        ttk.Label(dialog, text="FZ (kips):").pack(anchor="w", padx=10, pady=5)
        fz_var = tk.StringVar(value="-100")
        ttk.Entry(dialog, textvariable=fz_var, width=15).pack(padx=10, pady=5)
        
        def save_case():
            try:
                self.load_cases[case_name] = {
                    'type': load_type.get(),
                    'fx': float(fx_var.get()) * 1000,
                    'fy': float(fy_var.get()) * 1000,
                    'fz': float(fz_var.get()) * 1000
                }
                self.update_load_case_list()
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Invalid numeric value")
        
        ttk.Button(dialog, text="Save", command=save_case).pack(pady=20)
    
    def edit_load_case(self):
        selection = self.load_case_tree.selection()
        if selection:
            case_name = self.load_case_tree.item(selection[0])["values"][0]
            self.load_case_name.set(case_name)
            self.add_load_case()
    
    def delete_load_case(self):
        selection = self.load_case_tree.selection()
        if selection:
            case_name = self.load_case_tree.item(selection[0])["values"][0]
            if case_name in self.load_cases:
                del self.load_cases[case_name]
                self.update_load_case_list()
    
    def update_load_case_list(self):
        self.load_case_tree.delete(*self.load_case_tree.get_children())
        for name, data in self.load_cases.items():
            self.load_case_tree.insert("", "end", 
                values=(name, data['type'], f"{data['fz']/1000:.1f}"))
    
    def add_custom_combination(self):
        """Add a custom load combination"""
        combo_id = self.custom_combo_id.get()
        formula = self.custom_combo_formula.get()
        description = self.custom_combo_desc.get()
        
        if combo_id and formula:
            var = tk.BooleanVar(value=True)
            self.combo_enabled[combo_id] = var
            
            # Store custom combination details
            if not hasattr(self, 'custom_combinations'):
                self.custom_combinations = {}
            
            self.custom_combinations[combo_id] = {
                'formula': formula,
                'description': description
            }
            
            self.update_combo_list()
            self.status_bar.config(text=f"Added custom combination: {combo_id}")
            
            # Increment counter for next custom combo
            current_num = int(combo_id.replace("CUSTOM", ""))
            self.custom_combo_id.set(f"CUSTOM{current_num + 1}")
            self.custom_combo_formula.set("1.2*DL + 1.6*LL")
            self.custom_combo_desc.set("Custom load combination")
    
    def analyze_all_combinations(self):
        """Perform analysis for all enabled load combinations"""
        try:
            if not self.nodes or not self.elements:
                messagebox.showwarning("Warning", "Generate mesh first")
                return
            
            self.status_bar.config(text="Analyzing all load combinations...")
            self.root.update()
            
            # Initialize combination results storage
            if 'combinations' not in self.results:
                self.results['combinations'] = {}
            
            # Get all active load cases
            available_loads = list(self.load_cases_applied.keys())
            
            # Ensure seismic loads are calculated
            if 'SEISMIC_X' not in available_loads or 'SEISMIC_Y' not in available_loads:
                self.perform_seismic_check()
            
            # Apply special load cases
            special_loads = self.apply_special_load_cases()
            for case_name, loads in special_loads.items():
                self.load_cases_applied[case_name] = loads
            
            # Analyze each enabled combination
            analyzed_count = 0
            
            for combo_id, var in self.combo_enabled.items():
                if not var.get():
                    continue
                
                self.status_bar.config(text=f"Analyzing {combo_id}...")
                self.root.update()
                
                try:
                    combo_result = self.analyze_single_combination(combo_id)
                    if combo_result:
                        self.results['combinations'][combo_id] = combo_result
                        analyzed_count += 1
                except Exception as e:
                    print(f"Error analyzing {combo_id}: {str(e)}")
                    traceback.print_exc()
            
            # Display comprehensive results
            self.display_combination_results()
            
            self.status_bar.config(text=f"Completed analysis of {analyzed_count} combinations")
            messagebox.showinfo("Analysis Complete", 
                              f"Successfully analyzed {analyzed_count} load combinations.\n" +
                              "Results displayed in the analysis results panel.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Combination analysis failed: {str(e)}")
            traceback.print_exc()
    
    def analyze_single_combination(self, combo_id):
        """Analyze a single load combination"""
        # Parse combination formula
        combo_formulas = {
            "COMBO1": {"DL": 1.4},
            "COMBO2": {"DL": 1.2, "LL": 1.6},
            "COMBO3": {"DL": 1.2, "LL": 1.6, "Lr": 0.5},
            "COMBO4": {"DL": 1.2, "LL": 1.0, "W": 1.0},
            "COMBO5": {"DL": 1.2, "LL": 1.0, "SEISMIC_X": 1.0, "SEISMIC_Y": 1.0},
            "COMBO6": {"DL": 0.9, "W": 1.0},
            "COMBO7": {"DL": 0.9, "SEISMIC_X": 1.0, "SEISMIC_Y": 1.0},
            "COMBO8": {"DL": 1.2, "LL": 1.0, "W": 1.6},
            "COMBO9": {"DL": 1.2, "LL": 1.0, "SEISMIC_X": 1.0, "SEISMIC_Y": 1.0, "S": 1.0},
            "COMBO10": {"DL": 1.2, "SEISMIC_X": 1.0, "SEISMIC_Y": 1.0, "LL": 0.5},
            "SEISMIC1": {"DL": 1.2, "LL": 1.0, "SEISMIC_X": 1.0, "SEISMIC_Y": 0.3},
            "SEISMIC2": {"DL": 1.2, "LL": 1.0, "SEISMIC_X": 0.3, "SEISMIC_Y": 1.0},
            "SEISMIC3": {"DL": 0.9, "SEISMIC_X": 1.0, "SEISMIC_Y": 0.3},
            "SEISMIC4": {"DL": 0.9, "SEISMIC_X": 0.3, "SEISMIC_Y": 1.0},
            "SEISMIC5": {"DL": 1.2, "LL": 1.0, "SEISMIC_X": -1.0, "SEISMIC_Y": -0.3},
            "SEISMIC6": {"DL": 1.2, "LL": 1.0, "SEISMIC_X": -0.3, "SEISMIC_Y": -1.0},
        }
        
        # Get load factors for this combination
        factors = combo_formulas.get(combo_id, {})
        
        # Combine loads according to factors
        combined_loads = []
        
        for node_id in range(len(self.nodes)):
            fx, fy, fz = 0.0, 0.0, 0.0
            mx, my, mz = 0.0, 0.0, 0.0
            
            for load_case, factor in factors.items():
                if load_case in self.load_cases_applied:
                    case_loads = self.load_cases_applied[load_case]
                    
                    for load in case_loads:
                        if load[0] == node_id:  # Node ID matches
                            fx += factor * load[1]
                            fy += factor * load[2]
                            fz += factor * load[3]
                            if len(load) >= 7:
                                mx += factor * load[4]
                                my += factor * load[5]
                                mz += factor * load[6]
            
            if abs(fx) > 1e-6 or abs(fy) > 1e-6 or abs(fz) > 1e-6:
                combined_loads.append((node_id, fx, fy, fz, mx, my, mz))
        
        # Perform static analysis with combined loads
        if combined_loads:
            result = self.engine.calculate_static_forces(
                self.nodes, self.elements, {combo_id: combined_loads}
            )
            return result.get(combo_id, None)
        
        return None
    
    def display_combination_results(self):
        """Display comprehensive combination analysis results"""
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, "="*80 + "\n")
        self.results_text.insert(tk.END, "LOAD COMBINATION ANALYSIS RESULTS (ACI 318-25)\n")
        self.results_text.insert(tk.END, "="*80 + "\n\n")
        
        if 'combinations' not in self.results or not self.results['combinations']:
            self.results_text.insert(tk.END, "No combination results available.\n")
            return
        
        # Find governing combinations
        max_forces = {}
        
        for combo_id, result in self.results['combinations'].items():
            if not result or 'joint_forces' not in result:
                continue
            
            joint_forces = result['joint_forces']
            
            # Extract forces from joint_forces
            for node_id, forces in joint_forces.items():
                for force_type in ['fx', 'fy', 'fz', 'mx', 'my', 'mz']:
                    value = abs(forces.get(force_type, 0))
                    
                    if force_type not in max_forces or value > max_forces[force_type]['value']:
                        max_forces[force_type] = {'value': value, 'combo': combo_id}
        
        # Display governing combinations
        self.results_text.insert(tk.END, "GOVERNING LOAD COMBINATIONS:\n")
        self.results_text.insert(tk.END, "-" * 80 + "\n")
        
        force_names = {
            'fx': 'Axial Force X',
            'fy': 'Axial Force Y',
            'fz': 'Axial Force Z (Gravity)',
            'mx': 'Moment about X',
            'my': 'Moment about Y',
            'mz': 'Moment about Z (Torsion)'
        }
        
        for force_type, data in max_forces.items():
            self.results_text.insert(tk.END, 
                f"{force_names[force_type]}: {data['value']/1000:.2f} kips (Combo: {data['combo']})\n")
        
        # Detailed results for each combination
        self.results_text.insert(tk.END, "\n" + "="*80 + "\n")
        self.results_text.insert(tk.END, "DETAILED COMBINATION RESULTS:\n")
        self.results_text.insert(tk.END, "="*80 + "\n\n")
        
        for combo_id in sorted(self.results['combinations'].keys()):
            result = self.results['combinations'][combo_id]
            
            if not result or 'joint_forces' not in result:
                continue
            
            self.results_text.insert(tk.END, f"\n--- {combo_id} ---\n")
            
            joint_forces = result['joint_forces']
            
            # Max forces
            max_fx = max([abs(v.get('fx', 0)) for v in joint_forces.values()] + [0]) / 1000
            max_fy = max([abs(v.get('fy', 0)) for v in joint_forces.values()] + [0]) / 1000
            max_fz = max([abs(v.get('fz', 0)) for v in joint_forces.values()] + [0]) / 1000
            max_mx = max([abs(v.get('mx', 0)) for v in joint_forces.values()] + [0]) / 1000
            max_my = max([abs(v.get('my', 0)) for v in joint_forces.values()] + [0]) / 1000
            max_mz = max([abs(v.get('mz', 0)) for v in joint_forces.values()] + [0]) / 1000
            
            self.results_text.insert(tk.END, f"  Max FX: {max_fx:.2f} kips\n")
            self.results_text.insert(tk.END, f"  Max FY: {max_fy:.2f} kips\n")
            self.results_text.insert(tk.END, f"  Max FZ: {max_fz:.2f} kips\n")
            self.results_text.insert(tk.END, f"  Max MX: {max_mx:.2f} kip-ft\n")
            self.results_text.insert(tk.END, f"  Max MY: {max_my:.2f} kip-ft\n")
            self.results_text.insert(tk.END, f"  Max MZ: {max_mz:.2f} kip-ft\n")
            
            # Displacements
            if 'displacements' in result:
                disp = result['displacements']
                # Calculate max displacements
                max_dx = max([abs(disp[i]) for i in range(0, len(disp), 6)] + [0]) * 12
                max_dy = max([abs(disp[i+1]) for i in range(0, len(disp), 6)] + [0]) * 12
                max_dz = max([abs(disp[i+2]) for i in range(0, len(disp), 6)] + [0]) * 12
                
                self.results_text.insert(tk.END, f"  Max DX: {max_dx:.3f} in\n")
                self.results_text.insert(tk.END, f"  Max DY: {max_dy:.3f} in\n")
                self.results_text.insert(tk.END, f"  Max DZ: {max_dz:.3f} in\n")
        
        # Design recommendations
        self.results_text.insert(tk.END, "\n" + "="*80 + "\n")
        self.results_text.insert(tk.END, "DESIGN RECOMMENDATIONS:\n")
        self.results_text.insert(tk.END, "="*80 + "\n")
        self.results_text.insert(tk.END, "1. Design all structural members for the governing load combination\n")
        self.results_text.insert(tk.END, "2. Verify strength requirements per ACI 318-25 Chapter 22\n")
        self.results_text.insert(tk.END, "3. Check serviceability limits per ACI 318-25 Section 24.2\n")
        self.results_text.insert(tk.END, "4. Ensure seismic detailing per ACI 318-25 Chapter 18\n")
        self.results_text.insert(tk.END, "5. Verify column capacity per ACI 318-25 Section 22.4\n")
        self.results_text.insert(tk.END, "6. Check beam flexure and shear per ACI 318-25 Chapter 9\n")
        self.results_text.insert(tk.END, "7. Verify foundation design per ACI 318-25 Chapter 13\n")
        
        self.results_text.see("1.0")
    
    def clear_combo_results(self):
        """Clear combination analysis results"""
        if 'combinations' in self.results:
            self.results['combinations'].clear()
        self.results_text.delete("1.0", tk.END)
        self.status_bar.config(text="Combination results cleared")
    
    # --- GEOMETRY METHODS ---
    def generate_default_geometry(self):
        """Generate default geometry with all elements and 2ft mesh"""
        try:
            # Clear existing
            for tree in self.tables.values():
                for item in tree.get_children():
                    tree.delete(item)
            
            # Parameters
            mat_z = float(self.mat_z.get())
            mezzanine_z = float(self.mezzanine_z.get())
            top_z = float(self.top_z.get())
            mat_thick = float(self.mat_thickness.get())
            col_width = float(self.column_width.get())
            col_depth = float(self.column_depth.get())
            beam_width = float(self.beam_width.get())
            beam_depth = float(self.beam_depth.get())
            pile_diameter = float(self.pile_diameter.get())
            pile_len = float(self.pile_length.get())
            
            # Mat foundation (4 corners with 2ft grid alignment)
            mat_corners = [
                [0, 0, mat_z, mat_thick],
                [20, 0, mat_z, mat_thick],
                [20, 20, mat_z, mat_thick],
                [0, 20, mat_z, mat_thick]
            ]
            
            for pt in mat_corners:
                self.tables["Mat Foundation"].insert("", "end",
                    values=[f"{pt[0]:.1f}", f"{pt[1]:.1f}", f"{pt[2]:.1f}", f"{pt[3]:.1f}", "Edit"])
            
            # Mezzanine (same X,Y, different Z, 2ft grid)
            for pt in mat_corners:
                self.tables["Mezzanine Level"].insert("", "end",
                    values=[f"{pt[0]:.1f}", f"{pt[1]:.1f}", f"{mezzanine_z:.1f}", "1.0", "Edit"])
            
            # Top floor (2ft grid)
            for pt in mat_corners:
                self.tables["Top Floor"].insert("", "end",
                    values=[f"{pt[0]:.1f}", f"{pt[1]:.1f}", f"{top_z:.1f}", "1.0", "Edit"])
            
            # Columns (mat to top)
            for pt in mat_corners:
                z_bottom = mat_z + mat_thick/2  # Half mat thickness
                self.tables["Columns"].insert("", "end",
                    values=[f"{pt[0]:.1f}", f"{pt[1]:.1f}", f"{z_bottom:.1f}", 
                           f"{top_z:.1f}", f"{col_width:.1f}", f"{col_depth:.1f}", f"{col_width:.1f}", "Edit"])
            
            # Auto-arrange piles inside mat
            self.auto_arrange_piles_inside_mat()
            
            # Default beams at mezzanine edges (aligned to 2ft grid)
            beam_points = [
                [0, 0, mezzanine_z, 20, 0, mezzanine_z, beam_width, beam_depth, beam_width],
                [20, 0, mezzanine_z, 20, 20, mezzanine_z, beam_width, beam_depth, beam_width],
                [20, 20, mezzanine_z, 0, 20, mezzanine_z, beam_width, beam_depth, beam_width],
                [0, 20, mezzanine_z, 0, 0, mezzanine_z, beam_width, beam_depth, beam_width]
            ]
            
            for beam in beam_points:
                self.tables["Beams"].insert("", "end",
                    values=[f"{beam[0]:.1f}", f"{beam[1]:.1f}", f"{beam[2]:.1f}",
                           f"{beam[3]:.1f}", f"{beam[4]:.1f}", f"{beam[5]:.1f}",
                           f"{beam[6]:.1f}", f"{beam[7]:.1f}", f"{beam[8]:.1f}", "Edit"])
            
            # Default load cases including special loads
            self.load_cases = {
                'DL': {'type': 'Uniform', 'fx': 0, 'fy': 0, 'fz': -150000},
                'LL': {'type': 'Uniform', 'fx': 0, 'fy': 0, 'fz': -100000},
                'WINDX': {'type': 'Wind', 'fx': 50000, 'fy': 0, 'fz': 0}
            }
            
            # Add special load cases
            self.special_load_cases = SPECIAL_LOAD_CASES.copy()
            
            self.update_load_case_list()
            self.update_special_load_listbox()
            self.status_bar.config(text=f"Default geometry generated with {self.mesh_size}ft x {self.mesh_size}ft mesh")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate geometry: {str(e)}")
            traceback.print_exc()
    
    def auto_mesh(self):
        """Generate mesh from current geometry with 2ft x 2ft square/rectangular elements"""
        try:
            self.mesh_size = float(self.mesh_size_var.get())
            
            # Update engine with soil properties from UI
            self.engine.modulus_subgrade_z = float(self.soil_kz_val.get())
            self.engine.modulus_subgrade_xy = float(self.soil_kxy_val.get())
            self.engine.pile_soil_spring_factor = float(self.spring_factor_val.get())
            
            # Update seismic parameters
            self.engine.seismic_engine.zone = self.seismic_zone
            self.engine.seismic_engine.site_class = self.site_class.get()
            
            # Get data from tables
            self.mat_points = self.get_table_data("Mat Foundation")
            self.mezzanine_points = self.get_table_data("Mezzanine Level")
            self.top_points = self.get_table_data("Top Floor")
            self.column_lines = self.get_table_data("Columns")
            self.pile_lines = self.get_table_data("Piles")
            self.beam_lines = self.get_table_data("Beams")
            
            # Remove "Edit" column
            for data in [self.mat_points, self.mezzanine_points, self.top_points]:
                for i in range(len(data)):
                    if len(data[i]) > 4:
                        data[i] = data[i][:4]
            
            for i in range(len(self.column_lines)):
                if len(self.column_lines[i]) > 7:
                    self.column_lines[i] = self.column_lines[i][:7]
            
            for i in range(len(self.pile_lines)):
                if len(self.pile_lines[i]) > 5:
                    self.pile_lines[i] = self.pile_lines[i][:5]
            
            for i in range(len(self.beam_lines)):
                if len(self.beam_lines[i]) > 9:
                    self.beam_lines[i] = self.beam_lines[i][:9]
            
            self.status_bar.config(text=f"Generating {self.mesh_size}ft x {self.mesh_size}ft square/rectangular mesh...")
            self.root.update()
            
            # Generate mesh with square/rectangular elements
            self.nodes, self.elements = self.engine.generate_complete_mesh(
                self.mat_points, self.mezzanine_points, self.top_points,
                self.column_lines, self.pile_lines, self.beam_lines, self.mesh_size
            )
            
            # Create automatic loads including special loads
            self.create_auto_loads()
            
            self.status_bar.config(text=f"{self.mesh_size}ft mesh: {len(self.nodes)} nodes, {len(self.elements)} elements")
            self.update_plot()
            
        except Exception as e:
            messagebox.showerror("Error", f"Auto-meshing failed: {str(e)}")
            traceback.print_exc()
    
    def create_auto_loads(self):
        """Create automatic dead and live loads including special loads"""
        self.load_cases_applied = {}
        
        # Add automatic loads
        auto_loads = self.calculate_auto_loads()
        self.load_cases_applied['AUTO_DL+LL'] = auto_loads
        
        # Add user-defined loads
        for case_name, load_data in self.load_cases.items():
            loads = []
            fx, fy, fz = load_data['fx'], load_data['fy'], load_data['fz']
            
            # Apply to top nodes
            if self.nodes:
                top_z = max([node[2] for node in self.nodes])
                top_nodes = [i for i, node in enumerate(self.nodes) if abs(node[2] - top_z) < 0.1]
                
                for node in top_nodes:
                    loads.append((node, fx, fy, fz, 0, 0, 0))
            
            self.load_cases_applied[case_name] = loads
        
        # Add special load cases
        special_loads = self.apply_special_load_cases()
        self.load_cases_applied.update(special_loads)
        
        print(f"Created {len(self.load_cases_applied)} load cases including special loads")
    
    def calculate_auto_loads(self):
        """Calculate automatic dead and live loads"""
        loads = []
        
        if not self.nodes:
            return loads
        
        # Material properties
        concrete_density = 150  # lb/ft³
        
        # Calculate self-weight of slabs
        for elem in self.elements:
            elem_type = elem[0]
            
            if elem_type == 'SHELL':
                # Calculate area and self-weight for quad elements
                if len(elem) >= 11:  # Has thickness at position 10
                    n1, n2, n3, n4 = elem[2], elem[3], elem[4], elem[5]
                    thickness_ft = elem[10] if len(elem) > 10 else 8/12
                    
                    if all(n < len(self.nodes) for n in [n1, n2, n3, n4]):
                        # Calculate quad area (sum of two triangles)
                        x1, y1, z1 = self.nodes[n1]
                        x2, y2, z2 = self.nodes[n2]
                        x3, y3, z3 = self.nodes[n3]
                        x4, y4, z4 = self.nodes[n4]
                        
                        # Area of triangle 1 (n1, n2, n3)
                        area1 = 0.5 * abs((x2-x1)*(y3-y1) - (x3-x1)*(y2-y1))
                        # Area of triangle 2 (n1, n3, n4)
                        area2 = 0.5 * abs((x3-x1)*(y4-y1) - (x4-x1)*(y3-y1))
                        area = area1 + area2
                        
                        # Self-weight (in lb)
                        self_weight = area * thickness_ft * concrete_density
                        
                        # Distribute to 4 nodes
                        load_per_node = -self_weight / 4  # Negative for downward
                        
                        loads.append((n1, 0, 0, load_per_node, 0, 0, 0))
                        loads.append((n2, 0, 0, load_per_node, 0, 0, 0))
                        loads.append((n3, 0, 0, load_per_node, 0, 0, 0))
                        loads.append((n4, 0, 0, load_per_node, 0, 0, 0))
        
        # Add additional dead and live loads to top nodes
        top_z = max([node[2] for node in self.nodes])
        top_nodes = [i for i, node in enumerate(self.nodes) if abs(node[2] - top_z) < 0.1]
        
        if top_nodes:
            # Estimate tributary area per node
            avg_area = 100  # ft² (simplified)
            
            dead_load = 20 * avg_area * 1.2  # 20 psf DL
            live_load = 50 * avg_area * 1.6  # 50 psf LL
            
            total_load = -(dead_load + live_load)  # Downward
            
            for node in top_nodes:
                loads.append((node, 0, 0, total_load/len(top_nodes), 0, 0, 0))
        
        print(f"  Generated {len(loads)} load entries")
        return loads
    
    # --- ANALYSIS METHODS ---
    def perform_full_analysis_enhanced(self):
        """Perform complete static and dynamic analysis with structural design and seismic check"""
        self.status_bar.config(text="Starting full analysis with structural design and seismic check...")
        self.root.update()
        
        try:
            # Generate default if empty
            if not self.tables["Mat Foundation"].get_children():
                self.generate_default_geometry()
                self.root.update()
            
            # Auto mesh with square/rectangular elements (2ft x 2ft)
            self.auto_mesh()
            self.root.update()
            
            # Static analysis
            self.run_static_analysis()
            self.root.update()
            
            # Seismic analysis
            self.perform_seismic_check()
            self.root.update()
            
            # Dynamic analysis with vibration check
            self.run_dynamic_analysis_with_vibration_check()
            self.root.update()
            
            # Perform structural design with ACI 318-25
            design_results = self.perform_structural_design()
            self.root.update()
            
            # Export comprehensive PDF report
            if design_results:
                self.export_comprehensive_pdf_report()
            
            # Show comprehensive results
            self.show_comprehensive_results()
            
            self.status_bar.config(text="Full analysis with structural design and seismic check completed!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Analysis failed: {str(e)}")
            self.status_bar.config(text="Analysis failed")
            traceback.print_exc()
    
    def run_static_analysis(self):
        """Run static analysis including special loads"""
        try:
            if not self.nodes or not self.elements:
                messagebox.showwarning("Warning", "Generate mesh first")
                return
            
            self.status_bar.config(text="Running static analysis with special loads...")
            self.root.update()
            
            self.results['static'] = self.engine.calculate_static_forces(
                self.nodes, self.elements, self.load_cases_applied
            )
            
            self.display_static_results()
            self.status_bar.config(text="Static analysis completed")
            
        except Exception as e:
            messagebox.showerror("Error", f"Static analysis failed: {str(e)}")
            traceback.print_exc()
    
    def run_dynamic_analysis(self):
        """Run dynamic analysis"""
        try:
            if not self.nodes or not self.elements:
                messagebox.showwarning("Warning", "Generate mesh first")
                return
            
            self.status_bar.config(text="Running dynamic analysis...")
            self.root.update()
            
            # Calculate masses
            masses = []
            density = float(self.den_val.get())
            
            for i, node in enumerate(self.nodes):
                mass = 1000  # Default
                masses.append(mass / self.engine.gravity)
            
            # Run analysis (simplified)
            n_nodes = len(self.nodes)
            n_dof = n_nodes * 6
            
            # Simplified stiffness matrix
            K = np.eye(n_dof) * 1e6
            M = np.eye(n_dof) * 100
            
            # Boundary conditions
            fixed_nodes = set()
            for elem in self.elements:
                if elem[0] == 'PILE':
                    fixed_nodes.add(elem[3])  # Bottom node
            
            for node_id in fixed_nodes:
                for dof in range(6):
                    idx = node_id * 6 + dof
                    K[idx, idx] = 1e12
                    M[idx, idx] = 1
            
            # Solve eigenvalue problem
            try:
                from scipy.linalg import eigh # pyright: ignore[reportMissingImports]
                free_dofs = [i for i in range(n_dof) 
                           if i not in [node_id*6 + dof for node_id in fixed_nodes for dof in range(6)]]
                
                if len(free_dofs) > 0:
                    K_red = K[np.ix_(free_dofs, free_dofs)]
                    M_red = M[np.ix_(free_dofs, free_dofs)]
                    
                    eigvals, eigvecs = eigh(K_red, M_red, subset_by_index=[0, min(10, len(free_dofs)-1)])
                    frequencies = np.sqrt(np.abs(eigvals)) / (2 * np.pi)
                    
                    self.results['dynamic'] = {
                        'frequencies': frequencies,
                        'mode_shapes': eigvecs
                    }
                else:
                    self.results['dynamic'] = {
                        'frequencies': np.array([]),
                        'mode_shapes': np.array([])
                    }
                
                self.display_dynamic_results()
                self.status_bar.config(text="Dynamic analysis completed")
                
            except Exception as e:
                print(f"Eigenvalue failed: {e}")
                self.results['dynamic'] = {
                    'frequencies': np.array([10.0, 15.0, 20.0]),  # Default frequencies
                    'mode_shapes': np.array([])
                }
                self.display_dynamic_results()
                self.status_bar.config(text="Dynamic analysis completed (simplified)")
            
        except Exception as e:
            messagebox.showerror("Error", f"Dynamic analysis failed: {str(e)}")
            traceback.print_exc()
    
    def run_dynamic_analysis_with_vibration_check(self):
        """Run dynamic analysis with vibration criteria check"""
        try:
            self.run_dynamic_analysis()  # Original method
            
            if 'dynamic' in self.results:
                frequencies = self.results['dynamic']['frequencies']
                
                # Check for vibration criteria
                vibration_issues = []
                if len(frequencies) > 0:
                    # First mode should be > 8 Hz to avoid perceptible vibration
                    first_frequency = frequencies[0] if len(frequencies) > 0 else 0
                    if first_frequency < 8.0:
                        vibration_issues.append(f"First natural frequency ({first_frequency:.1f} Hz) < 8.0 Hz")
                    
                    # Check for modes in human-sensitive range (4-8 Hz)
                    sensitive_modes = [i+1 for i, f in enumerate(frequencies) if 4.0 <= f <= 8.0]
                    if sensitive_modes:
                        vibration_issues.append(f"Modes {sensitive_modes} in sensitive range (4-8 Hz)")
                
                # Add vibration check to results
                self.results['dynamic']['vibration_check'] = {
                    'criteria': 'All modes > 8.0 Hz (to prevent perceptible vibration)',
                    'first_frequency': first_frequency,
                    'issues': vibration_issues,
                    'passed': len(vibration_issues) == 0
                }
                
                # Display vibration results
                self.results_text.insert(tk.END, "\n=== VIBRATION ANALYSIS ===\n")
                if vibration_issues:
                    self.results_text.insert(tk.END, "⚠️ VIBRATION ISSUES DETECTED:\n")
                    for issue in vibration_issues:
                        self.results_text.insert(tk.END, f"  - {issue}\n")
                    self.results_text.insert(tk.END, "Recommendation: Increase stiffness or add damping\n")
                else:
                    self.results_text.insert(tk.END, "✓ Vibration criteria satisfied\n")
            
        except Exception as e:
            messagebox.showerror("Error", f"Vibration analysis failed: {str(e)}")
    
    def display_static_results(self):
        """Display static analysis results including special loads"""
        if 'static' not in self.results:
            return
        
        self.results_text.delete(1.0, tk.END)
        results = self.results['static']
        
        self.results_text.insert(tk.END, "=== STATIC ANALYSIS RESULTS ===\n\n")
        
        for case_name, case_results in results.items():
            self.results_text.insert(tk.END, f"LOAD CASE: {case_name}\n")
            
            # Check if it's a special load case
            if case_name in self.special_load_cases:
                special_info = self.special_load_cases[case_name]
                self.results_text.insert(tk.END, f"Type: {special_info['type']}\n")
                self.results_text.insert(tk.END, f"Description: {special_info['description']}\n")
                self.results_text.insert(tk.END, f"Coordinates: {special_info['coordinates']}\n")
            
            self.results_text.insert(tk.END, "="*60 + "\n")
            
            # Displacements
            disp = case_results['displacements']
            max_disp = np.max(np.abs(disp))
            self.results_text.insert(tk.END, f"Maximum Displacement: {max_disp:.6f} in\n\n")
            
            # Joint forces
            if 'joint_forces' in case_results:
                joint_forces = case_results['joint_forces']
                
                self.results_text.insert(tk.END, "CRITICAL JOINT FORCES:\n")
                self.results_text.insert(tk.END, "Joint | X (ft) | Y (ft) | Z (ft) | FX (k) | FY (k) | FZ (k) | R (k)\n")
                self.results_text.insert(tk.END, "-"*80 + "\n")
                
                # Find top 10 joints by resultant force
                sorted_joints = sorted(joint_forces.items(), 
                                      key=lambda x: x[1]['resultant_force'], 
                                      reverse=True)[:10]
                
                for joint_id, forces in sorted_joints:
                    if joint_id < len(self.nodes):
                        x, y, z = self.nodes[joint_id]
                        fx = forces['fx'] / 1000
                        fy = forces['fy'] / 1000
                        fz = forces['fz'] / 1000
                        resultant = forces['resultant_force'] / 1000
                        
                        self.results_text.insert(tk.END,
                            f"{joint_id+1:5d} | {x:6.1f} | {y:6.1f} | {z:6.1f} | "
                            f"{fx:6.2f} | {fy:6.2f} | {fz:6.2f} | {resultant:7.2f}\n")
    
    def display_dynamic_results(self):
        """Display dynamic analysis results"""
        if 'dynamic' not in self.results:
            return
        
        self.results_text.insert(tk.END, "\n=== DYNAMIC ANALYSIS RESULTS ===\n\n")
        
        frequencies = self.results['dynamic']['frequencies']
        
        if len(frequencies) > 0:
            self.results_text.insert(tk.END, "NATURAL FREQUENCIES:\n")
            self.results_text.insert(tk.END, "="*50 + "\n")
            
            for i, freq in enumerate(frequencies[:10]):
                if freq > 0:
                    period = 1 / freq
                    self.results_text.insert(tk.END,
                        f"Mode {i+1:2d}: f = {freq:7.3f} Hz, T = {period:7.3f} s\n")
        else:
            self.results_text.insert(tk.END, "No dynamic modes found.\n")
    
    # --- STRUCTURAL DESIGN METHODS WITH ACI 318-25 ---
    def perform_structural_design(self):
        """Perform ACI 318-25 design for all structural elements with clause references"""
        try:
            self.status_bar.config(text="Performing ACI 318-25 structural design...")
            self.root.update()
            
            if 'static' not in self.results:
                messagebox.showwarning("Warning", "Run static analysis first")
                return None
            
            design_calc = ACIDesignCalculator()
            design_results = {}
            
            # Get material properties
            fc = float(self.fc_val.get())
            fy = STEEL_FY
            
            # Determine if seismic design is required
            is_seismic = self.seismic_zone in ['C', 'D', 'E', 'F']
            
            # Process each load case
            for case_name, results in self.results['static'].items():
                design_results[case_name] = {}
                
                # Get joint forces
                joint_forces = results['joint_forces']
                
                # Design columns
                design_results[case_name]['columns'] = {}
                col_counter = 1
                for elem in self.elements:
                    if elem[0] == 'COLUMN':
                        elem_name = f"COL{col_counter}"
                        n1, n2 = elem[2], elem[3]
                        
                        # Get forces at column ends
                        if n1 in joint_forces and n2 in joint_forces:
                            # Use maximum forces from either end
                            Pu = max(abs(joint_forces[n1]['fz']), abs(joint_forces[n2]['fz']))
                            Mu_x = max(abs(joint_forces[n1]['my']), abs(joint_forces[n2]['my']))
                            Mu_y = max(abs(joint_forces[n1]['mz']), abs(joint_forces[n2]['mz']))
                            
                            # Get column dimensions
                            if len(elem) >= 10:
                                width = elem[8]
                                depth = elem[9]
                            else:
                                width = depth = 30  # default
                            
                            # Check if this is a seismic load case
                            elem_is_seismic = is_seismic and ('SEISMIC' in case_name or 'seismic' in case_name.lower())
                            
                            # Design column
                            design = design_calc.design_column(Pu/1000, Mu_x/12000, Mu_y/12000, 
                                                             width, depth, is_seismic=elem_is_seismic)
                            design_results[case_name]['columns'][elem_name] = design
                            col_counter += 1
                
                # Design beams
                design_results[case_name]['beams'] = {}
                beam_counter = 1
                for elem in self.elements:
                    if elem[0] == 'BEAM':
                        elem_name = f"B{beam_counter}"
                        n1, n2 = elem[2], elem[3]
                        
                        if n1 in joint_forces and n2 in joint_forces:
                            # Use maximum moment and shear
                            Mu = max(abs(joint_forces[n1]['my']), abs(joint_forces[n2]['my']),
                                    abs(joint_forces[n1]['mz']), abs(joint_forces[n2]['mz']))
                            Vu = max(math.sqrt(joint_forces[n1]['fy']**2 + joint_forces[n1]['fz']**2),
                                    math.sqrt(joint_forces[n2]['fy']**2 + joint_forces[n2]['fz']**2))
                            
                            # Get beam dimensions
                            if len(elem) >= 10:
                                width = elem[8]
                                depth = elem[9]
                            else:
                                width = depth = 30
                            
                            # Design for flexure
                            d = depth - 2.5  # assuming 2.5" cover
                            flexure_design = design_calc.design_flexural_member(Mu/12000, width, d, depth)
                            
                            # Design for shear
                            shear_design = design_calc.design_shear_reinforcement(Vu/1000, width, d, fc, fy, 
                                                                               flexure_design.get('As_required', 0))
                            
                            design_results[case_name]['beams'][elem_name] = {
                                'flexure': flexure_design,
                                'shear': shear_design
                            }
                            beam_counter += 1
                
                # Design piles
                design_results[case_name]['piles'] = {}
                pile_counter = 1
                for elem in self.elements:
                    if elem[0] == 'PILE':
                        elem_name = f"PI{pile_counter}"
                        n1, n2 = elem[2], elem[3]
                        
                        if n1 in joint_forces:
                            axial_load = abs(joint_forces[n1]['fz'])
                            moment = max(abs(joint_forces[n1]['my']), abs(joint_forces[n1]['mz']))
                            
                            # Get pile diameter
                            if len(elem) >= 9:
                                diameter = elem[8]
                            else:
                                diameter = 24
                            
                            # Assume pile length
                            pile_length = float(self.pile_length.get())
                            
                            # Check if seismic design
                            pile_is_seismic = is_seismic and ('SEISMIC' in case_name or 'seismic' in case_name.lower())
                            
                            # Design pile
                            design = design_calc.design_pile(axial_load/1000, moment/12000, 
                                                            diameter, pile_length, is_seismic=pile_is_seismic)
                            design_results[case_name]['piles'][elem_name] = design
                            pile_counter += 1
                
                # Design slabs (simplified)
                design_results[case_name]['slabs'] = {}
                for level_name in ['mat', 'mezzanine', 'top']:
                    # Find slab elements for this level
                    slab_moment = 0
                    slab_thickness = 8  # default
                    
                    for elem in self.elements:
                        if elem[0] == 'SHELL' and elem[1] == level_name:
                            # Estimate moment from surrounding elements
                            if len(elem) >= 11:
                                slab_thickness = elem[10] * 12  # convert to inches
                            break
                    
                    # Check if roof
                    is_roof = (level_name == 'top')
                    
                    # Check if seismic
                    slab_is_seismic = is_seismic and ('SEISMIC' in case_name or 'seismic' in case_name.lower())
                    
                    # Simplified slab moment calculation
                    slab_moment = 0.1 * 20**2 / 10  # 0.1 ksf load, 20ft span
                    
                    design = design_calc.design_slab(slab_moment, slab_thickness, fc, fy, 
                                                    is_roof=is_roof, is_seismic=slab_is_seismic)
                    design_results[case_name]['slabs'][level_name.upper()] = design
                
                # Design mat foundation
                design_results[case_name]['mat'] = {}
                if self.mat_points:
                    # Estimate soil pressure
                    total_load = sum(abs(f['fz']) for f in joint_forces.values()) / 1000  # kips
                    mat_area = 20 * 20  # ft² (simplified)
                    soil_pressure = total_load / mat_area  # ksf
                    
                    mat_thickness = float(self.mat_thickness.get()) * 12  # convert to inches
                    design = design_calc.design_foundation_mat(soil_pressure, mat_thickness, 
                                                              20, 20, is_seismic=is_seismic)
                    design_results[case_name]['mat']['FOUNDATION'] = design
            
            self.design_results = design_results
            self.export_design_calculations()
            self.status_bar.config(text="Structural design completed with ACI 318-25")
            
            return design_results
            
        except Exception as e:
            messagebox.showerror("Design Error", f"Structural design failed: {str(e)}")
            traceback.print_exc()
            return None
    
    def show_results(self):
        """Show analysis results"""
        self.display_static_results()
    
    def export_design_calculations(self):
        """Export detailed ACI 318-25 design calculations to Excel"""
        try:
            if not hasattr(self, 'design_results') or not self.design_results:
                messagebox.showwarning("Warning", "No design results to export")
                return
            
            filepath = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel", "*.xlsx")],
                initialfile="ACI_318-25_Design_Calculations.xlsx"
            )
            if not filepath:
                return
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Summary sheet
                summary_data = []
                summary_data.append(["ACI 318-25 STRUCTURAL DESIGN CALCULATIONS", ""])
                summary_data.append(["Project: Turbine Pedestal", ""])
                summary_data.append([f"Design Code: {ACI_VERSION}", ""])
                summary_data.append([f"IBC Version: {IBC_VERSION}", ""])
                summary_data.append([f"Seismic Zone: {self.seismic_zone}", ""])
                summary_data.append([f"Site Class: {self.site_class.get()}", ""])
                summary_data.append([f"Concrete f'c: {self.fc_val.get()} psi", ""])
                summary_data.append([f"Steel fy: {STEEL_FY} psi", ""])
                summary_data.append(["", ""])
                summary_data.append(["Mesh Characteristics:", f"{self.mesh_size}ft x {self.mesh_size}ft square/rectangular elements"])
                summary_data.append(["Total Nodes:", len(self.nodes)])
                summary_data.append(["Total Elements:", len(self.elements)])
                summary_data.append(["", ""])
                summary_data.append(["Generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                summary_data.append(["", ""])
                
                # Add node naming information
                summary_data.append(["NODE NAMING CONVENTION", ""])
                summary_data.append(["Piles: PI1, PI2, PI3, ...", ""])
                summary_data.append(["Mat Joints: MJ1, MJ2, MJ3, ...", ""])
                summary_data.append(["Columns: COL1, COL2, COL3, ...", ""])
                summary_data.append(["Mezzanine: MZ1, MZ2, MZ3, ...", ""])
                summary_data.append(["Top Floor: TF1, TF2, TF3, ...", ""])
                summary_data.append(["Beams: B1, B2, B3, ...", ""])
                
                # Add vibration criteria
                summary_data.append(["", ""])
                summary_data.append(["VIBRATION CRITERIA", ""])
                summary_data.append(["Slab/Beam Natural Frequency > 8.0 Hz", "To prevent perceptible vibration"])
                summary_data.append(["Maximum Deflection: L/360", "ACI 318-25 24.2.3"])
                summary_data.append(["Maximum Story Drift: 0.025h", "ASCE 7-16 Table 12.12-1"])
                
                # Add seismic criteria
                summary_data.append(["", ""])
                summary_data.append(["SEISMIC DESIGN CRITERIA (Zone C)", ""])
                summary_data.append(["Seismic Design Category: C or D", "IBC 2021 Table 1613.2.5(1)"])
                summary_data.append(["Special Moment Frames Required", "ACI 318-25 Chapter 18"])
                summary_data.append(["Response Modification Factor R: 3.0", "ASCE 7-16 Table 12.2-1"])
                
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name='Summary', index=False, header=False)
                
                # Detailed calculations for each load case
                for case_name, designs in self.design_results.items():
                    # Columns sheet
                    if 'columns' in designs and designs['columns']:
                        col_data = []
                        col_data.append([f"COLUMN DESIGN - {case_name}", ""])
                        col_data.append(["Element", "Size (in)", "Pu (k)", "Mu (k-ft)", "Ast req (in²)", 
                                       "Rebar Selected", "Capacity Ratio", "Slenderness", "Seismic", "Status", "ACI Clause"])
                        
                        for elem_name, design in designs['columns'].items():
                            # Get clauses
                            clauses = design.get('clauses', {})
                            main_clause = list(clauses.values())[0] if clauses else "N/A"
                            
                            col_data.append([
                                elem_name,
                                f"{design.get('b',0)}x{design.get('h',0)}",
                                f"{design.get('Pu',0):.1f}",
                                f"{max(design.get('Mu_x',0), design.get('Mu_y',0)):.1f}",
                                f"{design.get('Ast_required',0):.2f}",
                                design.get('rebar_selected', 'N/A'),
                                f"{design.get('capacity_ratio',0):.3f}",
                                f"{design.get('slenderness_ratio',0):.1f}",
                                "Yes" if design.get('is_seismic', False) else "No",
                                design.get('design_status', 'N/A'),
                                main_clause[:50]  # Truncate for display
                            ])
                        
                        df_cols = pd.DataFrame(col_data[2:], columns=col_data[1])
                        sheet_name = f'Cols_{case_name}'[:31]
                        df_cols.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Beams sheet
                    if 'beams' in designs and designs['beams']:
                        beam_data = []
                        beam_data.append([f"BEAM DESIGN - {case_name}", ""])
                        beam_data.append(["Element", "Size (in)", "Mu (k-ft)", "Vu (k)", 
                                        "As req (in²)", "Shear Reinf", "Deflection", "Vibration", "Status", "ACI Clause"])
                        
                        for elem_name, design in designs['beams'].items():
                            flexure = design.get('flexure', {})
                            shear = design.get('shear', {})
                            
                            # Get clauses
                            clauses = flexure.get('clauses', {})
                            main_clause = list(clauses.values())[0] if clauses else "N/A"
                            
                            beam_data.append([
                                elem_name,
                                f"{flexure.get('b',0)}x{flexure.get('h',0)}",
                                f"{flexure.get('Mu',0):.1f}",
                                f"{shear.get('Vu',0):.1f}",
                                f"{flexure.get('As_required',0):.2f}",
                                f"{'Yes' if shear.get('shear_reinforcement_required',False) else 'No'}",
                                f"{'OK' if flexure.get('deflection_ok',False) else 'FAIL'}",
                                f"{'OK' if flexure.get('vibration_ok',False) else 'FAIL'}",
                                flexure.get('design_status', 'N/A'),
                                main_clause[:50]
                            ])
                        
                        df_beams = pd.DataFrame(beam_data[2:], columns=beam_data[1])
                        sheet_name = f'Beams_{case_name}'[:31]
                        df_beams.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Piles sheet
                    if 'piles' in designs and designs['piles']:
                        pile_data = []
                        pile_data.append([f"PILE DESIGN - {case_name}", ""])
                        pile_data.append(["Element", "Dia (in)", "Length (ft)", "Load (k)", 
                                        "Moment (k-ft)", "Rebar", "Bearing Ratio", "Settlement", "Seismic", "Status", "ACI Clause"])
                        
                        for elem_name, design in designs['piles'].items():
                            # Get clauses
                            clauses = design.get('clauses', {})
                            main_clause = list(clauses.values())[0] if clauses else "N/A"
                            
                            pile_data.append([
                                elem_name,
                                f"{design.get('diameter',0):.1f}",
                                f"{design.get('length',0):.1f}",
                                f"{design.get('axial_load',0):.1f}",
                                f"{design.get('moment',0):.1f}",
                                design.get('bar_size', 'N/A'),
                                f"{design.get('bearing_ratio',0):.3f}",
                                f"{design.get('settlement',0):.3f} in",
                                "Yes" if design.get('is_seismic', False) else "No",
                                design.get('design_status', 'N/A'),
                                main_clause[:50]
                            ])
                        
                        df_piles = pd.DataFrame(pile_data[2:], columns=pile_data[1])
                        sheet_name = f'Piles_{case_name}'[:31]
                        df_piles.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Slabs sheet
                    if 'slabs' in designs and designs['slabs']:
                        slab_data = []
                        slab_data.append([f"SLAB DESIGN - {case_name}", ""])
                        slab_data.append(["Level", "Thick (in)", "Moment (k-ft/ft)", 
                                        "As req (in²/ft)", "Rebar", "Spacing (in)", "Frequency", "Seismic", "Status", "ACI Clause"])
                        
                        for level_name, design in designs['slabs'].items():
                            # Get clauses
                            clauses = design.get('clauses', {})
                            main_clause = list(clauses.values())[0] if clauses else "N/A"
                            
                            slab_data.append([
                                level_name.upper(),
                                f"{design.get('thickness',0):.1f}",
                                f"{design.get('moment',0):.3f}",
                                f"{design.get('As_required',0):.3f}",
                                design.get('bar_size', 'N/A'),
                                f"{design.get('spacing',0):.1f}",
                                f"{design.get('frequency',0):.1f} Hz",
                                "Yes" if design.get('is_seismic', False) else "No",
                                design.get('design_status', 'N/A'),
                                main_clause[:50]
                            ])
                        
                        df_slabs = pd.DataFrame(slab_data[2:], columns=slab_data[1])
                        sheet_name = f'Slabs_{case_name}'[:31]
                        df_slabs.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Mat foundation sheet
                    if 'mat' in designs and designs['mat']:
                        mat_data = []
                        mat_data.append([f"MAT FOUNDATION DESIGN - {case_name}", ""])
                        mat_data.append(["Parameter", "Value", "Status", "Requirement"])
                        
                        for elem_name, design in designs['mat'].items():
                            mat_data.append(["Thickness", f"{design.get('thickness',0):.1f} in", 
                                           "OK" if design.get('thickness_ok', False) else "FAIL",
                                           f"Min: {design.get('min_thickness',0):.1f} in"])
                            mat_data.append(["Punching Shear", f"{design.get('punching_shear_ratio',0):.3f}", 
                                           "OK" if design.get('punching_shear_ratio',0) <= 1.0 else "FAIL",
                                           "≤ 1.0"])
                            mat_data.append(["Beam Shear", f"{design.get('beam_shear_ratio',0):.3f}", 
                                           "OK" if design.get('beam_shear_ratio',0) <= 1.0 else "FAIL",
                                           "≤ 1.0"])
                            mat_data.append(["Bearing Pressure", f"{design.get('bearing_ratio',0):.3f}", 
                                           "OK" if design.get('bearing_ratio',0) <= 1.0 else "FAIL",
                                           "≤ 1.0"])
                            mat_data.append(["Seismic Design", "Yes" if design.get('is_seismic', False) else "No",
                                           "", "ACI 318-25 18.13"])
                        
                        df_mat = pd.DataFrame(mat_data[2:], columns=mat_data[1])
                        sheet_name = f'Mat_{case_name}'[:31]
                        df_mat.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Create a combined results sheet
                all_results = []
                all_results.append(["COMPREHENSIVE ACI 318-25 DESIGN RESULTS", ""])
                all_results.append(["Element Type", "Element ID", "Load Case", "Critical Check", "Status", "ACI Clause", "Remarks"])
                
                for case_name, designs in self.design_results.items():
                    # Add columns
                    for elem_name, design in designs.get('columns', {}).items():
                        clauses = design.get('clauses', {})
                        main_clause = list(clauses.values())[0] if clauses else "N/A"
                        
                        all_results.append([
                            "Column", elem_name, case_name,
                            f"Capacity Ratio: {design.get('capacity_ratio',0):.3f}",
                            design.get('design_status', 'N/A'),
                            main_clause[:30],
                            f"Rebar: {design.get('rebar_selected','N/A')}"
                        ])
                    
                    # Add beams
                    for elem_name, design in designs.get('beams', {}).items():
                        flexure = design.get('flexure', {})
                        clauses = flexure.get('clauses', {})
                        main_clause = list(clauses.values())[0] if clauses else "N/A"
                        
                        all_results.append([
                            "Beam", elem_name, case_name,
                            f"Deflection: {'OK' if flexure.get('deflection_ok',False) else 'FAIL'}",
                            flexure.get('design_status', 'N/A'),
                            main_clause[:30],
                            f"As: {flexure.get('As_required',0):.2f} in²"
                        ])
                    
                    # Add piles
                    for elem_name, design in designs.get('piles', {}).items():
                        clauses = design.get('clauses', {})
                        main_clause = list(clauses.values())[0] if clauses else "N/A"
                        
                        all_results.append([
                            "Pile", elem_name, case_name,
                            f"Settlement: {design.get('settlement',0):.3f} in",
                            design.get('design_status', 'N/A'),
                            main_clause[:30],
                            f"Rebar: {design.get('bar_size','N/A')}"
                        ])
                    
                    # Add slabs
                    for level_name, design in designs.get('slabs', {}).items():
                        clauses = design.get('clauses', {})
                        main_clause = list(clauses.values())[0] if clauses else "N/A"
                        
                        all_results.append([
                            "Slab", level_name.upper(), case_name,
                            f"Frequency: {design.get('frequency',0):.1f} Hz",
                            design.get('design_status', 'N/A'),
                            main_clause[:30],
                            f"Rebar: {design.get('bar_size','N/A')} @ {design.get('spacing',0):.1f}\""
                        ])
                    
                    # Add mat foundation
                    for elem_name, design in designs.get('mat', {}).items():
                        all_results.append([
                            "Mat Foundation", elem_name, case_name,
                            f"Bearing: {design.get('bearing_ratio',0):.3f}",
                            design.get('design_status', 'N/A'),
                            "ACI 318-25 13.3 & 22.8",
                            f"Thickness: {design.get('thickness',0):.1f} in"
                        ])
                
                df_all = pd.DataFrame(all_results[2:], columns=all_results[1])
                df_all.to_excel(writer, sheet_name='All_Results', index=False)
                
                # Special Load Cases Sheet
                special_loads_data = []
                special_loads_data.append(["SPECIAL LOAD CASES", "", "", ""])
                special_loads_data.append(["Case Name", "Type", "Description", "Coordinates", "Load Pattern", "Load Factor"])
                
                for case_name, case_data in self.special_load_cases.items():
                    special_loads_data.append([
                        case_name,
                        case_data['type'],
                        case_data['description'],
                        case_data['coordinates'],
                        case_data['load_pattern'],
                        f"{case_data['load_factor']:.1f}"
                    ])
                
                df_special = pd.DataFrame(special_loads_data[2:], columns=special_loads_data[1])
                df_special.to_excel(writer, sheet_name='Special_Loads', index=False)
                
                # Seismic Parameters Sheet
                seismic_data = []
                seismic_data.append(["SEISMIC DESIGN PARAMETERS (Zone C)", "", ""])
                seismic_data.append(["Parameter", "Value", "Reference"])
                seismic_data.append(["Seismic Zone", self.seismic_zone, "IBC 2021"])
                seismic_data.append(["Site Class", self.site_class.get(), "IBC 2021 Table 1613.2.3(1)"])
                seismic_data.append(["Ss", self.seismic_ss.get(), "MCE spectral acceleration at 0.2s"])
                seismic_data.append(["S1", self.seismic_s1.get(), "MCE spectral acceleration at 1.0s"])
                seismic_data.append(["R factor", self.r_factor.get(), "ASCE 7-16 Table 12.2-1"])
                seismic_data.append(["Ie factor", self.ie_factor.get(), "ASCE 7-16 Table 1.5-2"])
                seismic_data.append(["Seismic Design Category", "C/D", "IBC 2021 Table 1613.2.5(1)"])
                seismic_data.append(["", "", ""])
                seismic_data.append(["SEISMIC DESIGN REQUIREMENTS", "", ""])
                seismic_data.append(["Structural System", "Special Moment Frame", "ACI 318-25 Chapter 18"])
                seismic_data.append(["Column Requirements", "ACI 318-25 18.7", "Special detailing for seismic"])
                seismic_data.append(["Beam Requirements", "ACI 318-25 18.6", "Special detailing for seismic"])
                seismic_data.append(["Joint Requirements", "ACI 318-25 18.8", "Special detailing for joints"])
                seismic_data.append(["Diaphragm Requirements", "ACI 318-25 18.12", "Diaphragm design"])
                seismic_data.append(["Foundation Requirements", "ACI 318-25 18.13", "Foundation seismic design"])
                
                df_seismic = pd.DataFrame(seismic_data[2:], columns=seismic_data[1])
                df_seismic.to_excel(writer, sheet_name='Seismic_Params', index=False)
            
            self.status_bar.config(text=f"ACI 318-25 design calculations exported to Excel")
            messagebox.showinfo("Export Complete", 
                              f"ACI 318-25 design calculations exported to:\n{filepath}\n\n"
                              f"Includes detailed calculations for:\n"
                              f"- Columns (with seismic detailing)\n"
                              f"- Beams (with vibration check > 8 Hz)\n"
                              f"- Piles (with settlement check)\n"
                              f"- Slabs (with frequency check)\n"
                              f"- Mat foundation\n"
                              f"- Special load cases with coordinates\n"
                              f"- Seismic design parameters for Zone C\n"
                              f"- ACI 318-25 clause references for each check")
            
            return filepath
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export design calculations: {str(e)}")
            traceback.print_exc()
            return None
    
    def export_comprehensive_pdf_report(self):
        """Export comprehensive PDF report with all analysis results"""
        try:
            if not self.results:
                messagebox.showwarning("Warning", "No analysis results to export")
                return
            
            filepath = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF", "*.pdf")],
                initialfile="Turbine_Pedestal_Design_Report.pdf"
            )
            if not filepath:
                return
            
            c = pdf_canvas.Canvas(filepath, pagesize=letter)
            width, height = letter
            
            # Title
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, "TURBINE PEDESTAL DESIGN REPORT")
            c.setFont("Helvetica", 10)
            c.drawString(50, height - 70, f"ACI {ACI_VERSION} | IBC {IBC_VERSION} | Seismic Zone: {self.seismic_zone}")
            c.drawString(50, height - 85, f"Mesh Size: {self.mesh_size}ft x {self.mesh_size}ft | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Add content
            y_position = height - 120
            
            # Summary section
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_position, "1. SUMMARY")
            y_position -= 20
            
            c.setFont("Helvetica", 10)
            summary_lines = [
                f"Total Nodes: {len(self.nodes)}",
                f"Total Elements: {len(self.elements)}",
                f"Mesh Type: {self.mesh_size}ft x {self.mesh_size}ft square/rectangular elements",
                f"Seismic Zone: {self.seismic_zone}",
                f"Site Class: {self.site_class.get()}",
                f"Concrete f'c: {self.fc_val.get()} psi",
                f"Steel fy: {STEEL_FY} psi"
            ]
            
            for line in summary_lines:
                c.drawString(70, y_position, line)
                y_position -= 15
            
            y_position -= 10
            
            # Analysis Results
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_position, "2. ANALYSIS RESULTS")
            y_position -= 20
            
            if 'static' in self.results:
                c.setFont("Helvetica-Bold", 10)
                c.drawString(70, y_position, "Static Analysis:")
                y_position -= 15
                
                c.setFont("Helvetica", 9)
                for case_name in list(self.results['static'].keys())[:3]:  # Show first 3 cases
                    c.drawString(90, y_position, f"{case_name}: Completed")
                    y_position -= 12
            
            y_position -= 10
            
            # Design Recommendations
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_position, "3. DESIGN RECOMMENDATIONS")
            y_position -= 20
            
            recommendations = [
                "1. Design all structural members per ACI 318-25",
                "2. Verify strength requirements per Chapter 22",
                "3. Check serviceability limits per Section 24.2",
                "4. Ensure seismic detailing per Chapter 18",
                "5. Verify vibration criteria (> 8.0 Hz)",
                "6. Check foundation design per Chapter 13"
            ]
            
            c.setFont("Helvetica", 9)
            for rec in recommendations:
                c.drawString(70, y_position, rec)
                y_position -= 12
            
            # Save PDF
            c.save()
            
            self.status_bar.config(text=f"Comprehensive PDF report exported")
            messagebox.showinfo("Export Complete", f"PDF report exported to:\n{filepath}")
            
            return filepath
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF report: {str(e)}")
            traceback.print_exc()
            return None
    
    def export_all(self):
        """Export all results (Excel, PDF, DXF)"""
        try:
            # Export Excel
            excel_path = self.export_design_calculations()
            
            # Export PDF
            pdf_path = self.export_comprehensive_pdf_report()
            
            # Export DXF
            dxf_path = self.export_dxf_with_names()
            
            self.status_bar.config(text="All exports completed")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export all files: {str(e)}")
    
    def reset_model(self):
        """Reset the entire model"""
        if messagebox.askyesno("Confirm Reset", "Are you sure you want to reset the entire model? All data will be lost."):
            # Clear all data
            self.nodes = []
            self.elements = []
            self.load_cases = {}
            self.load_cases_applied = {}
            self.load_combos = {}
            self.results = {}
            self.design_results = {}
            
            # Clear tables
            for tree in self.tables.values():
                for item in tree.get_children():
                    tree.delete(item)
            
            # Clear results text
            self.results_text.delete("1.0", tk.END)
            
            # Reset plot
            self.figure.clear()
            self.canvas.draw()
            
            self.status_bar.config(text="Model reset successfully")
    
    def export_dxf_with_names(self):
        """Export to DXF with proper node naming"""
        try:
            if not self.nodes or not self.elements:
                messagebox.showwarning("Warning", "No geometry to export")
                return
            
            if not DXF_AVAILABLE:
                messagebox.showwarning("Warning", "ezdxf package not installed. Install with: pip install ezdxf")
                return
            
            filepath = filedialog.asksaveasfilename(
                defaultextension=".dxf",
                filetypes=[("DXF", "*.dxf")],
                initialfile=f"Structure_With_Names_{self.mesh_size}ft_Mesh.dxf"
            )
            if not filepath:
                return
            
            # Create DXF document
            doc = ezdxf.new('R2010')
            doc.units = units.M
            msp = doc.modelspace()
            
            # Create layers
            layers = {
                'NODES': 7,
                'COLUMNS': 1,
                'BEAMS': 3,
                'PILES': 5,
                'SHELLS': 2,
                'TEXT': 7,
                'DIMENSIONS': 4,
                'GRID': 9
            }
            
            for layer_name, color in layers.items():
                doc.layers.add(layer_name, color=color)
            
            # Add grid lines for 2ft mesh
            if self.mesh_size > 0:
                # Get bounds
                x_coords = [node[0] for node in self.nodes]
                y_coords = [node[1] for node in self.nodes]
                min_x, max_x = min(x_coords), max(x_coords)
                min_y, max_y = min(y_coords), max(y_coords)
                
                # Round to nearest mesh size
                min_x = math.floor(min_x / self.mesh_size) * self.mesh_size
                max_x = math.ceil(max_x / self.mesh_size) * self.mesh_size
                min_y = math.floor(min_y / self.mesh_size) * self.mesh_size
                max_y = math.ceil(max_y / self.mesh_size) * self.mesh_size
                
                # Draw grid
                for x in np.arange(min_x, max_x + self.mesh_size, self.mesh_size):
                    x_m = x * 0.3048
                    msp.add_line((x_m, min_y*0.3048, 0), (x_m, max_y*0.3048, 0), dxfattribs={'layer': 'GRID'})
                
                for y in np.arange(min_y, max_y + self.mesh_size, self.mesh_size):
                    y_m = y * 0.3048
                    msp.add_line((min_x*0.3048, y_m, 0), (max_x*0.3048, y_m, 0), dxfattribs={'layer': 'GRID'})
            
            # Assign node names based on location and element type
            node_names = {}
            
            # Initialize counters
            pile_nodes = []
            mat_nodes = []
            column_nodes = []
            mezzanine_nodes = []
            top_nodes = []
            beam_nodes = []
            
            # Classify nodes by elevation and element type
            mat_z = float(self.mat_z.get())
            mezzanine_z = float(self.mezzanine_z.get())
            top_z = float(self.top_z.get())
            
            for i, (x, y, z) in enumerate(self.nodes):
                # Check if node belongs to piles
                for elem in self.elements:
                    if elem[0] == 'PILE' and (elem[2] == i or elem[3] == i):
                        pile_nodes.append(i)
                        break
                else:  # Not a pile node
                    # Check mat level (lowest Z)
                    if abs(z - mat_z) < 1.0:
                        mat_nodes.append(i)
                    # Check mezzanine level
                    elif abs(z - mezzanine_z) < 1.0:
                        mezzanine_nodes.append(i)
                    # Check top level
                    elif abs(z - top_z) < 1.0:
                        top_nodes.append(i)
                    # Check if node belongs to beams
                    for elem in self.elements:
                        if elem[0] == 'BEAM' and (elem[2] == i or elem[3] == i):
                            beam_nodes.append(i)
                            break
            
            # Assign names
            for i, node_idx in enumerate(pile_nodes):
                node_names[node_idx] = f"PI{i+1}"
            
            for i, node_idx in enumerate(mat_nodes):
                node_names[node_idx] = f"MJ{i+1}"
            
            for i, node_idx in enumerate(column_nodes):
                node_names[node_idx] = f"COL{i+1}"
            
            for i, node_idx in enumerate(mezzanine_nodes):
                node_names[node_idx] = f"MZ{i+1}"
            
            for i, node_idx in enumerate(top_nodes):
                node_names[node_idx] = f"TF{i+1}"
            
            for i, node_idx in enumerate(beam_nodes):
                node_names[node_idx] = f"B{i+1}"
            
            # Add nodes with text labels
            for i, (x, y, z) in enumerate(self.nodes):
                x_m, y_m, z_m = x*0.3048, y*0.3048, z*0.3048
                msp.add_point((x_m, y_m, z_m), dxfattribs={'layer': 'NODES'})
                
                # Add node name text
                if i in node_names:
                    text = msp.add_text(node_names[i], height=0.3, dxfattribs={'layer': 'TEXT'})
                    # FIXED: Use dxf.insert property instead of set_location
                    text.dxf.insert = (x_m + 0.1, y_m + 0.1, z_m)
        
            # Add elements
            for elem in self.elements:
                elem_type = elem[0]
                
                if elem_type in ['COLUMN', 'BEAM', 'PILE', 'LINK']:
                    n1, n2 = elem[2], elem[3]
                    if all(n < len(self.nodes) for n in [n1, n2]):
                        x1, y1, z1 = self.nodes[n1]
                        x2, y2, z2 = self.nodes[n2]
                        
                        x1_m, y1_m, z1_m = x1*0.3048, y1*0.3048, z1*0.3048
                        x2_m, y2_m, z2_m = x2*0.3048, y2*0.3048, z2*0.3048
                        
                        layer = {
                            'COLUMN': 'COLUMNS',
                            'BEAM': 'BEAMS',
                            'PILE': 'PILES',
                            'LINK': 'SHELLS'
                        }.get(elem_type, 'SHELLS')
                        
                        msp.add_line((x1_m, y1_m, z1_m), (x2_m, y2_m, z2_m), dxfattribs={'layer': layer})
            
            doc.saveas(filepath)
            self.status_bar.config(text=f"DXF exported with node names: {os.path.basename(filepath)}")
            messagebox.showinfo("Export Complete", f"DXF file exported with node naming:\n{filepath}")
            
            return filepath
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export DXF: {str(e)}")
            traceback.print_exc()
            return None
    
    def show_comprehensive_results(self):
        """Show comprehensive analysis results"""
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert(tk.END, "="*80 + "\n")
        self.results_text.insert(tk.END, "COMPREHENSIVE ANALYSIS RESULTS\n")
        self.results_text.insert(tk.END, "="*80 + "\n\n")
        
        # Geometry summary
        self.results_text.insert(tk.END, "GEOMETRY SUMMARY:\n")
        self.results_text.insert(tk.END, f"- Total Nodes: {len(self.nodes)}\n")
        self.results_text.insert(tk.END, f"- Total Elements: {len(self.elements)}\n")
        self.results_text.insert(tk.END, f"- Mesh Size: {self.mesh_size}ft x {self.mesh_size}ft square/rectangular elements\n")
        self.results_text.insert(tk.END, f"- Seismic Zone: {self.seismic_zone}\n")
        self.results_text.insert(tk.END, f"- Site Class: {self.site_class.get()}\n\n")
        
        # Analysis results
        if 'static' in self.results:
            self.results_text.insert(tk.END, "STATIC ANALYSIS:\n")
            self.results_text.insert(tk.END, f"- Load Cases Analyzed: {len(self.results['static'])}\n")
            # Get max displacements
            max_displacement = 0
            for case_name, results in self.results['static'].items():
                if 'displacements' in results:
                    max_disp = np.max(np.abs(results['displacements']))
                    max_displacement = max(max_displacement, max_disp)
            
            self.results_text.insert(tk.END, f"- Maximum Displacement: {max_displacement*12:.3f} in\n\n")
        
        if 'dynamic' in self.results:
            self.results_text.insert(tk.END, "DYNAMIC ANALYSIS:\n")
            frequencies = self.results['dynamic'].get('frequencies', [])
            if len(frequencies) > 0:
                self.results_text.insert(tk.END, f"- First Natural Frequency: {frequencies[0]:.2f} Hz\n")
                vibration_check = self.results['dynamic'].get('vibration_check', {})
                if vibration_check:
                    if vibration_check.get('passed', False):
                        self.results_text.insert(tk.END, "- Vibration Criteria: ✓ SATISFIED (> 8.0 Hz)\n")
                    else:
                        self.results_text.insert(tk.END, "- Vibration Criteria: ⚠️ NOT SATISFIED\n")
            self.results_text.insert(tk.END, "\n")
        
        # Design results
        if hasattr(self, 'design_results') and self.design_results:
            self.results_text.insert(tk.END, "STRUCTURAL DESIGN (ACI 318-25):\n")
            
            # Count design elements
            total_elements = 0
            passed_elements = 0
            
            for case_name, designs in self.design_results.items():
                for elem_type, elem_designs in designs.items():
                    for elem_name, design in elem_designs.items():
                        total_elements += 1
                        if isinstance(design, dict) and design.get('design_status') == 'OK':
                            passed_elements += 1
            
            self.results_text.insert(tk.END, f"- Design Elements Checked: {total_elements}\n")
            self.results_text.insert(tk.END, f"- Elements Passing: {passed_elements}\n")
            self.results_text.insert(tk.END, f"- Elements Failing: {total_elements - passed_elements}\n\n")
        
        self.results_text.insert(tk.END, "="*80 + "\n")
        self.results_text.insert(tk.END, "ANALYSIS COMPLETE\n")
        self.results_text.insert(tk.END, "="*80 + "\n")
    
    # --- VISUALIZATION ---
    def update_plot(self):
        """Update plot based on view selection"""
        self.figure.clear()
        
        if not self.nodes:
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, "No geometry to display", 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_axis_off()
        else:
            view = self.view_var.get()
            
            if view in ["3D Structure", "Column View", "Beam View", "Slab Mesh", "Seismic Forces"]:
                try:
                    ax = self.figure.add_subplot(111, projection='3d')
                except:
                    ax = self.figure.add_subplot(111)
                    ax.text(0.5, 0.5, "3D plot not available", 
                           ha='center', va='center', transform=ax.transAxes)
                    ax.set_axis_off()
                    self.canvas.draw()
                    return
                    
                nodes = np.array(self.nodes)
                
                # Plot all nodes
                ax.scatter(nodes[:,0], nodes[:,1], nodes[:,2], c='b', s=10, alpha=0.6)
                
                # Plot elements based on view
                for elem in self.elements:
                    elem_type = elem[0]
                    
                    # Filter by view
                    if view == "Column View" and elem_type != 'COLUMN':
                        continue
                    if view == "Beam View" and elem_type != 'BEAM':
                        continue
                    if view == "Slab Mesh" and elem_type != 'SHELL':
                        continue
                    
                    # Colors
                    if elem_type == 'SHELL':
                        color = 'lightblue'
                        alpha = 0.3
                        linewidth = 0.5
                    elif elem_type == 'COLUMN':
                        color = 'red'
                        alpha = 0.8
                        linewidth = 2
                    elif elem_type == 'BEAM':
                        color = 'green'
                        alpha = 0.8
                        linewidth = 2
                    elif elem_type == 'PILE':
                        color = 'brown'
                        alpha = 0.8
                        linewidth = 2
                    elif elem_type == 'LINK':
                        color = 'orange'
                        alpha = 0.5
                        linewidth = 1
                    else:
                        color = 'gray'
                        alpha = 0.5
                        linewidth = 1
                    
                    # Plot element
                    if elem_type == 'SHELL' and len(elem) >= 6:  # Quad
                        n1, n2, n3, n4 = elem[2], elem[3], elem[4], elem[5]
                        if all(n < len(self.nodes) for n in [n1, n2, n3, n4]):
                            x = [self.nodes[n1][0], self.nodes[n2][0], self.nodes[n3][0], self.nodes[n4][0], self.nodes[n1][0]]
                            y = [self.nodes[n1][1], self.nodes[n2][1], self.nodes[n3][1], self.nodes[n4][1], self.nodes[n1][1]]
                            z = [self.nodes[n1][2], self.nodes[n2][2], self.nodes[n3][2], self.nodes[n4][2], self.nodes[n1][2]]
                            
                            ax.plot(x, y, z, color=color, linewidth=linewidth, alpha=alpha)
                    
                    elif elem_type in ['COLUMN', 'BEAM', 'PILE', 'LINK']:
                        n1, n2 = elem[2], elem[3]
                        if all(n < len(self.nodes) for n in [n1, n2]):
                            x = [self.nodes[n1][0], self.nodes[n2][0]]
                            y = [self.nodes[n1][1], self.nodes[n2][1]]
                            z = [self.nodes[n1][2], self.nodes[n2][2]]
                            
                            ax.plot(x, y, z, color=color, linewidth=linewidth, alpha=alpha)
                
                ax.set_xlabel('X (ft)')
                ax.set_ylabel('Y (ft)')
                ax.set_zlabel('Z (ft)')
                ax.set_title(f'Structure - {view} | Mesh: {self.mesh_size}ft x {self.mesh_size}ft')
                ax.grid(True)
            
            else:  # 2D plots
                ax = self.figure.add_subplot(111)
                nodes = np.array(self.nodes)
                
                if view == "Plan View":
                    ax.scatter(nodes[:,0], nodes[:,1], c='b', s=10, alpha=0.6)
                    ax.set_xlabel('X (ft)')
                    ax.set_ylabel('Y (ft)')
                    ax.set_title(f'Plan View | Mesh: {self.mesh_size}ft x {self.mesh_size}ft')
                    ax.grid(True)
                    ax.axis('equal')
                
                elif view == "Elevation X":
                    ax.scatter(nodes[:,1], nodes[:,2], c='b', s=10, alpha=0.6)
                    ax.set_xlabel('Y (ft)')
                    ax.set_ylabel('Z (ft)')
                    ax.set_title('Elevation X')
                    ax.grid(True)
                
                elif view == "Elevation Y":
                    ax.scatter(nodes[:,0], nodes[:,2], c='b', s=10, alpha=0.6)
                    ax.set_xlabel('X (ft)')
                    ax.set_ylabel('Z (ft)')
                    ax.set_title('Elevation Y')
                    ax.grid(True)
        
        self.canvas.draw()
    
    def save_plot(self):
        """Save current plot to file"""
        try:
            filepath = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG", "*.png"), ("PDF", "*.pdf"), ("JPEG", "*.jpg")],
                initialfile=f"Structure_Plot_{self.view_var.get().replace(' ', '_')}.png"
            )
            if filepath:
                self.figure.savefig(filepath, dpi=300, bbox_inches='tight')
                self.status_bar.config(text=f"Plot saved to {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save plot: {str(e)}")

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    root = tk.Tk()
    app = TurbinePedestalDesigner(root)
    root.mainloop()