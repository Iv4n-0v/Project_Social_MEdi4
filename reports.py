from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import select, Session
from db import SessionDep
from models import Methodology, MethodologyBenefitLink, Benefit, User

from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

router = APIRouter(tags=["reports"])

@router.get("/methodologies_benefits_users/pdf")
def generate_pdf(session: SessionDep):
    # Crear buffer en memoria
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Título
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Reporte de Metodologías, Beneficios y Usuarios")

    y_position = height - 80
    c.setFont("Helvetica", 12)

    # Obtener todas las metodologías
    metodologias = session.exec(select(Methodology)).all()
    if not metodologias:
        raise HTTPException(status_code=404, detail="No hay metodologías registradas")

    for met in metodologias:
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_position, f"Metodología: {met.name}")
        y_position -= 20
        c.setFont("Helvetica", 12)
        desc = met.description if met.description else "Sin descripción"
        c.drawString(70, y_position, f"Descripción: {desc}")
        y_position -= 20

        # Beneficios asociados
        links = session.exec(
            select(MethodologyBenefitLink).where(MethodologyBenefitLink.methodology_id == met.id)
        ).all()
        if links:
            c.drawString(70, y_position, "Beneficios:")
            y_position -= 15
            for link in links:
                benefit = session.get(Benefit, link.benefit_id)
                if benefit:
                    c.drawString(90, y_position, f"- {benefit.name}: {benefit.description or 'Sin descripción'}")
                    y_position -= 15
        else:
            c.drawString(70, y_position, "Beneficios: Ninguno")
            y_position -= 15

        # Usuarios asignados
        users = session.exec(select(User).where(User.methodology_id == met.id)).all()
        if users:
            c.drawString(70, y_position, "Usuarios asignados:")
            y_position -= 15
            for u in users:
                c.drawString(90, y_position, f"- {u.name} ({u.type})")
                y_position -= 15
        else:
            c.drawString(70, y_position, "Usuarios asignados: Ninguno")
            y_position -= 15

        y_position -= 20

        # Salto de página si es necesario
        if y_position < 100:
            c.showPage()
            y_position = height - 50
            c.setFont("Helvetica", 12)

    c.save()
    buffer.seek(0)

    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": "inline; filename=report.pdf"})