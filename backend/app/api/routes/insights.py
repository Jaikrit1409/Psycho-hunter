from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.client import Client
from app.models.evidence import Evidence
from app.models.insight import Insight
from app.schemas.insight import InsightCreate, InsightRead

router = APIRouter(tags=["insights"])


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/clients/{client_id}/insights", response_model=InsightRead, status_code=status.HTTP_201_CREATED)
def create_insight_for_client(
    client_id: int,
    insight_data: InsightCreate,
    db: Session = Depends(get_db),
) -> Insight:
    client = db.query(Client).filter(Client.id == client_id).first()
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    if insight_data.evidence_id is not None:
        evidence = db.query(Evidence).filter(Evidence.id == insight_data.evidence_id).first()
        if evidence is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found")
        if evidence.client_id != client_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Evidence does not belong to this client")

    insight = Insight(
        client_id=client_id,
        category=insight_data.category,
        subject=insight_data.subject,
        observation=insight_data.observation,
        confidence=insight_data.confidence,
        evidence_id=insight_data.evidence_id,
    )
    db.add(insight)
    db.commit()
    db.refresh(insight)
    return insight


@router.get("/clients/{client_id}/insights", response_model=list[InsightRead])
def list_insights_for_client(client_id: int, db: Session = Depends(get_db)) -> list[Insight]:
    client = db.query(Client).filter(Client.id == client_id).first()
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

    return db.query(Insight).filter(Insight.client_id == client_id).order_by(Insight.id).all()


@router.get("/insights/{insight_id}", response_model=InsightRead)
def get_insight(insight_id: int, db: Session = Depends(get_db)) -> Insight:
    insight = db.query(Insight).filter(Insight.id == insight_id).first()
    if insight is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found")
    return insight
