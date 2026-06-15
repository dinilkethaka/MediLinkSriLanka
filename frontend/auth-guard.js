// auth-guard.js
// ---------------------------------------------------------
// Include this script on every protected page (admin/*, hospital/*, doctor/*).
// It checks whether the user is logged in AND has the correct role
// for this page. If not, it redirects to the login page.
//
// USAGE: set a global variable BEFORE including this script:
//   <script>const REQUIRED_ROLE = "admin";</script>
//   <script src="../auth-guard.js"></script>
//
// This script also sets `window.currentUser` to the logged-in user's
// info (from /api/auth/me), so page scripts can use it - e.g. to show
// the user's name in the sidebar.
// ---------------------------------------------------------

(async function authGuard() {
  try {
    const result = await apiMe(); // GET /api/auth/me
    const user = result.user;

    // If this page requires a specific role and the logged-in user
    // doesn't have it, send them back to login.
    if (typeof REQUIRED_ROLE !== "undefined" && user.role !== REQUIRED_ROLE) {
      window.location.href = "../login.html";
      return;
    }

    // Make the user info available to the page's own script.
    window.currentUser = user;

    // Fill in the sidebar user info, if those elements exist on this page.
    const avatarEl = document.getElementById("sb-avatar");
    const nameEl = document.getElementById("sb-uname");

    if (avatarEl) {
      avatarEl.textContent = user.full_name
        .split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();
    }
    if (nameEl) {
      nameEl.textContent = user.full_name;
    }

    // Dispatch a custom event so the page's own script knows
    // the auth check finished and window.currentUser is ready.
    document.dispatchEvent(new CustomEvent("auth-ready"));

  } catch (err) {
    // apiMe() throws if the response is not 2xx (e.g. 401 Unauthorized -
    // nobody is logged in). Redirect to login.
    window.location.href = "../login.html";
  }
})();


/**
 * Logs the current user out and redirects to the login page.
 * Call this from a "Sign Out" button's onclick.
 */
async function handleLogout() {
  try {
    await apiLogout();
  } catch (err) {
    // Even if logout fails server-side, we still redirect -
    // worst case the session cookie just expires naturally.
  }
  window.location.href = "../login.html";
}