import React from 'react';

// Cadre visuel commun a toutes les pages du portail : logo, titre, carte
// centree. Garde le portail sobre et coherent quel que soit le type de
// connexion en cours.
export default function PortalLayout({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md rounded-xl bg-white p-8 shadow-lg">
        <div className="mb-6 text-center">
          <h1 className="text-2xl font-bold text-telix-dark">Telix Secure Pro</h1>
          <p className="mt-1 text-sm text-gray-500">Portail d'acces Wi-Fi securise</p>
        </div>
        <h2 className="mb-1 text-lg font-semibold text-gray-800">{title}</h2>
        {subtitle && <p className="mb-4 text-sm text-gray-500">{subtitle}</p>}
        {children}
      </div>
    </div>
  );
}
