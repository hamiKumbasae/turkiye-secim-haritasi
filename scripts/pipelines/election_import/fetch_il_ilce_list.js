// Turkiye'deki TUM il/ilce resmi YSK ID listesini ceker (mahalle-veri-
// pipeline'in aksine, poligon/geometri kisiti YOK - sadece sayisal ID
// eslemesi). Cikti: data/raw/ysk/acikveri-il-ilce-listesi.json
const { chromium } = require('../mahalle_veri/node_modules/playwright');
const fs = require('fs');
const path = require('path');

const IL_LIST = [
  [1,'ADANA'],[2,'ADIYAMAN'],[3,'AFYONKARAHİSAR'],[4,'AĞRI'],[5,'AMASYA'],
  [6,'ANKARA'],[7,'ANTALYA'],[8,'ARTVİN'],[9,'AYDIN'],[10,'BALIKESİR'],
  [11,'BİLECİK'],[12,'BİNGÖL'],[13,'BİTLİS'],[14,'BOLU'],[15,'BURDUR'],
  [16,'BURSA'],[17,'ÇANAKKALE'],[18,'ÇANKIRI'],[19,'ÇORUM'],[20,'DENİZLİ'],
  [21,'DİYARBAKIR'],[22,'EDİRNE'],[23,'ELAZIĞ'],[24,'ERZİNCAN'],[25,'ERZURUM'],
  [26,'ESKİŞEHİR'],[27,'GAZİANTEP'],[28,'GİRESUN'],[29,'GÜMÜŞHANE'],[30,'HAKKARİ'],
  [31,'HATAY'],[32,'ISPARTA'],[33,'MERSİN'],[34,'İSTANBUL'],[35,'İZMİR'],
  [36,'KARS'],[37,'KASTAMONU'],[38,'KAYSERİ'],[39,'KIRKLARELİ'],[40,'KIRŞEHİR'],
  [41,'KOCAELİ'],[42,'KONYA'],[43,'KÜTAHYA'],[44,'MALATYA'],[45,'MANİSA'],
  [46,'KAHRAMANMARAŞ'],[47,'MARDİN'],[48,'MUĞLA'],[49,'MUŞ'],[50,'NEVŞEHİR'],
  [51,'NİĞDE'],[52,'ORDU'],[53,'RİZE'],[54,'SAKARYA'],[55,'SAMSUN'],
  [56,'SİİRT'],[57,'SİNOP'],[58,'SİVAS'],[59,'TEKİRDAĞ'],[60,'TOKAT'],
  [61,'TRABZON'],[62,'TUNCELİ'],[63,'ŞANLIURFA'],[64,'UŞAK'],[65,'VAN'],
  [66,'YOZGAT'],[67,'ZONGULDAK'],[68,'AKSARAY'],[69,'BAYBURT'],[70,'KARAMAN'],
  [71,'KIRIKKALE'],[72,'BATMAN'],[73,'ŞIRNAK'],[74,'BARTIN'],[75,'ARDAHAN'],
  [76,'IĞDIR'],[77,'YALOVA'],[78,'KARABÜK'],[79,'KİLİS'],[80,'OSMANİYE'],
  [81,'DÜZCE'],
];

const OUT = path.join(__dirname, '..', '..', 'data', 'raw', 'ysk', 'acikveri-il-ilce-listesi.json');
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('https://acikveri.ysk.gov.tr/', { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(1000);

  const result = {}; // il_ID -> {il_ADI, ilceler: [{ilce_ID, ilce_ADI}]}
  let errors = [];

  for (const [ilId, ilAdi] of IL_LIST) {
    let attempt = 0;
    while (attempt < 3) {
      attempt++;
      try {
        const rows = await page.evaluate(async (ilId) => {
          const r = await fetch(`/api/getIlceList?ilId=${ilId}`, { credentials: 'include' });
          if (r.status !== 200) return { error: 'status ' + r.status };
          return r.json();
        }, ilId);
        if (rows.error) throw new Error(rows.error);
        result[ilId] = {
          il_ADI: ilAdi,
          ilceler: rows.map(r => ({ ilce_ID: r.ilce_ID, ilce_ADI: r.ilce_ADI })),
        };
        console.log(`il ${ilId} (${ilAdi}): ${rows.length} ilce`);
        break;
      } catch (e) {
        if (attempt >= 3) { errors.push([ilId, ilAdi, String(e)]); console.log('FAILED', ilId, ilAdi, String(e)); }
        else await sleep(500 * attempt);
      }
    }
    await sleep(150);
  }

  const totalIlce = Object.values(result).reduce((s, x) => s + x.ilceler.length, 0);
  console.log(`\nToplam il: ${Object.keys(result).length}/81, toplam ilce: ${totalIlce}`);
  if (errors.length) console.log('HATALAR:', errors);

  fs.writeFileSync(OUT, JSON.stringify(result, null, 1));
  console.log('yazildi:', OUT);

  await browser.close();
})();
