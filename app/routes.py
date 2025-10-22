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
        # Autenticação básica no Supabase (tabela credential)
        result = supabase.table("credential") \
            .select("*") \
            .eq("email", user) \
            .eq("senha", password) \
            .execute()

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


# --- API: buscar dados com filtros e paginação ---
@main.route("/api/services", methods=["GET"])
def get_services():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 50))
    offset = (page - 1) * limit

    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    status = request.args.get("status")
    employee = request.args.get("employee")
    service = request.args.get("service")

    # 1. Construir a consulta para os DADOS (sem count() na seleção)
    data_query = supabase.table("services").select("order_id, PGTO, DATPGTO, gross_total, employees, schedule_date, space_name, service_name, stay_external, service_status")

    # 2. Construir a consulta para a CONTAGEM TOTAL (apenas count())
    count_query = supabase.table("services").select("*", count="exact")

    # Aplicar os mesmos filtros a AMBAS as consultas
    if start_date:
        data_query = data_query.gte("schedule_date", start_date)
        count_query = count_query.gte("schedule_date", start_date)
    if end_date:
        data_query = data_query.lte("schedule_date", end_date)
        count_query = count_query.lte("schedule_date", end_date)

    if status:
        if status == "Pendente":
            # A cláusula .or_ precisa ser construída cuidadosamente para PostgREST
            data_query = data_query.or_("PGTO.is.null,PGTO.eq.\\'\\'", group="and")
            count_query = count_query.or_("PGTO.is.null,PGTO.eq.\\'\\'", group="and")
        else:
            data_query = data_query.eq("PGTO", status)
            count_query = count_query.eq("PGTO", status)

    if employee:
        data_query = data_query.ilike("employees", f"%{employee}%")
        count_query = count_query.ilike("employees", f"%{employee}%")
    if service:
        data_query = data_query.ilike("service_name", f"%{service}%")
        count_query = count_query.ilike("service_name", f"%{service}%")


    # Executa a consulta de dados com paginação
    data_result = data_query.range(offset, offset + limit - 1).execute()
    data = data_result.data


    # Executa a consulta de contagem separadamente
    total_count_result = count_query.execute()
    total = total_count_result.count or 0

    return jsonify({
        "data": data or [],
        "total": total
    })


# --- API: atualizar dados ---
@main.route("/api/services/update", methods=["PUT"])
def update_services():
    updates = request.get_json()
    if not updates or not isinstance(updates, list):
        return jsonify({"error": "Payload inválido"}), 400

    updated_count = 0
    errors = []

    for row in updates:
        order_id = row.get("order_id")
        if not order_id:
            errors.append({"row": row, "error": "order_id ausente"})
            continue

        try:
            supabase.table("services").update({
                "PGTO": row.get("PGTO"),
                "DATPGTO": row.get("DATPGTO") or None
            }).eq("order_id", order_id).execute()
            updated_count += 1
        except Exception as e:
            errors.append({"order_id": order_id, "error": str(e)})

    resp = {"message": "Atualizações processadas", "updated": updated_count}
    if errors:
        resp["errors"] = errors

    return jsonify(resp)


# --- Logout ---
@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))