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

# Ustawienia motywu graficznego
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

VEHICLES_FILE = "vehicles.json"


class VehicleManagerWindow(ctk.CTkToplevel):
    """Osobne okienko do zarządzania flotą pojazdów (Dodaj / Edytuj / Usuń)"""

    def __init__(self, parent_app):
        super().__init__(parent_app)

        self.parent_app = parent_app
        self.title("Zarządzanie flotą pojazdów i kierowcami")
        self.geometry("580x600")
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        # Nagłówek
        lbl_title = ctk.CTkLabel(
            self,
            text="Baza pojazdów i kierowców",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        lbl_title.grid(row=0, column=0, padx=15, pady=(15, 5))

        # Lista pojazdów (Scrollable)
        self.scroll_frame = ctk.CTkScrollableFrame(self)
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=5)

        # Formularz dodawania / edycji
        self.form_frame = ctk.CTkFrame(self)
        self.form_frame.grid(row=2, column=0, sticky="ew", padx=15, pady=(5, 15))
        self.form_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.form_frame, text="Pojazd / rejestracja:").grid(
            row=0, column=0, padx=8, pady=5, sticky="w"
        )
        self.entry_name = ctk.CTkEntry(
            self.form_frame, placeholder_text="np. Sprinter (ST 12345)"
        )
        self.entry_name.grid(row=0, column=1, padx=8, pady=5, sticky="ew")

        ctk.CTkLabel(self.form_frame, text="Kierowca:").grid(
            row=1, column=0, padx=8, pady=5, sticky="w"
        )
        self.entry_driver = ctk.CTkEntry(
            self.form_frame, placeholder_text="np. Jan Kowalski"
        )
        self.entry_driver.grid(row=1, column=1, padx=8, pady=5, sticky="ew")

        ctk.CTkLabel(self.form_frame, text="Pojemność (worki 240L):").grid(
            row=2, column=0, padx=8, pady=5, sticky="w"
        )
        self.entry_cap = ctk.CTkEntry(self.form_frame, placeholder_text="24")
        self.entry_cap.grid(row=2, column=1, padx=8, pady=5, sticky="ew")

        # Przycisk Zapisz/Dodaj
        self.btn_save = ctk.CTkButton(
            self.form_frame,
            text="Dodaj nowy pojazd",
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

        vehicles = self.parent_app.vehicles

        if not vehicles:
            ctk.CTkLabel(
                self.scroll_frame, text="Brak zapisanych pojazdów w bazie. Dodaj pierwszy poniżej."
            ).pack(pady=20)
            return

        for v_id, v_data in vehicles.items():
            card = ctk.CTkFrame(self.scroll_frame)
            card.pack(fill="x", pady=4, padx=5)

            info_text = f"Samochód: {v_data['name']}\nKierowca: {v_data['driver']}\nPojemność podana w workach (240L): {v_data['capacity']}"
            lbl = ctk.CTkLabel(
                card, text=info_text, justify="left", font=ctk.CTkFont(size=12)
            )
            lbl.pack(side="left", padx=10, pady=8)

            btn_del = ctk.CTkButton(
                card,
                text="Usuń",
                width=35,
                fg_color="#EA4335",
                hover_color="#B31412",
                command=lambda id_to_del=v_id: self.delete_vehicle(id_to_del),
            )
            btn_del.pack(side="right", padx=5)

            btn_edit = ctk.CTkButton(
                card,
                text="Edytuj",
                width=35,
                fg_color="#3B82F6",
                hover_color="#1D4ED8",
                command=lambda id_to_edit=v_id: self.load_to_edit(id_to_edit),
            )
            btn_edit.pack(side="right", padx=2)

    def load_to_edit(self, v_id):
        v = self.parent_app.vehicles.get(v_id)
        if not v:
            return
        self.selected_vehicle_id = v_id
        self.entry_name.delete(0, "end")
        self.entry_name.insert(0, v["name"])

        self.entry_driver.delete(0, "end")
        self.entry_driver.insert(0, v["driver"])

        self.entry_cap.delete(0, "end")
        self.entry_cap.insert(0, str(v["capacity"]))

        self.btn_save.configure(
            text="Zapisz zmiany w pojeździe", fg_color="#EAB308"
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

        self.entry_name.delete(0, "end")
        self.entry_driver.delete(0, "end")
        self.entry_cap.delete(0, "end")
        self.btn_save.configure(text="Dodaj nowy pojazd", fg_color="green")

        self.refresh_list()

    def delete_vehicle(self, v_id):
        if v_id in self.parent_app.vehicles:
            del self.parent_app.vehicles[v_id]
            self.parent_app.save_vehicles_to_file()
            self.refresh_list()


class RoutePlannerApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Optymalizator tras - automaty z butelkami")
        self.geometry("1350x980")

        self.vehicles = {}
        self.load_vehicles_from_file()

        self.start_point = None  # Baza
        self.dropoff_points = []  # Lista dostępnych stref zrzutu
        self.loaded_points = []  # Automaty (punkty odbioru)
        self.ordered_points_list = []  # Posortowane punkty po optymalizacji
        self.current_selected_vehicle_str = "-- Wybierz pojazd --"  # Domyślny placeholder

        self.start_marker = None
        self.current_paths = []
        self.gmaps_url = None
        self.geolocator = ArcGIS(user_agent="bottle_route_planner")

        # Layout (1 wiersz, 2 kolumny)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ------------------- PANEL BOCZNY -------------------
        self.sidebar_frame = ctk.CTkFrame(self, width=400, corner_radius=0)
        self.sidebar_frame.grid(
            row=0, column=0, sticky="nsew", padx=10, pady=10
        )

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Planowanie tras",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.logo_label.pack(padx=15, pady=(15, 10))

        # SEKCJA 0: WYBÓR POJAZDU Z BAZY
        self.vehicle_section_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Pojazd i kierowca:",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.vehicle_section_label.pack(padx=15, pady=(2, 2), anchor="w")

        veh_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        veh_frame.pack(padx=15, pady=(0, 6), fill="x")

        self.vehicle_option_menu = ctk.CTkOptionMenu(
            veh_frame,
            values=["-- Wybierz pojazd --"],
            command=self.on_vehicle_selected,
        )
        self.vehicle_option_menu.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_manage_vehicles = ctk.CTkButton(
            veh_frame,
            text="Flota",
            width=80,
            fg_color="#8E24AA",
            hover_color="#6A1B9A",
            command=self.open_vehicle_manager,
        )
        self.btn_manage_vehicles.pack(side="right")

        # SEKCJA 1: NAZWA TRASY
        self.route_name_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="1. Nazwa trasy (opcjonalnie):",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.route_name_label.pack(padx=15, pady=(2, 2), anchor="w")

        self.route_name_entry = ctk.CTkEntry(
            self.sidebar_frame,
            placeholder_text="np. Trasa Śląsk - Jan Kowalski",
        )
        self.route_name_entry.pack(padx=15, pady=(2, 6), fill="x")

        # SEKCJA 2: BAZA (START)
        self.start_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="2. Punkt startowy (baza):",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.start_label.pack(padx=15, pady=(2, 2), anchor="w")

        self.start_entry = ctk.CTkEntry(
            self.sidebar_frame,
            placeholder_text="np. ul. Sportowa 1, Chorzów",
        )
        self.start_entry.pack(padx=15, pady=2, fill="x")

        self.btn_set_start = ctk.CTkButton(
            self.sidebar_frame,
            text="Ustaw bazę",
            fg_color="#3B82F6",
            hover_color="#1D4ED8",
            command=self.set_start_point,
        )
        self.btn_set_start.pack(padx=15, pady=(2, 6))

        # SEKCJA 3: STREFY ZRZUTU
        self.dropoff_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="3. Strefy zrzutu (można dodać kilka):",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.dropoff_label.pack(padx=15, pady=(2, 2), anchor="w")

        self.dropoff_entry = ctk.CTkEntry(
            self.sidebar_frame,
            placeholder_text="np. ul. Katowicka 5, Chorzów",
        )
        self.dropoff_entry.pack(padx=15, pady=2, fill="x")

        self.btn_add_dropoff = ctk.CTkButton(
            self.sidebar_frame,
            text="Dodaj strefę zrzutu",
            fg_color="#EAB308",
            hover_color="#CA8A04",
            command=self.add_dropoff_point,
        )
        self.btn_add_dropoff.pack(padx=15, pady=(2, 4))

        self.dropoff_list_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Dodane zrzuty: Brak",
            text_color="gray",
            font=ctk.CTkFont(size=11),
            wraplength=340,
        )
        self.dropoff_list_label.pack(padx=15, pady=(0, 6))

        # SEKCJA 4: POJEMNOŚĆ I CZAS
        self.param_frame = ctk.CTkFrame(
            self.sidebar_frame, fg_color="transparent"
        )
        self.param_frame.pack(padx=15, pady=2, fill="x")

        self.capacity_label = ctk.CTkLabel(
            self.param_frame,
            text="Max worków\n(240L):",
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
            text="Start:",
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
            text="Postój\n(min):",
            font=ctk.CTkFont(size=11, weight="bold"),
        )
        self.stop_time_label.grid(row=0, column=2, sticky="w")

        self.stop_time_entry = ctk.CTkEntry(
            self.param_frame, width=90, placeholder_text="15"
        )
        self.stop_time_entry.insert(0, "15")
        self.stop_time_entry.grid(row=1, column=2, sticky="w")

        # SEKCJA 5: PLIK (ZLECENIA PDF / EXCEL)
        self.file_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="5. Wgraj pliki zleceń (.pdf / .xlsx / .csv):",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.file_label.pack(padx=15, pady=(6, 2), anchor="w")

        self.btn_load_excel = ctk.CTkButton(
            self.sidebar_frame,
            text="Wgraj zlecenia (PDF / Excel)",
            command=self.load_file,
        )
        self.btn_load_excel.pack(padx=15, pady=2, fill="x")

        # SEKCJA 6: PODGLĄD I EDYCJA WORKÓW
        self.points_edit_frame = ctk.CTkScrollableFrame(
            self.sidebar_frame, height=140, label_text="Liczba worków na sklepach | 240L | 1000L | Inne |:"
        )
        self.points_edit_frame.pack(padx=15, pady=(4, 4), fill="x")

        # SEKCJA 7: AKCJE
        self.btn_generate = ctk.CTkButton(
            self.sidebar_frame,
            text="Generuj optymalną trasę",
            fg_color="green",
            hover_color="darkgreen",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.generate_route,
        )
        self.btn_generate.pack(padx=15, pady=(4, 4), fill="x")

        self.btn_open_gmaps = ctk.CTkButton(
            self.sidebar_frame,
            text="Otwórz w Google Maps",
            fg_color="#EA4335",
            hover_color="#B31412",
            state="disabled",
            command=self.open_in_gmaps,
        )
        self.btn_open_gmaps.pack(padx=15, pady=2, fill="x")

        self.btn_export = ctk.CTkButton(
            self.sidebar_frame,
            text="Zapisz plan trasy (.txt)",
            fg_color="#8E24AA",
            hover_color="#6A1B9A",
            state="disabled",
            command=self.export_route_to_file,
        )
        self.btn_export.pack(padx=15, pady=2, fill="x")

        self.status_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="Status: Ustaw punkty lub wgraj pliki...",
            text_color="gray",
            wraplength=340,
        )
        self.status_label.pack(padx=15, pady=(4, 2))

        # SEKCJA 8: LISTA KROK PO KROKU
        self.route_textbox = ctk.CTkTextbox(
            self.sidebar_frame, height=120, corner_radius=5
        )
        self.route_textbox.pack(padx=15, pady=(0, 10), fill="both", expand=True)
        self.route_textbox.insert("1.0", "Brak wyznaczonej trasy.")
        self.route_textbox.configure(state="disabled")

        # ------------------- WIDOK MAPY (CHORZÓW) -------------------
        self.map_frame = ctk.CTkFrame(self)
        self.map_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.map_widget = TkinterMapView(self.map_frame, corner_radius=10)
        self.map_widget.pack(fill="both", expand=True)

        self.map_widget.set_position(50.2976, 18.9542)  # Pozycja Chorzów
        self.map_widget.set_zoom(13)

        self.update_vehicle_dropdown()

    # --- OBSŁUGA BAZY POJAZDÓW JSON ---
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
        placeholder = "-- Wybierz pojazd --"
        if not self.vehicles:
            self.vehicle_option_menu.configure(values=[placeholder])
            self.vehicle_option_menu.set(placeholder)
            self.current_selected_vehicle_str = placeholder
            return

        values = [placeholder] + [f"{v['name']} ({v['driver']})" for v in self.vehicles.values()]
        self.vehicle_option_menu.configure(values=values)

        # Jeśli poprzednio coś wybrano, spróbuj to zachować, inaczej ustaw placeholder
        if self.current_selected_vehicle_str in values:
            self.vehicle_option_menu.set(self.current_selected_vehicle_str)
        else:
            self.vehicle_option_menu.set(placeholder)
            self.current_selected_vehicle_str = placeholder

    def on_vehicle_selected(self, selected_str):
        placeholder = "-- Wybierz pojazd --"

        if self.current_selected_vehicle_str == selected_str:
            return

        # Pytamy o potwierdzenie TYLKO wtedy, gdy użytkownik faktycznie zmieniał już konkretny pojazd na inny
        # (czyli z wybranego pojazdu przełącza na inny i ma załadowaną trasę/punkty)
        if (self.loaded_points or self.ordered_points_list) and self.current_selected_vehicle_str != placeholder:
            confirm = messagebox.askyesno(
                "Zmiana pojazdu",
                "Wyznaczenie trasy dotyczy innego pojazdu.\nCzy na pewno chcesz zmienić pojazd i zresetować obecną trasę?",
                parent=self,
            )

            if not confirm:
                if self.current_selected_vehicle_str:
                    self.vehicle_option_menu.set(self.current_selected_vehicle_str)
                return

            self.clear_loaded_markers()

        self.current_selected_vehicle_str = selected_str

        if selected_str == placeholder:
            # Gdy użytkownik kliknie powrotnie "Wybierz pojazd..."
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
                if not current_route or "Trasa - " in current_route or " - " in current_route:
                    self.route_name_entry.delete(0, "end")
                    self.route_name_entry.insert(0, f"Trasa - {v['driver']}")
                break

    def open_vehicle_manager(self):
        VehicleManagerWindow(self)

    # --- POZOSTAŁA LOGIKA APLIKACJI ---
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
        parts = []
        if pt.get("w240", 0) > 0 or (pt.get("w1000", 0) == 0 and pt.get("w_other", 0) == 0):
            parts.append(f"{pt.get('w240', 0)}x240L")
        if pt.get("w1000", 0) > 0:
            parts.append(f"{pt['w1000']}x1000L")
        if pt.get("w_other", 0) > 0:
            parts.append(f"{pt['w_other']}xInne")
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
        raw_addr = self.start_entry.get().strip()
        if not raw_addr:
            self.update_status("Wpisz adres bazy!", "orange")
            return

        threading.Thread(
            target=self.process_start_point, args=(raw_addr,), daemon=True
        ).start()

    def process_start_point(self, raw_addr):
        cleaned_addr = self.clean_address(raw_addr)
        self.update_status("Szukam adresu bazy...", "yellow")

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
                        text=f"BAZA: {self.start_point['name']}",
                    )
                    self.map_widget.set_position(
                        self.start_point["lat"], self.start_point["lon"]
                    )

                self.after(0, draw_start_marker)
                self.update_status("Ustawiono bazę!", "cyan")
            else:
                self.update_status("Nie znaleziono adresu bazy!", "red")
        except Exception as e:
            self.update_status(f"Błąd bazy: {str(e)}", "red")

    def add_dropoff_point(self):
        raw_addr = self.dropoff_entry.get().strip()
        if not raw_addr:
            self.update_status("Wpisz adres strefy zrzutu!", "orange")
            return

        threading.Thread(
            target=self.process_add_dropoff, args=(raw_addr,), daemon=True
        ).start()

    def process_add_dropoff(self, raw_addr):
        cleaned_addr = self.clean_address(raw_addr)
        self.update_status("Szukam strefy zrzutu...", "yellow")

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
                        text=f"STREFA ZRZUTU: {drop_pt['name']}",
                    )
                    names = [d["name"] for d in self.dropoff_points]
                    self.dropoff_list_label.configure(
                        text=f"Dodane zrzuty ({len(names)}):\n" + ", ".join(names),
                        text_color="cyan",
                    )
                    self.dropoff_entry.delete(0, "end")

                self.after(0, update_dropoff_ui)
                self.update_status("Dodano strefę zrzutu!", "cyan")
            else:
                self.update_status("Nie znaleziono strefy zrzutu!", "red")
        except Exception as e:
            self.update_status(f"Błąd strefy zrzutu: {str(e)}", "red")

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
        file_paths = filedialog.askopenfilenames(
            filetypes=[("Pliki zleceń (.pdf, .xlsx, .csv)", "*.pdf *.xlsx *.csv")]
        )
        if not file_paths:
            return

        threading.Thread(
            target=self.process_files, args=(file_paths,), daemon=True
        ).start()

    def process_files(self, file_paths):
        try:
            self.update_status("Odczytywanie plików zleceń...", "yellow")
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
                        f"Szukam na mapie ({idx + 1}/{total}):\n{name}", "yellow"
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
                f"Załadowano {count} z {total} punktów ze zleceń!",
                "cyan" if count > 0 else "orange",
            )

        except Exception as e:
            self.update_status(f"Błąd odczytu: {str(e)}", "red")

    def clear_loaded_markers(self):
        self.map_widget.delete_all_marker()
        if self.start_point:
            self.start_marker = self.map_widget.set_marker(
                self.start_point["lat"],
                self.start_point["lon"],
                text=f"BAZA: {self.start_point['name']}",
            )
        for drop_pt in self.dropoff_points:
            self.map_widget.set_marker(
                drop_pt["lat"],
                drop_pt["lon"],
                text=f"STREFA ZRZUTU: {drop_pt['name']}",
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
        self.route_textbox.insert("1.0", "Brak wyznaczonej trasy.")
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
        if not self.loaded_points:
            self.update_status("Wgraj najpierw pliki zleceń!", "orange")
            return

        self.sync_bags_from_gui()
        threading.Thread(target=self.calculate_osrm_multi_trip, daemon=True).start()

    def calculate_osrm_multi_trip(self):
        try:
            self.update_status("Optymalizacja kursów...", "yellow")

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
                self.update_status("Ustaw najpierw punkt startowy (Bazę)!", "orange")
                return

            if not self.dropoff_points:
                self.update_status("Dodaj przynajmniej 1 strefę zrzutu!", "orange")
                return

            all_initial_pts = [self.start_point] + list(self.loaded_points)
            coords_str = ";".join([f"{pt['lon']},{pt['lat']}" for pt in all_initial_pts])
            url_trip = f"http://router.project-osrm.org/trip/v1/driving/{coords_str}?overview=false&source=first"

            res = requests.get(url_trip, timeout=15).json()
            if res.get("code") != "Ok":
                self.update_status("Błąd API OSRM!", "red")
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
            list_text = f"TRASA: {self.route_name_entry.get().strip() or 'Plan Przejazdu'}\n"
            list_text += f"Liczba kursów: {len(trips)} | Pojemność vana: {vehicle_capacity} worków (240L)\n"
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

                list_text += f"--- KURS #{trip_idx} (Załadunek: {trip_units}/{vehicle_capacity} ekwiwalentu 240L) ---\n"
                list_text += f"START [{trip_start_str}]: {current_start_node['name']}\n"
                self.ordered_points_list.append(
                    f"START KURSU #{trip_idx} [{trip_start_str}]: {current_start_node['name']}")

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

                    entry_line = f"{stop_counter}. {pt['name']} [{details}]\n   -> Przyjazd: {arrival_str} | Odjazd: {dep_str}"
                    list_text += f"{entry_line}\n"
                    self.ordered_points_list.append(entry_line)
                    stop_counter += 1

                if len(legs) > len(trip_points):
                    last_leg_drive_min = round(legs[-1]["duration"] / 60)
                    total_driving_duration_min += last_leg_drive_min
                    current_time += timedelta(minutes=last_leg_drive_min)

                dropoff_arrival_str = current_time.strftime("%H:%M")

                full_ordered_coords_gmaps.append(f"{chosen_dropoff['lat']},{chosen_dropoff['lon']}")
                dropoff_line = f"---> ZRZUT [{dropoff_arrival_str}]: {chosen_dropoff['name']} (Rozładunek kursu)\n\n"
                list_text += dropoff_line
                self.ordered_points_list.append(
                    f"ZRZUT KURSU #{trip_idx} [{dropoff_arrival_str}]: {chosen_dropoff['name']}")

                current_time += timedelta(minutes=10)
                total_service_duration_min += 10

                current_start_node = chosen_dropoff

            total_overall_time_min = total_driving_duration_min + total_service_duration_min
            total_hours = total_overall_time_min // 60
            total_mins = total_overall_time_min % 60

            header_summary = f"Dystans łączny: {total_distance_km:.1f} km\n"
            header_summary += f"Łączny czas pracy: {total_hours}h {total_mins}m (Jazda: {total_driving_duration_min}m, Postoje: {total_service_duration_min}m)\n"
            header_summary += "-----------------------------------\n\n"

            final_full_text = list_text[:list_text.find("===================\n\n") + 21] + header_summary + list_text[
                list_text.find("===================\n\n") + 21:]

            def render_multi_trip_results():
                self.map_widget.delete_all_marker()

                self.start_marker = self.map_widget.set_marker(
                    self.start_point["lat"], self.start_point["lon"], text=f"START/BAZA: {self.start_point['name']}"
                )
                for drop_pt in self.dropoff_points:
                    self.map_widget.set_marker(
                        drop_pt["lat"], drop_pt["lon"], text=f"STREFA ZRZUTU: {drop_pt['name']}"
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
                    f"Wyznaczono {len(trips)} kursy!\nDystans: {total_distance_km:.1f} km | Czas pracy: {total_hours}h {total_mins}m",
                    "lime",
                )

            self.after(0, render_multi_trip_results)

        except Exception as e:
            self.update_status(f"Błąd optymalizacji: {str(e)}", "red")

    def open_in_gmaps(self):
        if self.gmaps_url:
            webbrowser.open(self.gmaps_url)

    def export_route_to_file(self):
        if not self.ordered_points_list:
            return

        route_title = self.route_name_entry.get().strip() or "Plan_Trasy"
        safe_filename = (
                re.sub(r'[\\/*?:"<>|]', "", route_title).replace(" ", "_") + ".txt"
        )

        file_path = filedialog.asksaveasfilename(
            initialfile=safe_filename,
            defaultextension=".txt",
            filetypes=[("Plik Tekstowy", "*.txt")],
            title="Zapisz plan trasy",
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"PLAN TRASY: {route_title.upper()}\n")
                    f.write("========================\n\n")
                    for line in self.ordered_points_list:
                        f.write(f"{line}\n")
                    if self.gmaps_url:
                        f.write(
                            f"\nLink do Google Maps:\n{self.gmaps_url}\n"
                        )
                self.update_status("Zapisano plan do pliku!", "cyan")
            except Exception as e:
                self.update_status(f"Błąd zapisu: {str(e)}", "red")


if __name__ == "__main__":
    app = RoutePlannerApp()
    app.mainloop()