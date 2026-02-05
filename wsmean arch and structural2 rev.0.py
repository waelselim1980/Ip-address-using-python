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
current_datetime: datetime = datetime.datetime.now() # Renamed 'd' for clarity
g=str(IPAddr)
w=str('192.168.1.163')
if(g!=w):
    print("License Expired")
    print(1/0)
else:
    print("Software Activated")


class StructuralEngineeringEstimator:
    def __init__(self):
        # Initialize with default construction industry data
        self.load_industry_data()
        self.load_labor_rates()
        
        # Initialize GUI
        self.root = tk.Tk()
        self.root.title("Structural Engineering Cost Estimator")
        self.create_widgets()
        self.setup_menu()
        
    def load_industry_data(self):
        """Load industry data from JSON file or use defaults"""
        try:
            with open('construction_data.json', 'r') as f:
                data = json.load(f)
                self.engineering_rate = data.get('engineering_rate', 125.00)
                self.architectural_rate = data.get('architectural_rate', 95.00)
                self.drafting_rate = data.get('drafting_rate', 45.00)
                self.overhead_rate = data.get('overhead_rate', 0.30)
                self.profit_margin = data.get('profit_margin', 0.25)
                self.region_adjustments = data.get('region_adjustments', {})
                self.project_types = data.get('project_types', {})
        except FileNotFoundError:
            # Default values if file doesn't exist
            self.engineering_rate = 125.00
            self.architectural_rate = 95.00
            self.drafting_rate = 45.00
            self.overhead_rate = 0.30
            self.profit_margin = 0.25
            self.region_adjustments = {
                'Northeast': 1.15,
                'Midwest': 1.00,
                'South': 0.95,
                'West': 1.10
            }
            self.project_types = {
                'Residential': 0.9,
                'Commercial': 1.0,
                'Industrial': 1.2,
                'Infrastructure': 1.3,
                'Institutional': 1.15
            }
    
    def load_labor_rates(self):
        """Load labor rates from CSV file or use defaults"""
        try:
            self.labor_rates = pd.read_csv('labor_rates.csv').set_index('Position').to_dict()['Rate']
        except FileNotFoundError:
            # Default labor rates
            self.labor_rates = {
                'Structural Engineer': 125.00,
                'Architect': 95.00,
                'CAD Technician': 45.00,
                'Project Manager': 85.00,
                'Field Inspector': 65.00,
                'Geotechnical Engineer': 110.00
            }
    
    def save_industry_data(self):
        """Save current industry data to JSON file"""
        data = {
            'engineering_rate': self.engineering_rate,
            'architectural_rate': self.architectural_rate,
            'drafting_rate': self.drafting_rate,
            'overhead_rate': self.overhead_rate,
            'profit_margin': self.profit_margin,
            'region_adjustments': self.region_adjustments,
            'project_types': self.project_types
        }
        with open('construction_data.json', 'w') as f:
            json.dump(data, f, indent=4)
    
    def save_labor_rates(self):
        """Save labor rates to CSV file"""
        pd.DataFrame.from_dict(self.labor_rates, orient='index', columns=['Rate'])\
            .rename_axis('Position').to_csv('labor_rates.csv')
    
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
        edit_menu.add_command(label="Edit Industry Data", command=self.edit_industry_data)
        edit_menu.add_command(label="Edit Labor Rates", command=self.edit_labor_rates)
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
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Project specifications
        ttk.Label(scrollable_frame, text="Project Specifications", font=('Arial', 12, 'bold'))\
            .grid(column=0, row=0, columnspan=3, pady=10, sticky=tk.W)
        
        # Project name
        ttk.Label(scrollable_frame, text="Project Name:").grid(column=0, row=1, sticky=tk.W)
        self.project_name_var = tk.StringVar(value="New Project")
        ttk.Entry(scrollable_frame, textvariable=self.project_name_var).grid(column=1, row=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Project type
        ttk.Label(scrollable_frame, text="Project Type:").grid(column=0, row=2, sticky=tk.W)
        self.project_type_var = tk.StringVar(value='Commercial')
        project_type_combo = ttk.Combobox(scrollable_frame, textvariable=self.project_type_var, 
                                         values=list(self.project_types.keys()))
        project_type_combo.grid(column=1, row=2, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Region selection
        ttk.Label(scrollable_frame, text="Project Region:").grid(column=0, row=3, sticky=tk.W)
        self.region_var = tk.StringVar(value='Midwest')
        region_combo = ttk.Combobox(scrollable_frame, textvariable=self.region_var, 
                                   values=list(self.region_adjustments.keys()))
        region_combo.grid(column=1, row=3, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Project size
        ttk.Label(scrollable_frame, text="Project Size (sq ft):").grid(column=0, row=4, sticky=tk.W)
        self.project_size_var = tk.DoubleVar(value=10000.0)
        ttk.Entry(scrollable_frame, textvariable=self.project_size_var).grid(column=1, row=4, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Complexity factor
        ttk.Label(scrollable_frame, text="Complexity Factor:").grid(column=0, row=5, sticky=tk.W)
        self.complexity_var = tk.DoubleVar(value=1.0)
        ttk.Scale(scrollable_frame, from_=0.5, to=2.0, variable=self.complexity_var, orient=tk.HORIZONTAL)\
            .grid(column=1, row=5, sticky=(tk.W, tk.E), padx=5, pady=2)
        ttk.Label(scrollable_frame, text="1.0 (average)").grid(column=2, row=5, sticky=tk.W)
        
        # Labor frame
        labor_frame = ttk.LabelFrame(scrollable_frame, text="Labor Requirements", padding=10)
        labor_frame.grid(column=0, row=6, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Engineering hours
        ttk.Label(labor_frame, text="Engineering Hours:").grid(column=0, row=0, sticky=tk.W)
        self.engineering_hours_var = tk.DoubleVar(value=80.0)
        ttk.Entry(labor_frame, textvariable=self.engineering_hours_var).grid(column=1, row=0, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Architectural hours
        ttk.Label(labor_frame, text="Architectural Hours:").grid(column=0, row=1, sticky=tk.W)
        self.architectural_hours_var = tk.DoubleVar(value=60.0)
        ttk.Entry(labor_frame, textvariable=self.architectural_hours_var).grid(column=1, row=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Drafting hours
        ttk.Label(labor_frame, text="Drafting Hours:").grid(column=0, row=2, sticky=tk.W)
        self.drafting_hours_var = tk.DoubleVar(value=120.0)
        ttk.Entry(labor_frame, textvariable=self.drafting_hours_var).grid(column=1, row=2, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Additional services frame
        services_frame = ttk.LabelFrame(scrollable_frame, text="Additional Services", padding=10)
        services_frame.grid(column=0, row=7, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Site visits
        ttk.Label(services_frame, text="Site Visits:").grid(column=0, row=0, sticky=tk.W)
        self.site_visits_var = tk.IntVar(value=2)
        ttk.Entry(services_frame, textvariable=self.site_visits_var).grid(column=1, row=0, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Meetings with clients
        ttk.Label(services_frame, text="Client Meetings:").grid(column=0, row=1, sticky=tk.W)
        self.meetings_var = tk.IntVar(value=4)
        ttk.Entry(services_frame, textvariable=self.meetings_var).grid(column=1, row=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        # Permit assistance
        self.permit_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(services_frame, text="Permit Assistance", variable=self.permit_var)\
            .grid(column=0, row=2, sticky=tk.W, columnspan=2)
        
        # Construction admin
        self.construction_admin_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(services_frame, text="Construction Administration", variable=self.construction_admin_var)\
            .grid(column=0, row=3, sticky=tk.W, columnspan=2)
        
        # Calculate button
        ttk.Button(scrollable_frame, text="Calculate Costs", command=self.calculate_costs)\
            .grid(column=0, row=8, columnspan=3, pady=20)
        
        # Configure column weights
        scrollable_frame.columnconfigure(1, weight=1)
    
    def calculate_costs(self):
        """Perform cost calculations and display results"""
        try:
            # Get input values
            project_name = self.project_name_var.get()
            project_type = self.project_type_var.get()
            region = self.region_var.get()
            project_size = self.project_size_var.get()
            complexity = self.complexity_var.get()
            engineering_hours = self.engineering_hours_var.get()
            architectural_hours = self.architectural_hours_var.get()
            drafting_hours = self.drafting_hours_var.get()
            site_visits = self.site_visits_var.get()
            meetings = self.meetings_var.get()
            permit_assistance = self.permit_var.get()
            construction_admin = self.construction_admin_var.get()
            
            # Get adjustment factors
            region_factor = self.region_adjustments.get(region, 1.0)
            project_type_factor = self.project_types.get(project_type, 1.0)
            
            # Calculate labor costs
            engineering_cost = engineering_hours * self.engineering_rate * region_factor
            architectural_cost = architectural_hours * self.architectural_rate * region_factor
            drafting_cost = drafting_hours * self.drafting_rate * region_factor
            
            # Calculate additional services costs
            site_visit_cost = site_visits * 4 * self.engineering_rate * region_factor  # 4 hours per visit
            meeting_cost = meetings * 2 * (self.engineering_rate + self.architectural_rate)/2 * region_factor  # 2 hours per meeting
            permit_cost = 1000 * region_factor if permit_assistance else 0
            admin_cost = 0.15 * (engineering_cost + architectural_cost) if construction_admin else 0
            
            # Calculate total direct costs
            direct_costs = (engineering_cost + architectural_cost + drafting_cost + 
                           site_visit_cost + meeting_cost + permit_cost + admin_cost)
            
            # Apply complexity factor
            direct_costs *= complexity
            
            # Apply project type factor
            direct_costs *= project_type_factor
            
            # Calculate overhead
            overhead = direct_costs * self.overhead_rate
            
            # Total cost
            total_cost = direct_costs + overhead
            
            # Recommended fee with profit margin
            recommended_fee = total_cost * (1 + self.profit_margin)
            
            # Cost per square foot
            cost_per_sqft = recommended_fee / project_size if project_size > 0 else 0
            
            # Update results tab
            self.update_results_tab(project_name, total_cost, recommended_fee, cost_per_sqft,
                                  engineering_cost, architectural_cost, drafting_cost,
                                  site_visit_cost, meeting_cost, permit_cost, admin_cost,
                                  overhead)
            
            # Show results tab
            self.notebook.tab(1, state='normal')
            self.notebook.select(1)
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
    
    def update_results_tab(self, project_name, total_cost, recommended_fee, cost_per_sqft,
                         engineering_cost, architectural_cost, drafting_cost,
                         site_visit_cost, meeting_cost, permit_cost, admin_cost, overhead):
        """Update the results tab with calculation results"""
        # Clear previous results
        for widget in self.results_tab.winfo_children():
            widget.destroy()
        
        # Main results frame
        main_frame = ttk.Frame(self.results_tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Project info frame
        project_frame = ttk.LabelFrame(main_frame, text=f"Project: {project_name}", padding=10)
        project_frame.grid(column=0, row=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Cost breakdown frame
        breakdown_frame = ttk.LabelFrame(main_frame, text="Cost Breakdown", padding=10)
        breakdown_frame.grid(column=0, row=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        
        # Cost breakdown labels
        ttk.Label(breakdown_frame, text="Engineering:").grid(column=0, row=0, sticky=tk.W)
        ttk.Label(breakdown_frame, text=f"${engineering_cost:,.2f}").grid(column=1, row=0, sticky=tk.E)
        
        ttk.Label(breakdown_frame, text="Architectural:").grid(column=0, row=1, sticky=tk.W)
        ttk.Label(breakdown_frame, text=f"${architectural_cost:,.2f}").grid(column=1, row=1, sticky=tk.E)
        
        ttk.Label(breakdown_frame, text="Drafting:").grid(column=0, row=2, sticky=tk.W)
        ttk.Label(breakdown_frame, text=f"${drafting_cost:,.2f}").grid(column=1, row=2, sticky=tk.E)
        
        ttk.Label(breakdown_frame, text="Site Visits:").grid(column=0, row=3, sticky=tk.W)
        ttk.Label(breakdown_frame, text=f"${site_visit_cost:,.2f}").grid(column=1, row=3, sticky=tk.E)
        
        ttk.Label(breakdown_frame, text="Client Meetings:").grid(column=0, row=4, sticky=tk.W)
        ttk.Label(breakdown_frame, text=f"${meeting_cost:,.2f}").grid(column=1, row=4, sticky=tk.E)
        
        ttk.Label(breakdown_frame, text="Permit Assistance:").grid(column=0, row=5, sticky=tk.W)
        ttk.Label(breakdown_frame, text=f"${permit_cost:,.2f}").grid(column=1, row=5, sticky=tk.E)
        
        ttk.Label(breakdown_frame, text="Construction Admin:").grid(column=0, row=6, sticky=tk.W)
        ttk.Label(breakdown_frame, text=f"${admin_cost:,.2f}").grid(column=1, row=6, sticky=tk.E)
        
        ttk.Label(breakdown_frame, text="Overhead:", font=('Arial', 10, 'bold'))\
            .grid(column=0, row=7, sticky=tk.W)
        ttk.Label(breakdown_frame, text=f"${overhead:,.2f}", font=('Arial', 10, 'bold'))\
            .grid(column=1, row=7, sticky=tk.E)
        
        ttk.Label(breakdown_frame, text="Total Cost:", font=('Arial', 10, 'bold'))\
            .grid(column=0, row=8, sticky=tk.W)
        ttk.Label(breakdown_frame, text=f"${total_cost:,.2f}", font=('Arial', 10, 'bold'))\
            .grid(column=1, row=8, sticky=tk.E)
        
        ttk.Label(breakdown_frame, text="Recommended Fee:", font=('Arial', 10, 'bold'))\
            .grid(column=0, row=9, sticky=tk.W)
        ttk.Label(breakdown_frame, text=f"${recommended_fee:,.2f}", font=('Arial', 10, 'bold'))\
            .grid(column=1, row=9, sticky=tk.E)
        
        ttk.Label(breakdown_frame, text="Cost per sq ft:", font=('Arial', 10, 'bold'))\
            .grid(column=0, row=10, sticky=tk.W)
        ttk.Label(breakdown_frame, text=f"${cost_per_sqft:,.2f}", font=('Arial', 10, 'bold'))\
            .grid(column=1, row=10, sticky=tk.E)
        
        # Create pie chart of cost breakdown
        self.create_cost_breakdown_chart(main_frame, engineering_cost, architectural_cost, 
                                       drafting_cost, site_visit_cost, meeting_cost, 
                                       permit_cost, admin_cost, overhead)
        
        # Configure column weights
        breakdown_frame.columnconfigure(1, weight=1)
        project_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
    
    def create_cost_breakdown_chart(self, parent, engineering, architectural, drafting, 
                                  site_visits, meetings, permits, admin, overhead):
        """Create a pie chart showing cost breakdown"""
        # Prepare data - group smaller items into "Other"
        threshold = 0.05 * (engineering + architectural + drafting + site_visits + 
                           meetings + permits + admin + overhead)
        
        labels = ['Engineering', 'Architectural', 'Drafting']
        sizes = [engineering, architectural, drafting]
        colors = ['#ff9999','#66b3ff','#99ff99']
        
        # Add other items if they're significant
        other = 0
        if site_visits > threshold:
            labels.append('Site Visits')
            sizes.append(site_visits)
            colors.append('#ffcc99')
        else:
            other += site_visits
            
        if meetings > threshold:
            labels.append('Meetings')
            sizes.append(meetings)
            colors.append('#c2c2f0')
        else:
            other += meetings
            
        if permits > threshold:
            labels.append('Permits')
            sizes.append(permits)
            colors.append('#ffb3e6')
        else:
            other += permits
            
        if admin > threshold:
            labels.append('Admin')
            sizes.append(admin)
            colors.append('#c2f0c2')
        else:
            other += admin
            
        if overhead > threshold:
            labels.append('Overhead')
            sizes.append(overhead)
            colors.append('#ff6666')
        else:
            other += overhead
            
        if other > 0:
            labels.append('Other')
            sizes.append(other)
            colors.append('#d3d3d3')
        
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
    
    def edit_industry_data(self):
        """Open dialog to edit industry parameters"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Industry Data")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Engineering rate
        ttk.Label(dialog, text="Engineering Rate ($/hr):").grid(column=0, row=0, sticky=tk.W, padx=5, pady=5)
        engineering_var = tk.DoubleVar(value=self.engineering_rate)
        ttk.Entry(dialog, textvariable=engineering_var).grid(column=1, row=0, padx=5, pady=5)
        
        # Architectural rate
        ttk.Label(dialog, text="Architectural Rate ($/hr):").grid(column=0, row=1, sticky=tk.W, padx=5, pady=5)
        architectural_var = tk.DoubleVar(value=self.architectural_rate)
        ttk.Entry(dialog, textvariable=architectural_var).grid(column=1, row=1, padx=5, pady=5)
        
        # Drafting rate
        ttk.Label(dialog, text="Drafting Rate ($/hr):").grid(column=0, row=2, sticky=tk.W, padx=5, pady=5)
        drafting_var = tk.DoubleVar(value=self.drafting_rate)
        ttk.Entry(dialog, textvariable=drafting_var).grid(column=1, row=2, padx=5, pady=5)
        
        # Overhead rate
        ttk.Label(dialog, text="Overhead Rate (%):").grid(column=0, row=3, sticky=tk.W, padx=5, pady=5)
        overhead_var = tk.DoubleVar(value=self.overhead_rate * 100)
        ttk.Entry(dialog, textvariable=overhead_var).grid(column=1, row=3, padx=5, pady=5)
        
        # Profit margin
        ttk.Label(dialog, text="Profit Margin (%):").grid(column=0, row=4, sticky=tk.W, padx=5, pady=5)
        profit_var = tk.DoubleVar(value=self.profit_margin * 100)
        ttk.Entry(dialog, textvariable=profit_var).grid(column=1, row=4, padx=5, pady=5)
        
        # Save button
        def save_changes():
            self.engineering_rate = engineering_var.get()
            self.architectural_rate = architectural_var.get()
            self.drafting_rate = drafting_var.get()
            self.overhead_rate = overhead_var.get() / 100
            self.profit_margin = profit_var.get() / 100
            self.save_industry_data()
            dialog.destroy()
            messagebox.showinfo("Success", "Industry data updated successfully")
        
        ttk.Button(dialog, text="Save", command=save_changes).grid(column=0, row=5, columnspan=2, pady=10)
    
    def edit_labor_rates(self):
        """Open dialog to edit labor rates"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Labor Rates")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Treeview to display and edit labor rates
        tree_frame = ttk.Frame(dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview
        tree = ttk.Treeview(tree_frame, columns=('Position', 'Rate'), show='headings', yscrollcommand=scrollbar.set)
        tree.heading('Position', text='Position')
        tree.heading('Rate', text='Rate ($/hr)')
        tree.column('Position', width=150)
        tree.column('Rate', width=100)
        tree.pack(fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=tree.yview)
        
        # Populate with current labor rates
        for position, rate in self.labor_rates.items():
            tree.insert('', 'end', values=(position, rate))
        
        # Controls frame
        controls_frame = ttk.Frame(dialog)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add new position
        ttk.Label(controls_frame, text="New Position:").grid(column=0, row=0, padx=5)
        new_position_var = tk.StringVar()
        ttk.Entry(controls_frame, textvariable=new_position_var).grid(column=1, row=0, padx=5)
        
        ttk.Label(controls_frame, text="Rate:").grid(column=2, row=0, padx=5)
        new_rate_var = tk.DoubleVar()
        ttk.Entry(controls_frame, textvariable=new_rate_var, width=8).grid(column=3, row=0, padx=5)
        
        def add_position():
            position = new_position_var.get().strip()
            rate = new_rate_var.get()
            if position and rate > 0:
                tree.insert('', 'end', values=(position, rate))
                new_position_var.set('')
                new_rate_var.set(0.0)
        
        ttk.Button(controls_frame, text="Add", command=add_position).grid(column=4, row=0, padx=5)
        
        # Remove selected position
        def remove_position():
            selected = tree.selection()
            if selected:
                tree.delete(selected)
        
        ttk.Button(controls_frame, text="Remove Selected", command=remove_position).grid(column=5, row=0, padx=5)
        
        # Save button
        def save_changes():
            # Get all positions from treeview
            self.labor_rates = {}
            for child in tree.get_children():
                position, rate = tree.item(child)['values']
                self.labor_rates[position] = rate
            
            self.save_labor_rates()
            dialog.destroy()
            messagebox.showinfo("Success", "Labor rates updated successfully")
        
        ttk.Button(dialog, text="Save", command=save_changes).pack(pady=10)
    
    def save_project(self):
        """Save current project to file"""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".see",
            filetypes=[("Structural Engineering Estimator", "*.see"), ("All Files", "*.*")]
        )
        if filepath:
            try:
                # Gather all input values
                project_data = {
                    'project_name': self.project_name_var.get(),
                    'project_type': self.project_type_var.get(),
                    'region': self.region_var.get(),
                    'project_size': self.project_size_var.get(),
                    'complexity': self.complexity_var.get(),
                    'engineering_hours': self.engineering_hours_var.get(),
                    'architectural_hours': self.architectural_hours_var.get(),
                    'drafting_hours': self.drafting_hours_var.get(),
                    'site_visits': self.site_visits_var.get(),
                    'meetings': self.meetings_var.get(),
                    'permit_assistance': self.permit_var.get(),
                    'construction_admin': self.construction_admin_var.get()
                }
                
                with open(filepath, 'w') as f:
                    json.dump(project_data, f, indent=4)
                
                messagebox.showinfo("Success", f"Project saved to {filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save project: {str(e)}")
    
    def load_project(self):
        """Load project from file"""
        filepath = filedialog.askopenfilename(
            filetypes=[("Structural Engineering Estimator", "*.see"), ("All Files", "*.*")]
        )
        if filepath:
            try:
                with open(filepath, 'r') as f:
                    project_data = json.load(f)
                
                # Set all input values
                self.project_name_var.set(project_data.get('project_name', 'New Project'))
                self.project_type_var.set(project_data.get('project_type', 'Commercial'))
                self.region_var.set(project_data.get('region', 'Midwest'))
                self.project_size_var.set(project_data.get('project_size', 10000.0))
                self.complexity_var.set(project_data.get('complexity', 1.0))
                self.engineering_hours_var.set(project_data.get('engineering_hours', 80.0))
                self.architectural_hours_var.set(project_data.get('architectural_hours', 60.0))
                self.drafting_hours_var.set(project_data.get('drafting_hours', 120.0))
                self.site_visits_var.set(project_data.get('site_visits', 2))
                self.meetings_var.set(project_data.get('meetings', 4))
                self.permit_var.set(project_data.get('permit_assistance', False))
                self.construction_admin_var.set(project_data.get('construction_admin', False))
                
                messagebox.showinfo("Success", f"Project loaded from {filepath}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load project: {str(e)}")
    
    def export_report(self):
        """Export calculation results to PDF or Excel"""
        # This would be implemented with a proper reporting library
        messagebox.showinfo("Info", "Export functionality would generate a detailed report with tables and charts")
    
    def show_cost_breakdown(self):
        """Show detailed cost breakdown"""
        messagebox.showinfo("Info", "Detailed cost breakdown with subcategories would be shown here")
    
    def show_sensitivity_analysis(self):
        """Show sensitivity analysis for key parameters"""
        messagebox.showinfo("Info", "Sensitivity analysis showing how costs change with variations in inputs")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = StructuralEngineeringEstimator()
    app.run()
