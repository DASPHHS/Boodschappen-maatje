'use strict';
const api=require('../docs/recipe-products.js');
let input='';process.stdin.setEncoding('utf8');process.stdin.on('data',chunk=>input+=chunk);
process.stdin.on('end',()=>{
 const records=JSON.parse(input);
 process.stdout.write(JSON.stringify(records.map(name=>api.profile(name,{ingredient:true})).filter(Boolean)));
});
