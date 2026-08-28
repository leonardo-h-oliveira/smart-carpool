const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

let token = localStorage.getItem("sc_token");
let user = null;
let returnToOfferAfterVehicle = false;
let pendingVehicleId = null;
let ownedVehicles = [];
let editingVehicleId = null;

try {
  user = JSON.parse(localStorage.getItem("sc_user") || "null");
} catch {
  localStorage.removeItem("sc_user");
}

const statusNames = {
  pending: "Aguardando motorista",
  accepted: "Aceita",
  rejected: "Recusada",
  cancelled: "Cancelada",
  open: "Aberta",
};

const esc = (value) =>
  String(value ?? "").replace(
    /[&<>'"]/g,
    (char) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[
        char
      ],
  );

function formatPhone(value) {
  const digits = String(value || "").replace(/\D/g, "");
  if (digits.length === 11) {
    return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7)}`;
  }
  if (digits.length === 10) {
    return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`;
  }
  return value || "";
}

function clearSession() {
  token = null;
  user = null;
  localStorage.removeItem("sc_token");
  localStorage.removeItem("sc_user");
  $("#logout").classList.add("hidden");
  $("#avatar").textContent = "?";
}

function notice(message, error = false) {
  $("#notice").innerHTML = `<div class="notice ${error ? "error" : ""}">${esc(message)}</div>`;
  window.setTimeout(() => {
    $("#notice").innerHTML = "";
  }, 5000);
}

function authMessage(message = "Entre ou crie uma conta para continuar.") {
  clearSession();
  $$(".view").forEach((view) => view.classList.add("hidden"));
  $("#auth").classList.remove("hidden");
  $("#login-form").classList.remove("hidden");
  $("#register-form").classList.add("hidden");
  $("#title").textContent = "Entre para continuar";
  $$("#nav button").forEach((button) => button.classList.remove("active"));
  $(".sidebar").classList.remove("open");
  notice(message, true);
  $("#login-form input[name='email']").focus();
}

function apiErrorMessage(detail) {
  if (Array.isArray(detail)) {
    return detail
      .map((item) => String(item.msg).replace(/^Value error,\s*/, ""))
      .join(" ");
  }
  return detail || "Não foi possível concluir a operação.";
}

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (token) headers.Authorization = `Bearer ${token}`;

  let response;
  try {
    response = await fetch(`/api${path}`, { ...options, headers });
  } catch {
    throw new Error("Não foi possível conectar ao servidor. Tente novamente.");
  }

  const data = await response.json().catch(() => ({}));
  if (response.status === 401 && !path.startsWith("/auth/")) {
    authMessage("Sua sessão expirou. Entre novamente para continuar.");
    throw new Error("Sessão expirada.");
  }
  if (!response.ok) throw new Error(apiErrorMessage(data.detail));
  return data;
}

function show(view) {
  if (!token || !user) {
    authMessage();
    return;
  }

  $$(".view").forEach((item) => item.classList.add("hidden"));
  $(`#${view}`).classList.remove("hidden");
  $$("#nav button").forEach((button) =>
    button.classList.toggle("active", button.dataset.view === view),
  );

  const names = {
    home: `Olá, ${user.name.split(" ")[0]} 👋`,
    search: "Buscar carona",
    offer: "Oferecer carona",
    trips: "Minhas viagens",
    vehicle: "Meus veículos",
    profile: "Meu perfil",
  };
  $("#title").textContent = names[view] || "Smart Carpool";
  $(".sidebar").classList.remove("open");

  if (view === "search") loadRides();
  if (view === "home") loadFeatured();
  if (view === "vehicle" || view === "offer") loadVehicles();
  if (view === "trips") loadDashboard();
  if (view === "profile") loadProfile();
}

