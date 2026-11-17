
document.querySelectorAll('.card').forEach(c=>{
  const a=c.querySelector('audio'), bs=c.querySelectorAll('.tempos button'), l=c.querySelector('input');
  bs.forEach(b=>b.onclick=()=>{const play=!a.paused; a.src=b.dataset.src; bs.forEach(x=>x.classList.remove('on'));
    b.classList.add('on'); if(play) a.play();});
  l.onchange=()=>a.loop=l.checked;
});
