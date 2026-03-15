// ========================================
// Configuration & State
// ========================================
const CONFIG = {
  maxHistoryItems: 10,
  maxFavorites: 50,
  currentView: "grid",
};

let state = {
  searchHistory: JSON.parse(localStorage.getItem("searchHistory") || "[]"),
  favorites: JSON.parse(localStorage.getItem("favorites") || "[]"),
  currentTheme: localStorage.getItem("theme") || "dark",
  lastSearchQuery: "",
  lastProjectObjective: "",
  currentResults: [],
};

// ========================================
// DOM Elements
// ========================================
const form = document.getElementById("search-form");
const projectObjectiveInput = document.getElementById("project-objective");
const searchInput = document.getElementById("search-input");
const searchButton = document.getElementById("search-button");
const searchButtonText = document.getElementById("search-button-text");
const clearButton = document.getElementById("clear-button");
const loadingState = document.getElementById("loading-state");
const statusMessage = document.getElementById("status-message");
const resultsGrid = document.getElementById("results-grid");
const resultsCount = document.getElementById("results-count");
const resultsTitle = document.getElementById("results-title");
const emptyState = document.getElementById("empty-state");

// Filters
const sourceFilter = document.getElementById("source-filter");
const sortFilter = document.getElementById("sort-filter");
const limitFilter = document.getElementById("limit-filter");

// Theme & Sidebar
const themeToggle = document.getElementById("theme-toggle");
const historyToggle = document.getElementById("history-toggle");
const favoritesToggle = document.getElementById("favorites-toggle");
const historySidebar = document.getElementById("history-sidebar");
const favoritesSidebar = document.getElementById("favorites-sidebar");
const historyClose = document.getElementById("history-close");
const favoritesClose = document.getElementById("favorites-close");
const sidebarOverlay = document.getElementById("sidebar-overlay");
const favoritesBadge = document.getElementById("favorites-badge");

// Modal
const detailModal = document.getElementById("detail-modal");
const modalClose = document.getElementById("modal-close");
const modalContent = document.getElementById("modal-content");

// View Toggle
const viewToggleBtns = document.querySelectorAll(".view-toggle-btn");

// ========================================
// Initialization
// ========================================
function init() {
  initTheme();
  initEventListeners();
  updateFavoritesBadge();
  renderSearchHistory();
  renderFavorites();
}

// ========================================
// Theme Management
// ========================================
function initTheme() {
  document.documentElement.setAttribute("data-theme", state.currentTheme);
  document.body.setAttribute("data-theme", state.currentTheme);
  updateThemeIcon();
}

function updateThemeIcon() {
  const isDark = state.currentTheme === "dark";
  themeToggle.innerHTML = isDark ? '<i class="fas fa-sun w-5 h-5"></i>' : '<i class="fas fa-moon w-5 h-5"></i>';
}

function toggleTheme() {
  state.currentTheme = state.currentTheme === "dark" ? "light" : "dark";
  localStorage.setItem("theme", state.currentTheme);
  initTheme();
}

// ========================================
// Search History Management
// ========================================
function addToSearchHistory(query, objective) {
  const item = {
    id: Date.now(),
    query,
    objective,
    timestamp: new Date().toLocaleString(),
  };

  state.searchHistory = [item, ...state.searchHistory.filter((h) => h.query !== query)].slice(0, CONFIG.maxHistoryItems);
  localStorage.setItem("searchHistory", JSON.stringify(state.searchHistory));
  renderSearchHistory();
}

function renderSearchHistory() {
  const historyList = document.getElementById("history-list");
  const historyEmpty = document.getElementById("history-empty");

  if (state.searchHistory.length === 0) {
    historyList.innerHTML = "";
    historyEmpty.style.display = "block";
    return;
  }

  historyEmpty.style.display = "none";
  historyList.innerHTML = state.searchHistory
    .map(
      (item) => `
    <button type="button" class="search-history-item w-full text-left transition-all hover:translate-x-1" data-query="${escapeHtml(item.query)}" data-objective="${escapeHtml(item.objective)}">
      <div class="font-medium text-white">${escapeHtml(item.query)}</div>
      <div class="text-xs text-slate-500 mt-1">${item.timestamp}</div>
      ${item.objective ? `<div class="text-xs text-gold-400 mt-1">Objective: ${escapeHtml(item.objective.substring(0, 50))}...</div>` : ""}
    </button>
  `
    )
    .join("");

  // Add click handlers
  document.querySelectorAll(".search-history-item").forEach((btn) => {
    btn.addEventListener("click", () => {
      searchInput.value = btn.dataset.query;
      projectObjectiveInput.value = btn.dataset.objective;
      closeSidebars();
      form.dispatchEvent(new Event("submit"));
    });
  });
}

