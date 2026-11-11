"""Interfaz Streamlit de 100%LIFE."""
from calendar import monthrange
from datetime import date, datetime, time, timedelta
import streamlit as st
from src.db import init_db
from src.services import *

st.set_page_config(page_title="100%LIFE", page_icon="💯", layout="wide", initial_sidebar_state="collapsed")
init_db()
MONTHS=("","Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre")

def dt(d,t): return datetime.combine(d,t)
def go(page): st.session_state.page=page

def styles():
 st.markdown("""<style>
 .stApp{background:#f6f8fc;color:#172033}[data-testid="stHeader"]{background:transparent}[data-testid="stSidebar"]{display:none}.block-container{max-width:1320px;padding-top:1.2rem}
 .brand{font-size:1.55rem;font-weight:800;letter-spacing:-.04em}.brand span{color:#2563eb}.eyebrow{color:#64748b;font-size:.76rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase}.hero{font-size:2rem;font-weight:800;letter-spacing:-.045em}
 .card{background:#fff;border:1px solid #e8edf5;border-radius:18px;padding:1rem;box-shadow:0 8px 24px #1e345c0d}.muted{color:#64748b}.dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#ef4444;margin-right:7px}
 .water-card{background:linear-gradient(145deg,#eff7ff,#fff);border:1px solid #dcecff;border-radius:24px;padding:1.5rem;text-align:center}.glass{position:relative;width:128px;height:170px;margin:12px auto 18px;border:8px solid #b9d8f3;border-top-width:4px;border-radius:8px 8px 30px 30px;overflow:hidden;background:#fff}.water{position:absolute;left:0;right:0;bottom:0;background:linear-gradient(#4ba9ff,#1479ea)}.water:before{content:'';position:absolute;left:-10%;top:-5px;width:120%;height:12px;background:#7cc3ff;border-radius:50%}.water-number{font-size:2rem;font-weight:800;color:#145fc3}
 .reminder{padding:.85rem 1rem;border-radius:14px;background:#fff7ed;border:1px solid #fed7aa;margin:.45rem 0}div[data-testid="stButton"] button{border-radius:12px;font-weight:700}@media(max-width:760px){.hero{font-size:1.5rem}.block-container{padding:.8rem}}
 </style>""",unsafe_allow_html=True)

def login():
 st.markdown("<div class='brand'>100%<span>LIFE</span></div>",unsafe_allow_html=True); st.title("Organiza tus días. Cuida de ti."); st.caption("Estudios, hidratación y entrenamiento en un solo lugar.")
 _,center,_=st.columns([1,1.25,1])
 with center:
  a,b=st.tabs(["Iniciar sesión","Crear cuenta"])
  with a,st.form("login"):
   u=st.text_input("Usuario"); p=st.text_input("Contraseña",type="password")
   if st.form_submit_button("Entrar",use_container_width=True,type="primary"):
    user=authenticate(u,p)
    if user: st.session_state.user=user; go("Inicio"); st.rerun()
    st.error("Credenciales incorrectas.")
  with b,st.form("register"):
   u=st.text_input("Usuario",key="ru"); p=st.text_input("Contraseña (mínimo 8 caracteres)",type="password",key="rp"); c=st.text_input("Confirmar",type="password")
   if st.form_submit_button("Crear cuenta",use_container_width=True):
    if p!=c: st.error("Las contraseñas no coinciden.")
    else:
     ok,msg=register(u,p); (st.success if ok else st.error)(msg)

def profile(uid,first=False):
 cur=get_profile(uid) or {}; st.header("Completa tu perfil" if first else "Configuración"); st.caption("Personaliza tus hábitos, horarios y meta.")
 with st.form("profile"):
  athlete=st.radio("Tipo de estudiante",["general","atleta"],index=1 if cur.get("student_type")=="atleta" else 0,format_func=lambda x:"Estudiante atleta" if x=="atleta" else "Estudiante general",horizontal=True)
  opts=["Mañana","Tarde","Noche","Sin preferencia"]; pref=st.selectbox("Preferencia de estudio",opts,index=opts.index(cur.get("study_preference","Sin preferencia")))
  a,b=st.columns(2); sleep1=a.time_input("Hora de dormir",time.fromisoformat(cur.get("sleep_start","23:00"))); sleep2=b.time_input("Hora de despertar",time.fromisoformat(cur.get("sleep_end","07:00")))
  food=st.text_input("Preferencias alimentarias",cur.get("dietary_preferences","")); restrictions=st.text_input("Restricciones o alergias",cur.get("dietary_restrictions","")); goal=st.number_input("Meta de agua (ml/día)",250,10000,int(cur.get("water_goal_ml",2000)),50)
  if st.form_submit_button("Guardar configuración",use_container_width=True,type="primary"):
   save_profile(uid,{"student_type":athlete,"study_preference":pref,"sleep_start":sleep1.strftime("%H:%M"),"sleep_end":sleep2.strftime("%H:%M"),"dietary_preferences":food,"dietary_restrictions":restrictions,"water_goal_ml":goal}); go("Inicio"); st.rerun()

