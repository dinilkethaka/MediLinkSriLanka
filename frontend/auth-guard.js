//frontend security layer
(async function authGuard() {
  try {
    const result = await apiMe(); 
    const user = result.user;

    if (typeof REQUIRED_ROLE !== "undefined" && user.role !== REQUIRED_ROLE) {
      window.location.href = "../login.html";
      return;
    }

    window.currentUser = user;

    const avatarEl = document.getElementById("sb-avatar");
    const nameEl = document.getElementById("sb-uname");

    // Short name
    if (avatarEl) {
      avatarEl.textContent = user.full_name
        .split(" ").map(w => w[0]).join("").slice(0, 2).toUpperCase();
    }
    if (nameEl) {
      nameEl.textContent = user.full_name;
    }

    document.dispatchEvent(new CustomEvent("auth-ready"));

  } catch (err) {
    window.location.href = "../login.html";
  }
})();

async function handleLogout() {
  try {
    await apiLogout();
  } catch (err) {
  }
  window.location.href = "../login.html";
}