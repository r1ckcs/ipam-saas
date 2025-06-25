from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
import ipaddress
from enum import Enum

class UserRole(str, Enum):
    VISUALIZADOR = "VISUALIZADOR"
    OPERADOR = "OPERADOR"
    ADMIN = "ADMIN"

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    password: str
    role: Optional[UserRole] = UserRole.VISUALIZADOR

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(UserBase):
    id: int
    role: str  # Aceitar como string para evitar problemas de enum
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    user: UserResponse
    message: str

class UserRoleUpdate(BaseModel):
    role: UserRole

class IPPrefixBase(BaseModel):
    prefix: str
    description: str
    usado: bool = False  # True se marcado como usado
    is_auto_created: bool = False  # True se criado automaticamente
    
    @validator('prefix')
    def validate_prefix(cls, v):
        try:
            ipaddress.ip_network(v, strict=False)
            return v
        except ValueError:
            raise ValueError('Invalid IP prefix format')

class IPPrefixCreate(IPPrefixBase):
    pass

class IPPrefixUpdate(BaseModel):
    description: Optional[str] = None
    usado: Optional[bool] = None
    is_auto_created: Optional[bool] = None

class IPPrefixResponse(IPPrefixBase):
    id: int
    parent_id: Optional[int]
    is_ipv6: bool
    created_at: datetime
    updated_at: datetime
    user_id: Optional[int] = None  # Tornar opcional para compatibilidade
    
    class Config:
        from_attributes = True

class SummaryResponse(BaseModel):
    prefix: str
    description: str
    total_addresses: int
    used_addresses: int
    available_addresses: int
    utilization_percent: float
    children_count: int

class SubnetResponse(BaseModel):
    prefix: str
    description: str
    status: str  # "usado", "livre", "parcialmente_usado" (calculado automaticamente)
    usado: bool = False  # True se marcado manualmente como usado
    is_real: bool  # True se foi criado pelo usuário, False se é calculado
    id: Optional[int] = None  # ID se for real
    parent_id: Optional[int] = None
    children: List['SubnetResponse'] = []
    total_addresses: int
    used_addresses: int
    available_addresses: int
    utilization_percent: float

class DivideRequest(BaseModel):
    target_mask: Optional[int] = None  # Máscara específica ou None para usar máxima
    count: Optional[int] = None  # Número de sub-redes ou None para usar máximo

class DivideResponse(BaseModel):
    subnets: List[IPPrefixResponse]
    message: str

SubnetResponse.model_rebuild()