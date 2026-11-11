export default {
  template: `
    <div class="sv-wave">
      <div class="sv-wave-tools">
        <button @click="showSignals=!showSignals; schedule()" :aria-expanded="showSignals">Signals {{showSignals ? '▴' : '▾'}}</button>
        <button @click="zoom(0.5)">Zoom +</button><button @click="zoom(2)">Zoom −</button>
        <button @click="fit">Fit</button><button @click="pan(-0.4)">◀</button><button @click="pan(0.4)">▶</button>
        <label>Values <select v-model="radix" @change="draw"><option value="hex">Hex</option><option value="bin">Binary</option><option value="dec">Unsigned</option></select></label>
        <span :title="cursor === null ? '' : cursor + ' ticks × ' + data.timescale">Cursor: {{cursor === null ? 'click a trace' : timeLabel(cursor)}}</span>
      </div>
      <div class="sv-wave-body">
        <aside v-if="showSignals"><input v-model="filter" placeholder="Find signal…" aria-label="Find waveform signal">
          <div class="sv-wave-select"><button @click="selectAll">Select all (64 max)</button><button @click="selected=[]; schedule()">Clear</button></div>
          <label v-for="s in filtered" :key="s.name" :title="s.name"><input type="checkbox" :value="s.name" v-model="selected" @change="limitSelection"><span class="sv-signal-name">{{shortName(s)}}</span> <small>[{{s.width}}]</small></label>
        </aside>
        <div class="sv-wave-scroll" ref="scroll"><canvas ref="canvas" @click="point" @wheel.prevent="wheel" aria-label="Digital signal waveform traces"></canvas></div>
      </div>
      <div class="sv-wave-footer">{{timeLabel(start)}} – {{timeLabel(start+span)}} · {{visible.length}} traces · click: cursor · wheel: zoom · Shift+wheel: pan · X / Z</div>
    </div>`,
  props: {data: Object},
  data() {return {selected: [], filter:'', start:0, span:1, cursor:null, radix:'hex', showSignals:false}},
  computed: {
    rootScope(){const root=this.data.signals[0]?.name.split('.')[0];return root&&this.data.signals.every(s=>s.name.startsWith(root+'.'))?root+'.':''},
    filtered() {return this.data.signals.filter(s=>s.name.toLowerCase().includes(this.filter.toLowerCase()))},
    visible() {return this.data.signals.filter(s=>this.selected.includes(s.name)).slice(0,64)},
  },
  mounted() {
    const codes = new Set();
    this.selected = this.data.signals.filter(s=>{if(codes.has(s.code)) return false; codes.add(s.code);return true}).slice(0,12).map(s=>s.name);
    this.span=Math.max(1,this.data.end);
    this.observer=new ResizeObserver(()=>this.schedule());this.observer.observe(this.$refs.scroll);
    this.schedule();
  },
  beforeUnmount() {this.observer?.disconnect();cancelAnimationFrame(this.pending)},
  methods: {
    shortName(signal){return this.rootScope?signal.name.slice(this.rootScope.length):signal.name},
    timeLabel(ticks){const match=this.data.timescale.match(/^(1|10|100)(s|ms|us|ns|ps|fs)$/);if(!match)return Math.round(ticks)+' ticks';const units={s:1,ms:1e-3,us:1e-6,ns:1e-9,ps:1e-12,fs:1e-15};const factor=Number(match[1])*units[match[2]],duration=Math.max(1,this.data.end)*factor;let unit='fs';for(const [name,scale] of Object.entries(units)){if(duration>=scale*.999999){unit=name;break}}return Number((ticks*factor/units[unit]).toPrecision(6))+' '+unit},
    limitSelection(){if(this.selected.length>64)this.selected=this.selected.slice(0,64);this.schedule()},
    schedule(){cancelAnimationFrame(this.pending);this.pending=requestAnimationFrame(()=>this.draw())},
    selectAll(){this.selected=this.filtered.slice(0,64).map(s=>s.name);this.schedule()},
    fit(){this.start=0;this.span=Math.max(1,this.data.end);this.schedule()},
    zoom(factor){const center=this.cursor??(this.start+this.span/2);this.span=Math.min(Math.max(1,this.data.end),Math.max(1,this.span*factor));this.start=Math.round(Math.max(0,Math.min(center-this.span/2,Math.max(0,this.data.end-this.span))));this.schedule()},
    pan(fraction){this.start=Math.round(Math.max(0,Math.min(this.start+this.span*fraction,Math.max(0,this.data.end-this.span))));this.schedule()},
    wheel(e){if(e.shiftKey)this.pan(e.deltaY>0?.15:-.15);else this.zoom(e.deltaY>0?1.25:.8)},
    point(e){const rect=this.$refs.canvas.getBoundingClientRect();const x=e.clientX-rect.left;if(x<180)return;this.cursor=Math.round(Math.min(this.data.end,Math.max(0,this.start+(x-180)/(rect.width-192)*this.span)));this.schedule()},
    index(events,time){let lo=0,hi=events.length;while(lo<hi){const mid=(lo+hi)>>1;if(events[mid][0]<=time)lo=mid+1;else hi=mid}return lo-1},
    format(value,kind){if(value==null)return 'X';if(['real','realtime','string'].includes(kind))return value;if(/[xz]/i.test(value))return value.toUpperCase();if(this.radix==='bin')return value;try{return BigInt('0b'+value).toString(this.radix==='hex'?16:10).toUpperCase()}catch{return value}},
    draw(){
      const canvas=this.$refs.canvas;if(!canvas)return;
      const width=Math.max(360,this.$refs.scroll.clientWidth),height=Math.max(130,42+this.visible.length*32),ratio=devicePixelRatio||1;
      canvas.width=width*ratio;canvas.height=height*ratio;canvas.style.width=width+'px';canvas.style.height=height+'px';
      const ctx=canvas.getContext('2d');ctx.scale(ratio,ratio);ctx.fillStyle='#101821';ctx.fillRect(0,0,width,height);ctx.font='12px Consolas, monospace';
      const left=180,right=width-12,scale=(right-left)/this.span,x=t=>left+(t-this.start)*scale;
      ctx.strokeStyle='#293746';ctx.fillStyle='#aab9ca';
      ctx.fillText('Signal / value',6,18);const ticks=Math.max(2,Math.floor((right-left)/100));for(let i=0;i<=ticks;i++){const xx=left+(right-left)*i/ticks;ctx.beginPath();ctx.moveTo(xx,27);ctx.lineTo(xx,height);ctx.stroke();ctx.textAlign=i===ticks?'right':i===0?'left':'center';ctx.fillText(this.timeLabel(this.start+this.span*i/ticks),xx,18)}ctx.textAlign='left';
      this.visible.forEach((signal,row)=>{
        const y=42+row*32,events=this.data.changes[signal.code]||[],at=this.cursor??this.start,idx=this.index(events,at),current=idx>=0?events[idx][1]:null;
        ctx.fillStyle='#d9e5f1';ctx.save();ctx.beginPath();ctx.rect(4,y-10,170,30);ctx.clip();ctx.fillText(this.shortName(signal),6,y+1);ctx.fillStyle='#81c9f0';ctx.fillText(this.format(current,signal.kind),6,y+16);ctx.restore();
        ctx.strokeStyle='#23303e';ctx.beginPath();ctx.moveTo(0,y+27);ctx.lineTo(width,y+27);ctx.stroke();
        let i=Math.max(-1,this.index(events,this.start));let t=this.start,steps=0;
        while(t<this.start+this.span){
          const value=i>=0?events[i][1]:'x'.repeat(signal.width),next=i+1<events.length?events[i+1][0]:this.start+this.span;
          const end=Math.min(next,this.start+this.span),a=x(t),b=x(end),color=/x/i.test(value)?'#f07e88':/z/i.test(value)?'#dfb96b':'#6edba9';ctx.strokeStyle=color;ctx.fillStyle=color;
          if(signal.width===1&&!['real','realtime','string'].includes(signal.kind)&&['0','1','x','z'].includes(value)){
            const yy=value==='1'?y-6:value==='0'?y+16:y+5;
            ctx.setLineDash(/[xz]/.test(value)?[3,3]:[]);ctx.beginPath();ctx.moveTo(a,yy);ctx.lineTo(b,yy);ctx.stroke();ctx.setLineDash([]);
            if(next<=this.start+this.span&&i+1<events.length){const v=events[i+1][1];ctx.beginPath();ctx.moveTo(b,yy);ctx.lineTo(b,v==='1'?y-6:v==='0'?y+16:y+5);ctx.stroke()}
          }else{
            const bevel=Math.min(4,Math.max(0,(b-a)/2));ctx.beginPath();ctx.moveTo(a,y+5);ctx.lineTo(a+bevel,y-6);ctx.lineTo(b-bevel,y-6);ctx.lineTo(b,y+5);ctx.lineTo(b-bevel,y+16);ctx.lineTo(a+bevel,y+16);ctx.closePath();ctx.stroke();
            const label=this.format(value,signal.kind);if(b-a>ctx.measureText(label).width+12)ctx.fillText(label,a+6,y+9);
          }
          if(next>=this.start+this.span)break;i++;t=next;
          // Bound drawing work at low zoom; exact cursor values still use all events.
          const pixelTime=this.start+(Math.floor(x(next)-left)+1)/scale;
          const skip=this.index(events,pixelTime);if(skip>i){ctx.strokeStyle='#a8bdcc';ctx.beginPath();ctx.moveTo(x(next),y-6);ctx.lineTo(x(next),y+16);ctx.stroke();i=skip;t=events[i][0]}
          if(++steps>width*3)break;
        }
      });
      if(this.cursor!==null&&this.cursor>=this.start&&this.cursor<=this.start+this.span){ctx.strokeStyle='#f4d775';ctx.beginPath();ctx.moveTo(x(this.cursor),25);ctx.lineTo(x(this.cursor),height);ctx.stroke()}
      if(!this.visible.length){ctx.fillStyle='#aab9ca';ctx.fillText('Select signals from the list to display traces.',240,70)}
    },
  },
};

