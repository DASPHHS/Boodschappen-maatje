/* Regressietests voor de aparte aanbiedingfilters; zonder browser of netwerk. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const html = fs.readFileSync("recepten/index.html", "utf8");
const script = html.match(/<script>([\s\S]*?)<\/script>/i)?.[1];
assert.ok(script, "Ingesloten JavaScript aanwezig");
assert.doesNotThrow(() => new Function(script), "HTML JavaScript heeft geldige syntax");
for (const id of [
  "deal-filters", "recipe-filters", "deal-search", "deal-category", "deal-status",
  "deal-promotion", "deal-minimum", "deal-sort", "deal-reset", "deal-count",
]) {
  assert.ok(html.includes('id="' + id + '"'), "Filter ontbreekt: " + id);
}
assert.ok(script.includes('"recipe-filters").hidden=state.mode==="deals"'), "Receptfilters verdwijnen in dealmodus");
assert.ok(script.includes('"deal-filters").hidden=state.mode!=="deals"'), "Dealfilters verschijnen alleen in dealmodus");
assert.ok(script.includes('"cart-panel").hidden=state.mode==="deals"'), "Receptmand verdwijnt in dealmodus");
assert.ok(html.includes("../aanbiedingen.html"), "Aanvullende folders blijven bereikbaar");

const first = script.indexOf(" const DEAL_CATEGORIES=");
const end = script.indexOf("\n function renderDeals(){", first);
assert.ok(first >= 0 && end > first, "Losse categoriefuncties aanwezig");
const {dealCategory, dealPromotion, words} = new Function(script.slice(first, end) + ";return {dealCategory,dealPromotion,words};")();
const cases = [
  ["AH Passievruchten zak", "produce"],
  ["Jumbo Bloemkool", "produce"],
  ["Jumbo Kipburgers 250 g", "protein"],
  ["Campina Magere Kwark Naturel", "dairy"],
  ["AH Volkoren pasta", "grains"],
  ["Red Bull Energy drink", "drinks"],
  ["Ariel Wasmiddel", "care"],
  ["Kruidvat Shampoo", "care"],
  ["Chips paprika", "pantry"],
  ["Niet-herkend product", "other"]
];
for (const [name, expected] of cases) {
  assert.equal(dealCategory({name}), expected, name);
}
assert.equal(words("Crème").trim(), "creme", "Accentnormalisatie werkt");
assert.equal(dealPromotion({is_loyalty: true, multi_buy_quantity: 2, multi_buy_price: 3}), "loyalty");
assert.equal(dealPromotion({multi_buy_quantity: 2, multi_buy_price: 3}), "bundle");
assert.equal(dealPromotion({multi_buy_quantity: 0}), "other");
console.log("Aanbiedingenfilters: HTML, weergavemodus en categorieën gecontroleerd.");
