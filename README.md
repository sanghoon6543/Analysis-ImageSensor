# Image Sensor Analysis GUI Tools

Tkinter-based Python GUI tools for image sensor characterization and raw frame analysis.

This repository contains portfolio-cleaned analysis tools developed for practical image sensor evaluation workflows.
The tools support raw frame loading, frame/region selection, dark-frame correction, characteristic curve analysis, temporal noise analysis, spatial noise analysis, line/frame stability analysis, IQR-based outlier masking, and result export.

> Note: This repository is a portfolio version. Proprietary datasets, confidential product information, internal measurement results, and company-specific parameters are not included.

---

## Overview

Image sensor development requires repeated measurement and analysis of raw frame data under different operating conditions such as exposure, bias, temperature, readout configuration, illumination, and dark conditions.

This repository demonstrates practical Python-based GUI tools used to support that evaluation workflow.

The tools are designed to help engineers:

* Load raw image frame sequences
* Select frame-of-interest and region-of-interest
* Apply optional dark-frame correction
* Visualize raw and processed sensor frames
* Calculate pixel-level and ROI-level statistics
* Analyze characteristic response curves
* Evaluate temporal noise and spatial noise
* Analyze frame stability and line stability
* Apply IQR-based defective/outlier pixel masking
* Export processed results to CSV or clipboard

The main purpose of this repository is to demonstrate practical engineering capability in image sensor characterization, not to provide a fully packaged commercial software product.

---

## Tool Categories

### 1. General Image Sensor Analysis Tools

These tools are intended for general image sensor characterization workflows.

| File                              | Purpose                                                                          |
| --------------------------------- | -------------------------------------------------------------------------------- |
| `CharacteristicCurve.py`          | Signal response and characteristic curve analysis from raw image frame sequences |
| `DarkCurrent.py`                  | Dark current and dark-frame property analysis                                    |
| `TemporalNoise.py`                | Temporal noise analysis from frame stacks                                        |
| `SpatialNoise.py`                 | Spatial noise and non-uniformity analysis                                        |
| `TemporalNoise_FrameStability.py` | Frame-to-frame stability and temporal drift analysis                             |
| `PixelMath.py`                    | Pixel-level utility calculations, if included                                    |

### 2. Digital Pixel Sensor-Specific Tools

The scripts with the `DPS` prefix were developed for a specific digital pixel sensor architecture.

| File                         | Purpose                                                                    |
|------------------------------| -------------------------------------------------------------------------- |
| `DPS_CharacteristicCurve.py` | Characteristic curve analysis for a digital pixel sensor workflow          |
| `DPS_DarkProperties.py`      | Dark property analysis for a digital pixel sensor workflow                 |
| `DPSConfig.py`               | Sensor-specific timing, pixel-value conversion, and lookup-table utilities |

These tools are separated from the general image sensor tools because their timing conversion and parameter handling are specific to a digital pixel sensor architecture.

### 3. Common Helper Modules

| File                | Purpose                                                                                                                                       |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `HelperFunction.py` | Numerical processing functions for image statistics, noise calculation, filtering, ROI handling, curve fitting, and raw data loading          |
| `WidgetHelper.py`   | Common plotting, file dialog, button event, clipboard, and GUI state helper functions                                                         |
| `UI_Builder.py`     | Reusable Tkinter widget builder for generating frames, labels, entries, buttons, comboboxes, and checkbuttons from configuration dictionaries |

---

## Key Features

### Raw Image Handling

* Raw, TIFF, and binary image loading
* Folder-based frame sequence loading
* Multi-frame stack handling
* Frame-of-interest selection
* Region-of-interest selection
* Dark-frame subtraction

### Sensor Metric Extraction

* Temporal average
* Spatial average
* Spatial median
* Temporal noise
* Spatial noise
* Total noise
* Frame noise
* Row/column line noise
* Pixel-level noise statistics
* ROI-level mean and standard deviation

### Outlier and Defective Pixel Handling

* IQR-based outlier masking
* Iterative masking
* Excluding-zero option
* Reusing previous masks
* Visualizing masked regions

### Digital Pixel Sensor-Specific Processing

