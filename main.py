from datetime import datetime, timedelta
import json
import math
import os
import re
import threading
import time
from tkinter import messagebox
import webbrowser
import customtkinter as ctk
from customtkinter import filedialog
from geopy.geocoders import ArcGIS
import pandas as pd
from pypdf import PdfReader
import requests
from tkintermapview import TkinterMapView

# Theme settings
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

VEHICLES_FILE = "vehicles.json"

# Polish/English translation dictionary
TRANSLATIONS = {
    "pl": {
        "app_title": "Optymalizator tras - automaty z butelkami",
        "logo": "Planowanie tras",
        "vehicle_section": "Pojazd i kierowca:",
        "vehicle_placeholder": "-- Wybierz pojazd --",
        "fleet_btn": "Flota",
        "route_name": "1. Nazwa trasy (opcjonalnie):",
        "route_name_placeholder": "np. Trasa Śląsk - Jan Kowalski",
        "start_point": "2. Punkt startowy (baza):",
        "start_placeholder": "np. ul. Sportowa 1, Chorzów",
        "set_start": "Ustaw bazę",
        "dropoff_points": "3. Strefy zrzutu (można dodać kilka):",
        "dropoff_placeholder": "np. ul. Katowicka 5, Chorzów",
        "add_dropoff": "Dodaj strefę zrzutu",
        "dropoffs_none": "Dodane zrzuty: Brak",
        "dropoffs_added": "Dodane zrzuty",
        "max_capacity": "Max worków\n(240L):",
        "start_time": "Start:",
        "stop_time": "Postój\n(min):",
        "load_orders": "5. Wgraj pliki zleceń (.pdf / .xlsx / .csv):",
        "btn_load": "Wgraj zlecenia (PDF / Excel)",
        "bags_frame_title": "Liczba worków na sklepach | 240L | 1000L | Inne |:",
        "generate_route": "Generuj optymalną trasę",
        "open_gmaps": "Otwórz w Google Maps",
        "export_txt": "Zapisz plan trasy (.txt)",
        "status_ready": "Status: Ustaw punkty lub wgraj pliki...",
        "no_route": "Brak wyznaczonej trasy.",
        "other_bags": "Inne",
        "base_tag": "BAZA",
        "dropoff_tag": "STREFA ZRZUTU",
        "save_dialog_title": "Zapisz plan trasy",
        "filetype_desc": "Plik Tekstowy",
        "filetype_orders": "Pliki zleceń (.pdf, .xlsx, .csv)",
        "txt_plan_header": "PLAN TRASY",
        "txt_gmaps_link": "Link do Google Maps:",
        "alert_change_veh_title": "Zmiana pojazdu",
        "alert_change_veh_msg": "Wyznaczenie trasy dotyczy innego pojazdu.\nCzy na pewno chcesz zmienić pojazd i zresetować obecną trasę?",
        "status_enter_base": "Wpisz adres bazy!",
        "status_search_base": "Szukam adresu bazy...",
        "status_base_set": "Ustawiono bazę!",
        "status_base_not_found": "Nie znaleziono adresu bazy!",
        "status_base_err": "Błąd bazy:",
        "status_enter_dropoff": "Wpisz adres strefy zrzutu!",
        "status_search_dropoff": "Szukam strefy zrzutu...",
        "status_dropoff_added": "Dodano strefę zrzutu!",
        "status_dropoff_not_found": "Nie znaleziono strefy zrzutu!",
        "status_dropoff_err": "Błąd strefy zrzutu:",
        "status_reading_files": "Odczytywanie plików zleceń...",
        "status_geocoding": "Szukam na mapie",
        "status_loaded_pts": "Załadowano {count} z {total} punktów ze zleceń!",
        "status_read_err": "Błąd odczytu:",
        "status_saved_txt": "Zapisano plan do pliku!",
        "status_save_err": "Błąd zapisu:",
        "status_load_files_first": "Wgraj najpierw pliki zleceń!",
        "status_optimizing": "Optymalizacja kursów...",
        "status_set_base_first": "Ustaw najpierw punkt startowy (Bazę)!",
        "status_add_dropoff_first": "Dodaj przynajmniej 1 strefę zrzutu!",
        "status_osrm_err": "Błąd API OSRM!",
        "status_opt_err": "Błąd optymalizacji:",
        "status_calc_success": "Wyznaczono {trips} kursy!\nDystans: {dist:.1f} km | Czas pracy: {hours}h {mins}m",
        "route_prefix": "Trasa - ",
        "rep_route": "TRASA",
        "rep_plan": "Plan Przejazdu",
        "rep_trips": "Liczba kursów",
        "rep_cap": "Pojemność vana",
        "rep_bags": "worków (240L)",
        "rep_trip": "KURS",
        "rep_load": "Załadunek",
        "rep_eq": "ekwiwalentu 240L",
        "rep_start": "START",
        "rep_arr": "Przyjazd",
        "rep_dep": "Odjazd",
        "rep_drop": "ZRZUT",
        "rep_unloading": "(Rozładunek kursu)",
        "rep_tot_dist": "Dystans łączny",
        "rep_tot_time": "Łączny czas pracy",
        "rep_drive": "Jazda",
        "rep_stops": "Postoje",
        "fleet_win_title": "Zarządzanie flotą pojazdów i kierowcami",
        "fleet_header": "Baza pojazdów i kierowców",
        "fleet_empty": "Brak zapisanych pojazdów w bazie. Dodaj pierwszy poniżej.",
        "fleet_car": "Samochód",
        "fleet_driver": "Kierowca",
        "fleet_cap": "Pojemność podana w workach (240L)",
        "fleet_del": "Usuń",
        "fleet_edit": "Edytuj",
        "fleet_lbl_veh": "Pojazd / rejestracja:",
        "fleet_lbl_driver": "Kierowca:",
        "fleet_lbl_cap": "Pojemność (worki 240L):",
        "fleet_btn_add": "Dodaj nowy pojazd",
        "fleet_btn_save_changes": "Zapisz zmiany w pojeździe",
    },
    "en": {
        "app_title": "Route Optimizer - Bottle Return VRP",
        "logo": "Route Planner",
        "vehicle_section": "Vehicle and driver:",
        "vehicle_placeholder": "-- Choose vehicle --",
        "fleet_btn": "Fleet",
        "route_name": "1. Route Name (optional):",
        "route_name_placeholder": "e.g. Route Silesia - John Doe",
        "start_point": "2. Starting Point (Depot):",
        "start_placeholder": "e.g. 1 High Street, City",
        "set_start": "Set Depot",
        "dropoff_points": "3. Disposal Points (multiple allowed):",
        "dropoff_placeholder": "e.g. 5 Central Road, City",
        "add_dropoff": "Add Disposal Site",
        "dropoffs_none": "Added dropoffs: None",
        "dropoffs_added": "Added dropoffs",
        "max_capacity": "Max bags\n(240L):",
        "start_time": "Start:",
        "stop_time": "Stop\n(min):",
        "load_orders": "5. Load Order Files (.pdf / .xlsx / .csv):",
        "btn_load": "Load Orders (PDF / Excel)",
        "bags_frame_title": "Bag counts per store | 240L | 1000L | Other |:",
        "generate_route": "Generate Optimal Route",
        "open_gmaps": "Open in Google Maps",
        "export_txt": "Export Route Plan (.txt)",
        "status_ready": "Status: Set points or load files...",
        "no_route": "No route generated.",
        "other_bags": "Other",
        "base_tag": "DEPOT",
        "dropoff_tag": "DISPOSAL SITE",
        "save_dialog_title": "Save route plan",
        "filetype_desc": "Text File",
        "filetype_orders": "Order files (.pdf, .xlsx, .csv)",
        "txt_plan_header": "ROUTE PLAN",
        "txt_gmaps_link": "Google Maps Link:",
        "alert_change_veh_title": "Change vehicle",
        "alert_change_veh_msg": "Route is planned for another vehicle.\nAre you sure you want to change vehicle and reset current route?",
        "status_enter_base": "Enter depot address!",
        "status_search_base": "Searching depot address...",
        "status_base_set": "Depot set!",
        "status_base_not_found": "Depot address not found!",
        "status_base_err": "Depot error:",
        "status_enter_dropoff": "Enter disposal address!",
        "status_search_dropoff": "Searching disposal site...",
        "status_dropoff_added": "Disposal site added!",
        "status_dropoff_not_found": "Disposal site not found!",
        "status_dropoff_err": "Disposal error:",
        "status_reading_files": "Reading order files...",
        "status_geocoding": "Geocoding",
        "status_loaded_pts": "Loaded {count} of {total} order stops!",
        "status_read_err": "Read error:",
        "status_saved_txt": "Route plan saved!",
        "status_save_err": "Save error:",
        "status_load_files_first": "Please load order files first!",
        "status_optimizing": "Optimizing trips...",
        "status_set_base_first": "Set Starting Point (Depot) first!",
        "status_add_dropoff_first": "Add at least 1 disposal site!",
        "status_osrm_err": "OSRM API error!",
        "status_opt_err": "Optimization error:",
        "status_calc_success": "Calculated {trips} trips!\nDistance: {dist:.1f} km | Total time: {hours}h {mins}m",
        "route_prefix": "Route - ",
        "rep_route": "ROUTE",
        "rep_plan": "Trip Plan",
        "rep_trips": "Trips count",
        "rep_cap": "Van capacity",
        "rep_bags": "bags (240L)",
        "rep_trip": "TRIP",
        "rep_load": "Load",
        "rep_eq": "240L equiv",
        "rep_start": "START",
        "rep_arr": "Arrival",
        "rep_dep": "Departure",
        "rep_drop": "DROPOFF",
        "rep_unloading": "(Trip unloading)",
        "rep_tot_dist": "Total Distance",
        "rep_tot_time": "Total Work Duration",
        "rep_drive": "Driving",
        "rep_stops": "Stops",
        "fleet_win_title": "Fleet and Driver Management",
        "fleet_header": "Vehicles and Drivers Database",
        "fleet_empty": "No vehicles saved in database. Add the first one below.",
        "fleet_car": "Vehicle",
        "fleet_driver": "Driver",
        "fleet_cap": "Capacity in bags (240L)",
        "fleet_del": "Delete",
        "fleet_edit": "Edit",
        "fleet_lbl_veh": "Vehicle / Plate:",
        "fleet_lbl_driver": "Driver:",
        "fleet_lbl_cap": "Capacity (240L bags):",
        "fleet_btn_add": "Add New Vehicle",
        "fleet_btn_save_changes": "Save Changes",
    }
}


