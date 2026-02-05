import pandas as pd # pyright: ignore[reportMissingModuleSource]
import numpy as np # pyright: ignore[reportMissingImports]
from datetime import datetime
import matplotlib.pyplot as plt # pyright: ignore[reportMissingModuleSource]
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # pyright: ignore[reportMissingModuleSource]
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import datetime
import socket
import tkinter as tk
from tkinter.ttk import *
import ntplib # pyright: ignore[reportMissingImports]
import sys

# Hard License System Configuration
# Set expiry date to August 31, 2025
TARGET_EXPIRY_DATE = datetime.datetime(2026, 8, 31, 23, 59, 59)
NTP_SERVERS = [
    "pool.ntp.org",
    "time.google.com",
    "time.cloudflare.com",
    "time.windows.com",
    "time.apple.com"
]

class HardLicenseManager:
    def __init__(self):
        pass

    def _get_ntp_time(self):
        """
        Get accurate time from NTP servers.
        Tries multiple servers and falls back to system time if all fail.
        """
        for server in NTP_SERVERS:
            try:
                client = ntplib.NTPClient()
                # Request NTP response with a timeout
                response = client.request(server, version=3, timeout=5)
                # Convert NTP timestamp to datetime object
                ntp_time = datetime.datetime.fromtimestamp(response.tx_time)
                print(f"NTP time retrieved from {server}: {ntp_time}")
                return ntp_time
            except Exception as e:
                print(f"Failed to get time from {server}: {e}")
                continue

        # If all NTP servers fail, use system time (less secure but allows offline use)
        print("Warning: Could not connect to NTP servers, using system time.")
        return datetime.datetime.now()

    def verify_license(self):
        """
        Verify if the software license is still valid based on the current date.
        Compares current time (preferably NTP) against a hardcoded expiry date.
        """
        try:
            # Get current time using the NTP time retrieval method
            current_time = self._get_ntp_time()

            # Check if license has expired
            if current_time > TARGET_EXPIRY_DATE:
                print(f"License expired on: {TARGET_EXPIRY_DATE}")
                print(f"Current time: {current_time}")
                return False

            # Calculate days remaining until expiry
            days_remaining = (TARGET_EXPIRY_DATE - current_time).days
            print(f"License is valid. Days remaining: {days_remaining}")
            print(f"License expires on: {TARGET_EXPIRY_DATE}")
            return True

        except Exception as e:
            print(f"License verification failed: {e}")
            return False

# Initialize license manager
license_manager = HardLicenseManager()

# Verify license before running the main program
if not license_manager.verify_license():
    print("\n" + "="*50)
    print("LICENSE VERIFICATION FAILED")
    print("="*50)
    print("This software license has expired.")
    print(f"Software was valid until: {TARGET_EXPIRY_DATE}")
    print("Please contact the developer for a new license.")
    print("="*50)
    input("Press Enter to exit...")
    sys.exit()

# Original code continues here...
hostname = socket.gethostname()
IPAddr = socket.gethostbyname(hostname)
local_ip_address = str(IPAddr) # Renamed 'g' for clarity
print(local_ip_address)
current_datetime = datetime.datetime.now() # Renamed 'd' for clarity
g=str(IPAddr)
w=str('192.168.1.163')
if(g!=w):
    print("License Expired")
    print(1/0)
else:
    print("Software Activated")