const style=document.createElement('style');style.textContent=`
.sv-wave{height:100%;min-height:0;flex:1;width:100%;display:flex;flex-direction:column;background:#101821;color:#d9e5f1;font:12px 'Segoe UI',sans-serif;border:1px solid #334353;border-radius:4px;overflow:hidden;box-sizing:border-box}
.sv-wave-tools{display:flex;gap:6px;align-items:center;flex-wrap:wrap;padding:5px 8px;border-bottom:1px solid #334353;flex-shrink:0;font-size:11px}
.sv-wave button,.sv-wave select,.sv-wave input{font-size:11px;line-height:18px;background:#1c2b3a;color:#d9e5f1;border:1px solid #405569;border-radius:3px;padding:2px 6px;box-sizing:border-box}
.sv-wave button{cursor:pointer;white-space:nowrap}.sv-wave-tools label{display:flex;align-items:center;gap:5px}.sv-wave-tools>span{margin-left:auto;white-space:nowrap;color:#c6d4e4}
.sv-wave-body{display:flex;flex:1;min-height:0;overflow:hidden}.sv-wave aside{width:230px;flex-shrink:0;min-width:0;overflow:auto;padding:6px;border-right:1px solid #334353;box-sizing:border-box}
.sv-wave aside>input{width:100%}.sv-wave aside label{display:flex;gap:5px;align-items:center;white-space:nowrap;padding:3px 0;min-width:0;font-size:11px}.sv-signal-name{overflow:hidden;text-overflow:ellipsis;min-width:0;flex:1}.sv-wave aside small{opacity:.6;flex-shrink:0}.sv-wave aside input[type=checkbox]{flex-shrink:0;width:13px;height:13px}
.sv-wave-select{display:flex;gap:4px;margin:5px 0}.sv-wave-select button{font-size:10px}.sv-wave-scroll{flex:1;min-width:0;min-height:0;overflow:auto;overscroll-behavior:contain}.sv-wave canvas{display:block;cursor:crosshair}
.sv-wave-footer{padding:4px 8px;border-top:1px solid #334353;color:#9eb0c3;font-size:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;flex-shrink:0}
@media(max-width:800px){.sv-wave aside{width:180px}.sv-wave-tools>span{margin-left:0}}
`;document.head.appendChild(style);
