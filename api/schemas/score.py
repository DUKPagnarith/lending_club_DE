from pydantic import BaseModel, Field
from typing import Optional


class ScoreRequest(BaseModel):
    loan_amnt: float = Field(..., gt=0, description="Requested loan amount ($)")
    funded_amnt: float = Field(..., gt=0, description="Funded loan amount ($)")
    term_int: int = Field(..., ge=36, le=60, description="Loan term in months (36 or 60)")
    int_rate: float = Field(..., gt=0, lt=1, description="Interest rate as decimal (e.g. 0.1199)")
    grade: str = Field(..., description="Loan grade A–G")
    emp_length_int: int = Field(..., ge=0, le=10, description="Employment length in years (0–10+)")
    home_ownership: str = Field(..., description="RENT | OWN | MORTGAGE | OTHER")
    annual_inc: float = Field(..., gt=0, description="Annual income ($)")
    verification_status: str = Field(..., description="Verified | Source Verified | Not Verified")
    purpose: str = Field(..., description="Loan purpose (debt_consolidation, credit_card, …)")
    dti: float = Field(..., ge=0, description="Debt-to-income ratio (%)")
    fico_score: float = Field(..., ge=300, le=850, description="FICO score")
    inq_last_6mths: int = Field(..., ge=0, description="Credit inquiries in last 6 months")
    revol_util: float = Field(..., ge=0, lt=2, description="Revolving utilization as decimal")
    mths_since_last_delinq: Optional[float] = Field(None, description="Months since last delinquency (None = never)")
    initial_list_status: str = Field("w", description="w | f")
    mths_since_issue_d: Optional[int] = Field(None, description="Months since loan issued")
    mths_since_earliest_cr_line: Optional[float] = Field(None, description="Months since earliest credit line")

    model_config = {"json_schema_extra": {"example": {
        "loan_amnt": 15000, "funded_amnt": 15000, "term_int": 36,
        "int_rate": 0.1199, "grade": "B", "emp_length_int": 5,
        "home_ownership": "MORTGAGE", "annual_inc": 75000,
        "verification_status": "Verified", "purpose": "debt_consolidation",
        "dti": 18.5, "fico_score": 710, "inq_last_6mths": 1,
        "revol_util": 0.42, "mths_since_last_delinq": None,
        "initial_list_status": "w", "mths_since_issue_d": 60,
        "mths_since_earliest_cr_line": 160,
    }}}


class ScoreResponse(BaseModel):
    pd: float = Field(..., description="Probability of Default")
    lgd: float = Field(..., description="Loss Given Default")
    ead: float = Field(..., description="Exposure at Default ($)")
    expected_loss: float = Field(..., description="Expected Loss = PD × LGD × EAD ($)")
    credit_score: int = Field(..., description="Credit score (300–850)")
    risk_class: str = Field(..., description="Risk class AA | A | AB | BB | B | BC | C | CD | DD | F")
    decision: str = Field(..., description="AUTO_APPROVE | APPROVE | REJECT | AUTO_REJECT")
    annualized_roi: float = Field(..., description="Annualized ROI after expected loss")
    model_version: str = Field(..., description="Model version used")


class HealthResponse(BaseModel):
    status: str
    models_loaded: bool
    version: str
