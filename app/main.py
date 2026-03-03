import shutil
import os
import uuid
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .models.schemas import AnalysisResponse, BoundingBox, Features, HoleFeature, DFMFeedback
from .core.geometry_utils import GeometryEngine
from .core.feature_extraction import FeatureExtractor
from .core.dfm_rules import DFMRulesEngine

app = FastAPI(title="DFM Engine", description="Deterministic DFM analysis for 3-axis CNC milling")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# Temporary storage for uploaded files
TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_geometry_file(file: UploadFile = File(...)):
    filename_lower = file.filename.lower()
    allowed_extensions = {".step", ".stp", ".stl", ".obj"}
    if not any(filename_lower.endswith(ext) for ext in allowed_extensions):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file format. Supported formats: {', '.join(allowed_extensions)}"
        )

    file_id = str(uuid.uuid4())
    temp_file_path = os.path.join(TEMP_DIR, f"{file_id}_{file.filename}")

    try:
        # Save file to temp
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Initialize Engines
        geo_engine = GeometryEngine()
        success = False
        if filename_lower.endswith(".step") or filename_lower.endswith(".stp"):
            success = geo_engine.load_step(temp_file_path)
        elif filename_lower.endswith(".stl"):
            success = geo_engine.load_stl(temp_file_path)
        elif filename_lower.endswith(".obj"):
            success = geo_engine.load_obj(temp_file_path)

        if not success:
            raise HTTPException(status_code=422, detail="Geometry parsing failure. The file may be corrupt or format not supported.")

        # Extract BBox
        dx, dy, dz = geo_engine.get_bounding_box()
        
        # Extract Geometry Index (v2)
        geometry_index = geo_engine.get_geometry_index()
        
        # Extract Features
        extractor = FeatureExtractor(geo_engine.shape, indexer=geo_engine.indexer)
        raw_features = extractor.extract_all_features()

        features_model = Features(
            holes=[HoleFeature(**h) for h in raw_features["holes"]],
            min_wall_thickness=raw_features["min_wall_thickness"]["thickness"],
            internal_corners=raw_features["internal_corners"]
        )

        # Evaluate DFM Rules
        rules_engine = DFMRulesEngine()
        feedback = rules_engine.evaluate_all(raw_features)

        return AnalysisResponse(
            status="success",
            units=geo_engine.get_units(),
            bounding_box=BoundingBox(x=dx, y=dy, z=dz),
            geometry_index=geometry_index,
            features=features_model,
            dfm_feedback=feedback
        )

    except Exception as e:
        # Log error in production
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temp file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
