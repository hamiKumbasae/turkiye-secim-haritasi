  $('#btnBackCountry').addEventListener('click', ()=>{
    $('#searchBox').value='';
    renderCountryMap();
    if(selectedPlaka) $$('.il-path').forEach(p=>p.classList.toggle('selected', +p.dataset.plaka===selectedPlaka));
  });

  $('#btnBackProvince').addEventListener('click', ()=>{
    if(view.plaka!=null){ renderProvinceMap(view.plaka); selectProvince(view.plaka); }
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

