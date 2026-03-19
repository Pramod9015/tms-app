"""
Slip OCR router — accepts a transaction slip image and returns structured fields
extracted via Gemini Vision API.

Supports:
  - Hindi + English handwritten slips
  - Fields: date, amount, mobile, bank_name, account_number, beneficiary_name, reference_number
"""
import io
import json
import base64
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.config import settings
from app.dependencies import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/transactions", tags=["Transactions"])

# ── Response model ────────────────────────────────────────────────────────────

class SlipExtractResult(BaseModel):
    """Fields extracted from a transaction slip image."""
    amount: Optional[str] = None
    date: Optional[str] = None
    mobile_number: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    beneficiary_name: Optional[str] = None
    reference_number: Optional[str] = None
    raw_text: Optional[str] = None       # full text for debugging
    confidence: str = "low"              # low / medium / high
    error: Optional[str] = None


# ── Gemini prompt ─────────────────────────────────────────────────────────────

_PROMPT = """
You are an expert OCR system for Indian financial transaction slips.
The image may contain text in Hindi, English, or both (bilingual).

Extract the following fields from the slip and return ONLY a valid JSON object (no markdown, no extra text):

{
  "amount": "numeric amount in rupees, digits only (e.g. '5000')",
  "date": "date in YYYY-MM-DD format if found, else null",
  "mobile_number": "10-digit mobile number if found, else null",
  "bank_name": "bank name if found (बैंक का नाम), else null",
  "account_number": "account number if found (खाता संख्या), else null",
  "beneficiary_name": "customer/beneficiary name if found (ग्राहक का नाम), else null",
  "reference_number": "reference/receipt/slip number if found, else null",
  "confidence": "high/medium/low based on image clarity and field legibility"
}

Hindi field labels to look for:
- बैंक का नाम = bank name
- खाता संख्या = account number  
- ग्राहक का नाम = customer/beneficiary name
- रुपये = amount
- दिनांक = date
- मोब = mobile

Return ONLY the JSON. No explanation.
"""


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/parse-slip", response_model=SlipExtractResult)
async def parse_slip_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a transaction slip image (JPG/PNG/WEBP).
    Returns extracted fields using Gemini Vision.
    """
    # Validate API key
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Slip OCR is not configured. Add GEMINI_API_KEY to your .env file. "
                   "Get a free key at https://aistudio.google.com/"
        )

    # Validate file type
    content_type = file.content_type or ""
    if not any(t in content_type for t in ["image/jpeg", "image/png", "image/webp", "image/jpg"]):
        # Accept unknown content types gracefully (mobile uploads often have odd types)
        if not file.filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            raise HTTPException(status_code=415, detail="Only JPG, PNG, or WEBP images are supported")

    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:  # 10 MB limit
        raise HTTPException(status_code=413, detail="Image too large (max 10 MB)")

    # Configure Gemini using new google.genai SDK
    try:
        from google import genai
        from google.genai import types as genai_types
    except ImportError:
        raise HTTPException(status_code=500, detail="OCR dependencies not installed. Run: pip install google-genai pillow")

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    # Prepare image
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        img_bytes = buf.getvalue()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot open image: {e}")

    # Call Gemini Vision
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                genai_types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
                _PROMPT,
            ],
        )
        raw_text = response.text.strip()
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise HTTPException(status_code=502, detail=f"Gemini Vision API error: {e}")

    # Parse JSON response
    try:
        # Strip markdown if model added backticks despite instructions
        if raw_text.startswith("```"):
            raw_text = "\n".join(raw_text.split("\n")[1:-1])
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        logger.warning(f"Gemini returned non-JSON: {raw_text[:200]}")
        return SlipExtractResult(raw_text=raw_text, error="Could not parse structured data from image", confidence="low")

    return SlipExtractResult(
        amount=data.get("amount"),
        date=data.get("date"),
        mobile_number=data.get("mobile_number"),
        bank_name=data.get("bank_name"),
        account_number=data.get("account_number"),
        beneficiary_name=data.get("beneficiary_name"),
        reference_number=data.get("reference_number"),
        raw_text=raw_text,
        confidence=data.get("confidence", "low"),
    )