class AdvancedWidgetCostEstimator:
    def __init__(self):
        # Initialize with default US economic data
        self.load_economic_data()
        self.load_material_data()
        
        # Initialize GUI
        self.root = tk.Tk()
        self.root.title("Advanced US Widget Cost Estimator")
        self.create_widgets()
        self.setup_menu()
        
    def load_economic_data(self):
        """Load economic data from JSON file or use defaults"""
        try:
            with open('economic_data.json', 'r') as f:
                data = json.load(f)
                self.us_hourly_labor_rate = data.get('hourly_labor_rate', 32.50)
                self.us_productivity_factor = data.get('productivity_factor', 1.25)
                self.overhead_rate = data.get('overhead_rate', 0.35)
                self.profit_margin = data.get('profit_margin', 0.20)
                self.material_markup = data.get('material_markup', 0.15)
                self.energy_cost = data.get('energy_cost', 0.12)
                self.region_adjustments = data.get('region_adjustments', {})
        except FileNotFoundError:
            # Default values if file doesn't exist
            self.us_hourly_labor_rate = 32.50
            self.us_productivity_factor = 1.25
            self.overhead_rate = 0.35
            self.profit_margin = 0.20
            self.material_markup = 0.15
            self.energy_cost = 0.12
            self.region_adjustments = {
                'Northeast': 1.10,
                'Midwest': 1.00,
                'South': 0.95,
                'West': 1.05
            }
    
    def load_material_data(self):
        """Load material data from CSV file or use defaults"""
        try:
            self.material_costs = pd.read_csv('material_costs.csv').set_index('Material').to_dict()['Cost']
        except FileNotFoundError:
            # Default material costs
            self.material_costs = {
                'Steel': 0.85,
                'Aluminum': 2.10,
                'Plastic': 1.20,
                'Copper': 6.80,
                'Electronics': 18.50,
                'Titanium': 15.75,
                'Rubber': 2.30,
                'Glass': 1.40
            }
    
    def save_economic_data(self):
        """Save current economic data to JSON file"""
        data = {
            'hourly_labor_rate': self.us_hourly_labor_rate,
            'productivity_factor': self.us_productivity_factor,
            'overhead_rate': self.overhead_rate,
            'profit_margin': self.profit_margin,
            'material_markup': self.material_markup,
            'energy_cost': self.energy_cost,
            'region_adjustments': self.region_adjustments
        }
        with open('economic_data.json', 'w') as f:
            json.dump(data, f, indent=4)
    
    def save_material_data(self):
        """Save material data to CSV file"""
        pd.DataFrame.from_dict(self.material_costs, orient='index', columns=['Cost'])\
            .rename_axis('Material').to_csv('material_costs.csv')
    
    def setup_menu(self):
        """Create menu bar with additional options"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Save Project", command=self.save_project)
        file_menu.add_command(label="Load Project", command=self.load_project)
        file_menu.add_separator()
        file_menu.add_command(label="Export Report", command=self.export_report)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Edit Economic Data", command=self.edit_economic_data)
        edit_menu.add_command(label="Edit Material Costs", command=self.edit_material_costs)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Show Cost Breakdown", command=self.show_cost_breakdown)
        view_menu.add_command(label="Show Sensitivity Analysis", command=self.show_sensitivity_analysis)
        menubar.add_cascade(label="View", menu=view_menu)
        
        self.root.config(menu=menubar)
    
    def create_widgets(self):
        """Create main application widgets"""
        # Notebook for multiple tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Main calculation tab
        self.main_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.main_tab, text="Cost Estimation")
        
        # Results tab (initially empty)
        self.results_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.results_tab, text="Results Analysis", state='hidden')
        
        # Create widgets for main tab
        self.create_main_tab_widgets()
    
    def create_main_tab_widgets(self):
        """Create widgets for the main calculation tab"""
        # Main frame with scrollbar
        main_frame = ttk.Frame(self.main_tab)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind
        "<Configure>",            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all"))
        
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Widget specifications
        ttk.Label(scrollable_frame, text="Widget Specifications", font=('Arial', 12, 'bold'))\
            .grid(column=0, row=0, columnspan=3, pady=10, sticky=tk.W)
        
        # Region selection
        ttk.Label(scrollable_frame, text="Manufacturing Region:").grid(column=0, row=1, sticky=tk.W)
        self.region_var = tk.StringVar(value='Midwest')
        region_combo = ttk.Combobox(scrollable_frame, textvariable=self.region_var, 
                                   values=list(self.region_adjustments.keys()))
        region_combo.grid(column=1, row=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Material selection
        ttk.Label(scrollable_frame, text="Primary Material:").grid(column=0, row=2, sticky=tk.W)
        self.material_var = tk.StringVar(value='Steel')
        material_combo = ttk.Combobox(scrollable_frame, textvariable=self.material_var, 
                                     values=list(self.material_costs.keys()))
        material_combo.grid(column=1, row=2, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Custom material option
        self.custom_material_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(scrollable_frame, text="Custom Material", variable=self.custom_material_var,
                       command=self.toggle_custom_material).grid(column=2, row=2, sticky=tk.W)
        
        # Custom material entry (initially disabled)
        self.custom_material_name = tk.StringVar()
        self.custom_material_cost = tk.DoubleVar(value=0.0)
        self.custom_material_entry = ttk.Entry(scrollable_frame, textvariable=self.custom_material_name, state='disabled')
        self.custom_material_cost_entry = ttk.Entry(scrollable_frame, textvariable=self.custom_material_cost, state='disabled')
        
        # Material quantity
        ttk.Label(scrollable_frame, text="Material Quantity (kg):").grid(column=0, row=3, sticky=tk.W)
        self.material_qty = tk.DoubleVar(value=1.0)
        ttk.Entry(scrollable_frame, textvariable=self.material_qty).grid(column=1, row=3, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Additional components frame
        components_frame = ttk.LabelFrame(scrollable_frame, text="Additional Components", padding=10)
        components_frame.grid(column=0, row=4, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Electronics components
        ttk.Label(components_frame, text="Electronic Components:").grid(column=0, row=0, sticky=tk.W)
        self.electronics_var = tk.IntVar(value=1)
        ttk.Entry(components_frame, textvariable=self.electronics_var).grid(column=1, row=0, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Fasteners
        ttk.Label(components_frame, text="Fasteners (units):").grid(column=0, row=1, sticky=tk.W)
        self.fasteners_var = tk.IntVar(value=4)
        ttk.Entry(components_frame, textvariable=self.fasteners_var).grid(column=1, row=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Production parameters frame
        production_frame = ttk.LabelFrame(scrollable_frame, text="Production Parameters", padding=10)
        production_frame.grid(column=0, row=5, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Production time
        ttk.Label(production_frame, text="Production Time (hours):").grid(column=0, row=0, sticky=tk.W)
        self.prod_time = tk.DoubleVar(value=0.5)
        ttk.Entry(production_frame, textvariable=self.prod_time).grid(column=1, row=0, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Energy consumption
        ttk.Label(production_frame, text="Energy Consumption (kWh):").grid(column=0, row=1, sticky=tk.W)
        self.energy_use = tk.DoubleVar(value=2.5)
        ttk.Entry(production_frame, textvariable=self.energy_use).grid(column=1, row=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Setup time (for first unit)
        ttk.Label(production_frame, text="Setup Time (hours):").grid(column=0, row=2, sticky=tk.W)
        self.setup_time = tk.DoubleVar(value=2.0)
        ttk.Entry(production_frame, textvariable=self.setup_time).grid(column=1, row=2, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Production volume
        ttk.Label(scrollable_frame, text="Production Volume:").grid(column=0, row=6, sticky=tk.W)
        self.volume = tk.IntVar(value=1000)
        ttk.Entry(scrollable_frame, textvariable=self.volume).grid(column=1, row=6, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Learning curve (for reduced production time with experience)
        ttk.Label(scrollable_frame, text="Learning Curve (%):").grid(column=0, row=7, sticky=tk.W)
        self.learning_curve = tk.DoubleVar(value=0.0)
        ttk.Scale(scrollable_frame, from_=0, to=30, variable=self.learning_curve, orient=tk.HORIZONTAL)\
            .grid(column=1, row=7, sticky=(tk.W, tk.E), padx=5, pady=2)
        ttk.Label(scrollable_frame, text="0% (no improvement)").grid(column=2, row=7, sticky=tk.W)
        
        # Calculate button
        ttk.Button(scrollable_frame, text="Calculate Costs", command=self.calculate_costs)\
            .grid(column=0, row=8, columnspan=3, pady=20)
        
        # Configure column weights
        scrollable_frame.columnconfigure(1, weight=1)
    
    def toggle_custom_material(self):
        """Enable/disable custom material entry fields"""
        if self.custom_material_var.get():
            self.custom_material_entry.config(state='normal')
            self.custom_material_cost_entry.config(state='normal')
            self.material_var.set('')
        else:
            self.custom_material_entry.config(state='disabled')
            self.custom_material_cost_entry.config(state='disabled')
            self.material_var.set('Steel')
    
    def calculate_costs(self):
        """Perform cost calculations and display results"""
        try:
            # Get input values
            region = self.region_var.get()
            material = self.material_var.get() if not self.custom_material_var.get() else self.custom_material_name.get()
            material_qty = self.material_qty.get()
            electronics = self.electronics_var.get()
            fasteners = self.fasteners_var.get()
            prod_time = self.prod_time.get()
            energy_use = self.energy_use.get()
            setup_time = self.setup_time.get()
            volume = self.volume.get()
            learning_curve = self.learning_curve.get() / 100.0  # Convert to decimal
            
            # Get regional adjustment factor
            region_factor = self.region_adjustments.get(region, 1.0)
            
            # Calculate material cost
            if self.custom_material_var.get():
                material_cost_per_kg = self.custom_material_cost.get()
            else:
                material_cost_per_kg = self.material_costs.get(material, 0)
            
            base_material_cost = material_cost_per_kg * material_qty
            electronics_cost = self.material_costs['Electronics'] * electronics
            fasteners_cost = 0.15 * fasteners  # $0.15 per fastener
            material_cost = (base_material_cost + electronics_cost + fasteners_cost) * (1 + self.material_markup)
            
            # Calculate labor cost (adjusted for US productivity and region)
            adjusted_labor_rate = self.us_hourly_labor_rate * region_factor
            
            # Apply learning curve if applicable
            if learning_curve > 0 and volume > 1:
                # Calculate average time per unit with learning curve
                total_units = volume
                learning_factor = np.log2(learning_curve + 1)
                total_time = setup_time + sum(prod_time * (unit ** -learning_factor) for unit in range(1, total_units + 1))
                avg_time_per_unit = total_time / total_units
            else:
                avg_time_per_unit = (setup_time / volume) + prod_time
            
            labor_cost = (avg_time_per_unit * adjusted_labor_rate) / self.us_productivity_factor
            
            # Calculate energy cost
            energy_cost = energy_use * self.energy_cost
            
            # Calculate overhead
            overhead_cost = labor_cost * self.overhead_rate
            
            # Total cost per unit
            total_unit_cost = material_cost + labor_cost + energy_cost + overhead_cost
            
            # Recommended price with profit margin
            recommended_price = total_unit_cost * (1 + self.profit_margin)
            
            # Update results tab
            self.update_results_tab(total_unit_cost, recommended_price, volume, 
                                  material_cost, labor_cost, energy_cost, overhead_cost)
            
            # Show results tab
            self.notebook.tab(1, state='normal')
            self.notebook.select(1)
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def update_results_tab(self, unit_cost, price, volume, material_cost, labor_cost, energy_cost, overhead_cost):
        """Update the results tab with calculation results"""
        # Clear previous results
        for widget in self.results_tab.winfo_children():
            widget.destroy()
        
        # Main results frame
        main_frame = ttk.Frame(self.results_tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Cost breakdown frame
        breakdown_frame = ttk.LabelFrame(main_frame, text="Cost Breakdown per Unit", padding=10)
        breakdown_frame.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Cost breakdown labels
        ttk.Label(breakdown_frame, text="Material Cost:").grid(column=0, row=0, sticky=tk.W)
        ttk.Label(breakdown_frame, text=f"${material_cost:.2f}").grid(column=1, row=0, sticky=tk.E)
        
        ttk.Label(breakdown_frame, text="Labor Cost:").grid(column=0, row=1, sticky=tk.W)
        ttk.Label(breakdown_frame, text=f"${labor_cost:.2f}").grid(column=1, row=1, sticky=tk.E)
        
        ttk.Label(breakdown_frame, text="Energy Cost:").grid(column=0, row=2, sticky=tk.W)
        ttk.Label(breakdown_frame, text=f"${energy_cost:.2f}").grid(column=1, row=2, sticky=tk.E)
        
        ttk.Label(breakdown_frame, text="Overhead Cost:").grid(column=0, row=3, sticky=tk.W)
        ttk.Label(breakdown_frame, text=f"${overhead_cost:.2f}").grid(column=1, row=3, sticky=tk.E)
        
        ttk.Label(breakdown_frame, text="Total Cost per Unit:", font=('Arial', 10, 'bold'))\
            .grid(column=0, row=4, sticky=tk.W)
        ttk.Label(breakdown_frame, text=f"${unit_cost:.2f}", font=('Arial', 10, 'bold'))\
            .grid(column=1, row=4, sticky=tk.E)
        
        ttk.Label(breakdown_frame, text="Recommended Price:", font=('Arial', 10, 'bold'))\
            .grid(column=0, row=5, sticky=tk.W)
        ttk.Label(breakdown_frame, text=f"${price:.2f}", font=('Arial', 10, 'bold'))\
            .grid(column=1, row=5, sticky=tk.E)
        
        # Volume production frame
        volume_frame = ttk.LabelFrame(main_frame, text=f"Volume Production ({volume} units)", padding=10)
        volume_frame.grid(column=0, row=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Volume calculations
        total_cost = unit_cost * volume
        total_revenue = price * volume
        profit = total_revenue - total_cost
        profit_margin = (profit / total_revenue) * 100 if total_revenue > 0 else 0
        
        ttk.Label(volume_frame, text="Total Production Cost:").grid(column=0, row=0, sticky=tk.W)
        ttk.Label(volume_frame, text=f"${total_cost:,.2f}").grid(column=1, row=0, sticky=tk.E)
        
        ttk.Label(volume_frame, text="Potential Revenue:").grid(column=0, row=1, sticky=tk.W)
        ttk.Label(volume_frame, text=f"${total_revenue:,.2f}").grid(column=1, row=1, sticky=tk.E)
        
        ttk.Label(volume_frame, text="Estimated Profit:").grid(column=0, row=2, sticky=tk.W)
        ttk.Label(volume_frame, text=f"${profit:,.2f}").grid(column=1, row=2, sticky=tk.E)
        
        ttk.Label(volume_frame, text="Profit Margin:").grid(column=0, row=3, sticky=tk.W)
        ttk.Label(volume_frame, text=f"{profit_margin:.1f}%").grid(column=1, row=3, sticky=tk.E)
        
        # Create pie chart of cost breakdown
        self.create_cost_breakdown_chart(main_frame, material_cost, labor_cost, energy_cost, overhead_cost)
        
        # Configure column weights
        breakdown_frame.columnconfigure(1, weight=1)
        volume_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
    
    def create_cost_breakdown_chart(self, parent, material_cost, labor_cost, energy_cost, overhead_cost):
        """Create a pie chart showing cost breakdown"""
        # Prepare data
        labels = ['Materials', 'Labor', 'Energy', 'Overhead']
        sizes = [material_cost, labor_cost, energy_cost, overhead_cost]
        colors = ['#ff9999','#66b3ff','#99ff99','#ffcc99']
        
        # Create figure
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')  # Equal aspect ratio ensures pie is drawn as a circle
        ax.set_title('Cost Breakdown')
        
        # Embed in Tkinter
        chart_frame = ttk.Frame(parent)
        chart_frame.grid(column=0, row=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def edit_economic_data(self):
        """Open dialog to edit economic parameters"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Economic Data")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Labor rate
        ttk.Label(dialog, text="Hourly Labor Rate ($):").grid(column=0, row=0, sticky=tk.W, padx=5, pady=5)
        labor_rate_var = tk.DoubleVar(value=self.us_hourly_labor_rate)
        ttk.Entry(dialog, textvariable=labor_rate_var).grid(column=1, row=0, padx=5, pady=5)
        
        # Productivity factor
        ttk.Label(dialog, text="Productivity Factor:").grid(column=0, row=1, sticky=tk.W, padx=5, pady=5)
        productivity_var = tk.DoubleVar(value=self.us_productivity_factor)
        ttk.Entry(dialog, textvariable=productivity_var).grid(column=1, row=1, padx=5, pady=5)
        
        # Overhead rate
        ttk.Label(dialog, text="Overhead Rate (%):").grid(column=0, row=2, sticky=tk.W, padx=5, pady=5)
        overhead_var = tk.DoubleVar(value=self.overhead_rate * 100)
        ttk.Entry(dialog, textvariable=overhead_var).grid(column=1, row=2, padx=5, pady=5)
        
        # Profit margin
        ttk.Label(dialog, text="Profit Margin (%):").grid(column=0, row=3, sticky=tk.W, padx=5, pady=5)
        profit_var = tk.DoubleVar(value=self.profit_margin * 100)
        ttk.Entry(dialog, textvariable=profit_var).grid(column=1, row=3, padx=5, pady=5)
        
        # Material markup
        ttk.Label(dialog, text="Material Markup (%):").grid(column=0, row=4, sticky=tk.W, padx=5, pady=5)
        markup_var = tk.DoubleVar(value=self.material_markup * 100)
        ttk.Entry(dialog, textvariable=markup_var).grid(column=1, row=4, padx=5, pady=5)
        
        # Energy cost
        ttk.Label(dialog, text="Energy Cost ($/kWh):").grid(column=0, row=5, sticky=tk.W, padx=5, pady=5)
        energy_var = tk.DoubleVar(value=self.energy_cost)
        ttk.Entry(dialog, textvariable=energy_var).grid(column=1, row=5, padx=5, pady=5)
        
        # Save button
        def save_changes():
            self.us_hourly_labor_rate = labor_rate_var.get()
            self.us_productivity_factor = productivity_var.get()
            self.overhead_rate = overhead_var.get() / 100
            self.profit_margin = profit_var.get() / 100
            self.material_markup = markup_var.get() / 100
            self.energy_cost = energy_var.get()
            self.save_economic_data()
            dialog.destroy()
            messagebox.showinfo("Success", "Economic data updated successfully")
        
        ttk.Button(dialog, text="Save", command=save_changes).grid(column=0, row=6, columnspan=2, pady=10)
    
    def edit_material_costs(self):
        """Open dialog to edit material costs"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Material Costs")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Treeview to display and edit materials
        tree_frame = ttk.Frame(dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview
        tree = ttk.Treeview(tree_frame, columns=('Material', 'Cost'), show='headings', yscrollcommand=scrollbar.set)
        tree.heading('Material', text='Material')
        tree.heading('Cost', text='Cost ($/kg)')
        tree.column('Material', width=150)
        tree.column('Cost', width=100)
        tree.pack(fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=tree.yview)
        
        # Populate with current material costs
        for material, cost in self.material_costs.items():
            tree.insert('', 'end', values=(material, cost))
        
        # Controls frame
        controls_frame = ttk.Frame(dialog)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add new material
        ttk.Label(controls_frame, text="New Material:").grid(column=0, row=0, padx=5)
        new_material_var = tk.StringVar()
        ttk.Entry(controls_frame, textvariable=new_material_var).grid(column=1, row=0, padx=5)
        
        ttk.Label(controls_frame, text="Cost:").grid(column=2, row=0, padx=5)
        new_cost_var = tk.DoubleVar()
        ttk.Entry(controls_frame, textvariable=new_cost_var, width=8).grid(column=3, row=0, padx=5)
        
        def add_material():
            material = new_material_var.get().strip()
            cost = new_cost_var.get()
            if material and cost > 0:
                tree.insert('', 'end', values=(material, cost))
                new_material_var.set('')
                new_cost_var.set(0.0)
        
        ttk.Button(controls_frame, text="Add", command=add_material).grid(column=4, row=0, padx=5)
        
        # Remove selected material
        def remove_material():
            selected = tree.selection()
            if selected:
                tree.delete(selected)
        
        ttk.Button(controls_frame, text="Remove Selected", command=remove_material).grid(column=5, row=0, padx=5)
        
        # Save button
        def save_changes():
            # Get all materials from treeview
            self.material_costs = {}
            for child in tree.get_children():
                material, cost = tree.item(child)['values']
                self.material_costs[material] = cost
            
            self.save_material_data()
            dialog.destroy()
            messagebox.showinfo("Success", "Material costs updated successfully")
            
            # Refresh material dropdown in main UI
            self.main_tab.children['!frame'].children['!combobox']['values'] = list(self.material_costs.keys())
        
        ttk.Button(dialog, text="Save", command=save_changes).pack(pady=10)
    
    def save_project(self):
        """Save current project to file"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".wce",
            filetypes=[("Widget Cost Estimator", "*.wce"), ("All Files", "*.*")]
        )
        if filepath:
            try:
                # Gather all input values
                project_data = {
                    'region': self.region_var.get(),
                    'material': self.material_var.get(),
                    'custom_material': self.custom_material_var.get(),
                    'custom_material_name': self.custom_material_name.get(),
                    'custom_material_cost': self.custom_material_cost.get(),
                    'material_qty': self.material_qty.get(),
                    'electronics': self.electronics_var.get(),
                    'fasteners': self.fasteners_var.get(),
                    'prod_time': self.prod_time.get(),
                    'energy_use': self.energy_use.get(),
                    'setup_time': self.setup_time.get(),
                    'volume': self.volume.get(),
                    'learning_curve': self.learning_curve.get()
                }
                
                with open(filepath, 'w') as f:
                    json.dump(project_data, f, indent=4)
                
                messagebox.showinfo("Success", f"Project saved to {filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save project: {str(e)}")
    
    def load_project(self):
        """Load project from file"""
        filepath = filedialog.askopenfilename(
            filetypes=[("Widget Cost Estimator", "*.wce"), ("All Files", "*.*")]
        )
        if filepath:
            try:
                with open(filepath, 'r') as f:
                    project_data = json.load(f)
                
                # Set all input values
                self.region_var.set(project_data.get('region', 'Midwest'))
                self.material_var.set(project_data.get('material', 'Steel'))
                self.custom_material_var.set(project_data.get('custom_material', False))
                self.custom_material_name.set(project_data.get('custom_material_name', ''))
                self.custom_material_cost.set(project_data.get('custom_material_cost', 0.0))
                self.material_qty.set(project_data.get('material_qty', 1.0))
                self.electronics_var.set(project_data.get('electronics', 1))
                self.fasteners_var.set(project_data.get('fasteners', 4))
                self.prod_time.set(project_data.get('prod_time', 0.5))
                self.energy_use.set(project_data.get('energy_use', 2.5))
                self.setup_time.set(project_data.get('setup_time', 2.0))
                self.volume.set(project_data.get('volume', 1000))
                self.learning_curve.set(project_data.get('learning_curve', 0.0))
                
                # Update UI state for custom material
                self.toggle_custom_material()
                
                messagebox.showinfo("Success", f"Project loaded from {filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load project: {str(e)}")
    
    def export_report(self):
        """Export calculation results to PDF or Excel"""
        # This would be implemented with a proper reporting library
        # For now, we'll just show a message
        messagebox.showinfo("Info", "Export functionality would be implemented with a reporting library like ReportLab or pandas Excel export")
    
    def show_cost_breakdown(self):
        """Show detailed cost breakdown"""
        # This would show a more detailed breakdown with subcomponents
        messagebox.showinfo("Info", "Detailed cost breakdown would be shown here")
    
    def show_sensitivity_analysis(self):
        """Show sensitivity analysis for key parameters"""
        # This would show how costs change with variations in inputs
        messagebox.showinfo("Info", "Sensitivity analysis would be shown here")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = AdvancedWidgetCostEstimator()
    app.run()
