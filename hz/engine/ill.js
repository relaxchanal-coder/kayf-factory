// مكتبة رسوم «حكايا الزمان»: مجسّمات وشخصيات فلات موشن. كل دالة ترجع SVG داخل مربّع -600..600 × -600..400
// k = تقدّم الظهور (0..1)، T = الزمن، A/A2 = لون المشهد
const _e=x=>Math.max(0,Math.min(1,x));
const _up=(k,a,d)=>{const x=_e((k-a)/d);return 1-Math.pow(1-x,3)};
const _bk=(k,a,d)=>{const x=_e((k-a)/d);if(x>=1)return 1;return 1+2.7*Math.pow(x-1,3)+1.7*Math.pow(x-1,2)};
const _svg=(inner,defs='')=>`<svg viewBox="-600 -600 1200 1000" width="100%" height="100%" style="overflow:visible"><defs>${defs}</defs>${inner}</svg>`;
const _grad=(id,a,b,vert)=>`<linearGradient id="${id}" x1="0" y1="0" x2="${vert?0:1}" y2="${vert?1:0}"><stop offset="0" stop-color="${a}"/><stop offset="1" stop-color="${b}"/></linearGradient>`;
const _glow=(id,c)=>`<radialGradient id="${id}"><stop offset="0" stop-color="${c}" stop-opacity=".55"/><stop offset="1" stop-color="${c}" stop-opacity="0"/></radialGradient>`;
let _uid=0;const U=p=>p+(++_uid);
const ILL={};
const rise=(k,a,d,dy=80)=>{const u=_up(k,a,d);return `opacity="${u}" transform="translate(0,${(1-u)*dy})"`};
const pop=(k,a,d,cx=0,cy=0)=>{const u=_bk(k,a,d);return `opacity="${_e(u*1.5)}" transform="translate(${cx},${cy}) scale(${Math.max(.001,u)}) translate(${-cx},${-cy})"`};
// ---------- أرضية عامة ----------
function ground(k,c='#b48a52',y=300){const u=_up(k,0,.25);return `<ellipse cx="0" cy="${y+30}" rx="${560*u}" ry="40" fill="rgba(0,0,0,.35)"/><rect x="${-520*u}" y="${y}" width="${1040*u}" height="26" rx="13" fill="${c}"/>`}
// ---------- قبة الصخرة ----------
ILL.dome=(k,T,A,A2)=>{const g=U('g');const sh=.5+.5*Math.sin(T*2);
 const tiles=[...Array(12)].map((_,i)=>`<rect x="${-232+i*39}" y="150" width="30" height="70" rx="15" fill="url(#${g}t)" stroke="#c4e3ff" stroke-width="2"/>`).join('');
 const win=[...Array(8)].map((_,i)=>`<rect x="${-128+i*33}" y="12" width="16" height="34" rx="8" fill="#0b1a3a" stroke="#c4e3ff" stroke-width="1.5"/>`).join('');
 const cyp=(x,s)=>`<g transform="translate(${x},300) scale(${s*_up(k,.4,.4)})"><path d="M0 0 C-22 -60 -16 -150 0 -200 C16 -150 22 -60 0 0Z" fill="#1f7a5a"/><path d="M0 0 C-10 -60 -6 -150 0 -200 C2 -150 4 -60 0 0Z" fill="#2fa77a"/></g>`;
 const merl=[...Array(26)].map((_,i)=>`<rect x="${-520+i*40}" y="164" width="22" height="20" fill="#c9a36a"/>`).join('');
 return _svg(`<circle cx="0" cy="-40" r="${380*_up(k,.6,.3)}" fill="url(#${g}g)"/>
  <g ${rise(k,.1,.3,120)}><rect x="-520" y="184" width="1040" height="116" fill="#b48a52"/>${merl}<rect x="-450" y="110" width="90" height="190" fill="#a77c45"/><rect x="360" y="110" width="90" height="190" fill="#a77c45"/></g>
  ${cyp(-310,1)}${cyp(-260,.8)}${cyp(290,1)}${cyp(340,.75)}
  <g ${rise(k,0,.25,60)}><rect x="-300" y="260" width="600" height="40" rx="6" fill="#e8d8b8"/></g>
  <g ${rise(k,.3,.3,80)}><rect x="-250" y="90" width="500" height="170" fill="url(#${g}o)"/><rect x="-250" y="90" width="500" height="24" fill="#f4f0e6"/>${tiles}<rect x="-36" y="150" width="72" height="110" rx="36" fill="#0b1a3a" stroke="#c4e3ff" stroke-width="3"/></g>
  <g ${rise(k,.5,.25,60)}><rect x="-150" y="0" width="300" height="90" fill="url(#${g}o)"/>${win}<rect x="-150" y="-6" width="300" height="10" fill="#f4f0e6"/></g>
  <g transform="translate(0,-6) scale(${_up(k,.62,.3)})"><path d="M-160 0 C-160 -120 -70 -190 0 -205 C70 -190 160 -120 160 0Z" fill="url(#${g}d)" stroke="#8a5a0a" stroke-width="3"/><path d="M-110 -20 C-100 -110 -40 -165 0 -180" fill="none" stroke="#fff6d0" stroke-width="8" stroke-linecap="round" opacity="${.35+.4*sh}"/></g>
  <g ${rise(k,.85,.15,30)}><g transform="translate(0,-240)"><rect x="-3" y="0" width="6" height="30" fill="#ffd76a"/><path d="M0 -40 a22 22 0 1 0 0.1 0 M6 -36 a17 17 0 1 0 0.1 0" fill="#ffd76a" fill-rule="evenodd"/></g></g>`,
  `<linearGradient id="${g}d" x1="0" x2="1"><stop offset="0" stop-color="#b07a12"/><stop offset="${.35+.3*sh}" stop-color="#ffe9a0"/><stop offset="1" stop-color="#c8901c"/></linearGradient>${_grad(g+'t','#3aa0ff','#1446a8',1)}<linearGradient id="${g}o" x1="0" x2="1"><stop offset="0" stop-color="#1c5fc4"/><stop offset=".5" stop-color="#3d8ef0"/><stop offset="1" stop-color="#173f8f"/></linearGradient>${_glow(g+'g',A2)}`)};
// ---------- قلعة ----------
ILL.castle=(k,T,A,A2,o={})=>{const g=U('c');const st=o.stone||'#a8875a',st2=o.stone2||'#8c6e45';
 const tower=(x,h,w,d)=>`<g ${rise(k,d,.3,120)}><rect x="${x-w/2}" y="${300-h}" width="${w}" height="${h}" fill="${st}"/><rect x="${x-w/2}" y="${300-h}" width="${w*.35}" height="${h}" fill="${st2}" opacity=".5"/>${[...Array(Math.round(w/30))].map((_,i)=>`<rect x="${x-w/2+i*30}" y="${300-h-22}" width="18" height="22" fill="${st}"/>`).join('')}<rect x="${x-9}" y="${300-h+40}" width="18" height="34" rx="9" fill="#2a1a0c"/></g>`;
 const flag=(x,y,d)=>`<g ${rise(k,d,.2,30)}><rect x="${x}" y="${y-90}" width="5" height="90" fill="#3a2a1a"/><path d="M${x+5} ${y-90} Q${x+45} ${y-80+8*Math.sin(T*4+x)} ${x+80} ${y-88} L${x+80} ${y-52} Q${x+45} ${y-44+8*Math.sin(T*4+x+1)} ${x+5} ${y-54}Z" fill="${A}"/></g>`;
 return _svg(`<circle cx="0" cy="0" r="${420*_up(k,.5,.4)}" fill="url(#${g}g)"/>
  <g ${rise(k,0,.25,60)}><path d="M-560 300 Q-300 200 0 210 Q300 200 560 300Z" fill="#5a4630"/></g>
  <g ${rise(k,.1,.3,100)}><rect x="-330" y="90" width="660" height="210" fill="${st}"/>${[...Array(22)].map((_,i)=>`<rect x="${-330+i*30}" y="68" width="18" height="22" fill="${st}"/>`).join('')}
   ${[...Array(5)].map((_,r)=>[...Array(11)].map((_,c)=>`<rect x="${-330+c*60+(r%2)*30}" y="${100+r*38}" width="56" height="34" fill="none" stroke="${st2}" stroke-width="2" opacity=".5"/>`).join('')).join('')}
   <path d="M-60 300 v-110 a60 60 0 0 1 120 0 v110z" fill="#2a1a0c"/><path d="M-60 300 v-110 a60 60 0 0 1 120 0 v110z" fill="none" stroke="#d9b77a" stroke-width="6"/></g>
  ${tower(-330,330,120,.25)}${tower(330,330,120,.3)}${tower(0,430,150,.4)}
  ${flag(-5,-130,.7)}${flag(-335,-30,.75)}${flag(325,-30,.8)}`,_glow(g+'g',A2))};
// ---------- مسجد عام (قبة + مئذنتان) ----------
ILL.mosque=(k,T,A,A2,o={})=>{const g=U('m');const dc=o.dome||'#2fae6a',dc2=o.dome2||'#7fe0a8',wall=o.wall||'#efe6d2';const sh=.5+.5*Math.sin(T*2);
 const minaret=(x,d)=>`<g ${rise(k,d,.3,160)}><rect x="${x-26}" y="-210" width="52" height="510" fill="${wall}"/><rect x="${x-40}" y="-120" width="80" height="18" rx="4" fill="#cdbf9f"/><rect x="${x-40}" y="20" width="80" height="18" rx="4" fill="#cdbf9f"/><path d="M${x-26} -210 L${x} -300 L${x+26} -210Z" fill="${dc}"/><circle cx="${x}" cy="-312" r="9" fill="#ffd76a"/><rect x="${x-8}" y="-170" width="16" height="30" rx="8" fill="#3a2a1a"/></g>`;
 return _svg(`<circle cx="0" cy="-20" r="${400*_up(k,.55,.35)}" fill="url(#${g}g)"/>${ground(k,'#d7c7a3')}
  ${minaret(-330,.2)}${minaret(330,.25)}
  <g ${rise(k,.1,.3,100)}><rect x="-260" y="60" width="520" height="240" fill="${wall}"/>${[...Array(5)].map((_,i)=>`<path d="M${-220+i*95} 300 v-120 a35 35 0 0 1 70 0 v120z" fill="#3a2a1a"/><path d="M${-220+i*95} 300 v-120 a35 35 0 0 1 70 0 v120" fill="none" stroke="${dc}" stroke-width="5"/>`).join('')}<rect x="-260" y="50" width="520" height="16" fill="#cdbf9f"/></g>
  <g transform="translate(0,50) scale(${_up(k,.45,.35)})"><rect x="-120" y="-60" width="240" height="60" fill="${wall}"/><path d="M-150 -60 C-150 -190 150 -190 150 -60Z" fill="url(#${g}d)"/><path d="M-100 -80 C-95 -140 -50 -170 -10 -176" stroke="#fff" stroke-width="7" fill="none" opacity="${.3+.4*sh}" stroke-linecap="round"/></g>
  <g ${rise(k,.8,.2,20)}><path d="M0 -230 a20 20 0 1 0 0.1 0 M6 -226 a15 15 0 1 0 0.1 0" fill="#ffd76a" fill-rule="evenodd"/><rect x="-3" y="-210" width="6" height="24" fill="#ffd76a"/></g>`,
  `<linearGradient id="${g}d" x1="0" x2="1"><stop offset="0" stop-color="${dc}"/><stop offset="${.4+.2*sh}" stop-color="${dc2}"/><stop offset="1" stop-color="${dc}"/></linearGradient>${_glow(g+'g',A2)}`)};
