const SUPPORTED_SESSIONS = new Set(['manager', 'worker']);
const GOTTY_PROTOCOLS = ['webtty'];

const MSG_INPUT = '1';
const MSG_PING = '2';
const MSG_RESIZE = '3';
const MSG_SET_ENCODING = '4';

const MSG_OUTPUT = '1';
const MSG_PONG = '2';
const MSG_SET_WINDOW_TITLE = '3';
const MSG_SET_PREFERENCES = '4';
const MSG_SET_RECONNECT = '5';
const MSG_SET_BUFFER_SIZE = '6';

class ConnectionFactory {
  constructor(url, protocols) {
    this.url = url;
    this.protocols = protocols;
  }

  create() {
    return new Connection(this.url, this.protocols);
  }
}

class Connection {
  constructor(url, protocols) {
    this.socket = new WebSocket(url, protocols);
  }

  open() {}

  close() {
    this.socket.close();
  }

  send(payload) {
    this.socket.send(payload);
  }

  isOpen() {
    return this.socket.readyState === WebSocket.CONNECTING || this.socket.readyState === WebSocket.OPEN;
  }

  onOpen(cb) {
    this.socket.onopen = cb;
  }

  onReceive(cb) {
    this.socket.onmessage = (event) => cb(event.data);
  }

  onClose(cb) {
    this.socket.onclose = cb;
  }
}

class WebTTY {
  constructor(term, connectionFactory, callbacks = {}) {
    this.term = term;
    this.connectionFactory = connectionFactory;
    this.reconnect = -1;
    this.bufSize = 1024;
    this.callbacks = {
      onStatus: () => {},
      onReconnect: () => {},
      ...callbacks
    };
  }

  open() {
    let connection = this.connectionFactory.create();
    let pingTimer;
    let reconnectTimer;
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
        clearInterval(pingTimer);
        this.callbacks.onStatus('disconnected');
        this.term.deactivate();
        this.term.showMessage('Connection closed', 0);
        if (this.reconnect > 0) {
          reconnectTimer = setTimeout(() => {
            this.callbacks.onStatus('reconnecting');
            connection = this.connectionFactory.create();
            this.term.reset();
            setup();
          }, this.reconnect * 1000);
        }
      });

      connection.open();
    };

    setup();
    return () => {
      clearTimeout(reconnectTimer);
      clearInterval(pingTimer);
      connection.close();
    };
  }

  initializeConnection() {
    this.connection.send(JSON.stringify({ Arguments: '', AuthToken: '' }));
  }

  sendInput(input) {
    const effective = this.bufSize - 1;
    const maxChunkSize = Math.floor(effective / 4) * 3;
    let dataString = typeof input === 'string' ? input : String.fromCharCode(...input);

    for (let i = 0; i < Math.ceil(dataString.length / maxChunkSize); i++) {
      const chunk = dataString.substring(i * maxChunkSize, Math.min((i + 1) * maxChunkSize, dataString.length));
      this.connection.send(MSG_INPUT + btoa(chunk));
    }
  }

  sendPing() {
    this.connection.send(MSG_PING);
  }

  sendResizeTerminal(columns, rows) {
    this.connection.send(MSG_RESIZE + JSON.stringify({ columns, rows }));
  }

  sendSetEncoding(mode) {
    this.connection.send(MSG_SET_ENCODING + mode);
  }
}

class XtermTerminal {
  constructor(container, session) {
    this.container = container;
    this.session = session;
    this.fitAddon = new window.FitAddon.FitAddon();
    this.weblinksAddon = new window.WebLinksAddon.WebLinksAddon();
    this.encoder = new TextEncoder();

    this.term = new window.Terminal({
      allowProposedApi: true,
      theme: {
        background: '#05060a',
        foreground: '#f5f5f5',
        cursor: '#38bdf8',
        selectionBackground: '#1d4ed8'
      },
      cursorBlink: true,
      fontSize: 14,
      fontFamily: "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace"
    });

    this.term.loadAddon(this.fitAddon);
    this.term.loadAddon(this.weblinksAddon);

    this.messageEl = document.createElement('div');
    this.messageEl.className = 'xterm-overlay';
    this.messageTimeout = null;

    this.term.open(container);
    this.fitAddon.fit();
    this.term.focus();

    window.addEventListener('resize', () => {
      this.fitAddon.fit();
      this.term.scrollToBottom();
    });
  }

  info() {
    return { columns: this.term.cols, rows: this.term.rows };
  }

  output(data) {
    this.term.write(data);
  }

  showMessage(message, timeout = 2000) {
    this.messageEl.textContent = message;
    if (!this.messageEl.isConnected) {
      this.container.appendChild(this.messageEl);
    }
    if (this.messageTimeout) {
      clearTimeout(this.messageTimeout);
    }
    if (timeout > 0) {
      this.messageTimeout = setTimeout(() => this.removeMessage(), timeout);
    }
  }