def topbar(user):
 logo,_,update,menu=st.columns([2,5,1.4,1.7],vertical_alignment="center"); logo.markdown("<div class='brand'>100%<span>LIFE</span></div>",unsafe_allow_html=True)
 with update.popover("🔄 Actualizar",use_container_width=True):
  for label,page in (("📅 Pendientes","Pendientes"),("💧 Hidratación","Hidratación"),("🏃 Entrenamiento","Entrenamiento")):
   if st.button(label,use_container_width=True): go(page); st.rerun()
 with menu.popover(f"👤 {user['username']}",use_container_width=True):
  st.markdown(f"**{user['username']}**"); st.caption("Tu perfil de 100%LIFE")
  for label,page in (("⚙️ Configuración","Configuración"),("📈 Seguimiento","Seguimiento")):
   if st.button(label,use_container_width=True): go(page); st.rerun()
  if st.button("Cerrar sesión",use_container_width=True): st.session_state.clear(); st.rerun()
 st.divider()

def activity_form(uid,old=None,workout=False):
 old=old or {}
 with st.expander("Editar actividad" if old else ("Registrar entrenamiento" if workout else "Nueva actividad"),expanded=not old),st.form(f"act{old.get('id','new')}{workout}"):
  title=st.text_input("Título",old.get("title","")); kind="entrenamiento" if workout else st.selectbox("Tipo",KINDS,index=KINDS.index(old.get("kind","tarea")))
  s=datetime.fromisoformat(old.get("starts_at",datetime.now().replace(second=0,microsecond=0).isoformat())); e=datetime.fromisoformat(old.get("ends_at",(datetime.now()+timedelta(hours=1)).replace(second=0,microsecond=0).isoformat()))
  a,b,c,d=st.columns(4); sd=a.date_input("Fecha",s.date()); stime=b.time_input("Inicio",s.time()); ed=c.date_input("Fecha final",e.date()); etime=d.time_input("Fin",e.time())
  priority=st.select_slider("Prioridad",[1,2,3],value=int(old.get("priority",2)),format_func=lambda x:{1:"Baja",2:"Media",3:"Alta"}[x]); deadline=None
  if not workout and st.checkbox("Tiene fecha límite",bool(old.get("deadline"))):
   limit=datetime.fromisoformat(old["deadline"]) if old.get("deadline") else e; a,b=st.columns(2); deadline=dt(a.date_input("Fecha límite",limit.date()),b.time_input("Hora límite",limit.time()))
  notes=st.text_area("Notas o tipo de entrenamiento",old.get("notes","")); intensity=fatigue=None; pain=False
  if kind=="entrenamiento":
   a,b=st.columns(2); intensity=a.slider("Intensidad",1,5,int(old.get("perceived_intensity") or 3)); fatigue=b.slider("Fatiga",1,5,int(old.get("fatigue") or 3)); pain=st.checkbox("Dolor o síntomas preocupantes",bool(old.get("pain")))
  if st.form_submit_button("Guardar",use_container_width=True,type="primary"):
   start,end=dt(sd,stime),dt(ed,etime)
   try:
    overlap=conflicts(uid,start,end,old.get("id"))
    if overlap: st.error("Conflicto con: "+", ".join(x["title"] for x in overlap))
    else: save_activity(uid,{"title":title,"kind":kind,"starts_at":start,"ends_at":end,"priority":priority,"deadline":deadline,"notes":notes,"perceived_intensity":intensity,"fatigue":fatigue,"pain":pain},old.get("id")); st.rerun()
   except ValueError as ex: st.error(str(ex))

