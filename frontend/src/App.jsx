import { useState } from "react";
import Login from "./Login.jsx";
import Chat from "./Chat.jsx";

export default function App() {
  const [user, setUser] = useState(null);

  return (
    <div className="page">
      <header className="topbar">
        <span className="topbar-mark">CR</span>
        <span className="topbar-title">Complaint Registry</span>
        {user && (
          <span className="topbar-user">
            {user.name}
            <button className="link-btn" onClick={() => setUser(null)}>
              Sign out
            </button>
          </span>
        )}
      </header>

      <main className="content">
        {user ? <Chat user={user} /> : <Login onLogin={setUser} />}
      </main>
    </div>
  );
}
