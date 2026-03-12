import { redirect } from "next/navigation";

/**
 * Portfolio alias route module.
 */

/**
 * Legacy Portfolio route alias.
 * Redirects users to the workspace with the portfolio tab selected.
 *
 * @returns {never}
 */
export default function PortfolioPage() {
  redirect("/workspace?tab=portfolio");
}
