// dashboard.js — versão debugada e adaptada para Flask

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
let sortField = null;
let sortOrder = 1; // 1 = asc, -1 = desc

// --- Funções utilitárias ---
function showAlert(message, type = "error") {
  alertBox.innerHTML = `<div class="${type === "error" ? "error" : "success"}">${message}</div>`;
  setTimeout(() => (alertBox.innerHTML = ""), 4000);
}

// --- Carregar dados ---
async function loadData() {
  try {
    loading.textContent = "Carregando dados...";
    const response = await fetch(API_URL);
    const data = await response.json();

    if (!Array.isArray(data) || data.length === 0) {
      loading.textContent = "Nenhum dado encontrado.";
      return;
    }

    tableData = JSON.parse(JSON.stringify(data));
    originalData = JSON.parse(JSON.stringify(data));

    renderTable();
    setupFilters();
    setupSorting();

    loading.style.display = "none";
    table.style.display = "table";
    saveButton.style.display = "block";
  } catch (err) {
    console.error("Erro ao carregar dados:", err);
    loading.textContent = "Erro ao carregar dados.";
  }
}

// --- Renderizar tabela com filtros, ordenação e paginação ---
function renderTable() {
  tbody.innerHTML = "";

  let filteredData = applyFilters();

  // Ordenação
  if (sortField) {
    filteredData.sort((a, b) => {
      let valA = a[sortField];
      let valB = b[sortField];

      if (sortField.includes("date")) {
        valA = new Date(valA || "1970-01-01");
        valB = new Date(valB || "1970-01-01");
      }

      if (typeof valA === "string") valA = valA.toLowerCase();
      if (typeof valB === "string") valB = valB.toLowerCase();

      if (valA > valB) return 1 * sortOrder;
      if (valA < valB) return -1 * sortOrder;
      return 0;
    });
  }

  // Paginação
  const totalRows = filteredData.length;
  const totalPages = Math.ceil(totalRows / rowsPerPage);
  const start = (currentPage - 1) * rowsPerPage;
  const end = start + rowsPerPage;
  const pageData = filteredData.slice(start, end);

  pageData.forEach((row, index) => {
    const tr = document.createElement("tr");
    const globalIndex = tableData.findIndex(r => r.id === row.id);

    tr.innerHTML = `
      <td>${row.order_id || "-"}</td>
      <td>${row.employees || "-"}</td>
      <td>${row.customer_name || "-"}</td>
      <td>${row.schedule_date || "-"}</td>
      <td>${row.space_name || "-"}</td>
      <td>${row.service_name || "-"}</td>
      <td>${row.stay_external || "-"}</td>
      <td>${row.service_status || "-"}</td>
      <td>${row.gross_total || "-"}</td>
      <td>
        <select data-index="${globalIndex}" name="PGTO" disabled>
          <option value="">Selecione</option>
          <option value="Sim" ${row.PGTO === "Sim" ? "selected" : ""}>Sim</option>
          <option value="Não" ${row.PGTO === "Não" ? "selected" : ""}>Não</option>
          <option value="Cancelado" ${row.PGTO === "Cancelado" ? "selected" : ""}>Cancelado</option>
        </select>
      </td>
      <td><input type="date" data-index="${globalIndex}" name="DATPGTO" value="${row.DATPGTO || ""}" disabled></td>
      <td><button class="btn-edit" data-index="${globalIndex}">Editar</button></td>
    `;
    tbody.appendChild(tr);
  });

  setupEditButtons();
  setupPaginationButtons(totalPages);
}

// --- Filtros ---
function setupFilters() {
  [startDateInput, endDateInput, statusFilter, employeeFilter, customerFilter].forEach(el => {
    el.addEventListener("input", () => {
      currentPage = 1;
      renderTable();
    });
  });
}

