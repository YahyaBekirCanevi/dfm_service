# Product Requirements Document (PRD)

# Product Name

**DFM Engine v2 (CNC Milling – Deterministic Geometric Analysis with Localization)**

---

# 1. Purpose

DFM Engine v2 provides deterministic, explainable, and geometrically localized Design for Manufacturability (DFM) feedback for 3-axis CNC milling.

Unlike v1, this version:

- Identifies not only what is wrong
- Precisely identifies where the issue exists in 3D topology
- Returns structured, machine-readable geometric references
- Remains fully deterministic (no AI, no probabilistic logic)

The system must remain suitable for integration into ERP systems, quoting engines, CAD viewers, and automated review pipelines.

---

# 2. In Scope (v2)

- STEP file ingestion
- Solid geometry validation
- Deterministic topology indexing
- Core geometric feature extraction
- Rule-based DFM evaluation
- Geometric localization of violations
- Structured JSON response including geometry index

---

# 3. Out of Scope (v2)

- AI / ML reasoning
- Manufacturability scoring
- Cost estimation
- Toolpath generation
- CAM output
- Tolerance stack-up analysis
- Assembly-level analysis
- UI / visualization logic
- Full BRep export via API

---

# 4. Target Users

- Manufacturing engineers
- CNC process engineers
- Quoting systems
- ERP systems
- CAD visualization services
- Automated design validation pipelines

---

# 5. Technology Stack

## Backend Framework
- FastAPI
- Uvicorn

## Data Modeling
- Pydantic

## File Handling
- python-multipart

## Communication
- REST API (JSON)

The DFM Engine must remain:

- Stateless
- Independent
- UI-agnostic
- Deterministic

---

# 6. Architectural Principles

## 6.1 Deterministic Execution

Same input must always produce identical output.

## 6.2 Strict Layer Separation

```

STEP Import
↓
Topology Indexing
↓
Feature Extraction
↓
Rule Engine
↓
Localization Mapper
↓
API Serialization

```

## 6.3 Rule Isolation

- Rules must not mutate geometry.
- Rules must operate as pure functions.
- Geometry layer must not depend on rule layer.

## 6.4 Stable Geometric References

All topology entities must receive deterministic, reproducible IDs.

---

# 7. Functional Requirements

---

## FR-1: STEP File Ingestion

- Accept STEP files via REST endpoint
- Reject unsupported file formats
- Temporarily store files for analysis
- Enforce single-part constraint

---

## FR-2: Geometry Validation

- Validate presence of at least one solid
- Reject empty or invalid geometries
- Report parsing errors deterministically

---

## FR-3: Unit Detection & Normalization

- Detect model units (mm or inches)
- Normalize all internal calculations to millimeters
- Return detected unit in response

---

## FR-4: Deterministic Topology Indexing

The system shall:

- Traverse all topological entities
- Assign deterministic IDs to:
  - Solids
  - Faces
  - Edges
  - Vertices
- Ensure stable ordering for identical geometry inputs

### ID Format

```

solid_1
face_12
edge_44
vertex_102

```

IDs must remain stable for identical models.

---

## FR-5: Geometry Index Export

The system shall return a structured geometry index including:

### Faces
- Surface type (plane, cylinder, etc.)
- Area
- Centroid
- Normal (if planar)

### Edges
- Curve type
- Length
- Adjacent face IDs
- Vertex references

### Vertices
- XYZ coordinates

The index must not include:
- Full BRep serialization
- Mesh data
- Rendering data

---

## FR-6: Feature Extraction

### Holes
- Diameter
- Depth
- Axis vector
- Blind / Through classification
- Associated face IDs

### Planar Faces
- Identify candidate setup faces (largest planar faces)

---

## FR-7: Rule Engine

- Each rule operates independently
- Rules are implemented as isolated, testable functions
- Rules receive:
  - Feature data
  - Geometry references
- Rules must not mutate geometry

---

## FR-8: Rule Localization

Each DFM violation must include:

- Rule identifier
- Severity level
- Human-readable message
- Affected feature ID (if applicable)
- Geometric references (face/edge/vertex IDs)
- Measured values metadata

