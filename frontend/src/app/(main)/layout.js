import Sidebar from '../../components/layout/Sidebar';

export default function MainAppLayout({ children }) {
  return (
    <div>
      <Sidebar />
      <main style={{ marginLeft: '300px', transition: 'margin-left 0.3s ease-in-out' }}>
        {children}
      </main>
    </div>
  );
}