export default function Card({ children, className = "", glass = false }) {
  return (
    <div className={`${glass ? "glass-panel" : "surface-card surface-elevated"} ${className}`}>
      {children}
    </div>
  );
}
