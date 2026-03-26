import React, { useState, useEffect } from "react";
import { useTranslation } from 'react-i18next';

export default function LangSwitcher() {
  const { i18n } = useTranslation();
  const [lang, setLang] = useState(i18n.language || 'en');

  useEffect(() => {
    const handleLanguageChanged = (lng) => {
      setLang(lng);
    };
    i18n.on('languageChanged', handleLanguageChanged);
    return () => i18n.off('languageChanged', handleLanguageChanged);
  }, [i18n]);

  const toggle = () => {
    const next = lang === 'en' ? 'hi' : 'en';
    i18n.changeLanguage(next);
    localStorage.setItem('lang', next);
  };

  return (
    <button
      onClick={toggle}
      title={lang === 'en' ? 'Switch to Hindi' : 'Switch to English'}
      style={{
        background: 'var(--bg3)',
        border: '1px solid var(--border)',
        borderRadius: 6,
        padding: '4px 10px',
        fontSize: 12,
        fontWeight: 700,
        color: 'var(--text2)',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        transition: 'all 0.2s',
      }}
    >
      {lang === 'en' ? '🇮🇳 हिन्दी' : '🇬🇧 English'}
    </button>
  );
}