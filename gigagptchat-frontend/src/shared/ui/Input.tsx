import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  label?: string;
}

export const Input: React.FC<InputProps> = ({ error, label, className = '', id, ...props }) => {
  const inputId = id || `input-${Math.random().toString(36).slice(2)}`;

  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={inputId} className="text-sm font-medium text-[var(--sber-text-secondary)]">
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={`
          px-4 py-2.5
          bg-[var(--sber-bg-primary)]
          border border-[var(--sber-border)]
          rounded-xl
          text-[var(--sber-text-primary)]
          placeholder:text-[var(--sber-text-tertiary)]
          focus:outline-none focus:ring-2 focus:ring-[var(--sber-primary)] focus:border-transparent
          transition-all duration-200
          disabled:bg-[var(--sber-bg-tertiary)] disabled:cursor-not-allowed
          ${error ? 'border-[var(--sber-error)] focus:ring-[var(--sber-error)]' : ''}
          ${className}
        `}
        {...props}
      />
      {error && (
        <span className="text-sm text-[var(--sber-error)]">{error}</span>
      )}
    </div>
  );
};