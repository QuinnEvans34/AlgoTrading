import { NavLink, Outlet } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard" },
  { to: "/stocks", label: "Stocks" },
  { to: "/forex", label: "Forex" },
  { to: "/strategy", label: "Strategy Lab" },
  { to: "/ml", label: "ML Lab" },
  { to: "/history", label: "History" },
  { to: "/compare", label: "Compare" },
  { to: "/paper", label: "Paper" },
  { to: "/live-execution", label: "Live" },
  { to: "/settings", label: "Settings" },
  { to: "/runs", label: "Legacy Runs" }
];

export function AppShell() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <h1>Capstone Research Platform</h1>
          <p>Multi-asset research workspace with curated browsing and saved workflows</p>
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