// ---------- الكعبة ----------
ILL.kaaba=(k,T,A,A2)=>{const g=U('k');
 return _svg(`<circle cx="0" cy="40" r="${420*_up(k,.5,.4)}" fill="url(#${g}g)"/>
  <g ${rise(k,0,.3,40)}><ellipse cx="0" cy="250" rx="520" ry="110" fill="#e9e4d8"/><ellipse cx="0" cy="250" rx="420" ry="85" fill="none" stroke="#cfc8b8" stroke-width="3"/><ellipse cx="0" cy="250" rx="320" ry="62" fill="none" stroke="#cfc8b8" stroke-width="3"/></g>
  ${[...Array(36)].map((_,i)=>{const a=i/36*6.283+T*.4,r=380+(i%3)*35;const u=_up(k,.5,.4);return `<circle cx="${Math.cos(a)*r}" cy="${250+Math.sin(a)*r*.22}" r="${7*u}" fill="#fff" opacity=".85"/>`}).join('')}
  <g ${rise(k,.15,.35,140)}><path d="M-190 260 L-190 -40 L40 -110 L240 -40 L240 230 L40 300Z" fill="#111"/><path d="M40 -110 L240 -40 L240 230 L40 300Z" fill="#1d1d1d"/>
   <path d="M-190 20 L40 -50 L240 20 L240 70 L40 0 L-190 70Z" fill="url(#${g}b)"/>
   <path d="M100 120 h60 v130 h-60z" fill="url(#${g}b)" opacity=".9"/></g>`,
  `<linearGradient id="${g}b" x1="0" x2="1"><stop offset="0" stop-color="#b8860b"/><stop offset=".5" stop-color="#ffe08a"/><stop offset="1" stop-color="#b8860b"/></linearGradient>${_glow(g+'g',A2)}`)};
// ---------- غار ----------
ILL.cave=(k,T,A,A2)=>{const g=U('v');const w=_up(k,.55,.35);
 return _svg(`<g ${rise(k,0,.35,100)}><path d="M-560 300 L-420 -60 L-300 -10 L-160 -250 L20 -120 L160 -290 L330 -60 L440 -120 L560 300Z" fill="#6d5338"/><path d="M-160 -250 L20 -120 L160 -290 L100 300 L-200 300Z" fill="#5a4430" opacity=".6"/></g>
  <g ${rise(k,.25,.3,40)}><path d="M-150 300 C-160 140 -80 40 0 40 C80 40 160 140 150 300Z" fill="#1a110a"/></g>
  <g opacity="${w}" stroke="#e8e8f0" stroke-width="2" fill="none">${[...Array(8)].map((_,i)=>{const a=-Math.PI+i*Math.PI/7;return `<line x1="0" y1="110" x2="${Math.cos(a)*140*w}" y2="${110+Math.sin(a)*120*w}"/>`}).join('')}
   ${[40,80,120].map(r=>`<path d="M${-r*w} 110 ${[...Array(8)].map((_,i)=>{const a=-Math.PI+i*Math.PI/7;return `L${Math.cos(a)*r*w} ${110+Math.sin(a)*r*.85*w}`}).join(' ')}"/>`).join('')}</g>
  <g ${pop(k,.75,.3,170,40)}><ellipse cx="170" cy="60" rx="46" ry="18" fill="#8a6a3a"/><path d="M150 40 q20 -34 44 -10 q14 -18 28 0 q-30 18 -72 10z" fill="#f4f4f4"/><circle cx="196" cy="24" r="4" fill="#222"/></g>`,'')};
// ---------- قافلة جمال ----------
ILL.caravan=(k,T,A,A2)=>{const g=U('cv');
 const camel=(x,d)=>{const u=_up(k,d,.3),b=Math.sin(T*4+x)*4;return `<g opacity="${u}" transform="translate(${x+(1-u)*-80},${190+b})"><path d="M-70 0 C-70 -40 -50 -60 -20 -60 C-10 -95 20 -95 30 -60 C50 -60 60 -40 60 -20 L90 -70 L105 -80 L120 -72 L112 -62 L96 -58 L70 0Z" fill="#3a2614"/>${[-55,-35,30,50].map((lx,i)=>`<rect x="${lx}" y="-4" width="10" height="${70+Math.sin(T*8+i+x)*6}" fill="#3a2614"/>`).join('')}</g>`};
 return _svg(`<circle cx="260" cy="-160" r="${120*_up(k,0,.4)}" fill="#ffcf6a"/><circle cx="260" cy="-160" r="${210*_up(k,0,.4)}" fill="url(#${g}g)"/>
  <g ${rise(k,.05,.3,60)}><path d="M-600 260 Q-300 140 0 230 Q300 120 600 240 L600 400 L-600 400Z" fill="#d79a4e"/><path d="M-600 320 Q-200 230 200 300 Q400 260 600 300 L600 400 L-600 400Z" fill="#c07e36"/></g>
  ${camel(-260,.3)}${camel(-60,.42)}${camel(140,.54)}`,_glow(g+'g','#ffcf6a'))};
// ---------- مكتبة / كتب ----------
ILL.library=(k,T,A,A2)=>{const g=U('l');const cols=['#c0392b','#2e86de','#27ae60','#f39c12','#8e44ad','#16a085','#d35400'];
 const shelf=(y,d)=>`<g ${rise(k,d,.3,60)}><rect x="-360" y="${y}" width="720" height="16" fill="#6b4423"/>${[...Array(18)].map((_,i)=>{const h=70+((i*37)%30),w=30+((i*13)%14);return `<rect x="${-350+i*39}" y="${y-h}" width="${w}" height="${h}" rx="3" fill="${cols[(i+y)%7]}"/><rect x="${-350+i*39+4}" y="${y-h+12}" width="${w-8}" height="5" fill="#ffd76a" opacity=".7"/>`}).join('')}</g>`;
 const fl=Math.sin(T*3)*.15+.85;
 return _svg(`<circle cx="0" cy="-20" r="${430*_up(k,.6,.35)}" fill="url(#${g}g)"/><g ${rise(k,0,.25,80)}><rect x="-390" y="-280" width="780" height="590" rx="12" fill="#3e2714"/></g>${shelf(-150,.15)}${shelf(-10,.25)}${shelf(130,.35)}${shelf(270,.45)}
  <g ${pop(k,.7,.3,0,-330)}><path d="M-40 -330 h80 l-10 30 h-60z" fill="#d4a017"/><ellipse cx="0" cy="-360" rx="${18*fl}" ry="${34*fl}" fill="#ffb347"/><ellipse cx="0" cy="-354" rx="8" ry="18" fill="#fff3c4"/><circle cx="0" cy="-350" r="${120*fl}" fill="url(#${g}f)"/></g>`,_glow(g+'g',A2)+_glow(g+'f','#ffb347'))};
ILL.book=(k,T,A,A2)=>{const g=U('b');const op=_up(k,.25,.4);
 const pages=[...Array(6)].map((_,i)=>{const t=(T*.6+i/6)%1;const x=-40+t*420,y=-60-t*360+Math.sin(t*9+i)*30;return `<g opacity="${(1-t)*_up(k,.6,.3)}" transform="translate(${x},${y}) rotate(${t*200+i*40})"><rect x="-26" y="-34" width="52" height="68" rx="4" fill="#fffbe9"/>${[0,1,2,3].map(j=>`<rect x="-18" y="${-24+j*14}" width="36" height="4" fill="#b9a77a"/>`).join('')}</g>`}).join('');
 return _svg(`<circle cx="0" cy="0" r="${400*_up(k,.4,.4)}" fill="url(#${g}g)"/>
  <g ${rise(k,0,.3,80)}><path d="M0 280 L-360 240 L-360 20 L0 60Z" fill="#7a2e1d"/><path d="M0 280 L360 240 L360 20 L0 60Z" fill="#8f3a24"/></g>
  <g transform="translate(0,60)"><path d="M0 0 C-120 -40 -250 -30 -330 ${-10-170*op} L-330 ${170-170*op} C-250 150 -120 150 0 200Z" fill="#fffbe9"/><path d="M0 0 C120 -40 250 -30 330 ${-10-170*op} L330 ${170-170*op} C250 150 120 150 0 200Z" fill="#f6efd6"/>
   ${[...Array(6)].map((_,j)=>`<path d="M-290 ${10+j*26-120*op} Q-150 ${-10+j*26} -30 ${30+j*26}" stroke="#7a6a4a" stroke-width="5" fill="none" opacity="${op*.7}"/><path d="M30 ${30+j*26} Q150 ${-10+j*26} 290 ${10+j*26-120*op}" stroke="#7a6a4a" stroke-width="5" fill="none" opacity="${op*.7}"/>`).join('')}</g>${pages}`,_glow(g+'g',A2))};
// ---------- لفافة / معاهدة ----------
ILL.scroll=(k,T,A,A2)=>{const g=U('s');const u=_up(k,.15,.5);
 return _svg(`<circle cx="0" cy="0" r="${380*_up(k,.4,.4)}" fill="url(#${g}g)"/>
  <rect x="-300" y="${-200}" width="600" height="${420*u}" fill="#f3e4bf"/>${[...Array(9)].map((_,j)=>`<rect x="-240" y="${-150+j*40}" width="${(j%3==2?300:480)*_up(k,.4+j*.04,.2)}" height="10" rx="5" fill="#8a6a3a" opacity=".6"/>`).join('')}
  <rect x="-330" y="-230" width="660" height="40" rx="20" fill="#9a6b30"/><rect x="-330" y="${-210+420*u}" width="660" height="40" rx="20" fill="#9a6b30"/>
  <g ${pop(k,.75,.3,200,160)}><circle cx="200" cy="160" r="50" fill="#c0392b"/><circle cx="200" cy="160" r="34" fill="none" stroke="#7d1f15" stroke-width="5"/><path d="M180 205 l-14 60 l34 -24 l34 24 l-14 -60" fill="#c0392b"/></g>`,_glow(g+'g',A2))};
// ---------- سيوف متقاطعة (معركة) ----------
ILL.swords=(k,T,A,A2)=>{const g=U('w');const u=_bk(k,.1,.45);const sp=_up(k,.5,.3);
 const sword=(rot,dx)=>`<g transform="rotate(${rot*u}) translate(${dx*(1-u)},0)"><path d="M-8 -380 Q0 -410 8 -380 L12 120 L-12 120Z" fill="url(#${g}s)"/><rect x="-70" y="120" width="140" height="20" rx="10" fill="#d4a017"/><rect x="-10" y="140" width="20" height="90" rx="6" fill="#4a2a12"/><circle cx="0" cy="240" r="16" fill="#d4a017"/></g>`;
 return _svg(`<circle cx="0" cy="-60" r="${420*sp}" fill="url(#${g}g)"/>
  <g transform="translate(0,-40)">${sword(-40,-300)}${sword(40,300)}</g>
  ${[...Array(14)].map((_,i)=>{const a=i/14*6.283,r=(60+((T*300+i*50)%260))*sp;return `<line x1="${Math.cos(a)*r}" y1="${-260+Math.sin(a)*r}" x2="${Math.cos(a)*(r+30)}" y2="${-260+Math.sin(a)*(r+30)}" stroke="#ffd76a" stroke-width="5" stroke-linecap="round" opacity="${sp*(1-((T*300+i*50)%260)/260)}"/>`}).join('')}
  <g ${rise(k,.3,.3,80)}><path d="M-430 120 l90 -40 l90 40 l-10 120 q-80 60 -80 60 q-80 -40 -80 -60z" fill="${A}" stroke="#fff" stroke-width="6"/><path d="M250 120 l90 -40 l90 40 l-10 120 q-80 60 -80 60 q-80 -40 -80 -60z" fill="#8e1b23" stroke="#fff" stroke-width="6"/></g>`,
  `<linearGradient id="${g}s" x1="0" x2="1"><stop offset="0" stop-color="#8a96a6"/><stop offset=".5" stop-color="#f1f5fa"/><stop offset="1" stop-color="#7b8796"/></linearGradient>${_glow(g+'g','#ffd76a')}`)};
