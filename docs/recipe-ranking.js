/* Promotions on the protein/main ingredient outrank a cheap incidental vegetable.
   The rank measures relevance, not savings: savings need a complete comparison. */
(function(root,factory){
 const obj=factory();
 if(typeof module==='object'&&module.exports)module.exports=obj;
 if(root)root.MaatjeRanking=obj;
})(typeof window!=='undefined'?window:null,function(){
 function score(info){
  const confirmed=info?.confirmed||[],anchors=info?.anchors||[];
  const main=(a)=>a.role==='eiwitbron';
  return confirmed.filter(main).length*12+anchors.filter(main).length*8+
   confirmed.filter(x=>!main(x)).length*3+anchors.filter(x=>!main(x)).length;
 }
 function mainOffer(info){return [...(info?.confirmed||[]),...(info?.anchors||[])].find(x=>x.role==='eiwitbron')||null}
 return {score,mainOffer};
});
