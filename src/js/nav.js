  $('#btnBackCountry').addEventListener('click', ()=>{
    $('#searchBox').value='';
    renderCountryMap();
    if(selectedPlaka) $$('.il-path').forEach(p=>p.classList.toggle('selected', +p.dataset.plaka===selectedPlaka));
  });

  $('#btnBackProvince').addEventListener('click', ()=>{
    if(view.plaka!=null){ renderProvinceMap(view.plaka); selectProvince(view.plaka); }
  });

  $('#mapMode').addEventListener('change', applyMapMode);

  $('#methodNoteToggle').addEventListener('click', ()=>{
    const el = $('#methodNoteText');
    const expanded = el.classList.toggle('clamped')===false;
    $('#methodNoteToggle').textContent = expanded ? 'Daha az göster' : 'Devamını oku';
    $('#methodNoteToggle').setAttribute('aria-expanded', expanded ? 'true' : 'false');
  });

  // ---------------- view toggle ----------------
  $('#btnMapView').addEventListener('click', ()=>{
    $('#btnMapView').classList.add('active'); $('#btnTableView').classList.remove('active');
    $('#mapView').classList.remove('hidden-view'); $('#tableView').classList.remove('active');
  });
  $('#btnTableView').addEventListener('click', ()=>{
    $('#btnTableView').classList.add('active'); $('#btnMapView').classList.remove('active');
    $('#mapView').classList.add('hidden-view'); $('#tableView').classList.add('active');
  });

