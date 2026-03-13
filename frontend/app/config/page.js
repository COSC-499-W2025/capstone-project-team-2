"use client";

/**
 * User configuration route module.
 *
 * Purpose:
 * - hydrate persisted consent/profile values,
 * - provide editable controls,
 * - and persist updates through backend config endpoints.
 */
import { useEffect, useState } from "react";
import { GlassCard, LiquidShell } from "../../components/LiquidShell";
import { LiquidSegmentedControl } from "../../components/LiquidPillControl";
import { fetchConfig, saveConsent, updateConfig } from "../../lib/api";
import {
  applyNameToConfig,
  formatExternalConsentLabel,
  resolveExternalConsentState,
  validateExternalConsentSelection
} from "./helpers";

/**
 * User configuration route for consent and profile preference updates.
 * Loads current configuration, allows controlled edits, and persists
 * changes through backend config endpoints.
 *
 * @returns {JSX.Element}
 */
export default function ConfigPage() {
  /**
   * Primary data and request-state atoms for this page.
   */
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const [externalConsent, setExternalConsent] = useState("unset");
  const [fullName, setFullName] = useState("");

  useEffect(() => {
    let ignore = false;
    /**
     * Loads persisted configuration and maps it into local component state.
     * Uses an `ignore` guard to avoid state updates after unmount.
     *
     * @returns {Promise<void>}
     */
    async function load() {
      setLoading(true);
      setError("");
      try {
        const data = await fetchConfig();
        if (ignore) return;
        setConfig(data || {});

        setExternalConsent(resolveExternalConsentState(data));

        const first = String(data?.["First Name"] || "").trim();
        const last = String(data?.["Last Name"] || "").trim();
        setFullName([first, last].filter(Boolean).join(" "));
      } catch (err) {
        if (!ignore) setError(err.message || "Failed to load config.");
      } finally {
        if (!ignore) setLoading(false);
      }
    }
    load();
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
      await saveConsent(allowExternal);

      const nextConfig = applyNameToConfig(config, fullName);
      nextConfig.consented = { external: allowExternal, "Data consent": true };

      await updateConfig(nextConfig);
      setConfig(nextConfig);
      setMessage("Configuration saved.");
    } catch (err) {
      setError(err.message || "Failed to save configuration.");
    }
  }

  const currentExternalConsent = formatExternalConsentLabel(resolveExternalConsentState(config));

  return (
    <LiquidShell
      title="User Configuration"
      subtitle="Set external-tool consent and optional profile preferences."
    >
      <div className="page-stack config-page">
        {loading ? <p className="muted">Loading configuration...</p> : null}
        {error ? <p className="error">{error}</p> : null}
        {message ? <p className="success">{message}</p> : null}

        {!loading && config ? (
          <div className="grid two-col config-grid">
            <GlassCard title="Current Settings">
              <p className="muted">Current persisted configuration values.</p>
              <div className="settings-list">
                <div className="settings-row">
                  <span className="settings-label">External tools</span>
                  <strong className="settings-value">{currentExternalConsent}</strong>
                </div>
                <div className="settings-row">
                  <span className="settings-label">Name</span>
                  <strong className="settings-value">{fullName || "Not set"}</strong>
                </div>
              </div>
            </GlassCard>

            <GlassCard title="Update Settings">
              <p className="muted">Adjust values and save to persist changes.</p>
              <form onSubmit={onSave} className="form-stack config-form">
                <label>
                  External tools consent
                  <LiquidSegmentedControl
                    className="config-consent-control"
                    value={externalConsent}
                    onChange={setExternalConsent}
                    options={[
                      { value: "unset", label: "Not set" },
                      { value: "allow", label: "Allow" },
                      { value: "deny", label: "Do not allow" }
                    ]}
                  />
                </label>

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
          </div>
        ) : null}
      </div>
    </LiquidShell>
  );
}
