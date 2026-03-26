import { useEffect, useRef, useState, useCallback } from 'react';
import { RawTerminal, type ConnectionStatus } from '../lib/webtty';
import { XtermAdapter } from '../lib/xterm-adapter';
import { Keypad } from './Keypad';
import '@xterm/xterm/css/xterm.css';

interface TerminalProps {
  name: string;
  session: string;
  onBack: () => void;
}

function buildWebsocketUrl(name: string, session: string): string {
  const scheme = location.protocol === 'https:' ? 'wss' : 'ws';
  return `${scheme}://${location.host}/api/koolnas/${name}/terminal?session=${encodeURIComponent(session)}`;
}

const statusColors: Record<ConnectionStatus, string> = {
  connected: 'text-green-400',
  disconnected: 'text-red-400',
  reconnecting: 'text-yellow-400',
};

export function Terminal({ name, session, onBack }: TerminalProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const rawTermRef = useRef<RawTerminal | null>(null);
  const adapterRef = useRef<XtermAdapter | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');

  useEffect(() => {
    if (!containerRef.current) return;
    let cancelled = false;
    let inputDisposable: { dispose(): void } | undefined;
    let resizeDisposable: { dispose(): void } | undefined;

    XtermAdapter.create(containerRef.current).then((adapter) => {
      if (cancelled) { adapter.dispose(); return; }
      adapterRef.current = adapter;
      adapter.setupOSC52Clipboard();

      const encoder = new TextEncoder();
      const { columns, rows } = adapter.info();
      const wsUrl = buildWebsocketUrl(name, session);

      const rawTerm = new RawTerminal(wsUrl, {
        onData: (data) => {
          // Log first 20 messages and any with high bytes
          if ((window as any).__koolnaCount === undefined) (window as any).__koolnaCount = 0;
          (window as any).__koolnaCount++;
          const count = (window as any).__koolnaCount;
          let hasHigh = false;
          for (let i = 0; i < data.length; i++) {
            if (data[i] >= 0x80) { hasHigh = true; break; }
          }
          if (count <= 20 || hasHigh) {
            const hex = [...data.slice(0, 100)].map(b => b.toString(16).padStart(2, '0')).join(' ');
            console.log(`[koolna] msg#${count} (${data.length}B) high=${hasHigh}:`, hex);
          }
          adapter.term.write(data);
        },
        onStatus: setStatus,
      }, { cols: columns, rows });
      rawTermRef.current = rawTerm;

      inputDisposable = adapter.term.onData((input) => {
        rawTerm.sendInput(encoder.encode(input));
      });

      resizeDisposable = adapter.term.onResize(() => {
        rawTerm.sendResize(adapter.term.cols, adapter.term.rows);
      });

      rawTerm.open();
    });

    return () => {
      cancelled = true;
      inputDisposable?.dispose();
      resizeDisposable?.dispose();
      rawTermRef.current?.close();
      adapterRef.current?.dispose();
      rawTermRef.current = null;
      adapterRef.current = null;
    };
  }, [name, session]);

  const handleKeypadKey = useCallback((seq: string) => {
    const encoder = new TextEncoder();
    rawTermRef.current?.sendInput(encoder.encode(seq));
    adapterRef.current?.term.focus();
  }, []);

  return (
    <div className="h-screen flex flex-col bg-bg">
      <header className="flex items-center justify-between px-4 py-2 bg-surface border-b border-gray-800">
        <button
          onClick={onBack}
          className="text-gray-400 hover:text-white transition-colors"
        >
          ← Back
        </button>
        <span className="text-gray-300 font-mono">{session}</span>
        <span className={`font-mono text-sm ${statusColors[status]}`}>
          {status}
        </span>
      </header>
      <div ref={containerRef} className="flex-1 overflow-hidden pb-16 md:pb-0" />
      <Keypad onKey={handleKeypadKey} />
    </div>
  );
}
