import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";
import { SessionStoreProvider } from "./hooks/useSessionStore";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <SessionStoreProvider>
        <App />
      </SessionStoreProvider>
    </BrowserRouter>
  </React.StrictMode>,
);