// ---------- جيش ----------
ILL.army=(k,T,A,A2,o={})=>{const g=U('a');const c=o.color||A;
 const sol=(x,y,s,d)=>{const u=_up(k,d,.3);const b=Math.sin(T*5+x*.05)*3;return `<g opacity="${u}" transform="translate(${x},${y+(1-u)*60+b}) scale(${s})"><rect x="-2" y="-230" width="5" height="250" fill="#6b4a2a"/><path d="M0 -250 l8 22 h-16z" fill="#ddd"/><circle cx="-24" cy="-120" r="22" fill="#c49a6c"/><path d="M-50 -132 q26 -36 52 0z" fill="#fff"/><path d="M-60 20 q0 -110 36 -110 q36 0 36 110z" fill="${c}"/><circle cx="-24" cy="-40" r="34" fill="#8a6a3a" stroke="#d4a017" stroke-width="5"/></g>`};
 const banner=(x,d)=>`<g ${rise(k,d,.3,80)}><rect x="${x}" y="-260" width="6" height="420" fill="#4a3020"/><path d="M${x+6} -260 Q${x+70} ${-250+10*Math.sin(T*4+x)} ${x+130} -258 L${x+130} -160 Q${x+70} ${-150+10*Math.sin(T*4+x+1)} ${x+6} -162Z" fill="${c}"/></g>`;
 let s='';for(let r=0;r<3;r++)for(let i=0;i<7;i++)s+=sol(-420+i*140+(r%2)*70,150+r*70,.7+r*.12,.1+r*.12+i*.02);
 return _svg(`${banner(-300,.05)}${banner(160,.1)}${s}`,'')};
// ---------- سفينة ----------
ILL.ship=(k,T,A,A2,o={})=>{const g=U('sh');const rk=Math.sin(T*1.5)*4,bob=Math.sin(T*1.5)*8;const sail=o.sail||'#f4ecd8',cross=o.cross;
 const wave=(y,c,a,ph)=>`<path d="M-620 ${y} ${[...Array(14)].map((_,i)=>`Q${-575+i*90} ${y-22*Math.sin(T*2+i+ph)} ${-530+i*90} ${y}`).join(' ')} L620 400 L-620 400Z" fill="${c}" opacity="${a}"/>`;
 return _svg(`<g ${rise(k,0,.3,60)}>${wave(250,'#1e5a8a',.9,0)}</g>
  <g transform="translate(0,${bob+(1-_up(k,.15,.4))*300}) rotate(${rk})"><path d="M-330 160 L330 160 L250 270 L-260 270Z" fill="#6b3f1d"/><path d="M-330 160 L330 160 L320 185 L-320 185Z" fill="#8b5a2b"/>${[...Array(6)].map((_,i)=>`<circle cx="${-200+i*80}" cy="215" r="12" fill="#3a2010"/>`).join('')}
   <rect x="-8" y="-330" width="16" height="490" fill="#4a2a12"/><rect x="-180" y="-230" width="10" height="390" fill="#4a2a12" transform="rotate(0)"/>
   <g transform="scale(${_up(k,.45,.35)},1)"><path d="M10 -310 Q170 -200 10 -40Z" fill="${sail}" stroke="#cbb98f" stroke-width="3"/><path d="M-10 -300 Q-200 -170 -10 -20Z" fill="${sail}" stroke="#cbb98f" stroke-width="3"/>${cross?`<path d="M-110 -200 h40 v-40 h30 v40 h40 v30 h-40 v70 h-30 v-70 h-40z" fill="#c0392b"/>`:''}</g>
   <path d="M8 -330 L80 -312 L8 -296Z" fill="${A}"/></g>
  ${wave(290,'#2876b4',.85,1)}${wave(330,'#3a92d4',.8,2)}`,'')};
// ---------- سلسلة عبر الماء ----------
ILL.chain=(k,T,A,A2)=>{const u=_up(k,.3,.5);const n=16;
 const links=[...Array(n)].map((_,i)=>{const x=-360+i*48,y=60+Math.sin(i/(n-1)*Math.PI)*60;return i/n<u?`<ellipse cx="${x}" cy="${y}" rx="${i%2?28:24}" ry="${i%2?12:20}" fill="none" stroke="#9aa3ad" stroke-width="10"/>`:''}).join('');
 return _svg(`<g ${rise(k,0,.3,60)}><rect x="-600" y="120" width="1200" height="280" fill="#1e5a8a"/>${[...Array(8)].map((_,i)=>`<path d="M${-600+i*160} ${170+Math.sin(T*2+i)*6} q40 -12 80 0" stroke="#5aa9e6" stroke-width="5" fill="none"/>`).join('')}</g>
  <g ${rise(k,.1,.3,120)}><rect x="-500" y="-160" width="130" height="300" fill="#a8875a"/>${[0,1,2,3].map(i=>`<rect x="${-500+i*35}" y="-184" width="22" height="24" fill="#a8875a"/>`).join('')}<rect x="370" y="-160" width="130" height="300" fill="#a8875a"/>${[0,1,2,3].map(i=>`<rect x="${370+i*35}" y="-184" width="22" height="24" fill="#a8875a"/>`).join('')}</g>${links}`,'')};
// ---------- قصر الحمراء ----------
ILL.palace=(k,T,A,A2)=>{const g=U('p');
 const arch=(x,d)=>`<g ${rise(k,d,.25,60)}><rect x="${x-14}" y="40" width="28" height="200" fill="#f3e6cf"/><path d="M${x} 40 v-6 a70 80 0 0 1 140 0 v6" fill="none" stroke="#e3cfa8" stroke-width="10"/>${[...Array(5)].map((_,j)=>`<path d="M${x+10+j*24} 0 q12 -14 24 0" stroke="#c9a878" stroke-width="3" fill="none"/>`).join('')}</g>`;
 return _svg(`<circle cx="0" cy="-60" r="${440*_up(k,.6,.35)}" fill="url(#${g}g)"/>
  <g ${rise(k,0,.3,100)}><rect x="-480" y="-240" width="960" height="300" fill="#b9573a"/><rect x="-160" y="-360" width="320" height="130" fill="#a84a30"/>${[...Array(8)].map((_,i)=>`<rect x="${-160+i*42}" y="-382" width="26" height="22" fill="#a84a30"/>`).join('')}${[...Array(24)].map((_,i)=>`<rect x="${-480+i*41}" y="-262" width="26" height="22" fill="#b9573a"/>`).join('')}</g>
  <g ${rise(k,.1,.3,80)}><rect x="-460" y="-40" width="920" height="300" fill="#e9d8b6"/>${[...Array(7)].map((_,i)=>`<path d="M${-430+i*126} 240 v-180 a63 70 0 0 1 126 0 v180z" fill="#2d4a3e"/>`).join('')}</g>
  ${[...Array(8)].map((_,i)=>arch(-450+i*126,.25+i*.04)).join('')}
  <g ${rise(k,.55,.3,40)}><rect x="-460" y="260" width="920" height="60" fill="#3a7fb0"/>${[...Array(6)].map((_,i)=>`<path d="M${-420+i*150} ${290+Math.sin(T*2+i)*4} q30 -8 60 0" stroke="#9fd0f0" stroke-width="4" fill="none"/>`).join('')}</g>`,_glow(g+'g',A2))};
// ---------- مفتاح ----------
ILL.key=(k,T,A,A2)=>{const g=U('ky');const u=_bk(k,.1,.5);
 return _svg(`<circle cx="0" cy="-40" r="${380*_up(k,.4,.4)}" fill="url(#${g}g)"/><g transform="translate(0,-40) rotate(${-30+30*u+Math.sin(T*1.5)*4}) scale(${u})">
  <circle cx="-200" cy="0" r="110" fill="none" stroke="url(#${g}k)" stroke-width="34"/><circle cx="-200" cy="0" r="50" fill="none" stroke="url(#${g}k)" stroke-width="14"/>
  <rect x="-95" y="-18" width="420" height="36" rx="10" fill="url(#${g}k)"/><path d="M230 18 v70 h34 v-40 h30 v60 h34 v-90z" fill="url(#${g}k)"/></g>`,
  `<linearGradient id="${g}k" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#b8860b"/><stop offset=".5" stop-color="#ffe08a"/><stop offset="1" stop-color="#a87412"/></linearGradient>${_glow(g+'g','#ffd76a')}`)};
// ---------- عملات ----------
ILL.coins=(k,T,A,A2)=>{const g=U('co');
 const coin=(x,y,d,r=60)=>{const u=_bk(k,d,.35);return `<g opacity="${_e(u*1.5)}" transform="translate(${x},${y-(1-u)*300})"><ellipse cx="0" cy="0" rx="${r*Math.abs(Math.cos(T*2+x))+6}" ry="${r}" fill="url(#${g}c)" stroke="#8a5a0a" stroke-width="4"/></g>`};
 return _svg(`<circle cx="0" cy="40" r="${360*_up(k,.4,.4)}" fill="url(#${g}g)"/>${coin(-200,120,.1,110)}${coin(40,190,.2,95)}${coin(250,110,.3,105)}${coin(-60,-40,.4,90)}`,
  `<linearGradient id="${g}c" x1="0" x2="1"><stop offset="0" stop-color="#b8860b"/><stop offset=".5" stop-color="#ffe08a"/><stop offset="1" stop-color="#b8860b"/></linearGradient>${_glow(g+'g','#ffd76a')}`)};
// ---------- ضريح ----------
ILL.tomb=(k,T,A,A2)=>{const g=U('t');
 return _svg(`<circle cx="0" cy="-40" r="${400*_up(k,.5,.4)}" fill="url(#${g}g)"/>${ground(k,'#d7c7a3')}
  <g ${rise(k,.1,.35,100)}><rect x="-220" y="0" width="440" height="300" fill="#efe6d2"/>${[0,1,2,3,4,5].map(i=>`<rect x="-220" y="${20+i*46}" width="440" height="22" fill="#d9c8a6" opacity=".6"/>`).join('')}<path d="M-60 300 v-160 a60 70 0 0 1 120 0 v160z" fill="#3a2a1a"/></g>
  <g transform="translate(0,0) scale(${_up(k,.45,.35)})"><rect x="-130" y="-60" width="260" height="60" fill="#efe6d2"/><path d="M-150 -60 C-150 -210 150 -210 150 -60Z" fill="#b3202b"/><path d="M-100 -80 C-95 -150 -50 -180 -10 -186" stroke="#ff8a8a" stroke-width="7" fill="none" stroke-linecap="round" opacity=".6"/></g>`,_glow(g+'g',A2))};
// ---------- تروس ----------
ILL.gears=(k,T,A,A2)=>{const g=U('ge');
 const gear=(x,y,r,n,sp,c,d)=>{const u=_bk(k,d,.35);let p='';for(let i=0;i<n;i++){const a=i/n*6.283;p+=`<rect x="${-r*.14}" y="${-r-r*.22}" width="${r*.28}" height="${r*.34}" rx="4" transform="rotate(${a*57.3})" fill="${c}"/>`;}
  return `<g opacity="${_e(u*1.4)}" transform="translate(${x},${y}) scale(${u}) rotate(${T*sp})">${p}<circle r="${r}" fill="${c}"/><circle r="${r*.62}" fill="none" stroke="rgba(0,0,0,.25)" stroke-width="${r*.1}"/><circle r="${r*.22}" fill="#2a1a0c"/>${[0,1,2,3,4,5].map(i=>`<rect x="-6" y="${-r*.55}" width="12" height="${r*.3}" transform="rotate(${i*60})" fill="rgba(0,0,0,.25)"/>`).join('')}</g>`};
 return _svg(`<circle cx="0" cy="0" r="${420*_up(k,.4,.4)}" fill="url(#${g}g)"/>${gear(-150,-40,170,14,30,'#d38b45',.05)}${gear(140,140,120,10,-42,'#e8b04a',.2)}${gear(210,-210,90,8,-56,'#b9773a',.35)}`,_glow(g+'g',A2))};
