import React, { useEffect, useState, useRef } from "react";
import { RiBook3Line } from "react-icons/ri";
import { FiLogOut } from "react-icons/fi";
import { getBoltDrivers, getBoltOrders, getMe } from "../api/fleetApi";
import "../styles/overview-page.css";

type OverviewPageProps = {
  token: string;
  onLogout: () => void;
};

type OverviewStats = {
  connectedUsers: number | null;
  workingUsers: number | null;
  grossEarnings: number | null;
};

const knowledgeBaseCards = [
  {
    title: "Personnaliser Connect avec les SDKs",
    description: "Créez votre personnalisation Connect pour décider facilement de l'apparence de Connect dans votre application ou site web.",
    link: "https://developers.getrollee.com/docs/connect-sdk",
    imageAlt: "Personnalisation Connect",
    image: "/assets/images/CustomizeConnectwithSDKs.svg",
  },
  {
    title: "Documentation développeur",
    description: "Explorez Rollee Connect et découvrez ce à quoi vous attendre lorsque les utilisateurs connectent leurs comptes professionnels.",
    link: "https://developers.getrollee.com/docs",
    imageAlt: "Documentation développeur",
    image: "/assets/images/DeveloperDocumentation.svg",
  },
  {
    title: "Recettes",
    description: "Cette recette vous guide à travers trois étapes simples qui vous permettront d'utiliser Rollee Connect.",
    link: "https://developers.getrollee.com/recipes",
    imageAlt: "Recettes Rollee",
    image: "/assets/images/Recipes.svg",
  },
  {
    title: "Couverture des plateformes",
    description: "Nous avons construit une couverture de plateformes sur toutes les principales plateformes pour que vous puissiez vous concentrer sur la construction de votre produit.",
    link: "#",
    imageAlt: "Couverture des plateformes",
    image: "/assets/images/PlatformCoverage.svg",
  },
];

const formatNumber = (value: number | null, options?: Intl.NumberFormatOptions) => {
  if (value === null || Number.isNaN(value)) {
    return "--";
  }
  return new Intl.NumberFormat("en-US", options).format(value);
};

