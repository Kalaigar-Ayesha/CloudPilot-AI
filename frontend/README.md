# CloudPilot AI: React Frontend

This directory contains the premium, dark-mode-first React frontend dashboard for **CloudPilot AI**.

---

## 1. Technology Stack

* **Core UI:** React 19 + TypeScript + Vite + TailwindCSS
* **State Management:** TanStack React Query (caching, background refetching, custom queries)
* **Routing:** Protected route layouts via React Router
* **Visual Data Widgets:** Recharts (responsive area charts, cost distribution pies)
* **Icons:** Lucide React

---

## 2. Launching Locally

### Step 1: Install Dependencies
Run from the `frontend` folder:
```bash
npm install
```

### Step 2: Launch Development Server
```bash
npm run dev
```

The application defaults to [http://localhost:5173](http://localhost:5173) in your browser.

---

## 3. Directory Layout

* `src/components/`: Modular component structures (e.g. `Sidebar.tsx` navigation shell).
* `src/context/`: Authentication provider managers (`AuthContext.tsx` token decryption).
* `src/pages/`: Page views:
  * `Dashboard.tsx`: Global spend timelines, utilization cards, and allocations.
  * `CloudAccounts.tsx`: Multi-cloud connect Form wizards and list tables.
  * `Billing.tsx`: Historic cost area charts and future forecast cards.
  * `Optimization.tsx`: Right-sizing recommendations lists and detailed action modals.
  * `Copilot.tsx`: Multi-thread chat interface with suggeted chips and source citations.
* `src/services/`: API configuration wrapper (`api.ts` axios token headers interceptors).
* `src/index.css`: Global baseline Tailwind imports and custom styling scrollbars.