// ---------- ساعة الفيل ----------
ILL.elephant=(k,T,A,A2)=>{const g=U('el');const tr=Math.sin(T*2)*6;
 return _svg(`<circle cx="0" cy="-60" r="${440*_up(k,.5,.4)}" fill="url(#${g}g)"/>${ground(k,'#c7a676')}
  <g ${rise(k,.05,.35,120)}><path d="M-300 120 C-300 0 -180 -40 -20 -40 C140 -40 230 20 230 120 L230 200 L-300 200Z" fill="#8d8d96"/>
   ${[-270,-160,70,170].map(x=>`<rect x="${x}" y="170" width="70" height="130" rx="10" fill="#7d7d86"/>`).join('')}
   <path d="M220 20 C330 20 340 120 320 220 Q310 ${260+tr} 290 ${250+tr}" stroke="#8d8d96" stroke-width="44" fill="none" stroke-linecap="round"/><circle cx="250" cy="40" r="10" fill="#222"/>
   <path d="M150 -20 C210 -40 240 40 200 90 C170 80 150 40 150 -20Z" fill="#7d7d86"/><path d="M290 110 l50 20" stroke="#f4f0e6" stroke-width="14" stroke-linecap="round"/>
   <path d="M-260 -10 h480 v40 h-480z" fill="#b3202b"/><path d="M-260 30 h480" stroke="#ffd76a" stroke-width="8"/></g>
  <g ${rise(k,.35,.35,100)}><rect x="-150" y="-340" width="300" height="300" fill="#e9d8b6"/><rect x="-150" y="-340" width="300" height="20" fill="#d4a017"/>
   <circle cx="0" cy="-200" r="80" fill="#fff8e6" stroke="#d4a017" stroke-width="10"/><line x1="0" y1="-200" x2="${Math.cos(T*.8)*60}" y2="${-200+Math.sin(T*.8)*60}" stroke="#333" stroke-width="8" stroke-linecap="round"/><line x1="0" y1="-200" x2="${Math.cos(T*.1)*40}" y2="${-200+Math.sin(T*.1)*40}" stroke="#333" stroke-width="10" stroke-linecap="round"/>
   <path d="M-110 -340 C-110 -460 110 -460 110 -340Z" fill="#2fae6a"/><path d="M-20 -470 q20 -40 40 0 q-20 14 -40 0z" fill="#ffd76a"/></g>`,_glow(g+'g',A2))};
// ---------- ناعورة / مضخّة ماء ----------
ILL.wheel=(k,T,A,A2)=>{const g=U('wh');const u=_bk(k,.15,.45);
 return _svg(`<g ${rise(k,0,.3,60)}><rect x="-600" y="200" width="1200" height="200" fill="#2876b4"/>${[...Array(8)].map((_,i)=>`<path d="M${-600+i*160} ${230+Math.sin(T*2+i)*6} q40 -12 80 0" stroke="#7fc0ee" stroke-width="5" fill="none"/>`).join('')}</g>
  <g transform="translate(0,0) scale(${u}) rotate(${T*25})"><circle r="260" fill="none" stroke="#7a4a22" stroke-width="22"/><circle r="40" fill="#7a4a22"/>${[...Array(12)].map((_,i)=>`<line x1="0" y1="0" x2="${Math.cos(i*.5236)*260}" y2="${Math.sin(i*.5236)*260}" stroke="#8b5a2b" stroke-width="12"/><rect x="${Math.cos(i*.5236)*260-26}" y="${Math.sin(i*.5236)*260-18}" width="52" height="36" rx="6" fill="#c98a3a" transform="rotate(${i*30} ${Math.cos(i*.5236)*260} ${Math.sin(i*.5236)*260})"/>`).join('')}</g>
  <g ${rise(k,.4,.3,60)}><rect x="-20" y="-20" width="440" height="40" fill="#a8875a"/><rect x="380" y="-20" width="40" height="320" fill="#a8875a"/>${[...Array(5)].map((_,i)=>`<circle cx="${60+((T*120+i*80)%340)}" cy="${-34}" r="9" fill="#7fc0ee"/>`).join('')}</g>`,'')};
// ---------- عين وضوء ----------
ILL.eye=(k,T,A,A2)=>{const g=U('ey');const u=_up(k,.1,.4);const r=_up(k,.4,.4);
 return _svg(`<circle cx="0" cy="-40" r="${420*u}" fill="url(#${g}g)"/>
  ${[...Array(5)].map((_,i)=>{const y=-180+i*70;const p=((T*.8+i*.2)%1);return `<line x1="-560" y1="${y}" x2="${-560+400*r}" y2="${-40+(y+40)*.2}" stroke="#ffe066" stroke-width="10" opacity="${r*.8}"/><circle cx="${-560+400*r*p}" cy="${y+(-40+(y+40)*.2-y)*p}" r="10" fill="#fff6a0" opacity="${r}"/>`}).join('')}
  <g transform="translate(120,-40) scale(${u})"><path d="M-260 0 Q0 -200 260 0 Q0 200 -260 0Z" fill="#fff" stroke="#2a1a0c" stroke-width="12"/><circle r="110" fill="#2e86de"/><circle r="110" fill="url(#${g}i)"/><circle r="52" fill="#111"/><circle cx="-26" cy="-30" r="18" fill="#fff"/></g>
  <circle cx="-180" cy="-40" r="${60*r}" fill="none" stroke="#c4e3ff" stroke-width="10" opacity=".9"/>`,
  `${_glow(g+'g','#ffe066')}<radialGradient id="${g}i"><stop offset=".4" stop-color="#1a5fa8" stop-opacity="0"/><stop offset="1" stop-color="#0b2a55"/></radialGradient>`)};
// ---------- الغرفة المظلمة ----------
ILL.camera=(k,T,A,A2)=>{const u=_up(k,.1,.4),r=_up(k,.45,.4);
 const tree=(x,y,s,flip)=>`<g transform="translate(${x},${y}) scale(${s},${flip?-s:s})"><rect x="-10" y="-20" width="20" height="90" fill="#7a4a22"/><circle cx="0" cy="-70" r="70" fill="#2fae6a"/><circle cx="-40" cy="-40" r="44" fill="#27964f"/><circle cx="40" cy="-40" r="44" fill="#27964f"/></g>`;
 return _svg(`<circle cx="-440" cy="-300" r="60" fill="#ffd76a" opacity="${u}"/>${tree(-420,120,1.1*u,0)}
  <g ${rise(k,.2,.35,60)}><rect x="-120" y="-220" width="640" height="440" rx="14" fill="#1a1a22" stroke="#555" stroke-width="8"/><circle cx="-120" cy="0" r="10" fill="#ffe066"/></g>
  <g opacity="${r}"><path d="M-420 -80 L-120 0 L500 180 M-420 120 L-120 0 L500 -160" stroke="#ffe066" stroke-width="3" stroke-dasharray="12 10" fill="none"/>${tree(470,-10,.9,1)}</g>`,'')};
// ---------- نهر بالكتب والحبر ----------
ILL.river=(k,T,A,A2,o={})=>{const ink=o.ink;const c1=ink?'#1d2333':'#2876b4',c2=ink?'#0d1220':'#1e5a8a';
 const book=(x,d)=>{const u=_up(k,d,.3);const xx=((x+T*60)%1300)-650;return `<g opacity="${u}" transform="translate(${xx},${210+Math.sin(T*2+x)*8}) rotate(${Math.sin(T+x)*10})"><rect x="-50" y="-30" width="100" height="60" rx="6" fill="${['#c0392b','#2e86de','#27ae60','#f39c12'][Math.abs(x)%4]}"/><rect x="-40" y="-22" width="80" height="10" fill="#f4ecd8"/></g>`};
 return _svg(`<g ${rise(k,0,.3,80)}><path d="M-600 120 Q-200 60 0 110 Q200 160 600 100 L600 400 L-600 400Z" fill="${c2}"/><path d="M-600 170 Q-200 120 0 160 Q200 200 600 150 L600 400 L-600 400Z" fill="${c1}"/></g>
  ${ink?[0,1,2,3,4,5].map(i=>`<ellipse cx="${-400+i*170}" cy="${260+Math.sin(T+i)*10}" rx="${70*_up(k,.4+i*.05,.4)}" ry="14" fill="#000" opacity=".6"/>`).join(''):''}
  ${[0,300,650,950].map((x,i)=>book(x,.3+i*.08)).join('')}
  <g ${rise(k,.1,.3,100)}><path d="M-600 120 L-600 -60 L-480 -60 L-480 -140 L-400 -140 L-400 -40 L-300 -40 L-300 -180 L-220 -180 L-220 110Z" fill="#3a2a1a"/><path d="M220 110 L220 -100 L300 -100 L300 -200 L360 -260 L420 -200 L420 -60 L520 -60 L520 -120 L600 -120 L600 100Z" fill="#3a2a1a"/></g>`,'')};
// ---------- تلال حارقة (حطين) ----------
ILL.hills=(k,T,A,A2)=>{const g=U('h');const u=_up(k,.1,.4);
 return _svg(`<circle cx="0" cy="-220" r="${130*u}" fill="#ffb347"/><circle cx="0" cy="-220" r="${260*u}" fill="url(#${g}g)"/>
  ${[...Array(5)].map((_,i)=>`<path d="M${-300+i*150} ${40+Math.sin(T*3+i)*6} q20 -20 40 0 q20 20 40 0" stroke="#ffcf8a" stroke-width="4" fill="none" opacity="${u*.6}"/>`).join('')}
  <g ${rise(k,0,.35,100)}><path d="M-600 300 L-600 160 Q-420 20 -260 100 Q-180 -40 -90 60 Q0 120 100 60 Q190 -40 270 100 Q420 30 600 170 L600 300Z" fill="#a8743a"/><path d="M-600 300 L-600 230 Q-200 150 0 220 Q300 160 600 240 L600 300Z" fill="#8a5a2a"/></g>
  ${[[-180,-10],[190,-10]].map(([x,y],i)=>`<g ${pop(k,.5+i*.1,.3,x,y)}><path d="M${x-30} ${y+30} l30 -60 l30 60z" fill="#6a4320"/></g>`).join('')}`,_glow(g+'g','#ff8a3a'))};
// ---------- هلال وتقويم ----------
ILL.calendar=(k,T,A,A2)=>{const g=U('ca');const u=_bk(k,.15,.45);
 return _svg(`<circle cx="-160" cy="-120" r="${300*_up(k,.4,.4)}" fill="url(#${g}g)"/>
  <g transform="translate(-170,-120) scale(${u}) rotate(${Math.sin(T)*4})"><path d="M0 -160 a160 160 0 1 0 0.1 0 M60 -140 a130 130 0 1 0 0.1 0" fill="#ffd76a" fill-rule="evenodd"/></g>
  <g ${rise(k,.35,.35,100)}><rect x="40" y="-120" width="380" height="420" rx="24" fill="#fffbe9"/><rect x="40" y="-120" width="380" height="90" rx="24" fill="${A}"/><rect x="40" y="-60" width="380" height="30" fill="${A}"/>
   ${[...Array(20)].map((_,i)=>`<rect x="${70+(i%5)*68}" y="${-10+Math.floor(i/5)*68}" width="50" height="50" rx="8" fill="${i==7?A:'#e8e0cc'}"/>`).join('')}</g>`,_glow(g+'g','#ffd76a'))};
// ---------- تاج ----------
ILL.crown=(k,T,A,A2)=>{const g=U('cr');const u=_bk(k,.1,.5);
 return _svg(`<circle cx="0" cy="-40" r="${380*_up(k,.4,.4)}" fill="url(#${g}g)"/><g transform="translate(0,${-40+Math.sin(T*1.5)*10}) scale(${u})">
  <path d="M-260 140 L-280 -100 L-140 20 L0 -160 L140 20 L280 -100 L260 140Z" fill="url(#${g}c)" stroke="#8a5a0a" stroke-width="6"/><rect x="-270" y="120" width="540" height="60" rx="10" fill="url(#${g}c)"/>
  ${[[-280,-100,'#c0392b'],[0,-160,'#2e86de'],[280,-100,'#27ae60']].map(([x,y,c])=>`<circle cx="${x}" cy="${y}" r="24" fill="${c}" stroke="#fff" stroke-width="4"/>`).join('')}${[-160,-60,60,160].map(x=>`<circle cx="${x}" cy="150" r="16" fill="#c0392b"/>`).join('')}</g>`,
  `<linearGradient id="${g}c" x1="0" x2="1"><stop offset="0" stop-color="#b8860b"/><stop offset=".5" stop-color="#ffe08a"/><stop offset="1" stop-color="#b8860b"/></linearGradient>${_glow(g+'g','#ffd76a')}`)};
