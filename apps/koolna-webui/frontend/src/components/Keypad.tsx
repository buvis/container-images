import { useRef } from 'react';

const KEY_MAP: Record<string, string> = {
  Escape: '\x1b',
  Tab: '\t',
  ArrowUp: '\x1b[A',
  ArrowDown: '\x1b[B',
  ArrowRight: '\x1b[C',
  ArrowLeft: '\x1b[D',
};

interface KeypadProps {
  onKey: (seq: string) => void;
}

export function Keypad({ onKey }: KeypadProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleButtonClick = (key?: string, ctrl?: string) => {
    let seq = '';
    if (key) {
      seq = KEY_MAP[key] || '';
    } else if (ctrl) {
      const char = ctrl.toLowerCase();
      seq = String.fromCharCode(char.charCodeAt(0) - 96);
    }
    if (seq) {
      onKey(seq);
    }
  };

  const handleKeyboardToggle = () => {
    inputRef.current?.focus();
  };

  const handleMobileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.value) {
      onKey(e.target.value);
      e.target.value = '';
    }
  };

  const handleMobileKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      onKey('\r');
      e.preventDefault();
    } else if (e.key === 'Backspace') {
      onKey('\x7f');
      e.preventDefault();
    }
  };

  return (
    <div className="fixed bottom-0 left-0 right-0 p-2 bg-surface border-t border-gray-800 touch-manipulation md:hidden">
      <input
        ref={inputRef}
        type="text"
        className="opacity-0 absolute pointer-events-none"
        onInput={handleMobileInput}
        onKeyDown={handleMobileKeyDown}
        autoComplete="off"
        autoCapitalize="off"
        autoCorrect="off"
      />
      <div className="grid grid-cols-7 gap-1">
        <KeyButton onClick={() => handleButtonClick('Escape')}>Esc</KeyButton>
        <KeyButton onClick={() => handleButtonClick('Tab')}>Tab</KeyButton>
        <KeyButton onClick={() => handleButtonClick(undefined, 'c')}>^C</KeyButton>
        <KeyButton onClick={() => handleButtonClick(undefined, 'd')}>^D</KeyButton>
        <KeyButton onClick={() => handleButtonClick('ArrowUp')}>↑</KeyButton>
        <KeyButton onClick={() => handleButtonClick('ArrowDown')}>↓</KeyButton>
        <KeyButton onClick={handleKeyboardToggle}>⌨</KeyButton>
        <KeyButton onClick={() => handleButtonClick('ArrowLeft')}>←</KeyButton>
        <KeyButton onClick={() => handleButtonClick('ArrowRight')}>→</KeyButton>
      </div>
    </div>
  );
}

function KeyButton({ children, onClick }: { children: React.ReactNode; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="bg-gray-800 hover:bg-gray-700 active:bg-gray-600 text-gray-200 font-mono text-sm py-2 px-1 rounded transition-colors"
    >
      {children}
    </button>
  );
}
