# backend/routes/academico.py
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from backend.models.auth_model import User
from backend.models.user_model import (
    UserOut,
    RolEnum,
    Calificacion,
    CalificacionesResponse,
    EstadoUsuarioResponse,
    EstadoEstudianteResponse,
    CertificadosResponse,
    Certificado,
    HorariosResponse,
    Horario,
    ProgresoResponse,
    CursoProgreso,
    TutorResponse,
)
from backend.db.mongodb import (
    get_users_chat_collection,
    get_certificados_collection,
    get_horarios_collection,
    get_progreso_cursos_collection,
    get_tutores_collection,
    get_calificaciones_collection,
)
from backend.auth.deps import get_current_user


router = APIRouter(
    prefix="/api",
    tags=["academico"],
)


# ─────────────────────────────────────────
#  /api/estado-estudiante
# ─────────────────────────────────────────
@router.get("/estado-estudiante", response_model=EstadoEstudianteResponse)
def get_estado_estudiante(user: User = Depends(get_current_user)):
    col = get_users_chat_collection()
    doc = col.find_one({"_id": user.id})

    estado = doc.get("estado", "Activo") if doc else "Activo"
    return EstadoEstudianteResponse(estado=estado)


# ─────────────────────────────────────────
#  /api/tutor
# ─────────────────────────────────────────
@router.get("/tutor", response_model=TutorResponse)
def get_tutor(user: User = Depends(get_current_user)):
    col = get_tutores_collection()
    doc = col.find_one({"user_id": user.id})

    if not doc:
        return TutorResponse(
            nombre="Tutor no asignado",
            contacto="Sin contacto",
        )

    return TutorResponse(
        nombre=doc.get("nombre", "Tutor"),
        contacto=doc.get("contacto", "Sin contacto"),
    )


# ─────────────────────────────────────────
#  /api/certificados
# ─────────────────────────────────────────
@router.get("/certificados", response_model=CertificadosResponse)
def get_certificados(user: User = Depends(get_current_user)):
    col = get_certificados_collection()
    docs = list(col.find({"user_id": user.id}))

    if not docs:
        demo_data = [
            Certificado(
                curso="Excel Intermedio",
                fecha="2025-06-10",
                url="https://zajuna.edu/cert/123",
            ),
            Certificado(
                curso="Programación Básica",
                fecha="2025-04-02",
                url="https://zajuna.edu/cert/456",
            ),
        ]
        return CertificadosResponse(certificados=demo_data)

    certificados = []
    for d in docs:
        certificados.append(
            Certificado(
                curso=d.get("curso") or d.get("programa") or "Certificado",
                fecha=d.get("fecha") or d.get("fecha_emision") or "",
                url=d.get("url"),
                tipo=d.get("tipo", "certificado"),
            )
        )

    return CertificadosResponse(certificados=certificados)


# ─────────────────────────────────────────
#  /api/horarios
# ─────────────────────────────────────────
@router.get("/horarios", response_model=HorariosResponse)
def get_horarios(user: User = Depends(get_current_user)):
    col = get_horarios_collection()
    docs = list(col.find({"user_id": user.id}))

    horarios = [
        Horario(
            curso=doc.get("curso", "Curso"),
            dia=doc.get("dia", "Día"),
            hora=doc.get("hora", "Horario"),
            aula=doc.get("aula"),
        )
        for doc in docs
    ]

    return HorariosResponse(horarios=horarios)


# ─────────────────────────────────────────
#  /api/progreso-cursos
# ─────────────────────────────────────────
@router.get("/progreso-cursos", response_model=ProgresoResponse)
def get_progreso_cursos(user: User = Depends(get_current_user)):
    col = get_progreso_cursos_collection()
    docs = list(col.find({"user_id": user.id}))

    # Opción 1: estructura plana (un documento por curso)
    if docs and "cursos" not in docs[0]:
        cursos = []
        total = 0
        count = 0

        for doc in docs:
            avance = doc.get("avance")
            if isinstance(avance, (int, float)):
                total += avance
                count += 1

            cursos.append(
                CursoProgreso(
                    nombre=doc.get("curso", "Curso"),
                    avance=int(avance) if isinstance(avance, (int, float)) else None,
                )
            )

        avance_global = int(total / count) if count else None
        return ProgresoResponse(avance_global=avance_global, cursos=cursos)

    # Opción 2: documento único con "cursos" y "avance_global"
    if docs:
        doc = docs[0]
        cursos = [
            CursoProgreso(
                nombre=c.get("nombre", "Curso"),
                avance=c.get("avance"),
            )
            for c in doc.get("cursos", [])
        ]
        return ProgresoResponse(
            avance_global=doc.get("avance_global"),
            cursos=cursos,
        )

    # Sin datos → vacío
    return ProgresoResponse(avance_global=None, cursos=[])


# ─────────────────────────────────────────
#  /api/usuarios/{user_id}
# ─────────────────────────────────────────
@router.get("/usuarios/{user_id}", response_model=UserOut)
def get_usuario_detalle(
    user_id: str,
    user: User = Depends(get_current_user),
):
    col = get_users_chat_collection()
    doc = col.find_one({"_id": user_id}) or col.find_one({"id": user_id})

    if not doc:
        return UserOut(
            id=user_id,
            nombre="Estudiante Demo",
            email=user.email,
            rol=RolEnum.usuario,
            documento="123456789",
            programa="Tecnólogo en Gestión Administrativa",
            estado="Activo",
        )

    return UserOut(
        id=str(doc.get("_id") or doc.get("id") or user_id),
        nombre=doc.get("nombre", "Estudiante"),
        email=doc.get("email", user.email),
        rol=RolEnum.usuario,  # ajusta si guardas rol en Mongo
        documento=doc.get("documento"),
        programa=doc.get("programa"),
        estado=doc.get("estado", "Activo"),
    )


# ─────────────────────────────────────────
#  /api/usuarios/{user_id}/calificaciones
# ─────────────────────────────────────────
@router.get(
    "/usuarios/{user_id}/calificaciones",
    response_model=CalificacionesResponse,
)
def get_calificaciones(
    user_id: str,
    user: User = Depends(get_current_user),
):
    col = get_calificaciones_collection()
    docs = list(col.find({"user_id": user_id}))

    calificaciones = [
        Calificacion(
            curso=doc.get("curso", "Curso"),
            nota=float(doc.get("nota", 0.0)),
        )
        for doc in docs
    ]

    return CalificacionesResponse(
        usuario=user_id,
        calificaciones=calificaciones,
    )


# ─────────────────────────────────────────
#  /api/usuarios/{user_id}/estado
# ─────────────────────────────────────────
@router.get(
    "/usuarios/{user_id}/estado",
    response_model=EstadoUsuarioResponse,
)
def get_estado_por_usuario(
    user_id: str,
    user: User = Depends(get_current_user),
):
    col = get_users_chat_collection()
    doc = col.find_one({"_id": user_id}) or col.find_one({"id": user_id})

    estado = (doc or {}).get("estado", "Activo")

    return EstadoUsuarioResponse(
        usuario=user_id,
        estado=estado,
    )