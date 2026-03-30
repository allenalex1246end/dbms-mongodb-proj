const saleForm = document.getElementById("sale-form");
const saleIdInput = document.getElementById("sale-id");
const productInput = document.getElementById("product");
const quantityInput = document.getElementById("quantity");
const priceInput = document.getElementById("price");
const submitBtn = document.getElementById("submit-btn");
const cancelBtn = document.getElementById("cancel-btn");
const refreshBtn = document.getElementById("refresh-btn");
const salesBody = document.getElementById("sales-body");
const productSummaryBody = document.getElementById("product-summary-body");
const dailySummaryBody = document.getElementById("daily-summary-body");
const formTitle = document.getElementById("form-title");
const statusMessage = document.getElementById("status-message");

let cachedSales = [];

function setStatus(message, type = "") {
    statusMessage.textContent = message;
    statusMessage.classList.remove("error", "success");
    if (type) {
        statusMessage.classList.add(type);
    }
}

function money(value) {
    return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
    }).format(value);
}

function formatDate(iso) {
    if (!iso) {
        return "-";
    }
    const date = new Date(iso);
    return `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
}

function formatDay(iso) {
    if (!iso) {
        return "-";
    }
    return new Date(iso).toLocaleDateString();
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function resetForm() {
    saleIdInput.value = "";
    saleForm.reset();
    formTitle.textContent = "Add Sale";
    submitBtn.textContent = "Create Sale";
    cancelBtn.classList.add("hidden");
}

function beginEdit(sale) {
    saleIdInput.value = sale.id;
    productInput.value = sale.product;
    quantityInput.value = sale.quantity;
    priceInput.value = sale.price;

    formTitle.textContent = "Edit Sale";
    submitBtn.textContent = "Update Sale";
    cancelBtn.classList.remove("hidden");
    productInput.focus();
}

function renderSales(sales) {
    salesBody.innerHTML = "";

    if (!sales.length) {
        salesBody.innerHTML = '<tr class="empty-row"><td colspan="6">No sales yet. Add your first entry above.</td></tr>';
        return;
    }

    for (const sale of sales) {
        const row = document.createElement("tr");
        const product = escapeHtml(sale.product);
        row.innerHTML = `
            <td>${product}</td>
      <td>${sale.quantity}</td>
      <td>${money(sale.price)}</td>
      <td>${money(sale.total)}</td>
      <td>${formatDate(sale.created_at)}</td>
      <td>
        <div class="inline-actions">
          <button class="secondary" data-action="edit" data-id="${sale.id}">Edit</button>
          <button class="danger" data-action="delete" data-id="${sale.id}">Delete</button>
        </div>
      </td>
    `;
        salesBody.appendChild(row);
    }
}

function buildProductSummary(sales) {
    const grouped = new Map();

    for (const sale of sales) {
        const key = String(sale.product || "").trim().toLowerCase();
        if (!key) {
            continue;
        }

        if (!grouped.has(key)) {
            grouped.set(key, {
                name: String(sale.product).trim(),
                units: 0,
                revenue: 0,
            });
        }

        const item = grouped.get(key);
        item.units += Number(sale.quantity) || 0;
        item.revenue += Number(sale.total) || 0;
    }

    return Array.from(grouped.values()).sort((a, b) => b.revenue - a.revenue);
}

function buildDailySummary(sales) {
    const grouped = new Map();

    for (const sale of sales) {
        const dateKey = sale.created_at ? new Date(sale.created_at).toISOString().slice(0, 10) : "unknown";
        if (!grouped.has(dateKey)) {
            grouped.set(dateKey, {
                dateKey,
                transactions: 0,
                units: 0,
                revenue: 0,
            });
        }

        const item = grouped.get(dateKey);
        item.transactions += 1;
        item.units += Number(sale.quantity) || 0;
        item.revenue += Number(sale.total) || 0;
    }

    return Array.from(grouped.values()).sort((a, b) => b.dateKey.localeCompare(a.dateKey));
}

function renderProductSummary(rows) {
    productSummaryBody.innerHTML = "";

    if (!rows.length) {
        productSummaryBody.innerHTML = '<tr class="empty-row"><td colspan="4">No product summary available.</td></tr>';
        return;
    }

    for (const rowData of rows) {
        const row = document.createElement("tr");
        const avgPrice = rowData.units > 0 ? rowData.revenue / rowData.units : 0;
        row.innerHTML = `
      <td>${escapeHtml(rowData.name)}</td>
      <td>${rowData.units}</td>
      <td>${money(rowData.revenue)}</td>
      <td>${money(avgPrice)}</td>
    `;
        productSummaryBody.appendChild(row);
    }
}

function renderDailySummary(rows) {
    dailySummaryBody.innerHTML = "";

    if (!rows.length) {
        dailySummaryBody.innerHTML = '<tr class="empty-row"><td colspan="4">No daily summary available.</td></tr>';
        return;
    }

    for (const rowData of rows) {
        const row = document.createElement("tr");
        row.innerHTML = `
      <td>${formatDay(rowData.dateKey)}</td>
      <td>${rowData.transactions}</td>
      <td>${rowData.units}</td>
      <td>${money(rowData.revenue)}</td>
    `;
        dailySummaryBody.appendChild(row);
    }
}

function renderAllTables(sales) {
    renderSales(sales);
    renderProductSummary(buildProductSummary(sales));
    renderDailySummary(buildDailySummary(sales));
}

async function loadSales() {
    try {
        const response = await fetch("/api/sales");
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Could not load sales.");
        }

        cachedSales = data;
        renderAllTables(cachedSales);
    } catch (error) {
        setStatus(error.message, "error");
    }
}

async function saveSale(event) {
    event.preventDefault();
    setStatus("");

    const payload = {
        product: productInput.value.trim(),
        quantity: Number(quantityInput.value),
        price: Number(priceInput.value),
    };

    const id = saleIdInput.value;
    const endpoint = id ? `/api/sales/${id}` : "/api/sales";
    const method = id ? "PUT" : "POST";

    try {
        const response = await fetch(endpoint, {
            method,
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || "Could not save sale.");
        }

        setStatus(data.message || "Saved.", "success");
        resetForm();
        await loadSales();
    } catch (error) {
        setStatus(error.message, "error");
    }
}

async function deleteSale(id) {
    const confirmed = window.confirm("Delete this sale?");
    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch(`/api/sales/${id}`, { method: "DELETE" });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Could not delete sale.");
        }

        setStatus(data.message || "Deleted.", "success");
        if (saleIdInput.value === id) {
            resetForm();
        }
        await loadSales();
    } catch (error) {
        setStatus(error.message, "error");
    }
}

async function handleTableClick(event) {
    const button = event.target.closest("button");
    if (!button) {
        return;
    }

    const action = button.dataset.action;
    const id = button.dataset.id;
    if (!action || !id) {
        return;
    }

    if (action === "delete") {
        await deleteSale(id);
        return;
    }

    if (action === "edit") {
        try {
            const selected = cachedSales.find((item) => item.id === id);
            if (!selected) {
                throw new Error("Sale not found.");
            }
            beginEdit(selected);
            setStatus("Editing selected sale.", "success");
        } catch (error) {
            setStatus(error.message, "error");
        }
    }
}

saleForm.addEventListener("submit", saveSale);
cancelBtn.addEventListener("click", () => {
    resetForm();
    setStatus("Edit canceled.");
});
refreshBtn.addEventListener("click", () => {
    setStatus("");
    loadSales();
});
salesBody.addEventListener("click", handleTableClick);

loadSales();
