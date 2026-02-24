# Product Requirements Document (PRD)

## Product Name

DFM Engine v1 (CNC Milling – Geometry & Rule-Based Analysis)

## Purpose

The purpose of DFM Engine v1 is to provide **deterministic, explainable Design for Manufacturability (DFM) feedback** based on solid CAD models. The system analyzes STEP files and returns rule-based manufacturability risks for **3-axis CNC milling**.

This version explicitly **does not use AI or machine learning**. All outputs must be reproducible, debuggable, and explainable to a manufacturing engineer.

---

## In Scope (v1)

- STEP file ingestion
- Solid geometry validation
- Core geometric feature extraction
- Rule-based DFM feedback for CNC milling
- JSON-based API responses

## Out of Scope (v1)

- AI / ML / LLM-based reasoning
- Cost estimation
- UI or visualization
- Non-CNC processes (turning, injection molding, sheet metal, additive)
- Tolerance stack-up analysis
- Toolpath generation

---

## Target Users

- Manufacturing engineers
- CNC process engineers
- DFM reviewers
- Quoting engineers
- Downstream systems (ERP / quoting tools)

---

## Assumptions & Constraints

- Input CAD files are provided in STEP format (.step / .stp)
- Models represent a single manufacturable part (no assemblies)
- Geometry units are either millimeters or inches
- Analysis is performed for **3-axis CNC milling only**
- Deterministic output is required (same input → same output)

---

## System Architecture (High-Level)

- **Backend Framework**: FastAPI
- **Geometry Kernel**: OpenCascade (pythonocc-core)
- **Execution Model**: Synchronous (v1)
- **Integration**: REST API

The DFM Engine operates as an independent service and must not depend on any frontend or framework-specific logic.

---

## Functional Requirements

### FR-1: STEP File Ingestion

- The system shall accept STEP files via a REST API endpoint
- The system shall reject unsupported file formats
- The system shall store uploaded files temporarily for analysis

### FR-2: Geometry Validation

- The system shall verify that the STEP file contains at least one valid solid
- The system shall reject empty, invalid, or non-solid geometries
- The system shall identify and report geometry parsing errors

### FR-3: Unit Detection

- The system shall detect whether the model is in millimeters or inches
- The system shall normalize all internal calculations to millimeters

### FR-4: Bounding Box Extraction

- The system shall compute the axis-aligned bounding box of the part
- The system shall return overall dimensions (X, Y, Z)

### FR-5: Hole Feature Extraction

- The system shall identify cylindrical faces
- The system shall extract hole radius and axis direction
- The system shall calculate hole depth
- The system shall classify holes as blind or through

### FR-6: Basic Face Classification

- The system shall identify planar faces
- The system shall identify candidate setup faces (largest planar faces)

### FR-7: DFM Rule Evaluation (CNC Milling)

- The system shall evaluate extracted features against predefined DFM rules
- Each rule shall operate independently
- Rules shall not mutate geometry or features

### FR-8: DFM Feedback Generation

- The system shall generate structured feedback objects
- Each feedback item shall include:
  - Rule identifier
  - Message
  - Severity level (low / medium / high)
  - Affected feature reference

---

## Initial DFM Rule Set (v1)

### Rule 1: Hole Depth-to-Diameter Ratio

- Condition: depth / diameter > 10
- Severity: High
- Rationale: Requires special tooling and increases cost

### Rule 2: Minimum Hole Diameter

- Condition: diameter < 2 mm
- Severity: Medium
- Rationale: Standard tooling limitations

### Rule 3: Minimum Wall Thickness

- Condition: wall thickness < 1 mm
- Severity: High
- Rationale: Risk of deformation or breakage

### Rule 4: Sharp Internal Corners

- Condition: internal corner radius < tool minimum
- Severity: Medium
- Rationale: Requires smaller tools, increases machining time

---

## API Requirements

### Endpoint: POST /analyze

**Request**

- Multipart form-data
- File field: `file` (STEP file)

**Response (JSON)**

```json
{
  "status": "success",
  "units": "mm",
  "bounding_box": {
    "x": 120.0,
    "y": 80.0,
    "z": 40.0
  },
  "features": {
    "holes": [
      {
        "id": "hole_1",
        "diameter": 6.0,
        "depth": 80.0,
        "type": "blind"
      }
    ]
  },
  "dfm_feedback": [
    {
      "rule_id": "CNC_HOLE_DEPTH_RATIO",
      "severity": "high",
      "message": "Hole depth-to-diameter ratio exceeds recommended limit",
      "feature_id": "hole_1"
    }
  ]
}
```

---

## Non-Functional Requirements

### Performance

- Analysis time < 5 seconds for typical single-part STEP files

### Reliability

- Geometry parsing failures must not crash the service
- Errors must be returned with actionable messages

### Explainability

- Every feedback item must be traceable to a specific rule
- No black-box decisions are allowed

### Maintainability

- Rules must be implemented as isolated, testable functions
- Feature extraction and rule evaluation must be decoupled

---

## Error Handling

- Invalid file format → 400 Bad Request
- Geometry parsing failure → 422 Unprocessable Entity
- Internal processing error → 500 Internal Server Error

---

## Success Criteria (v1)

- The system successfully analyzes real CNC-milled parts
- Feedback is consistent and explainable
- Manufacturing engineers can validate rule correctness
- The engine can be integrated into a larger platform without refactoring

---

## Explicit Non-Goals

- Predictive manufacturability scoring using AI
- Automated design optimization
- Toolpath or CAM output
- Visual CAD markup

---

## Long-Term Extension Points

- Additional CNC rules
- Other manufacturing processes
- AI-assisted cost and risk prediction (post-v1)

---

## Final Note

This PRD defines a **foundational DFM engine**, not a demo. If these requirements are met cleanly, the system is a valid base for industrial-scale extensions. Anything added before this foundation is complete increases technical debt and reduces credibility.
