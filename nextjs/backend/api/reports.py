"""PDF report endpoint — delegates to reportlab-based generator."""
from fastapi import APIRouter, HTTPException
from backend.core.data_manager import data_manager as dm

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/generate")
async def generate_report(station: str | None = None):
    try:
        # Minimal stub — real implementation lives in backend.reports.pdf_generator
        pdf_bytes = dm.get_training_simulation_data()[1]
        return {"report_id": f"RPT-{__import__('random').randint(10000,99999)}",
                "message": "Report generation stub — implement via backend.reports.pdf_generator",
                "content_type": "application/pdf"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{report_id}")
async def download_report(report_id: str):
    return {"report_id": report_id, "status": "not yet implemented"}
