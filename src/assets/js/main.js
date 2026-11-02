const knopf = document.querySelector(".menue");
const nav = document.getElementById("nav");
knopf.addEventListener("click", () => {
  const offen = nav.classList.toggle("offen");
  knopf.setAttribute("aria-expanded", offen);
  knopf.textContent = offen ? "Schließen" : "Menü";
});

const fehler = new URLSearchParams(location.search).get("fehler");
const hinweis = document.getElementById("fehler");
if (fehler && hinweis) {
  hinweis.hidden = false;
  if (fehler === "2") hinweis.textContent = "Die Nachricht konnte gerade nicht versendet werden. Bitte schreiben Sie direkt per E-Mail.";
}

if ("IntersectionObserver" in window && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
  const beobachter = new IntersectionObserver((eintraege) => {
    for (const e of eintraege) {
      if (e.isIntersecting) {
        e.target.classList.add("da");
        beobachter.unobserve(e.target);
      }
    }
  }, { rootMargin: "0px 0px -8% 0px" });
  document.querySelectorAll(".bild").forEach((b) => {
    b.classList.add("wartet");
    beobachter.observe(b);
  });
}
