import "./globals.css";

/**
 * Root layout module metadata.
 *
 * These values are used for document title/description in static rendering
 * contexts and browser tabs.
 */
export const metadata = {
  title: "Project Console UI",
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
    <html lang="en" data-theme="light" style={{ colorScheme: "light" }} suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