// ---------- نار على مدينة ----------
ILL.fire=(k,T,A,A2)=>{const u=_up(k,.2,.4);
 const flame=(x,s,d)=>{const f=_up(k,d,.3)*(1+.12*Math.sin(T*9+x));return `<g transform="translate(${x},120) scale(${s*f})"><path d="M0 0 C-60 -60 -30 -150 0 -220 C20 -150 80 -110 50 -30 C40 -10 20 0 0 0Z" fill="#ff5a1f"/><path d="M0 0 C-30 -40 -14 -100 4 -140 C16 -100 44 -70 28 -20Z" fill="#ffc83a"/></g>`};
 return _svg(`<g ${rise(k,0,.3,80)}><path d="M-600 300 L-600 40 L-500 40 L-500 -40 L-420 -40 L-420 60 L-300 60 L-300 -100 L-200 -160 L-100 -100 L-100 40 L60 40 L60 -60 L160 -60 L160 20 L280 20 L280 -140 L340 -190 L400 -140 L400 40 L600 40 L600 300Z" fill="#2a1a12"/></g>
  ${[-420,-200,0,220,380].map((x,i)=>flame(x,1+(i%2)*.3,.3+i*.06)).join('')}
  ${[...Array(10)].map((_,i)=>{const p=(T*.3+i/10)%1;return `<circle cx="${-400+i*90+Math.sin(T+i)*30}" cy="${-100-p*400}" r="${30+p*60}" fill="#555" opacity="${u*.35*(1-p)}"/>`}).join('')}`,'')};
// ---------- أسوار القسطنطينية ----------
ILL.walls=(k,T,A,A2)=>{const st='#b09a7a';
 const wall=(y,h,d,c)=>`<g ${rise(k,d,.3,100)}><rect x="-600" y="${y}" width="1200" height="${h}" fill="${c}"/>${[...Array(30)].map((_,i)=>`<rect x="${-600+i*41}" y="${y-18}" width="24" height="18" fill="${c}"/>`).join('')}${[-450,-150,150,450].map(x=>`<rect x="${x-50}" y="${y-80}" width="100" height="${h+80}" fill="${c}"/><rect x="${x-50}" y="${y-80}" width="100" height="12" fill="rgba(0,0,0,.15)"/>`).join('')}</g>`;
 return _svg(`${wall(-60,360,.05,'#8f7b5e')}${wall(60,240,.2,st)}${wall(180,120,.35,'#c9b28e')}`,'')};
// ---------- آيا صوفيا ----------
ILL.hagia=(k,T,A,A2)=>{const g=U('hg');
 const min=(x,d)=>`<g ${rise(k,d,.3,200)}><rect x="${x-14}" y="-300" width="28" height="600" fill="#f0e2c8"/><path d="M${x-14} -300 L${x} -420 L${x+14} -300Z" fill="#5a6a7a"/><rect x="${x-24}" y="-160" width="48" height="12" fill="#d9c8a6"/></g>`;
 return _svg(`<circle cx="0" cy="-60" r="${440*_up(k,.55,.35)}" fill="url(#${g}g)"/>${min(-470,.4)}${min(-400,.45)}${min(400,.5)}${min(470,.55)}
  <g ${rise(k,0,.3,100)}><rect x="-340" y="40" width="680" height="260" fill="#d88a6a"/><rect x="-200" y="-40" width="400" height="90" fill="#d88a6a"/></g>
  <g transform="translate(0,-40) scale(${_up(k,.3,.35)})"><path d="M-200 0 C-200 -170 200 -170 200 0Z" fill="#6b7d8f"/>${[...Array(9)].map((_,i)=>`<rect x="${-180+i*44}" y="-18" width="16" height="18" fill="#2a2a2a"/>`).join('')}</g>
  ${[-260,260].map((x,i)=>`<g transform="translate(${x},40) scale(${_up(k,.25+i*.05,.3)})"><path d="M-80 0 C-80 -80 80 -80 80 0Z" fill="#6b7d8f"/></g>`).join('')}`,_glow(g+'g',A2))};
// ---------- أسطرلاب ----------
ILL.astrolabe=(k,T,A,A2)=>{const g=U('as');const u=_bk(k,.1,.5);
 return _svg(`<circle cx="0" cy="-40" r="${400*_up(k,.4,.4)}" fill="url(#${g}g)"/><g transform="translate(0,-40) scale(${u})"><circle r="280" fill="url(#${g}b)" stroke="#8a5a0a" stroke-width="10"/><circle r="230" fill="none" stroke="#8a5a0a" stroke-width="4"/>
  ${[...Array(24)].map((_,i)=>`<line x1="0" y1="-280" x2="0" y2="-250" stroke="#5a3a0a" stroke-width="4" transform="rotate(${i*15})"/>`).join('')}
  <g transform="rotate(${T*20})"><circle r="150" fill="none" stroke="#5a3a0a" stroke-width="6" stroke-dasharray="20 12"/><path d="M0 -220 L14 0 L0 220 L-14 0Z" fill="#5a3a0a"/></g><circle r="20" fill="#5a3a0a"/><circle cx="0" cy="-310" r="30" fill="none" stroke="#8a5a0a" stroke-width="12"/></g>`,
  `<linearGradient id="${g}b" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f6d27a"/><stop offset="1" stop-color="#c48a2a"/></linearGradient>${_glow(g+'g',A2)}`)};
