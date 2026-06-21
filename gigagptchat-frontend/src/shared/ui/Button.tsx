import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  children: React.ReactNode;
  className?: string;
}

const getVariantClasses = (variant: ButtonProps['variant']) => {
  switch (variant) {
    case 'primary':
      return 'text-white shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed';
    case 'secondary':
      return 'bg-[var(--sber-bg-tertiary)] text-[var(--sber-text-primary)] hover:bg-[var(--sber-border)] disabled:opacity-50';
    case 'ghost':
      return 'bg-transparent text-[var(--sber-text-secondary)] hover:bg-[var(--sber-bg-tertiary)] disabled:opacity-50';
    case 'danger':
      return 'bg-[var(--sber-error)] text-white hover:bg-red-600 disabled:opacity-50';
    default:
      return '';
  }
};

const getSizeClasses = (size: ButtonProps['size']) => {
  switch (size) {
    case 'sm':
      return 'px-3 py-1.5 text-sm';
    case 'md':
      return 'px-4 py-2 text-base';
    case 'lg':
      return 'px-6 py-3 text-lg';
    default:
      return '';
  }
};

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  children,
  className = '',
  disabled,
  style,
  ...props
}) => {
  const isPrimary = variant === 'primary';
  
  const classes = `
    inline-flex items-center justify-center font-medium
    transition-all duration-200 ease-out
    focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[var(--sber-primary)]
    ${isPrimary ? 'rounded-xl' : 'rounded-lg'}
    ${getVariantClasses(variant)}
    ${getSizeClasses(size)}
    ${className}
  `.trim();

  const combinedStyle = isPrimary
    ? {
        ...style,
        background: 'var(--sber-gradient-primary)',
      }
    : style;

  return (
    <button className={classes} disabled={disabled} style={combinedStyle} {...props}>
      {children}
    </button>
  );
};