const fs=require('node:fs');
const assert=require('node:assert/strict');
const path=require('node:path');
const vm=require('node:vm');
const root=path.resolve(__dirname,'..');
const read=p=>fs.readFileSync(path.join(root,p),'utf8');
const pattern=/https:\/\/(?:www\.)?buymeacoffee\.com\/divclass016/g;
for(const page of ['docs/index.html','docs/privacy/index.html','docs/terms/index.html']){
 const count=(read(page).match(pattern)||[]).length;
 assert.equal(count,1,page+' should have one optional support link');
}
const js=read('docs/assets/tool-ux.js');
assert.doesNotMatch(js,/function installCoffeeLine\(/,'No extra donation request after result');
assert.match(js,/function consolidateSupportLinks\(/);
let removed=0;
const links=[
 {closest(sel){return sel==='.oct-support'?this:null;},remove(){removed++}},
 {closest(){return null},remove(){removed++}}
];
const document={
 readyState:'complete',
 querySelector(selector){return selector.startsWith('a[')?links[0]:null},
 querySelectorAll(selector){return selector.includes('buymeacoffee')?links:[]}
};
vm.runInNewContext(js,{document,console,window:{}},{filename:'tool-ux.js'});
assert.equal(removed,1,'Remove the duplicate footer link while leaving the support area intact');
const generator=read('scripts/apply_commercial_polish.py');
const home=generator.slice(generator.indexOf('HOME_FOOTER'),generator.indexOf('SCRIPT_RE'));
assert.doesNotMatch(home,/>Support<\/a>/,'Homepage generator must not bring back a duplicate');
console.log('PASS: one support link on homepage, privacy and terms; calculator DOM dedupes footer and omits extra result prompt');
