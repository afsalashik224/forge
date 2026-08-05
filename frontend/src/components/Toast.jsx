import React, { useEffect } from 'react';
import { CheckCircle2, AlertCircle, X } from 'lucide-react';

export default function Toast({ message, type = 'success', onClose, duration = 4000 }) {
  useEffect(() => {
    if (!message) return;
    const timer = setTimeout(() => {
      onClose();
    }, duration);
    return () => clearTimeout(timer);
  }, [message, type, onClose, duration]);

  if (!message) return null;

  const isSuccess = type === 'success';

  return (
    <div style={{
      position: 'fixed',
      bottom: '24px',
      right: '24px',
      zIndex: 200,
      backgroundColor: 'var(--surface-primary)',
      border: `1px solid ${isSuccess ? 'var(--emerald-border)' : 'rgba(239, 68, 68, 0.4)'}`,
      borderRadius: '8px',
      padding: '12px 16px',
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      boxShadow: '0 10px 30px rgba(0, 0, 0, 0.4)',
      color: 'var(--text-primary)',
      fontSize: '0.875rem',
      maxWidth: '400px'
    }}>
      {isSuccess ? (
        <CheckCircle2 size={18} color="var(--emerald-primary)" />
      ) : (
        <AlertCircle size={18} color="#EF4444" />
      )}

      <span style={{ flex: 1 }}>{message}</span>

      <button
        onClick={onClose}
        style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', display: 'flex' }}
        aria-label="Close notification"
      >
        <X size={16} />
      </button>
    </div>
  );
}
