// Logo mapping for platforms
// Placeholder images - replace with actual logos later

export const platformLogos: Record<string, string> = {
  bolt: "/assets/logos/bolt.png",
  uber: "/assets/logos/uber.png",
  heetch: "/assets/logos/heetch.png",
  freenow: "/assets/logos/freenow.png",
  hub: "/assets/logos/hub.png",
  yango: "/assets/logos/yango.png",
};

export const getPlatformLogo = (platform: string): string => {
  const normalized = platform.toLowerCase();
  return platformLogos[normalized] || "/assets/logos/default.png";
};

export const getPlatformColor = (platform: string): string => {
  const colors: Record<string, string> = {
    bolt: "#00D9A5", // Vert Bolt
    uber: "#000000", // Noir Uber
    heetch: "#FF6E9D", // Rose Heetch
    freenow: "#FF0000", // Rouge FreeNow
    hub: "#FF6B35", // Orange Hub
    yango: "#FFD700", // Or Yango
  };
  return colors[platform.toLowerCase()] || "#6B7280";
};