function renderRide(ride, { canBook = false, actions = "" } = {}) {
  const contact = ride.driver.phone
    ? `<div class="contact"><strong>Contato liberado</strong><br><span>${esc(formatPhone(ride.driver.phone))} · ${esc(ride.vehicle.plate)}</span></div>`
    : "";
  const bookAction = canBook
    ? `<button class="primary compact" onclick="book(${ride.id})">Solicitar vaga</button>`
    : "";

  return `<article class="ride">
    <div class="route">
      <i class="dot"></i><div><small>Origem</small><h4>${esc(ride.origin)}</h4></div>
      <i class="dot end"></i><div><small>Destino</small><h4>${esc(ride.destination)}</h4></div>
    </div>
    <footer>
      <div><strong>${esc(ride.date.split("-").reverse().join("/"))} · ${esc(ride.time)}</strong><br><small>${esc(ride.driver.name)} · ${esc(ride.vehicle.model)}</small></div>
      <div class="ride-actions"><span class="badge">${ride.seats_available} vaga(s)</span>${bookAction}${actions}</div>
    </footer>
    ${contact}
  </article>`;
}

async function loadRides(params = "") {
  try {
    const rides = await api(`/rides${params}`);
    $("#results").innerHTML = rides.length
      ? rides.map((ride) => renderRide(ride, { canBook: true })).join("")
      : '<div class="empty">Nenhuma carona encontrada.</div>';
  } catch (error) {
    notice(error.message, true);
  }
}

async function loadFeatured() {
  try {
    const rides = await api("/rides");
    $("#featured").innerHTML =
      rides
        .slice(0, 3)
        .map((ride) => renderRide(ride, { canBook: true }))
        .join("") || '<div class="empty">Ainda não há caronas abertas.</div>';
  } catch (error) {
    notice(error.message, true);
  }
}

function selectVehicle(vehicleId) {
  const selectedId = String(vehicleId);
  $("#vehicle-select").value = selectedId;
  $$("#offer-vehicle-list [data-vehicle-id]").forEach((button) => {
    button.classList.toggle("active", button.dataset.vehicleId === selectedId);
    button.setAttribute("aria-pressed", button.dataset.vehicleId === selectedId);
  });
}

function startVehicleRegistration() {
  resetVehicleForm();
  returnToOfferAfterVehicle = true;
  show("vehicle");
  notice("Cadastre o veículo. Depois você voltará para concluir a carona.");
  $("#vehicle-form input[name='model']").focus();
}

function resetVehicleForm() {
  editingVehicleId = null;
  $("#vehicle-form").reset();
  $("#vehicle-form-title").textContent = "Cadastrar novo veículo";
  $("#vehicle-form-description").textContent =
    "Informe os dados do veículo que você dirige.";
  $("#save-vehicle").textContent = "Salvar veículo";
  $("#cancel-vehicle-edit").classList.add("hidden");
}

function editVehicle(vehicleId) {
  const vehicle = ownedVehicles.find((item) => item.id === vehicleId);
  if (!vehicle) return;
  editingVehicleId = vehicle.id;
  const form = $("#vehicle-form");
  form.elements.model.value = vehicle.model;
  form.elements.color.value = vehicle.color;
  form.elements.plate.value = vehicle.plate;
  $("#vehicle-form-title").textContent = `Editar ${vehicle.model}`;
  $("#vehicle-form-description").textContent =
    "Corrija os dados e salve para atualizar todas as telas.";
  $("#save-vehicle").textContent = "Salvar alterações";
  $("#cancel-vehicle-edit").classList.remove("hidden");
  form.scrollIntoView({ behavior: "smooth", block: "start" });
  form.elements.model.focus();
}

async function removeVehicle(vehicleId) {
  const vehicle = ownedVehicles.find((item) => item.id === vehicleId);
  if (!vehicle) return;
  if (!window.confirm(`Excluir ${vehicle.model} · ${vehicle.plate}?`)) return;
  try {
    await api(`/vehicles/${vehicle.id}`, { method: "DELETE" });
    if (editingVehicleId === vehicle.id) resetVehicleForm();
    notice("Veículo excluído.");
    loadVehicles();
  } catch (error) {
    notice(error.message, true);
  }
}

