// Mahalle yayin dosyalarinin kompakt bicimi (scripts/kompakt.py) tarayicida kaynaktakiyle ayni
// mantiksal veriye aciliyor mu? data-loader.js'teki cozuculer (yuvarla2, mahalleOyAc, topoAc) metinden
// alinip site/dist/ dosyalarina uygulanir ve data/normalized/ + geo/normalized/ ile karsilastirilir.
// Onkosul: python3 site/build.py
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const ROOT = path.resolve(__dirname, '..');
const DIST = path.join(ROOT, 'site', 'dist');
const kod = fs.readFileSync(path.join(ROOT, 'site/src/js/data-loader.js'), 'utf8');
const bas = kod.indexOf('  // Python round(x, 2)'), son = kod.indexOf('  // acilmis hali onbellege');
const {mahalleOyAc, topoAc} = new Function(kod.slice(bas, son) + 'return {mahalleOyAc, topoAc};')();
const oku = p => JSON.parse(fs.readFileSync(p, 'utf8'));
const dist = fs.existsSync(path.join(DIST, 'data', 'mahalle_votes'));

test('mahalle oy dosyalari kaynakla ayni aciliyor (oran ve katilim dahil)', {skip: !dist && 'site/dist yok'}, () => {
  for(const ad of fs.readdirSync(path.join(ROOT, 'data/normalized/mahalle'))){
    assert.deepEqual(mahalleOyAc(oku(path.join(DIST, 'data/mahalle_votes', ad))),
                     oku(path.join(ROOT, 'data/normalized/mahalle', ad)), ad);
  }
});

test('mahalle sinirlari (TopoJSON) kaynakla ayni poligonlara aciliyor', {skip: !dist && 'site/dist yok'}, () => {
  // halka baslangic noktasi degisebilir: halka, kaynaktakinin donusu olmali
  const ayniHalka = (a, b) => {
    a = a.slice(0, -1).map(String); b = b.slice(0, -1).map(String);
    return a.length === b.length && a.some((p, i) => p === b[0] && a.slice(i).concat(a.slice(0, i)).join() === b.join());
  };
  const kaynak = oku(path.join(ROOT, 'geo/normalized/mahalle_geo.json'));
  for(const [g, satirlar] of Object.entries(kaynak)){
    const acik = topoAc(oku(path.join(DIST, 'geo/mahalle', g + '.json')));
    assert.deepEqual(Object.keys(acik).sort(), Object.keys(satirlar).sort(), g);
    for(const [m, s] of Object.entries(satirlar)){
      const a = acik[m], t = s.geometry.type;
      assert.equal(a.ad, s.ad); assert.equal(a.geometry.type, t);
      const polys = x => t === 'Polygon' ? [x] : x;
      if(t === 'LineString'){ assert.deepEqual(a.geometry.coordinates, s.geometry.coordinates); continue; }
      const p1 = polys(s.geometry.coordinates), p2 = polys(a.geometry.coordinates);
      assert.equal(p1.length, p2.length, g + '/' + m);
      p1.forEach((p, i) => p.forEach((r, j) => assert(ayniHalka(r, p2[i][j]), g + '/' + m)));
    }
  }
});
