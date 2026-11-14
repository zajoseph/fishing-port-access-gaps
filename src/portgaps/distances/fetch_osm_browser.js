// T3.1 geometry extraction, run in a web browser (the analysis workspace could not reach these hosts).
// 1) OSM land polygons: stream land-polygons-split-4326.zip with HTTP Range requests, inflate the
//    land_polygons.shp entry with DecompressionStream('deflate-raw'), and keep every shapefile record whose
//    bbox intersects lon [-126.6,-116.4], lat [31.9,49.6]. Output: concatenated raw .shp records
//    (8-byte big-endian record header + content), read by raster_osm.read_records().
//    Run from a page on https://osmdata.openstreetmap.de (same origin). Zip central directory gave
//    land_polygons.shp at local-header offset 231597, compressed size 925,850,949 (file of 2026-11-13 01:49 UTC).
// 2) OSM water polygons near harbors: Overpass query (out geom) for way/relation natural=water,
//    waterway=riverbank and leisure=marina inside a +/-0.12 deg lat (+/-0.162 deg lon) box around each of
//    the 58 harbors (marina polygons are dropped in osmwater.load()). Endpoint https://overpass-api.de/api/interpreter.
// The exact scripts used are reproduced below.
async function fetchLandRecords(){
  const u='https://osmdata.openstreetmap.de/download/land-polygons-split-4326.zip';
  const off=231597, hdr=new Uint8Array(await (await fetch(u,{headers:{Range:`bytes=${off}-${off+29}`}})).arrayBuffer());
  const dvh=new DataView(hdr.buffer); const start=off+30+dvh.getUint16(26,true)+dvh.getUint16(28,true), end=start+925850949-1;
  const reader=(await fetch(u,{headers:{Range:`bytes=${start}-${end}`}})).body.pipeThrough(new DecompressionStream('deflate-raw')).getReader();
  let buf=new Uint8Array(0),pos=0,gotHeader=false; const kept=[]; const X0=-126.6,X1=-116.4,Y0=31.9,Y1=49.6;
  while(true){const {done,value}=await reader.read(); if(done)break;
    const nb=new Uint8Array(buf.length-pos+value.length); nb.set(buf.subarray(pos)); nb.set(value,buf.length-pos); buf=nb; pos=0;
    const dv=new DataView(buf.buffer); if(!gotHeader){if(buf.length<100)continue; pos=100; gotHeader=true;}
    while(buf.length-pos>=8){const clen=dv.getInt32(pos+4,false)*2; if(buf.length-pos<8+clen)break; const c=pos+8;
      const xmin=dv.getFloat64(c+4,true),ymin=dv.getFloat64(c+12,true),xmax=dv.getFloat64(c+20,true),ymax=dv.getFloat64(c+28,true);
      if(xmax>=X0&&xmin<=X1&&ymax>=Y0&&ymin<=Y1) kept.push(buf.slice(pos,pos+8+clen)); pos+=8+clen;}}
  return new Blob(kept);   // saved as osm_land_polygons_split4326_uswest_records.bin
}
async function fetchWater(P){ // P = [[lat,lon],...] for the 58 harbors (ports.csv order)
  const d=0.12; let q='[out:json][timeout:600];(';
  for(const [la,lo] of P){const b=`${(la-d).toFixed(3)},${(lo-d*1.35).toFixed(3)},${(la+d).toFixed(3)},${(lo+d*1.35).toFixed(3)}`;
    q+=`way["natural"="water"](${b});relation["natural"="water"](${b});way["waterway"="riverbank"](${b});relation["waterway"="riverbank"](${b});way["leisure"="marina"](${b});`;}
  q+=');out geom;';
  return (await fetch('https://overpass-api.de/api/interpreter',{method:'POST',body:'data='+encodeURIComponent(q),headers:{'Content-Type':'application/x-www-form-urlencoded'}})).text();
}