async function loadVehicles() {
  try {
    const vehicles = await api("/vehicles");
    ownedVehicles = vehicles;
    $("#vehicles").innerHTML =
      vehicles
        .map(
          (vehicle) => `<article class="ride vehicle-card">
            <div class="vehicle-card-heading"><div><h4>${esc(vehicle.model)}</h4><p>${esc(vehicle.color)} · ${esc(vehicle.plate)}</p></div><span class="badge">${vehicle.can_delete ? "Disponível" : "Em uso"}</span></div>
            <div class="vehicle-card-actions">
              <button type="button" class="secondary compact" onclick="editVehicle(${vehicle.id})">Editar</button>
              ${vehicle.can_delete
                ? `<button type="button" class="danger compact" onclick="removeVehicle(${vehicle.id})">Excluir</button>`
                : '<button type="button" class="danger compact" disabled title="Há uma carona vinculada a este veículo">Vinculado a carona</button>'}
            </div>
          </article>`,
        )
        .join("") || '<div class="empty">Cadastre um veículo para oferecer caronas.</div>';
    const select = $("#vehicle-select");
    const previousVehicleId = pendingVehicleId
      ? String(pendingVehicleId)
      : select.value;
    const vehicleOptions = vehicles
      .map(
        (vehicle) =>
          `<option value="${vehicle.id}">${esc(vehicle.model)} · ${esc(vehicle.plate)}</option>`,
      )
      .join("");
    const emptyOption = vehicles.length
      ? ""
      : '<option value="" selected disabled>Você ainda não tem veículo</option>';
    select.innerHTML = `${emptyOption}${vehicleOptions}<option value="new">＋ Cadastrar novo veículo</option>`;

    $("#offer-vehicle-list").innerHTML = `${vehicles
      .map(
        (vehicle) => `<button type="button" class="vehicle-option" data-vehicle-id="${vehicle.id}" aria-pressed="false">
          <span class="vehicle-icon" aria-hidden="true">🚗</span>
          <span><strong>${esc(vehicle.model)}</strong><small>${esc(vehicle.color)} · ${esc(vehicle.plate)}</small></span>
          <span class="vehicle-check" aria-hidden="true">✓</span>
        </button>`,
      )
      .join("")}<button type="button" class="vehicle-option new" data-add-vehicle>
        <span class="vehicle-icon" aria-hidden="true">＋</span>
        <span><strong>Novo veículo</strong><small>Cadastrar outro veículo</small></span>
      </button>`;

    $$("#offer-vehicle-list [data-vehicle-id]").forEach((button) => {
      button.onclick = () => selectVehicle(button.dataset.vehicleId);
    });
    $("#offer-vehicle-list [data-add-vehicle]").onclick = startVehicleRegistration;
    select.onchange = () => {
      if (select.value === "new") {
        startVehicleRegistration();
        return;
      }
      selectVehicle(select.value);
    };

    const selectedVehicle = vehicles.find(
      (vehicle) => String(vehicle.id) === previousVehicleId,
    );
    if (selectedVehicle) {
      selectVehicle(selectedVehicle.id);
    } else if (vehicles.length) {
      selectVehicle(vehicles[0].id);
    }
    pendingVehicleId = null;

    const publishButton = $("#publish-ride");
    publishButton.disabled = vehicles.length === 0;
    publishButton.textContent = vehicles.length
      ? "Publicar carona"
      : "Cadastre um veículo para continuar";
  } catch (error) {
    notice(error.message, true);
  }
}