def month_calendar(items):
 today=date.today(); shown=st.session_state.get("calendar_month",today.replace(day=1)); prev,title,nxt=st.columns([1,4,1],vertical_alignment="center")
 if prev.button("←",use_container_width=True): st.session_state.calendar_month=(shown-timedelta(days=1)).replace(day=1); st.rerun()
 title.markdown(f"### {MONTHS[shown.month]} {shown.year}")
 if nxt.button("→",use_container_width=True): st.session_state.calendar_month=(shown.replace(day=28)+timedelta(days=4)).replace(day=1); st.rerun()
 for col,name in zip(st.columns(7),("L","M","M","J","V","S","D")): col.markdown(f"<div style='text-align:center;color:#64748b;font-weight:700'>{name}</div>",unsafe_allow_html=True)
 offset,days=monthrange(shown.year,shown.month); cells=[None]*offset+list(range(1,days+1)); cells += [None]*((7-len(cells)%7)%7); busy={datetime.fromisoformat(x["deadline"] or x["starts_at"]).date() for x in items}
 for i in range(0,len(cells),7):
  for col,num in zip(st.columns(7),cells[i:i+7]):
   if num:
    day=date(shown.year,shown.month,num)
    if col.button(f"{num}{' •' if day in busy else ''}",key=f"day{day}",use_container_width=True,type="primary" if day==st.session_state.get("selected_day",today) else "secondary"): st.session_state.selected_day=day; st.rerun()

def day_summary(uid,items):
 selected=st.session_state.get("selected_day",date.today()); st.markdown(f"#### {selected:%d/%m/%Y}"); found=[x for x in items if datetime.fromisoformat(x["deadline"] or x["starts_at"]).date()==selected]
 if not found: st.info("No hay pendientes para esta fecha.")
 for x in found:
  due=datetime.fromisoformat(x["deadline"] or x["starts_at"]); st.markdown(f"<div class='card'><span class='dot'></span><b>{x['title']}</b><br><span class='muted'>{x['kind'].capitalize()} · {due:%H:%M} h</span></div>",unsafe_allow_html=True)
  if st.button("Hecho",key=f"done{x['id']}",use_container_width=True,type="primary"): set_completed(uid,x["id"],True); st.rerun()

def water_glass(uid,quick=True):
 total=water_total(uid,date.today()); goal=get_profile(uid)["water_goal_ml"]; pct=min(total/goal*100,100)
 st.markdown(f"<div class='water-card'><div class='eyebrow'>Hidratación de hoy</div><div class='glass'><div class='water' style='height:{pct:.0f}%'></div></div><div class='water-number'>{total:,} ml</div><div class='muted'>de {goal:,} ml · {pct:.0f}%</div></div>",unsafe_allow_html=True)
 if quick:
  amount=st.select_slider("Agregar agua",[150,250,350,500,750],value=250,format_func=lambda x:f"{x} ml")
  if st.button("+ Registrar agua",use_container_width=True,type="primary"): add_water(uid,amount,datetime.now()); st.rerun()