// ========================================
// Favorites Management
// ========================================
function toggleFavorite(datasetId) {
  const dataset = state.currentResults.find((d) => d.id === datasetId);
  if (!dataset) return;

  const index = state.favorites.findIndex((f) => f.id === datasetId);
  if (index > -1) {
    state.favorites.splice(index, 1);
  } else {
    if (state.favorites.length < CONFIG.maxFavorites) {
      state.favorites.push({
        ...dataset,
        addedAt: new Date().toISOString(),
      });
    } else {
      alert("Maximum favorites reached!");
      return;
    }
  }

  localStorage.setItem("favorites", JSON.stringify(state.favorites));
  updateFavoritesBadge();
  renderFavorites();
  // Update heart icon
  updateFavoriteIcons();
}

function updateFavoriteIcons() {
  document.querySelectorAll(".favorite-btn").forEach((btn) => {
    const datasetId = btn.dataset.datasetId;
    const isFavorited = state.favorites.some((f) => f.id === datasetId);
    btn.classList.toggle("text-gold-400", isFavorited);
    btn.classList.toggle("text-slate-400", !isFavorited);
    btn.innerHTML = isFavorited ? '<i class="fas fa-heart w-5 h-5"></i>' : '<i class="far fa-heart w-5 h-5"></i>';
  });
}

function updateFavoritesBadge() {
  const count = state.favorites.length;
  if (count > 0) {
    favoritesBadge.textContent = count;
    favoritesBadge.classList.remove("hidden");
  } else {
    favoritesBadge.classList.add("hidden");
  }
}

function renderFavorites() {
  const favoritesList = document.getElementById("favorites-list");
  const favoritesEmpty = document.getElementById("favorites-empty");

  if (state.favorites.length === 0) {
    favoritesList.innerHTML = "";
    favoritesEmpty.style.display = "block";
    return;
  }

  favoritesEmpty.style.display = "none";
  favoritesList.innerHTML = state.favorites
    .map(
      (dataset) => `
    <div class="favorite-item">
      <div class="favorite-item-title truncate">${escapeHtml(dataset.name)}</div>
      <div class="favorite-item-source">${escapeHtml(formatSource(dataset.source))}</div>
      <div class="flex gap-2 mt-3">
        <button type="button" class="flex-1 text-xs px-2 py-1.5 bg-gold-400/20 hover:bg-gold-400/30 text-gold-400 rounded transition" onclick="openDetailModal('${dataset.id}')">View</button>
        <button type="button" class="text-xs px-2 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded transition" onclick="removeFavorite('${dataset.id}')">Remove</button>
      </div>
    </div>
  `
    )
    .join("");
}

function removeFavorite(datasetId) {
  state.favorites = state.favorites.filter((f) => f.id !== datasetId);
  localStorage.setItem("favorites", JSON.stringify(state.favorites));
  updateFavoritesBadge();
  renderFavorites();
  updateFavoriteIcons();
}

