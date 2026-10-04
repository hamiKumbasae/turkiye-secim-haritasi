  // ---------------- search ----------------
  $('#searchBox').addEventListener('input', e=>{
    const q = e.target.value.toLocaleLowerCase('tr');
    if(q.length<2) return;
    if(view.level==='country'){
      const match = DATA.iller.find(p=>p.ad.toLocaleLowerCase('tr').startsWith(q));
      if(match) goToProvince(match.plaka);
    } else if(view.level==='mahalle'){
      const match = currentMahalleRows.find(r=>r.ad.toLocaleLowerCase('tr').startsWith(q));
      if(match && pathByMahalleId[match.id]){
        $$('.geo-path').forEach(p=>p.classList.toggle('selected', p===pathByMahalleId[match.id]));
      }
    } else if(view.level==='meclis-ilce'){
      const list = districtsByPlaka[view.plaka]||[];
      const match = list.find(d=>d.ad.toLocaleLowerCase('tr').startsWith(q));
      if(match && match.geomId) renderMeclisIlceMap(view.plaka, match.geomId);
    } else {
      const list = districtsByPlaka[view.plaka]||[];
      const match = list.find(d=>d.ad.toLocaleLowerCase('tr').startsWith(q));
      if(match && match.geomId && pathByGeomId[match.geomId] && districtHasRealData(match)) selectDistrict(match, view.plaka);
      renderDistrictList(view.plaka, e.target.value);
    }
  });

