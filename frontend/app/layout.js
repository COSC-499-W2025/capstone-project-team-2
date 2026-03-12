import "./globals.css";

/**
 * Root layout module metadata.
 *
 * These values are used for document title/description in static rendering
 * contexts and browser tabs.
 */
export const metadata = {
  title: "Project Workspace UI",
  description: "Next.js frontend for project analysis and document workflows"
};

/**
 * Root layout that initializes theme state early to prevent hydration
 * flicker and wraps every route in a shared HTML structure.
 *
 * @param {{ children: import("react").ReactNode }} props
 * @returns {JSX.Element}
 */
export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/**
          * Inline boot script runs before React hydration to keep initial
          * theme value in sync with local storage or system preference.
          * This avoids visible flash between light/dark variants.
          */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function () {
                try {
                  var stored = localStorage.getItem('uiTheme');
                  var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                  var theme = (stored === 'dark' || stored === 'light') ? stored : (prefersDark ? 'dark' : 'light');
                  document.documentElement.dataset.theme = theme;
                  document.documentElement.style.colorScheme = theme;
                } catch (e) {}
              })();
            `
          }}
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
