  let currentTur = 'genel'; // app.js'in acilista cagirdigi switchTur('genel') ile ayni olmali
  // cogunluk usulu genel secim yillari (il kazanani vekil sayisina gore)
  const COGUNLUK_YILLARI = new Set(['1950', '1954', '1957']);
  let DATA, MAJOR, ilByPlaka, districtsByPlaka, districtByGeomId, currentYear;

  function partyColor(name){
    if(renkKoruModu) return renkKoruRengi(name); // bkz. erisim.js
    const cur = document.documentElement.getAttribute('data-theme');
    const dark = cur === 'dark' || (cur !== 'light' && matchMedia('(prefers-color-scheme: dark)').matches);
    const meta = PARTY[name] || PARTY['Diğer'];
    return dark ? meta.dark : meta.light;
  }
  let currentOylama = 'baskan'; // yerel secimde gosterilen oylama: baskan | igm | bm
