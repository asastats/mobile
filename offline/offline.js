// offline.html's Retry button; capacitor.config.ts inlines this file and sets window.ASASTATS_URL.
document.getElementById("retry").addEventListener("click", function () {
  window.location.href = window.ASASTATS_URL || "https://www.asastats.com";
});