// ---------- شخصيات ----------
const CHARS={
 saladin:{skin:'#d49a6c',beard:'full',bc:'#1d1712',head:'turban',tur:'#ffffff',gem:'#1f8f5f',robe:['#0f5c43','#17855f'],cape:'#c22d36',trim:'#ffe08a',armor:1,item:'sword'},
 nuraldin:{skin:'#c98d63',beard:'full',bc:'#2a2018',head:'turban',tur:'#2b2b2b',gem:'#d4a017',robe:['#2a3a6a','#3d5590'],cape:'#1a2440',trim:'#d4a017',armor:1,item:'sword'},
 shirkuh:{skin:'#c98d63',beard:'full',bc:'#3a2a1a',head:'helmet',robe:['#6a4a2a','#8a6a3a'],cape:'#5a3020',trim:'#d4a017',armor:1,item:'sword'},
 guy:{skin:'#f0c8a8',beard:'short',bc:'#8a5a2a',head:'crown',robe:['#e8e8ee','#ffffff'],cape:'#2a3a8a',trim:'#d4a017',armor:1,cross:1,item:'sword'},
 richard:{skin:'#f0c8a8',beard:'short',bc:'#c07a3a',head:'crown',robe:['#b3202b','#d63a44'],cape:'#1d2a60',trim:'#ffd76a',armor:1,lions:1,item:'sword'},
 mehmed:{skin:'#e0aa80',beard:'short',bc:'#5a3a1a',head:'ottoman',tur:'#ffffff',robe:['#8a1d24','#b3303a'],cape:'#e8c26a',trim:'#ffffff',fur:1,item:'none'},
 boabdil:{skin:'#d9a57a',beard:'short',bc:'#2a1a10',head:'turban',tur:'#c0392b',gem:'#ffd76a',robe:['#1d4a6a','#2a6a8a'],cape:'#e9d8b6',trim:'#ffd76a',item:'none'},
 scholar:{skin:'#c98d63',beard:'full',bc:'#5a5a5a',head:'turban',tur:'#f2efe6',gem:null,robe:['#5a3a1a','#7a5a2a'],cape:'#3a2a14',trim:'#d4a017',item:'book'},
 scholar2:{skin:'#c48a5e',beard:'full',bc:'#d8d8d8',head:'turban',tur:'#1d1d1d',gem:null,robe:['#1d3a5a','#2a5a8a'],cape:'#13263c',trim:'#c4e3ff',item:'scroll'},
 scholar3:{skin:'#d49a6c',beard:'full',bc:'#2a2018',head:'turban',tur:'#2fae6a',gem:null,robe:['#6a2a4a','#8a3a6a'],cape:'#3a1a2a',trim:'#ffd76a',item:'book'},
 caliph:{skin:'#d49a6c',beard:'full',bc:'#1d1712',head:'turban',tur:'#111111',gem:'#d4a017',robe:['#111111','#2a2a2a'],cape:'#3a2a10',trim:'#d4a017',item:'none'},
 mongol:{skin:'#d6a878',beard:'mustache',bc:'#2a1a10',head:'mongol',robe:['#6a4a2a','#8a5a2a'],cape:'#3a2a1a',trim:'#c0392b',armor:1,item:'sword'},
 fatima:{skin:'#d9a57a',head:'hijab',hj:'#3a5a8a',robe:['#3a5a8a','#4a6aa0'],cape:'#2a4060',trim:'#e8c26a',female:1,item:'none'},
 sacred:{head:'glow',robe:['#f2efe6','#ffffff'],cape:'#2fae6a',trim:'#e8c26a',item:'none'},
};
function CH(name,k,T){const o=typeof name==='string'?CHARS[name]:name;const g=U('ch');
 const body=_up(k,0,.35), head=_up(k,.2,.35), tur=_up(k,.4,.35), it=_up(k,.6,.35);
 const blink=(T%4)>3.85?0.15:1, br=Math.sin(T*1.6)*2, breathe=1+Math.sin(T*1.8)*.008;
 const r0=o.robe[0],r1=o.robe[1];
 let item='';
 if(o.item==='sword') item=`<g opacity="${it}" transform="translate(265,${90+(1-it)*120}) rotate(16)"><path d="M-9 -330 Q0 -350 9 -330 L12 60 L-12 60Z" fill="url(#${g}st)"/><rect x="-55" y="60" width="110" height="16" rx="8" fill="#d4a017"/><rect x="-10" y="76" width="20" height="80" rx="6" fill="#4a2a12"/><circle cx="0" cy="164" r="14" fill="#d4a017"/></g>`;
 const front= o.item==='book'?`<g opacity="${it}" transform="translate(0,${330+(1-it)*60})"><path d="M0 0 L-110 -20 L-110 70 L0 90Z" fill="#7a2e1d"/><path d="M0 0 L110 -20 L110 70 L0 90Z" fill="#8f3a24"/><path d="M0 6 L-96 -10 L-96 60 L0 78Z" fill="#fffbe9"/><path d="M0 6 L96 -10 L96 60 L0 78Z" fill="#f6efd6"/></g>`
  : o.item==='scroll'?`<g opacity="${it}" transform="translate(0,${330+(1-it)*60})"><rect x="-120" y="-10" width="240" height="90" fill="#f3e4bf"/><rect x="-135" y="-20" width="270" height="20" rx="10" fill="#9a6b30"/><rect x="-135" y="70" width="270" height="20" rx="10" fill="#9a6b30"/></g>`:'';
 // الجسد
 let b=`<g transform="translate(0,${(1-body)*140}) scale(1,${breathe})" opacity="${body}" style="transform-origin:0 440px">
  <path d="M-330 440 C-320 250 -230 170 -120 150 L120 150 C230 170 320 250 330 440Z" fill="${o.cape}"/>
  <path d="M-250 440 C-240 280 -170 200 -90 175 L90 175 C170 200 240 280 250 440Z" fill="url(#${g}r)"/>
  <path d="M-90 175 L0 300 L90 175" fill="none" stroke="${o.trim}" stroke-width="14" stroke-linejoin="round"/><path d="M0 300 L0 440" stroke="${o.trim}" stroke-width="12"/>
  ${o.fur?`<path d="M-250 440 C-240 280 -170 200 -90 175 L-60 175 C-140 220 -190 300 -190 440Z" fill="#f4ecd8"/><path d="M250 440 C240 280 170 200 90 175 L60 175 C140 220 190 300 190 440Z" fill="#f4ecd8"/>`:''}
  ${o.cross?`<path d="M-26 250 h52 v50 h50 v40 h-50 v90 h-52 v-90 h-50 v-40 h50z" fill="#c0392b"/>`:''}
  ${o.lions?`<path d="M-60 260 q30 -30 60 0 q30 -30 60 0 v20 h-120z M-60 330 q30 -30 60 0 q30 -30 60 0 v20 h-120z" fill="#ffd76a"/>`:''}
  ${o.armor?`<path d="M-70 150 Q0 200 70 150 L70 185 Q0 235 -70 185Z" fill="#9aa3ad"/>${[...Array(9)].map((_,i)=>`<circle cx="${-60+i*15}" cy="${172+Math.abs(i-4)*-3}" r="4" fill="#cfd6dd"/>`).join('')}`:''}
  ${!o.cross&&!o.lions?[0,1,2,3].map(i=>`<circle cx="0" cy="${330+i*30}" r="7" fill="${o.trim}"/>`).join(''):''}</g>`;
 let h='';
 if(o.head==='glow'){
  const p=.85+.15*Math.sin(T*2);
  h=`<g opacity="${head}" transform="translate(0,${(1-head)*60})"><circle cx="0" cy="20" r="${230*p}" fill="url(#${g}hg)"/>${[...Array(16)].map((_,i)=>`<line x1="0" y1="20" x2="${Math.cos(i*.3927+T*.3)*260}" y2="${20+Math.sin(i*.3927+T*.3)*260}" stroke="#fffbe0" stroke-width="${i%2?3:7}" opacity=".35"/>`).join('')}<ellipse cx="0" cy="20" rx="125" ry="150" fill="url(#${g}hc)"/><circle cx="0" cy="20" r="${70+8*Math.sin(T*3)}" fill="#ffffff"/></g>`;
 } else if(o.head==='hijab'){
  h=`<g transform="translate(0,${(1-head)*90})" opacity="${head}"><path d="M-150 160 C-170 -40 -120 -170 0 -175 C120 -170 170 -40 150 160 C100 200 -100 200 -150 160Z" fill="${o.hj}"/>
   <path d="M-92 -10 C-92 -110 92 -110 92 -10 L86 50 C78 105 40 130 0 130 C-40 130 -78 105 -86 50Z" fill="url(#${g}sk)"/>
   <g transform="translate(0,-10) scale(1,${blink})" style="transform-box:fill-box;transform-origin:center"><path d="M-64 0 Q-42 -18 -20 0 Q-42 10 -64 0Z" fill="#fff"/><circle cx="-41" cy="-3" r="8" fill="#2b1a0f"/><path d="M20 0 Q42 -18 64 0 Q42 10 20 0Z" fill="#fff"/><circle cx="41" cy="-3" r="8" fill="#2b1a0f"/></g>
   <path d="M-70 -34 Q-44 -46 -18 -36" stroke="#2a1a10" stroke-width="7" fill="none" stroke-linecap="round"/><path d="M18 -36 Q44 -46 70 -34" stroke="#2a1a10" stroke-width="7" fill="none" stroke-linecap="round"/>
   <path d="M0 4 C-5 30 -10 42 -6 50 C0 54 8 52 10 48" fill="none" stroke="#a8683e" stroke-width="5" stroke-linecap="round"/><path d="M-22 84 Q0 98 22 84" stroke="#a04a3a" stroke-width="7" fill="none" stroke-linecap="round"/>
   <path d="M-92 -60 C-60 -120 60 -120 92 -60 C60 -90 -60 -90 -92 -60Z" fill="${o.hj}"/></g>`;
 } else {
  const beard=o.beard==='full'?`<path d="M-106 10 C-104 90 -70 165 0 178 C70 165 104 90 106 10 C92 60 70 82 40 88 C20 74 -20 74 -40 88 C-70 82 -92 60 -106 10Z" fill="${o.bc}"/>`
   : o.beard==='short'?`<path d="M-100 30 C-96 95 -60 140 0 146 C60 140 96 95 100 30 C86 70 60 86 36 90 C18 80 -18 80 -36 90 C-60 86 -86 70 -100 30Z" fill="${o.bc}"/>`:'';
  const must=o.beard==='mustache'?`<path d="M-60 76 C-30 56 -8 62 0 66 C8 62 30 56 60 76 C70 110 66 130 58 140 C50 110 30 84 0 80 C-30 84 -50 110 -58 140 C-66 130 -70 110 -60 76Z" fill="${o.bc}"/>`:`<path d="M-52 70 C-30 54 -8 58 0 64 C8 58 30 54 52 70 C30 74 10 76 0 72 C-10 76 -30 74 -52 70Z" fill="${o.bc}"/>`;
  h=`<g transform="translate(0,${(1-head)*90}) scale(${.9+.1*head})" opacity="${head}"><rect x="-38" y="70" width="76" height="70" fill="${o.skin}" filter="brightness(.85)"/>
   <path d="M-112 -40 C-112 -150 112 -150 112 -40 L104 40 C96 105 50 140 0 140 C-50 140 -96 105 -104 40Z" fill="url(#${g}sk)"/>
   <ellipse cx="-114" cy="10" rx="16" ry="26" fill="${o.skin}"/><ellipse cx="114" cy="10" rx="16" ry="26" fill="${o.skin}"/>${beard}${must}
   <path d="M-24 104 Q0 114 24 104" stroke="#8e4a3a" stroke-width="7" fill="none" stroke-linecap="round"/><path d="M0 -10 C-6 20 -14 34 -10 44 C-4 50 6 50 12 44" fill="none" stroke="rgba(90,50,20,.6)" stroke-width="5" stroke-linecap="round"/>
   <g transform="translate(0,-12) scale(1,${blink})" style="transform-box:fill-box;transform-origin:center"><path d="M-74 -8 Q-50 -28 -22 -8 Q-50 4 -74 -8Z" fill="#fff"/><circle cx="-47" cy="-11" r="9" fill="#2b1a0f"/><circle cx="-44" cy="-14" r="3" fill="#fff"/><path d="M22 -8 Q50 -28 74 -8 Q50 4 22 -8Z" fill="#fff"/><circle cx="47" cy="-11" r="9" fill="#2b1a0f"/><circle cx="50" cy="-14" r="3" fill="#fff"/></g>
   <path d="M-82 -44 Q-52 -62 -20 -46" stroke="${o.bc||'#2a1a10'}" stroke-width="11" fill="none" stroke-linecap="round"/><path d="M20 -46 Q52 -62 82 -44" stroke="${o.bc||'#2a1a10'}" stroke-width="11" fill="none" stroke-linecap="round"/></g>`;
  const tg=`transform="translate(0,${-100-(1-tur)*120}) scale(.95)" opacity="${tur}"`;
  if(o.head==='turban') h+=`<g ${tg}><path d="M-60 -60 C-60 -170 60 -170 60 -60Z" fill="#b3202b"/><path d="M-132 -10 C-150 -90 -90 -150 0 -150 C90 -150 150 -90 132 -10 C90 10 -90 10 -132 -10Z" fill="${o.tur}"/>${[0,1,2,3].map(i=>`<path d="M${-135+i*8} ${-20-i*30} C-60 ${10-i*34} 60 ${-40-i*30} ${132-i*10} ${-20-i*26}" stroke="rgba(0,0,0,.18)" stroke-width="5" fill="none"/>`).join('')}<path d="M-134 -8 C-80 18 80 18 134 -8 L128 14 C80 38 -80 38 -128 14Z" fill="${o.tur}" filter="brightness(.92)"/>${o.gem?`<g transform="translate(0,-70)"><path d="M0 -34 L22 0 L0 34 L-22 0Z" fill="#d4a017" stroke="#8a5a0a" stroke-width="3"/><circle r="11" fill="${o.gem}"/><path d="M0 -36 C-14 -80 -6 -110 ${16+br} -130" stroke="#fff" stroke-width="7" fill="none" stroke-linecap="round"/></g>`:''}</g>`;
  if(o.head==='ottoman') h+=`<g ${tg}><path d="M-150 -10 C-190 -150 -110 -270 0 -270 C110 -270 190 -150 150 -10 C90 14 -90 14 -150 -10Z" fill="${o.tur}"/>${[...Array(6)].map((_,i)=>`<path d="M${-150+i*6} ${-30-i*36} C-60 ${0-i*38} 60 ${-50-i*36} ${150-i*8} ${-30-i*30}" stroke="rgba(0,0,0,.12)" stroke-width="5" fill="none"/>`).join('')}<path d="M-40 -250 C-40 -320 40 -320 40 -250Z" fill="#b3202b"/><g transform="translate(60,-150)"><circle r="18" fill="#2fae6a" stroke="#d4a017" stroke-width="5"/><path d="M0 -18 C10 -70 40 -90 ${50+br} -120" stroke="#fff" stroke-width="8" fill="none" stroke-linecap="round"/></g></g>`;
  if(o.head==='crown') h+=`<g ${tg}><path d="M-120 0 L-130 -110 L-65 -60 L0 -140 L65 -60 L130 -110 L120 0Z" fill="#d4a017" stroke="#8a5a0a" stroke-width="5"/><rect x="-125" y="-20" width="250" height="34" rx="8" fill="#d4a017"/>${[-130,0,130].map((x,i)=>`<circle cx="${x}" cy="${[-110,-140,-110][i]}" r="13" fill="#c0392b"/>`).join('')}<path d="M-118 10 C-130 60 -120 120 -112 160 M118 10 C130 60 120 120 112 160" stroke="#9aa3ad" stroke-width="26" fill="none"/></g>`;
  if(o.head==='helmet') h+=`<g ${tg}><path d="M-130 0 C-130 -150 130 -150 130 0Z" fill="#9aa3ad"/><path d="M0 -170 L0 -120" stroke="#9aa3ad" stroke-width="14"/><rect x="-136" y="-12" width="272" height="26" rx="8" fill="#7d8792"/><path d="M-130 10 C-140 70 -130 130 -118 170 M130 10 C140 70 130 130 118 170" stroke="#7d8792" stroke-width="24" fill="none"/></g>`;
  if(o.head==='mongol') h+=`<g ${tg}><path d="M-140 0 C-130 -120 130 -120 140 0Z" fill="#7a4a22"/><path d="M-150 0 h300 v26 h-300z" fill="#d9c8a6"/><path d="M0 -110 L0 -190" stroke="#c0392b" stroke-width="10"/><circle cx="0" cy="-196" r="12" fill="#c0392b"/><path d="M-150 20 C-170 80 -160 120 -140 150 M150 20 C170 80 160 120 140 150" stroke="#d9c8a6" stroke-width="30" fill="none"/></g>`;
 }
 const sk=o.skin||'#d49a6c';
 return _svg(`${item}${b}${h}${front}`,`<linearGradient id="${g}r" x1="0" x2="1"><stop offset="0" stop-color="${r0}"/><stop offset=".5" stop-color="${r1}"/><stop offset="1" stop-color="${r0}"/></linearGradient>
  <linearGradient id="${g}sk" x1="0" x2="1"><stop offset="0" stop-color="${sk}" stop-opacity="1"/><stop offset=".55" stop-color="${sk}"/><stop offset="1" stop-color="${sk}"/></linearGradient>
  <linearGradient id="${g}st" x1="0" x2="1"><stop offset="0" stop-color="#8a96a6"/><stop offset=".5" stop-color="#f1f5fa"/><stop offset="1" stop-color="#7b8796"/></linearGradient>
  <radialGradient id="${g}hc"><stop offset="0" stop-color="#ffffff"/><stop offset=".6" stop-color="#fffbe6" stop-opacity=".9"/><stop offset="1" stop-color="#fff6c8" stop-opacity="0"/></radialGradient><radialGradient id="${g}hg"><stop offset="0" stop-color="#ffffff" stop-opacity=".95"/><stop offset=".5" stop-color="#fff6c8" stop-opacity=".5"/><stop offset="1" stop-color="#fff6c8" stop-opacity="0"/></radialGradient>`).replace('viewBox="-600 -600 1200 1000"','viewBox="-420 -480 840 920"');
}
function DRAW(spec,k,T,A,A2){ // spec: "castle" أو "char:saladin" أو {k:"mosque",o:{...}}
 if(typeof spec==='string'){if(spec.startsWith('char:'))return CH(spec.slice(5),k,T);return ILL[spec]?ILL[spec](k,T,A,A2,{}):'';}
 if(spec.char)return CH(spec.char,k,T);return ILL[spec.k]?ILL[spec.k](k,T,A,A2,spec.o||{}):'';}
