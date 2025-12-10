import { Outlet, Link } from 'react-router-dom';

export default function Layout() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <nav style={{ padding: '1rem', borderBottom: '1px solid #333', display: 'flex', gap: '1rem', justifyContent: 'center' }}>
        <Link to="/">Live Dashboard</Link>
        <Link to="/history">Session History</Link>
        <Link to="/config">Configuration</Link>
      </nav>
      <main style={{ flex: 1, padding: '2rem' }}>
        <Outlet />
      </main>
    </div>
  );
}
