
// --- Elementos principais ---
const table = document.getElementById("dataTable");
const tbody = document.getElementById("tableBody");
const loading = document.getElementById("loading");
const saveButton = document.getElementById("saveButton");
const alertBox = document.getElementById("alertBox");

const startDateInput = document.getElementById("startDate");
const endDateInput = document.getElementById("endDate");
const statusFilter = document.getElementById("statusFilter");
const employeeFilter = document.getElementById("employeeFilter");
const customerFilter = document.getElementById("customerFilter");
const pagination = document.getElementById("pagination");

// --- Endpoints Flask ---
const API_URL = "/api/services";
const SAVE_URL = "/api/services/update";

// --- Variáveis globais ---
let tableData = [];
let originalData = [];
let currentPage = 1;
const rowsPerPage = 30;
let totalRecords = 0;

// --- Funções utilitárias ---
function showAlert(message, type = "error") {
  alertBox.innerHTML = `<div class="${type === "error" ? "error" : "success"}">${message}</div>`;
  setTimeout(() => (alertBox.innerHTML = ""), 4000);
}

// --- Carregar dados do servidor ---
async function loadData(page = 1) {
  try {
    loading.style.display = "block";
    table.style.display = "none";
    saveButton.style.display = "none";
    loading.textContent = "Carregando dados...";

    const params = new URLSearchParams({
      page,
      limit: rowsPerPage,
      start_date: startDateInput.value || "",
      end_date: endDateInput.value || "",
      status: statusFilter.value || "",
      employee: employeeFilter.value || "",
      customer: customerFilter.value || "",
    });

    const response = await fetch(`${API_URL}?${params.toString()}`);
    const result = await response.json();

    if (!result.data || result.data.length === 0) {
      loading.textContent = "Nenhum dado encontrado.";
      return;
    }

    tableData = result.data;
    originalData = JSON.parse(JSON.stringify(result.data));
    totalRecords = result.total || tableData.length;

    renderTable();
    renderPagination();

    loading.style.display = "none";
    table.style.display = "table";
    saveButton.style.display = "block";
  } catch (err) {
    console.error("❌ Erro ao carregar dados:", err);
    loading.textContent = "Erro ao carregar dados.";
  }
}

// --- Renderizar tabela ---
function renderTable() {
  tbody.innerHTML = "";

  tableData.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
    <td><button class="btn-edit" data-id="${row.order_id}">Editar</button></td>
    <td>
      <select data-id="${row.order_id}" name="PGTO" disabled>
        <option value="">Selecione</option>
        <option value="Sim" ${row.PGTO === "Sim" ? "selected" : ""}>Sim</option>
        <option value="Não" ${row.PGTO === "Não" ? "selected" : ""}>Não</option>
        <option value="Cancelado" ${row.PGTO === "Cancelado" ? "selected" : ""}>Cancelado</option>
      </select>
    </td>
    <td><input type="date" data-id="${row.order_id}" name="DATPGTO" value="${row.DATPGTO || ""}" disabled></td>
      <td>${row.order_id || "-"}</td>
      <td>${row.employees || "-"}</td>
      <td>${row.customer_name || "-"}</td>
      <td>${row.schedule_date || "-"}</td>
      <td>${row.space_name || "-"}</td>
      <td>${row.service_name || "-"}</td>
      <td>${row.stay_external || "-"}</td>
      <td>${row.service_status || "-"}</td>
      <td>${row.gross_total || "-"}</td>
    `;
    tbody.appendChild(tr);
  });

  setupEditButtons();
}

// --- Paginação ---
function renderPagination() {
  pagination.innerHTML = "";
  const totalPages = Math.ceil(totalRecords / rowsPerPage);

  const prevBtn = document.createElement("button");
  prevBtn.textContent = "Anterior";
  prevBtn.disabled = currentPage === 1;
  prevBtn.addEventListener("click", () => {
    if (currentPage > 1) {
      currentPage--;
      loadData(currentPage);
    }
  });

  const nextBtn = document.createElement("button");
  nextBtn.textContent = "Próximo";
  nextBtn.disabled = currentPage === totalPages;
  nextBtn.addEventListener("click", () => {
    if (currentPage < totalPages) {
      currentPage++;
      loadData(currentPage);
    }
  });

  const pageInfo = document.createElement("span");
  pageInfo.textContent = `Página ${currentPage} de ${totalPages}`;

  pagination.appendChild(prevBtn);
  pagination.appendChild(pageInfo);
  pagination.appendChild(nextBtn);
}

// --- Filtros ---
[startDateInput, endDateInput, statusFilter, employeeFilter, customerFilter].forEach(el => {
  el.addEventListener("input", () => {
    currentPage = 1;
    loadData(1);
  });
});

// --- Edição ---
function setupEditButtons() {
  document.querySelectorAll(".btn-edit").forEach(btn => {
    btn.addEventListener("click", () => {
      const tr = btn.closest("tr");
      const select = tr.querySelector("select[name='PGTO']");
      const dateInput = tr.querySelector("input[name='DATPGTO']");
      const orderId = btn.dataset.id;

      if (select.disabled) {
        select.disabled = false;
        dateInput.disabled = false;
        tr.classList.add("modified");
        btn.textContent = "Bloquear";
      } else {
        select.disabled = true;
        dateInput.disabled = true;
        tr.classList.remove("modified");
        btn.textContent = "Editar";

        const original = originalData.find(r => r.order_id === orderId);
        if (original) {
          select.value = original.PGTO || "";
          dateInput.value = original.DATPGTO || "";
          const row = tableData.find(r => r.order_id === orderId);
          if (row) {
            row.PGTO = original.PGTO;
            row.DATPGTO = original.DATPGTO;
          }
        }
      }
    });
  });

  document.querySelectorAll("select[name='PGTO'], input[name='DATPGTO']").forEach(el => {
    el.addEventListener("change", e => {
      const id = e.target.dataset.id;
      const name = e.target.name;
      const value = e.target.value;
      const row = tableData.find(r => r.order_id === id);
      if (row) row[name] = value;
    });
  });
}

// --- Salvar alterações ---
saveButton.addEventListener("click", async () => {
  try {
    saveButton.disabled = true;
    saveButton.textContent = "Salvando...";
    alertBox.innerHTML = "";

    const modifiedRows = tableData.filter(row => {
      const original = originalData.find(r => r.order_id === row.order_id);
      return (
        row.PGTO !== original.PGTO ||
        row.DATPGTO !== original.DATPGTO
      );
    }).map(row => ({
      order_id: row.order_id,
      PGTO: row.PGTO,
      DATPGTO: row.DATPGTO
    }));

    if (modifiedRows.length === 0) {
      showAlert("Nenhuma alteração para salvar.", "error");
      return;
    }

    const response = await fetch(SAVE_URL, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(modifiedRows)
    });

    if (!response.ok) throw new Error("Falha ao salvar dados.");

    const result = await response.json();
    showAlert("Alterações salvas com sucesso!", "success");

    originalData = JSON.parse(JSON.stringify(tableData));
    loadData(currentPage);
  } catch (err) {
    console.error("❌ Erro ao salvar:", err);
    showAlert("Erro ao salvar alterações.", "error");
  } finally {
    saveButton.disabled = false;
    saveButton.textContent = "Salvar Alterações";
  }
});

// --- Inicialização ---
document.addEventListener("DOMContentLoaded", () => loadData(1));
