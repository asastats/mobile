// offline.html's Retry button; window.ASASTATS_URL comes from server-url.js.
document.getElementById("retry").addEventListener("click", function () {
  window.location.href = window.ASASTATS_URL || "https://www.asastats.com";
});
