import { NavLink, Outlet } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/", label: "Home" },
  { to: "/metadata", label: "Metadata" },
  { to: "/settings", label: "Settings" },
  { to: "/live-execution", label: "Live Execution" },
  { to: "/strategy", label: "Strategy Run" },
  { to: "/ml", label: "ML Run" },
  { to: "/paper", label: "Paper Trading" },
  { to: "/history", label: "Run History" },
  { to: "/compare", label: "Compare Runs" },
  { to: "/runs", label: "Legacy Runs" }
];

export function AppShell() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <h1>Capstone Research Platform</h1>
          <p>Backend-first multi-asset research shell</p>
        </div>
        <nav>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                isActive ? "nav-link active" : "nav-link"
              }
              end={item.to === "/"}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
