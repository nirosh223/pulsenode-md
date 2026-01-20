from fastapi import FastAPI, HTTPException
import math

# 1. Create the FastAPI app instance
app = FastAPI(
    title="PulseNode MD - Clinical Logic Engine",
    description="Physician-verified ASCVD Risk Calculator (2013 PCE Guidelines).",
    version="1.0.0"
)

# 2. Home / Welcome Endpoint
@app.get("/")
def welcome():
    return {"status": "PulseNode MD Online", "message": "Global Clinical Infrastructure Ready."}


# 3. Pediatric Dose Example Endpoint
@app.get("/test-dose")
def calculate_dose(weight: int = 10):
    dose = weight * 15
    return {
        "logic": "Pediatric Paracetamol",
        "weight_kg": weight,
        "recommended_dose_mg": dose
    }


# 4. Core ASCVD Risk Calculation Function
def calculate_pce_risk(age, is_male, is_black, total_chol, hdl, sbp, on_htn_meds, is_smoker, is_diabetic):
    """
    Core math engine based on the 2013 ACC/AHA Pooled Cohort Equations.
    """
    ln_age = math.log(age)
    ln_total_chol = math.log(total_chol)
    ln_hdl = math.log(hdl)
    ln_sbp = math.log(sbp)
    
    # Coefficients based on Gender & Race
    if not is_male and not is_black:  # White Female
        s10 = 0.9665; mean_xb = -29.18
        xb = (-29.799 * ln_age) + (4.884 * ln_age**2) + (13.54 * ln_total_chol) + \
             (-3.114 * ln_age * ln_total_chol) + (-13.578 * ln_hdl) + \
             (3.149 * ln_age * ln_hdl) + ((2.019 if on_htn_meds else 1.957) * ln_sbp) + \
             (0.661 * is_smoker) + (0.657 * is_diabetic)
    
    elif not is_male and is_black:  # Black Female
        s10 = 0.9533; mean_xb = 86.61
        xb = (17.114 * ln_age) + (0.94 * ln_total_chol) + (-18.92 * ln_hdl) + \
             (4.475 * ln_age * ln_hdl) + ((29.29 if on_htn_meds else 27.82) * ln_sbp) + \
             (-6.432 * ln_age * ln_sbp) + (0.691 * is_smoker) + (0.874 * is_diabetic)
    
    elif is_male and not is_black:  # White Male
        s10 = 0.9144; mean_xb = 61.18
        xb = (12.344 * ln_age) + (11.853 * ln_total_chol) + (-2.664 * ln_age * ln_total_chol) + \
             (-7.99 * ln_hdl) + (1.769 * ln_age * ln_hdl) + ((1.996 if on_htn_meds else 1.933) * ln_sbp) + \
             (7.837 * is_smoker) + (-1.795 * ln_age * is_smoker) + (0.658 * is_diabetic)

    else:  # Black Male
        s10 = 0.8954; mean_xb = 19.54
        xb = (2.469 * ln_age) + (0.302 * ln_total_chol) + (-0.307 * ln_hdl) + \
             ((1.916 if on_htn_meds else 1.809) * ln_sbp) + (0.549 * is_smoker) + (0.645 * is_diabetic)

    risk = 1 - (s10 ** math.exp(xb - mean_xb))
    return round(risk * 100, 2)


# 5. ASCVD Risk Endpoint
@app.get("/v1/calculate/ascvd")
def get_ascvd_risk(
    age: int,
    is_male: bool,
    is_black: bool,
    total_chol: float,
    hdl: float,
    sbp: float,
    model_version: str = "pce2013",
    on_htn_meds: bool = False,
    is_smoker: bool = False,
    is_diabetic: bool = False
):
    # 1. Select model version
    if model_version == "pce2013":
        risk_percent = calculate_pce_risk(
            age, is_male, is_black,
            total_chol, hdl, sbp,
            on_htn_meds, is_smoker, is_diabetic
        )

    elif model_version == "prevent2023":
        raise HTTPException(
            status_code=501,
            detail="PREVENT 2023 model not yet implemented"
        )

    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid model_version. Use 'pce2013' or 'prevent2023'."
        )

    # 2. Risk categorization
    category = "Low (<5%)"
    if risk_percent >= 20:
        category = "High (≥20%)"
    elif risk_percent >= 7.5:
        category = "Intermediate (7.5-19.9%)"
    elif risk_percent >= 5:
        category = "Borderline (5-7.4%)"

    # 3. Return response
    return {
        "ten_year_risk": f"{risk_percent}%",
        "risk_category": category,
        "model_version": model_version,
        "disclaimer": "Clinical Decision Support Only. Not a substitute for professional medical judgment."
    }

