'use strict';
const assert=require('node:assert/strict');
const week=require('../docs/weekdeals-engine.js');
const today='2026-11-01';
assert.deepEqual(week.week(today,'now'),{from:'2026-10-26',through:'2026-11-01'});
assert.deepEqual(week.week(today,'next'),{from:'2026-11-02',through:'2026-11-08'});
const base={source_provider:'PrijsProfeet',id:'pp-100',name:'Jumbo Pindakaas naturel 600g',price:1.45,
 source:{url:'https://www.jumbo.com/producten/test-12345STK'},
 promotion_status:'active',start_date:'2026-10-30',end_date:'2026-11-07'};
const future={...base,id:'pp-101',start_date:'2026-11-02',end_date:'2026-11-08',promotion_status:'upcoming'};
const passed={status:'ok',offers:[base],upcoming_offers:[future]};
assert.deepEqual(week.next('jumbo',passed,today).map(x=>x.id),['pp-100','pp-101'],
 'Next week contains a current deal running into next week and an upcoming deal');
assert.deepEqual(week.next('jumbo',{...passed,upcoming_offers:[]},today).map(x=>x.id),['pp-100']);
assert.deepEqual(week.next('ah',{status:'stale',offers:[base]},today),[],
 'Stale feed must not be falsely presented as a live upcoming week');
assert.equal(week.eligible({...base,online_only:true},'jumbo',today,'next'),false);
assert.equal(week.eligible({...base,price_conflict:'shops differ'},'jumbo',today,'next'),false);
assert.equal(week.eligible({...base,end_date:'2026-11-01'},'jumbo',today,'next'),false);
assert.equal(week.eligible({...future,start_date:'2026-11-10',end_date:'2026-11-12'},'jumbo',today,'next'),false);
assert.equal(week.eligible({...future,price:NaN},'jumbo',today,'next'),false);
assert.equal(week.eligible({...future,source:{url:'http://bad'}},'jumbo',today,'next'),false);
assert.equal(week.eligible({...future,source:{url:'https://example.com'},price:2.5},'lidl',today,'next'),true);
assert.equal(week.eligible({...future,source:{url:'https://example.com'},price:2.5},'ah',today,'next'),true);
assert.equal(week.eligible({...future},'aldi',today,'next'),false);
assert.equal(week.week('invalid','now'),null);
console.log('Speciale Deals week principle: this/next week, no future price presented as current, three supermarkets only');
