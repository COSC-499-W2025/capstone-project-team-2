import { redirect } from "next/navigation";

/**
 * Resume alias route module.
 */

/**
 * Legacy Resume route alias.
 * Redirects users to the workspace with the resume tab selected.
 *
 * @returns {never}
 */
export default function ResumePage() {
  redirect("/workspace?tab=resume");
}
