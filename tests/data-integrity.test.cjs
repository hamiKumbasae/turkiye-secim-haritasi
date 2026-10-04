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
