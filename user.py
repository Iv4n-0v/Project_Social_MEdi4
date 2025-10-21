from fastapi import APIRouter, HTTPException
from db import SessionDep
from models import User, UserBase, UserAudit

router = APIRouter()

@router.post("/", response_model=User)
def create_user(new_user: UserBase, session: SessionDep):
    user = User.model_validate(new_user)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

#  Obtener todos los usuarios activos

@router.get("/", response_model=list[User])
def get_active_users(session: SessionDep):
    return session.query(User).filter(User.is_active==True).all()

# 🔹 Obtener todos los usuarios (incluidos eliminados)
@router.get("/all", response_model=list[User])
def get_all_users(session: SessionDep):
    return session.query(User).all()

# 🔹 Obtener un usuario por ID
@router.get("/{user_id}", response_model=User)
def get_user(user_id: int, session: SessionDep):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# 🔹 Actualizar usuario
@router.put("/{user_id}", response_model=User)
def update_user(user_id: int, updated_user: UserBase, session: SessionDep):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.name = updated_user.name
    user.type = updated_user.type
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

# 🔹 Eliminar usuario (Soft Delete)
@router.delete("/{user_id}")
def delete_user(user_id: int, session: SessionDep):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Marcamos como inactivo
    user.is_active = False
    session.add(user)

    # Registramos la acción en la tabla UserAudit
    audit = UserAudit(user_id=user_id, action="DELETE")
    session.add(audit)

    session.commit()
    return {"message": "User marked as deleted"}

# 🔹 Restaurar usuario eliminado
@router.patch("/{user_id}/restore")
def restore_user(user_id: int, session: SessionDep):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = True
    session.add(user)

    audit = UserAudit(user_id=user_id, action="RESTORE")
    session.add(audit)

    session.commit()
    return {"message": "User restored successfully"}

# 🔹 Obtener logs de auditoría de usuarios
@router.get("/audit/logs", response_model=list[UserAudit])
def get_audit_logs(session: SessionDep):
    return session.query(UserAudit).all()

