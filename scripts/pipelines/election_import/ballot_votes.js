// Independent totals are a separate authoritative YSK field. They must not be
// added to the same candidates a second time. President/referendum columns
// describe individual candidates/options and retain their original identities.
function ballotVotes(row, columns, individualCandidates = false){
  const result = {};
  for(const col of columns){
    if(!individualCandidates && /^bagimsiz\d+_ALDIGI_OY$/.test(col)) continue;
    if(row[col]) result[col] = row[col];
  }
  if(!individualCandidates){
    const named = Object.entries(row).reduce((s,[k,v])=>s+(/^bagimsiz\d+_ALDIGI_OY$/.test(k) ? (v||0) : 0),0);
    const independent = row.bagimsiz_TOPLAM_OY || named;
    if(independent) result.bagimsiz0_ALDIGI_OY = independent;
  }
  return result;
}
module.exports = {ballotVotes};
