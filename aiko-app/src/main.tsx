import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import MobileApp from "./MobileApp";
import "./App.css";

// Detect if running on Android (Tauri sets a custom user agent)
// OR detect via touch support + small screen
const isMobile = () => {
  const isAndroid = navigator.userAgent.toLowerCase().includes('android');
  const isSmallScreen = window.innerWidth < 768;
  const isTouch = navigator.maxTouchPoints > 0;
  return isAndroid || (isSmallScreen && isTouch);
};

// Native feel: Prevent default browser behaviors
document.addEventListener("contextmenu", (e) => {
  // Allow right-click only in inputs/textareas
  if (!(e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement)) {
    e.preventDefault();
  }
});
document.addEventListener("selectstart", (e) => {
  if (!(e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement || (e.target as HTMLElement).closest('.selectable'))) {
    e.preventDefault();
  }
});
document.addEventListener("dragstart", (e) => e.preventDefault());

class ErrorBoundary extends React.Component<{children: React.ReactNode}, {hasError: boolean, error: any}> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error: any) {
    return { hasError: true, error };
  }
  componentDidCatch(error: any, errorInfo: any) {
    console.error("[React Crash]", error, errorInfo);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 40, color: '#f87171', background: '#1C1320', height: '100vh', fontFamily: 'monospace' }}>
          <h1 style={{ fontSize: 24, marginBottom: 20 }}>[NEURAL_LINK_ERROR]</h1>
          <p style={{ fontSize: 14, color: '#94a3b8', marginBottom: 20 }}>The Aiko interface encountered a critical failure.</p>
          <pre style={{ background: '#2A1B30', padding: 20, borderRadius: 12, overflow: 'auto', fontSize: 12 }}>
            {this.state.error?.toString()}
          </pre>
          <button 
            onClick={() => window.location.reload()}
            style={{ marginTop: 20, padding: '10px 20px', background: '#C9A8D9', border: 'none', borderRadius: 8, color: '#1C1320', fontWeight: 'bold', cursor: 'pointer' }}
          >
            Reconnect Neural Interface
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

import MascotApp from "./MascotApp";
import SplashScreen from "./SplashScreen";

const isMascot = window.location.search.includes('mascot');
const isSplash = window.location.search.includes('splash');
if (isMascot) {
  document.body.classList.add('mascot-mode');
}
if (isSplash) {
  document.body.classList.add('splash-mode');
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <ErrorBoundary>
      {isSplash 
        ? <SplashScreen />
        : (isMascot 
            ? <MascotApp /> 
            : (isMobile() ? <MobileApp /> : <App />))
      }
    </ErrorBoundary>
  </React.StrictMode>,
);

