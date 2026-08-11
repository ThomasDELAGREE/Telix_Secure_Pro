import React, { createContext, useContext, useMemo } from 'react';

// Parametres transmis par l'equipement Wi-Fi (controleur/borne) au moment de
// la redirection vers le portail captif. Le format exact (nom des parametres)
// depend du constructeur (Unifi, Cisco, Aruba, Ruckus, MikroTik...) -- voir
// ADR-005 et docs/captive-portal.md pour le detail des hypotheses retenues.
//
// IMPORTANT : un navigateur ne peut PAS lire l'adresse MAC d'un appareil pour
// des raisons de securite. Elle ne peut venir que de l'equipement Wi-Fi
// lui-meme, via l'URL de redirection (query params ci-dessous).
export interface WifiParams {
  macAddress: string | null;
  clientIp: string | null;
  apMac: string | null;
  ssid: string | null;
}

const WifiParamsContext = createContext<WifiParams>({
  macAddress: null,
  clientIp: null,
  apMac: null,
  ssid: null,
});

// Alias de parametres connus, tolerants aux variations entre constructeurs.
// Ordre de priorite : le premier trouve dans l'URL est retenu.
const MAC_PARAM_ALIASES = ['mac', 'client_mac', 'clientMac', 'user_mac'];
const IP_PARAM_ALIASES = ['ip', 'client_ip', 'clientIp'];
const AP_MAC_PARAM_ALIASES = ['ap_mac', 'apMac', 'gw_id'];
const SSID_PARAM_ALIASES = ['ssid'];

function firstMatch(searchParams: URLSearchParams, aliases: string[]): string | null {
  for (const key of aliases) {
    const value = searchParams.get(key);
    if (value) return value;
  }
  return null;
}

// Normalise une adresse MAC vers le format aa:bb:cc:dd:ee:ff, quel que soit le
// separateur d'origine (-, ., ou aucun). Coherent avec la normalisation deja
// appliquee cote auth-service (voir ADR-005).
function normalizeMac(raw: string | null): string | null {
  if (!raw) return null;
  const hex = raw.replace(/[^a-fA-F0-9]/g, '');
  if (hex.length !== 12) return raw.toLowerCase();
  return hex.toLowerCase().match(/.{1,2}/g)!.join(':');
}

export function WifiParamsProvider({ children }: { children: React.ReactNode }) {
  const value = useMemo<WifiParams>(() => {
    const searchParams = new URLSearchParams(window.location.search);
    return {
      macAddress: normalizeMac(firstMatch(searchParams, MAC_PARAM_ALIASES)),
      clientIp: firstMatch(searchParams, IP_PARAM_ALIASES),
      apMac: normalizeMac(firstMatch(searchParams, AP_MAC_PARAM_ALIASES)),
      ssid: firstMatch(searchParams, SSID_PARAM_ALIASES),
    };
  }, []);

  return <WifiParamsContext.Provider value={value}>{children}</WifiParamsContext.Provider>;
}

export function useWifiParams(): WifiParams {
  return useContext(WifiParamsContext);
}
