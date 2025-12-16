/**
 * Calculate performance scores based on driver orders and activity
 */

export type PerformanceScores = {
  incomeScore: number; // 0-100
  workingEfficiencyScore: number; // 0-100
  workingSustainabilityScore: number; // 0-100
  overallPerformanceScore: number; // 0-100
};

export function calculatePerformanceScores(orders: any[], driverId: string): PerformanceScores {
  const driverOrders = orders.filter((o: any) => o.driver_uuid === driverId);
  
  if (driverOrders.length === 0) {
    return {
      incomeScore: 0,
      workingEfficiencyScore: 0,
      workingSustainabilityScore: 0,
      overallPerformanceScore: 0,
    };
  }

  // Calculate metrics
  const totalNetEarnings = driverOrders.reduce((sum, o) => sum + (o.net_earnings || 0), 0);
  const totalDistance = driverOrders.reduce((sum, o) => sum + (o.ride_distance || 0), 0);
  const totalTrips = driverOrders.length;
  
  // Time on trips (in hours)
  let totalTimeHours = 0;
  driverOrders.forEach((o: any) => {
    if (o.order_pickup_timestamp && o.order_drop_off_timestamp) {
      const timeSeconds = o.order_drop_off_timestamp - o.order_pickup_timestamp;
      totalTimeHours += timeSeconds / 3600;
    }
  });
  
  // Completed trips
  const completedTrips = driverOrders.filter((o: any) => 
    o.order_status && o.order_status.toLowerCase().includes("finished")
  ).length;
  
  const cancelledTrips = totalTrips - completedTrips;
  const completionRate = totalTrips > 0 ? (completedTrips / totalTrips) * 100 : 0;
  
  // Income Score (0-100)
  // Based on net earnings per trip compared to a target (e.g., €15 per trip average)
  const avgEarningsPerTrip = totalTrips > 0 ? totalNetEarnings / totalTrips : 0;
  const targetEarningsPerTrip = 15; // Target: €15 per trip
  const incomeScore = Math.min(100, Math.max(0, (avgEarningsPerTrip / targetEarningsPerTrip) * 100));
  
  // Working Efficiency Score (0-100)
  // Based on trips per hour and completion rate
  const tripsPerHour = totalTimeHours > 0 ? totalTrips / totalTimeHours : 0;
  const targetTripsPerHour = 2.0; // Target: 2 trips per hour
  const efficiencyFromTripsPerHour = Math.min(100, (tripsPerHour / targetTripsPerHour) * 100);
  const efficiencyFromCompletion = completionRate;
  const workingEfficiencyScore = (efficiencyFromTripsPerHour * 0.6) + (efficiencyFromCompletion * 0.4);
  
  // Working Sustainability Score (0-100)
  // Based on consistency: cancellation rate and activity spread
  const cancellationRate = totalTrips > 0 ? (cancelledTrips / totalTrips) * 100 : 0;
  const sustainabilityFromCancellation = Math.max(0, 100 - cancellationRate * 2); // Penalty for cancellations
  
  // Check activity spread (working on multiple days)
  const uniqueDays = new Set(
    driverOrders
      .filter((o: any) => o.order_created_timestamp)
      .map((o: any) => {
        const date = new Date(o.order_created_timestamp * 1000);
        return `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
      })
  ).size;
  
  const targetDays = 20; // Target: active on 20 different days
  const sustainabilityFromActivity = Math.min(100, (uniqueDays / targetDays) * 100);
  
  const workingSustainabilityScore = (sustainabilityFromCancellation * 0.7) + (sustainabilityFromActivity * 0.3);
  
  // Overall Performance Score
  // Weighted average of all scores
  const overallPerformanceScore = (
    incomeScore * 0.4 +
    workingEfficiencyScore * 0.3 +
    workingSustainabilityScore * 0.3
  );
  
  return {
    incomeScore: Math.round(incomeScore),
    workingEfficiencyScore: Math.round(workingEfficiencyScore),
    workingSustainabilityScore: Math.round(workingSustainabilityScore),
    overallPerformanceScore: Math.round(overallPerformanceScore),
  };
}