function applyFilters() {
  return tableData.filter(row => {
    const start = startDateInput.value;
    const end = endDateInput.value;
    const status = statusFilter.value;
    const emp = employeeFilter.value.toLowerCase();
    const cust = customerFilter.value.toLowerCase();

    let keep = true;
    if (start && row.schedule_date < start) keep = false;
    if (end && row.schedule_date > end) keep = false;
    if (status && row.PGTO !== status) keep = false;
    if (emp && !(row.employees || "").toLowerCase().includes(emp)) keep = false;
    if (cust && !(row.customer_name || "").toLowerCase().includes(cust)) keep = false;

    return keep;
  });
}

// --- Ordenação ---
function setupSorting() {
  document.querySelectorAll("th[data-field]").forEach(th => {
    th.addEventListener("click", () => {
      if (sortField === th.dataset.field) {
        sortOrder *= -1;
      } else {
        sortField = th.dataset.field;
        sortOrder = 1;
      }
      renderTable();
    });
  });
}


function setupEditButtons() {
  document.querySelectorAll(".btn-edit").forEach(btn => {
    btn.addEventListener("click", () => {
      const tr = btn.closest("tr");
      const select = tr.querySelector("select[name='PGTO']");
      const dateInput = tr.querySelector("input[name='DATPGTO']");
      const index = select.dataset.index;

      console.log(`Botão clicado na linha ${index}`);

      // Alterna entre modo edição e bloqueado
      if (select.disabled) {
        select.disabled = false;
        dateInput.disabled = false;
        tr.classList.add("modified");
        btn.textContent = "Bloquear";
        console.log(`Linha ${index} habilitada`);
      } else {
        select.disabled = true;
        dateInput.disabled = true;
        tr.classList.remove("modified");
        btn.textContent = "Editar";

        // Reverter valores originais
        select.value = originalData[index].PGTO || "";
        dateInput.value = originalData[index].DATPGTO || "";
        tableData[index].PGTO = originalData[index].PGTO;
        tableData[index].DATPGTO = originalData[index].DATPGTO;
        console.log(`Linha ${index} revertida`);
      }
    });
  });

  // Captura alterações em tempo real
  document.querySelectorAll("select[name='PGTO'], input[name='DATPGTO']").forEach(el => {
    el.addEventListener("change", e => {
      const index = e.target.dataset.index;
      const name = e.target.name;
      const value = e.target.value;

      // Atualiza dados em memória
      tableData[index][name] = value;
      console.log(`Alteração detectada na linha ${index}: ${name} = ${value}`);
    });
  });
}



// --- Salvar alterações ---
saveButton.addEventListener("click", async () => {
  try {
    saveButton.disabled = true;
    saveButton.textContent = "Salvando...";
    alertBox.innerHTML = "";

const modifiedRows = tableData
  .filter((row, i) => row.PGTO !== originalData[i].PGTO || row.DATPGTO !== originalData[i].DATPGTO)
  .map(row => ({
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

    showAlert("Alterações salvas com sucesso!", "success");
    originalData = JSON.parse(JSON.stringify(tableData));
    renderTable();
  } catch (err) {
    console.error("Erro ao salvar:", err);
    showAlert("Erro ao salvar alterações.", "error");
  } finally {
    saveButton.disabled = false;
    saveButton.textContent = "Salvar Alterações";
  }
});

// --- Paginação ---
function setupPaginationButtons(totalPages) {
  pagination.innerHTML = "";

  const prevBtn = document.createElement("button");
  prevBtn.textContent = "Anterior";
  prevBtn.disabled = currentPage === 1;
  prevBtn.addEventListener("click", () => {
    currentPage--;
    renderTable();
  });

  const nextBtn = document.createElement("button");
  nextBtn.textContent = "Próximo";
  nextBtn.disabled = currentPage === totalPages;
  nextBtn.addEventListener("click", () => {
    currentPage++;
    renderTable();
  });

  const pageInfo = document.createElement("span");
  pageInfo.textContent = `Página ${currentPage} de ${totalPages}`;

  pagination.appendChild(prevBtn);
  pagination.appendChild(pageInfo);
  pagination.appendChild(nextBtn);
}

// --- Inicialização ---
document.addEventListener("DOMContentLoaded", loadData);
