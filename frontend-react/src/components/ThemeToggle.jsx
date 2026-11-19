import { useState } from 'react';

function initialTheme() {
  return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
}

export default function ThemeToggle() {
  const [theme, setTheme] = useState(initialTheme);
  const dark = theme === 'dark';

  function toggle() {
    const next = dark ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try {
      localStorage.setItem('theme', next);
    } catch {
      /* si el navegador bloquea el almacenamiento, el cambio vale solo para esta visita */
    }
    setTheme(next);
  }

  return (
    <button type="button" role="switch" aria-checked={dark} aria-label="Modo oscuro" className="theme-switch" onClick={toggle}>
      <span aria-hidden="true">{dark ? 'Modo oscuro' : 'Modo claro'}</span>
      <span className="knob" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="20" height="20" focusable="false">
          {dark ? (
            <>
              <path d="M17 14.2A7 7 0 0 1 8.3 5.5 7.4 7.4 0 1 0 17 14.2z" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
              <path d="M17.5 3l.6 1.6 1.6.6-1.6.6-.6 1.6-.6-1.6-1.6-.6 1.6-.6z" fill="currentColor" />
              <path d="M21 9.5l.4 1 1 .4-1 .4-.4 1-.4-1-1-.4 1-.4z" fill="currentColor" />
            </>
          ) : (
            <>
              <circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" strokeWidth="2" />
              <path
                d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </>
          )}
        </svg>
      </span>
    </button>
  );
}