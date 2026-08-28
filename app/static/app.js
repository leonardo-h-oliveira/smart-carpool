const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

let token = localStorage.getItem("sc_token");
let user = null;

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
    return detail.map((item) => item.msg).join(" ");
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
    vehicle: "Meu veículo",
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
    ? `<div class="contact"><strong>Contato liberado</strong><br><span>${esc(ride.driver.phone)} · ${esc(ride.vehicle.plate)}</span></div>`
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

async function loadVehicles() {
  try {
    const vehicles = await api("/vehicles");
    $("#vehicles").innerHTML =
      vehicles
        .map(
          (vehicle) =>
            `<article class="ride"><h4>${esc(vehicle.model)}</h4><p>${esc(vehicle.color)} · ${esc(vehicle.plate)}</p></article>`,
        )
        .join("") || '<div class="empty">Cadastre um veículo para oferecer caronas.</div>';
    $("#vehicle-select").innerHTML = vehicles.length
      ? vehicles
          .map(
            (vehicle) =>
              `<option value="${vehicle.id}">${esc(vehicle.model)} · ${esc(vehicle.plate)}</option>`,
          )
          .join("")
      : '<option value="">Cadastre um veículo primeiro</option>';
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
    $("#profile-card").innerHTML = `
      <div class="profile-row"><span>Nome</span><strong>${esc(profile.name)}</strong></div>
      <div class="profile-row"><span>E-mail</span><strong>${esc(profile.email)}</strong></div>
      <div class="profile-row"><span>Universidade</span><strong>${esc(profile.university)}</strong></div>
      <div class="profile-row"><span>Telefone</span><strong>${esc(profile.phone || "Não informado")}</strong></div>`;
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

$("#vehicle-form").onsubmit = async (event) => {
  event.preventDefault();
  try {
    const data = Object.fromEntries(new FormData(event.target));
    await api("/vehicles", { method: "POST", body: JSON.stringify(data) });
    event.target.reset();
    notice("Veículo cadastrado.");
    loadVehicles();
  } catch (error) {
    notice(error.message, true);
  }
};

$("#ride-form").onsubmit = async (event) => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.target));
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
  button.onclick = () => show(button.dataset.view);
});
$$('[data-go]').forEach((button) => {
  button.onclick = () => show(button.dataset.go);
});
$(".brand").onclick = (event) => {
  event.preventDefault();
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
