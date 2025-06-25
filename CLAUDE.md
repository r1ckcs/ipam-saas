Crie um SaaS para gerenciamento de prefixos IP com os requisitos abaixo. Não invente funcionalidades além do pedido. Atue como um arquiteto de software experiente, proponha uma arquitetura clara, módulos, fluxos e exemplos de entidades. Use Python para o backend, JavaScript para o frontend, e Docker como pilar do deployment (tudo em containers). Não utilize frameworks ou bibliotecas proprietárias.

Requisitos funcionais:

Cadastro, edição e exclusão de prefixos IP (IPv4 e IPv6).

Cada prefixo deve ter uma descrição associada.

Aninhamento automático de prefixos filhos (ao cadastrar um novo prefixo, identificar o pai automaticamente).

Indicação visual de prefixos usados e livres.

Exibir quantidade de endereços disponíveis e utilizados em cada prefixo.

Mostrar sumarização de prefixos usados (agregação, não listagem simples), exibindo range mínimo de sub-redes ativas.

Restrições técnicas:

Frontend em JavaScript, backend em Python.

Tudo deve ser orquestrado via Docker, cada componente isolado em container.

Modelagem clara de dados (desenhe ou explique o modelo).

Não implemente autenticação, não implemente billing.

Foco em lógica de prefixos, sumarização e UI objetiva.

Entregue:

Esquema de arquitetura do SaaS (diagrama ou descrição detalhada).

Fluxo de uso (user flow).

Modelagem de dados (exemplo em formato JSON ou ORM).

Exemplos de API endpoints essenciais.

Justificativa das decisões técnicas (por que esse stack? Por que esse modelo?).

Pontos críticos para automação de aninhamento e sumarização de prefixos.

Como o frontend deve exibir essas informações (wireframe textual ou descrição precisa).

Não forneça texto motivacional. Seja direto, técnico e crítico. Liste riscos ou limitações da solução proposta.

altere a tag de versão sempre que fizer alguma alteração
