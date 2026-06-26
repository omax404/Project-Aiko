import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("Aiko ErrorBoundary caught an error:", error, errorInfo);
    this.setState({ error, errorInfo });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-[#0c0b0a]">
          <div className="max-w-md w-full mx-4 p-8 bg-[#141210] border border-white/[0.06] rounded-2xl shadow-2xl">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-[#f87171]/10 border border-[#f87171]/20 flex items-center justify-center">
                <AlertTriangle size={20} className="text-[#f87171]" />
              </div>
              <div>
                <h2 className="text-[16px] font-semibold text-[#f0ebe3]">Something went wrong</h2>
                <p className="text-[12px] text-[#5a5248]">Aiko encountered an unexpected error</p>
              </div>
            </div>

            <div className="bg-[var(--bg-base)] border border-white/[0.04] rounded-lg p-4 mb-6 overflow-auto max-h-[200px]">
              <p className="text-[11px] font-mono text-[#f87171] leading-relaxed">
                {this.state.error?.toString()}
              </p>
            </div>

            <button
              onClick={this.handleReset}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-[var(--accent)] text-[var(--bg-base)] rounded-lg text-[13px] font-medium hover:bg-[var(--accent)]/80 transition-colors"
            >
              <RotateCcw size={16} />
              Reload Aiko
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