class VehicleManagerWindow(ctk.CTkToplevel):
    """Separate window for vehicle fleet management (Add / Edit / Delete)"""

    def __init__(self, parent_app):
        super().__init__(parent_app)

        self.parent_app = parent_app
        lang = self.parent_app.current_lang
        t = TRANSLATIONS[lang]

        self.title(t["fleet_win_title"])
        self.geometry("580x600")
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        # Header
        self.lbl_title = ctk.CTkLabel(
            self,
            text=t["fleet_header"],
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self.lbl_title.grid(row=0, column=0, padx=15, pady=(15, 5))

        # Vehicle list (Scrollable)
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=5)

        # Add / edit form
        self.form_frame = ctk.CTkFrame(self)
        self.form_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(5, 15))
        self.form_frame.grid_columnconfigure(1, weight=1)

        self.lbl_name = ctk.CTkLabel(self.form_frame, text=t["fleet_lbl_veh"])
        self.lbl_name.grid(row=0, column=0, padx=8, pady=5, sticky="w")
        self.entry_name = ctk.CTkEntry(
            self.form_frame, placeholder_text="np. Sprinter (ST 12345)"
        )
        self.entry_name.grid(row=0, column=1, padx=8, pady=5, sticky="ew")

        self.lbl_driver = ctk.CTkLabel(self.form_frame, text=t["fleet_lbl_driver"])
        self.lbl_driver.grid(row=1, column=0, padx=8, pady=5, sticky="w")
        self.entry_driver = ctk.CTkEntry(
            self.form_frame, placeholder_text="np. Jan Kowalski"
        )
        self.entry_driver.grid(row=1, column=1, padx=8, pady=5, sticky="ew")

        self.lbl_cap = ctk.CTkLabel(self.form_frame, text=t["fleet_lbl_cap"])
        self.lbl_cap.grid(row=2, column=0, padx=8, pady=5, sticky="w")
        self.entry_cap = ctk.CTkEntry(self.form_frame, placeholder_text="24")
        self.entry_cap.grid(row=2, column=1, padx=8, pady=5, sticky="ew")

        # Save/Add button
        self.btn_save = ctk.CTkButton(
            self.form_frame,
            text=t["fleet_btn_add"],
            fg_color="green",
            hover_color="darkgreen",
            height=35,
            command=self.save_vehicle,
        )
        self.btn_save.grid(row=3, column=0, columnspan=2, padx=8, pady=10, sticky="ew")

        self.selected_vehicle_id = None
        self.refresh_list()

    def refresh_list(self):
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        t = TRANSLATIONS[self.parent_app.current_lang]
        vehicles = self.parent_app.vehicles

        if not vehicles:
            ctk.CTkLabel(
                self.scroll_frame, text=t["fleet_empty"]
            ).pack(pady=20)
            return

        for v_id, v_data in vehicles.items():
            card = ctk.CTkFrame(self.scroll_frame)
            card.pack(fill="x", pady=4, padx=5)

            info_text = f"{t['fleet_car']}: {v_data['name']}\n{t['fleet_driver']}: {v_data['driver']}\n{t['fleet_cap']}: {v_data['capacity']}"
            lbl = ctk.CTkLabel(
                card, text=info_text, justify="left", font=ctk.CTkFont(size=12)
            )
            lbl.pack(side="left", padx=10, pady=8)

            btn_del = ctk.CTkButton(
                card,
                text=t["fleet_del"],
                width=55,
                fg_color="#EA4335",
                hover_color="#B31412",
                command=lambda id_to_del=v_id: self.delete_vehicle(id_to_del),
            )
            btn_del.pack(side="right", padx=5)

            btn_edit = ctk.CTkButton(
                card,
                text=t["fleet_edit"],
                width=55,
                fg_color="#3B82F6",
                hover_color="#1D4ED8",
                command=lambda id_to_edit=v_id: self.load_to_edit(id_to_edit),
            )
            btn_edit.pack(side="right", padx=2)

    def load_to_edit(self, v_id):
        v = self.parent_app.vehicles.get(v_id)
        if not v:
            return
        t = TRANSLATIONS[self.parent_app.current_lang]
        self.selected_vehicle_id = v_id
        self.entry_name.delete(0, "end")
        self.entry_name.insert(0, v["name"])

        self.entry_driver.delete(0, "end")
        self.entry_driver.insert(0, v["driver"])

        self.entry_cap.delete(0, "end")
        self.entry_cap.insert(0, str(v["capacity"]))

        self.btn_save.configure(
            text=t["fleet_btn_save_changes"], fg_color="#EAB308"
        )

    def save_vehicle(self):
        name = self.entry_name.get().strip()
        driver = self.entry_driver.get().strip()
        cap_str = self.entry_cap.get().strip()

        if not name or not driver or not cap_str:
            return

        try:
            cap = int(cap_str)
        except ValueError:
            return

        if self.selected_vehicle_id:
            v_id = self.selected_vehicle_id
        else:
            v_id = str(int(time.time() * 1000))

        self.parent_app.vehicles[v_id] = {
            "name": name,
            "driver": driver,
            "capacity": cap,
        }

        self.parent_app.save_vehicles_to_file()
        self.selected_vehicle_id = None

        t = TRANSLATIONS[self.parent_app.current_lang]
        self.entry_name.delete(0, "end")
        self.entry_driver.delete(0, "end")
        self.entry_cap.delete(0, "end")
        self.btn_save.configure(text=t["fleet_btn_add"], fg_color="green")

        self.refresh_list()

    def delete_vehicle(self, v_id):
        if v_id in self.parent_app.vehicles:
            del self.parent_app.vehicles[v_id]
            self.parent_app.save_vehicles_to_file()
            self.refresh_list()


class RoutePlannerApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.current_lang = "pl"
        self.title(TRANSLATIONS["pl"]["app_title"])
        self.geometry("1350x980")

        self.vehicles = {}
        self.load_vehicles_from_file()

        self.start_point = None  # Base / Depot
        self.dropoff_points = []  # List of available dropoff zones
        self.loaded_points = []  # Reverse vending machines (pickup points)
        self.ordered_points_list = []  # Sorted points after optimization
        self.current_selected_vehicle_str = TRANSLATIONS["pl"]["vehicle_placeholder"]

        self.start_marker = None
        self.current_paths = []
        self.gmaps_url = None
        self.geolocator = ArcGIS(user_agent="bottle_route_planner")

        # Layout (1 row, 2 columns)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=400, corner_radius=0)
        self.sidebar_frame.grid(
            row=0, column=0, sticky="nsew", padx=10, pady=10
        )

        # Header frame with logo and language selector
        self.header_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.header_frame.pack(padx=15, pady=(15, 10), fill="x")

        self.logo_label = ctk.CTkLabel(
            self.header_frame,
            text=TRANSLATIONS["pl"]["logo"],
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.logo_label.pack(side="left", anchor="w")

        self.lang_option_menu = ctk.CTkOptionMenu(
            self.header_frame,
            values=["PL", "EN"],
            width=65,
            command=self.change_language,
        )
        self.lang_option_menu.set("PL")
        self.lang_option_menu.pack(side="right")

        # Vehicle selection from database
        self.vehicle_section_label = ctk.CTkLabel(
            self.sidebar_frame,
            text=TRANSLATIONS["pl"]["vehicle_section"],
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.vehicle_section_label.pack(padx=15, pady=(2, 2), anchor="w")

        veh_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        veh_frame.pack(padx=15, pady=(0, 6), fill="x")

        self.vehicle_option_menu = ctk.CTkOptionMenu(
            veh_frame,
            values=[TRANSLATIONS["pl"]["vehicle_placeholder"]],
            command=self.on_vehicle_selected,
        )
        self.vehicle_option_menu.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_manage_vehicles = ctk.CTkButton(
            veh_frame,
            text=TRANSLATIONS["pl"]["fleet_btn"],
            width=80,
            fg_color="#8E24AA",
            hover_color="#6A1B9A",
            command=self.open_vehicle_manager,
        )
        self.btn_manage_vehicles.pack(side="right")

        # Route name
        self.route_name_label = ctk.CTkLabel(
            self.sidebar_frame,
            text=TRANSLATIONS["pl"]["route_name"],
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.route_name_label.pack(padx=15, pady=(2, 2), anchor="w")

        self.route_name_entry = ctk.CTkEntry(
            self.sidebar_frame,
            placeholder_text=TRANSLATIONS["pl"]["route_name_placeholder"],
        )
        self.route_name_entry.pack(padx=15, pady=(2, 6), fill="x")

        # Base/depot
        self.start_label = ctk.CTkLabel(
            self.sidebar_frame,
            text=TRANSLATIONS["pl"]["start_point"],
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.start_label.pack(padx=15, pady=(2, 2), anchor="w")

        self.start_entry = ctk.CTkEntry(
            self.sidebar_frame,
            placeholder_text=TRANSLATIONS["pl"]["start_placeholder"],
        )
        self.start_entry.pack(padx=15, pady=2, fill="x")

        self.btn_set_start = ctk.CTkButton(
            self.sidebar_frame,
            text=TRANSLATIONS["pl"]["set_start"],
            fg_color="#3B82F6",
            hover_color="#1D4ED8",
            command=self.set_start_point,
        )
        self.btn_set_start.pack(padx=15, pady=(2, 6))

        # Dropoff zones
        self.dropoff_label = ctk.CTkLabel(
            self.sidebar_frame,
            text=TRANSLATIONS["pl"]["dropoff_points"],
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.dropoff_label.pack(padx=15, pady=(2, 2), anchor="w")

        self.dropoff_entry = ctk.CTkEntry(
            self.sidebar_frame,
            placeholder_text=TRANSLATIONS["pl"]["dropoff_placeholder"],
        )
        self.dropoff_entry.pack(padx=15, pady=2, fill="x")

        self.btn_add_dropoff = ctk.CTkButton(
            self.sidebar_frame,
            text=TRANSLATIONS["pl"]["add_dropoff"],
            fg_color="#EAB308",
            hover_color="#CA8A04",
            command=self.add_dropoff_point,
        )
        self.btn_add_dropoff.pack(padx=15, pady=(2, 4))

        self.dropoff_list_label = ctk.CTkLabel(
            self.sidebar_frame,
            text=TRANSLATIONS["pl"]["dropoffs_none"],
            text_color="gray",
            font=ctk.CTkFont(size=11),
            wraplength=340,
        )
        self.dropoff_list_label.pack(padx=15, pady=(0, 6))

        # Capacity and time
        self.param_frame = ctk.CTkFrame(
            self.sidebar_frame, fg_color="transparent"
        )
        self.param_frame.pack(padx=15, pady=2, fill="x")

        self.capacity_label = ctk.CTkLabel(
            self.param_frame,
            text=TRANSLATIONS["pl"]["max_capacity"],
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        self.capacity_label.grid(row=0, column=0, sticky="w")

        self.capacity_entry = ctk.CTkEntry(
            self.param_frame, width=90, placeholder_text="20"
        )
        self.capacity_entry.insert(0, "20")
        self.capacity_entry.grid(row=1, column=0, padx=(0, 5), sticky="w")

        self.start_time_label = ctk.CTkLabel(
            self.param_frame,
            text=TRANSLATIONS["pl"]["start_time"],
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        self.start_time_label.grid(row=0, column=1, sticky="w")

        self.start_time_entry = ctk.CTkEntry(
            self.param_frame, width=90, placeholder_text="08:00"
        )
        self.start_time_entry.insert(0, "08:00")
        self.start_time_entry.grid(row=1, column=1, padx=(0, 5), sticky="w")

        self.stop_time_label = ctk.CTkLabel(
            self.param_frame,
            text=TRANSLATIONS["pl"]["stop_time"],
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        self.stop_time_label.grid(row=0, column=2, sticky="w")

        self.stop_time_entry = ctk.CTkEntry(
            self.param_frame, width=90, placeholder_text="15"
        )
        self.stop_time_entry.insert(0, "15")
        self.stop_time_entry.grid(row=1, column=2, sticky="w")

        # Order files (pdf/xlsx/csv)
        self.file_label = ctk.CTkLabel(
            self.sidebar_frame,
            text=TRANSLATIONS["pl"]["load_orders"],
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.file_label.pack(padx=15, pady=(6, 2), anchor="w")

        self.btn_load_excel = ctk.CTkButton(
            self.sidebar_frame,
            text=TRANSLATIONS["pl"]["btn_load"],
            command=self.load_file,
        )
        self.btn_load_excel.pack(padx=15, pady=2, fill="x")

        # Bag preview and editing
        self.points_edit_frame = ctk.CTkScrollableFrame(
            self.sidebar_frame, height=140, label_text=TRANSLATIONS["pl"]["bags_frame_title"]
        )
        self.points_edit_frame.pack(padx=15, pady=(4, 4), fill="x")

        # Actions
        self.btn_generate = ctk.CTkButton(
            self.sidebar_frame,
            text=TRANSLATIONS["pl"]["generate_route"],
            fg_color="green",
            hover_color="darkgreen",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.generate_route,
        )
        self.btn_generate.pack(padx=15, pady=(4, 4), fill="x")

        self.btn_open_gmaps = ctk.CTkButton(
            self.sidebar_frame,
            text=TRANSLATIONS["pl"]["open_gmaps"],
            fg_color="#EA4335",
            hover_color="#B31412",
            state="disabled",
            command=self.open_in_gmaps,
        )
        self.btn_open_gmaps.pack(padx=15, pady=2, fill="x")

        self.btn_export = ctk.CTkButton(
            self.sidebar_frame,
            text=TRANSLATIONS["pl"]["export_txt"],
            fg_color="#8E24AA",
            hover_color="#6A1B9A",
            state="disabled",
            command=self.export_route_to_file,
        )
        self.btn_export.pack(padx=15, pady=2, fill="x")

        self.status_label = ctk.CTkLabel(
            self.sidebar_frame,
            text=TRANSLATIONS["pl"]["status_ready"],
            text_color="gray",
            wraplength=340,
        )
        self.status_label.pack(padx=15, pady=(4, 2))

        # Step by step list
        self.route_textbox = ctk.CTkTextbox(
            self.sidebar_frame, height=120, corner_radius=5
        )
        self.route_textbox.pack(padx=15, pady=(0, 10), fill="both", expand=True)
        self.route_textbox.insert("1.0", TRANSLATIONS["pl"]["no_route"])
        self.route_textbox.configure(state="disabled")

        # Map view
        self.map_frame = ctk.CTkFrame(self)
        self.map_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.map_widget = TkinterMapView(self.map_frame, corner_radius=10)
        self.map_widget.pack(fill="both", expand=True)

        self.map_widget.set_position(50.2976, 18.9542)  # Position Chorzów
        self.map_widget.set_zoom(13)

        self.update_vehicle_dropdown()

    def change_language(self, lang_choice):
        self.current_lang = "pl" if lang_choice == "PL" else "en"
        t = TRANSLATIONS[self.current_lang]

        self.title(t["app_title"])
        self.logo_label.configure(text=t["logo"])
        self.vehicle_section_label.configure(text=t["vehicle_section"])
        self.btn_manage_vehicles.configure(text=t["fleet_btn"])
        self.route_name_label.configure(text=t["route_name"])
        self.route_name_entry.configure(placeholder_text=t["route_name_placeholder"])
        self.start_label.configure(text=t["start_point"])
        self.start_entry.configure(placeholder_text=t["start_placeholder"])
        self.btn_set_start.configure(text=t["set_start"])
        self.dropoff_label.configure(text=t["dropoff_points"])
        self.dropoff_entry.configure(placeholder_text=t["dropoff_placeholder"])
        self.btn_add_dropoff.configure(text=t["add_dropoff"])
        self.capacity_label.configure(text=t["max_capacity"])
        self.start_time_label.configure(text=t["start_time"])
        self.stop_time_label.configure(text=t["stop_time"])
        self.file_label.configure(text=t["load_orders"])
        self.btn_load_excel.configure(text=t["btn_load"])
        self.points_edit_frame.configure(label_text=t["bags_frame_title"])
        self.btn_generate.configure(text=t["generate_route"])
        self.btn_open_gmaps.configure(text=t["open_gmaps"])
        self.btn_export.configure(text=t["export_txt"])

        # Update default status and empty route box if route is not generated yet
        if not self.ordered_points_list:
            self.update_status(t["status_ready"], "gray")
            self.route_textbox.configure(state="normal")
            self.route_textbox.delete("1.0", "end")
            self.route_textbox.insert("1.0", t["no_route"])
            self.route_textbox.configure(state="disabled")

        if not self.dropoff_points:
            self.dropoff_list_label.configure(text=t["dropoffs_none"])
        else:
            names = [d["name"] for d in self.dropoff_points]
            self.dropoff_list_label.configure(text=f"{t['dropoffs_added']} ({len(names)}):\n" + ", ".join(names))

        self.update_vehicle_dropdown()

        # Update map markers to new language
        if self.start_point:
            if self.start_marker:
                self.map_widget.delete(self.start_marker)
            self.start_marker = self.map_widget.set_marker(
                self.start_point["lat"],
                self.start_point["lon"],
                text=f"{t['base_tag']}: {self.start_point['name']}",
            )

        if self.loaded_points:
            for pt in self.loaded_points:
                bags_desc = self.format_bags_text(pt)
                self.map_widget.set_marker(
                    pt["lat"], pt["lon"], text=f"{pt['name']} [{bags_desc}]"
                )

    def load_vehicles_from_file(self):
        if os.path.exists(VEHICLES_FILE):
            try:
                with open(VEHICLES_FILE, "r", encoding="utf-8") as f:
                    self.vehicles = json.load(f)
            except Exception:
                self.vehicles = {}
        else:
            self.vehicles = {}
            try:
                with open(VEHICLES_FILE, "w", encoding="utf-8") as f:
                    json.dump(self.vehicles, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

    def save_vehicles_to_file(self):
        try:
            with open(VEHICLES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.vehicles, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        self.update_vehicle_dropdown()

    def update_vehicle_dropdown(self):
        t = TRANSLATIONS[self.current_lang]
        placeholder = t["vehicle_placeholder"]
        old_pl_placeholder = TRANSLATIONS["pl"]["vehicle_placeholder"]
        old_en_placeholder = TRANSLATIONS["en"]["vehicle_placeholder"]

        if not self.vehicles:
            self.vehicle_option_menu.configure(values=[placeholder])
            self.vehicle_option_menu.set(placeholder)
            self.current_selected_vehicle_str = placeholder
            return

        values = [placeholder] + [f"{v['name']} ({v['driver']})" for v in self.vehicles.values()]
        self.vehicle_option_menu.configure(values=values)

        if self.current_selected_vehicle_str in [old_pl_placeholder, old_en_placeholder]:
            self.vehicle_option_menu.set(placeholder)
            self.current_selected_vehicle_str = placeholder
        elif self.current_selected_vehicle_str in values:
            self.vehicle_option_menu.set(self.current_selected_vehicle_str)
        else:
            self.vehicle_option_menu.set(placeholder)
            self.current_selected_vehicle_str = placeholder

    def on_vehicle_selected(self, selected_str):
        t = TRANSLATIONS[self.current_lang]
        placeholder = t["vehicle_placeholder"]

        if self.current_selected_vehicle_str == selected_str:
            return

        if (self.loaded_points or self.ordered_points_list) and self.current_selected_vehicle_str != placeholder:
            confirm = messagebox.askyesno(
                t["alert_change_veh_title"],
                t["alert_change_veh_msg"],
                parent=self,
            )

            if not confirm:
                if self.current_selected_vehicle_str:
                    self.vehicle_option_menu.set(self.current_selected_vehicle_str)
                return

            self.clear_loaded_markers()

        self.current_selected_vehicle_str = selected_str

        if selected_str == placeholder:
            self.capacity_entry.delete(0, "end")
            self.capacity_entry.insert(0, "20")
            self.route_name_entry.delete(0, "end")
            return

        for v in self.vehicles.values():
            disp = f"{v['name']} ({v['driver']})"
            if disp == selected_str:
                self.capacity_entry.delete(0, "end")
                self.capacity_entry.insert(0, str(v["capacity"]))

                current_route = self.route_name_entry.get().strip()
                prefix = t["route_prefix"]
                if not current_route or "Trasa - " in current_route or "Route - " in current_route or " - " in current_route:
                    self.route_name_entry.delete(0, "end")
                    self.route_name_entry.insert(0, f"{prefix}{v['driver']}")
                break

    def open_vehicle_manager(self):
        VehicleManagerWindow(self)

    def update_status(self, text, color="white"):
        self.after(
            0, lambda: self.status_label.configure(text=text, text_color=color)
        )

    def clean_address(self, raw_address: str) -> str:
        addr = str(raw_address)
        addr = re.sub(
            r"\b(ul\.|ulica|al\.|aleja)\b", "", addr, flags=re.IGNORECASE
        )
        addr = re.sub(r"/(\d+)", "", addr)
        return re.sub(r"\s+", " ", addr).strip()

    def clean_store_name(self, raw_name: str) -> str:
        name = str(raw_name)
        name = re.sub(r"\b(SP\.\s*Z\s*O\.O\.|SPÓŁKA\s*Z\s*O\.O\.|S\.A\.|SP\.K\.|SP\.J\.)\b", "", name,
                      flags=re.IGNORECASE)
        name = re.sub(r"\b(ul\.|ulica)\s+.*$", "", name, flags=re.IGNORECASE)
        name = re.sub(r"\s+", " ", name).strip(" ,\"'-")
        return name if name else "Sklep"

    def format_bags_text(self, pt: dict) -> str:
        t = TRANSLATIONS[self.current_lang]
        parts = []
        if pt.get("w240", 0) > 0 or (pt.get("w1000", 0) == 0 and pt.get("w_other", 0) == 0):
            parts.append(f"{pt.get('w240', 0)}x240L")
        if pt.get("w1000", 0) > 0:
            parts.append(f"{pt['w1000']}x1000L")
        if pt.get("w_other", 0) > 0:
            parts.append(f"{pt['w_other']}x{t['other_bags']}")
        return ", ".join(parts)

    def distance_haversine(self, lat1, lon1, lat2, lon2):
        r = 6371
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(
            math.radians(lat2)
        ) * math.sin(d_lon / 2) ** 2
        return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def get_closest_dropoff(self, current_pt):
        if not self.dropoff_points:
            return None
        return min(
            self.dropoff_points,
            key=lambda d: self.distance_haversine(
                current_pt["lat"], current_pt["lon"], d["lat"], d["lon"]
            ),
        )

    def set_start_point(self):
        t = TRANSLATIONS[self.current_lang]
        raw_addr = self.start_entry.get().strip()
        if not raw_addr:
            self.update_status(t["status_enter_base"], "orange")
            return

        threading.Thread(
            target=self.process_start_point, args=(raw_addr,), daemon=True
        ).start()

    def process_start_point(self, raw_addr):
        t = TRANSLATIONS[self.current_lang]
        cleaned_addr = self.clean_address(raw_addr)
        self.update_status(t["status_search_base"], "yellow")

        try:
            location = self.geolocator.geocode(f"{cleaned_addr}, Polska", timeout=10)
            if location:
                self.start_point = {
                    "name": f"{raw_addr}",
                    "lat": location.latitude,
                    "lon": location.longitude,
                    "bags": 0,
                }

                def draw_start_marker():
                    if self.start_marker:
                        self.map_widget.delete(self.start_marker)
                    self.start_marker = self.map_widget.set_marker(
                        self.start_point["lat"],
                        self.start_point["lon"],
                        text=f"{t['base_tag']}: {self.start_point['name']}",
                    )
                    self.map_widget.set_position(
                        self.start_point["lat"], self.start_point["lon"]
                    )

                self.after(0, draw_start_marker)
                self.update_status(t["status_base_set"], "cyan")
            else:
                self.update_status(t["status_base_not_found"], "red")
        except Exception as e:
            self.update_status(f"{t['status_base_err']} {str(e)}", "red")

    def add_dropoff_point(self):
        t = TRANSLATIONS[self.current_lang]
        raw_addr = self.dropoff_entry.get().strip()
        if not raw_addr:
            self.update_status(t["status_enter_dropoff"], "orange")
            return

        threading.Thread(
            target=self.process_add_dropoff, args=(raw_addr,), daemon=True
        ).start()

    def process_add_dropoff(self, raw_addr):
        t = TRANSLATIONS[self.current_lang]
        cleaned_addr = self.clean_address(raw_addr)
        self.update_status(t["status_search_dropoff"], "yellow")

        try:
            location = self.geolocator.geocode(f"{cleaned_addr}, Polska", timeout=10)
            if location:
                drop_pt = {
                    "name": f"{raw_addr}",
                    "lat": location.latitude,
                    "lon": location.longitude,
                    "bags": 0,
                }
                self.dropoff_points.append(drop_pt)

                def update_dropoff_ui():
                    self.map_widget.set_marker(
                        drop_pt["lat"],
                        drop_pt["lon"],
                        text=f"{t['dropoff_tag']}: {drop_pt['name']}",
                    )
                    names = [d["name"] for d in self.dropoff_points]
                    self.dropoff_list_label.configure(
                        text=f"{t['dropoffs_added']} ({len(names)}):\n" + ", ".join(names),
                        text_color="cyan",
                    )
                    self.dropoff_entry.delete(0, "end")

                self.after(0, update_dropoff_ui)
                self.update_status(t["status_dropoff_added"], "cyan")
            else:
                self.update_status(t["status_dropoff_not_found"], "red")
        except Exception as e:
            self.update_status(f"{t['status_dropoff_err']} {str(e)}", "red")

    def parse_pdf_file(self, pdf_path):
        reader = PdfReader(pdf_path)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text() + "\n"

        cleaned_text = full_text.replace('"', '').replace('\r', '')
        lines = [l.strip() for l in cleaned_text.split("\n") if l.strip()]

        postal_match = re.search(r"\b(\d{2}-\d{3})\b", cleaned_text)
        postal_code = postal_match.group(1) if postal_match else ""

        raw_name = "Sklep"
        for i, line in enumerate(lines):
            if "Nazwa Punktu Zbiórki" in line:
                for offset in range(1, 5):
                    if i + offset < len(lines):
                        cand = lines[i + offset].strip(", ").strip()
                        if cand and not any(
                                k in cand for k in ["Gmina", "Miejscowość", "Kod pocztowy", "Osoba kontaktowa"]):
                            raw_name = cand
                            break
                break

        street = ""
        city = ""

        for line in lines:
            line_pure = line.strip(", ").strip()
            if not street and re.search(r"\b(ul\.|Rynek|Aleja|al\.|pl\.|Plac)\b", line_pure, re.IGNORECASE):
                match_street = re.search(r"(ul\.|Rynek|Aleja|al\.|pl\.|Plac)[^,]+", line_pure, re.IGNORECASE)
                street = match_street.group(0).strip() if match_street else line_pure
            elif not street and re.search(r"\b[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+\s+\d+\b", line_pure):
                street = line_pure

        if postal_code:
            for i, line in enumerate(lines):
                if postal_code in line:
                    for offset in [-2, -1, 1, 2]:
                        idx = i + offset
                        if 0 <= idx < len(lines):
                            val = lines[idx].strip(", ").strip()
                            if val and val != street and val != postal_code and not val.isdigit() and len(val) > 2:
                                if not any(k in val for k in ["Magdalena", "Michał", "Damian", "Osoba", "Telefon"]):
                                    city = val
                                    break
                    break

        short_name = self.clean_store_name(raw_name)
        if len(short_name) > 22:
            short_name = short_name[:20] + "..."

        if street:
            display_name = f"{short_name} ({street})"
        elif city:
            display_name = f"{short_name} ({city})"
        else:
            display_name = short_name

        search_parts = [p for p in [street, city, postal_code] if p and len(p) > 2]
        full_search_address = ", ".join(search_parts) if search_parts else raw_name

        sizes = re.findall(r"\b(120|240|1000)\b", cleaned_text)
        w240 = sizes.count("240")
        w1000 = sizes.count("1000")
        w_other = sizes.count("120")

        if w240 == 0 and w1000 == 0 and w_other == 0:
            w240 = 1

        return {
            "name": display_name,
            "search_address": full_search_address,
            "w240": w240,
            "w1000": w1000,
            "w_other": w_other,
        }

    def load_file(self):
        t = TRANSLATIONS[self.current_lang]
        file_paths = filedialog.askopenfilenames(
            filetypes=[(t["filetype_orders"], "*.pdf *.xlsx *.csv")]
        )
        if not file_paths:
            return

        threading.Thread(
            target=self.process_files, args=(file_paths,), daemon=True
        ).start()

    def process_files(self, file_paths):
        t = TRANSLATIONS[self.current_lang]
        try:
            self.update_status(t["status_reading_files"], "yellow")
            self.after(0, self.clear_loaded_markers)

            new_points = []
            total = len(file_paths)
            count = 0

            for idx, file_path in enumerate(file_paths):
                if file_path.endswith(".pdf"):
                    pdf_data = self.parse_pdf_file(file_path)
                    name = pdf_data["name"]
                    search_addr = pdf_data["search_address"]

                    self.update_status(
                        f"{t['status_geocoding']} ({idx + 1}/{total}):\n{name}", "yellow"
                    )

                    try:
                        clean_q = self.clean_address(search_addr)
                        location = self.geolocator.geocode(f"{clean_q}, Polska", timeout=10)

                        if location:
                            new_points.append({
                                "name": name,
                                "lat": location.latitude,
                                "lon": location.longitude,
                                "w240": pdf_data["w240"],
                                "w1000": pdf_data["w1000"],
                                "w_other": pdf_data["w_other"],
                            })
                            count += 1
                    except Exception:
                        continue

                elif file_path.endswith(".csv") or file_path.endswith(".xlsx"):
                    df = pd.read_csv(file_path) if file_path.endswith(".csv") else pd.read_excel(file_path)
                    has_gps = "Szerokosc" in df.columns and "Dlugosc" in df.columns
                    has_address = "Adres" in df.columns
                    has_name = "Nazwa" in df.columns

                    for row_idx, row in df.iterrows():
                        if has_name and has_address:
                            clean_n = self.clean_store_name(str(row['Nazwa']))
                            name = f"{clean_n} ({row['Adres']})"
                        elif has_address:
                            name = str(row["Adres"])
                        else:
                            name = str(row.get("Nazwa", f"Automat {row_idx + 1}"))

                        w240_count = int(row.get("Worki 240", row.get("Ilosc", row.get("Ilość", 1))))
                        w1000_count = int(row.get("Worki 1000", 0))
                        w_other_count = int(row.get("Inne", 0))

                        if has_gps:
                            lat, lon = float(row["Szerokosc"]), float(row["Dlugosc"])
                        else:
                            clean_a = self.clean_address(str(row["Adres"]))
                            location = self.geolocator.geocode(f"{clean_a}, Polska", timeout=10)
                            if location:
                                lat, lon = location.latitude, location.longitude
                            else:
                                continue

                        new_points.append({
                            "name": name,
                            "lat": lat,
                            "lon": lon,
                            "w240": w240_count,
                            "w1000": w1000_count,
                            "w_other": w_other_count,
                        })
                        count += 1

            self.loaded_points = new_points

            def render_loaded_points():
                for pt in self.loaded_points:
                    bags_desc = self.format_bags_text(pt)
                    self.map_widget.set_marker(
                        pt["lat"], pt["lon"], text=f"{pt['name']} [{bags_desc}]"
                    )
                if self.loaded_points and not self.start_point:
                    self.map_widget.set_position(
                        self.loaded_points[0]["lat"],
                        self.loaded_points[0]["lon"],
                    )

                for widget in self.points_edit_frame.winfo_children():
                    widget.destroy()

                for pt_idx, pt in enumerate(self.loaded_points):
                    row_frame = ctk.CTkFrame(self.points_edit_frame, fg_color="transparent")
                    row_frame.pack(fill="x", pady=2)

                    lbl = ctk.CTkLabel(
                        row_frame, text=f"{pt_idx + 1}. {pt['name'][:20]}...", font=ctk.CTkFont(size=11)
                    )
                    lbl.pack(side="left", padx=(0, 2))

                    e_other = ctk.CTkEntry(row_frame, width=38, font=ctk.CTkFont(size=10))
                    e_other.insert(0, str(pt["w_other"]))
                    e_other.pack(side="right", padx=1)

                    e1000 = ctk.CTkEntry(row_frame, width=38, font=ctk.CTkFont(size=10))
                    e1000.insert(0, str(pt["w1000"]))
                    e1000.pack(side="right", padx=1)

                    e240 = ctk.CTkEntry(row_frame, width=38, font=ctk.CTkFont(size=10))
                    e240.insert(0, str(pt["w240"]))
                    e240.pack(side="right", padx=1)

                    pt["ref_240"] = e240
                    pt["ref_1000"] = e1000
                    pt["ref_other"] = e_other

            self.after(0, render_loaded_points)

            self.update_status(
                t["status_loaded_pts"].format(count=count, total=total),
                "cyan" if count > 0 else "orange",
            )

        except Exception as e:
            self.update_status(f"{t['status_read_err']} {str(e)}", "red")

    def clear_loaded_markers(self):
        t = TRANSLATIONS[self.current_lang]
        self.map_widget.delete_all_marker()
        if self.start_point:
            self.start_marker = self.map_widget.set_marker(
                self.start_point["lat"],
                self.start_point["lon"],
                text=f"{t['base_tag']}: {self.start_point['name']}",
            )
        for drop_pt in self.dropoff_points:
            self.map_widget.set_marker(
                drop_pt["lat"],
                drop_pt["lon"],
                text=f"{t['dropoff_tag']}: {drop_pt['name']}",
            )
        for path in self.current_paths:
            self.map_widget.delete(path)
        self.current_paths.clear()

        for widget in self.points_edit_frame.winfo_children():
            widget.destroy()

        self.loaded_points.clear()
        self.ordered_points_list.clear()
        self.btn_open_gmaps.configure(state="disabled")
        self.btn_export.configure(state="disabled")

        self.route_textbox.configure(state="normal")
        self.route_textbox.delete("1.0", "end")
        self.route_textbox.insert("1.0", t["no_route"])
        self.route_textbox.configure(state="disabled")

    def sync_bags_from_gui(self):
        for pt in self.loaded_points:
            if "ref_240" in pt:
                try:
                    pt["w240"] = int(pt["ref_240"].get().strip())
                    pt["w1000"] = int(pt["ref_1000"].get().strip())
                    pt["w_other"] = int(pt["ref_other"].get().strip())
                except ValueError:
                    pass

            pt["bags_equiv"] = pt["w240"] + (pt["w1000"] * 4) + math.ceil(pt["w_other"] * 0.5)

    def generate_route(self):
        t = TRANSLATIONS[self.current_lang]
        if not self.loaded_points:
            self.update_status(t["status_load_files_first"], "orange")
            return

        self.sync_bags_from_gui()
        threading.Thread(target=self.calculate_osrm_multi_trip, daemon=True).start()

    def calculate_osrm_multi_trip(self):
        t = TRANSLATIONS[self.current_lang]
        try:
            self.update_status(t["status_optimizing"], "yellow")

            try:
                vehicle_capacity = int(self.capacity_entry.get().strip())
            except ValueError:
                vehicle_capacity = 20

            start_time_str = self.start_time_entry.get().strip() or "08:00"
            try:
                current_time = datetime.strptime(start_time_str, "%H:%M")
            except ValueError:
                current_time = datetime.strptime("08:00", "%H:%M")

            stop_duration_min = int(self.stop_time_entry.get().strip() or "15")

            if not self.start_point:
                self.update_status(t["status_set_base_first"], "orange")
                return

            if not self.dropoff_points:
                self.update_status(t["status_add_dropoff_first"], "orange")
                return

            all_initial_pts = [self.start_point] + list(self.loaded_points)
            coords_str = ";".join([f"{pt['lon']},{pt['lat']}" for pt in all_initial_pts])
            url_trip = f"http://router.project-osrm.org/trip/v1/driving/{coords_str}?overview=false&source=first"

            res = requests.get(url_trip, timeout=15).json()
            if res.get("code") != "Ok":
                self.update_status(t["status_osrm_err"], "red")
                return

            waypoints = res.get("waypoints", [])
            for idx, wp in enumerate(waypoints):
                wp["input_idx"] = idx

            sorted_waypoints = sorted(waypoints, key=lambda x: x.get("waypoint_index", 0))

            ordered_pickup_points = []
            for wp in sorted_waypoints:
                orig_idx = wp["input_idx"]
                if orig_idx != 0:
                    ordered_pickup_points.append(all_initial_pts[orig_idx])

            trips = []
            current_trip_pickups = []
            current_load = 0

            for pt in ordered_pickup_points:
                pt_units = pt.get("bags_equiv", 1)
                if current_load + pt_units > vehicle_capacity and current_trip_pickups:
                    trips.append(current_trip_pickups)
                    current_trip_pickups = [pt]
                    current_load = pt_units
                else:
                    current_trip_pickups.append(pt)
                    current_load += pt_units

            if current_trip_pickups:
                trips.append(current_trip_pickups)

            full_route_geometry = []
            full_ordered_coords_gmaps = []
            total_distance_km = 0
            total_driving_duration_min = 0
            total_service_duration_min = 0

            current_start_node = self.start_point

            self.ordered_points_list.clear()

            title_route = self.route_name_entry.get().strip() or t["rep_plan"]

            list_text = f"{t['rep_route']}: {title_route}\n"
            list_text += f"{t['rep_trips']}: {len(trips)} | {t['rep_cap']}: {vehicle_capacity} {t['rep_bags']}\n"
            list_text += "===================================\n\n"

            stop_counter = 1

            for trip_idx, trip_points in enumerate(trips, 1):
                last_pickup = trip_points[-1]
                chosen_dropoff = self.get_closest_dropoff(last_pickup)

                trip_all_nodes = [current_start_node] + trip_points + [chosen_dropoff]
                trip_coords_str = ";".join([f"{pt['lon']},{pt['lat']}" for pt in trip_all_nodes])

                url_route = f"http://router.project-osrm.org/route/v1/driving/{trip_coords_str}?overview=full&geometries=geojson&steps=true"
                route_res = requests.get(url_route, timeout=15).json()

                legs = []
                if route_res.get("code") == "Ok":
                    r_data = route_res["routes"][0]
                    total_distance_km += round(r_data["distance"] / 1000, 1)
                    legs = r_data.get("legs", [])

                    geo = [(c[1], c[0]) for c in r_data["geometry"]["coordinates"]]
                    full_route_geometry.append(geo)

                trip_units = sum(pt.get("bags_equiv", 1) for pt in trip_points)
                trip_start_str = current_time.strftime("%H:%M")

                list_text += f"--- {t['rep_trip']} #{trip_idx} ({t['rep_load']}: {trip_units}/{vehicle_capacity} {t['rep_eq']}) ---\n"
                list_text += f"{t['rep_start']} [{trip_start_str}]: {current_start_node['name']}\n"
                self.ordered_points_list.append(
                    f"{t['rep_start']} {t['rep_trip']} #{trip_idx} [{trip_start_str}]: {current_start_node['name']}")

                full_ordered_coords_gmaps.append(f"{current_start_node['lat']},{current_start_node['lon']}")

                for pt_idx, pt in enumerate(trip_points):
                    full_ordered_coords_gmaps.append(f"{pt['lat']},{pt['lon']}")

                    if pt_idx < len(legs):
                        drive_min = round(legs[pt_idx]["duration"] / 60)
                        total_driving_duration_min += drive_min
                        current_time += timedelta(minutes=drive_min)

                    arrival_str = current_time.strftime("%H:%M")

                    dep_time = current_time + timedelta(minutes=stop_duration_min)
                    dep_str = dep_time.strftime("%H:%M")
                    total_service_duration_min += stop_duration_min
                    current_time = dep_time

                    details = self.format_bags_text(pt)

                    entry_line = f"{stop_counter}. {pt['name']} [{details}]\n   -> {t['rep_arr']}: {arrival_str} | {t['rep_dep']}: {dep_str}"
                    list_text += f"{entry_line}\n"
                    self.ordered_points_list.append(entry_line)
                    stop_counter += 1

                if len(legs) > len(trip_points):
                    last_leg_drive_min = round(legs[-1]["duration"] / 60)
                    total_driving_duration_min += last_leg_drive_min
                    current_time += timedelta(minutes=last_leg_drive_min)

                dropoff_arrival_str = current_time.strftime("%H:%M")

                full_ordered_coords_gmaps.append(f"{chosen_dropoff['lat']},{chosen_dropoff['lon']}")
                dropoff_line = f"---> {t['rep_drop']} [{dropoff_arrival_str}]: {chosen_dropoff['name']} {t['rep_unloading']}\n\n"
                list_text += dropoff_line
                self.ordered_points_list.append(
                    f"{t['rep_drop']} #{trip_idx} [{dropoff_arrival_str}]: {chosen_dropoff['name']}")

                current_time += timedelta(minutes=10)
                total_service_duration_min += 10

                current_start_node = chosen_dropoff

            total_overall_time_min = total_driving_duration_min + total_service_duration_min
            total_hours = total_overall_time_min // 60
            total_mins = total_overall_time_min % 60

            header_summary = f"{t['rep_tot_dist']}: {total_distance_km:.1f} km\n"
            header_summary += f"{t['rep_tot_time']}: {total_hours}h {total_mins}m ({t['rep_drive']}: {total_driving_duration_min}m, {t['rep_stops']}: {total_service_duration_min}m)\n"
            header_summary += "-----------------------------------\n\n"

            final_full_text = list_text[:list_text.find("===================\n\n") + 21] + header_summary + list_text[
                list_text.find("===================\n\n") + 21:]

            def render_multi_trip_results():
                self.map_widget.delete_all_marker()

                self.start_marker = self.map_widget.set_marker(
                    self.start_point["lat"], self.start_point["lon"], text=f"{t['base_tag']}: {self.start_point['name']}"
                )
                for drop_pt in self.dropoff_points:
                    self.map_widget.set_marker(
                        drop_pt["lat"], drop_pt["lon"], text=f"{t['dropoff_tag']}: {drop_pt['name']}"
                    )
                for pt in self.loaded_points:
                    bags_desc = self.format_bags_text(pt)
                    self.map_widget.set_marker(
                        pt["lat"], pt["lon"], text=f"{pt['name']} [{bags_desc}]"
                    )

                for path in self.current_paths:
                    self.map_widget.delete(path)
                self.current_paths.clear()

                colors = ["green", "blue", "orange", "purple", "cyan"]
                for idx, geo in enumerate(full_route_geometry):
                    path_color = colors[idx % len(colors)]
                    p = self.map_widget.set_path(geo, color=path_color, width=5)
                    self.current_paths.append(p)

                self.gmaps_url = f"https://www.google.com/maps/dir/{'/'.join(full_ordered_coords_gmaps)}"
                self.btn_open_gmaps.configure(state="normal")
                self.btn_export.configure(state="normal")

                self.route_textbox.configure(state="normal")
                self.route_textbox.delete("1.0", "end")
                self.route_textbox.insert("1.0", final_full_text)
                self.route_textbox.configure(state="disabled")

                self.update_status(
                    t["status_calc_success"].format(
                        trips=len(trips), dist=total_distance_km, hours=total_hours, mins=total_mins
                    ),
                    "lime",
                )

            self.after(0, render_multi_trip_results)

        except Exception as e:
            self.update_status(f"{t['status_opt_err']} {str(e)}", "red")

    def open_in_gmaps(self):
        if self.gmaps_url:
            webbrowser.open(self.gmaps_url)

    def export_route_to_file(self):
        t = TRANSLATIONS[self.current_lang]
        if not self.ordered_points_list:
            return

        route_title = self.route_name_entry.get().strip() or t["rep_plan"].replace(" ", "_")
        safe_filename = (
                re.sub(r'[\\/*?:"<>|]', "", route_title).replace(" ", "_") + ".txt"
        )

        file_path = filedialog.asksaveasfilename(
            initialfile=safe_filename,
            defaultextension=".txt",
            filetypes=[(t["filetype_desc"], "*.txt")],
            title=t["save_dialog_title"],
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"{t['txt_plan_header']}: {route_title.upper()}\n")
                    f.write("========================\n\n")
                    for line in self.ordered_points_list:
                        f.write(f"{line}\n")
                    if self.gmaps_url:
                        f.write(
                            f"\n{t['txt_gmaps_link']}\n{self.gmaps_url}\n"
                        )
                self.update_status(t["status_saved_txt"], "cyan")
            except Exception as e:
                self.update_status(f"{t['status_save_err']} {str(e)}", "red")


if __name__ == "__main__":
    app = RoutePlannerApp()
    app.mainloop()