* Pixel-value to integer conversion
* Pixel-value to time conversion
* Lookup-table-based timing conversion
* Current-density-related conversion
* Sensor-specific parameter handling such as log factor, bit depth, threshold parameter, and system clock

### GUI-Based Engineering Workflow

The tools are implemented as Tkinter GUI applications to support interactive analysis during experimental sensor evaluation.

Typical GUI operations include:

1. Open raw image folder or file
2. Define image size and file format
3. Load sensor frame sequence
4. Select frame-of-interest
5. Select region-of-interest
6. Apply optional dark correction
7. Visualize selected ROI
8. Calculate sensor metrics
9. Apply optional IQR masking
10. Export results

---

## Repository Structure

```text
Analysis_ImageSensor/
├── README.md
├── requirements.txt
├── python/
│   ├── HelperFunction.py
│   ├── WidgetHelper.py
│   ├── UI_Builder.py
│   ├── CharacteristicCurve.py
│   ├── DarkCurrent.py
│   ├── TemporalNoise.py
│   ├── SpatialNoise.py
│   ├── TemporalNoise_FrameStability.py
│   └── DPS/
│      ├── DPSConfig.py
│      ├── DPS_CharacteristicCurve.py
│      └── DPS_DarkProperties.py
├── docs/
│   └── gui_screenshots/
└── sample_data/
    └── README.md
```

---

## How to Run

Install dependencies:

```bash
pip install -r requirements.txt
```

Run each GUI tool directly:

```bash
cd python
python CharacteristicCurve.py
python DarkCurrent.py
python TemporalNoise.py
python SpatialNoise.py
```

Run digital pixel sensor-specific tools:

```bash
cd python/DPS
python DPS_CharacteristicCurve.py
python DPS_DarkProperties.py
```

---

## Requirements

The tools use:

* Python
* NumPy
* pandas
* SciPy
* OpenCV
* Matplotlib
* imageio
* Tkinter

## Example Workflow

### Dark Current Analysis

1. Load dark frame sequence
2. Select ROI and FOI
3. Apply optional dark correction
4. Calculate dark signal statistics
5. Apply IQR masking if needed
6. Export ROI-level or block-level statistics

### Temporal Noise Analysis

1. Load multi-frame raw sensor data
2. Select ROI and FOI
3. Configure system gain and differential mode
4. Calculate temporal noise components
5. Separate pixel noise, frame noise, and line noise
6. Export histogram or noise summary

### Characteristic Curve Analysis

1. Load raw frame sequences from folders or files
2. Select ROI and FOI
3. Calculate response statistics
4. Apply optional pixel-value to time conversion for digital pixel sensor data
5. Apply optional IQR masking
6. Export characteristic curve data

---

## Skills Demonstrated

This repository demonstrates the following engineering capabilities:

* Image sensor characterization
* Raw sensor frame analysis
* Photodetector array data processing
* Temporal and spatial noise analysis
* Dark current analysis
* Characteristic response curve extraction
* Digital pixel sensor timing conversion
* IQR-based outlier masking
* Python-based GUI tool development
* Measurement data automation
* Engineering workflow design for sensor evaluation
* Data-driven feedback for sensor/device development

---

## Portfolio Context

These tools were developed from practical image sensor evaluation workflows.

They were designed to reduce repetitive manual analysis and provide reproducible measurement results during sensor development. The focus is on connecting raw measurement data to engineering metrics that can support design, process, and system-level feedback.

This project is especially relevant to roles involving:

* Image sensor characterization
* CMOS image sensor evaluation
* SWIR image sensor development
* Photodetector array evaluation
* Sensor test automation
* Electro-optical sensor analysis
* Camera/sensor module characterization
* Advanced sensor R&D

---

## Confidentiality Statement

This repository does not include:

* Proprietary raw image datasets
* Product-specific measurement results
* Customer information
* Confidential design parameters
* Internal company documentation
* Process-sensitive information

The code has been cleaned and generalized for portfolio purposes. Any example data should be synthetic, anonymized, or simplified for demonstration.

---

## Author

Sanghoon Kim
Image Sensor / Photodetector / SWIR Sensor Development
