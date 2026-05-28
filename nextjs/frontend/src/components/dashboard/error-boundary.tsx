"use client";

import { Component, type ReactNode } from "react";

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
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div className="flex flex-col items-center justify-center p-8 rounded-lg border border-danger/30 bg-danger/5">
          <p className="text-danger font-semibold mb-2">Something went wrong</p>
          <p className="text-text-muted text-sm mb-4">
            {this.state.error?.message || "An unexpected error occurred"}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="px-4 py-2 text-sm bg-bg-surface border border-border-default rounded-lg hover:bg-bg-elevated transition-colors text-text-primary"
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}