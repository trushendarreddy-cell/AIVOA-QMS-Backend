import os
import traceback
from typing import TypedDict, Optional, List
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.1,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

class ExtractedComplaintData(BaseModel):
    customerName: Optional[str] = Field(description="Name of the customer, hospital, or distributor reporting the issue.", default="Unknown Customer")
    productId: Optional[str] = Field(description="Product name, code, or SKU.", default="Unknown Product")
    strength: Optional[str] = Field(description="Dosage strength or concentration if mentioned.", default=None)
    batchNumber: Optional[str] = Field(description="Batch or lot number of the product.", default=None)
    manufacturingDate: Optional[str] = Field(description="Manufacturing date if mentioned.", default=None)
    expiryDate: Optional[str] = Field(description="Expiry or retest date if mentioned.", default=None)
    affectedQuantity: Optional[str] = Field(description="Quantity affected or returned.", default=None)
    issueCategory: Optional[str] = Field(description="Category of issue: Packaging Defect, Contamination, Adverse Event, Labeling Error, or Other.", default="Packaging Defect")
    complaintDescription: Optional[str] = Field(description="Detailed summary of the complaint.", default="")
    urgencyLevel: Optional[str] = Field(description="Urgency level evaluated as Low, Medium, High, or Critical.", default="Medium")

class CompletenessCheckData(BaseModel):
    is_complete: bool = Field(description="True if critical fields (customer name, product name, batch number, affected quantity, description) are present. False if any critical information is missing.")
    missing_fields: List[str] = Field(description="List of vital pharmaceutical fields that were missing from the complaint.")
    completeness_message: str = Field(description="A concise status summary message regarding completeness.")

class RiskAssessmentData(BaseModel):
    summary: Optional[str] = Field(description="A concise, professional QA-friendly summary of the complaint.", default="Complaint recorded for review.")
    riskLevel: Optional[str] = Field(description="Risk severity level: Low, Moderate, High, or Critical.", default="Moderate")
    riskReason: Optional[str] = Field(description="Justification for the assigned risk level based on pharmaceutical compliance standards.", default="Standard QA evaluation.")
    recommendedAction: Optional[str] = Field(description="Suggested immediate containment or QA action.", default="Isolate affected batch.")
    safetyImpact: Optional[str] = Field(description="Potential patient or product safety impact.", default="Requires review.")
    investigationRequired: Optional[str] = Field(description="Type of root cause investigation required (e.g., Lab, Packaging Line, Supplier).", default="Standard Lab Investigation")
    rootCauseHypothesis: Optional[str] = Field(description="Predicted pharmaceutical manufacturing or packaging root cause.", default="Pending investigation.")
    capaRecommendation: Optional[str] = Field(description="Corrective and Preventive Action (CAPA) recommendation for audit compliance.", default="Perform line clearance and equipment audit.")
    missingFields: Optional[List[str]] = Field(description="List of any critical pharmaceutical fields that were missing.", default=[])

class QMSState(TypedDict):
    raw_prompt: str
    extracted_data: Optional[dict]
    completeness_data: Optional[dict]
    risk_assessment: Optional[dict]
    validation_status: str
    error: Optional[str]

import json # Make sure to add this at the top of workflow.py!

def extract_node(state: QMSState):
    # Fetch the current state of the form to pass to the AI
    current_data = state.get("extracted_data") or {}
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert pharmaceutical Quality Management AI. 
        Your job is to update an existing complaint form based on user instructions.
        
        === CURRENT FORM DATA ===
        {current_data}
        
        === OVERRIDE RULES ===
        1. The user will provide a new prompt or instruction. Treat this as an OVERRIDE command.
        2. If the user asks to change, update, or correct a value (e.g., "change 500 to 50"), you MUST apply this change to the relevant field.
        3. For all other fields that the user did not mention, copy the exact values from the CURRENT FORM DATA into your response.
        4. Do not leave fields blank or revert them to defaults if they have data in the current form.
        """),
        ("human", "New Instruction / Update:\n{text}")
    ])
    
    structured_llm = llm.with_structured_output(ExtractedComplaintData)
    chain = prompt | structured_llm
    
    try:
        # Use json.dumps to ensure the AI reads the dictionary perfectly
        result = chain.invoke({
            "text": state["raw_prompt"],
            "current_data": json.dumps(current_data, indent=2) 
        })
        return {"extracted_data": result.model_dump(), "validation_status": "extracted"}
    except Exception as e:
        print("ERROR IN EXTRACT NODE:")
        traceback.print_exc()
        return {"error": str(e), "validation_status": "failed"}
def completeness_node(state: QMSState):
    data = state.get("extracted_data", {})
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a pharmaceutical compliance auditor. Evaluate whether the complaint data contains essential fields: customer name, product name, batch/lot number, affected quantity, and complaint description. Do not invent missing info."),
        ("human", "Extracted Complaint Data:\n{data}")
    ])
    structured_llm = llm.with_structured_output(CompletenessCheckData)
    chain = prompt | structured_llm
    try:
        result = chain.invoke({"data": str(data)})
        return {"completeness_data": result.model_dump(), "validation_status": "checked_completeness"}
    except Exception as e:
        print("ERROR IN COMPLETENESS NODE:")
        traceback.print_exc()
        return {"error": str(e), "validation_status": "completeness_failed"}

def assess_risk_node(state: QMSState):
    data = state.get("extracted_data", {})
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a pharmaceutical QA Compliance expert. Based on the extracted complaint data, generate a concise AI summary, evaluate risk level, patient safety impact, root cause hypothesis, and CAPA recommendations."),
        ("human", "Complaint Details:\n{complaint_info}")
    ])
    structured_llm = llm.with_structured_output(RiskAssessmentData)
    chain = prompt | structured_llm
    try:
        result = chain.invoke({"complaint_info": str(data)})
        return {"risk_assessment": result.model_dump(), "validation_status": "completed"}
    except Exception as e:
        print("ERROR IN RISK NODE:")
        traceback.print_exc()
        return {"error": str(e), "validation_status": "risk_failed"}

workflow = StateGraph(QMSState)
workflow.add_node("extract_complaint", extract_node)
workflow.add_node("check_completeness", completeness_node)
workflow.add_node("assess_risk", assess_risk_node)

workflow.set_entry_point("extract_complaint")
workflow.add_edge("extract_complaint", "check_completeness")
workflow.add_edge("check_completeness", "assess_risk")
workflow.add_edge("assess_risk", END)

compiled_workflow = workflow.compile()