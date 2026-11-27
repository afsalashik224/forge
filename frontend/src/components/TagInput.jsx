import React, { useState } from 'react';
import { X, Plus } from 'lucide-react';

export default function TagInput({ tags, onChange, disabled, placeholder }) {
  const [input, setInput] = useState('');

  const addTag = (tagText) => {
    const cleaned = tagText.trim().toLowerCase();
    if (cleaned && !tags.includes(cleaned)) {
      onChange([...tags, cleaned]);
    }
    setInput('');
  };

  const removeTag = (index) => {
    onChange(tags.filter((_, i) => i !== index));
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addTag(input);
    } else if (e.key === 'Backspace' && !input && tags.length > 0) {
      removeTag(tags.length - 1);
    } else if (e.key === ',') {
      e.preventDefault();
      addTag(input);
    }
  };

  return (
    <div>
      {/* Tags Display */}
      {tags.length > 0 && (
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '6px',
          marginBottom: '8px',
        }}>
          {tags.map((tag, index) => (
            <span
              key={tag}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                backgroundColor: 'var(--emerald-subtle)',
                color: 'var(--emerald-primary)',
                border: '1px solid var(--emerald-border)',
                borderRadius: '4px',
                padding: '2px 6px 2px 8px',
                fontSize: '0.75rem',
                fontWeight: 500,
              }}
            >
              {tag}
              {!disabled && (
                <button
                  type="button"
                  onClick={() => removeTag(index)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: 'var(--emerald-primary)',
                    cursor: 'pointer',
                    padding: '0',
                    display: 'flex',
                    alignItems: 'center',
                    opacity: 0.7,
                  }}
                  title={`Remove tag: ${tag}`}
                  aria-label={`Remove tag: ${tag}`}
                >
                  <X size={12} />
                </button>
              )}
            </span>
          ))}
        </div>
      )}

      {/* Input */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
      }}>
        <input
          type="text"
          className="input-matte"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder={placeholder || "Type a tag and press Enter…"}
          style={{ flex: 1 }}
        />
        <button
          type="button"
          onClick={() => addTag(input)}
          disabled={disabled || !input.trim()}
          style={{
            background: 'var(--surface-secondary)',
            border: '1px solid var(--border-color)',
            borderRadius: '6px',
            padding: '8px',
            cursor: input.trim() ? 'pointer' : 'not-allowed',
            color: input.trim() ? 'var(--emerald-primary)' : 'var(--text-muted)',
            display: 'flex',
            alignItems: 'center',
            opacity: input.trim() ? 1 : 0.5,
          }}
          title="Add tag"
          aria-label="Add tag"
        >
          <Plus size={16} />
        </button>
      </div>
    </div>
  );
}
