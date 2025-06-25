from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import ipaddress
from database import get_db, init_db
from models import IPPrefix, User, UserRole
from schemas import IPPrefixCreate, IPPrefixResponse, IPPrefixUpdate, SummaryResponse, SubnetResponse, DivideRequest, DivideResponse, UserCreate, UserLogin, UserResponse, AuthResponse, UserRoleUpdate, UserUpdate

app = FastAPI(title="IPAM - IP Address Management", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    init_db()

@app.get("/")
async def root():
    return {"message": "IPAM API is running"}

@app.post("/auth/register", response_model=AuthResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Cadastrar novo usuário"""
    # Verificar se email já existe
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Criar novo usuário
    user = User(nome=user_data.nome, email=user_data.email, role=user_data.role)
    user.set_password(user_data.password)
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return AuthResponse(
        user=UserResponse.from_orm(user),
        message="User registered successfully"
    )

@app.post("/auth/login", response_model=AuthResponse)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Login de usuário"""
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not user.verify_password(login_data.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="User account is disabled")
    
    return AuthResponse(
        user=UserResponse.from_orm(user),
        message="Login successful"
    )

def get_current_user(user_email: str = Header(..., alias="X-User-Email"), db: Session = Depends(get_db)) -> User:
    """Middleware para obter usuário atual baseado no header"""
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="User account is disabled")
    return user

def require_role(required_roles: List[UserRole]):
    """Decorator para verificar se o usuário tem a role necessária"""
    def decorator(current_user: User = Depends(get_current_user)):
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=403, 
                detail=f"Insufficient permissions. Required roles: {[role.value for role in required_roles]}"
            )
        return current_user
    return decorator

def require_operador_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """Middleware que requer role OPERADOR ou ADMIN"""
    if current_user.role not in [UserRole.OPERADOR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=403, 
            detail="Insufficient permissions. Required role: OPERADOR or ADMIN"
        )
    return current_user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Middleware que requer role ADMIN"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403, 
            detail="Insufficient permissions. Required role: ADMIN"
        )
    return current_user