  removeMessage() {
    if (this.messageEl.isConnected) {
      this.container.removeChild(this.messageEl);
    }
  }

  setWindowTitle(title) {
    document.title = `${title} - ${this.session}`;
  }

  setPreferences(preferences) {
    if (preferences['font-size']) {
      this.term.options.fontSize = preferences['font-size'];
    }
    if (preferences['font-family']) {
      this.term.options.fontFamily = preferences['font-family'];
    }
  }

  onInput(callback) {
    if (this.onDataHandler) {
      this.onDataHandler.dispose();
    }
    this.onDataHandler = this.term.onData((input) => {
      callback(this.encoder.encode(input));
    });
  }

  onResize(callback) {
    if (this.onResizeHandler) {
      this.onResizeHandler.dispose();
    }
    this.onResizeHandler = this.term.onResize(() => callback(this.term.cols, this.term.rows));
  }

  deactivate() {
    this.term.blur();
    this.onDataHandler?.dispose();
    this.onResizeHandler?.dispose();
  }

  reset() {
    this.removeMessage();
    this.term.clear();
    this.term.focus();
  }

  close() {
    this.term.dispose();
  }
}

function getSessionFromPath() {
  const [_, maybeSession] = window.location.pathname.split('/');
  if (SUPPORTED_SESSIONS.has(maybeSession)) {
    return maybeSession;
  }
  return null;
}

function buildWebsocketUrl(session) {
  const scheme = window.location.protocol === 'https:' ? 'wss' : 'ws';
  return `${scheme}://${window.location.host}/${session}/ws`;
}

function updateConnectionStatus(state, el, reconnectDelay = 0) {
  switch (state) {
    case 'connected':
      el.textContent = 'Connected';
      el.style.color = '#4ade80';
      break;
    case 'reconnecting':
      el.textContent = reconnectDelay > 0 ? `Reconnecting in ${reconnectDelay}s` : 'Reconnecting...';
      el.style.color = '#fbbf24';
      break;
    default:
      el.textContent = 'Disconnected';
      el.style.color = '#f87171';
  }
}

async function init() {
  const session = getSessionFromPath();
  const statusEl = document.getElementById('connection-status');
  const sessionLabel = document.getElementById('session-label');
  const terminalContainer = document.getElementById('terminal');

  if (!session || !terminalContainer) {
    if (statusEl) statusEl.textContent = 'Invalid session';
    return;
  }

  if (sessionLabel) sessionLabel.textContent = session;

  const wsUrl = buildWebsocketUrl(session);
  const term = new XtermTerminal(terminalContainer, session);
  const connectionFactory = new ConnectionFactory(wsUrl, GOTTY_PROTOCOLS);
  let reconnectDelay = 0;

  const tty = new WebTTY(term, connectionFactory, {
    onStatus: (state) => {
      if (state === 'connected') reconnectDelay = 0;
      if (statusEl) updateConnectionStatus(state, statusEl, reconnectDelay);
    },
    onReconnect: (seconds) => {
      reconnectDelay = seconds;
    }
  });

  const close = tty.open();
  initKeypad(tty, term);

  window.addEventListener('beforeunload', () => {
    close();
    term.close();
  });
}

const KEY_MAP = {
  Escape: '\x1b',
  Tab: '\t',
  ArrowUp: '\x1b[A',
  ArrowDown: '\x1b[B',
  ArrowRight: '\x1b[C',
  ArrowLeft: '\x1b[D'
};

function initKeypad(tty, term) {
  const keypad = document.getElementById('keypad');
  const kbToggle = document.getElementById('kb-toggle');
  const mobileInput = document.getElementById('mobile-input');
  if (!keypad) return;

  keypad.addEventListener('click', (e) => {
    const btn = e.target.closest('button');
    if (!btn || btn.id === 'kb-toggle') return;

    let seq;
    if (btn.dataset.key) {
      seq = KEY_MAP[btn.dataset.key] || '';
    } else if (btn.dataset.ctrl) {
      const char = btn.dataset.ctrl.toLowerCase();
      seq = String.fromCharCode(char.charCodeAt(0) - 96);
    }

    if (seq) {
      tty.sendInput(seq);
      term.term.focus();
    }
  });

  if (kbToggle && mobileInput) {
    kbToggle.addEventListener('click', () => {
      mobileInput.focus();
    });

    mobileInput.addEventListener('input', (e) => {
      if (e.target.value) {
        tty.sendInput(e.target.value);
        e.target.value = '';
      }
    });

    mobileInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        tty.sendInput('\r');
        e.preventDefault();
      } else if (e.key === 'Backspace') {
        tty.sendInput('\x7f');
        e.preventDefault();
      }
    });
  }
}

document.addEventListener('DOMContentLoaded', init);
