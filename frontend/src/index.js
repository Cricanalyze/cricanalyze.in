import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "@/index.css";
import App from "@/App";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      refetchOnWindowFocus: false,
    },
  },
});

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
);

const pre = document.getElementById("preloader");
if (pre) {
  const hide = () => { pre.style.opacity = "0"; pre.style.visibility = "hidden"; setTimeout(() => pre.remove(), 500); };
  if (document.readyState === "complete") setTimeout(hide, 250); else window.addEventListener("load", () => setTimeout(hide, 250), { once: true });
  setTimeout(hide, 4000);
}
