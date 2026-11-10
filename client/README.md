# VoiceIQ India — Frontend Client

React 19 + TypeScript + Vite + Tailwind CSS v4 e-commerce storefront and multilingual voice assistant interface.

---

## 🚀 Quick Start (Run Client Separately)

### 1. Prerequisites
- Node.js 20+
- npm

### 2. Install Dependencies
From within the `client/` directory:

```bash
cd client
npm install
```

### 3. Start Development Server
```bash
npm run dev
```

- **Local URL**: [http://localhost:5000](http://localhost:5000) (or port displayed in terminal)
- The Vite dev server automatically proxies all `/api/*` calls to the FastAPI backend running at `http://127.0.0.1:8000`.

---

## 🛠 Available Scripts

- `npm run dev` — Starts Vite dev server with hot module replacement (HMR) and `/api` proxy.
- `npm run build` — Compiles TypeScript and builds production-ready bundles in `client/dist`.
- `npm run preview` — Locally preview the production build.
- `npm run check` — Type-checks all TypeScript files without emitting files.

---

## 📁 Directory Structure
```
client/
├── public/            # Static assets
├── src/
│   ├── components/    # Reusable UI & store components (cart, checkout, etc.)
│   ├── hooks/         # Custom React hooks (voice recording, audio playback)
│   ├── lib/           # API client, TanStack Query client, utility functions
│   ├── pages/         # Page views (Home, Store, Admin, 404)
│   ├── types/         # TypeScript type definitions
│   ├── App.tsx        # Root routing and context providers
│   ├── index.css      # Tailwind CSS v4 & theme variables
│   └── main.tsx       # Vite entry point
├── index.html         # HTML entry point
├── package.json       # Dependencies & scripts
├── vite.config.ts     # Vite configuration & /api proxy
└── tsconfig.json      # TypeScript compiler settings
```
