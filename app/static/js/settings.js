const providerSelect = document.getElementById("providerSelect");
const modelSelect = document.getElementById("modelSelect");
const customModelInput = document.getElementById("customModelInput");
const modelHint = document.getElementById("modelHint");
const ollamaBaseUrl = document.getElementById("ollamaBaseUrl");
const temperatureInput = document.getElementById("temperature");
const settingsForm = document.getElementById("settingsForm");
const status = document.getElementById("status");

const apiProviderLabel = document.getElementById("apiProviderLabel");
const apiKeyState = document.getElementById("apiKeyState");
const providerApiKeyInput = document.getElementById("providerApiKeyInput");
const saveApiKeyBtn = document.getElementById("saveApiKeyBtn");
const removeApiKeyBtn = document.getElementById("removeApiKeyBtn");

let settingsCache = null;

function setStatus(text, isError = false) {
  status.textContent = text;
  status.style.color = isError ? "#c62828" : "#5f6b7a";
}

async function fetchSettings() {
  const res = await fetch("/api/settings");
  if (!res.ok) throw new Error("Failed to load settings");
  return res.json();
}

async function fetchProviderModels(provider) {
  const baseUrl = ollamaBaseUrl.value.trim();
  const query = baseUrl ? `?base_url=${encodeURIComponent(baseUrl)}` : "";
  try {
    const res = await fetch(`/api/settings/provider-models/${provider}${query}`);
    if (!res.ok) return [];
    const payload = await res.json();
    return Array.isArray(payload.models) ? payload.models : [];
  } catch {
    return [];
  }
}

function populateProviderOptions(providers, selected) {
  providerSelect.innerHTML = "";
  providers.forEach((provider) => {
    const option = document.createElement("option");
    option.value = provider;
    option.textContent = provider;
    if (provider === selected) option.selected = true;
    providerSelect.appendChild(option);
  });
}

function setCustomModelVisibility(show, value = "") {
  customModelInput.style.display = show ? "block" : "none";
  customModelInput.required = show;
  if (show) customModelInput.value = value;
  if (!show) customModelInput.value = "";
}

function buildModelOptions(models, selectedModel) {
  modelSelect.innerHTML = "";

  models.forEach((model) => {
    const option = document.createElement("option");
    option.value = model;
    option.textContent = model;
    modelSelect.appendChild(option);
  });

  const customOption = document.createElement("option");
  customOption.value = "__custom__";
  customOption.textContent = "Custom model";
  modelSelect.appendChild(customOption);

  if (models.includes(selectedModel)) {
    modelSelect.value = selectedModel;
    setCustomModelVisibility(false);
  } else {
    modelSelect.value = "__custom__";
    setCustomModelVisibility(true, selectedModel);
  }
}

async function refreshModelOptions(provider, selectedModel = "") {
  if (!settingsCache) return;

  const defaultModel = settingsCache.default_models[provider] || "";
  modelHint.textContent = `Default for ${provider}: ${defaultModel || "custom"}`;

  let models = await fetchProviderModels(provider);
  if (!models.length) {
    models = settingsCache.model_catalog[provider] || [];
  }

  if (!models.length && defaultModel) {
    models = [defaultModel];
  }

  models = Array.from(new Set(models));
  const current = selectedModel || defaultModel;
  buildModelOptions(models, current);
}

function getSelectedModel() {
  if (modelSelect.value === "__custom__") {
    return customModelInput.value.trim();
  }
  return modelSelect.value;
}

function updateApiKeySection(provider) {
  apiProviderLabel.textContent = `Provider: ${provider.toUpperCase()}`;

  if (provider === "ollama") {
    apiKeyState.className = "api-status";
    apiKeyState.textContent = "API key not required for Ollama.";
    providerApiKeyInput.value = "";
    providerApiKeyInput.disabled = true;
    saveApiKeyBtn.disabled = true;
    removeApiKeyBtn.disabled = true;
    return;
  }

  const hasKey = !!settingsCache?.api_key_status?.[provider];
  apiKeyState.className = `api-status ${hasKey ? "ok" : "missing"}`;
  apiKeyState.textContent = hasKey ? "API key saved." : "API key missing.";
  providerApiKeyInput.placeholder = `Enter ${provider} API key`;
  providerApiKeyInput.disabled = false;
  saveApiKeyBtn.disabled = false;
  removeApiKeyBtn.disabled = false;
}

