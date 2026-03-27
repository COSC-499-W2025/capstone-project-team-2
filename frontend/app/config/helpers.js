export function resolveExternalConsentState(config) {
  const external = config?.consented?.external;
  if (external === true) return "allow";
  if (external === false) return "deny";
  return "deny";
}

export function formatExternalConsentLabel(state) {
  if (state === "allow") return "Allow";
  return "Do not allow";
}

export function validateExternalConsentSelection(_state) {
  return "";
}

export function resolveLocalConsentState(config) {
  const local = config?.consented?.["Data consent"];
  if (local === true) return "allow";
  return "deny";
}

export function formatLocalConsentLabel(state) {
  if (state === "allow") return "Allow";
  return "Do not allow";
}

export function applyNameToConfig(baseConfig, fullName) {
  const nextConfig = { ...baseConfig };
  const cleaned = String(fullName || "").trim();

  if (cleaned) {
    const [first, ...rest] = cleaned.split(/\s+/);
    nextConfig["First Name"] = first;
    nextConfig["Last Name"] = rest.join(" ");
  } else {
    nextConfig["First Name"] = "";
    nextConfig["Last Name"] = "";
  }

  return nextConfig;
}
