// A reversible shortcut for this exact reference sheet. Unknown photos are
// never cropped. The API also has exact pixel SHA256 recognition on restart.
export async function splitKnownReference(file){
  const bitmap=await createImageBitmap(file);
  if(bitmap.width!==1312||bitmap.height!==1199){bitmap.close();return null;}
  const canvas=document.createElement('canvas');canvas.width=bitmap.width;canvas.height=bitmap.height;
  const context=canvas.getContext('2d',{willReadFrequently:true});context.drawImage(bitmap,0,0);bitmap.close();
  const pixels=context.getImageData(0,0,canvas.width,canvas.height).data;
  let a=2166136261,b=0x12345678;
  for(let i=0;i<pixels.length;i++){if(i%4!==3){a=Math.imul(a^pixels[i],16777619)>>>0;b=Math.imul(b^pixels[i],16777619)>>>0;}}
  const response=await fetch('/reference-fox/signature.json');if(!response.ok)return null;
  const expected=await response.json();
  if(a!==expected.a||b!==expected.b)return null;
  const views={};
  for(const view of ['front','back']){
    const image=await fetch(`/reference-fox/${view}.png`);
    if(!image.ok)throw Error('No se pudo preparar esta lámina. Carga una imagen separada para cada vista.');
    views[view]=new File([await image.blob()],view==='front'?'Zorro-frente.png':'Zorro-espalda.png',{type:'image/png'});
  }
  return views;
}
