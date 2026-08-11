import React from 'react';

// Composant partage pour afficher un message d'erreur de maniere coherente
// sur tous les formulaires du portail.
export default function ErrorBanner({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <div className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
      {message}
    </div>
  );
}
