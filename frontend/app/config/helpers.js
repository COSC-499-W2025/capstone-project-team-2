export function resolveExternalConsentState(config) {
  const external = config?.consented?.external;
  if (external === true) return "allow";
  if (external === false) return "deny";
  return "unset";
}

export function formatExternalConsentLabel(state) {
  if (state === "allow") return "Allow";
  if (state === "deny") return "Do not allow";
  return "Not set";
}

export function validateExternalConsentSelection(state) {
  if (state === "unset") {
    return "Please choose whether external tools are allowed.";
  }
  return "";
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
