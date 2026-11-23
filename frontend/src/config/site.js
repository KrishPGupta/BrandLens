export const SITE = {
  name: "BrandLens",
  tagline: "Social media sentiment and drift monitoring",
  description:
    "BrandLens tracks how people talk about a brand, sets bot activity aside, and flags the weeks where opinion shifts, with the words behind each flag.",
};

export const LINKS = {
  github: "https://github.com/KrishPGupta/BrandLens",
  issues: "https://github.com/KrishPGupta/BrandLens/issues",
};

// Swap a photo here and nothing else changes.
export const IMAGES = {
  hero: "/images/hero.jpg",
  features: "/images/features.jpg",
};

export const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const FEATURES = [
  {
    title: "Bot filtering",
    description:
      "A Random Forest scores every account on followers, posting rate, links and repeated text. Suspected bots are set aside before any sentiment is counted, so spam cannot hide or fake a shift.",
  },
  {
    title: "Drift alerts",
    description:
      "Each week's share of positive and negative posts is compared with the previous 12 normal weeks. A week that moves three standard deviations is flagged as needing review.",
  },
  {
    title: "Explanations",
    description:
      "SHAP shows which words pushed a post toward positive, neutral or negative, so every alert comes with evidence you can read instead of a bare score.",
  },
];

export const STAGES = [
  {
    title: "Clean the text",
    description:
      "Links, mentions and hashtag symbols are stripped, and exact duplicate posts are removed.",
  },
  {
    title: "Filter bots",
    description:
      "Accounts are scored on follower ratio, age, posting rate and repeated text. Flagged posts are kept but set aside.",
  },
  {
    title: "Classify sentiment",
    description:
      "A TF-IDF and Logistic Regression baseline or a fine-tuned DistilBERT labels each post, behind one prediction call.",
  },
  {
    title: "Detect drift",
    description:
      "Weekly sentiment shares are compared with a rolling baseline. Weeks beyond three standard deviations are flagged.",
  },
  {
    title: "Explain the result",
    description:
      "SHAP word contributions are computed for selected posts, so each flag can be traced to the language behind it.",
  },
  {
    title: "Serve it anywhere",
    description:
      "Results are stored in SQLite and served by a REST API, so any dashboard or tool can read them.",
  },
];

// Shown if the API is not running, so the page never looks broken.
// These are the real values from the demo dataset.
export const FALLBACK_SUMMARY = { posts: 19500, bot_pct: 12.73 };
export const FALLBACK_ALERT = {
  brand: "Nova",
  week: "2025-04-21",
  driver: "negative up, positive down",
  negative: 58.6,
  positive: 19.5,
  z_negative: 6.7,
  z_positive: -7.5,
};
