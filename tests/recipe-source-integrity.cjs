// Do not inadvertently present scraped third-party recipes as original content.
'use strict';
const fs=require('node:fs');
const assert=require('node:assert/strict');
const d=JSON.parse(fs.readFileSync('docs/data/recipe-sources.json','utf8'));
const domains={allerhande:'ah.nl',jumbo:'jumbo.com',voedingscentrum:'voedingscentrum.nl', '24kitchen':'24kitchen.nl',lidl:'lidl.nl'};
assert.equal(d.schema_version,1);
assert.equal(d.policy,'link_only');
assert.ok(d.sources.length>=4);
for(const source of d.sources){
 assert.equal(source.reuse,'link_only','Never copy source instructions or photos without permissions');
 assert.ok(source.name&&source.tag&&domains[source.id]);
 const u=new URL(source.url);
 assert.equal(u.protocol,'https:');
 const host=u.hostname.replace(/^www\./,'');
 assert.ok(host===domains[source.id]||host.endsWith('.'+domains[source.id]));
 assert.ok(!source.instructions&&!source.ingredients&&!source.image,
  'External directory must contain outbound links only');
}
const app=fs.readFileSync('docs/app.js','utf8');
assert.ok(app.includes('recipeSourceDirectory()'));
assert.ok(app.includes("load('data/recipe-sources.json')"));
assert.ok(!app.includes("const focus={\nlidl:"),'Fixed campaign IDs will leave the homepage stale');
console.log('Recipe source allowlist, outbound-only rights and dynamic offer highlights validated');
