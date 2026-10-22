// Note legali e privacy sono scritte in italiano: nelle altre lingue
// traduciamo il link per tornare indietro e avvisiamo con un riquadro.
(function () {
  const back = document.querySelector(".back");
  if (back) back.lastChild.textContent = " " + i18n.t("back");
  document.documentElement.lang = "it";
  if (i18n.lang === "it") return;
  const note = document.createElement("p");
  note.className = "disclaimer";
  note.lang = i18n.lang;
  note.textContent = "🌐 " + i18n.t("legal.only_it");
  document.querySelector("header").append(note);
})();
