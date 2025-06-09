// =======================
// Carregar Dashboard
// =======================
async function carregarDashboard() {
    const token = localStorage.getItem("token");

    if (!token) {
        alert("Você precisa estar logado.");
        window.location.href = "login.html";
        return;
    }

    try {
        const response = await fetch("http://localhost:5000/dashboard", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        const data = await response.json();

        if (response.ok) {
            const nome = localStorage.getItem("nome");
            document.getElementById("boasVindas").textContent = `Bem-vindo, ${nome || "usuário"}!`;
        } else {
            alert(data.error || "Erro ao carregar dashboard");
            localStorage.removeItem("token");
            localStorage.removeItem("nome");
            window.location.href = "login.html";
        }
    } catch (error) {
        console.error("Erro:", error);
        alert("Erro de conexão com o servidor");
    }
}

// Função para sanitizar inputs
function sanitize(str) {
    return str.replace(/[<>"'\/]/g, "");
}

// =======================
// Validação de Cadastro
// =======================
document.getElementById('registerForm')?.addEventListener('submit', async function (e) {
    e.preventDefault();

    const form = e.target;
    const nome = sanitize(form.querySelector('#nome').value);
    const email = sanitize(form.querySelector('#email').value);
    const senha = form.querySelector('#senha').value;
    const confirmSenha = form.querySelector('#confirmsenha').value;

    if (senha.length < 8) {
        alert("A senha deve ter no mínimo 8 caracteres.");
        return;
    }

    if (senha !== confirmSenha) {
        alert("As senhas não coincidem.");
        return;
    }

    try {
        const response = await fetch('http://localhost:5000/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome, email, senha })
        });

        const data = await response.json();

        if (response.ok) {
            alert("Cadastro realizado com sucesso!");
            window.location.href = "login.html";
        } else {
            alert(data.error || 'Erro no cadastro');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao conectar com o servidor');
    }
});

// =======================
// Login Local
// =======================
document.getElementById('loginForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const form = e.target;
    const email = sanitize(form.querySelector('#email').value);
    const senha = form.querySelector('#senha').value;

    try {
        const response = await fetch('http://localhost:5000/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, senha })
        });

        const data = await response.json();

        if (response.ok) {
            localStorage.setItem('token', data.token);
            localStorage.setItem('nome', data.nome);
            window.location.href = '/dashboard.html';
        } else {
            alert(data.error || 'Erro no login');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao conectar com o servidor');
    }
});

// =======================
// Login com Google
// =======================
document.getElementById('googleLogin')?.addEventListener('click', () => {
    window.location.href = '/auth/google';
});

// =======================
// Login com Microsoft
// =======================
document.getElementById('microsoftLogin')?.addEventListener('click', () => {
    window.location.href = '/auth/microsoft';
});
