import React from "react";

type PlatformLogoProps = {
  platform: string;
  size?: number;
};

export function PlatformLogo({ platform, size = 32 }: PlatformLogoProps) {
  const normalized = platform.toLowerCase();
  
  // Logos SVG pour les plateformes qui en ont
  const platformLogos: Record<string, string> = {
    bolt: "/assets/logos/bolt.svg",
    uber: "/assets/logos/uber.svg",
  };

  // Colors for other platforms
  const platformStyles: Record<string, { bg: string; text: string; label: string }> = {
    heetch: { bg: "#FF6E9D", text: "#FFFFFF", label: "H" },
    freenow: { bg: "#FF0000", text: "#FFFFFF", label: "V" },
    hub: { bg: "#FF6B35", text: "#FFFFFF", label: "Hub" },
    yango: { bg: "#FFD700", text: "#000000", label: "Y" },
  };

  // Si la plateforme a un logo SVG, l'utiliser
  if (platformLogos[normalized]) {
    return (
      <img
        src={platformLogos[normalized]}
        alt={platform}
        className="platform-logo"
        style={{
          width: size,
          height: size,
          marginRight: "6px",
          flexShrink: 0,
          objectFit: "contain",
        }}
        title={platform}
      />
    );
  }

  // Sinon, utiliser le style par défaut avec couleurs
  const style = platformStyles[normalized] || {
    bg: "#6B7280",
    text: "#FFFFFF",
    label: normalized.charAt(0).toUpperCase(),
  };

  return (
    <div
      className="platform-logo"
      style={{
        width: size,
        height: size,
        borderRadius: "50%",
        backgroundColor: style.bg,
        color: style.text,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        fontSize: size * 0.4,
        fontWeight: "bold",
        marginRight: "6px",
        flexShrink: 0,
      }}
      title={platform}
    >
      {style.label.length > 3 ? style.label.slice(0, 3) : style.label}
    </div>
  );
}

