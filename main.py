from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db, ComplaintDB, init_db
from workflow import compiled_workflow
import io
from pypdf import PdfReader
import traceback

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for React frontend (Vite runs on localhost:5173 by default)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PromptRequest(BaseModel):
    prompt: str

class DuplicateCheckRequest(BaseModel):
    customerName: str
    productId: str
    batchNumber: str = None

@app.post("/api/upload-extract")
async def upload_and_extract(file: UploadFile = File(...)):
    try:
        content = await file.read()
        text = ""
        filename = file.filename.lower()
        
        # Extract text based on file format
        if filename.endswith(".pdf"):
            reader = PdfReader(io.BytesIO(content))
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        elif filename.endswith((".txt", ".eml", ".csv")):
            text = content.decode("utf-8", errors="ignore")
        else:
            text = f"Uploaded document: {file.filename}. (Pharmaceutical complaint document / image file attached for AI compliance review)."

        if not text.strip():
            text = f"Complaint document: {file.filename}"

        # Run LangGraph workflow with extracted text
        initial_state = {
            "raw_prompt": text,
            "extracted_data": None,
            "completeness_data": None,
            "risk_assessment": None,
            "validation_status": "pending",
            "error": None
        }
        final_state = compiled_workflow.invoke(initial_state)
        
        if final_state.get("error"):
            raise HTTPException(status_code=500, detail=final_state["error"])
            
        return {
            "extracted": final_state.get("extracted_data"),
            "completenessData": final_state.get("completeness_data"),
            "riskAssessment": final_state.get("risk_assessment"),
            "rawText": text
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/extract")
def extract_complaint_workflow(req: PromptRequest):
    try:
        initial_state = {
            "raw_prompt": req.prompt,
            "extracted_data": None,
            "completeness_data": None,
            "risk_assessment": None,
            "validation_status": "pending",
            "error": None
        }
        
        # Execute LangGraph workflow
        final_state = compiled_workflow.invoke(initial_state)
        
        if final_state.get("error"):
            raise HTTPException(status_code=500, detail=final_state["error"])
            
        return {
            "extracted": final_state.get("extracted_data"),
            "completenessData": final_state.get("completeness_data"),
            "riskAssessment": final_state.get("risk_assessment")
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# Duplicate Detection Endpoint
@app.post("/api/check-duplicate")
def check_duplicate(req: DuplicateCheckRequest, db: Session = Depends(get_db)):
    try:
        query = db.query(ComplaintDB).filter(
            ComplaintDB.customerName.ilike(f"%{req.customerName}%"),
            ComplaintDB.productId.ilike(f"%{req.productId}%")
        )
        if req.batchNumber:
            query = query.filter(ComplaintDB.batchNumber == req.batchNumber)
            
        existing = query.first()
        if existing:
            return {
                "duplicate_detected": True,
                "possible_duplicate_id": existing.id,
                "duplicate_reason": f"Similar complaint found with ID #{existing.id} for customer '{existing.customerName}' and product '{existing.productId}'."
            }
        return {"duplicate_detected": False}
    except Exception as e:
        return {"duplicate_detected": False, "error": str(e)}

@app.post("/api/complaints")
def save_complaint(data: dict, db: Session = Depends(get_db)):
    try:
        extracted = data.get("extracted", {})
        risk = data.get("riskAssessment", {})
        completeness = data.get("completenessData", {})
        
        db_item = ComplaintDB(
            complaintSource=extracted.get("complaintSource", "Pharmacy"),
            customerName=extracted.get("customerName"),
            productId=extracted.get("productId"),
            strength=extracted.get("strength"),
            batchNumber=extracted.get("batchNumber"),
            affectedQuantity=extracted.get("affectedQuantity"),
            manufacturingDate=extracted.get("manufacturingDate"),
            expiryDate=extracted.get("expiryDate"),
            issueCategory=extracted.get("issueCategory"),
            complaintDescription=extracted.get("complaintDescription"),
            urgencyLevel=extracted.get("urgencyLevel"),
            riskLevel=risk.get("riskLevel"),
            riskReason=risk.get("riskReason"),
            recommendedAction=risk.get("recommendedAction"),
            safetyImpact=risk.get("safetyImpact"),
            investigationRequired=risk.get("investigationRequired"),
            rootCause=risk.get("rootCauseHypothesis"),
            capaRecommendation=risk.get("capaRecommendation"),
            summary=risk.get("summary"),
            isComplete=completeness.get("is_complete", True),
            missingFields=", ".join(completeness.get("missing_fields", [])),
            status="OPEN"
        )
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return {"message": "Complaint saved successfully with hybrid demo fields", "id": db_item.id}
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/complaints")
def get_complaints(db: Session = Depends(get_db)):
    return db.query(ComplaintDB).all()

# Update Complaint Status Endpoint
class StatusUpdateRequest(BaseModel):
    status: str

@app.patch("/api/complaints/{complaint_id}/status")
def update_complaint_status(complaint_id: int, req: StatusUpdateRequest, db: Session = Depends(get_db)):
    try:
        complaint = db.query(ComplaintDB).filter(ComplaintDB.id == complaint_id).first()
        if not complaint:
            raise HTTPException(status_code=404, detail="Complaint not found")
        
        valid_statuses = ["OPEN", "UNDER_INVESTIGATION", "QA_REVIEW", "CLOSED"]
        if req.status not in valid_statuses:
            raise HTTPException(status_code=400, detail="Invalid status workflow value")
            
        complaint.status = req.status
        db.commit()
        return {"message": f"Status updated to {req.status}", "id": complaint.id, "status": complaint.status}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Initialize database table structures
init_db()