// ===== دفعة 2: الأنبياء وأهل البيت =====
Object.assign(CHARS,{
 noah:{head:'glow',robe:['#6a4a2a','#8a6a3a'],cape:'#3a5a3a',trim:'#e8c26a',item:'none'},
 ali:{head:'glow',robe:['#14653f','#1d8a57'],cape:'#0d3a26',trim:'#e8c26a',item:'dhulfiqar'},
 yusuf:{head:'glow',robe:['#e9e2d2','#ffffff'],cape:'#2e6ab0',trim:'#e8c26a',item:'none'},
 bilal:{head:'glow',robe:['#f2efe6','#ffffff'],cape:'#7a5a3a',trim:'#c9a878',item:'none'},
 yunus:{head:'glow',robe:['#2a5a7a','#3a7aa0'],cape:'#1a3a50',trim:'#c4e3ff',item:'none'},
 hasan:{head:'glow',robe:['#14653f','#1d8a57'],cape:'#e9e2d2',trim:'#e8c26a',item:'none'},
 husayn:{head:'glow',robe:['#111','#2a2a2a'],cape:'#14653f',trim:'#e8c26a',item:'sword'},
 abbas:{head:'glow',robe:['#14653f','#1d8a57'],cape:'#111',trim:'#e8c26a',item:'banner'},
 zaynab:{head:'glowf',hj:'#111',robe:['#111','#222'],cape:'#1a1a1a',trim:'#e8c26a',item:'none'},
});
(function(){const _CH=CH;CH=function(name,k,T){const o=typeof name==='string'?CHARS[name]:name;
 if(o.item==='dhulfiqar'||o.item==='banner'||o.head==='glowf'){
  let base=_CH(Object.assign({},o,{item:'none',head:o.head==='glowf'?'glow':o.head}),k,T);
  const it=_up(k,.6,.35);let add='';
  if(o.item==='dhulfiqar') add=`<g opacity="${it}" transform="translate(265,${90+(1-it)*120}) rotate(16)"><path d="M-12 60 L-12 -260 L-30 -330 L-4 -290 L0 -340 L6 -290 L30 -330 L12 -260 L12 60Z" fill="#dfe6ee" stroke="#8a96a6" stroke-width="3"/><rect x="-55" y="60" width="110" height="16" rx="8" fill="#d4a017"/><rect x="-10" y="76" width="20" height="80" rx="6" fill="#4a2a12"/><circle cx="0" cy="164" r="14" fill="#d4a017"/></g>`;
  if(o.item==='banner') add=`<g opacity="${it}" transform="translate(250,${(1-it)*120})"><rect x="-6" y="-380" width="12" height="800" fill="#5a3a1a"/><path d="M6 -380 Q90 ${-370+12*Math.sin(T*3)} 170 -378 L170 -220 Q90 ${-212+12*Math.sin(T*3+1)} 6 -222Z" fill="#14653f"/><circle cx="0" cy="-392" r="14" fill="#d4a017"/></g>`;
  if(o.head==='glowf') add+=`<g opacity="${_up(k,.2,.35)}"><path d="M-175 170 C-200 -60 -140 -200 0 -205 C140 -200 200 -60 175 170 C120 215 -120 215 -175 170Z M-118 20 C-118 -110 118 -110 118 20 C118 120 60 160 0 160 C-60 160 -118 120 -118 20Z" fill="${o.hj}" fill-rule="evenodd"/></g>`;
  return base.replace('</svg>',add+'</svg>');}
 return _CH(name,k,T);};})();
ILL.ark=(k,T,A,A2)=>{const u=_up(k,.15,.6);const planks=Math.round(10*u);
 return _svg(`${ground(k,'#8a6a3a')}<g ${rise(k,0,.3,60)}>${[...Array(5)].map((_,i)=>`<path d="M${-420+i*200} 300 L${-400+i*200} 120" stroke="#6b4423" stroke-width="10"/>`).join('')}</g>
  <path d="M-420 160 L420 160 L330 290 L-330 290Z" fill="none" stroke="#7a4a22" stroke-width="6" stroke-dasharray="20 10"/>
  ${[...Array(planks)].map((_,i)=>`<path d="M${-420+i*84} ${160+(i%2)*4} L${-336+i*84} 160 L${-336+i*84-(i>4?-9:9)} 290 L${-420+i*84+(i>4?-9:9)} 290Z" fill="${i%2?'#8b5a2b':'#7a4a22'}"/>`).join('')}
  <g transform="translate(${-380+u*740},${120+Math.abs(Math.sin(T*6))*-30})" opacity="${_up(k,.3,.2)}"><rect x="-6" y="-60" width="12" height="70" fill="#5a3a1a" transform="rotate(${-40+Math.sin(T*6)*30})"/><rect x="-26" y="-80" width="52" height="28" fill="#555" transform="rotate(${-40+Math.sin(T*6)*30})"/></g>`,'')};
ILL.flood=(k,T,A,A2)=>{const rk=Math.sin(T*1.2)*5;
 const rain=[...Array(60)].map((_,i)=>{const x=-600+(i*97)%1200,y=((T*900+i*137)%1100)-650;return `<line x1="${x}" y1="${y}" x2="${x-12}" y2="${y+50}" stroke="#9fc3e6" stroke-width="3" opacity="${_up(k,0,.4)*.7}"/>`}).join('');
 const wave=(y,c,ph)=>`<path d="M-640 ${y} ${[...Array(15)].map((_,i)=>`Q${-595+i*90} ${y-36*Math.sin(T*2+i+ph)} ${-550+i*90} ${y}`).join(' ')} L640 420 L-640 420Z" fill="${c}"/>`;
 return _svg(`<rect x="-600" y="-600" width="1200" height="1000" fill="#1a2330" opacity="${_up(k,0,.4)*.5}"/>${rain}
  <g transform="translate(0,${40+Math.sin(T*1.2)*14+(1-_up(k,.1,.5))*300}) rotate(${rk})"><path d="M-380 60 L380 60 L300 200 L-300 200Z" fill="#7a4a22"/><rect x="-220" y="-90" width="440" height="150" fill="#8b5a2b"/><path d="M-250 -90 L0 -200 L250 -90Z" fill="#6b3f1d"/>${[...Array(5)].map((_,i)=>`<rect x="${-180+i*85}" y="-40" width="40" height="40" rx="6" fill="#3a2010"/>`).join('')}</g>
  ${wave(220,'#1e4a72',0)}${wave(270,'#2a6aa0',1)}${wave(320,'#3a86c0',2)}`,'')};
ILL.mountain=(k,T,A,A2)=>{const g=U('mt');
 return _svg(`<circle cx="0" cy="-200" r="${300*_up(k,.5,.4)}" fill="url(#${g}g)"/><g ${rise(k,0,.35,100)}><path d="M-600 300 L-250 -120 L-120 0 L60 -260 L300 40 L600 300Z" fill="#5a6a4a"/><path d="M60 -260 L-20 -160 L30 -170 L60 -200 L100 -150 L140 -180Z" fill="#e8eef4"/></g>
  <g ${rise(k,.35,.4,-160)}><g transform="translate(60,-250) scale(.45)"><path d="M-380 60 L380 60 L300 200 L-300 200Z" fill="#7a4a22"/><rect x="-220" y="-90" width="440" height="150" fill="#8b5a2b"/><path d="M-250 -90 L0 -200 L250 -90Z" fill="#6b3f1d"/></g></g>
  <g ${rise(k,0,.3,40)}><path d="M-600 330 Q0 290 600 330 L600 400 L-600 400Z" fill="#3a86c0" opacity=".8"/></g>`,_glow(g+'g','#fff3c4'))};
ILL.well=(k,T,A,A2)=>{const g=U('wl');
 return _svg(`<circle cx="260" cy="-300" r="${70*_up(k,0,.4)}" fill="#fff3c4"/><circle cx="290" cy="-315" r="${62*_up(k,0,.4)}" fill="#141a2a"/>${ground(k,'#b48a52',250)}
  <g ${rise(k,.1,.35,100)}><path d="M-200 250 L-200 40 Q0 0 200 40 L200 250Z" fill="#8a7458"/>${[...Array(4)].map((_,r)=>[...Array(5)].map((_,c)=>`<rect x="${-200+c*80+(r%2)*40}" y="${60+r*48}" width="76" height="44" fill="none" stroke="#5e4a34" stroke-width="3"/>`).join('')).join('')}
   <ellipse cx="0" cy="40" rx="200" ry="44" fill="#5e4a34"/><ellipse cx="0" cy="44" rx="170" ry="34" fill="#0a0a10"/></g>
  <g ${rise(k,.35,.3,60)}><rect x="-230" y="-200" width="18" height="250" fill="#6b4423"/><rect x="212" y="-200" width="18" height="250" fill="#6b4423"/><rect x="-240" y="-210" width="480" height="20" fill="#7a4a22"/><line x1="0" y1="-190" x2="0" y2="${-60+Math.sin(T*2)*12}" stroke="#c9a878" stroke-width="5"/><path d="M-30 ${-60+Math.sin(T*2)*12} h60 l-10 50 h-40z" fill="#7a4a22"/></g>
  <circle cx="0" cy="44" r="${40+30*Math.sin(T*2)}" fill="url(#${g}g)" opacity="${_up(k,.6,.3)}"/>`,_glow(g+'g','#fff3c4'))};
ILL.dream=(k,T,A,A2)=>{const g=U('dr');
 const star=(x,y,i)=>{const u=_bk(k,.15+i*.05,.3);const tw=.7+.3*Math.sin(T*3+i);return `<g transform="translate(${x},${y}) scale(${u*tw})"><path d="M0 -26 L7 -8 L26 -8 L11 4 L17 24 L0 12 L-17 24 L-11 4 L-26 -8 L-7 -8Z" fill="#ffe680"/></g>`};
 const pos=[...Array(11)].map((_,i)=>{const a=Math.PI*(1.05+i*.09);return [Math.cos(a)*360,Math.sin(a)*300+80]});
 return _svg(`<circle cx="0" cy="-20" r="${420*_up(k,.6,.4)}" fill="url(#${g}g)"/>${pos.map(([x,y],i)=>star(x,y,i)).join('')}
  <g ${pop(k,.75,.3,-150,60)}><circle cx="-150" cy="60" r="90" fill="#ffb347"/><circle cx="-150" cy="60" r="130" fill="url(#${g}s)"/></g>
  <g ${pop(k,.85,.3,150,60)}><path d="M150 -20 a80 80 0 1 0 0.1 0 M185 -10 a68 68 0 1 0 0.1 0" fill="#fff3c4" fill-rule="evenodd"/></g>`,_glow(g+'g',A2)+_glow(g+'s','#ffb347'))};
ILL.pyramids=(k,T,A,A2)=>{const g=U('py');
 return _svg(`<circle cx="300" cy="-200" r="${90*_up(k,0,.4)}" fill="#ffcf6a"/><circle cx="300" cy="-200" r="${200*_up(k,0,.4)}" fill="url(#${g}g)"/>${ground(k,'#d9a85a')}
  ${[[-250,300,280,.1],[110,300,360,.2],[400,300,200,.3]].map(([x,y,s,d])=>`<g ${rise(k,d,.35,120)}><path d="M${x-s} ${y} L${x} ${y-s*1.05} L${x+s} ${y}Z" fill="#e0b25e"/><path d="M${x} ${y-s*1.05} L${x+s} ${y} L${x+s*.35} ${y}Z" fill="#c0904a"/></g>`).join('')}
  <g ${rise(k,.5,.3,40)}><path d="M-600 330 Q-200 300 0 320 Q300 340 600 315 L600 400 L-600 400Z" fill="#2a86b4"/></g>`,_glow(g+'g','#ffcf6a'))};
