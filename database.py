from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Update with your actual MySQL username, password, and port
DATABASE_URL = "mysql+pymysql://root:rushi0991@localhost:3306/aivoa_qms" 

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ComplaintDB(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    complaintSource = Column(String(100), default="Pharmacy")
    customerName = Column(String(255), index=True)
    productId = Column(String(255), index=True)
    strength = Column(String(100), nullable=True)
    batchNumber = Column(String(100), nullable=True)
    affectedQuantity = Column(String(100), nullable=True)
    manufacturingDate = Column(String(100), nullable=True)
    expiryDate = Column(String(100), nullable=True)
    issueCategory = Column(String(100))
    urgencyLevel = Column(String(50))
    complaintDescription = Column(Text)
    
    # AI & Audit Columns
    riskLevel = Column(String(50))
    riskReason = Column(Text)
    recommendedAction = Column(Text)
    safetyImpact = Column(Text)
    investigationRequired = Column(Text)
    rootCause = Column(Text)              
    capaRecommendation = Column(Text)     
    isComplete = Column(Boolean, default=True)           
    missingFields = Column(Text, nullable=True)          
    status = Column(String(50), default="OPEN")          
    summary = Column(Text, nullable=True)                

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()