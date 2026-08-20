import { GoogleLogin } from "@react-oauth/google";

const API_URL = import.meta.env.VITE_API_URL;

const STEPS = [
  { n: "1", label: "Tell us what happened", detail: "In your own words -- no forms to fill." },
  { n: "2", label: "Answer a few questions", detail: "Where, when, and how to reach you." },
  { n: "3", label: "We route it", detail: "Sent straight to the right department." },
  { n: "4", label: "You hear back", detail: "By email, at the address you sign in with." },
];

export default function Login({ onLogin }) {
  async function handleSuccess(credentialResponse) {
    const res = await fetch(`${API_URL}/api/auth/google`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ credential: credentialResponse.credential }),
    });
    if (!res.ok) {
      console.error("Google auth failed");
      return;
    }
    const user = await res.json();
    onLogin(user);
  }

  return (
    <div className="auth-shell">
      <div className="auth-brand">
        <span className="auth-seal">CR</span>
        <h1 className="auth-headline">
          File it once.
          <br />
          It finds the right desk.
        </h1>
        <p className="auth-sub">
          A single place to report an issue and have it routed to the
          department that actually handles it.
        </p>

        <ol className="auth-steps">
          {STEPS.map((s) => (
            <li key={s.n} className="auth-step">
              <span className="auth-step-num">{s.n}</span>
              <span className="auth-step-text">
                <strong>{s.label}</strong>
                <span>{s.detail}</span>
              </span>
            </li>
          ))}
        </ol>
      </div>

      <div className="auth-ticket-edge" aria-hidden="true">
        <span className="auth-notch auth-notch-top" />
        <span className="auth-perf" />
        <span className="auth-notch auth-notch-bottom" />
      </div>

      <div className="auth-panel">
        <div className="auth-panel-inner">
          <p className="auth-panel-eyebrow">Sign in to continue</p>
          <h2 className="auth-panel-title">Welcome</h2>
          <p className="auth-panel-sub">
            We use your Google account to verify who you are and to send
            updates on your complaint.
          </p>

          <div className="auth-google-wrap">
            <GoogleLogin onSuccess={handleSuccess} onError={() => console.error("Login failed")} />
          </div>

          <p className="auth-fine-print">
            We only read your name, email, and profile photo. We never post
            or send anything on your behalf.
          </p>
        </div>
      </div>
    </div>
  );
}