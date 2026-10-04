const {test}=require('node:test'),assert=require('node:assert/strict');
const {ballotVotes}=require('../scripts/pipelines/election_import/ballot_votes');
test('missing named independent columns use the official aggregate',()=>{
 assert.deepEqual(ballotVotes({parti1_ALDIGI_OY:6975,bagimsiz_TOPLAM_OY:3963},['parti1_ALDIGI_OY']),{parti1_ALDIGI_OY:6975,bagimsiz0_ALDIGI_OY:3963});
});
test('independent aggregate and named candidates are never counted twice',()=>{
 assert.deepEqual(ballotVotes({bagimsiz_TOPLAM_OY:10,bagimsiz1_ALDIGI_OY:7,bagimsiz2_ALDIGI_OY:3},['bagimsiz1_ALDIGI_OY','bagimsiz2_ALDIGI_OY']),{bagimsiz0_ALDIGI_OY:10});
});
test('aggregate rows retain the synthetic independent column exactly once',()=>{
 assert.deepEqual(ballotVotes({bagimsiz0_ALDIGI_OY:10},[]),{bagimsiz0_ALDIGI_OY:10});
});
test('presidential candidates and referendum options retain individual columns',()=>{
 assert.deepEqual(ballotVotes({bagimsiz1_ALDIGI_OY:7,bagimsiz2_ALDIGI_OY:3,bagimsiz_TOPLAM_OY:10},['bagimsiz1_ALDIGI_OY','bagimsiz2_ALDIGI_OY'],true),{bagimsiz1_ALDIGI_OY:7,bagimsiz2_ALDIGI_OY:3});
});
