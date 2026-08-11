import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import PortalLayout from '../components/PortalLayout';
import ErrorBanner from '../components/ErrorBanner';
import { useWifiParams } from '../context/WifiParamsContext';
import { requestOtp, verifyOtp, extractErrorMessage } from '../api/authClient';

// Authentification visiteur en deux temps : demande d'un code OTP par SMS,
// puis verification de ce code. Le numero de telephone saisi devient
// l'identifiant de tracabilite de la session (voir ADR-005).
export default function VisitorSmsPage() {
  const navigate = useNavigate();
  const { macAddress } = useWifiParams();
  const [step, setStep] = useState<'phone' | 'code'>('phone');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [code, setCode] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleRequestOtp(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await requestOtp({ phone_number: phoneNumber, mac_address: macAddress });
      setStep('code');
    } catch (err) {
      setError(extractErrorMessage(err, "Impossible d'envoyer le code. Verifiez le numero saisi."));
    } finally {
      setLoading(false);
    }
  }

  async function handleVerifyOtp(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await verifyOtp({ phone_number: phoneNumber, code, mac_address: macAddress });
      sessionStorage.setItem('telix_display_name', phoneNumber);
      navigate('/success');
    } catch (err) {
      setError(extractErrorMessage(err, 'Code invalide ou expire.'));
    } finally {
      setLoading(false);
    }
  }

  if (step === 'phone') {
    return (
      <PortalLayout title="Connexion visiteur" subtitle="Recevez un code d'acces par SMS.">
        <ErrorBanner message={error} />
        <form onSubmit={handleRequestOtp} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Numero de telephone</label>
            <input
              type="tel"
              required
              placeholder="+33612345678"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-telix focus:outline-none"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-telix px-4 py-2 font-medium text-white transition hover:bg-telix-dark disabled:opacity-50"
          >
            {loading ? 'Envoi...' : 'Recevoir le code'}
          </button>
        </form>
      </PortalLayout>
    );
  }

  return (
    <PortalLayout title="Entrez votre code" subtitle={`Code envoye au ${phoneNumber}.`}>
      <ErrorBanner message={error} />
      <form onSubmit={handleVerifyOtp} className="space-y-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Code recu par SMS</label>
          <input
            type="text"
            required
            inputMode="numeric"
            maxLength={6}
            value={code}
            onChange={(e) => setCode(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-center text-lg tracking-widest focus:border-telix focus:outline-none"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-telix px-4 py-2 font-medium text-white transition hover:bg-telix-dark disabled:opacity-50"
        >
          {loading ? 'Verification...' : 'Valider'}
        </button>
        <button
          type="button"
          onClick={() => setStep('phone')}
          className="w-full text-sm text-gray-500 hover:underline"
        >
          Changer de numero
        </button>
      </form>
    </PortalLayout>
  );
}
