from pydantic import BaseModel, Field
from typing import Optional

# What the frontend sends to FastAPI
class ExtractRequest(BaseModel):
    text: str

# The structured data fields the AI must extract to fill your form
class ComplaintExtractionResponse(BaseModel):
    customerName: Optional[str] = Field(None, description="Name of the customer or reporting organization")
    productId: Optional[str] = Field(None, description="Name or ID of the product mentioned")
    issueCategory: Optional[str] = Field(None, description="Category like Adverse Event, Product Quality, Packaging, or General Inquiry")
    complaintDescription: Optional[str] = Field(None, description="Detailed summary of the complaint")
    urgencyLevel: Optional[str] = Field("Low", description="Urgency level evaluated as Low, Medium, or High")