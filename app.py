from flask import Flask, request, jsonify
from flask_cors import CORS
import bcrypt
import jwt
import datetime
from db import get_db_connection
import os
from functools import wraps
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
import string

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configurações
JWT_SECRET = os.getenv("JWT_SECRET")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Decorator para verificar token JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]

        if not token:
            return jsonify({"error": "Token ausente"}), 401

        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            request.user = data
            
            # Verificar se o usuário ainda existe no banco de dados
            db = get_db_connection()
            cursor = db.cursor()
            cursor.execute("SELECT id FROM usuarios WHERE id = %s AND ativo = TRUE", (data["user_id"],))
            if not cursor.fetchone():
                return jsonify({"error": "Usuário não encontrado ou desativado"}), 401
            cursor.close()
            db.close()
            
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expirado"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token inválido"}), 401
        except Exception as e:
            return jsonify({"error": str(e)}), 500

        return f(*args, **kwargs)
    return decorated

# Função para enviar e-mail
def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False

# Gera token alfanumérico
def generate_token(length=32):
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

# Endpoint de registro
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    nome = data.get("nome")
    email = data.get("email")
    senha = data.get("senha")

    if not all([nome, email, senha]):
        return jsonify({"error": "Todos os campos são obrigatórios"}), 400

    if len(senha) < 8:
        return jsonify({"error": "A senha deve ter no mínimo 8 caracteres"}), 400

    hashed = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)", 
                      (nome, email, hashed))
        db.commit()
        
        # Registrar log
        user_id = cursor.lastrowid
        cursor.execute("INSERT INTO logs_autenticacao (usuario_id, acao) VALUES (%s, %s)",
                      (user_id, "registro"))
        db.commit()
        
        return jsonify({"message": "Usuário registrado com sucesso!"}), 201
    except mysql.connector.IntegrityError as e:
        if "Duplicate entry" in str(e):
            return jsonify({"error": "E-mail já cadastrado"}), 400
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()

# Endpoint de login
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    senha = data.get("senha")

    if not email or not senha:
        return jsonify({"error": "E-mail e senha são obrigatórios"}), 400

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id, nome, senha FROM usuarios WHERE email = %s AND ativo = TRUE", (email,))
        user = cursor.fetchone()
        
        if user and bcrypt.checkpw(senha.encode("utf-8"), user["senha"].encode("utf-8")):
            token = jwt.encode({
                "user_id": user["id"],
                "nome": user["nome"],
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
            }, JWT_SECRET, algorithm="HS256")

            # Registrar log de login
            cursor.execute("INSERT INTO logs_autenticacao (usuario_id, acao) VALUES (%s, %s)",
                          (user["id"], "login"))
            db.commit()
            
            return jsonify({
                "token": token,
                "nome": user["nome"],
                "user_id": user["id"]
            }), 200
        else:
            # Registrar tentativa falha
            cursor.execute("INSERT INTO logs_autenticacao (acao, ip) VALUES (%s, %s)",
                          ("login_failed", request.remote_addr))
            db.commit()
            return jsonify({"error": "Credenciais inválidas"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()

# Endpoint para solicitar recuperação de senha
@app.route("/forgot-password", methods=["POST"])
def forgot_password():
    email = request.json.get("email")
    
    if not email:
        return jsonify({"error": "E-mail é obrigatório"}), 400

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id, nome FROM usuarios WHERE email = %s AND ativo = TRUE", (email,))
        user = cursor.fetchone()
        
        if user:
            token = generate_token()
            expiracao = datetime.datetime.now() + datetime.timedelta(hours=1)
            
            cursor.execute("""
                INSERT INTO tokens_recuperacao (usuario_id, token, expiracao)
                VALUES (%s, %s, %s)
            """, (user["id"], token, expiracao))
            db.commit()
            
            # Enviar e-mail com o link de recuperação
            reset_link = f"{FRONTEND_URL}/reset-password?token={token}"
            subject = "Recuperação de Senha - NEXGEN"
            body = f"""
            <h3>Olá, {user['nome']}!</h3>
            <p>Recebemos uma solicitação para redefinir sua senha na NEXGEN.</p>
            <p>Clique no link abaixo para redefinir sua senha (válido por 1 hora):</p>
            <p><a href="{reset_link}">{reset_link}</a></p>
            <p>Se você não solicitou esta alteração, ignore este e-mail.</p>
            """
            
            if send_email(email, subject, body):
                return jsonify({"message": "E-mail de recuperação enviado com sucesso"}), 200
            else:
                return jsonify({"error": "Falha ao enviar e-mail de recuperação"}), 500
        else:
            return jsonify({"message": "Se o e-mail existir, um link de recuperação será enviado"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()

# Endpoint para redefinir senha
@app.route("/reset-password", methods=["POST"])
def reset_password():
    token = request.json.get("token")
    new_password = request.json.get("new_password")
    
    if not token or not new_password:
        return jsonify({"error": "Token e nova senha são obrigatórios"}), 400
    
    if len(new_password) < 8:
        return jsonify({"error": "A senha deve ter no mínimo 8 caracteres"}), 400

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT usuario_id FROM tokens_recuperacao 
            WHERE token = %s AND utilizado = FALSE AND expiracao > NOW()
        """, (token,))
        valid_token = cursor.fetchone()
        
        if valid_token:
            hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            
            # Atualizar senha do usuário
            cursor.execute("UPDATE usuarios SET senha = %s WHERE id = %s",
                         (hashed, valid_token["usuario_id"]))
            
            # Marcar token como utilizado
            cursor.execute("UPDATE tokens_recuperacao SET utilizado = TRUE WHERE token = %s",
                         (token,))
            
            # Registrar log
            cursor.execute("INSERT INTO logs_autenticacao (usuario_id, acao) VALUES (%s, %s)",
                          (valid_token["usuario_id"], "recuperacao_senha"))
            
            db.commit()
            return jsonify({"message": "Senha redefinida com sucesso"}), 200
        else:
            return jsonify({"error": "Token inválido ou expirado"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()

# Endpoint protegido - Dashboard
@app.route("/dashboard", methods=["GET"])
@token_required
def dashboard():
    user = request.user
    return jsonify({
        "message": f"Bem-vindo, {user['nome']}!",
        "user_id": user["user_id"],
        "user_name": user["nome"]
    })

# Endpoint para verificar token válido
@app.route("/validate-token", methods=["GET"])
@token_required
def validate_token():
    return jsonify({"valid": True}), 200

# Endpoint para obter informações do usuário
@app.route("/user-info", methods=["GET"])
@token_required
def user_info():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT id, nome, email, data_criacao 
            FROM usuarios 
            WHERE id = %s
        """, (request.user["user_id"],))
        user = cursor.fetchone()
        
        if user:
            return jsonify(user), 200
        else:
            return jsonify({"error": "Usuário não encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    app.run(debug=True)

    # Adicione esta rota temporária ao seu app.py
@app.route("/test-db")
def test_db():
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        db.close()
        return jsonify({"status": "success", "db_connection": "OK", "result": result[0]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500