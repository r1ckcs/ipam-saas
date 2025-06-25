class IPAMApp {
    constructor() {
        this.apiUrl = 'http://localhost:8000';
        this.prefixes = [];
        this.summary = [];
        this.allExpanded = true;
        this.init();
    }

    init() {
        this.checkAuth();
        this.setupEventListeners();
        this.setupNavigation();
        this.loadPrefixes();
    }

    checkAuth() {
        const user = localStorage.getItem('user');
        if (!user) {
            window.location.href = 'login.html';
            return;
        }
        
        try {
            const userData = JSON.parse(user);
            document.getElementById('userEmail').textContent = userData.email;
            document.getElementById('userRole').textContent = userData.role || 'visualizador';
            
            // Controlar permissões baseadas no role
            this.userRole = userData.role || 'visualizador';
            this.setupPermissions();
        } catch (e) {
            localStorage.removeItem('user');
            window.location.href = 'login.html';
        }
    }

    setupPermissions() {
        const prefixForm = document.getElementById('prefixForm');
        const menuUsuarios = document.querySelector('[data-page="usuarios"]');
        const addUserBtn = document.getElementById('addUserBtn');
        
        // Visualizador: apenas leitura
        if (this.userRole === 'VISUALIZADOR') {
            if (prefixForm) {
                prefixForm.style.display = 'none';
            }
            // Ocultar menu de usuários
            if (menuUsuarios) {
                menuUsuarios.style.display = 'none';
            }
        }
        // Operador: pode criar/editar prefixos, mas não gerenciar usuários
        else if (this.userRole === 'OPERADOR') {
            if (prefixForm) {
                prefixForm.style.display = 'grid';
            }
            // Ocultar menu de usuários
            if (menuUsuarios) {
                menuUsuarios.style.display = 'none';
            }
        }
        // Admin: acesso total
        else if (this.userRole === 'ADMIN') {
            if (prefixForm) {
                prefixForm.style.display = 'grid';
            }
            if (menuUsuarios) {
                menuUsuarios.style.display = 'flex';
            }
            if (addUserBtn) {
                addUserBtn.style.display = 'flex';
            }
        }
        
        // Atualizar interface baseada nas permissões
        this.updateUIPermissions();
    }

    updateUIPermissions() {
        // Desabilitar botões de ação para usuários sem permissão
        const actionButtons = document.querySelectorAll('.action-btn, .delete-btn');
        const editButtons = document.querySelectorAll('[onclick*="editPrefix"], [onclick*="deletePrefix"]');
        
        if (this.userRole === 'VISUALIZADOR') {
            // Desabilitar todos os botões de ação
            actionButtons.forEach(btn => {
                btn.disabled = true;
                btn.style.opacity = '0.5';
                btn.title = 'Sem permissão para esta ação';
            });
            
            editButtons.forEach(btn => {
                btn.disabled = true;
                btn.style.opacity = '0.5';
                btn.title = 'Sem permissão para editar';
            });
        }
    }

    canCreatePrefixes() {
        return this.userRole === 'OPERADOR' || this.userRole === 'ADMIN';
    }

    canManageUsers() {
        return this.userRole === 'ADMIN';
    }

    canEditPrefixes() {
        return this.userRole === 'OPERADOR' || this.userRole === 'ADMIN';
    }

    hasPermission(requiredRole) {
        const roleHierarchy = {
            'VISUALIZADOR': 1,
            'OPERADOR': 2,
            'ADMIN': 3
        };
        
        const userLevel = roleHierarchy[this.userRole] || 0;
        const requiredLevel = roleHierarchy[requiredRole] || 0;
        
        return userLevel >= requiredLevel;
    }

    setupEventListeners() {
        document.getElementById('prefixForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createPrefix();
        });

        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.loadPrefixes();
        });

        document.getElementById('summaryBtn').addEventListener('click', () => {
            this.loadSummary();
        });

        document.getElementById('expandAllBtn').addEventListener('click', () => {
            this.expandAll();
        });

        document.getElementById('collapseAllBtn').addEventListener('click', () => {
            this.collapseAll();
        });

        document.getElementById('toggleAllBtn').addEventListener('click', () => {
            this.toggleAll();
        });

        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tab = e.target.dataset.tab;
                this.switchTab(tab);
                if (tab === 'users') {
                    this.loadUsers();
                }
            });
        });

        document.querySelector('.close').addEventListener('click', () => {
            this.closeModal();
        });

        document.getElementById('logoutBtn').addEventListener('click', () => {
            this.logout();
        });

        document.getElementById('editForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.updatePrefix();
        });

        document.getElementById('deleteBtn').addEventListener('click', () => {
            this.deletePrefix();
        });


        window.addEventListener('click', (e) => {
            if (e.target === document.getElementById('modal')) {
                this.closeModal();
            }
            if (e.target === document.getElementById('userModal')) {
                this.closeUserModal();
            }
        });

        // Event listeners para gerenciamento de usuários
        document.getElementById('addUserBtn').addEventListener('click', () => {
            this.openUserModal();
        });

        document.getElementById('closeUserModal').addEventListener('click', () => {
            this.closeUserModal();
        });

        document.getElementById('userForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveUser();
        });

        document.getElementById('deleteUserBtn').addEventListener('click', () => {
            this.deleteUser();
        });
    }

    setupNavigation() {
        // Navegação do menu lateral
        document.querySelectorAll('.menu-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const page = e.currentTarget.dataset.page;
                this.navigateToPage(page);
            });
        });
    }

    navigateToPage(page) {
        // Atualizar menu ativo
        document.querySelectorAll('.menu-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-page="${page}"]`).classList.add('active');

        // Mostrar página correspondente
        document.querySelectorAll('.page').forEach(pageEl => {
            pageEl.classList.remove('active');
        });
        document.getElementById(`${page}-page`).classList.add('active');

        // Atualizar título da página
        const titles = {
            'prefixos': 'Gerenciamento de Prefixos IP',
            'usuarios': 'Gerenciamento de Usuários'
        };
        document.getElementById('pageTitle').textContent = titles[page] || 'IPAM';

        // Carregar dados específicos da página
        if (page === 'usuarios') {
            if (this.canManageUsers()) {
                this.loadUsers();
            } else {
                this.showAlert('Sem permissão para acessar gerenciamento de usuários', 'error');
                this.navigateToPage('prefixos'); // Redirecionar para prefixos
                return;
            }
        } else if (page === 'prefixos') {
            this.loadPrefixes();
        }
    }

    logout() {
        localStorage.removeItem('user');
        window.location.href = 'login.html';
    }

    getAuthHeaders() {
        const user = localStorage.getItem('user');
        if (!user) return {};
        
        try {
            const userData = JSON.parse(user);
            return {
                'X-User-Email': userData.email
            };
        } catch (e) {
            return {};
        }
    }

    async createPrefix() {
        if (!this.canCreatePrefixes()) {
            this.showAlert('Sem permissão para criar prefixos', 'error');
            return;
        }

        const prefix = document.getElementById('prefixInput').value.trim();
        const description = document.getElementById('descriptionInput').value.trim();

        if (!prefix || !description) {
            this.showAlert('Preencha todos os campos', 'error');
            return;
        }

        try {
            const response = await fetch(`${this.apiUrl}/prefixes/with-hierarchy`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...this.getAuthHeaders()
                },
                body: JSON.stringify({ prefix, description }),
            });

            if (response.ok) {
                this.showAlert('Prefixo criado com sucesso', 'success');
                document.getElementById('prefixForm').reset();
                this.loadPrefixes();
            } else {
                const error = await response.json();
                this.showAlert(error.detail || 'Erro ao criar prefixo', 'error');
            }
        } catch (error) {
            this.showAlert('Erro de conexão', 'error');
        }
    }

    async loadPrefixes() {
        try {
            const response = await fetch(`${this.apiUrl}/hierarchy`, {
                headers: this.getAuthHeaders()
            });
            if (response.ok) {
                this.hierarchy = await response.json();
                this.renderHierarchy();
            } else {
                this.showAlert('Erro ao carregar hierarquia', 'error');
            }
        } catch (error) {
            this.showAlert('Erro de conexão', 'error');
        }
    }

    async loadSummary() {
        try {
            const response = await fetch(`${this.apiUrl}/summary`, {
                headers: this.getAuthHeaders()
            });
            if (response.ok) {
                this.summary = await response.json();
                this.renderSummaryTable();
                this.switchTab('summary');
            } else {
                this.showAlert('Erro ao carregar resumo', 'error');
            }
        } catch (error) {
            this.showAlert('Erro de conexão', 'error');
        }
    }

    renderHierarchy() {
        const container = document.getElementById('prefixTree');
        container.innerHTML = this.renderHierarchyNodes(this.hierarchy, 0);
    }

    renderHierarchyNodes(nodes, level, parentId = '') {
        let html = '';
        nodes.forEach((node, index) => {
            const nodeId = `${parentId}_${index}`;
            const hasChildren = node.children && node.children.length > 0;
            
            // Definir classes CSS baseadas no status
            let statusClass = 'status-' + node.status;
            let statusIcon = this.getStatusIcon(node.status);
            let clickHandler = node.is_real ? 
                `onclick="app.editPrefixModal(${node.id})"` : 
                `onclick="app.editCalculatedPrefixModal('${node.prefix}', '${node.description}', ${node.parent_id})"`;
            let itemClass = node.is_real ? 'prefix-item real' : 'prefix-item calculated';
            
            
            // Botão de expansão/retração
            let expandBtn = '';
            if (hasChildren) {
                expandBtn = `<button class="expand-btn" onclick="event.stopPropagation(); app.toggleNode('${nodeId}')" data-expanded="true"><span class="material-icons">remove</span></button>`;
            }
            
            // Calcular indentação diretamente no estilo como fallback - FORÇA ABSOLUTA
            const indentPixels = level * 32;
            const indentStyle = `margin-left: ${indentPixels}px !important; padding-left: 0px !important;`;
            
            html += `
                <div class="${itemClass} ${statusClass} level-${level}" ${clickHandler} data-level="${level}" style="${indentStyle}">
                    <div class="prefix-info">
                        <div class="prefix-main">
                            ${expandBtn}
                            <span class="status-icon">${statusIcon}</span>
                            <span class="prefix-address">${node.prefix}</span>
                            <span class="prefix-description">${node.description}</span>
                            ${node.is_real ? '' : '<span class="calculated-label">(calculado)</span>'}
                        </div>
                        <div class="prefix-stats">
                            <span class="status-badge ${statusClass}">${node.status.replace('_', ' ')}</span>
                            <span>${this.formatNumber(node.total_addresses)} IPs</span>
                            <span>${this.formatNumber(node.used_addresses)} usados</span>
                            <span>${node.utilization_percent}%</span>
                            <div class="utilization-bar">
                                <div class="utilization-fill ${this.getUtilizationClass(node.utilization_percent)}" 
                                     style="width: ${node.utilization_percent}%"></div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            if (hasChildren) {
                html += `<div class="children-container" id="children_${nodeId}">`;
                html += this.renderHierarchyNodes(node.children, level + 1, nodeId);
                html += '</div>';
            }
        });
        return html;
    }

    getStatusIcon(status) {
        switch(status) {
            case 'livre': return '🔵';
            case 'usado': return '🔴';
            case 'parcialmente_usado': return '🟠';
            default: return '⚪';
        }
    }

    getUtilizationClass(percent) {
        if (percent > 80) return 'high';
        if (percent > 50) return 'medium';
        return 'low';
    }

    renderSummaryTable() {
        const container = document.getElementById('summaryTable');
        
        let html = `
            <table>
                <thead>
                    <tr>
                        <th>Prefixo</th>
                        <th>Descrição</th>
                        <th>Total</th>
                        <th>Usado</th>
                        <th>Disponível</th>
                        <th>Utilização</th>
                        <th>Filhos</th>
                    </tr>
                </thead>
                <tbody>
        `;

        this.summary.forEach(item => {
            const utilizationClass = item.utilization_percent > 80 ? 'high' : 
                                   item.utilization_percent > 50 ? 'medium' : '';
            
            html += `
                <tr>
                    <td><strong>${item.prefix}</strong></td>
                    <td>${item.description}</td>
                    <td>${this.formatNumber(item.total_addresses)}</td>
                    <td>${this.formatNumber(item.used_addresses)}</td>
                    <td>${this.formatNumber(item.available_addresses)}</td>
                    <td>
                        <div class="utilization-bar">
                            <div class="utilization-fill ${utilizationClass}" 
                                 style="width: ${item.utilization_percent}%"></div>
                        </div>
                        ${item.utilization_percent}%
                    </td>
                    <td>${item.children_count}</td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        container.innerHTML = html;
    }

    async editPrefixModal(prefixId) {
        try {
            const response = await fetch(`${this.apiUrl}/prefixes/${prefixId}`, {
                headers: this.getAuthHeaders()
            });
            if (response.ok) {
                const prefix = await response.json();
                document.getElementById('modalTitle').textContent = 'Editar Prefixo';
                document.getElementById('modalInfo').style.display = 'none';
                document.getElementById('editId').value = prefix.id;
                document.getElementById('editPrefix').value = prefix.prefix;
                document.getElementById('editDescription').value = prefix.description;
                document.getElementById('editUsado').checked = prefix.usado || false;
                document.getElementById('deleteBtn').style.display = 'block';
                document.getElementById('modal').style.display = 'block';
            } else {
                this.showAlert('Erro ao carregar prefixo', 'error');
            }
        } catch (error) {
            this.showAlert('Erro de conexão', 'error');
        }
    }

    closeModal() {
        document.getElementById('modal').style.display = 'none';
    }


    async updatePrefix() {
        const id = document.getElementById('editId').value;
        const prefix = document.getElementById('editPrefix').value;
        const description = document.getElementById('editDescription').value.trim();
        const usado = document.getElementById('editUsado').checked;

        if (!description) {
            this.showAlert('Descrição é obrigatória', 'error');
            return;
        }

        try {
            let response;
            
            if (!id) {
                // Criar novo prefixo (era calculado)
                response = await fetch(`${this.apiUrl}/prefixes/create-from-calculated`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...this.getAuthHeaders()
                    },
                    body: JSON.stringify({ prefix, description, usado }),
                });
                
                if (response.ok) {
                    this.showAlert('Prefixo criado com sucesso', 'success');
                } else {
                    const error = await response.json();
                    this.showAlert(error.detail || 'Erro ao criar prefixo', 'error');
                    return;
                }
            } else {
                // Atualizar prefixo existente
                response = await fetch(`${this.apiUrl}/prefixes/${id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        ...this.getAuthHeaders()
                    },
                    body: JSON.stringify({ description, usado }),
                });

                if (response.ok) {
                    this.showAlert('Prefixo atualizado com sucesso', 'success');
                } else {
                    const error = await response.json();
                    this.showAlert(error.detail || 'Erro ao atualizar prefixo', 'error');
                    return;
                }
            }
            
            this.closeModal();
            this.loadPrefixes();
        } catch (error) {
            this.showAlert('Erro de conexão', 'error');
        }
    }


    async editCalculatedPrefixModal(prefix, description, parentId) {
        // Mostrar modal de criação para prefixo calculado
        document.getElementById('modalTitle').textContent = 'Criar Prefixo';
        document.getElementById('modalInfo').style.display = 'block';
        document.getElementById('editId').value = '';
        document.getElementById('editPrefix').value = prefix;
        document.getElementById('editDescription').value = description;
        document.getElementById('editUsado').checked = false;
        document.getElementById('deleteBtn').style.display = 'none';
        document.getElementById('modal').style.display = 'block';
    }

    async deletePrefix() {
        const id = document.getElementById('editId').value;
        
        if (!confirm('Tem certeza que deseja excluir este prefixo?')) {
            return;
        }

        try {
            const response = await fetch(`${this.apiUrl}/prefixes/${id}`, {
                method: 'DELETE',
                headers: this.getAuthHeaders()
            });

            if (response.ok) {
                this.showAlert('Prefixo excluído com sucesso', 'success');
                this.closeModal();
                this.loadPrefixes();
            } else {
                const error = await response.json();
                this.showAlert(error.detail || 'Erro ao excluir prefixo', 'error');
            }
        } catch (error) {
            this.showAlert('Erro de conexão', 'error');
        }
    }

    switchTab(tabName) {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });

        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(tabName).classList.add('active');
    }

    formatNumber(num) {
        return new Intl.NumberFormat('pt-BR').format(num);
    }

    showAlert(message, type) {
        const existingAlert = document.querySelector('.alert');
        if (existingAlert) {
            existingAlert.remove();
        }

        const alert = document.createElement('div');
        alert.className = `alert ${type}`;
        alert.textContent = message;
        
        document.querySelector('.container').insertBefore(alert, document.querySelector('main'));
        
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }

    expandAll() {
        document.querySelectorAll('.children-container').forEach(container => {
            container.style.display = 'block';
        });
        document.querySelectorAll('.expand-btn').forEach(btn => {
            btn.textContent = '⊖';
            btn.setAttribute('data-expanded', 'true');
        });
        this.allExpanded = true;
        this.updateToggleButton();
    }

    collapseAll() {
        document.querySelectorAll('.children-container').forEach(container => {
            container.style.display = 'none';
        });
        document.querySelectorAll('.expand-btn').forEach(btn => {
            btn.textContent = '⊕';
            btn.setAttribute('data-expanded', 'false');
        });
        this.allExpanded = false;
        this.updateToggleButton();
    }

    toggleAll() {
        if (this.allExpanded) {
            this.collapseAll();
        } else {
            this.expandAll();
        }
    }

    toggleNode(nodeId) {
        const container = document.getElementById(`children_${nodeId}`);
        const btn = document.querySelector(`[onclick*="app.toggleNode('${nodeId}')"]`);
        
        if (container && btn) {
            const isExpanded = btn.getAttribute('data-expanded') === 'true';
            
            if (isExpanded) {
                container.style.display = 'none';
                btn.innerHTML = '<span class="material-icons">add</span>';
                btn.setAttribute('data-expanded', 'false');
            } else {
                container.style.display = 'block';
                btn.innerHTML = '<span class="material-icons">remove</span>';
                btn.setAttribute('data-expanded', 'true');
            }
            
            this.updateToggleButton();
        }
    }

    updateToggleButton() {
        const toggleBtn = document.getElementById('toggleAllBtn');
        const allExpanded = Array.from(document.querySelectorAll('.expand-btn')).every(btn => 
            btn.getAttribute('data-expanded') === 'true'
        );
        
        this.allExpanded = allExpanded;
        toggleBtn.innerHTML = allExpanded ? '<span class="material-icons">unfold_less</span>Retrair Todos' : '<span class="material-icons">unfold_more</span>Expandir Todos';
    }

    // Métodos para gerenciamento de usuários
    async loadUsers() {
        if (!this.canManageUsers()) {
            this.showAlert('Sem permissão para gerenciar usuários', 'error');
            return;
        }
        
        try {
            const response = await fetch(`${this.apiUrl}/auth/users`, {
                headers: this.getAuthHeaders()
            });
            
            if (response.ok) {
                this.users = await response.json();
                this.renderUsersTable();
            } else {
                this.showAlert('Erro ao carregar usuários', 'error');
            }
        } catch (error) {
            this.showAlert('Erro de conexão', 'error');
        }
    }

    renderUsersTable() {
        const container = document.getElementById('usersTable');
        
        let html = `
            <table>
                <thead>
                    <tr>
                        <th>Nome</th>
                        <th>Email</th>
                        <th>Papel</th>
                        <th>Status</th>
                        <th>Criado em</th>
                        <th>Ações</th>
                    </tr>
                </thead>
                <tbody>
        `;

        this.users.forEach(user => {
            const roleDisplay = {
                'admin': 'Administrador',
                'operador': 'Operador', 
                'visualizador': 'Visualizador'
            }[user.role] || user.role;
            
            const statusDisplay = user.is_active ? 'Ativo' : 'Inativo';
            const statusClass = user.is_active ? 'status-active' : 'status-inactive';
            
            html += `
                <tr>
                    <td><strong>${user.nome || 'N/A'}</strong></td>
                    <td>${user.email}</td>
                    <td>${roleDisplay}</td>
                    <td>
                        <span class="${statusClass}">${statusDisplay}</span>
                        <button onclick="app.toggleUserStatus(${user.id})" class="action-btn" title="${user.is_active ? 'Desativar' : 'Ativar'} usuário">
                            <span class="material-icons">${user.is_active ? 'toggle_on' : 'toggle_off'}</span>
                        </button>
                    </td>
                    <td>${new Date(user.created_at).toLocaleDateString('pt-BR')}</td>
                    <td>
                        <button onclick="app.editUser(${user.id})" class="action-btn" title="Editar usuário">
                            <span class="material-icons">edit</span>
                        </button>
                        <button onclick="app.deleteUserConfirm(${user.id})" class="action-btn delete-btn" title="Excluir usuário">
                            <span class="material-icons">delete</span>
                        </button>
                    </td>
                </tr>
            `;
        });

        html += '</tbody></table>';
        container.innerHTML = html;
    }

    openUserModal(userId = null) {
        document.getElementById('userModalTitle').textContent = userId ? 'Editar Usuário' : 'Adicionar Usuário';
        document.getElementById('editUserId').value = userId || '';
        document.getElementById('userName').value = '';
        document.getElementById('userEmail').value = '';
        document.getElementById('userPassword').value = '';
        document.getElementById('userRole').value = 'VISUALIZADOR';
        document.getElementById('userActive').checked = true;
        document.getElementById('deleteUserBtn').style.display = userId ? 'block' : 'none';
        
        if (userId) {
            // Carregar dados do usuário
            const user = this.users.find(u => u.id === userId);
            if (user) {
                document.getElementById('userName').value = user.nome || '';
                document.getElementById('userEmail').value = user.email;
                document.getElementById('userPassword').placeholder = 'Deixe em branco para manter a senha atual';
                document.getElementById('userPassword').removeAttribute('required');
                document.getElementById('userRole').value = user.role.toUpperCase();
                document.getElementById('userActive').checked = user.is_active;
            }
        } else {
            document.getElementById('userPassword').setAttribute('required', '');
            document.getElementById('userPassword').placeholder = '';
        }
        
        document.getElementById('userModal').style.display = 'block';
    }

    closeUserModal() {
        document.getElementById('userModal').style.display = 'none';
    }

    async saveUser() {
        const userId = document.getElementById('editUserId').value;
        const nome = document.getElementById('userName').value;
        const email = document.getElementById('userEmail').value;
        const password = document.getElementById('userPassword').value;
        const role = document.getElementById('userRole').value;
        const is_active = document.getElementById('userActive').checked;

        if (!nome || !email || (!password && !userId)) {
            this.showAlert('Preencha todos os campos obrigatórios', 'error');
            return;
        }

        try {
            let response;
            
            if (userId) {
                // Atualizar usuário existente
                const updateData = { nome, email, role, is_active };
                if (password) {
                    updateData.password = password;
                }
                
                response = await fetch(`${this.apiUrl}/auth/users/${userId}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        ...this.getAuthHeaders()
                    },
                    body: JSON.stringify(updateData)
                });
            } else {
                // Criar novo usuário
                response = await fetch(`${this.apiUrl}/auth/register`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        ...this.getAuthHeaders()
                    },
                    body: JSON.stringify({ nome, email, password, role })
                });
            }

            if (response.ok) {
                this.showAlert(userId ? 'Usuário atualizado com sucesso' : 'Usuário criado com sucesso', 'success');
                this.closeUserModal();
                this.loadUsers();
            } else {
                const error = await response.json();
                this.showAlert(error.detail || 'Erro ao salvar usuário', 'error');
            }
        } catch (error) {
            this.showAlert('Erro de conexão', 'error');
        }
    }

    editUser(userId) {
        this.openUserModal(userId);
    }

    async deleteUser() {
        const userId = document.getElementById('editUserId').value;
        
        if (!userId) return;
        
        if (!confirm('Tem certeza que deseja excluir este usuário?')) {
            return;
        }

        try {
            const response = await fetch(`${this.apiUrl}/auth/users/${userId}`, {
                method: 'DELETE',
                headers: this.getAuthHeaders()
            });

            if (response.ok) {
                this.showAlert('Usuário excluído com sucesso', 'success');
                this.closeUserModal();
                this.loadUsers();
            } else {
                const error = await response.json();
                this.showAlert(error.detail || 'Erro ao excluir usuário', 'error');
            }
        } catch (error) {
            this.showAlert('Erro de conexão', 'error');
        }
    }

    deleteUserConfirm(userId) {
        const user = this.users.find(u => u.id === userId);
        if (!user) return;

        if (confirm(`Tem certeza que deseja excluir o usuário "${user.nome || user.email}"?`)) {
            this.deleteUserDirect(userId);
        }
    }

    async deleteUserDirect(userId) {
        try {
            const response = await fetch(`${this.apiUrl}/auth/users/${userId}`, {
                method: 'DELETE',
                headers: this.getAuthHeaders()
            });

            if (response.ok) {
                this.showAlert('Usuário excluído com sucesso', 'success');
                this.loadUsers();
            } else {
                const error = await response.json();
                this.showAlert(error.detail || 'Erro ao excluir usuário', 'error');
            }
        } catch (error) {
            this.showAlert('Erro de conexão', 'error');
        }
    }

    async toggleUserStatus(userId) {
        try {
            const response = await fetch(`${this.apiUrl}/auth/users/${userId}/status`, {
                method: 'PUT',
                headers: this.getAuthHeaders()
            });

            if (response.ok) {
                const result = await response.json();
                this.showAlert(result.message, 'success');
                this.loadUsers();
            } else {
                const error = await response.json();
                this.showAlert(error.detail || 'Erro ao alterar status do usuário', 'error');
            }
        } catch (error) {
            this.showAlert('Erro de conexão', 'error');
        }
    }
}

const app = new IPAMApp();