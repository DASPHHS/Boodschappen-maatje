const assert=require("node:assert/strict");
const p=require("../recepten/persoonlijk_weekmenu.js");
const a=p.set(p.empty(),"jumbo",0,{id:"abc",title:"Champignonstoof"},2);
const b=p.set(a,"jumbo",1,{id:"abc",title:"Champignonstoof"},2);
assert.equal(p.portions(b,"jumbo","abc"),4);
assert.equal(p.portions(b,"ah","abc"),0);
assert.equal(p.portions(p.remove(b,"jumbo",0),"jumbo","abc"),2);
assert.equal(p.parse('{"ah":{"0":{"id":"x","portions":999}}}').ah[0],undefined);
assert.deepEqual(p.parse("{"),p.empty());
const rows=[
 {title:"Kip curry 1",category:"Kip",cuisine:"Indiaas",complete:true,nutrition:{priority:true}},
 {title:"Kip curry 2",category:"Kip",cuisine:"Indiaas",complete:true,nutrition:{priority:true}},
 {title:"Kip curry 3",category:"Kip",cuisine:"Indiaas",complete:true,nutrition:{priority:true}},
 {title:"Vispasta",category:"Vis",cuisine:"Italiaans",complete:true,nutrition:{priority:true}},
 {title:"Tofu wok",category:"Vegetarisch",cuisine:"Thais",complete:true,nutrition:{priority:true}},
 {title:"Niet geprijsd",category:"Vis",complete:false,nutrition:{priority:true}}
];
const out=p.diversify(rows);
assert.equal(out.length,rows.length);
assert.equal(out.at(-1).title,"Niet geprijsd");
assert(out.slice(0,3).some(x=>x.category==="Vis"));
assert(out.slice(0,3).some(x=>x.category==="Vegetarisch"));
console.log("Persoonlijk weekmenu, porties, veiligheidscontrole en variatie OK");
