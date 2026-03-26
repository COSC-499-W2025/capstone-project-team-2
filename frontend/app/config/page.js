"use client";

/**
 * User configuration route module.
 *
 * Purpose:
 * - hydrate persisted consent/profile values,
 * - and persist updates through backend configuration endpoints.
 */
import { useEffect, useState } from "react";
import { GlassCard, LiquidShell } from "../../components/LiquidShell";
import { LiquidSegmentedControl } from "../../components/LiquidPillControl";
import { fetchConfig, saveConsent, updateConfig } from "../../lib/api";
import {
  applyNameToConfig,
  formatExternalConsentLabel,
  formatLocalConsentLabel,
  resolveExternalConsentState,
  resolveLocalConsentState,
  validateExternalConsentSelection
} from "./helpers";
import ConsentDocument from "./ConsentDocument";

/**
 * User configuration route for consent and profile settings.
 *
 * @returns {JSX.Element}
 */
export default function ConfigPage() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [externalConsent, setExternalConsent] = useState("deny");
  const [localConsent, setLocalConsent] = useState("deny");
  const [fullName, setFullName] = useState("");
  const [consentExpanded, setConsentExpanded] = useState(false);

  useEffect(() => {
    let ignore = false;

    async function loadConfigData() {
      setLoading(true);
      setError("");
      try {
        const data = await fetchConfig();
        if (ignore) return;
        setConfig(data || {});
        setConsentExpanded(!data?.consented?.["Data consent"]);
        setExternalConsent(resolveExternalConsentState(data));
        setLocalConsent(resolveLocalConsentState(data));

        const first = String(data?.["First Name"] || "").trim();
        const last = String(data?.["Last Name"] || "").trim();
        setFullName([first, last].filter(Boolean).join(" "));
      } catch (err) {
        if (!ignore) setError(err.message || "Failed to load config.");
      } finally {
        if (!ignore) setLoading(false);
      }
    }

    loadConfigData();

    return () => {
      ignore = true;
    };
  }, []);

  /**
   * Persists consent and name changes back to backend configuration.
   *
   * @param {import("react").FormEvent<HTMLFormElement>} event
   * @returns {Promise<void>}
   */
  async function onSave(event) {
    event.preventDefault();
    if (!config) return;

    setError("");
    setMessage("");

    const consentError = validateExternalConsentSelection(externalConsent);
    if (consentError) {
      setError(consentError);
      return;
    }

    try {
      const allowExternal = externalConsent === "allow";
      const allowLocal = localConsent === "allow";
      await saveConsent(allowExternal);

      const nextConfig = applyNameToConfig(config, fullName);
      nextConfig.consented = { external: allowExternal, "Data consent": allowLocal };

      await updateConfig(nextConfig);
      setConfig(nextConfig);
      window.dispatchEvent(new CustomEvent("consentUpdated"));
      setMessage("Configuration saved.");
    } catch (err) {
      setError(err.message || "Failed to save configuration.");
    }
  }

  const currentExternalConsent = formatExternalConsentLabel(resolveExternalConsentState(config));
  const currentLocalConsent = formatLocalConsentLabel(resolveLocalConsentState(config));

  return (
    <LiquidShell
      title="User Configuration"
      subtitle="Set consent and profile details."
    >
      <div className="page-stack config-page">
        {loading ? <p className="muted">Loading configuration...</p> : null}
        {error ? <p className="error">{error}</p> : null}
        {message ? <p className="success">{message}</p> : null}

        {!loading && config ? (
          <GlassCard title="Data Consent Agreement">
            {consentExpanded ? (
              <>
                <ConsentDocument />
                <div className="button-row" style={{ marginTop: "0.75rem" }}>
                  <button type="button" className="liquid-btn" onClick={() => setConsentExpanded(false)}>
                    Collapse ▲
                  </button>
                </div>
              </>
            ) : (
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <p className="muted" style={{ margin: 0 }}>You have previously reviewed and agreed to the consent agreement.</p>
                <button type="button" className="liquid-btn" onClick={() => setConsentExpanded(true)}>
                  View agreement ▼
                </button>
              </div>
            )}
          </GlassCard>
        ) : null}

        {!loading && config ? (
          <div className="grid two-col config-grid">
            <GlassCard title="Update Settings">
              <p className="muted">Adjust values and save to persist changes.</p>
              <form onSubmit={onSave} className="form-stack config-form">
                <label>
                  Local data processing consent
                  <LiquidSegmentedControl
                    className="config-consent-control"
                    value={localConsent}
                    onChange={setLocalConsent}
                    options={[
                      { value: "allow", label: "Allow" },
                      { value: "deny", label: "Do not allow" }
                    ]}
                  />
                </label>
                {localConsent === "deny" ? (
                  <p className="consent-deny-warning">
                    ⚠ Local consent must be allowed to use this software.
                  </p>
                ) : null}

                <label>
                  External tools consent
                  <LiquidSegmentedControl
                    className="config-consent-control"
                    value={externalConsent}
                    onChange={setExternalConsent}
                    options={[
                      { value: "allow", label: "Allow" },
                      { value: "deny", label: "Do not allow" }
                    ]}
                  />
                </label>
                {externalConsent === "deny" ? (
                  <p className="consent-deny-warning">
                    ⚠ External tools are disabled. AI-powered features will not be available.
                  </p>
                ) : null}

                <label className="settings-row settings-field-row">
                  <span className="settings-label">Full name</span>
                  <input
                    className="settings-control"
                    type="text"
                    value={fullName}
                    placeholder="e.g., Jane Doe"
                    onChange={(e) => setFullName(e.target.value)}
                  />
                </label>

                <div className="button-row">
                  <button type="submit" className="liquid-btn solid">Save Configuration</button>
                </div>
              </form>
            </GlassCard>

            <GlassCard title="Current Settings">
              <p className="muted">Current persisted configuration values.</p>
              <div className="settings-list">
                <div className={`settings-row ${currentLocalConsent === "Allow" ? "status-ok" : "status-missing"}`.trim()}>
                  <span className="settings-label">Local processing</span>
                  <strong className="settings-value">{currentLocalConsent}</strong>
                </div>
                <div className={`settings-row ${currentExternalConsent === "Allow" ? "status-ok" : "status-missing"}`.trim()}>
                  <span className="settings-label">External tools</span>
                  <strong className="settings-value">{currentExternalConsent}</strong>
                </div>
                <div className={`settings-row ${fullName ? "status-ok" : "status-missing"}`.trim()}>
                  <span className="settings-label">Name</span>
                  <strong className="settings-value">{fullName || "Not set"}</strong>
                </div>
              </div>
            </GlassCard>
          </div>
        ) : null}
      </div>
    </LiquidShell>
  );
}
