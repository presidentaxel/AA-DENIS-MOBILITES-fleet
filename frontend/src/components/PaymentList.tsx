type Payment = { id?: string; occurred_at?: string; amount?: number; currency?: string; description?: string };

type Props = {
  payments: Payment[];
};

export function PaymentList({ payments }: Props) {
  if (!payments.length) return <div>Aucun paiement.</div>;
  return (
    <table>
      <thead>
        <tr>
          <th>Date</th>
          <th>Montant</th>
          <th>Devise</th>
          <th>Description</th>
        </tr>
      </thead>
      <tbody>
        {payments.map((p) => (
          <tr key={p.id}>
            <td>{p.occurred_at}</td>
            <td>{p.amount}</td>
            <td>{p.currency}</td>
            <td>{p.description}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

