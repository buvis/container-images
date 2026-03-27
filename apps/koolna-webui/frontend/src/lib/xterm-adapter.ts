import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import { WebLinksAddon } from '@xterm/addon-web-links';
import { WebglAddon } from '@xterm/addon-webgl';

export class XtermAdapter {
  readonly term: Terminal;
  private fitAddon: FitAddon;

  private constructor(container: HTMLElement) {
    this.fitAddon = new FitAddon();
    const weblinksAddon = new WebLinksAddon();

    this.term = new Terminal({
      allowProposedApi: true,
      customGlyphs: true,
      theme: {
        background: '#05060a',
        foreground: '#f5f5f5',
        cursor: '#38bdf8',
        selectionBackground: '#1d4ed8',
      },
      cursorBlink: true,
      fontSize: 14,
      fontFamily: "'MesloLGS NF', 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace",
    });

    this.term.loadAddon(this.fitAddon);
    this.term.loadAddon(weblinksAddon);

    this.term.open(container);

    try {
      this.term.loadAddon(new WebglAddon());
    } catch {
      // WebGL not available, DOM renderer used
    }

    this.fitAddon.fit();
    this.term.focus();

    window.addEventListener('resize', this.handleResize);
  }

  static async create(container: HTMLElement): Promise<XtermAdapter> {
    await document.fonts.ready;
    return new XtermAdapter(container);
  }

  setupOSC52Clipboard(): void {
    this.term.parser.registerOscHandler(52, (data: string) => {
      const parts = data.split(';');
      const b64 = parts.length > 1 ? parts[parts.length - 1] : parts[0];
      if (b64) {
        try {
          const bytes = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
          const text = new TextDecoder().decode(bytes);
          navigator.clipboard.writeText(text).catch(() => {});
        } catch {
          // invalid base64 — ignore
        }
      }
      return true;
    });
  }

  private handleResize = () => {
    this.fitAddon.fit();
    this.term.scrollToBottom();
  };

  info(): { columns: number; rows: number } {
    return { columns: this.term.cols, rows: this.term.rows };
  }

  dispose(): void {
    window.removeEventListener('resize', this.handleResize);
    this.term.dispose();
  }
}