async function loadDashboard() {
  try {
    const dashboard = await api("/dashboard");
    const offered = dashboard.offered
      .map((ride) => {
        const actions =
          ride.status === "open"
            ? `<button class="danger compact" onclick="cancelRide(${ride.id})">Cancelar carona</button>`
            : `<span class="status status-${ride.status}">${esc(statusNames[ride.status] || ride.status)}</span>`;
        return renderRide(ride, { actions });
      })
      .join("");
    const bookings = dashboard.bookings
      .map((booking) => {
        const canCancel = ["pending", "accepted"].includes(booking.status);
        const actions = canCancel
          ? `<button class="danger compact" onclick="cancelBooking(${booking.id})">Cancelar solicitação</button>`
          : "";
        return `<div class="booking-card">${renderRide(booking.ride, { actions })}<span class="status status-${booking.status}">${esc(statusNames[booking.status] || booking.status)}</span></div>`;
      })
      .join("");
    const requests = dashboard.requests
      .map(
        (request) => `<div class="request">
          <span><strong>${esc(request.passenger)}</strong> solicitou a carona #${request.ride_id}<br><small>${esc(statusNames[request.status] || request.status)}</small></span>
          ${
            request.status === "pending"
              ? `<div class="button-row"><button class="accept" onclick="decide(${request.id},'accepted')">Aceitar</button><button class="reject" onclick="decide(${request.id},'rejected')">Recusar</button></div>`
              : `<span class="status status-${request.status}">${esc(statusNames[request.status] || request.status)}</span>`
          }
        </div>`,
      )
      .join("");

    $("#dashboard").innerHTML = `
      <div class="trip-group"><h3>Caronas que ofereci</h3><div class="cards">${offered || '<div class="empty">Você ainda não ofereceu caronas.</div>'}</div></div>
      <div class="trip-group"><h3>Minhas solicitações</h3><div class="cards">${bookings || '<div class="empty">Nenhuma solicitação.</div>'}</div></div>
      <div class="trip-group"><h3>Pedidos recebidos</h3>${requests || '<div class="empty">Nenhum pedido recebido.</div>'}</div>`;
  } catch (error) {
    notice(error.message, true);
  }
}

async function loadProfile() {
  try {
    const profile = await api("/me");
    const form = $("#profile-form");
    form.elements.name.value = profile.name;
    form.elements.email.value = profile.email;
    form.elements.university.value = profile.university;
    form.elements.phone.value = formatPhone(profile.phone);
  } catch (error) {
    notice(error.message, true);
  }
}

async function book(id) {
  try {
    await api(`/rides/${id}/book`, { method: "POST" });
    notice("Solicitação enviada. Acompanhe a resposta em Minhas viagens.");
    show("trips");
  } catch (error) {
    notice(error.message, true);
  }
}

async function decide(id, status) {
  try {
    await api(`/bookings/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
    notice(status === "accepted" ? "Passageiro aceito." : "Solicitação recusada.");
    loadDashboard();
  } catch (error) {
    notice(error.message, true);
  }
}

async function cancelBooking(id) {
  if (!window.confirm("Deseja cancelar esta solicitação?")) return;
  try {
    await api(`/bookings/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ status: "cancelled" }),
    });
    notice("Solicitação cancelada.");
    loadDashboard();
  } catch (error) {
    notice(error.message, true);
  }
}

