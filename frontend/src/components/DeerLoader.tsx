export default function DeerLoader() {
  return (
    <div className="flex items-center gap-1 py-1">
      <span className="inline-block animate-amongus-walk [animation-delay:-0.3s]">👾</span>
      <span className="inline-block animate-amongus-walk [animation-delay:-0.1s]">👾</span>
      <span className="inline-block animate-amongus-walk [animation-delay:0.1s]">👾</span>
      <span className="inline-block animate-amongus-walk [animation-delay:0.3s]">👾</span>
      <style>{`
        @keyframes amongusWalk {
          0% { transform: translateX(0) translateY(0) scale(1); opacity: 0.7; }
          25% { transform: translateX(8px) translateY(-3px) scale(1.1); opacity: 1; }
          50% { transform: translateX(16px) translateY(0) scale(1); opacity: 0.8; }
          75% { transform: translateX(24px) translateY(-2px) scale(0.9); opacity: 0.9; }
          100% { transform: translateX(32px) translateY(0) scale(1); opacity: 0.7; }
        }
      `}</style>
      <style>{`.animate-amongus-walk{animation: amongusWalk 1.2s ease-in-out infinite;}`}</style>
    </div>
  );
}