def reminder_panel(uid,items):
 now=datetime.now(); upcoming=[]
 for x in items:
  due=datetime.fromisoformat(x["deadline"] or x["starts_at"]); delta=due-now
  if timedelta(0)<=delta<=timedelta(hours=24): upcoming.append((x,max(1,int(delta.total_seconds()//3600))))
 remaining=max(0,get_profile(uid)["water_goal_ml"]-water_total(uid,date.today()))
 if upcoming or remaining>=500: st.markdown("### Recordatorios")
 for x,hours in upcoming: st.markdown(f"<div class='reminder'>⏰ <b>{x['title']}</b> comienza o vence en aproximadamente {hours} h.</div>",unsafe_allow_html=True)
 if remaining>=500: st.markdown(f"<div class='reminder'>💧 Te faltan <b>{remaining:,} ml</b> para alcanzar tu meta de hoy.</div>",unsafe_allow_html=True)

def dashboard(uid,name):
 pending=[x for x in list_activities(uid) if not x["completed"] and x["kind"]!="entrenamiento"]
 st.markdown("<div class='eyebrow'>Panel principal</div>",unsafe_allow_html=True); st.markdown(f"<div class='hero'>Hola, {name} 👋</div>",unsafe_allow_html=True); st.caption("Esto es lo importante para tu día."); reminder_panel(uid,pending)
 left,right=st.columns([1.75,1],gap="large")
 with left: st.markdown("### Calendario de pendientes"); month_calendar(pending); day_summary(uid,pending)
 with right:
  water_glass(uid); st.markdown("### Próximos")
  upcoming=sorted(pending,key=lambda x:x["deadline"] or x["starts_at"])[:3]
  if not upcoming: st.success("Estás al día. No hay pendientes.")
  for x in upcoming:
   due=datetime.fromisoformat(x["deadline"] or x["starts_at"]); st.markdown(f"**{x['title']}**  \n{due:%d/%m · %H:%M} h")

def pending_page(uid):
 st.header("Pendientes"); st.caption("Crea, edita y organiza tus actividades escolares."); activity_form(uid); items=[x for x in list_activities(uid) if not x["completed"]]
 if not items: st.info("Aún no hay actividades pendientes.")
 for x in items:
  s,e=datetime.fromisoformat(x["starts_at"]),datetime.fromisoformat(x["ends_at"])
  with st.container(border=True):
   info,actions=st.columns([5,2]); info.markdown(f"**{x['title']}** · {x['kind'].capitalize()}  \n{s:%d/%m/%Y %H:%M}–{e:%H:%M} · Prioridad {x['priority']}/3")
   if actions.button("✓ Hecho",key=f"c{x['id']}",use_container_width=True): set_completed(uid,x["id"],True); st.rerun()
   if actions.button("Eliminar",key=f"d{x['id']}",use_container_width=True): delete_activity(uid,x["id"]); st.rerun()
   activity_form(uid,x)

def hydration_page(uid):
 st.header("Hidratación"); visual,form=st.columns([1,1.4],gap="large")
 with visual: water_glass(uid,False)
 with form,st.form("water"):
  st.subheader("Registrar consumo"); amount=st.number_input("Cantidad (ml)",1,5000,250,50); a,b=st.columns(2); day=a.date_input("Fecha",date.today()); clock=b.time_input("Hora",datetime.now().time())
  if st.form_submit_button("Registrar",use_container_width=True,type="primary"): add_water(uid,amount,dt(day,clock)); st.rerun()
 st.subheader("Historial")
 for x in water_history(uid):
  stamp=datetime.fromisoformat(x["consumed_at"])
  with st.expander(f"{stamp:%d/%m/%Y %H:%M} · {x['amount_ml']} ml"):
   if st.button("Eliminar registro",key=f"wdel{x['id']}"): delete_water(uid,x["id"]); st.rerun()

def training_page(uid):
 st.header("Entrenamiento"); st.caption("Registra tu sesión y recibe orientación general para recuperarte."); activity_form(uid,workout=True); workouts=[x for x in reversed(list_activities(uid)) if x["kind"]=="entrenamiento"]
 if not workouts: st.info("Registra tu primer entrenamiento para ver recomendaciones."); return
 latest=workouts[0]; st.subheader(f"Última sesión: {latest['title']}"); st.caption(f"{latest['notes'] or 'Sin detalles'} · Intensidad {latest['perceived_intensity'] or '—'}/5 · Fatiga {latest['fatigue'] or '—'}/5"); advice=wellbeing_advice(get_profile(uid),workouts); a,b=st.columns(2); a.info(f"**Recuperación**\n\n{advice['recuperacion']}"); b.success(f"**Nutrición**\n\n{advice['nutricion']}"); st.warning("Orientación general; no sustituye atención médica.")

def tracking(uid):
 st.header("Seguimiento"); acts=list_activities(uid); done=[x for x in acts if x["completed"]]; workouts=[x for x in acts if x["kind"]=="entrenamiento"]; start=date.today()-timedelta(days=6); weekly=sum(x["amount_ml"] for x in water_history(uid) if datetime.fromisoformat(x["consumed_at"]).date()>=start)
 a,b,c=st.columns(3); a.metric("Pendientes hechos",len(done)); b.metric("Entrenamientos",len(workouts)); c.metric("Agua · 7 días",f"{weekly:,} ml"); tasks,exercise,water=st.tabs(["Tareas y fechas","Ejercicio","Hidratación"])
 with tasks:
  if not done: st.info("Todavía no has marcado pendientes como hechos.")
  for x in reversed(done): st.markdown(f"✅ **{x['title']}** · {x['kind'].capitalize()}")
 with exercise:
  for x in reversed(workouts): st.markdown(f"🏃 **{x['title']}** · {datetime.fromisoformat(x['starts_at']):%d/%m/%Y} · Intensidad {x['perceived_intensity'] or '—'}/5")
 with water:
  for x in water_history(uid)[:30]: st.markdown(f"💧 **{x['amount_ml']} ml** · {datetime.fromisoformat(x['consumed_at']):%d/%m/%Y %H:%M}")

styles()
if "user" not in st.session_state: login(); st.stop()
user=st.session_state.user
if not get_profile(user["id"]): profile(user["id"],True); st.stop()
topbar(user); page=st.session_state.get("page","Inicio")
pages={"Inicio":lambda uid:dashboard(uid,user["username"]),"Pendientes":pending_page,"Hidratación":hydration_page,"Entrenamiento":training_page,"Configuración":profile,"Seguimiento":tracking}
pages.get(page,pages["Inicio"])(user["id"])
