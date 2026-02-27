import { useEffect, useRef, useState, useCallback } from 'react';
import { WebTTY, ConnectionFactory, GOTTY_PROTOCOLS, type ConnectionStatus } from '../lib/webtty';
import { XtermAdapter } from '../lib/xterm-adapter';
import { Keypad } from './Keypad';
import 'xterm/css/xterm.css';

interface TerminalProps {
  name: string;
  session: string;
  onBack: () => void;
}

function buildWebsocketUrl(name: string, session: string): string {
  const scheme = location.protocol === 'https:' ? 'wss' : 'ws';
  return `${scheme}://${location.host}/terminal/${name}/${session}`;
}

const statusColors: Record<ConnectionStatus, string> = {
  connected: 'text-green-400',
  disconnected: 'text-red-400',
  reconnecting: 'text-yellow-400',
};

export function Terminal({ name, session, onBack }: TerminalProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const ttyRef = useRef<WebTTY | null>(null);
  const adapterRef = useRef<XtermAdapter | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');

  useEffect(() => {
    if (!containerRef.current) return;

    const adapter = new XtermAdapter(containerRef.current, session);
    adapterRef.current = adapter;
    const wsUrl = buildWebsocketUrl(name, session);
    const connectionFactory = new ConnectionFactory(wsUrl, GOTTY_PROTOCOLS);

    const tty = new WebTTY(adapter, connectionFactory, {
      onStatus: setStatus,
    });
    ttyRef.current = tty;

    const close = tty.open();

    return () => {
      close();
      adapter.dispose();
      ttyRef.current = null;
      adapterRef.current = null;
    };
  }, [name, session]);

  const handleKeypadKey = useCallback((seq: string) => {
    ttyRef.current?.sendInput(seq);
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
