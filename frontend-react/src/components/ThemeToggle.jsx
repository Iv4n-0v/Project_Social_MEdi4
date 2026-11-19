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
      <span className="track" aria-hidden="true"><span className="knob" /></span>
      <span aria-hidden="true">Modo oscuro</span>
    </button>
  );
}