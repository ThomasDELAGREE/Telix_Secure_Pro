import { Link } from 'react-router-dom';
import PortalLayout from '../components/PortalLayout';

// Page d'accueil du portail : l'utilisateur choisit son type de connexion.
// C'est la premiere page vue apres la redirection de l'equipement Wi-Fi.
export default function LoginChoicePage() {
  return (
    <PortalLayout title="Comment souhaitez-vous vous connecter ?">
      <div className="space-y-3">
        <Link
          to="/corporate"
          className="block w-full rounded-md bg-telix px-4 py-3 text-center font-medium text-white transition hover:bg-telix-dark"
        >
          Je suis un collaborateur (annuaire d'entreprise)
        </Link>
        <Link
          to="/visitor/sms"
          className="block w-full rounded-md border border-telix px-4 py-3 text-center font-medium text-telix transition hover:bg-telix-light"
        >
          Je suis un visiteur (code par SMS)
        </Link>
        <Link
          to="/visitor/room"
          className="block w-full rounded-md border border-gray-300 px-4 py-3 text-center font-medium text-gray-700 transition hover:bg-gray-50"
        >
          J'ai un code de chambre
        </Link>
      </div>
    </PortalLayout>
  );
}
