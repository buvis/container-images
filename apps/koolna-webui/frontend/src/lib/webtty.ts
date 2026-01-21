// Message types sent to server
const MSG_INPUT = '1';
const MSG_PING = '2';
const MSG_RESIZE = '3';
const MSG_SET_ENCODING = '4';

// Message types received from server
const MSG_OUTPUT = '1';
const MSG_PONG = '2';
const MSG_SET_WINDOW_TITLE = '3';
const MSG_SET_PREFERENCES = '4';
const MSG_SET_RECONNECT = '5';
const MSG_SET_BUFFER_SIZE = '6';

export const GOTTY_PROTOCOLS = ['webtty'];

export interface TerminalInterface {
  info(): { columns: number; rows: number };
  output(data: Uint8Array): void;
  onInput(cb: (input: Uint8Array) => void): void;
  onResize(cb: (cols: number, rows: number) => void): void;
  deactivate(): void;
  reset(): void;
  showMessage(msg: string, timeout: number): void;
  setWindowTitle(title: string): void;
  setPreferences(prefs: Record<string, unknown>): void;
}

export type ConnectionStatus = 'connected' | 'disconnected' | 'reconnecting';

export interface WebTTYCallbacks {
  onStatus?: (status: ConnectionStatus) => void;
  onReconnect?: (seconds: number) => void;
}

export class ConnectionFactory {
  constructor(
    private url: string,
    private protocols: string[]
  ) {}

  create(): Connection {
    return new Connection(this.url, this.protocols);
  }
}

export class Connection {
  private socket: WebSocket;

  constructor(url: string, protocols: string[]) {
    this.socket = new WebSocket(url, protocols);
  }

  open(): void {}

  close(): void {
    this.socket.close();
  }

  send(payload: string): void {
    this.socket.send(payload);
  }

  isOpen(): boolean {
    return this.socket.readyState === WebSocket.CONNECTING || this.socket.readyState === WebSocket.OPEN;
  }

  onOpen(cb: () => void): void {
    this.socket.onopen = cb;
  }

  onReceive(cb: (data: string) => void): void {
    this.socket.onmessage = (event) => cb(event.data);
  }

  onClose(cb: () => void): void {
    this.socket.onclose = cb;
  }
}

export class WebTTY {
  private reconnect = -1;
  private bufSize = 1024;
  private connection: Connection | null = null;
  private callbacks: Required<WebTTYCallbacks>;

  constructor(
    private term: TerminalInterface,
    private connectionFactory: ConnectionFactory,
    callbacks: WebTTYCallbacks = {}
  ) {
    this.callbacks = {
      onStatus: callbacks.onStatus ?? (() => {}),
      onReconnect: callbacks.onReconnect ?? (() => {}),
    };
  }

  open(): () => void {
    let connection = this.connectionFactory.create();
    let pingTimer: ReturnType<typeof setInterval> | undefined;
    let reconnectTimer: ReturnType<typeof setTimeout> | undefined;
    this.connection = connection;

    const setup = () => {
      connection.onOpen(() => {
        this.callbacks.onStatus('connected');
        const termInfo = this.term.info();
        this.initializeConnection();

        this.term.onResize((columns, rows) => this.sendResizeTerminal(columns, rows));
        this.sendResizeTerminal(termInfo.columns, termInfo.rows);
        this.sendSetEncoding('base64');

        this.term.onInput((input) => this.sendInput(input));

        pingTimer = setInterval(() => this.sendPing(), 30000);
      });

      connection.onReceive((data) => {
        const payload = data.slice(1);
        switch (data[0]) {
          case MSG_OUTPUT:
            this.term.output(Uint8Array.from(atob(payload), (c) => c.charCodeAt(0)));
            break;
          case MSG_PONG:
            break;
          case MSG_SET_WINDOW_TITLE:
            this.term.setWindowTitle(payload);
            break;
          case MSG_SET_PREFERENCES:
            this.term.setPreferences(JSON.parse(payload));
            break;
          case MSG_SET_RECONNECT:
            this.reconnect = JSON.parse(payload);
            this.callbacks.onReconnect(this.reconnect);
            break;
          case MSG_SET_BUFFER_SIZE:
            this.bufSize = JSON.parse(payload);
            break;
        }
      });

      connection.onClose(() => {
        if (pingTimer) clearInterval(pingTimer);
        this.callbacks.onStatus('disconnected');
        this.term.deactivate();
        this.term.showMessage('Connection closed', 0);
        if (this.reconnect > 0) {
          reconnectTimer = setTimeout(() => {
            this.callbacks.onStatus('reconnecting');
            connection = this.connectionFactory.create();
            this.connection = connection;
            this.term.reset();
            setup();
          }, this.reconnect * 1000);
        }
      });

      connection.open();
    };

    setup();
    return () => {
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (pingTimer) clearInterval(pingTimer);
      connection.close();
    };
  }

  private initializeConnection(): void {
    this.connection?.send(JSON.stringify({ Arguments: '', AuthToken: '' }));
  }

  sendInput(input: Uint8Array | string): void {
    const effective = this.bufSize - 1;
    const maxChunkSize = Math.floor(effective / 4) * 3;
    const dataString = typeof input === 'string' ? input : String.fromCharCode(...input);

    for (let i = 0; i < Math.ceil(dataString.length / maxChunkSize); i++) {
      const chunk = dataString.substring(i * maxChunkSize, Math.min((i + 1) * maxChunkSize, dataString.length));
      this.connection?.send(MSG_INPUT + btoa(chunk));
    }
  }

  private sendPing(): void {
    this.connection?.send(MSG_PING);
  }

  private sendResizeTerminal(columns: number, rows: number): void {
    this.connection?.send(MSG_RESIZE + JSON.stringify({ columns, rows }));
  }

  private sendSetEncoding(mode: string): void {
    this.connection?.send(MSG_SET_ENCODING + mode);
  }
}
