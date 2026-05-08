from models.sup_client import supabase
import pandas as pd

# --- Função auxiliar para aplicar filtros ---
def apply_filters(query, start_date=None, end_date=None, status=None,statusdoinn=None, employee=None, service=None):
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

    if statusdoinn:
        query = query.eq("service_status", statusdoinn)

    if employee:
        query = query.ilike("employees", f"%{employee}%")

    if service:
        query = query.ilike("service_name", f"%{service}%")

    return query

def select():
    """Seleciona todos os dados da tabela 'services'."""
    result = supabase.table("services").select("*").execute()
    data = result.data
    df = pd.DataFrame(data)
    return df

def export_to_csv(df, filename="exported_data.csv"):
    """Exporta o DataFrame para um arquivo CSV."""
    df.to_csv(filename, index=False)

df = select()

df = apply_filters(
    df,
    start_date="2025-12-01",
    end_date="2025-12-31",
)

print(df.head(10),"Total de Linhas: ",len(df))  # Exibe as primeiras linhas do DataFrame para verificação