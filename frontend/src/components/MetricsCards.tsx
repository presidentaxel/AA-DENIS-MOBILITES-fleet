type Metric = { day: string; trips: number; online_hours: number; on_trip_hours: number; earnings: number };

type Props = {
  metrics: Metric[];
};

export function MetricsCards({ metrics }: Props) {
  if (!metrics.length) return <div>Aucune métrique.</div>;
  const latest = metrics[0];
  return (
    <div style={{ display: "flex", gap: 12 }}>
      <div>Jour: {latest.day}</div>
      <div>Courses: {latest.trips}</div>
      <div>Heures online: {latest.online_hours}</div>
      <div>Heures en course: {latest.on_trip_hours}</div>
      <div>Gain: {latest.earnings}</div>
    </div>
  );
}