// ========================================
// Event Listeners
// ========================================
function initEventListeners() {
  // Search
  form.addEventListener("submit", handleSearch);
  clearButton.addEventListener("click", () => {
    searchInput.value = "";
    projectObjectiveInput.value = "";
    resultsGrid.innerHTML = "";
    resultsCount.textContent = "";
    resultsTitle.textContent = "Search Results";
  });

  // Theme
  themeToggle.addEventListener("click", toggleTheme);

  // Sidebars
  historyToggle.addEventListener("click", () => toggleSidebar(historySidebar));
  favoritesToggle.addEventListener("click", () => toggleSidebar(favoritesSidebar));
  historyClose.addEventListener("click", closeSidebars);
  favoritesClose.addEventListener("click", closeSidebars);
  sidebarOverlay.addEventListener("click", closeSidebars);

  // Modal
  modalClose.addEventListener("click", closeDetailModal);
  detailModal.addEventListener("click", (e) => {
    if (e.target === detailModal) closeDetailModal();
  });

  // View Toggle
  viewToggleBtns.forEach((btn) => {
    btn.addEventListener("click", (e) => {
      viewToggleBtns.forEach((b) => b.classList.remove("active", "bg-gold-400/20", "text-white"));
      viewToggleBtns.forEach((b) => b.classList.add("text-slate-400"));
      btn.classList.add("active", "bg-gold-400/20", "text-white");
      CONFIG.currentView = btn.dataset.view;
      renderResults(state.currentResults);
    });
  });
}

function toggleSidebar(sidebar) {
  const isOpen = sidebar.classList.contains("translate-x-full") === false;
  if (isOpen) {
    closeSidebars();
  } else {
    document.querySelectorAll("#history-sidebar, #favorites-sidebar").forEach((s) => {
      s.classList.add("translate-x-full");
    });
    sidebar.classList.remove("translate-x-full");
    sidebarOverlay.classList.add("visible");
  }
}

function closeSidebars() {
  historySidebar.classList.add("translate-x-full");
  favoritesSidebar.classList.add("translate-x-full");
  sidebarOverlay.classList.remove("visible");
}

// ========================================
// Search Functionality
// ========================================
async function handleSearch(event) {
  event.preventDefault();

  const query = searchInput.value.trim();
  const objective = projectObjectiveInput.value.trim();

  if (!query) {
    setStatus("Please enter search keywords", "error");
    searchInput.focus();
    return;
  }

  state.lastSearchQuery = query;
  state.lastProjectObjective = objective;

  addToSearchHistory(query, objective);
  setLoading(true);
  setStatus("");
  resultsGrid.innerHTML = "";

  try {
    const results = await searchDatasets(query);
    state.currentResults = results.results || [];
    renderResults(state.currentResults);
  } catch (error) {
    setStatus(error.message || "Search failed. Please try again.", "error");
    resultsGrid.innerHTML = "";
  } finally {
    setLoading(false);
  }
}

