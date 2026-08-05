import React from 'react';

export default function SkeletonCard() {
  return (
    <div className="matte-card" style={{ padding: '20px', minHeight: '180px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '14px' }}>
          <div className="skeleton" style={{ width: '60px', height: '20px' }} />
          <div className="skeleton" style={{ width: '40px', height: '16px' }} />
        </div>
        <div className="skeleton" style={{ width: '75%', height: '22px', marginBottom: '10px' }} />
        <div className="skeleton" style={{ width: '45%', height: '16px', marginBottom: '16px' }} />
        <div className="skeleton" style={{ width: '100%', height: '14px', marginBottom: '6px' }} />
        <div className="skeleton" style={{ width: '85%', height: '14px' }} />
      </div>
      <div style={{ paddingTop: '12px', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between' }}>
        <div className="skeleton" style={{ width: '90px', height: '14px' }} />
        <div className="skeleton" style={{ width: '14px', height: '14px' }} />
      </div>
    </div>
  );
}