Every rule violation must reference at least one geometric entity.

---

# 8. Initial Rule Set (v2)

---

## Rule 1: Hole Depth-to-Diameter Ratio

Condition:

```

depth / diameter > 10

```

Severity: High  
Localization: Hole cylindrical face  

---

## Rule 2: Minimum Hole Diameter

Condition:

```

diameter < 2 mm

```

Severity: Medium  
Localization: Hole cylindrical face  

---

## Rule 3: Minimum Wall Thickness

Condition:

```

wall_thickness < 1 mm

```

Severity: High  
Localization: Opposing faces defining wall  

---

## Rule 4: Sharp Internal Corners

Condition:

```

internal_corner_radius < minimum_tool_radius

```

Severity: Medium  
Localization: Edge entity  

---

# 9. API Specification

---

## Endpoint

```

POST /analyze

```

---

## Request

Multipart form-data:

```

file: STEP file

````

---

## Response Structure (v2)

```json
{
  "status": "success",
  "units": "mm",

  "bounding_box": {
    "x": 120.0,
    "y": 80.0,
    "z": 40.0
  },

  "geometry_index": {
    "solids": {
      "solid_1": {}
    },
    "faces": {
      "face_12": {
        "surface_type": "plane",
        "area": 250.0,
        "centroid": [10.2, 4.0, 0.0],
        "normal": [0, 0, 1]
      }
    },
    "edges": {
      "edge_44": {
        "curve_type": "arc",
        "length": 12.4,
        "radius": 0.5,
        "faces": ["face_12", "face_13"],
        "vertices": ["vertex_101", "vertex_102"]
      }
    },
    "vertices": {
      "vertex_101": {
        "point": [12.0, 4.0, 0.0]
      }
    }
  },

  "features": {
    "holes": [
      {
        "id": "hole_1",
        "diameter": 6.0,
        "depth": 80.0,
        "type": "blind",
        "faces": ["face_12"],
        "axis": [0, 0, 1]
      }
    ]
  },

  "dfm_feedback": [
    {
      "rule_id": "CNC_HOLE_DEPTH_RATIO",
      "severity": "high",
      "message": "Hole depth-to-diameter ratio exceeds recommended limit",
      "feature_id": "hole_1",
      "geometric_references": [
        {
          "type": "face",
          "id": "face_12"
        }
      ],
      "metadata": {
        "ratio": 13.3,
        "max_allowed": 10.0
      }
    }
  ]
}
````

---

# 10. Non-Functional Requirements

## Performance

* Analysis time < 5 seconds for typical single-part STEP files
* Topology indexing must not exceed 30% of total analysis time

## Reliability

* Geometry parsing must not crash the service
* All failures must return structured JSON errors

## Determinism

* Identical input must produce identical:

  * Topology IDs
  * Feature IDs
  * Rule outputs
  * JSON ordering

## Maintainability

* Rules must be isolated and testable
* Clear separation between:

  * Geometry layer
  * Feature layer
  * Rule layer
  * API serialization layer

---

# 11. Error Handling

| Condition                 | Response                  |
| ------------------------- | ------------------------- |
| Invalid file format       | 400 Bad Request           |
| Geometry parsing failure  | 422 Unprocessable Entity  |
| No solid found            | 422                       |
| Internal processing error | 500 Internal Server Error |

All error responses must return structured JSON.

---

# 12. Success Criteria (v2)

The system is considered production-ready when:

* Engineers can identify exact problematic geometry in CAD
* External systems can highlight violations using returned IDs
* Outputs remain deterministic across repeated runs
* New rules can be added without modifying core architecture

---

# 13. Explicit Non-Goals

* AI-based manufacturability scoring
* Automated design optimization
* Embedded visualization
* Full BRep export
* Multi-process DFM

---

# 14. Strategic Positioning

DFM Engine v2 is a deterministic geometric reasoning service and a topology-aware manufacturing intelligence core.

If implemented correctly, it becomes the foundation for:

* Multi-process DFM
* Setup analysis
* 5-axis extensions
* Future AI-assisted cost and risk prediction (layered externally)

This version establishes architectural discipline before expansion.