async function searchDatasets(query) {
  const url = new URL("/search", window.location.origin);
  url.searchParams.set("q", query);

  const limit = parseInt(limitFilter.value) || 10;
  url.searchParams.set("limit", limit);

  const headers = {};
  const apiKey = window.DATAFINDER_CONFIG?.apiKey;
  if (apiKey) {
    headers.Authorization = `Bearer ${apiKey}`;
  }

  const response = await fetch(url.toString(), {
    method: "GET",
    headers,
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    const detail = typeof payload.detail === "string" ? payload.detail : "Failed to fetch results";
    throw new Error(detail);
  }

  return await response.json();
}

// ========================================
// Results Rendering
// ========================================
function renderResults(results) {
  if (!results || results.length === 0) {
    resultsCount.textContent = "0 datasets";
    resultsTitle.textContent = "No Results";
    emptyState.classList.remove("hidden");
    resultsGrid.innerHTML = "";
    return;
  }

  emptyState.classList.add("hidden");
  resultsCount.textContent = `${results.length} dataset${results.length === 1 ? "" : "s"} found`;
  resultsTitle.textContent = `Results (${results.length})`;

  // Apply filters
  let filtered = [...results];

  const sourceValue = sourceFilter.value;
  if (sourceValue) {
    filtered = filtered.filter((d) => formatSource(d.source).toLowerCase() === sourceValue);
  }

  const sortValue = sortFilter.value;
  if (sortValue === "newest") {
    filtered.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
  } else if (sortValue === "popularity") {
    filtered.sort((a, b) => (b.popularity || 0) - (a.popularity || 0));
  }

  // Render
  if (CONFIG.currentView === "grid") {
    resultsGrid.className = "grid gap-6 md:grid-cols-2 lg:grid-cols-3";
    resultsGrid.innerHTML = filtered.map((dataset) => createDatasetCard(dataset)).join("");
  } else {
    resultsGrid.className = "space-y-4";
    resultsGrid.innerHTML = filtered.map((dataset) => createDatasetListItem(dataset)).join("");
  }

  // Add event listeners
  document.querySelectorAll(".result-card").forEach((card) => {
    card.addEventListener("click", (e) => {
      if (!e.target.closest("button")) {
        openDetailModal(card.dataset.datasetId);
      }
    });
  });

  updateFavoriteIcons();
}

function createDatasetCard(dataset) {
  const tags = (dataset.tags || []).slice(0, 3);
  const isFavorited = state.favorites.some((f) => f.id === dataset.id);

  return `
    <article class="result-card cursor-pointer group" data-dataset-id="${dataset.id}">
      <div class="result-card-header">
        <div>
          <div class="result-card-source-badge">
            <i class="fas fa-database mr-2"></i>
            ${escapeHtml(formatSource(dataset.source))}
          </div>
          <h3 class="result-card-title mt-3">${escapeHtml(dataset.name)}</h3>
        </div>
        <div class="result-card-score">
          <i class="fas fa-star text-gold-300"></i>
          ${formatScore(dataset.score)}
        </div>
      </div>

      <p class="result-card-description">${escapeHtml(dataset.description || "No description available")}</p>

      ${tags.length > 0 ? `<div class="result-card-tags">${tags.map((tag) => `<span class="result-card-tag">#${escapeHtml(tag)}</span>`).join("")}</div>` : ""}

      <div class="result-card-footer">
        <button type="button" class="result-card-btn result-card-btn-primary" onclick="window.open('${escapeHtml(dataset.url)}', '_blank')">
          <i class="fas fa-external-link-alt mr-2"></i>View Dataset
        </button>
        <button type="button" class="result-card-btn result-card-btn-secondary favorite-btn" data-dataset-id="${dataset.id}" onclick="event.stopPropagation(); toggleFavorite('${dataset.id}')">
          <i class="fas ${isFavorited ? "fa-heart" : "fa-heart"} text-gold-400" style="color: ${isFavorited ? "#fcd34d" : "inherit"}"></i>
        </button>
      </div>
    </article>
  `;
}

function createDatasetListItem(dataset) {
  const isFavorited = state.favorites.some((f) => f.id === dataset.id);

  return `
    <div class="result-card cursor-pointer" data-dataset-id="${dataset.id}">
      <div class="flex items-start justify-between gap-4">
        <div class="flex-1">
          <div class="flex items-center gap-3 mb-2">
            <span class="result-card-source-badge"><i class="fas fa-database mr-1"></i>${escapeHtml(formatSource(dataset.source))}</span>
            <span class="result-card-score"><i class="fas fa-star text-gold-300"></i>${formatScore(dataset.score)}</span>
          </div>
          <h3 class="result-card-title">${escapeHtml(dataset.name)}</h3>
          <p class="result-card-description text-sm">${escapeHtml(dataset.description || "No description")}</p>
        </div>
        <button type="button" class="favorite-btn" data-dataset-id="${dataset.id}" onclick="event.stopPropagation(); toggleFavorite('${dataset.id}')" style="color: ${isFavorited ? "#fcd34d" : "inherit"}">
          <i class="fas ${isFavorited ? "fa-heart" : "fa-heart"} w-5 h-5"></i>
        </button>
      </div>
      <div class="flex gap-3 mt-4">
        <button type="button" class="result-card-btn result-card-btn-primary flex-1" onclick="window.open('${escapeHtml(dataset.url)}', '_blank')">
          <i class="fas fa-external-link-alt mr-2"></i>Open Dataset
        </button>
        <button type="button" class="result-card-btn result-card-btn-secondary" onclick="event.stopPropagation(); openDetailModal('${dataset.id}')">Details</button>
      </div>
    </div>
  `;
}

// ========================================
// Detail Modal
// ========================================
function openDetailModal(datasetId) {
  const dataset = state.currentResults.find((d) => d.id === datasetId);
  if (!dataset) return;

  const tags = (dataset.tags || []).slice(0, 10);
  const isFavorited = state.favorites.some((f) => f.id === datasetId);

  modalContent.innerHTML = `
    <div class="mb-6">
      <div class="flex items-start justify-between gap-4 mb-4">
        <div>
          <div class="result-card-source-badge mb-3">
            <i class="fas fa-database mr-2"></i>
            ${escapeHtml(formatSource(dataset.source))}
          </div>
          <h2 class="text-2xl font-bold text-white">${escapeHtml(dataset.name)}</h2>
        </div>
        <div class="result-card-score text-base">
          <i class="fas fa-star text-gold-300"></i>
          ${formatScore(dataset.score)}
        </div>
      </div>

      <p class="text-slate-200 leading-relaxed mb-6">${escapeHtml(dataset.description || "No description available")}</p>

      ${tags.length > 0 ? `<div class="result-card-tags mb-6">${tags.map((tag) => `<span class="result-card-tag">#${escapeHtml(tag)}</span>`).join("")}</div>` : ""}

      <div class="grid grid-cols-2 gap-4 mb-6 p-4 bg-slate-900/50 rounded-lg border border-slate-700">
        <div>
          <p class="text-xs text-slate-400 uppercase tracking-wide mb-1">Source</p>
          <p class="text-white font-semibold">${escapeHtml(formatSource(dataset.source))}</p>
        </div>
        <div>
          <p class="text-xs text-slate-400 uppercase tracking-wide mb-1">Relevance Score</p>
          <p class="text-gold-400 font-semibold">${formatScore(dataset.score)}</p>
        </div>
        ${dataset.size ? `<div><p class="text-xs text-slate-400 uppercase tracking-wide mb-1">Size</p><p class="text-white font-semibold">${escapeHtml(dataset.size)}</p></div>` : ""}
        ${dataset.records ? `<div><p class="text-xs text-slate-400 uppercase tracking-wide mb-1">Records</p><p class="text-white font-semibold">${dataset.records.toLocaleString()}</p></div>` : ""}
      </div>

      <div class="flex gap-3">
        <a href="${escapeHtml(dataset.url)}" target="_blank" rel="noopener noreferrer" class="flex-1 px-4 py-3 bg-gradient-to-r from-gold-400 to-gold-500 hover:from-gold-300 hover:to-gold-400 text-slate-900 font-bold rounded-lg transition transform hover:scale-105 flex items-center justify-center gap-2">
          <i class="fas fa-external-link-alt"></i>Go to Dataset
        </a>
        <button type="button" class="px-4 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition favorite-btn" data-dataset-id="${datasetId}" onclick="toggleFavorite('${datasetId}'); openDetailModal('${datasetId}')">
          <i class="fas ${isFavorited ? "fa-heart" : "fa-heart"}"></i>
        </button>
      </div>
    </div>
  `;

  detailModal.classList.remove("hidden");
}

function closeDetailModal() {
  detailModal.classList.add("hidden");
}

// ========================================
// Utilities
// ========================================
function setLoading(isLoading) {
  loadingState.classList.toggle("hidden", !isLoading);
  loadingState.classList.toggle("flex", isLoading);
  searchButton.disabled = isLoading;
  searchButtonText.textContent = isLoading ? "Searching..." : "Discover Datasets";
}

function setStatus(message = "", type = "info") {
  if (!message) {
    statusMessage.classList.add("hidden");
    return;
  }

  statusMessage.textContent = message;
  statusMessage.classList.remove("hidden", "text-emerald-200", "border-emerald-400/30", "bg-emerald-500/10", "text-rose-200", "border-rose-400/30", "bg-rose-500/10");

  if (type === "error") {
    statusMessage.classList.add("text-rose-200", "border-rose-400/30", "bg-rose-500/10");
  } else if (type === "success") {
    statusMessage.classList.add("text-emerald-200", "border-emerald-400/30", "bg-emerald-500/10");
  }
}

function formatSource(source) {
  const label = String(source || "").trim().toLowerCase();
  const sourceMap = {
    kaggle: "Kaggle",
    uci: "UCI",
    huggingface: "Hugging Face",
  };
  return sourceMap[label] || (label ? label.charAt(0).toUpperCase() + label.slice(1) : "Unknown");
}

function formatScore(score) {
  if (typeof score !== "number" || Number.isNaN(score)) return "N/A";
  return `${(score * 100).toFixed(1)}%`;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

// ========================================
// Initialize
// ========================================
init();
