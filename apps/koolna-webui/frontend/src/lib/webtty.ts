export type ConnectionStatus = 'connected' | 'disconnected' | 'reconnecting';

export interface RawTerminalCallbacks {
  onData: (data: Uint8Array<ArrayBuffer>) => void;
  onStatus: (status: ConnectionStatus) => void;
}

export class RawTerminal {
  private url: string;
  private callbacks: RawTerminalCallbacks;
  private ws: WebSocket | null = null;
  private reconnectDelay: number;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private disposed = false;
  private initialCols: number;
  private initialRows: number;

  constructor(
    url: string,
    callbacks: RawTerminalCallbacks,
    opts: { cols: number; rows: number; reconnectDelay?: number }
  ) {
    this.url = url;
    this.callbacks = callbacks;
    this.initialCols = opts.cols;
    this.initialRows = opts.rows;
    this.reconnectDelay = opts.reconnectDelay ?? 3000;
  }

  open(): void {
    this.connect();
  }

  close(): void {
    this.disposed = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.onclose = null;
      this.ws.close();
      this.ws = null;
    }
  }

  sendInput(data: Uint8Array<ArrayBuffer>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(data);
    }
  }

  sendResize(cols: number, rows: number): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'resize', cols, rows }));
    }
  }

  private connect(): void {
    if (this.disposed) return;

    const ws = new WebSocket(this.url);
    ws.binaryType = 'arraybuffer';
    this.ws = ws;

    ws.onopen = () => {
      this.callbacks.onStatus('connected');
      this.sendResize(this.initialCols, this.initialRows);
    };

    ws.onmessage = (event: MessageEvent) => {
      if (event.data instanceof ArrayBuffer) {
        this.callbacks.onData(new Uint8Array(event.data));
      }
    };

    ws.onclose = () => {
      this.callbacks.onStatus('disconnected');
      this.scheduleReconnect();
    };
  }

  private scheduleReconnect(): void {
    if (this.disposed) return;
    this.callbacks.onStatus('reconnecting');
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, this.reconnectDelay);
  }
}