@app.get("/auth/users", response_model=List[UserResponse])
async def get_users(current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Listar todos os usuários (apenas ADMIN)"""
    users = db.query(User).all()
    return users

@app.get("/auth/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Obter um usuário específico (apenas ADMIN)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/auth/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_data: UserUpdate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Atualizar usuário (apenas ADMIN)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verificar se email já existe (se estiver sendo alterado)
    if user_data.email and user_data.email != user.email:
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already exists")
        user.email = user_data.email
    
    if user_data.nome:
        user.nome = user_data.nome
    
    if user_data.password:
        user.set_password(user_data.password)
    
    if user_data.role:
        user.role = user_data.role
    
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    db.commit()
    db.refresh(user)
    
    return user

@app.delete("/auth/users/{user_id}")
async def delete_user(user_id: int, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Deletar usuário (apenas ADMIN)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Não permitir que admin delete a si mesmo
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted successfully"}

@app.put("/auth/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(user_id: int, role_data: UserRoleUpdate, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Atualizar role de um usuário (apenas ADMIN)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role = role_data.role
    db.commit()
    db.refresh(user)
    
    return user

@app.put("/auth/users/{user_id}/status")
async def toggle_user_status(user_id: int, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Ativar/desativar usuário (apenas ADMIN)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Não permitir que admin desative a si mesmo
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    
    return {"message": f"User {'activated' if user.is_active else 'deactivated'} successfully", "is_active": user.is_active}

@app.post("/prefixes", response_model=IPPrefixResponse)
async def create_prefix(prefix_data: IPPrefixCreate, current_user: User = Depends(require_operador_or_admin), db: Session = Depends(get_db)):
    try:
        network = ipaddress.ip_network(prefix_data.prefix, strict=False)
        
        # Verificar se já existe
        existing = db.query(IPPrefix).filter(IPPrefix.prefix == str(network)).first()
        if existing:
            raise HTTPException(status_code=400, detail="Prefix already exists")
        
        # Encontrar prefixo pai automaticamente
        parent_id = find_parent_prefix(db, network)
        
        prefix = IPPrefix(
            prefix=str(network),
            description=prefix_data.description,
            usado=prefix_data.usado,
            is_auto_created=prefix_data.is_auto_created,
            parent_id=parent_id,
            is_ipv6=network.version == 6,
            user_id=current_user.id
        )
        
        db.add(prefix)
        db.commit()
        db.refresh(prefix)
        
        return prefix
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid IP prefix: {str(e)}")

@app.post("/prefixes/with-hierarchy", response_model=IPPrefixResponse)
async def create_prefix_with_hierarchy(prefix_data: IPPrefixCreate, current_user: User = Depends(require_operador_or_admin), db: Session = Depends(get_db)):
    """Cria um prefixo criando automaticamente toda a hierarquia intermediária necessária"""
    try:
        network = ipaddress.ip_network(prefix_data.prefix, strict=False)
        
        # Verificar se já existe
        existing = db.query(IPPrefix).filter(IPPrefix.prefix == str(network)).first()
        if existing:
            # Se o prefixo existente foi criado automaticamente e tem descrição genérica,
            # permitir que o usuário o "promova" com uma descrição personalizada
            if existing.description and "Auto-created intermediate" in existing.description:
                existing.description = prefix_data.description
                existing.usado = prefix_data.usado
                existing.is_auto_created = prefix_data.is_auto_created
                db.commit()
                db.refresh(existing)
            return existing
        
        # Criar toda a hierarquia intermediária
        target_id = create_intermediate_prefixes(db, network, prefix_data.description, prefix_data.usado, current_user.id)
        
        db.commit()
        
        # Retornar o prefixo criado
        created_prefix = db.query(IPPrefix).filter(IPPrefix.id == target_id).first()
        return created_prefix
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid IP prefix: {str(e)}")

@app.get("/prefixes", response_model=List[IPPrefixResponse])
async def get_prefixes(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    prefixes = db.query(IPPrefix).all()
    return prefixes

@app.get("/prefixes/{prefix_id}", response_model=IPPrefixResponse)
async def get_prefix(prefix_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    prefix = db.query(IPPrefix).filter(IPPrefix.id == prefix_id).first()
    if not prefix:
        raise HTTPException(status_code=404, detail="Prefix not found")
    return prefix

@app.put("/prefixes/{prefix_id}", response_model=IPPrefixResponse)
async def update_prefix(prefix_id: int, prefix_data: IPPrefixUpdate, current_user: User = Depends(require_operador_or_admin), db: Session = Depends(get_db)):
    prefix = db.query(IPPrefix).filter(IPPrefix.id == prefix_id).first()
    if not prefix:
        raise HTTPException(status_code=404, detail="Prefix not found")
    
    if prefix_data.description is not None:
        prefix.description = prefix_data.description
    
    if prefix_data.usado is not None:
        prefix.usado = prefix_data.usado
    
    if prefix_data.is_auto_created is not None:
        prefix.is_auto_created = prefix_data.is_auto_created
    
    db.commit()
    db.refresh(prefix)
    return prefix

@app.delete("/prefixes/{prefix_id}")
async def delete_prefix(prefix_id: int, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    prefix = db.query(IPPrefix).filter(IPPrefix.id == prefix_id).first()
    if not prefix:
        raise HTTPException(status_code=404, detail="Prefix not found")
    
    db.delete(prefix)
    db.commit()
    return {"message": "Prefix deleted successfully"}

@app.get("/prefixes/{prefix_id}/children", response_model=List[IPPrefixResponse])
async def get_prefix_children(prefix_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    children = db.query(IPPrefix).filter(IPPrefix.parent_id == prefix_id).all()
    return children

@app.get("/summary", response_model=List[SummaryResponse])
async def get_summary(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    prefixes = db.query(IPPrefix).all()
    summary = calculate_prefix_summary(prefixes)
    return summary

@app.get("/hierarchy", response_model=List[SubnetResponse])
async def get_hierarchy(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retorna hierarquia completa com sub-redes calculadas"""
    prefixes = db.query(IPPrefix).all()
    hierarchy = build_subnet_hierarchy(prefixes)
    return hierarchy


@app.post("/prefixes/create-from-calculated", response_model=IPPrefixResponse)
async def create_from_calculated(prefix_data: IPPrefixCreate, current_user: User = Depends(require_operador_or_admin), db: Session = Depends(get_db)):
    """Converte um prefixo calculado em real criando-o no banco"""
    try:
        network = ipaddress.ip_network(prefix_data.prefix, strict=False)
        
        # Verificar se já existe
        existing = db.query(IPPrefix).filter(IPPrefix.prefix == str(network)).first()
        if existing:
            return existing
        
        # Encontrar prefixo pai automaticamente
        parent_id = find_parent_prefix(db, network)
        
        prefix = IPPrefix(
            prefix=str(network),
            description=prefix_data.description,
            usado=prefix_data.usado,
            is_auto_created=prefix_data.is_auto_created,
            parent_id=parent_id,
            is_ipv6=network.version == 6,
            user_id=current_user.id
        )
        
        db.add(prefix)
        db.commit()
        db.refresh(prefix)
        
        return prefix
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid IP prefix: {str(e)}")



def find_parent_prefix(db: Session, network: ipaddress.IPv4Network | ipaddress.IPv6Network) -> Optional[int]:
    """Encontra o prefixo pai mais específico para o novo prefixo"""
    prefixes = db.query(IPPrefix).filter(
        IPPrefix.is_ipv6 == (network.version == 6)
    ).all()
    
    best_parent = None
    best_prefix_len = -1
    
    for prefix in prefixes:
        try:
            prefix_network = ipaddress.ip_network(prefix.prefix)
            if network.subnet_of(prefix_network) and prefix_network.prefixlen > best_prefix_len:
                best_parent = prefix.id
                best_prefix_len = prefix_network.prefixlen
        except ValueError:
            continue
    
    return best_parent

def create_intermediate_prefixes(db: Session, target_network: ipaddress.IPv4Network | ipaddress.IPv6Network, 
                               target_description: str, target_usado: bool = False, user_id: int = None) -> int:
    """Cria automaticamente apenas a hierarquia intermediária necessária se existir relação pai/filho"""
    
    # Verificar se já existe algum prefixo relacionado (pai ou filho)
    has_related_prefix = False
    
    # Buscar por prefixos pais existentes
    parent_prefix = None
    parent_network = None
    
    for prefix_len in range(target_network.prefixlen - 1, 7, -1):  # Não ir além de /8 para IPv4
        candidate_network = target_network.supernet(new_prefix=prefix_len)
        existing = db.query(IPPrefix).filter(
            IPPrefix.prefix == str(candidate_network),
            IPPrefix.is_ipv6 == (target_network.version == 6)
        ).first()
        
        if existing:
            parent_prefix = existing
            parent_network = candidate_network
            has_related_prefix = True
            break
    
    # Buscar por prefixos filhos existentes
    if not has_related_prefix:
        children = db.query(IPPrefix).filter(
            IPPrefix.is_ipv6 == (target_network.version == 6)
        ).all()
        
        for child in children:
            try:
                child_network = ipaddress.ip_network(child.prefix)
                # Verificar se o child está contido no target (target seria pai do child)
                if child_network.subnet_of(target_network):
                    has_related_prefix = True
                    break
            except ValueError:
                continue
    
    # Se não há prefixos relacionados, criar apenas o prefixo solicitado sem hierarquia
    if not has_related_prefix:
        # Usar o find_parent_prefix normal que só conecta a pais existentes
        parent_id = find_parent_prefix(db, target_network)
        
        target_prefix = IPPrefix(
            prefix=str(target_network),
            description=target_description,
            usado=target_usado,
            is_auto_created=False,  # Este é o prefixo alvo, não é auto-criado
            parent_id=parent_id,
            is_ipv6=target_network.version == 6,
            user_id=user_id
        )
        db.add(target_prefix)
        db.flush()
        return target_prefix.id
    
    # Se há um pai existente, criar apenas os níveis intermediários necessários
    if parent_prefix:
        current_parent = parent_prefix
        current_prefix_len = parent_network.prefixlen
        
        # Criar cada nível intermediário um por um
        for next_len in range(current_prefix_len + 1, target_network.prefixlen):
            # Calcular a rede intermediária corretamente
            inter_network = ipaddress.ip_network(f"{target_network.network_address}/{next_len}", strict=False)
            
            # Verificar se já existe
            existing = db.query(IPPrefix).filter(
                IPPrefix.prefix == str(inter_network),
                IPPrefix.is_ipv6 == (inter_network.version == 6)
            ).first()
            
            if existing:
                current_parent = existing
            else:
                # Criar prefixo intermediário
                inter_prefix = IPPrefix(
                    prefix=str(inter_network),
                    description=f"Auto-created intermediate for {target_network}",
                    usado=False,
                    is_auto_created=True,  # Este é um prefixo intermediário auto-criado
                    parent_id=current_parent.id,
                    is_ipv6=inter_network.version == 6,
                    user_id=user_id
                )
                db.add(inter_prefix)
                db.flush()
                current_parent = inter_prefix
        
        parent_id = current_parent.id
    else:
        # Se há filhos mas não pai, usar find_parent_prefix normal
        parent_id = find_parent_prefix(db, target_network)
    
    # Finalmente criar o prefixo alvo
    target_prefix = IPPrefix(
        prefix=str(target_network),
        description=target_description,
        usado=target_usado,
        is_auto_created=False,  # Este é o prefixo alvo, não é auto-criado
        parent_id=parent_id,
        is_ipv6=target_network.version == 6,
        user_id=user_id
    )
    db.add(target_prefix)
    db.flush()
    
    return target_prefix.id

def calculate_prefix_summary(prefixes: List[IPPrefix]) -> List[SummaryResponse]:
    """Calcula sumarização de prefixos usados"""
    summary = []
    
    for prefix in prefixes:
        try:
            network = ipaddress.ip_network(prefix.prefix)
            children = [p for p in prefixes if p.parent_id == prefix.id]
            
            total_addresses = int(network.num_addresses)
            used_addresses = 0
            
            for child in children:
                child_network = ipaddress.ip_network(child.prefix)
                used_addresses += int(child_network.num_addresses)
            
            available_addresses = total_addresses - used_addresses
            
            summary.append(SummaryResponse(
                prefix=prefix.prefix,
                description=prefix.description,
                total_addresses=total_addresses,
                used_addresses=used_addresses,
                available_addresses=available_addresses,
                utilization_percent=round((used_addresses / total_addresses) * 100, 2) if total_addresses > 0 else 0,
                children_count=len(children)
            ))
        except ValueError:
            continue
    
    return summary

def build_subnet_hierarchy(prefixes: List[IPPrefix]) -> List[SubnetResponse]:
    """Constrói hierarquia completa com sub-redes automáticas"""
    # Mapear prefixos reais por string
    real_prefixes = {p.prefix: p for p in prefixes}
    
    # Construir árvore apenas com prefixos root (sem pai) e ordená-los
    root_prefixes = [p for p in prefixes if p.parent_id is None]
    root_prefixes.sort(key=lambda p: ipaddress.ip_network(p.prefix).network_address)
    
    hierarchy = []
    for root in root_prefixes:
        subnet_tree = build_subnet_tree(root, real_prefixes, prefixes)
        hierarchy.append(subnet_tree)
    
    return hierarchy

def calculate_status_from_children(prefix: IPPrefix, children: List[SubnetResponse]) -> str:
    """Calcula o status baseado nos filhos (incluindo sub-redes calculadas)"""
    # Se está marcado como usado, retorna "usado"
    if prefix.usado:
        return "usado"
    
    # Se não tem filhos, está livre
    if not children:
        return "livre"
    
    # Verificar status de todos os filhos
    children_status = [child.status for child in children]
    
    # Se TODOS os filhos estão usados, pai fica usado
    if all(status == "usado" for status in children_status):
        return "usado"
    
    # Se algum filho está usado ou parcialmente usado, pai fica parcialmente usado
    if any(status in ["usado", "parcialmente_usado"] for status in children_status):
        return "parcialmente_usado"
    
    return "livre"

def calculate_status(prefix: IPPrefix, all_prefixes: List[IPPrefix]) -> str:
    """Calcula o status automaticamente baseado na marcação 'usado' e filhos"""
    # Se está marcado como usado, retorna "usado"
    if prefix.usado:
        return "usado"
    
    # Verificar todos os filhos (incluindo auto-criados)
    children = [p for p in all_prefixes if p.parent_id == prefix.id]
    
    # Se não tem filhos, está livre
    if not children:
        return "livre"
    
    # Verificar status de todos os filhos
    children_status = []
    user_created_children_status = []
    
    for child in children:
        child_status = calculate_status(child, all_prefixes)
        children_status.append(child_status)
        
        # Se é um filho criado pelo usuário, adicionar à lista especial
        if not child.is_auto_created:
            user_created_children_status.append(child_status)
    
    # Usar todos os filhos (incluindo calculados) para determinar o status final
    # Se TODOS os filhos estão usados, pai fica usado
    if all(status == "usado" for status in children_status):
        return "usado"
    
    # Se algum filho está usado ou parcialmente usado, pai fica parcialmente usado
    if any(status in ["usado", "parcialmente_usado"] for status in children_status):
        return "parcialmente_usado"
    
    return "livre"

def build_subnet_tree(prefix: IPPrefix, real_prefixes: dict, all_prefixes: List[IPPrefix]) -> SubnetResponse:
    """Constrói árvore de sub-redes para um prefixo"""
    try:
        network = ipaddress.ip_network(prefix.prefix)
        
        # Calcular estatísticas
        total_addresses = int(network.num_addresses)
        used_addresses = calculate_used_addresses(prefix, all_prefixes)
        available_addresses = total_addresses - used_addresses
        utilization_percent = round((used_addresses / total_addresses) * 100, 2) if total_addresses > 0 else 0
        
        # Calcular status automaticamente após gerar filhos
        # Será calculado depois de gerar os filhos para considerar sub-redes calculadas
        
        # Gerar sub-redes automáticas primeiro
        children = generate_automatic_subnets(network, prefix, real_prefixes, all_prefixes)
        
        # Calcular status baseado nos filhos (incluindo calculados)
        status = calculate_status_from_children(prefix, children)
        
        subnet = SubnetResponse(
            prefix=prefix.prefix,
            description=prefix.description,
            status=status,
            usado=prefix.usado,
            is_real=True,
            id=prefix.id,
            parent_id=prefix.parent_id,
            total_addresses=total_addresses,
            used_addresses=used_addresses,
            available_addresses=available_addresses,
            utilization_percent=utilization_percent,
            children=children
        )
        
        return subnet
        
    except ValueError:
        return SubnetResponse(
            prefix=prefix.prefix,
            description=prefix.description,
            status="erro",
            usado=prefix.usado,
            is_real=True,
            id=prefix.id,
            parent_id=prefix.parent_id,
            total_addresses=0,
            used_addresses=0,
            available_addresses=0,
            utilization_percent=0,
            children=[]
        )

def generate_automatic_subnets(parent_network: ipaddress.IPv4Network | ipaddress.IPv6Network, 
                             parent_prefix: IPPrefix, 
                             real_prefixes: dict, 
                             all_prefixes: List[IPPrefix]) -> List[SubnetResponse]:
    """Gera sub-redes automáticas apenas se existir relacionamento pai/filho"""
    children = []
    
    # Buscar filhos reais e ordená-los numericamente
    real_children = [p for p in all_prefixes if p.parent_id == parent_prefix.id]
    real_children.sort(key=lambda p: ipaddress.ip_network(p.prefix).network_address)
    
    # Verificar se há prefixos filhos relacionados (diretos ou indiretos)
    has_related_children = False
    
    # Verificar filhos diretos
    if real_children:
        has_related_children = True
    else:
        # Verificar se há prefixos que estariam contidos neste parent
        for prefix in all_prefixes:
            if prefix.id != parent_prefix.id:
                try:
                    prefix_network = ipaddress.ip_network(prefix.prefix)
                    # Se o prefix está contido no parent (seria filho)
                    if prefix_network.subnet_of(parent_network):
                        has_related_children = True
                        break
                except ValueError:
                    continue
    
    # Só gerar subredes calculadas se houver relacionamento
    if not has_related_children:
        return children
    
    # Sequência de prefixos decrescente: /32,/31,/30,/29,/28,/27,/26,/25,/24,/23,/22,/21,/20,/19,/18,/17,/16,/15,/14,/13,/12,/11,/10,/9,/8,/7,/6,/5,/4,/3,/2,/1,/0
    prefix_sequence = list(range(32, -1, -1)) if parent_network.version == 4 else list(range(128, -1, -1))
    
    # Encontrar o próximo prefixo na sequência com maior máscara possível
    # Para máxima granularidade, sempre usar incremento de 1 bit
    current_prefix = parent_network.prefixlen
    target_prefix = current_prefix + 1
    
    # Verificar se o target_prefix está na sequência válida
    max_prefix = 32 if parent_network.version == 4 else 128
    if target_prefix > max_prefix:
        target_prefix = None
    
    # Primeiro, adicionar TODOS os filhos reais
    for real_child in real_children:
        child_tree = build_subnet_tree(real_child, real_prefixes, all_prefixes)
        children.append(child_tree)
    
    # Se encontrou um target prefix válido e pode ser dividido, adicionar sub-redes calculadas
    if target_prefix is not None:
        try:
            # Gerar todas as sub-redes do próximo tamanho na sequência
            subnets = list(parent_network.subnets(new_prefix=target_prefix))
            
            for i, subnet in enumerate(subnets):
                subnet_str = str(subnet)
                
                # Pular se já existe um prefixo real exatamente nesta sub-rede
                if any(p.prefix == subnet_str for p in real_children):
                    continue
                
                # Verificar se esta sub-rede tem prefixos reais dentro dela
                used_addresses = calculate_used_addresses_in_subnet(subnet, all_prefixes)
                total_addresses = int(subnet.num_addresses)
                available_addresses = total_addresses - used_addresses
                utilization_percent = round((used_addresses / total_addresses) * 100, 2) if total_addresses > 0 else 0
                
                # Determinar status
                if used_addresses == 0:
                    status = "livre"
                elif used_addresses == total_addresses:
                    status = "usado"
                else:
                    status = "parcialmente_usado"
                
                child_subnet = SubnetResponse(
                    prefix=subnet_str,
                    description=f"Sub-rede {i+1} de {parent_network}",
                    status=status,
                    usado=False,  # Sub-redes calculadas não são marcadas como usadas
                    is_real=False,  # Sub-rede calculada
                    id=None,
                    parent_id=parent_prefix.id,
                    total_addresses=total_addresses,
                    used_addresses=used_addresses,
                    available_addresses=available_addresses,
                    utilization_percent=utilization_percent,
                    children=[]
                )
                
                # Recursivamente gerar sub-redes se necessário
                if status == "parcialmente_usado" and subnet.prefixlen < max_prefix:
                    child_subnet.children = generate_automatic_subnets_calculated(subnet, parent_prefix.id, all_prefixes)
                
                children.append(child_subnet)
                
        except ValueError:
            pass
    
    # Ordenar todos os children por endereço IP
    children.sort(key=lambda c: ipaddress.ip_network(c.prefix).network_address)
    
    return children

def generate_automatic_subnets_calculated(network: ipaddress.IPv4Network | ipaddress.IPv6Network,
                                        parent_id: int,
                                        all_prefixes: List[IPPrefix]) -> List[SubnetResponse]:
    """Gera sub-redes para redes calculadas (não reais)"""
    children = []
    max_prefix = 30 if network.version == 4 else 126
    
    if network.prefixlen < max_prefix:
        try:
            subnets = list(network.subnets(new_prefix=network.prefixlen + 1))
            
            for i, subnet in enumerate(subnets):
                subnet_str = str(subnet)
                
                used_addresses = calculate_used_addresses_in_subnet(subnet, all_prefixes)
                total_addresses = int(subnet.num_addresses)
                available_addresses = total_addresses - used_addresses
                utilization_percent = round((used_addresses / total_addresses) * 100, 2) if total_addresses > 0 else 0
                
                if used_addresses == 0:
                    status = "livre"
                elif used_addresses == total_addresses:
                    status = "usado"
                else:
                    status = "parcialmente_usado"
                
                child_subnet = SubnetResponse(
                    prefix=subnet_str,
                    description=f"Sub-rede {i+1} de {network}",
                    status=status,
                    usado=False,  # Sub-redes calculadas não são marcadas como usadas
                    is_real=False,
                    id=None,
                    parent_id=parent_id,
                    total_addresses=total_addresses,
                    used_addresses=used_addresses,
                    available_addresses=available_addresses,
                    utilization_percent=utilization_percent,
                    children=[]
                )
                
                if status == "parcialmente_usado" and subnet.prefixlen < max_prefix:
                    child_subnet.children = generate_automatic_subnets_calculated(subnet, parent_id, all_prefixes)
                
                children.append(child_subnet)
                
        except ValueError:
            pass
    
    # Ordenar todos os children por endereço IP
    children.sort(key=lambda c: ipaddress.ip_network(c.prefix).network_address)
    
    return children

def calculate_used_addresses(prefix: IPPrefix, all_prefixes: List[IPPrefix]) -> int:
    """Calcula endereços usados pelos filhos diretos considerando uso recursivo"""
    used = 0
    
    # Buscar apenas filhos diretos
    direct_children = [p for p in all_prefixes if p.parent_id == prefix.id]
    
    for child in direct_children:
        try:
            child_network = ipaddress.ip_network(child.prefix)
            child_total = int(child_network.num_addresses)
            
            if child.usado:
                # Se o filho está marcado como usado, conta todos os seus endereços
                used += child_total
            else:
                # Se não está marcado como usado, conta apenas o que ele tem de usado recursivamente
                child_used = calculate_used_addresses(child, all_prefixes)
                used += child_used
        except ValueError:
            continue
    
    return used

def calculate_used_addresses_in_subnet(subnet: ipaddress.IPv4Network | ipaddress.IPv6Network, 
                                     all_prefixes: List[IPPrefix]) -> int:
    """Calcula endereços usados dentro de uma sub-rede calculada pelos filhos diretos marcados como 'usado'"""
    used = 0
    
    # Buscar apenas prefixos que são filhos diretos desta sub-rede
    for prefix in all_prefixes:
        try:
            if prefix.usado:
                prefix_network = ipaddress.ip_network(prefix.prefix)
                # Verificar se é filho direto (está contido e não há intermediários)
                if prefix_network.subnet_of(subnet):
                    # Verificar se não há prefixos intermediários
                    is_direct_child = True
                    for other in all_prefixes:
                        if other.id != prefix.id:
                            try:
                                other_network = ipaddress.ip_network(other.prefix)
                                # Se há um prefixo entre a subnet e este prefix
                                if (prefix_network.subnet_of(other_network) and 
                                    other_network.subnet_of(subnet) and 
                                    other_network != subnet):
                                    is_direct_child = False
                                    break
                            except ValueError:
                                continue
                    
                    if is_direct_child:
                        used += int(prefix_network.num_addresses)
        except ValueError:
            continue
    
    return used

@app.post("/prefixes/{prefix_id}/divide", response_model=DivideResponse)
async def divide_prefix(prefix_id: int, request: DivideRequest, current_user: User = Depends(require_operador_or_admin), db: Session = Depends(get_db)):
    """Divide um prefixo em sub-redes com a maior máscara possível"""
    prefix = db.query(IPPrefix).filter(IPPrefix.id == prefix_id).first()
    if not prefix:
        raise HTTPException(status_code=404, detail="Prefix not found")
    
    try:
        network = ipaddress.ip_network(prefix.prefix)
        current_mask = network.prefixlen
        max_mask = 32 if network.version == 4 else 128
        
        # Determinar a máscara alvo
        if request.target_mask is not None:
            target_mask = request.target_mask
            if target_mask <= current_mask or target_mask > max_mask:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Target mask must be between {current_mask + 1} and {max_mask}"
                )
        else:
            # Usar a máscara mais específica possível (incremento de 1)
            target_mask = current_mask + 1
            if target_mask > max_mask:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Cannot divide further - already at maximum mask /{max_mask}"
                )
        
        # Gerar sub-redes
        subnets = list(network.subnets(new_prefix=target_mask))
        
        # Limitar número de sub-redes se especificado
        if request.count is not None:
            if request.count <= 0 or request.count > len(subnets):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Count must be between 1 and {len(subnets)}"
                )
            subnets = subnets[:request.count]
        
        # Criar prefixos no banco
        created_prefixes = []
        for i, subnet in enumerate(subnets):
            subnet_str = str(subnet)
            
            # Verificar se já existe
            existing = db.query(IPPrefix).filter(IPPrefix.prefix == subnet_str).first()
            if existing:
                created_prefixes.append(existing)
                continue
            
            # Criar novo prefixo
            new_prefix = IPPrefix(
                prefix=subnet_str,
                description=f"Sub-rede {i+1} de {prefix.prefix}",
                usado=False,
                is_auto_created=True,
                parent_id=prefix_id,
                is_ipv6=network.version == 6
            )
            
            db.add(new_prefix)
            created_prefixes.append(new_prefix)
        
        db.commit()
        
        # Refresh all objects to get IDs
        for p in created_prefixes:
            if p.id is None:
                db.refresh(p)
        
        return DivideResponse(
            subnets=created_prefixes,
            message=f"Created {len(created_prefixes)} subnets with /{target_mask} mask"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid IP prefix: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error dividing prefix: {str(e)}")