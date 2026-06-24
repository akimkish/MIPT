import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
    };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
    });
  };

  render(): ReactNode {
    const { hasError, error } = this.state;
    const { children, fallback } = this.props;

    if (hasError) {
      if (fallback) {
        return fallback;
      }

      return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-[var(--sber-bg-secondary)] p-8">
          <div className="w-20 h-20 rounded-2xl bg-[var(--sber-error-bg)] flex items-center justify-center mb-6">
            <AlertTriangle size={40} className="text-[var(--sber-error)]" />
          </div>
          
          <h1 className="text-2xl font-bold text-[var(--sber-text-primary)] mb-2">
            Что-то пошло не так
          </h1>
          
          <p className="text-[var(--sber-text-secondary)] mb-6 text-center max-w-md">
            В приложении произошла ошибка. Попробуйте перезагрузить страницу или вернуться позже.
          </p>
          
          {error && (
            <div className="bg-[var(--sber-bg-primary)] border border-[var(--sber-border)] rounded-lg p-4 mb-6 max-w-2xl w-full overflow-auto">
              <p className="text-sm text-[var(--sber-error)] font-mono break-words">
                {error.message}
              </p>
            </div>
          )}
          
          <div className="flex gap-3">
            <button
              onClick={() => window.location.reload()}
              className="px-6 py-3 text-white rounded-xl hover:opacity-90 transition-all duration-200 shadow-md flex items-center gap-2 font-medium"
              style={{ background: 'var(--sber-gradient-primary)' }}
            >
              <RefreshCw size={16} />
              Перезагрузить страницу
            </button>
            <button
              onClick={this.handleReset}
              className="px-6 py-3 bg-[var(--sber-bg-tertiary)] text-[var(--sber-text-primary)] rounded-xl hover:bg-[var(--sber-border)] transition-colors font-medium"
            >
              Попробовать снова
            </button>
          </div>
        </div>
      );
    }

    return children;
  }
}