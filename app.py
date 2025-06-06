from flask import Flask, request, jsonify
from flask_cors import CORS
import bcrypt
import jwt
import datetime
from db import get_db_connection
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)
JWT_SECRET = os.getenv("JWT_SECRET")

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    nome = data["fullName"]
    email = data["email"]
    senha = data["password"]

    hashed = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt())

    db = get_db_connection()
    cursor = db.cursor()

    try:
        cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)", (nome, email, hashed))
        db.commit()
        return jsonify({"message": "Usuário registrado com sucesso!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        db.close()

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data["email"]
    senha = data["password"]

    db = get_db_connection()
    cursor = db.cursor()
    cursor.execute("SELECT id, nome, senha FROM usuarios WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    db.close()

    if user and bcrypt.checkpw(senha.encode("utf-8"), user[2].encode("utf-8")):
        token = jwt.encode({
            "user_id": user[0],
            "nome": user[1],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        }, JWT_SECRET, algorithm="HS256")

        return jsonify({"token": token, "nome": user[1]}), 200
    else:
        return jsonify({"error": "Credenciais inválidas"}), 401

if __name__ == "__main__":
    app.run(debug=True)
