# Smart Building Security Automation

This repository implements a modular Python pipeline to automate access control configuration in smart buildings using the VEREFOO framework. It takes SRL JSON input, generates VEREFOO-compatible XML, runs analysis in parallel, and aggregates the results.

---

## Repository Structure

```
smartbuilding_security/
├── main.py                  # Entry point: orchestrates the whole pipeline
├── config.py                # Global paths and settings
├── requirements.txt         # Python dependencies

├── srl/
│   └── srl_validator.py     # Validates SRL JSON input

├── translator/
│   └── translator.py        # Translates SRL JSON into VEREFOO-compatible XML files

├── executor/
│   └── verefoo_runner.py    # Runs VEREFOO in parallel for each XML input

├── aggregator/
│   └── aggregator.py        # Aggregates all outputs into a global JSON configuration

├── utils/
│   └── xml_utils.py         # Utilities for XML parsing and generation

├── data/
│   ├── input_srl.json       # Input SRL file
│   ├── verefoo_inputs/      # Folder for generated VEREFOO input XML files
│   └── verefoo_outputs/     # Folder for output files from VEREFOO

└── README.md
```

---

## How to Run the Pipeline

1. **Install required dependencies**:

```bash
pip install -r requirements.txt
```

2. **Place your SRL JSON** in:

```
data/input_srl.json
```

3. **Run the main script**:

```bash
python main.py
```

4. **Check the results**:

- Input XMLs: `data/verefoo_inputs/`
- VEREFOO outputs: `data/verefoo_outputs/`
- Final aggregated configuration: `data/final_config.json`

---

## Features

- **Validation**: ensures the SRL is correctly structured
- **Translation**: supports device mapping and inter-area rule propagation
- **Parallel Execution**: optimizes performance on large topologies
- **Aggregation**: merges results while checking for redundancy and conflicts

---

## Requirements

- Python 3.8 or higher
- Java Runtime (for executing VEREFOO)

### Python Dependencies
Listed in `requirements.txt`:

```
lxml
xmltodict
tqdm
```

Install them with:

```bash
pip install -r requirements.txt
```

---

## Device Type Mapping

Unsupported devices such as sensors, smart bulbs, and cameras are automatically mapped to supported VEREFOO types (e.g., `WEBCLIENT`) to ensure compatibility.

---

## Input Format (SRL JSON)

Here's a minimal example:

```json
{
  "global_network": {
    "connections": [
      {"from": "Office2", "to": "Office1", "rule": "deny"},
      {"from": "Office1", "to": "Lobby", "rule": "allow"}
    ]
  },
  "areas": [
    {
      "name": "Office1",
      "devices": [
        {"id": "office1_camera1", "type": "CAMERA", "ip": "130.10.0.1", "neighbors": ["1.0.0.1"]}
      ],
      "requested_policies": [
        {"rule": "deny", "source": "130.10.0.1", "target": "192.168.3.1", "dst_port": "80", "protocol": "TCP"}
      ]
    }
  ]
}
```

## Output Format (Aggregated JSON)

The final output is a single JSON file containing all devices, security rules, and verified configurations:

```json
{
  "global_configuration": {
    "global_network": {
      "connections": [
        {"from": "Office2", "to": "Office1", "rule": "deny"},
        {"from": "Office1", "to": "Lobby", "rule": "allow"}
      ]
    },
    "areas": [
      {
        "name": "Office_1",
        "devices": [
          {"id": "130.10.0.1", "type": "CAMERA", "configuration": { ... }},
          {"id": "1.0.0.1", "type": "WEBSERVER", "configuration": { ... }}
        ],
        "verified_policies": [
          {"rule": "deny", "source": "130.10.0.1", "target": "192.168.3.1"},
          {"rule": "allow", "source": "130.10.0.1", "target": "1.0.0.1"}
        ]
      }
    ]
  }
}
```

---

## External Dependencies

- [VEREFOO](https://github.com/netgroup-polito/verefoo): Make sure the VEREFOO binary is executable from the command line (e.g., `java -jar verefoo.jar input.xml > output.xml`)
- Java runtime is required to run the VEREFOO JAR file
