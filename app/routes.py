from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from .models.sup_client import supabase

main = Blueprint("main", __name__)

# --- Página de login ---
@main.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("email")
        password = request.form.get("senha")
        if not user or not password:
            return render_template("login.html", error="Por favor, preencha todos os campos")
        # Autenticação básica no Supabase (tabela usuarios)
        result = supabase.table("credential").select("*").eq("email", user).eq("senha", password).execute()

        if result.data:
            session["user"] = user
            return redirect(url_for("main.dashboard"))
        else:
            return render_template("login.html", error="Usuário ou senha inválidos")

    return render_template("login.html")

# --- Página principal ---
@main.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("main.login"))
    return render_template("services.html")

# --- API: buscar dados ---
@main.route("/api/services", methods=["GET"])
def get_services():
    data = supabase.table("services").select("*").execute()
    return jsonify(data.data)

# --- API: atualizar dados ---
@main.route("/api/services/update", methods=["PUT"])
def update_services():
    updates = request.get_json()
    for row in updates:
        supabase.table("services").update({
            "PGTO": row["PGTO"],
            "DATPGTO": row["DATPGTO"]
        }).eq("id", row["id"]).execute()
    return jsonify({"message": "Atualizações salvas com sucesso"})

# --- Logout ---
@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))
