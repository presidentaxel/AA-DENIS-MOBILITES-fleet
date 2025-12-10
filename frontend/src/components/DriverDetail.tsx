type Props = {
  driver?: { uuid?: string; name?: string; email?: string };
};

export function DriverDetail({ driver }: Props) {
  if (!driver) return <div>Sélectionnez un chauffeur.</div>;
  return (
    <div>
      <h3>Détails chauffeur</h3>
      <p>UUID: {driver.uuid}</p>
      <p>Nom: {driver.name}</p>
      <p>Email: {driver.email}</p>
    </div>
  );
}

