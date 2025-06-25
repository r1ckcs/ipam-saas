const API_BASE = 'http://localhost:8000';

// Controlar as abas
document.addEventListener('DOMContentLoaded', function() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            
            // Remover classe active de todas as abas
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));
            
            // Adicionar classe active na aba clicada
            btn.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });

    // Formulário de login
    document.getElementById('loginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const email = document.getElementById('loginEmail').value;
        const password = document.getElementById('loginPassword').value;
        
        try {
            const response = await fetch(`${API_BASE}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Salvar dados do usuário
                localStorage.setItem('user', JSON.stringify(data.user));
                showMessage('Login realizado com sucesso!', 'success');
                
                // Redirecionar para página principal após 1 segundo
                setTimeout(() => {
                    window.location.href = 'index.html';
                }, 1000);
            } else {
                showMessage(data.detail || 'Erro no login', 'error');
            }
        } catch (error) {
            showMessage('Erro de conexão com o servidor', 'error');
        }
    });

});

function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = text;
    messageDiv.className = `message ${type}`;
    messageDiv.style.display = 'block';
    
    // Ocultar mensagem após 5 segundos
    setTimeout(() => {
        messageDiv.style.display = 'none';
    }, 5000);
}