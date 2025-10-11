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
    customer = request.args.get("customer")

    query = supabase.table("services").select("*")

    if start_date:
        query = query.gte("schedule_date", start_date)
    if end_date:
        query = query.lte("schedule_date", end_date)

    if status:
        if status == "Pendente":
            try:
                query = query.or_("PGTO.is.null,PGTO.eq.''")
            except Exception:
                pass
        else:
            query = query.eq("PGTO", status)

    if employee:
        query = query.ilike("employees", f"%{employee}%")
    if customer:
        query = query.ilike("customer_name", f"%{customer}%")

    data_result = query.range(offset, offset + limit - 1).execute()

    # Total de registros filtrados
    try:
        count_query = supabase.table("services").select("order_id", count="exact")
        if start_date:
            count_query = count_query.gte("schedule_date", start_date)
        if end_date:
            count_query = count_query.lte("schedule_date", end_date)
        if status:
            if status == "Pendente":
                try:
                    count_query = count_query.or_("PGTO.is.null,PGTO.eq.''")
                except Exception:
                    pass
            else:
                count_query = count_query.eq("PGTO", status)
        if employee:
            count_query = count_query.ilike("employees", f"%{employee}%")
        if customer:
            count_query = count_query.ilike("customer_name", f"%{customer}%")
        total = getattr(count_query.execute(), "count", len(data_result.data))
    except Exception:
        total = len(data_result.data)

    return jsonify({
        "data": data_result.data or [],
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
