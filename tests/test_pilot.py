"""Synthetic fixtures only. These tests are not participant records."""
import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('pilot_summary',Path(__file__).resolve().parents[1]/'scripts/summarize_pilot.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def row(tid='L1',cond='A',seconds=100):
    return {'kind':'human','consent':True,'packet':'pilot-v1','round':'initial','participant_id':'P01','task_id':tid,'condition':cond,'elapsed_seconds':seconds,'status':'completed','assisted':False,'criteria':{k:'yes' for k in m.TASKS[tid]['criteria']},'build':'synthetic-test-build','snapshot':'synthetic-test-snapshot'}

def test_empty_is_no_sessions_not_success():
    r=m.summarize([]);assert r['status']=='no sessions';assert r['participants']==0;assert r['median_paired_A_minus_B_seconds'] is None

def test_paired_time_requires_both_correct_and_reports_denominator():
    a=row();b=row('L2','B',80);r=m.summarize([a,b]);assert r['paired_denominator']==1;assert r['median_paired_A_minus_B_seconds']==20
    b['criteria']['value_unit']='no';r=m.summarize([a,b]);assert r['paired_denominator']==0;assert r['conditions']['B']['attempted']==1

def test_failures_assistance_and_timeouts_are_retained():
    a=row();a['assisted']=True;b=row('L2','B',245);b['status']='timeout';r=m.summarize([a,b]);assert r['conditions']['A']['assisted']==1;assert r['conditions']['B']['timeouts']==1;assert r['paired_denominator']==0

def test_unscored_prevents_final_summary():
    a=row();a['criteria']['value_unit']='pending';r=m.summarize([a]);assert r['status']=='scoring incomplete';assert r['conditions']['A']['correct_unassisted']==0

def test_rejects_synthetic_nonconsented_retest_and_duplicate():
    for field,value in [('kind','synthetic'),('consent',False),('round','retest')]:
        a=row();a[field]=value
        with pytest.raises(ValueError):m.summarize([a])
    with pytest.raises(ValueError):m.summarize([row(),row()])

def test_rejects_missing_rubric_and_invalid_duration():
    a=row();a['criteria']={}
    with pytest.raises(ValueError):m.summarize([a])
    for v in [-1,float('nan'),True]:
        a=row();a['elapsed_seconds']=v
        with pytest.raises(ValueError):m.summarize([a])
