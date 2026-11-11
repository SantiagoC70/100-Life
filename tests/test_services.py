import tempfile, unittest
from datetime import date, datetime, timedelta
from pathlib import Path
from src.db import init_db
from src.services import *

class ServicesTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.db=Path(self.tmp.name)/"test.db"; init_db(self.db)
  register("general_user","password1",self.db); register("athlete_user","password2",self.db)
  self.general=authenticate("general_user","password1",self.db)["id"]; self.athlete=authenticate("athlete_user","password2",self.db)["id"]
  for uid,kind in ((self.general,"general"),(self.athlete,"atleta")): save_profile(uid,{"student_type":kind,"study_preference":"Tarde","sleep_start":"23:00","sleep_end":"07:00","water_goal_ml":2000},self.db)
 def tearDown(self): self.tmp.cleanup()
 def test_persistence_conflicts_and_isolation(self):
  self.assertEqual(get_profile(self.general,self.db)["student_type"],"general")
  start=datetime(2030,1,2,9); save_activity(self.general,{"title":"Clase","kind":"clase","starts_at":start,"ends_at":start+timedelta(hours=1)},path=self.db)
  self.assertEqual(conflicts(self.athlete,start,start+timedelta(hours=1),path=self.db),[])
  self.assertEqual(len(conflicts(self.general,start+timedelta(minutes=30),start+timedelta(hours=2),path=self.db)),1)
  self.assertEqual(conflicts(self.general,start+timedelta(hours=1),start+timedelta(hours=2),path=self.db),[])
 def test_hydration_total_edit_delete(self):
  day=date(2030,2,3); entry=add_water(self.general,250,datetime(2030,2,3),self.db); add_water(self.general,400,datetime(2030,2,3,12),self.db); add_water(self.athlete,999,datetime(2030,2,3,12),self.db)
  self.assertEqual(water_total(self.general,day,self.db),650); update_water(self.general,entry,300,datetime(2030,2,3,8),self.db); self.assertEqual(water_total(self.general,day,self.db),700); delete_water(self.general,entry,self.db); self.assertEqual(water_total(self.general,day,self.db),400)
 def test_recommendations_avoid_busy_and_sleep(self):
  now=datetime(2030,3,4,8); deadline=datetime(2030,3,4,13)
  task=save_activity(self.general,{"title":"Ensayo","kind":"tarea","starts_at":deadline-timedelta(hours=2),"ends_at":deadline,"deadline":deadline,"priority":3},path=self.db)
  save_activity(self.general,{"title":"Clase","kind":"clase","starts_at":datetime(2030,3,4,9),"ends_at":datetime(2030,3,4,10)},path=self.db)
  result=recommend_study_blocks(self.general,task,self.db,now); self.assertEqual(result["missing_minutes"],0)
  for block in result["blocks"]: self.assertFalse(block["start"]<datetime(2030,3,4,10) and block["end"]>datetime(2030,3,4,9)); self.assertGreaterEqual(block["start"].hour,7)

if __name__=="__main__": unittest.main()