ILL.whale=(k,T,A,A2,o={})=>{const sw=Math.sin(T*1.6)*10;const u=_up(k,.1,.5);
 return _svg(`<rect x="-600" y="-600" width="1200" height="1000" fill="#06203a" opacity="${u*.6}"/>${[...Array(18)].map((_,i)=>{const p=(T*.25+i/18)%1;return `<circle cx="${-500+(i*173)%1000}" cy="${300-p*900}" r="${4+(i%4)*3}" fill="none" stroke="#7fc0ee" stroke-width="2" opacity="${u*(1-p)}"/>`}).join('')}
  <g transform="translate(${(1-u)*-700},${sw}) ">
   <path d="M-420 0 C-420 -170 -150 -230 120 -200 C300 -180 420 -100 440 0 C420 110 280 170 80 170 C-150 170 -400 140 -420 0Z" fill="#2c5f8a"/>
   <path d="M-410 30 C-300 120 0 160 280 120 C360 100 420 60 440 0 C420 110 280 170 80 170 C-150 170 -380 140 -410 30Z" fill="#cfe3ef"/>
   ${[...Array(7)].map((_,i)=>`<path d="M${-250+i*60} 100 l20 40" stroke="#9cbfd6" stroke-width="5"/>`).join('')}
   <path d="M430 -10 C500 -80 560 -120 600 -150 C580 -60 560 -20 600 60 C540 40 490 30 430 20Z" fill="#2c5f8a" transform="rotate(${Math.sin(T*2)*6} 430 0)"/>
   <circle cx="-300" cy="-60" r="16" fill="#0a1a2a"/><circle cx="-294" cy="-66" r="5" fill="#fff"/>
   <path d="M-420 20 Q-360 50 -300 40" stroke="#1a3a5a" stroke-width="6" fill="none"/>
   ${o.glow?`<circle cx="0" cy="-20" r="${70+10*Math.sin(T*3)}" fill="#fff6c8" opacity=".85"/><circle cx="0" cy="-20" r="140" fill="#fff6c8" opacity=".25"/>`:''}</g>`,'')};
ILL.plant=(k,T,A,A2)=>{const g=U('pl');const u=_up(k,.1,.6);
 const leaf=(x,y,r,i)=>{const s=_bk(k,.2+i*.06,.3);return `<g transform="translate(${x},${y}) rotate(${r+Math.sin(T*2+i)*5}) scale(${s})"><path d="M0 0 C60 -60 160 -40 190 10 C140 50 50 50 0 0Z" fill="#3fae5a"/><path d="M0 0 L170 8" stroke="#2a7a3a" stroke-width="4"/></g>`};
 return _svg(`<circle cx="0" cy="-60" r="${400*_up(k,.4,.4)}" fill="url(#${g}g)"/>${ground(k,'#d9a85a')}
  <path d="M0 300 C-20 200 30 100 0 ${300-460*u}" stroke="#2a7a3a" stroke-width="14" fill="none"/>
  ${leaf(0,180,-160,0)}${leaf(0,120,-20,1)}${leaf(0,40,-170,2)}${leaf(0,-40,-10,3)}${leaf(0,-110,-150,4)}
  <g ${pop(k,.8,.3,-120,240)}><ellipse cx="-130" cy="250" rx="70" ry="44" fill="#e8b04a"/><ellipse cx="120" cy="260" rx="56" ry="36" fill="#d89a3a"/></g>`,_glow(g+'g',A2))};
ILL.rock=(k,T,A,A2)=>{const g=U('rk');
 return _svg(`<circle cx="0" cy="-300" r="${120*_up(k,0,.4)}" fill="#ffb347"/><circle cx="0" cy="-300" r="${260*_up(k,0,.4)}" fill="url(#${g}g)"/>${[...Array(6)].map((_,i)=>`<path d="M${-360+i*140} ${-60+Math.sin(T*3+i)*8} q20 -20 40 0 q20 20 40 0" stroke="#ffcf8a" stroke-width="5" fill="none" opacity=".6"/>`).join('')}
  <g ${rise(k,0,.3,60)}><path d="M-600 300 Q0 200 600 300 L600 400 L-600 400Z" fill="#d9a85a"/></g>
  <g ${rise(k,.3,.4,-300)}><path d="M-200 250 C-240 160 -160 70 -40 70 C80 50 200 110 210 200 C220 260 150 280 0 280 C-120 285 -190 280 -200 250Z" fill="#7a6a5a"/><path d="M-120 120 C-60 100 0 110 40 130" stroke="#5a4a3a" stroke-width="8" fill="none"/></g>`,_glow(g+'g','#ff8a3a'))};
ILL.adhan=(k,T,A,A2)=>{const g=U('ad');
 const waves=[...Array(5)].map((_,i)=>{const p=(T*.6+i/5)%1;return `<path d="M${60+p*360} ${-430-p*120} a${120+p*360} ${120+p*360} 0 0 1 0 ${240+p*720}" stroke="${A2}" stroke-width="${8-p*6}" fill="none" opacity="${(1-p)*_up(k,.5,.3)}" transform="rotate(-40 60 -350)"/>`}).join('');
 return _svg(`<circle cx="0" cy="-200" r="${380*_up(k,.4,.4)}" fill="url(#${g}g)"/>${ground(k,'#d7c7a3')}
  <g ${rise(k,.05,.4,200)}><rect x="-60" y="-350" width="120" height="650" fill="#efe6d2"/>${[0,1,2].map(i=>`<rect x="-80" y="${-250+i*170}" width="160" height="22" rx="6" fill="#cdbf9f"/>`).join('')}<path d="M-60 -350 L0 -470 L60 -350Z" fill="#2fae6a"/><circle cx="0" cy="-485" r="12" fill="#ffd76a"/><rect x="-20" y="-310" width="40" height="60" rx="20" fill="#3a2a1a"/></g>
  ${[1,-1].map(s=>[...Array(4)].map((_,i)=>{const p=(T*.6+i/4)%1;const r=90+p*380;return `<path d="M${s*r*Math.cos(.6)} ${-300-r*Math.sin(.6)} A${r} ${r} 0 0 ${s>0?1:0} ${s*r*Math.cos(.6)} ${-300+r*Math.sin(.6)}" stroke="${A2}" stroke-width="${7-p*5}" fill="none" opacity="${(1-p)*_up(k,.5,.3)}"/>`}).join('')).join('')}`,_glow(g+'g',A2))};
ILL.banner=(k,T,A,A2,o={})=>{const g=U('bn');const c=o.color||'#14653f';const u=_up(k,.1,.5);
 return _svg(`<circle cx="0" cy="-100" r="${400*_up(k,.4,.4)}" fill="url(#${g}g)"/><g transform="translate(-160,${(1-u)*300})"><rect x="-10" y="-500" width="20" height="900" fill="#5a3a1a"/><circle cx="0" cy="-515" r="22" fill="#d4a017"/>
  <path d="M10 -490 ${[...Array(8)].map((_,i)=>`L${10+(i+1)*55} ${-490+18*Math.sin(T*3+i*.8)*(i/8)}`).join(' ')} L450 -160 ${[...Array(8)].map((_,i)=>`L${450-(i+1)*55} ${-160+18*Math.sin(T*3+(8-i)*.8)*((8-i)/8)}`).join(' ')}Z" fill="${c}"/>
  <path d="M60 -440 L400 -440" stroke="#e8c26a" stroke-width="6" opacity=".7"/><path d="M60 -210 L400 -210" stroke="#e8c26a" stroke-width="6" opacity=".7"/></g>`,_glow(g+'g',A2))};
ILL.door=(k,T,A,A2)=>{const g=U('dr');const op=_up(k,.4,.5);
 return _svg(`<circle cx="0" cy="-60" r="${420*_up(k,.5,.4)}" fill="url(#${g}g)"/>
  <g ${rise(k,0,.35,100)}><rect x="-480" y="-300" width="960" height="600" fill="#5a4a3a"/>${[...Array(6)].map((_,r)=>[...Array(12)].map((_,c)=>`<rect x="${-480+c*80+(r%2)*40}" y="${-300+r*100}" width="76" height="96" fill="none" stroke="#3a2e22" stroke-width="3"/>`).join('')).join('')}
   <path d="M-200 300 L-200 -120 A200 200 0 0 1 200 -120 L200 300Z" fill="#fff3c4" opacity="${op*.9}"/></g>
  <g transform="translate(${-200+op*-60},${-op*40}) rotate(${-op*18} 0 300)" ${''}><path d="M0 300 L0 -120 A200 200 0 0 1 200 -120 L200 300Z" fill="#7a4a22" stroke="#4a2a12" stroke-width="8" transform="translate(0,0)"/>${[0,1,2,3].map(i=>`<rect x="0" y="${-60+i*90}" width="200" height="14" fill="#3a2a1a"/>`).join('')}${[...Array(8)].map((_,i)=>`<circle cx="${20+(i%2)*160}" cy="${-40+Math.floor(i/2)*90}" r="8" fill="#9aa3ad"/>`).join('')}</g>`,_glow(g+'g','#fff3c4'))};
ILL.tents=(k,T,A,A2)=>{const g=U('tn');
 const tent=(x,s,c,d)=>`<g ${rise(k,d,.3,80)}><g transform="translate(${x},300) scale(${s})"><path d="M-160 0 L0 -200 L160 0Z" fill="${c}"/><path d="M0 -200 L160 0 L40 0Z" fill="rgba(0,0,0,.25)"/><path d="M-30 0 L0 -90 L30 0Z" fill="#1a1208"/><line x1="0" y1="-200" x2="0" y2="-240" stroke="#5a3a1a" stroke-width="6"/></g></g>`;
 return _svg(`<circle cx="320" cy="-150" r="${90*_up(k,0,.4)}" fill="#ff7a3a"/><circle cx="320" cy="-150" r="${240*_up(k,0,.4)}" fill="url(#${g}g)"/>
  <g ${rise(k,0,.3,60)}><path d="M-600 300 Q-200 230 0 270 Q300 220 600 280 L600 400 L-600 400Z" fill="#c98f4a"/></g>
  ${tent(-380,.9,'#e9dcc0',.15)}${tent(-140,1.1,'#d9c8a6',.25)}${tent(120,.95,'#e9dcc0',.35)}${tent(360,.8,'#d9c8a6',.45)}
  ${[-520,520].map((x,i)=>`<g ${rise(k,.5+i*.05,.3,60)}><rect x="${x-8}" y="80" width="16" height="220" fill="#6b4423"/>${[...Array(6)].map((_,j)=>`<path d="M${x} 80 q${Math.cos(j)*90} ${-40+Math.sin(j)*30} ${Math.cos(j*1.1)*150} ${30+j*6}" stroke="#2f7a3a" stroke-width="16" fill="none" stroke-linecap="round"/>`).join('')}</g>`).join('')}`,_glow(g+'g','#ff7a3a'))};
ILL.dates=(k,T,A,A2)=>{const g=U('dt');
 return _svg(`<circle cx="0" cy="0" r="${380*_up(k,.4,.4)}" fill="url(#${g}g)"/><g ${rise(k,0,.35,100)}><path d="M-260 60 L260 60 L200 280 L-200 280Z" fill="#b5843a"/>${[...Array(5)].map((_,i)=>`<path d="M${-250+i*10} ${100+i*36} L${250-i*10} ${100+i*36}" stroke="#8a5a2a" stroke-width="6"/>`).join('')}</g>
  ${[...Array(16)].map((_,i)=>{const u=_bk(k,.3+i*.03,.3);return `<ellipse cx="${-200+(i%8)*57}" cy="${50-Math.floor(i/8)*40-(1-u)*200}" rx="30" ry="20" fill="#6a2a12" opacity="${_e(u*2)}" transform="rotate(${i*23} ${-200+(i%8)*57} ${50-Math.floor(i/8)*40})"/>`}).join('')}
  <g ${pop(k,.75,.3,0,-200)}><path d="M-120 -160 a60 60 0 0 1 120 0 a60 60 0 0 1 120 0 q0 90 -120 160 q-120 -70 -120 -160z" fill="#e74c3c" transform="translate(0,-60) scale(.8)"/></g>`,_glow(g+'g',A2))};
ILL.shrine=(k,T,A,A2)=>ILL.mosque(k,T,A,A2,{dome:'#d4a017',dome2:'#ffe9a0',wall:'#e9d8b6'});
