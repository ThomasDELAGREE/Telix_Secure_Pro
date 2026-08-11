import { useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import PortalLayout from '../components/PortalLayout';
import ErrorBanner from '../components/ErrorBanner';
import { useWifiParams } from '../context/WifiParamsContext';
import { loginCorporate, extractErrorMessage } from '../api/authClient';

// Authentification corporate : l'utilisateur choisit explicitement son
// fournisseur d'identite (LDAP/AD local ou Azure AD), l'API auth-service
// tente ensuite l'authentification correspondante.
export default function CorporateLoginPage() {
  const navigate = useNavigate();
  const { macAddress } = useWifiParams();
  const [provider, setProvider] = useState<'ldap' | 'azure_ad'>('ldap');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const response = await loginCorporate({
        username,
        password,
        auth_provider: provider,
        mac_address: macAddress,
      });
      sessionStorage.setItem('telix_display_name', response.display_name ?? username);
      navigate('/success');
    } catch (err) {
      setError(extractErrorMessage(err, 'Identifiants incorrects ou compte inaccessible.'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <PortalLayout
      title="Connexion collaborateur"
      subtitle="Utilisez vos identifiants d'entreprise habituels."
    >
      <ErrorBanner message={error} />
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setProvider('ldap')}
            className={`flex-1 rounded-md border px-3 py-2 text-sm font-medium ${
              provider === 'ldap' ? 'border-telix bg-telix-light text-telix-dark' : 'border-gray-300 text-gray-600'
            }`}
          >
            Annuaire local (AD)
          </button>
          <button
            type="button"
            onClick={() => setProvider('azure_ad')}
            className={`flex-1 rounded-md border px-3 py-2 text-sm font-medium ${
              provider === 'azure_ad' ? 'border-telix bg-telix-light text-telix-dark' : 'border-gray-300 text-gray-600'
            }`}
          >
            Azure AD
          </button>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Identifiant</label>
          <input
            type="text"
            required
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-telix focus:outline-none"
            autoComplete="username"
          />
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Mot de passe</label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 focus:border-telix focus:outline-none"
            autoComplete="current-password"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-telix px-4 py-2 font-medium text-white transition hover:bg-telix-dark disabled:opacity-50"
        >
          {loading ? 'Connexion...' : 'Se connecter'}
        </button>
      </form>
    </PortalLayout>
  );
}
