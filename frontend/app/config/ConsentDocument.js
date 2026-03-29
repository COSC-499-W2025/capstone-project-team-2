/**
 * Renders the static consent agreement document as structured JSX.
 *
 * @returns {JSX.Element}
 */
export default function ConsentDocument() {
  return (
    <div className="consent-document">
      <p>This software analyzes data you provide to generate insights about your project. Before continuing, please review the following terms and conditions.</p>

      <h2>How Your Data Will Be Used</h2>
      <p>Your data will be:</p>
      <ul>
        <li>Loaded and processed <strong>locally</strong> on your machine</li>
        <li>Used to perform analysis and generate results</li>
        <li>Stored only on your system unless you manually export or share it</li>
      </ul>
      <blockquote>You must consent to local data use to run the program.</blockquote>

      <h2>Optional External Processing</h2>
      <p>
        The program can optionally send portions of your data to trusted external AI services
        (e.g., large language model APIs) to enhance analysis quality.
      </p>
      <p>If you choose <strong>Do not allow</strong> for external processing:</p>
      <ul>
        <li>Your data <strong>stays local</strong></li>
        <li>The system still runs with <strong>basic analysis only</strong></li>
      </ul>

      <h2>What We Do NOT Do</h2>
      <p>We do <strong>not</strong>:</p>
      <ul>
        <li>Collect personal information outside the data you provide</li>
        <li>Sell or share your data</li>
        <li>Store your data remotely</li>
      </ul>

      <h2>Revoking Consent</h2>
      <p>You can revoke consent at any time. When revoked:</p>
      <ul>
        <li>Local processing stops</li>
        <li>External processing (if enabled) stops</li>
        <li>You may delete any local project files or outputs</li>
      </ul>

      <p className="muted" style={{ marginTop: "1rem", fontSize: "0.82rem" }}>
        By saving your configuration below, you acknowledge that you understand and agree to local
        data processing. External processing is optional and controlled by the consent toggle.
        You may change or revoke your choices at any time by returning to this page.
      </p>

      <p className="muted" style={{ fontSize: "0.78rem" }}>
        Team 2 · COSC 499 Capstone · 2025/26 · University of British Columbia
      </p>
    </div>
  );
}
