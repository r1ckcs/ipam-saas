# IPAM - IP Address Management

SaaS para gerenciamento de prefixos IP com suporte a IPv4 e IPv6.

## Arquitetura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Frontend     │    │     Backend     │    │    Database     │
│   (JavaScript)  │───►│    (Python)     │───►│  (PostgreSQL)   │
│     Nginx       │    │    FastAPI      │    │                 │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Funcionalidades

- ✅ Cadastro, edição e exclusão de prefixos IP (IPv4 e IPv6)
- ✅ Aninhamento automático de prefixos filhos
- ✅ Indicação visual de prefixos usados e livres
- ✅ Exibição de quantidade de endereços disponíveis e utilizados
- ✅ Sumarização de prefixos com estatísticas de utilização
- ✅ Interface hierárquica em árvore
- ✅ Resumo de utilização em tabela

## Modelo de Dados

```json
{
  "IPPrefix": {
    "id": "integer (primary key)",
    "prefix": "string (ex: 192.168.1.0/24)",
    "description": "string",
    "parent_id": "integer (foreign key, nullable)",
    "is_ipv6": "boolean",
    "created_at": "datetime",
    "updated_at": "datetime"
  }
}
```

## API Endpoints

- `POST /prefixes` - Criar prefixo
- `GET /prefixes` - Listar todos os prefixos
- `GET /prefixes/{id}` - Obter prefixo específico
- `PUT /prefixes/{id}` - Atualizar prefixo
- `DELETE /prefixes/{id}` - Excluir prefixo
- `GET /prefixes/{id}/children` - Obter filhos de um prefixo
- `GET /summary` - Obter resumo de utilização

## Execução

```bash
# Subir todos os serviços
docker-compose up -d

# Verificar logs
docker-compose logs -f

# Parar serviços
docker-compose down
```

## Acesso

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Documentação API: http://localhost:8000/docs

## Stack Técnica

- **Backend**: Python 3.11 + FastAPI + SQLAlchemy + PostgreSQL
- **Frontend**: JavaScript puro + HTML5 + CSS3
- **Database**: PostgreSQL 15
- **Deployment**: Docker + Docker Compose
- **Web Server**: Nginx (frontend) + Uvicorn (backend)

## Decisões Técnicas

### Por que FastAPI?
- Alta performance e tipagem automática
- Documentação automática com Swagger
- Suporte nativo a async/await
- Validação automática com Pydantic

### Por que JavaScript puro?
- Simplicidade e leveza
- Sem dependências externas
- Controle total sobre o DOM
- Fácil manutenção

### Por que PostgreSQL?
- Suporte robusto a tipos de dados complexos
- Excelente performance para consultas hierárquicas
- Suporte nativo a índices e constraints

### Aninhamento Automático
- Algoritmo busca o prefixo pai mais específico
- Comparação usando biblioteca `ipaddress` do Python
- Validação automática de sobreposição de redes

### Sumarização
- Cálculo dinâmico de utilização
- Agregação de estatísticas por prefixo
- Visualização com barras de progresso

## Limitações

- Não implementa autenticação/autorização
- Não tem sistema de billing
- Sem backup automático
- Sem monitoramento avançado
- Interface básica sem frameworks CSS
- Sem cache de consultas
- Sem paginação para grandes volumes

## Riscos

- **Concorrência**: Possível inconsistência em inserções simultâneas
- **Escalabilidade**: Query hierárquica pode ser lenta com muitos prefixos
- **Validação**: Sobreposição de prefixos não é completamente verificada
- **Segurança**: CORS habilitado para todas as origens