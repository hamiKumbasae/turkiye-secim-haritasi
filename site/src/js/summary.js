  // ---------------- kaynak siniflandirmasi ----------------
  // Ust bardaki ve "Kaynaklar" panelindeki rozet icin genel kategori -
  // hangi ozel arsiv/sayfanin kullanildigi burada degil, veri deposunun
  // kendi belgelerinde tutuluyor.
  const SHORT_BADGE = {
    'YSK Resmî Veri': 'YSK Resmî',
    'YSK Resmî Veri (İl)': 'YSK Resmî',
    'YSK (İl) + İkincil (İlçe)': 'YSK + İkincil',
    'YSK (İl) + TÜİK (İlçe)': 'YSK + TÜİK',
    'YSK + İkincil Kaynak': 'YSK + İkincil',
    'İkincil Kaynak': 'İkincil Kaynak',
  };

  function sourceInfo(){
    if(currentYear==='2004yerel' && !DATA.oylama) return {cat:'mixed',badge:'YSK + TÜİK',detail:'81 il ve 910 ilçe kaydı DİE 2004 tablolarıyla doğrulandı. Eşleşmeyen tarihsel kapsamlar ayrıca notlanır.'};
    if(currentYear==='1957' || currentYear==='1961') return {cat:'mixed',badge:'YSK + İkincil Kaynak',detail:'Sakarya sandalye dağılımı ikincil arşivdeki parti tablosu ve seçilen vekiller listesiyle tamamlandı.'};
    if(DATA.oylama) return {cat:'full', badge: DATA.rozet || 'YSK Resmî Veri', detail: DATA.aciklama || OYLAMA_ACIKLAMA[DATA.oylama]};
    if(currentYear==='2014cb' || currentYear==='2007referandum')
      return {cat:'full', badge:'YSK Resmî Veri'};
    if(YEARS_IL_YSK_ILCE_TUIK.has(currentYear) || YEARS_REF_IL_YSK_ILCE_TUIK.has(currentYear))
      return {cat:'full', badge:'YSK (İl) + TÜİK (İlçe)'};
    if(YEARS_YSK_OFFICIAL_IL.has(currentYear))
      return {cat:'full', badge:'YSK Resmî Veri (İl)'};
    if(YEARS_IL_YSK_ILCE_GITHUB.has(currentYear) || YEARS_YEREL_IL_YSK_ILCE_WIKI.has(currentYear) || currentYear==='2009yerel' || currentYear==='2004yerel')
      return {cat:'mixed', badge:'YSK (İl) + İkincil (İlçe)'};
    if(YEARS_YEREL_1950_1977.has(currentYear) || YEARS_IL_ONLY.has(currentYear))
      return {cat:'secondary', badge:'İkincil Kaynak'};
    return {cat:'full', badge:'YSK Resmî Veri'};
  }

  function computeLevels(){
    const ilceTotal = DATA.ilceler.length;
    const ilceWithData = DATA.ilceler.filter(d=>d.oy && Object.keys(d.oy).length>0).length;
    // MAHALLE_GEO sadece poligon var mi'yi soyler (yildan bagimsiz, hep yuklu) -
    // bu yilin GERCEKTEN mahalle-duzeyi oy verisi olup olmadigini (build.py'nin
    // her yil icin data/normalized/mahalle/<yil>.json'daki ilce sayisini onceden
    // hesaplayip gomdugu MAHALLE_COVERAGE) ayrica kontrol ediyoruz - yoksa
    // "Mahalleye kadar" rozeti, o yil hic mahalle oyu olmasa bile sadece
    // geometri var diye yanlislikla gorunebilirdi.
    const mahalleDistricts = DATA.oylama ? 0 : (MAHALLE_COVERAGE[currentYear] || 0);
    return {ilceTotal, ilceWithData, ilceOn: ilceWithData>0, mahalleDistricts, mahalleOn: mahalleDistricts>0};
  }

  function renderElectionBar(){
    const isRef = DATA.tur === 'referandum';
    const isYerel = DATA.tur === 'yerel';
    const isCB = DATA.tur === 'cumhurbaskanligi';
    const typeLabel = isRef ? 'Referandum' : (isYerel ? 'Yerel Seçim' : (isCB ? 'Cumhurbaşkanlığı Seçimi' : 'Milletvekili Genel Seçimi'));
    $('#eyebrowText').textContent = (isRef ? 'REFERANDUM' : (isYerel ? 'YEREL SEÇİM' : (isCB ? 'CUMHURBAŞKANLIĞI' : 'GENEL SEÇİM')));
    $('#pageTitle').textContent = DATA.ad+' '+typeLabel+(DATA.oylamaAdi ? ' · '+DATA.oylamaAdi : '');

    const src = sourceInfo();
    const dot = $('#sourceBadgeDot');
    dot.className = 'dot' + (src.cat==='secondary' ? ' secondary' : src.cat==='mixed' ? ' mixed' : '');

    const lv = computeLevels();
    const detailLevel = lv.mahalleOn ? 'Mahalleye kadar' : (lv.ilceOn ? 'İlçe' : 'İl düzeyi');
    $('#sourceBadgeText').textContent = (SHORT_BADGE[src.badge] || src.badge) + ' · Ayrıntı: ' + detailLevel;
  }

  function renderNationalSummary(){
    const iller = DATA.iller;
    const secmen = iller.reduce((s,i)=>s+(i.secmen||0),0);
    const gecerli = iller.reduce((s,i)=>s+(i.gecerliOy||0),0);
    const katilimNum = iller.reduce((s,i)=> s + (i.katilim!=null && i.secmen!=null ? i.katilim*i.secmen : 0), 0);
    const katilimDen = iller.reduce((s,i)=> s + (i.katilim!=null && i.secmen!=null ? i.secmen : 0), 0);
    const katilim = katilimDen>0 ? katilimNum/katilimDen : null;

    // Bu toplamlar sadece il kayitlarindan (DATA.iller) geliyor - yurtdisi
    // secmen ayri bir kapsamda tutuluyor (hicbir ile bagli degil, bkz.
    // renderYurtdisiCard). O yuzden bu secimde yurtdisi verisi VARSA
    // etiketleri "Yurt İçi ..." yaparak yaniltici bir "ulusal toplam"
    // izlenimi vermiyoruz.
    const hasYurtdisi = hasYurtdisiData();
    const localMayors = DATA.tur==='yerel' && !DATA.oylama && DATA.contestType!=='municipal_indirect';
    const prefix = localMayors ? 'Gösterilen belediyelerde ' : '';
    const items = [
      [hasYurtdisi ? 'Yurt İçi Katılım' : 'Katılım', katilim!=null ? '%'+katilim.toFixed(2) : '—'],
      [hasYurtdisi ? 'Yurt İçi Seçmen' : 'Seçmen', secmen ? fmt(secmen) : '—'],
      [hasYurtdisi ? 'Yurt İçi Geçerli Oy' : 'Geçerli Oy', gecerli ? fmt(gecerli) : '—'],
    ];
    if(DATA.tur === 'genel' && DATA.toplamSandalye!=null) items.push(['Sandalye', fmt(DATA.toplamSandalye)]);
    items.push(['İl', iller.filter(i => i.kazanan || !i.not).length]);

    $('#nationalSummary').innerHTML = items.map(([l,v])=>
      '<div class="ns-item"><div class="l">'+(l==='İl' ? l : prefix+l)+'</div><div class="v num">'+v+'</div></div>'
    ).join('');
  }

  // ---------------- kaynaklar drawer ----------------
  function renderDrawerBody(){
    const src = sourceInfo();
    const lv = computeLevels();
    let html = '';
    html += '<div class="drawer-section-title">Bu seçim</div>';
    html += '<p><b>'+escapeHtml(DATA.ad+' '+$('#eyebrowText').textContent)+'</b></p>';
    html += '<div class="dr-row"><span>Kaynak durumu</span><span class="dr-badge"><span class="dot" style="background:'+(src.cat==='secondary'?'var(--ink-3)':src.cat==='mixed'?'var(--ink-3)':'var(--ok)')+'"></span>'+src.badge+'</span></div>';
    html += '<div class="dr-row"><span>İl kayıtları</span><span>'+DATA.iller.length+'</span></div>';
    html += '<div class="dr-row"><span>İlçe kayıtları (oy verisiyle)</span><span>'+lv.ilceWithData+' / '+lv.ilceTotal+'</span></div>';
    html += '<div class="dr-row"><span>Mahalle kırılımı olan ilçe</span><span>'+lv.mahalleDistricts+'</span></div>';
    html += '<div class="drawer-section-title">Kaynak ve metodoloji</div>';
    if(src.detail) html += '<p>'+escapeHtml(src.detail)+'</p>';
    const flagged = [...DATA.iller,...DATA.ilceler].filter(r=>r.veriNotu);
    if(flagged.length) html += '<p>'+flagged.length+' kayıt kaynak doğrulaması bekliyor. Uyuşmayan oy toplamlarının yüzdeleri ve değişimleri gösterilmez; ham sayımlar ve kayıt notları korunur.</p>';
    const repairs = new Map();
    for(const r of [...DATA.iller,...DATA.ilceler]) if(r.duzeltmeKaynagi) repairs.set(r.duzeltmeKaynagi.url,r.duzeltmeKaynagi.aciklama);
    for(const [url,note] of repairs) if(/^https:\/\//.test(url)) html += '<p><a href="'+escapeHtml(url)+'" target="_blank" rel="noopener">'+escapeHtml(note)+'</a></p>';
    html += '<p>Seçim sonuçları ağırlıklı olarak YSK ve diğer resmî kamu kaynaklarından derlenmiştir. Eksik tarihsel dönemlerde ikincil kaynaklardan yararlanılmıştır. Veriler yayın öncesinde normalize edilip doğrulama kontrollerinden geçirilir.</p>';
    html += '<p>Yurtdışı seçmen oyları hiçbir ile bağlı olmadığı için haritaya dahil edilmez, mevcut olduğu seçimlerde ayrı bir panelde gösterilir.</p>';
    html += '<p><a class="link-btn" href="yontem.html" style="text-decoration:underline;">Kaynaklar ve yöntem sayfası →</a> (dönem sınırları, harita modları, bilinen eksikler)</p>';
    html += '<p>Bu bir kişisel veri derleme çalışmasıdır, resmî bir YSK yayını değildir. Kaynak kodu:<br><a class="link-btn" href="https://github.com/hamiKumbasae/turkiye-secim-haritasi" target="_blank" rel="noopener" style="text-decoration:underline;">github.com/hamiKumbasae/turkiye-secim-haritasi</a></p>';
    html += '<p><button class="link-btn" id="drawerCsv" type="button" style="text-decoration:underline;">Bu seçimin il ve ilçe sonuçlarını indir (CSV) ↓</button></p>';
    $('#drawerBody').innerHTML = html;
    $('#drawerCsv').addEventListener('click', csvIndir);
  }

  function openDrawer(){
    renderDrawerBody();
    $('#kaynaklarDrawer').classList.add('open');
    $('#drawerOverlay').classList.add('open');
  }
  function closeDrawer(){
    $('#kaynaklarDrawer').classList.remove('open');
    $('#drawerOverlay').classList.remove('open');
  }
  $('#sourceBadgeBtn').addEventListener('click', openDrawer);
  $('#btnKaynaklar').addEventListener('click', openDrawer);
  $('#footerKaynaklar').addEventListener('click', openDrawer);
  $('#drawerClose').addEventListener('click', closeDrawer);
  $('#drawerOverlay').addEventListener('click', closeDrawer);
  document.addEventListener('keydown', e=>{ if(e.key==='Escape') closeDrawer(); });

