import { describe, it, expect } from 'vitest';

// On teste ici uniquement la logique pure de normalisation MAC, extraite du
// contexte WifiParamsContext.tsx pour rester testable sans rendu React.
function normalizeMac(raw: string | null): string | null {
  if (!raw) return null;
  const hex = raw.replace(/[^a-fA-F0-9]/g, '');
  if (hex.length !== 12) return raw.toLowerCase();
  return hex.toLowerCase().match(/.{1,2}/g)!.join(':');
}

describe('normalizeMac', () => {
  it('normalise une MAC separee par des tirets', () => {
    expect(normalizeMac('AA-BB-CC-DD-EE-FF')).toBe('aa:bb:cc:dd:ee:ff');
  });

  it('normalise une MAC separee par des points (format Cisco)', () => {
    expect(normalizeMac('AABB.CCDD.EEFF')).toBe('aa:bb:cc:dd:ee:ff');
  });

  it('normalise une MAC sans separateur', () => {
    expect(normalizeMac('aabbccddeeff')).toBe('aa:bb:cc:dd:ee:ff');
  });

  it('retourne null si aucune valeur fournie', () => {
    expect(normalizeMac(null)).toBeNull();
  });

  it('retourne la valeur en minuscule si le format est inattendu', () => {
    expect(normalizeMac('NOT-A-MAC')).toBe('not-a-mac');
  });
});
