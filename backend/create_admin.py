#!/usr/bin/env python3
"""
Script para criar usuário admin padrão
Uso: python create_admin.py
"""

from database import get_db, init_db
from models import User, UserRole
from sqlalchemy.orm import Session

def create_default_admin():
    """Cria o usuário admin padrão se não existir"""
    init_db()
    
    # Obter sessão do banco
    db = next(get_db())
    
    try:
        # Verificar se já existe um admin
        existing_admin = db.query(User).filter(User.email == "admin@admin.com").first()
        
        if existing_admin:
            print("❌ Usuário admin@admin.com já existe!")
            print(f"   Nome: {existing_admin.nome}")
            print(f"   Role: {existing_admin.role.value}")
            print(f"   Ativo: {existing_admin.is_active}")
            return False
        
        # Criar usuário admin
        admin_user = User(
            nome="Administrador",
            email="admin@admin.com",
            role=UserRole.ADMIN,
            is_active=True
        )
        admin_user.set_password("Ipam")
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ Usuário admin criado com sucesso!")
        print(f"   ID: {admin_user.id}")
        print(f"   Nome: {admin_user.nome}")
        print(f"   Email: {admin_user.email}")
        print(f"   Role: {admin_user.role.value}")
        print(f"   Criado em: {admin_user.created_at}")
        print("\n🔑 Credenciais de acesso:")
        print("   Email: admin@admin.com")
        print("   Senha: Ipam")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar usuário admin: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Criando usuário administrador padrão...")
    print("=" * 50)
    create_default_admin()
    print("=" * 50)