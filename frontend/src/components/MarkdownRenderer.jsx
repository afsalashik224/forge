import React from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { Copy, Check } from 'lucide-react';

function CopyCodeButton({ code }) {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <button
      onClick={handleCopy}
      style={{
        position: 'absolute',
        top: '8px',
        right: '8px',
        background: 'var(--surface-secondary)',
        border: '1px solid var(--border-color)',
        borderRadius: '4px',
        padding: '4px 6px',
        cursor: 'pointer',
        color: copied ? 'var(--emerald-primary)' : 'var(--text-muted)',
        display: 'flex',
        alignItems: 'center',
        gap: '4px',
        fontSize: '0.7rem',
        opacity: 0.8,
        transition: 'opacity 0.15s',
      }}
      title={copied ? 'Copied!' : 'Copy code'}
      aria-label="Copy code"
    >
      {copied ? <Check size={12} /> : <Copy size={12} />}
      {copied ? 'Copied' : 'Copy'}
    </button>
  );
}

export default function MarkdownRenderer({ content }) {
  if (!content) {
    return null;
  }

  return (
    <div className="markdown-body">
      <Markdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          pre({ children, ...props }) {
            const code = React.Children.toArray(children).find(
              (child) => child?.type === 'code'
            );
            const codeText = code?.props?.children
              ? String(code.props.children).replace(/\n$/, '')
              : '';

            return (
              <div style={{ position: 'relative' }}>
                <CopyCodeButton code={codeText} />
                <pre {...props}>{children}</pre>
              </div>
            );
          },
        }}
      >
        {content}
      </Markdown>
    </div>
  );
}
