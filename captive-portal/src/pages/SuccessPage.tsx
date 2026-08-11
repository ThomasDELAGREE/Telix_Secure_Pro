import { useEffect, useState } from 'react';
import PortalLayout from '../components/PortalLayout';

// Page finale : confirme l'acces Wi-Fi accorde. Dans un deploiement reel,
// l'equipement Wi-Fi (controleur) est celui qui autorise effectivement le
// trafic une fois le token recu -- cette page est purement informative pour
// l'utilisateur final.
export default function SuccessPage() {
  const [displayName, setDisplayName] = useState<string | null>(null);

  useEffect(() => {
    setDisplayName(sessionStorage.getItem('telix_display_name'));
  }, []);

  return (
    <PortalLayout title="Connexion reussie">
      <div className="text-center">
        <div className="mb-4 text-5xl">✅</div>
        <p className="text-gray-700">
          {displayName ? `Bienvenue, ${displayName} !` : 'Bienvenue !'}
        </p>
        <p className="mt-2 text-sm text-gray-500">
          Vous disposez maintenant d'un acces a Internet. Bonne navigation.
        </p>
      </div>
    </PortalLayout>
  );
}