async function cancelRide(id) {
  if (!window.confirm("Deseja cancelar esta carona? As solicitações vinculadas também serão canceladas.")) return;
  try {
    await api(`/rides/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ status: "cancelled" }),
    });
    notice("Carona e solicitações vinculadas canceladas.");
    loadDashboard();
  } catch (error) {
    notice(error.message, true);
  }
}

function loginDone(data) {
  token = data.token;
  user = data.user;
  $("#notice").innerHTML = "";
  localStorage.setItem("sc_token", token);
  localStorage.setItem("sc_user", JSON.stringify(user));
  $("#logout").classList.remove("hidden");
  $("#avatar").textContent = user.name[0].toUpperCase();
  show("home");
}

$("#login-form").onsubmit = async (event) => {
  event.preventDefault();
  try {
    const data = Object.fromEntries(new FormData(event.target));
    loginDone(await api("/auth/login", { method: "POST", body: JSON.stringify(data) }));
  } catch (error) {
    notice(error.message, true);
  }
};

$("#register-form").onsubmit = async (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.target));
  data.university = "UNIFAL-MG";
  try {
    loginDone(await api("/auth/register", { method: "POST", body: JSON.stringify(data) }));
  } catch (error) {
    notice(error.message, true);
  }
};

$("#profile-form").onsubmit = async (event) => {
  event.preventDefault();
  const button = $("#save-profile");
  const data = Object.fromEntries(new FormData(event.target));
  delete data.email;
  data.phone = data.phone.trim() || null;
  button.disabled = true;
  button.textContent = "Salvando...";
  try {
    const profile = await api("/me", {
      method: "PATCH",
      body: JSON.stringify(data),
    });
    user = { ...user, name: profile.name, email: profile.email };
    localStorage.setItem("sc_user", JSON.stringify(user));
    $("#avatar").textContent = profile.name[0].toUpperCase();
    event.target.elements.phone.value = formatPhone(profile.phone);
    notice("Dados cadastrais atualizados.");
  } catch (error) {
    notice(error.message, true);
  } finally {
    button.disabled = false;
    button.textContent = "Salvar alterações";
  }
};

$("#vehicle-form").onsubmit = async (event) => {
  event.preventDefault();
  const button = $("#save-vehicle");
  const vehicleId = editingVehicleId;
  const wasEditing = vehicleId !== null;
  button.disabled = true;
  button.textContent = "Salvando...";
  try {
    const data = Object.fromEntries(new FormData(event.target));
    const vehicle = await api(wasEditing ? `/vehicles/${vehicleId}` : "/vehicles", {
      method: wasEditing ? "PATCH" : "POST",
      body: JSON.stringify(data),
    });
    resetVehicleForm();
    if (returnToOfferAfterVehicle) {
      returnToOfferAfterVehicle = false;
      pendingVehicleId = vehicle.id;
      show("offer");
      notice(
        wasEditing
          ? "Veículo atualizado e selecionado. Agora conclua a carona."
          : "Veículo cadastrado e selecionado. Agora conclua a carona.",
      );
    } else {
      notice(wasEditing ? "Veículo atualizado." : "Veículo cadastrado.");
      loadVehicles();
    }
  } catch (error) {
    notice(error.message, true);
  } finally {
    button.disabled = false;
    button.textContent = editingVehicleId === null ? "Salvar veículo" : "Salvar alterações";
  }
};

$("#cancel-vehicle-edit").onclick = resetVehicleForm;

$("#ride-form").onsubmit = async (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.target));
  if (!data.vehicle_id || data.vehicle_id === "new") {
    notice("Cadastre ou escolha um veículo antes de publicar a carona.", true);
    startVehicleRegistration();
    return;
  }
  data.vehicle_id = Number(data.vehicle_id);
  data.seats = Number(data.seats);
  try {
    await api("/rides", { method: "POST", body: JSON.stringify(data) });
    event.target.reset();
    notice("Carona publicada.");
    show("trips");
  } catch (error) {
    notice(error.message, true);
  }
};

$("#search-form").onsubmit = (event) => {
  event.preventDefault();
  const query = new URLSearchParams(
    [...new FormData(event.target)].filter(([, value]) => value),
  );
  loadRides(`?${query}`);
};

$("#show-register").onclick = () => {
  $("#login-form").classList.add("hidden");
  $("#register-form").classList.remove("hidden");
};
$("#show-login").onclick = () => {
  $("#register-form").classList.add("hidden");
  $("#login-form").classList.remove("hidden");
};

$$('[data-view]').forEach((button) => {
  button.onclick = () => {
    returnToOfferAfterVehicle = false;
    if (button.dataset.view === "vehicle") resetVehicleForm();
    show(button.dataset.view);
  };
});
$$('[data-go]').forEach((button) => {
  button.onclick = () => {
    returnToOfferAfterVehicle = false;
    show(button.dataset.go);
  };
});
$(".brand").onclick = (event) => {
  event.preventDefault();
  returnToOfferAfterVehicle = false;
  show("home");
};
$("#menu").onclick = () => $(".sidebar").classList.toggle("open");
$("#logout").onclick = () => {
  clearSession();
  authMessage("Você saiu da sua conta.");
};

$("#ride-form input[name='ride_date']").min = new Date().toISOString().split("T")[0];

if (token && user) {
  $("#logout").classList.remove("hidden");
  $("#avatar").textContent = user.name[0].toUpperCase();
  show("home");
} else {
  clearSession();
}
