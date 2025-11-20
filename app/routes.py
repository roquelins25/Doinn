from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from .models.sup_client import supabase

main = Blueprint("main", __name__)

# --- Função auxiliar para aplicar filtros ---
def apply_filters(query, start_date=None, end_date=None, status=None, employee=None, service=None):
    """Aplica filtros opcionais a uma consulta Supabase."""
    if start_date:
        query = query.gte("schedule_date", start_date)
    if end_date:
        query = query.lte("schedule_date", end_date)

    if status:
        if status == "Pendente":
            query = query.or_("PGTO.eq.Pendente,PGTO.is.null,PGTO.eq.''")
        else:
            query = query.eq("PGTO", status)

    if employee:
        query = query.ilike("employees", f"%{employee}%")

    if service:
        query = query.ilike("service_name", f"%{service}%")

    return query

# --- Página de login ---
@main.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("email")
        password = request.form.get("senha")
        if not user or not password:
            return render_template("login.html", error="Por favor, preencha todos os campos")

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

    order_by = request.args.get("order_by", "schedule_date")
    order_dir = request.args.get("order_dir", "asc").lower()
    allowed_columns = {
        "order_id", "PGTO", "DATPGTO", "gross_total",
        "employees", "schedule_date", "space_name",
        "service_name", "stay_external", "service_status"
    }
    if order_by not in allowed_columns:
        order_by = "schedule_date"

    desc_order = order_dir == "desc"

    try:
        data_query = supabase.table("services").select(
            "id_pk,order_id,PGTO,DATPGTO,gross_total,employees,schedule_date,space_name,service_name,stay_external,service_status"
        )
        data_query = data_query.neq("gross_total", 0).not_.is_("gross_total", None)
        data_query = apply_filters(data_query, start_date, end_date, status, employee, service)
        data_query = data_query.order(order_by, desc=desc_order)

        count_query = supabase.table("services").select("*", count="exact")
        count_query = count_query.neq("gross_total", 0).not_.is_("gross_total", None)
        count_query = apply_filters(count_query, start_date, end_date, status, employee, service)

        data_result = data_query.range(offset, offset + limit - 1).execute()
        data = data_result.data or []

        total_count_result = count_query.execute()
        total = total_count_result.count or len(data)

        return jsonify({"data": data, "total": total})
    except Exception as e:
        print(f"Erro ao buscar dados do Supabase: {e}")
        return jsonify({"error": "Erro ao conectar com o banco de dados. Tente novamente mais tarde."}), 500

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

# --- API: totais ---
@main.route("/api/totais", methods=["GET"])
def get_totals():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    status = request.args.get("status")
    employee = request.args.get("employee")
    service = request.args.get("service")

    try:
        query = supabase.table("services").select("gross_total", count="exact")
        query = query.neq("gross_total", 0).not_.is_("gross_total", None)
        query = apply_filters(query, start_date, end_date, status, employee, service)

        result = query.execute()
        data = result.data or []

        total_bruto = sum(float(row.get("gross_total") or 0) for row in data)
        total_count = result.count or len(data)

        return jsonify({
            "gross_total_sum": total_bruto,
            "services_count": total_count
        })
    except Exception as e:
        print(f"Erro ao buscar totais do Supabase: {e}")
        return jsonify({"error": "Erro ao conectar com o banco de dados. Tente novamente mais tarde."}), 500

# --- Logout ---
@main.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))

# --- Impressão ---
@main.route("/imprimir_relatorio")
def imprimir():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    status = request.args.get("status")
    employee = request.args.get("employee")
    service = request.args.get("service")

    query = supabase.table("services").select(
        "employees, service_name, space_name, schedule_date, gross_total, PGTO"
    ).gt("gross_total", 0)
    query = apply_filters(query, start_date, end_date, status, employee, service)
    result = query.execute()
    pagamentos = result.data or []

    total_bruto = sum(float(row.get("gross_total") or 0) for row in pagamentos)

    return render_template("imprimir.html", pagamentos=pagamentos, total_bruto=total_bruto)
