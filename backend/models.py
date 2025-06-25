from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import hashlib
import enum

Base = declarative_base()

class UserRole(enum.Enum):
    VISUALIZADOR = "visualizador"
    OPERADOR = "operador"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.VISUALIZADOR)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relacionamento com prefixos
    prefixes = relationship("IPPrefix", back_populates="owner")
    
    def set_password(self, password: str):
        """Define a senha do usuário com hash"""
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password: str) -> bool:
        """Verifica se a senha está correta"""
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()
    
    def has_permission(self, required_role: 'UserRole') -> bool:
        """Verifica se o usuário tem a permissão necessária"""
        role_hierarchy = {
            UserRole.VISUALIZADOR: 1,
            UserRole.OPERADOR: 2,
            UserRole.ADMIN: 3
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)
    
    def can_create_prefixes(self) -> bool:
        """Verifica se pode criar prefixos"""
        return self.has_permission(UserRole.OPERADOR)
    
    def can_manage_users(self) -> bool:
        """Verifica se pode gerenciar usuários"""
        return self.has_permission(UserRole.ADMIN)
    
    def __repr__(self):
        return f"<User(id={self.id}, nome='{self.nome}', email='{self.email}')>"

class IPPrefix(Base):
    __tablename__ = "ip_prefixes"
    
    id = Column(Integer, primary_key=True, index=True)
    prefix = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=False)
    usado = Column(Boolean, default=False, nullable=False)  # True se marcado como usado
    is_auto_created = Column(Boolean, default=False, nullable=False)  # True se criado automaticamente como intermediário
    parent_id = Column(Integer, ForeignKey("ip_prefixes.id"), nullable=True)
    is_ipv6 = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relacionamentos
    parent = relationship("IPPrefix", remote_side=[id], backref="children")
    owner = relationship("User", back_populates="prefixes")
    
    def __repr__(self):
        return f"<IPPrefix(id={self.id}, prefix='{self.prefix}', description='{self.description}')>"