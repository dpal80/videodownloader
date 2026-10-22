// Pagine legali: se esiste la traduzione nella lingua scelta la apriamo,
// altrimenti avvisiamo che la pagina è solo in italiano.
(function () {
  const html = document.documentElement;
  const translations = (html.dataset.translations || "it").split(" ");
  if (html.lang !== i18n.lang && translations.includes(i18n.lang)) {
    const url = new URL(location.href);
    url.searchParams.set("lang", i18n.lang);
    location.replace(url);
    return;
  }
  const back = document.querySelector(".back");
  if (back) back.lastChild.textContent = " " + i18n.t("back");
  if (html.lang === i18n.lang) return;
  const note = document.createElement("p");
  note.className = "disclaimer";
  note.lang = i18n.lang;
  note.textContent = "🌐 " + i18n.t("legal.only_it");
  document.querySelector("header").append(note);
})();
