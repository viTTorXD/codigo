// Login local
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    try {
        const response = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            localStorage.setItem('token', data.token);
            window.location.href = '/dashboard';
        } else {
            alert(data.error || 'Erro no login');
        }
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao conectar com o servidor');
    }
});

// Login com Google
document.getElementById('googleLogin').addEventListener('click', () => {
    window.location.href = '/auth/google';
});

// Login com Microsoft
document.getElementById('microsoftLogin').addEventListener('click', () => {
    window.location.href = '/auth/microsoft';
});

fetch('http://localhost:5000/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        fullName: 'João da Silva',
        email: 'joao@example.com',
        password: 'senha1234'
    })
})
.then(res => res.json())
.then(data => console.log(data));
