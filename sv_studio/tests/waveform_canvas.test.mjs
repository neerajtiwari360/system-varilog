// Run with node sv_studio/tests/waveform_canvas.test.mjs (no npm dependencies).
import {readFile} from 'node:fs/promises';
import vm from 'node:vm';
import assert from 'node:assert/strict';

const source = await readFile(new URL('../ui/waveform_canvas.js', import.meta.url), 'utf8');
const sandbox = {
  document: {createElement:()=>({}), head:{appendChild:()=>{}}},
  devicePixelRatio:1, requestAnimationFrame:()=>1, cancelAnimationFrame:()=>{},
};
vm.runInNewContext(source.replace('export default', 'this.component ='), sandbox);
const component = sandbox.component;

function viewer() {
  const strokes=[], texts=[], path=[];
  const ctx={scale(){},fillRect(){},save(){},restore(){},rect(){},clip(){},setLineDash(){},
    beginPath(){path.length=0},moveTo(x,y){path.push(['M',x,y])},lineTo(x,y){path.push(['L',x,y])},
    closePath(){},stroke(){strokes.push({color:this.strokeStyle,path:path.map(p=>[...p])})},
    fillText(text,x,y){texts.push([text,x,y])},measureText(text){return {width:text.length*7}}};
  const canvas={style:{},getContext:()=>ctx,getBoundingClientRect:()=>({left:0,width:500})};
  const state={...component.data(),data:{end:10,timescale:'1ns',signals:[{name:'tb.clk',code:'!',width:1,kind:'wire'}],changes:{'!':[[0,'0'],[5,'1'],[10,'0']]}},
    $refs:{canvas,scroll:{clientWidth:500}},selected:['tb.clk']};
  for(const [key,method] of Object.entries(component.methods))state[key]=method.bind(state);
  for(const [key,getter] of Object.entries(component.computed))Object.defineProperty(state,key,{get:()=>getter.call(state)});
  state.span=10;
  return {state,strokes,texts};
}

{
  const {state,strokes}=viewer();state.draw();
  assert(strokes.some(s=>s.path.some(p=>p[0]==='M'&&p[1]===180&&p[2]===58)&&s.path.some(p=>p[0]==='L'&&p[1]===334&&p[2]===58)), 'low trace must end exactly at tick 5');
  assert(strokes.some(s=>s.path.some(p=>p[0]==='L'&&p[1]===488&&p[2]===36)), 'high trace must extend to tick 10');
}
{
  const {state,texts}=viewer();state.point({clientX:334});assert.equal(state.cursor,5);state.draw();
  assert(texts.some(t=>t[0]==='1'&&t[1]===6),'cursor should read new value at exact transition');
  state.zoom(.5);assert.equal(state.span,5);state.pan(1);assert(state.start<=5);state.fit();assert.equal(state.span,10);assert.equal(state.start,0);
}
{
  const {state,strokes}=viewer();state.data.changes['!']=[[0,'x'],[5,'z']];state.draw();
  assert(strokes.some(s=>s.color==='#f07e88'));assert(strokes.some(s=>s.color==='#dfb96b'));
  state.radix='hex';assert.equal(state.format('1'.repeat(80),'wire'),'FFFFFFFFFFFFFFFFFFFF');
  state.radix='dec';assert.equal(state.format('1111','wire'),'15');assert.equal(state.format('xz01','wire'),'XZ01');
  state.filter='missing';assert.equal(state.filtered.length,0);state.selected=[];state.draw();
}
{
  const {state}=viewer();assert.equal(state.shortName(state.data.signals[0]),'clk');
  state.data.timescale='1ps';state.data.end=150000;assert.equal(state.timeLabel(150000),'150 ns');
  assert.equal(state.timeLabel(500),'0.5 ns');
  state.data.timescale='10ns';state.data.end=100;assert.equal(state.timeLabel(100),'1 us');
  state.selected=Array.from({length:70},(_,i)=>String(i));state.limitSelection();assert.equal(state.selected.length,64);
}
export const result = '4 native waveform drawing/interaction checks passed';
