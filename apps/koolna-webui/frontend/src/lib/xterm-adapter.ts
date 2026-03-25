import { Terminal } from 'xterm';
import { CanvasAddon } from 'xterm-addon-canvas';
import { FitAddon } from 'xterm-addon-fit';
import { Unicode11Addon } from 'xterm-addon-unicode11';
import { WebLinksAddon } from 'xterm-addon-web-links';
import { WebglAddon } from 'xterm-addon-webgl';

export class XtermAdapter {
  readonly term: Terminal;
  private fitAddon: FitAddon;

  private constructor(container: HTMLElement) {
    this.fitAddon = new FitAddon();
    const weblinksAddon = new WebLinksAddon();

    this.term = new Terminal({
      allowProposedApi: true,
      allowTransparency: true,
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

    const unicode11Addon = new Unicode11Addon();
    this.term.loadAddon(this.fitAddon);
    this.term.loadAddon(unicode11Addon);
    this.term.unicode.activeVersion = '11';
    this.term.loadAddon(weblinksAddon);

    this.term.open(container);

    // customGlyphs only works with canvas/webgl, not DOM renderer
    // Try WebGL first, fall back to canvas
    let renderer = 'dom';
    try {
      this.term.loadAddon(new WebglAddon());
      renderer = 'webgl';
    } catch (e) {
      console.warn('[koolna] WebGL failed, trying canvas:', e);
      try {
        this.term.loadAddon(new CanvasAddon());
        renderer = 'canvas';
      } catch (e2) {
        console.warn('[koolna] Canvas failed, using DOM:', e2);
      }
    }

    const opts = this.term.options;
    console.log('[koolna] terminal diagnostics:', {
      renderer,
      customGlyphs: opts.customGlyphs,
      allowTransparency: opts.allowTransparency,
      fontFamily: opts.fontFamily,
      fontSize: opts.fontSize,
      cols: this.term.cols,
      rows: this.term.rows,
    });

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