const getInitials = (email: string | null | undefined): string => {
  if (!email) return "U";
  const parts = email.split("@")[0].split(/[._-]/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return email.substring(0, 2).toUpperCase();
};

export function OverviewPage({ token, onLogout }: OverviewPageProps) {
  const [stats, setStats] = useState<OverviewStats>({
    connectedUsers: null,
    workingUsers: null,
    grossEarnings: null,
  });
  const [loading, setLoading] = useState(true);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const profileMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function loadUser() {
      try {
        const user = await getMe(token);
        setUserEmail(user?.email || null);
      } catch (err) {
        console.error("Erreur chargement utilisateur:", err);
      }
    }
    loadUser();
  }, [token]);

  const [allOrders, setAllOrders] = useState<any[]>([]);
  const [allDrivers, setAllDrivers] = useState<any[]>([]);

  useEffect(() => {
    async function loadStats() {
      setLoading(true);
      try {
        const [drivers, orders] = await Promise.all([
          getBoltDrivers(token, { limit: 200 }).catch(() => []),
          getBoltOrders(
            token,
            new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10),
            new Date().toISOString().slice(0, 10)
          ).catch(() => []),
        ]);

        setAllOrders(orders);
        setAllDrivers(drivers);

        const totalEarnings = orders.reduce((sum: number, order: any) => sum + (order.net_earnings || 0), 0);

        const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
        const activeDriverIds = new Set(
          orders
            .filter((o: any) => {
              // Use order_finished_timestamp for active driver detection
              const orderTs = o.order_finished_timestamp || o.order_created_timestamp;
              return orderTs && new Date(orderTs * 1000) >= weekAgo;
            })
            .map((o: any) => o.driver_uuid)
            .filter(Boolean)
        );

        setStats({
          connectedUsers: drivers?.length ?? null,
          workingUsers: activeDriverIds.size ?? null,
          grossEarnings: totalEarnings ?? null,
        });
      } catch (err) {
        console.error("Erreur chargement stats:", err);
        setStats({
          connectedUsers: null,
          workingUsers: null,
          grossEarnings: null,
        });
      } finally {
        setLoading(false);
      }
    }

    loadStats();
  }, [token]);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (profileMenuRef.current && !profileMenuRef.current.contains(event.target as Node)) {
        setProfileMenuOpen(false);
      }
    }

    if (profileMenuOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [profileMenuOpen]);

  return (
    <div className="overview-page">
      <header className="overview-header">
        <div className="overview-title">
          <div className="overview-title__icon" aria-hidden>
            <svg width="18" height="18" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M4 9H12V11H4V9Z" fill="white" />
              <path d="M14 9H16V11H14V9Z" fill="white" />
              <path d="M4 5H16V7H4V5Z" fill="white" />
              <path d="M4 13H16V15H4V13Z" fill="white" />
            </svg>
          </div>
          <h1>Vue d'ensemble</h1>
        </div>
        <div className="overview-profile" ref={profileMenuRef}>
          <div
            className="overview-profile__avatar"
            onClick={() => setProfileMenuOpen(!profileMenuOpen)}
            style={{ cursor: "pointer" }}
          >
            {getInitials(userEmail)}
          </div>
          <span className="overview-profile__chevron" />
          {profileMenuOpen && (
            <div className="overview-profile__menu">
              <button className="overview-profile__menu-item" onClick={onLogout}>
                <FiLogOut size={16} />
                <span>Déconnexion</span>
              </button>
            </div>
          )}
        </div>
      </header>

      <section>
        <div className="section-heading">
          <div className="section-heading__icon" aria-hidden>
            <RiBook3Line size={22} color="#fe9543" />
          </div>
          <h2>Base de connaissances</h2>
        </div>

        <div className="knowledge-grid">
          {knowledgeBaseCards.map((card, idx) => (
            <div className="knowledge-card" key={card.title}>
              <div className="knowledge-card__image" aria-hidden>
                <img src={card.image} alt={card.imageAlt} />
              </div>
              <div>
                <div className="knowledge-card__title">{card.title}</div>
                <p className="knowledge-card__desc">{card.description}</p>
                <a className="knowledge-card__link" href={card.link} target="_blank" rel="noreferrer">
                  En savoir plus
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path
                      d="M13 5H19V11"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                    <path
                      d="M11 13L19 5"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                    <path
                      d="M19 19H5V5H10"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </a>
              </div>
            </div>
          ))}
        </div>
      </section>

      <div className="insights-grid">
        <div className="card">
          <div className="card__head">
            <h5>Métriques clés</h5>
            <div className="combo-button">
              <span>Cette semaine</span>
              <svg width="10" height="6" viewBox="0 0 8 4" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M4 4L0 0H8L4 4Z" fill="currentColor" />
              </svg>
              <div className="combo-button__menu">
                <button className="combo-button__item">Semaine dernière</button>
                <button className="combo-button__item combo-button__item--active">Cette semaine</button>
              </div>
            </div>
          </div>
          <div className="metrics-list">
            <div className="metric-card">
              <div className="metric-card__icon blue">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path
                    d="M10.0001 18.3334C5.39758 18.3334 1.66675 14.6025 1.66675 10C1.66675 5.39753 5.39758 1.66669 10.0001 1.66669C14.6026 1.66669 18.3334 5.39753 18.3334 10C18.3334 14.6025 14.6026 18.3334 10.0001 18.3334Z"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M6.25 10.4167L8.75 12.9167L13.75 7.08337"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
              <div>
                <div className="metric-card__label">Nombre d'utilisateurs connectés</div>
                <div className="metric-card__value">{formatNumber(loading ? null : stats.connectedUsers)}</div>
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-card__icon green">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path
                    d="M16.6666 16.6667H3.33325V17.5C3.33325 17.721 3.24545 17.933 3.08917 18.0892C2.93289 18.2455 2.72093 18.3333 2.49992 18.3333H1.66659C1.44558 18.3333 1.23362 18.2455 1.07734 18.0892C0.921061 17.933 0.833252 17.721 0.833252 17.5V9.16667L2.89992 4.33333C3.02853 4.03333 3.24238 3.7777 3.51497 3.59815C3.78755 3.4186 4.10686 3.32304 4.43325 3.33333H15.5666C15.8928 3.33331 16.2119 3.42903 16.4841 3.60855C16.7563 3.78807 16.9699 4.04351 17.0983 4.34333L19.1666 9.16667V17.5C19.1666 17.721 19.0788 17.933 18.9225 18.0892C18.7662 18.2455 18.5543 18.3333 18.3333 18.3333H17.4999C17.2789 18.3333 17.067 18.2455 16.9107 18.0892C16.7544 17.933 16.6666 17.721 16.6666 17.5V16.6667Z"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  <path
                    d="M3.5 10H16.5"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
              <div>
                <div className="metric-card__label">Nombre d'utilisateurs actifs</div>
                <div className="metric-card__value">{formatNumber(loading ? null : stats.workingUsers)}</div>
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-card__icon navy">
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path
                    d="M2.5 7.5C2.5 5.01472 6.02944 3 10 3C13.9706 3 17.5 5.01472 17.5 7.5C17.5 9.98528 13.9706 12 10 12C6.02944 12 2.5 9.98528 2.5 7.5Z"
                    stroke="currentColor"
                    strokeWidth="1.5"
                  />
                  <path
                    d="M2.5 12.5C2.5 14.9853 6.02944 17 10 17C13.9706 17 17.5 14.9853 17.5 12.5"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                  />
                </svg>
              </div>
              <div>
                <div className="metric-card__label">Revenus bruts totaux</div>
                <div className="metric-card__value">
                  {formatNumber(loading ? null : stats.grossEarnings, {
                    style: "currency",
                    currency: "EUR",
                    maximumFractionDigits: 0,
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="cta-banner cta-banner--single">
        <div className="cta-banner__image" aria-hidden>
          <img src="/assets/images/question.19e1ed8e.svg" alt="Illustration d'aide" />
        </div>
        <div className="cta-banner__content">
          <h3>Vous ne savez pas par où commencer ? Nous sommes là pour vous aider !</h3>
          <p>
            Besoin d'une solution personnalisée ou de connecteurs supplémentaires pour améliorer votre
            <br />
            expérience ? Parlons-en !
          </p>
          <div className="cta-banner__actions">
            <button className="cta-banner__btn primary">Contacter l'équipe de support</button>
            <button className="cta-banner__btn secondary">Réserver une démonstration</button>
          </div>
        </div>
      </div>
    </div>
  );
}

