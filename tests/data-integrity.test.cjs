const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');
const election=y=>JSON.parse(fs.readFileSync(path.join(root,'data/normalized/elections',y.includes('yerel')?'yerel':y.includes('referandum')?'referandum':y.includes('cb')?'cumhurbaskanligi':'genel',y+'.json'),'utf8'));
const strip=v=>Array.isArray(v)?v.map(strip):v&&typeof v==='object'?Object.fromEntries(Object.entries(v).filter(([k])=>k!=='kaynak').map(([k,x])=>[k,strip(x)])):v;
test('1957 and 1961 parliament bars include Sakarya and account for every seat',()=>{
 for(const [y,expected,seats] of [['1957',610,{DP:8}],['1961',450,{AP:3,CHP:2,YTP61:1}]]){
  const d=election(y);assert.equal(d.iller.reduce((s,r)=>s+Object.values(r.vekil).reduce((a,b)=>a+b,0),0),expected);
  assert.deepEqual(d.iller.find(r=>r.plaka===54).vekil,seats);
 }
});
test('2004 central municipality uses official counts and bounded percentages',()=>{
 const d=election('2004yerel'),a=d.iller.find(r=>r.plaka===5);
 assert.equal(a.secmen,53650);assert.equal(a.gecerliOy,33901);assert.equal(a.oy['AK Parti'].oy,16258);assert.equal(a.katilim,65.33);
 for(const r of [...d.iller,...d.ilceler]) for(const v of Object.values(r.oy)) assert(v.oran>=0&&v.oran<=100);
});
test('Batman turnout is derived from its city and village electorate',()=>{
 const r=election('1982referandum').ilceler.find(r=>r.ad==='Batman');assert.equal(r.secmen,31121);assert.equal(r.oyKullanan,26790);assert.equal(r.katilim,86.08);
});
test('Karaisali includes the official independent aggregate in its denominator',()=>{
 const r=election('2024yerel').ilceler.find(r=>r.plaka===1&&r.ad==='Karaisalı');assert.equal(r.oy['Bağımsız'].oy,3963);assert.equal(r.oy.MHP.oy,6975);assert.equal(r.oy.MHP.oran,44.76);assert.equal(Object.values(r.oy).reduce((s,v)=>s+v.oy,0),r.gecerliOy);
});
test('Tillo matches verified YSK ballot aggregates without duplicate independent votes',()=>{
 const fixtures=JSON.parse(fs.readFileSync(path.join(__dirname,'fixtures/verified-repairs.json'),'utf8')).filter(x=>x.record.plaka===56);assert.equal(fixtures.length,15);
 for(const {year,record} of fixtures){const rows=election(year).ilceler.filter(r=>r.geomId==='TR-D-56-007');assert.equal(rows.length,1,year);assert.deepEqual(strip(rows[0]),record);assert.equal(Object.values(record.oy).reduce((s,v)=>s+v.oy,0),record.gecerliOy);}
});

test('Tillo is present in all eight modern council ballot files',()=>{
 for(const y of ['2009','2014','2019','2024']) for(const type of ['bm','igm']){
  const d=JSON.parse(fs.readFileSync(path.join(root,'data/normalized/meclis_harita',y+'yerel_'+type+'.json'),'utf8'));
  const rows=d.ilceler.filter(r=>r.geomId==='TR-D-56-007');assert.equal(rows.length,1);
  assert.equal(Object.values(rows[0].oy).reduce((s,v)=>s+v.oy,0),rows[0].gecerliOy);
 }
});
test('1994-2004 Diğer totals are split only where the DİE breakdown matches YSK exactly',()=>{
 const d=election('1994yerel'),kigi=d.ilceler.find(r=>r.plaka===12&&r.ad==='Kiğı');
 assert.equal(kigi.kazanan,'Bağımsız');assert.equal(kigi.oy['Diğer'],undefined);
 assert.deepEqual(kigi.kaynak.digerAyristirma.dagilim,{'Bağımsız':751,'DSP':77});
 for(const y of ['1994yerel','1999yerel','2004yerel']) for(const r of [...election(y).iller,...election(y).ilceler]){
  const a=r.kaynak&&r.kaynak.digerAyristirma; if(!a) continue;
  assert.equal(Object.values(a.dagilim).reduce((s,v)=>s+v,0),a.digerOy,y+' '+r.ad);
  assert.equal(r.kaynak.tuikKullanilmadi,undefined,y+' '+r.ad+': kontrolden geçmeyen DİE satırı kullanılmamalı');
 }
});
test('2009-2024 local and 2011-2023 general Diğer is split into YSK party columns without overriding official winners',()=>{
 const il=(y,plaka)=>election(y).iller.find(r=>r.plaka===plaka), ilce=(y,plaka,ad)=>election(y).ilceler.find(r=>r.plaka===plaka&&r.ad===ad);
 // İYİ Parti eskiden 'Diğer' icindeydi ve 'Diğer' kazanan gorunuyordu
 const usak=il('2019yerel',64);assert.equal(usak.kazanan,'AK Parti');assert.equal(usak.oy['İYİ Parti'].oy,49229);assert.equal(usak.oy['Diğer'],undefined);
 assert.equal(ilce('2024yerel',2,'Çelikhan').kazanan,'DEVA');
 // resmi kazanan sandik toplamindan farkli olabilir: korunur
 assert.equal(il('2024yerel',43).kazanan,'CHP');
 // bagimsizlarin toplami onde ama tek aday degil: kazanan degismez; tek aday onde: Bağımsız
 assert.equal(ilce('2014yerel',50,'Hacıbektaş').kazanan,'CHP');
 assert.equal(ilce('2014yerel',37,'Devrekani').kazanan,'Bağımsız');
 // genel: kucuk partiler ayri (2023 Ankara: Zafer Partisi); kazanan degismez
 const ankara=il('2023',6);assert.equal(ankara.oy['ZP'].oy,130407);assert.equal(ankara.oy['Diğer'],undefined);assert.equal(ankara.kazanan,'AK Parti');
 for(const y of ['2009yerel','2014yerel','2019yerel','2024yerel','2011','2015Haziran','2015Kasim','2018','2023']) for(const r of [...election(y).iller,...election(y).ilceler]){
  assert.notEqual(r.kazanan,'Diğer',y+' '+r.ad);
  assert.equal(r.oy['DEVA PARTİSİ'],undefined,y+' '+r.ad);
  const a=r.kaynak&&r.kaynak.digerAyristirma; if(!a) continue;
  assert.equal(r.oy['Diğer'],undefined,y+' '+r.ad);
  assert.equal(Object.values(r.oy).reduce((s,v)=>s+v.oy,0),r.gecerliOy,y+' '+r.ad);
  if(a.oncekiKazanan!==undefined&&a.oncekiKazanan!=='Diğer'){
   assert.ok(y.includes('yerel'),y+' '+r.ad+': genel seçimde kazanan değişmemeli');
   assert.equal(r.kazanan,'Bağımsız',y+' '+r.ad);assert.ok(a.enCokOyAlanBagimsizAday>r.oy[a.oncekiKazanan].oy,y+' '+r.ad);
  }
 }
});
