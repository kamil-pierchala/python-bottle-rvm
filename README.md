# Bottle Return Logistics Route Planner

A desktop-based Vehicle Routing Problem (VRP) optimization system designed for Reverse Deposit Return Schemes (DRS). The application automates route generation, vehicle capacity management, multi-trip scheduling, and PDF transport order parsing for bottle collection fleets.

## Overview

In automated bottle return systems, logistics managers face daily challenges in balancing vehicle volume capacities, handling diverse bag dimensions (e.g., standard 240L vs. 1000L BigBags), and optimizing multi-drop transport routes.

This project provides an end-to-end desktop software solution that parses PDF transport orders issued by deposit operators, calculates spatial volume equivalents, organizes multi-trip pickup routes with intermediate disposal stops, and provides detailed driver schedules.

## Key Features

- **Automated Order Parsing**: Direct ingestion and extraction of addresses, store names, and bag quantities from PDF transport documents and Excel/CSV spreadsheets.
- **Volume Equivalent Calculation**: In-app algorithms convert various bag sizes (240L, 1000L, custom) into standard volume equivalents to prevent vehicle overload.
- **Dynamic Fleet & Driver Management**: Integrated JSON-backed vehicle database allowing CRUD operations for vehicles, registration plates, drivers, and default capacities.
- **Multi-Trip Route Optimization**: Automatic route splitting into sequential trips when cumulative cargo volume exceeds vehicle limits, with intelligent redirection to the nearest available disposal site.
- **Schedule Estimation**: Precise arrival and departure timestamp calculations per location based on road distance matrices and customizable loading stay durations.
- **Interactive Mapping & Export**: Visual route presentation powered by TkinterMapView, one-click export to external navigation (Google Maps), and plain-text driver itinerary generation.

## Technical Architecture & Stack

- **GUI Framework**: `CustomTkinter` (Modern Python Desktop UI)
- **Map Visualization**: `TkinterMapView`
- **Routing Engine**: Open Source Routing Machine (OSRM) REST API
- **Geocoding Service**: ArcGIS via `geopy`
- **Document Processing**: `pypdf` (PDF text extraction), `pandas` (Excel/CSV processing)
- **Data Persistence**: JSON-based file storage (`vehicles.json`)

## Problem Formulation & Logic

The system solves a variant of the **Capacitated Vehicle Routing Problem with Multiple Trips (CVRPMT)**:

1. **Volume Normalization**:
   - $1 \times 240\text{L Bag} = 1.0 \text{ Unit}$
   - $1 \times 1000\text{L BigBag} = 4.0 \text{ Units}$
   - $1 \times \text{Custom Bag (120L)} = 0.5 \text{ Units}$

2. **Trip Segmentation Logic**:
   Given a sequence of optimal waypoints derived from spatial distance matrices, the system accumulates cargo volume $V_c$. If adding waypoint $i$ results in $V_c + v_i > V_{\text{capacity}}$, the current trip is closed:
   - The algorithm identifies the closest registered disposal site relative to waypoint $i-1$ using Haversine distance calculations.
   - The vehicle is routed to the disposal site, cargo volume is reset to zero, and a new trip segment is initialized from the disposal location.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Internet connection (required for OSRM routing and ArcGIS geocoding APIs)

### Installation

1. Clone the repository:
   ```bash
   git clone [https://github.com/your-username/bottle-route-planner.git](https://github.com/your-username/bottle-route-planner.git)
   cd bottle-route-planner
   
2. Create and activate a virtual environment:
    ```
    python -m venv .venv
   
    # On Windows:
    .venv\Scripts\activate
    # On macOS/Linux:
    source .venv/bin/activate
   
3. Install required dependencies:
    ```
    pip install customtkinter tkintermapview geopy pandas pypdf requests openpyxl
    
    ```

## Running the Application
Execute the main application script:
```
python main.py
```

## Application Usage Workflow
1. **Set Depot (Base):** Enter the starting address for the driver/vehicle.
2. **Add Disposal Sites:** Define one or more unloading points where vehicles empty collected bags.
3. **Select or Add Vehicle:** Choose a pre-configured vehicle/driver profile or open the Fleet Manager to add a new vehicle entry.
4. **Load Orders:** Select PDF transport orders or Excel/CSV order lists.
5. **Review Cargo:** Adjust bag quantities per store in the UI scrollable container if real-time volume changes occur.
6. **Generate Route:** Run the optimization engine to compute optimal trip sequences, schedules, and map path overlays.
7. **Export:** Export the final itinerary to .txt format or open the full navigation route in Google Maps.

### Project Structure
```
├── main.py
├── vehicles.json
└── README.md
```