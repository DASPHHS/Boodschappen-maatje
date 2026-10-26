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

const fs=require("node:fs");
const html=fs.readFileSync("recepten/index.html","utf8");
assert(html.includes('id="personal-weekmenu"'));
assert(html.includes('data-plan-add'));
assert(html.includes('data-cart-recipe'));
assert(html.includes('data-show-all'));
const begin=html.indexOf(" function calcCart(){");
const end=html.indexOf(" function renderCart(){",begin);
assert(begin>0&&end>begin);
const recipe={id:"1",title:"Champignons",ingredients:[{key:"champignons",label:"champignons",
  product:"Champignons 400 g",package:"400 g",required:600,unit:"g",package_size:400,
  unit_price:1.69}],missing:[],pantry:[]};
const state={data:{recipes:{jumbo:[recipe]}},selected:[{store:"jumbo",id:"1"}]};
let planned=4;
const factory=new Function("state","active","plannedPortions",
 html.slice(begin,end)+"return calcCart();");
const cart=()=>factory(state,()=>state.selected,()=>planned);
const original=cart();
assert.equal(original.items[0].required,600);
assert.equal(original.items[0].packages,2);
assert.equal(original.total,3.38);
assert.equal(original.items[0].packages*400-original.items[0].required,200);
planned=2;
const half=cart();
assert.equal(half.items[0].required,300);
assert.equal(half.items[0].packages,1);
assert.equal(half.total,1.69);
assert.equal(half.items[0].packages*400-half.items[0].required,100);
console.log("Champignons: 600 g nodig, 800 g gekocht en 200 g over; schaalbaar naar 2 porties.");
