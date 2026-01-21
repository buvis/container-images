import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import { WebLinksAddon } from 'xterm-addon-web-links';
import type { TerminalInterface } from './webtty';

export class XtermAdapter implements TerminalInterface {
  readonly term: Terminal;
  private fitAddon: FitAddon;
  private encoder = new TextEncoder();
  private onDataHandler?: { dispose(): void };
  private onResizeHandler?: { dispose(): void };
  private messageEl: HTMLDivElement;
  private messageTimeout?: ReturnType<typeof setTimeout>;

  constructor(
    private container: HTMLElement,
    private session: string
  ) {
    this.fitAddon = new FitAddon();
    const weblinksAddon = new WebLinksAddon();

    this.term = new Terminal({
      allowProposedApi: true,
      theme: {
        background: '#05060a',
        foreground: '#f5f5f5',
        cursor: '#38bdf8',
        selectionBackground: '#1d4ed8',
      },
      cursorBlink: true,
      fontSize: 14,
      fontFamily: "'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace",
    });

    this.term.loadAddon(this.fitAddon);
    this.term.loadAddon(weblinksAddon);

    this.messageEl = document.createElement('div');
    this.messageEl.className = 'xterm-overlay';

    this.term.open(container);
    this.fitAddon.fit();
    this.term.focus();

    window.addEventListener('resize', this.handleResize);
  }

  private handleResize = () => {
    this.fitAddon.fit();
    this.term.scrollToBottom();
  };

  info(): { columns: number; rows: number } {
    return { columns: this.term.cols, rows: this.term.rows };
  }

  output(data: Uint8Array): void {
    this.term.write(data);
  }

  showMessage(message: string, timeout = 2000): void {
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

  private removeMessage(): void {
    if (this.messageEl.isConnected) {
      this.container.removeChild(this.messageEl);
    }
  }

  setWindowTitle(title: string): void {
    document.title = `${title} - ${this.session}`;
  }

  setPreferences(preferences: Record<string, unknown>): void {
    if (preferences['font-size'] && typeof preferences['font-size'] === 'number') {
      this.term.options.fontSize = preferences['font-size'];
    }
    if (preferences['font-family'] && typeof preferences['font-family'] === 'string') {
      this.term.options.fontFamily = preferences['font-family'];
    }
  }

  onInput(callback: (input: Uint8Array) => void): void {
    this.onDataHandler?.dispose();
    this.onDataHandler = this.term.onData((input) => {
      callback(this.encoder.encode(input));
    });
  }

  onResize(callback: (cols: number, rows: number) => void): void {
    this.onResizeHandler?.dispose();
    this.onResizeHandler = this.term.onResize(() => callback(this.term.cols, this.term.rows));
  }

  deactivate(): void {
    this.term.blur();
    this.onDataHandler?.dispose();
    this.onResizeHandler?.dispose();
  }

  reset(): void {
    this.removeMessage();
    this.term.clear();
    this.term.focus();
  }

  dispose(): void {
    window.removeEventListener('resize', this.handleResize);
    this.term.dispose();
  }
}
