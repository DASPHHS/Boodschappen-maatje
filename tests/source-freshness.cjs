const assert=require('node:assert/strict'),f=require('../docs/source-freshness.js');
const item={id:'a',name:'Product',price:1.20,start_date:'2026-10-26',end_date:'2026-11-01'},feed={status:'ok',offers:[item]};
assert.equal(f.ageDays('2026-10-28','2026-10-29'),1);
assert.equal(f.available(feed,'2026-10-28T08:30:00+01:00','2026-10-29')[0].source_scan_stale,true);
assert.equal(f.available(feed,'2026-10-28T08:30:00+01:00','2026-10-28')[0].source_scan_stale,undefined);
assert.equal(f.available(feed,'2026-10-28T08:30:00+01:00','2026-10-30').length,0);
assert.equal(f.available({...feed,offers:[{...item,end_date:'2026-10-28'}]},'2026-10-28T08:30:00+01:00','2026-10-29').length,0);
assert.equal(f.available({...feed,status:'error'},'2026-10-28T08:30:00+01:00','2026-10-29').length,0);
console.log('Grace period: yesterday valid with warning; expired and older excluded');
