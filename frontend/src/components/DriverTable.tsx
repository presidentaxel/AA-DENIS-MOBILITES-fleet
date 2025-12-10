type Driver = { uuid?: string; name?: string; email?: string };

type Props = {
  drivers: Driver[];
  selected?: string | null;
  onSelect?: (uuid: string) => void;
};

export function DriverTable({ drivers, selected, onSelect }: Props) {
  if (!drivers.length) return <div>No drivers yet.</div>;
  return (
    <table>
      <thead>
        <tr>
          <th>UUID</th>
          <th>Name</th>
          <th>Email</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {drivers.map((d, idx) => (
          <tr key={d.uuid || idx} style={{ background: selected === d.uuid ? "#eef" : "transparent" }}>
            <td>{d.uuid}</td>
            <td>{d.name}</td>
            <td>{d.email}</td>
            <td>
              {onSelect && d.uuid && <button onClick={() => onSelect(d.uuid)}>Voir</button>}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