async function applySettings(settings) {
  settingsCache = settings;
  populateProviderOptions(settings.available_providers, settings.provider);
  ollamaBaseUrl.value = settings.ollama_base_url;
  temperatureInput.value = String(settings.temperature);

  await refreshModelOptions(settings.provider, settings.model);
  updateApiKeySection(settings.provider);
}

providerSelect.addEventListener("change", async () => {
  if (!settingsCache) return;

  const provider = providerSelect.value;
  await refreshModelOptions(provider);
  updateApiKeySection(provider);

  if (provider === "ollama") {
    setStatus("Using local Ollama. API key is not required.");
    return;
  }

  if (!settingsCache.api_key_status[provider]) {
    setStatus(`Set one ${provider} API key to use all ${provider} models.`, true);
  } else {
    setStatus(`API key detected for ${provider}.`);
  }
});

modelSelect.addEventListener("change", () => {
  if (modelSelect.value === "__custom__") {
    setCustomModelVisibility(true);
  } else {
    setCustomModelVisibility(false);
  }
});

ollamaBaseUrl.addEventListener("blur", async () => {
  if (providerSelect.value === "ollama") {
    await refreshModelOptions("ollama", getSelectedModel());
  }
});

saveApiKeyBtn.addEventListener("click", async () => {
  const provider = providerSelect.value;
  if (provider === "ollama") {
    setStatus("Ollama does not require an API key.");
    return;
  }

  const key = providerApiKeyInput.value.trim();
  if (!key) {
    setStatus("Enter an API key before saving.", true);
    return;
  }

  try {
    const res = await fetch(`/api/settings/api-keys/${provider}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ api_key: key }),
    });
    const payload = await res.json();
    if (!res.ok) throw new Error(payload.detail || "Unable to save API key");

    providerApiKeyInput.value = "";
    const refreshed = await fetchSettings();
    await applySettings(refreshed);
    await refreshModelOptions(provider, getSelectedModel());
    setStatus(`API key saved for ${provider}.`);
  } catch (error) {
    setStatus(error.message || "API key action failed", true);
  }
});

removeApiKeyBtn.addEventListener("click", async () => {
  const provider = providerSelect.value;
  if (provider === "ollama") {
    setStatus("Ollama does not require an API key.");
    return;
  }

  try {
    const res = await fetch(`/api/settings/api-keys/${provider}`, { method: "DELETE" });
    const payload = await res.json();
    if (!res.ok) throw new Error(payload.detail || "Unable to remove API key");

    const refreshed = await fetchSettings();
    await applySettings(refreshed);
    setStatus(`API key removed for ${provider}.`);
  } catch (error) {
    setStatus(error.message || "API key action failed", true);
  }
});

settingsForm.addEventListener("submit", async (event) => {
  event.preventDefault();

  const model = getSelectedModel();
  if (!model) {
    setStatus("Select or enter a model name.", true);
    return;
  }

  const payload = {
    provider: providerSelect.value,
    model,
    ollama_base_url: ollamaBaseUrl.value.trim(),
    temperature: Number(temperatureInput.value || "0.2"),
  };

  try {
    const res = await fetch("/api/settings", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Unable to save settings");

    await applySettings(data);
    setStatus("Settings saved.");
  } catch (error) {
    setStatus(error.message || "Unable to save settings", true);
  }
});

(async function init() {
  try {
    const settings = await fetchSettings();
    await applySettings(settings);
    setStatus("Settings loaded.");
  } catch {
    setStatus("Could not load settings.", true);
  }
})();
