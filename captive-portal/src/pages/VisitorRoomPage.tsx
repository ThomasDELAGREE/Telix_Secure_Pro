import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import PortalLayout from '../components/PortalLayout';
import ErrorBanner from '../components/ErrorBanner';
import { useWifiParams } from '../context/WifiParamsContext';
import { loginRoom, extractErrorMessage } from '../api/authClient';

// Authentification visiteur par numero de chambre + code d'acces, pensee
// pour un deploiement hotelier (voir ADR-005 : identifiant de type
// 'room_number'). Le provisionnement des codes reste manuel pour l'instant
// (pas d'integration PMS a ce stade).
export default function VisitorRoomPage() {
  const navigate = useNavigate();
  const { macAddress } = useWifiParams();
  const [roomNumber, setRoomNumber] = useState('');
  const [accessCode, setAccessCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await loginRoom({ room_number: roomNumber, access_code: accessCode, mac_address: macAddress });
      sessionStorage.setItem('telix_display_name', `Chambre ${roomNumber}`);
      navigate('/success');
    } catch (err) {
      setError(extractErrorMessage(err, 'Numero de chambre ou code invalide.'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <PortalLayout title="Connexion par code de chambre" subtitle="Renseignez le code fourni a votre arrivee.">
      <ErrorBanner message={error} />
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Numero de chambre</label>
          <input
            type="text"
            required
            value={roomNumber}
            onChange={(e) => setRoomNumber(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-telix focus:outline-none"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Code d'acces</label>
          <input
            type="text"
            required
            value={accessCode}
            onChange={(e) => setAccessCode(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-telix focus:outline-none"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-telix px-4 py-2 font-medium text-white transition hover:bg-telix-dark disabled:opacity-50"
        >
          {loading ? 'Verification...' : 'Se connecter'}
        </button>
      </form>
    </PortalLayout>
  );
}
