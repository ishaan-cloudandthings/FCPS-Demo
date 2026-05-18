/**
 * AppShell — authenticated layout wrapper.
 *
 * Pairs `AppHeader` (signed-in user pill + logout) with the same footer
 * as the anonymous screens. AC-22's vendor pages render their bodies
 * inside this shell.
 */
import { AppHeader } from "./AppHeader.jsx";
import { AuthShellFooter } from "./AuthShellFooter.jsx";
import { SkipLink } from "./SkipLink.jsx";

export function AppShell({ children }) {
  return (
    <div className="flex min-h-screen flex-col">
      <SkipLink targetId="main" />
      <AppHeader />
      <main id="main" role="main" className="flex-1 p-6">
        {children}
      </main>
      <AuthShellFooter />
    </div>
  );
}
