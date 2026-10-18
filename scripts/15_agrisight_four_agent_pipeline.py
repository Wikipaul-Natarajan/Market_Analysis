"""Four-role AgriSight pipeline with local-first inputs and optional live context.

Default execution is offline. --live enables Open-Meteo forecast and official PIB RSS.
--llm calls a locally hosted Ollama-compatible endpoint only.
"""
from __future__ import annotations
import argparse, json, os, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
RUN_OUT=Path(os.environ.get('AGRISIGHT_RUN_DIR',str(ROOT/'outputs')))
PROC=ROOT/'data/processed'; EXT=ROOT/'data/external'; MODELS=RUN_OUT/'models'
OUT=RUN_OUT/'objective_completion_pipeline'
PIB_RSS=os.getenv('AGRI_PIB_RSS','https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=1')
WEATHER_URL=os.getenv('AGRI_WEATHER_URL','https://api.open-meteo.com/v1/forecast?latitude=13.0827&longitude=80.2707&daily=precipitation_sum,temperature_2m_max,temperature_2m_mean&timezone=Asia%2FKolkata&forecast_days=7')
USER_AGENT='Mozilla/5.0 (compatible; AgriSight-research/1.0)'
MAX_NEWS=int(os.getenv('AGRI_MAX_NEWS','10'))

def fetch(url,timeout=25,data=None,headers=None):
    """GET (or POST when data is given) with a browser-like User-Agent; returns bytes."""
    h={'User-Agent':USER_AGENT,'Accept':'*/*'}; h.update(headers or {})
    req=urllib.request.Request(url,data=data,headers=h)
    with urllib.request.urlopen(req,timeout=timeout) as r: return r.read()

def strip_html(text):
    import html, re
    return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',text or ''))).strip()
KEYWORDS=('agriculture','vegetable','horticulture','market price','price','procurement','rainfall','monsoon','tomato','onion','farmers welfare')

class DataCollectorAgent:
    name='Data Collector'
    def run(self,live=False):
        path=PROC/'tn_features.parquet'
        if not path.exists(): raise FileNotFoundError(f'Run feature engineering first: {path}')
        frame=pd.read_parquet(path); frame['arrival_date']=pd.to_datetime(frame.arrival_date)
        latest=frame.sort_values('arrival_date').groupby('commodity',as_index=False).tail(1).sort_values('commodity')
        as_of=pd.Timestamp(latest.arrival_date.max()).normalize()
        age_days=max(0,(pd.Timestamp.now().normalize()-as_of).days)
        context={'market_scope':'Tamil Nadu aggregate; the model input is not Koyambedu-specific',
                 'price_as_of':str(as_of.date()),'data_age_days':age_days,
                 'freshness_status':'CURRENT' if age_days<=3 else 'STALE_ABSTAIN',
                 'commodities':latest.commodity.tolist(),'latest_rows':latest.to_dict(orient='records'),
                 'weather_history_path':str(EXT/'weather_chennai.parquet'),'weather_forecast':None,
                 'live_context_requested':bool(live)}
        context['weather_status']='not_requested'
        if live:
            try:
                payload=json.loads(fetch(WEATHER_URL).decode('utf-8')); daily=payload.get('daily',{}) or {}
                rain=[x for x in daily.get('precipitation_sum',[]) if x is not None]
                tmax=[x for x in daily.get('temperature_2m_max',[]) if x is not None]
                if not daily.get('time'): raise ValueError('response has no daily time axis')
                context['weather_forecast']={'daily':daily,'timezone':payload.get('timezone'),
                    'latitude':payload.get('latitude'),'longitude':payload.get('longitude'),'source':'Open-Meteo Forecast API',
                    'summary':{'start':daily['time'][0],'end':daily['time'][-1],'days':len(daily['time']),
                               'rain_total_mm':round(sum(rain),1),'wettest_day_mm':round(max(rain),1) if rain else None,
                               'rain_days_ge_10mm':sum(1 for x in rain if x>=10),'max_temp_c':round(max(tmax),1) if tmax else None}}
                context['weather_status']='ok'
            except Exception as exc:
                context['weather_status']='failed: '+str(exc)[:160]
        return context

class ForecastAgent:
    name='Price Forecaster'
    def run(self,context):
        import pickle
        path=MODELS/'ml_results.pkl'
        if not path.exists(): raise FileNotFoundError(f'Run scripts/07_ml_models.py first: {path}')
        with path.open('rb') as f: saved=pickle.load(f)
        raw=pd.read_parquet(PROC/'tn_vegetables_daily.parquet'); raw['arrival_date']=pd.to_datetime(raw.arrival_date)
        daily=raw.groupby(['arrival_date','commodity']).agg(modal_price=('modal_price','median'),
                    market_count=('market','nunique')).reset_index()
        last_date=max(pd.to_datetime(context['price_as_of']),daily.arrival_date.max())
        hist={}; counts={}; last_context={r['commodity']:r for r in context['latest_rows']}
        for commodity,g in daily.groupby('commodity'):
            g=g.set_index('arrival_date').sort_index().asfreq('D')
            hist[commodity]=g.modal_price.ffill(limit=3).dropna().astype(float)
            counts[commodity]=g.market_count.fillna(0).astype(float)
        forecast_by_commodity={c:{} for c in saved}
        model_by_commodity={c:saved[c]['model'] for c in saved}
        feature_by_commodity={c:saved[c]['features'] for c in saved}
        for step in range(1,15):
            target_date=last_date+pd.Timedelta(days=step); step_preds={}
            for commodity in saved:
                series=hist[commodity]; row={}; current=series.iloc[-1]
                for key in feature_by_commodity[commodity]:
                    if key.startswith('lag_'):
                        n=int(key.split('_')[1]); row[key]=series.iloc[-n] if len(series)>=n else current
                    elif key.startswith('rolling_mean_'):
                        n=int(key.rsplit('_',1)[1]); row[key]=series.tail(n).mean()
                    elif key.startswith('rolling_std_'):
                        n=int(key.rsplit('_',1)[1]); row[key]=series.tail(n).std()
                    elif key.startswith('rolling_min_'):
                        n=int(key.rsplit('_',1)[1]); row[key]=series.tail(n).min()
                    elif key.startswith('rolling_max_'):
                        n=int(key.rsplit('_',1)[1]); row[key]=series.tail(n).max()
                    elif key.startswith('ema_'):
                        n=int(key.split('_')[1]); row[key]=series.ewm(span=n,adjust=False).mean().iloc[-1]
                    elif key.startswith('cross_') and key.endswith('_lag1'):
                        peer=key[len('cross_'):-len('_lag1')]; peer=peer if peer in hist else peer.title()
                        row[key]=hist[peer].iloc[-1] if peer in hist else 0.0
                    elif key=='momentum_7': row[key]=series.pct_change(7).iloc[-1]
                    elif key=='momentum_14': row[key]=series.pct_change(14).iloc[-1]
                    elif key=='momentum_30': row[key]=series.pct_change(30).iloc[-1]
                    elif key=='price_acceleration': row[key]=series.pct_change(7).iloc[-1]-series.pct_change(14).iloc[-1]
                    elif key=='position_52w':
                        look=series.tail(365); span=look.max()-look.min(); row[key]=(current-look.min())/span if span else 0.0
                    elif key=='month': row[key]=target_date.month
                    elif key=='week_of_year': row[key]=int(target_date.isocalendar().week)
                    elif key=='day_of_week': row[key]=target_date.dayofweek
                    elif key=='sw_monsoon': row[key]=int(target_date.month in (6,7,8,9))
                    elif key=='ne_monsoon': row[key]=int(target_date.month in (10,11,12))
                    elif key=='pongal': row[key]=int(target_date.month==1 and 13<=target_date.day<=17)
                    elif key=='tamil_new_year': row[key]=int(target_date.month==4 and 13<=target_date.day<=15)
                    elif key=='diwali': row[key]=int(target_date.month in (10,11) and int(target_date.isocalendar().week) in range(40,47))
                    elif key=='navratri': row[key]=int(target_date.month in (9,10) and int(target_date.isocalendar().week) in range(38,43))
                    elif key=='market_count': row[key]=float(counts[commodity].iloc[-1]) if len(counts[commodity]) else 0.0
                    elif key in ('rain_7d_sum','rain_30d_sum','temp_max'):
                        row[key]=float(last_context[commodity].get(key,0.0) or 0.0)
                    else: row[key]=float(last_context[commodity].get(key,0.0) or 0.0)
                X=pd.DataFrame([[row.get(k,0.0) for k in feature_by_commodity[commodity]]],columns=feature_by_commodity[commodity]).astype(float)
                value=max(0.0,float(model_by_commodity[commodity].predict(X)[0])); step_preds[commodity]=value
            # Append all predictions together so cross-commodity lag features see the previous forecast day.
            for commodity,value in step_preds.items(): hist[commodity].loc[target_date]=value
            for commodity,value in step_preds.items(): forecast_by_commodity[commodity][step]=value
        forecasts=[]
        stale=context['freshness_status']!='CURRENT'
        for commodity in saved:
            latest=last_context[commodity]; current=float(latest['modal_price'])
            v7=forecast_by_commodity[commodity][7]; v14=forecast_by_commodity[commodity][14]
            pct=(v14/current-1)*100 if current else 0.0
            signal='ABSTAIN_STALE_DATA' if stale else 'BUY' if pct < -5 else 'SELL' if pct>5 else 'HOLD'
            forecasts.append({'commodity':commodity,'current_price':current,'forecast_7d':v7,'forecast_14d':v14,
                              'forecast_14d_change_pct':pct,'signal':signal,'freshness_status':context['freshness_status'],
                              'weather_feature_assumption':'last recorded weather values held constant; no weather forecast applied'})
        context['forecasts']=forecasts
        return context

class NewsReaderAgent:
    name='News Reader'
    def run(self,context,live=False):
        items=[]; context['news_status']='not_requested'
        if live:
            try:
                raw=fetch(PIB_RSS).lstrip(b'\xef\xbb\xbf').strip()
                root=ET.fromstring(raw); seen=set(); scanned=0
                for item in root.findall('.//item'):
                    scanned+=1
                    title=strip_html(item.findtext('title')); desc=strip_html(item.findtext('description'))
                    link=(item.findtext('link') or '').strip(); pub=(item.findtext('pubDate') or '').strip()
                    text=(title+' '+desc).casefold()
                    if title.casefold() in seen or not any(key in text for key in KEYWORDS): continue
                    seen.add(title.casefold())
                    items.append({'title':title,'summary':desc[:400],'url':link,'published':pub,'source':'PIB RSS'})
                    if len(items)>=MAX_NEWS: break
                context['news_status']=f'ok: {len(items)} relevant of {scanned} items'
            except Exception as exc:
                context['news_status']='failed: '+str(exc)[:160]
        context['news_items']=items; context['news_source']=PIB_RSS if live else 'Not fetched (offline run)'
        return context

class ReportWriterAgent:
    name='Report Writer'
    def __init__(self, use_llm=False): self.use_llm=use_llm
    def run(self,context):
        rows=context['forecasts']; news=context['news_items']
        base=['# AgriSight Market Intelligence Brief','',f"Price data through {context['price_as_of']}.",
              'Forecasts are from the available Tamil Nadu aggregate model; they are not Koyambedu-specific.',
              'This brief is decision support. It does not establish realized procurement savings.','', '## Price outlook','']
        base += [f"- **{r['commodity']}**: current {r['current_price']:.2f}; 7-day {r['forecast_7d']:.2f}; 14-day {r['forecast_14d']:.2f} ({r['forecast_14d_change_pct']:+.1f}%); signal {r['signal']}." for r in rows]
        base += ['', '## Weather outlook','']
        wf=context.get('weather_forecast')
        if wf:
            sm=wf['summary']
            base.append(f"Chennai forecast {sm['start']} to {sm['end']} (Open-Meteo): {sm['rain_total_mm']} mm total rain, "
                        f"wettest day {sm['wettest_day_mm']} mm, {sm['rain_days_ge_10mm']} day(s) with at least 10 mm, maximum temperature {sm['max_temp_c']} °C. "
                        'This is Chennai-area context, not a statewide forecast, and it is not an input to the price model.')
        else:
            base.append('Weather forecast is unavailable in this offline run.' if context.get('weather_status')=='not_requested'
                        else f"Weather forecast could not be retrieved ({context.get('weather_status')}).")
        base += ['', '## Policy and market news','']
        if news: base += [f"- [{x['title']}]({x['url']}) ({x['published']}): {x['summary']}" for x in news]
        elif context.get('news_status')=='not_requested': base.append('No RSS items were retrieved in this offline run.')
        elif str(context.get('news_status','')).startswith('ok'): base.append(f"No agriculture or price items in the current PIB feed ({context['news_status']}).")
        else: base.append(f"PIB news could not be retrieved ({context.get('news_status')}).")
        text='\n'.join(base)
        llm_status='not_requested'
        if self.use_llm:
            import re
            from urllib.parse import urlparse
            endpoint=os.getenv('AGRI_OLLAMA_URL','http://127.0.0.1:11434/api/generate')
            model=os.getenv('AGRI_OLLAMA_MODEL','llama3.1')
            host=(urlparse(endpoint).hostname or '').lower()
            context['llm_endpoint']=endpoint; context['llm_model']=model
            if host not in ('127.0.0.1','localhost','::1'):
                llm_status=f'refused_non_local_endpoint ({host}); fallback_template'
            else:
                prompt=('Rewrite these grounded facts as a concise buyer brief in Markdown. Preserve every number exactly as written, '
                        'keep every source, scope statement and caveat, and do not add facts, numbers or advice that are not present.\n\n'+text)
                try:
                    answer=json.loads(fetch(endpoint,timeout=int(os.getenv('AGRI_OLLAMA_TIMEOUT','180')),
                        data=json.dumps({'model':model,'prompt':prompt,'stream':False,'options':{'temperature':0}}).encode(),
                        headers={'Content-Type':'application/json'}).decode('utf-8'))
                    generated=(answer.get('response') or '').strip()
                    def norm(t):
                        t=re.sub(r'\b\d{4}-\d{2}-\d{2}\b',' ',t)   # dates are checked separately
                        out=set()
                        for n in re.findall(r'\d[\d,]*(?:\.\d+)?',t):
                            n=n.replace(',',''); n=n.rstrip('0').rstrip('.') if '.' in n else n
                            out.add(n.lstrip('0') or '0')
                        return out
                    key_lines=[l for l in base if l.startswith('- **') or l.startswith('Chennai forecast')]
                    required=norm('\n'.join(key_lines)); allowed=norm('\n'.join(base))|{'7','14'}
                    for iso in re.findall(r'\b(\d{4})-(\d{2})-(\d{2})\b','\n'.join(base)):
                        allowed|={iso[0],iso[1].lstrip('0'),iso[2].lstrip('0')}
                    found=norm(generated)
                    missing=sorted(required-found); invented=sorted(found-allowed)
                    asof=context['price_as_of']; y,m,dd=asof.split('-')
                    import calendar
                    date_ok=asof in generated or (f"{int(dd)} {calendar.month_name[int(m)]} {y}" in generated) or (f"{calendar.month_name[int(m)]} {int(dd)}, {y}" in generated)
                    if not date_ok: missing.append(f'price-as-of date {asof}')
                    context['llm_check']={'required_numbers':len(required),'missing':missing[:20],'unexpected':invented[:20],'date_preserved':date_ok}
                    if not generated: llm_status='local_model_empty_fallback_template'
                    elif missing or invented:
                        llm_status=f'local_model_rejected_numbers_changed (missing {len(missing)}, unexpected {len(invented)}); fallback_template'
                    else:
                        text=generated+'\n\n---\n'+'\n'.join(base[2:5])+f'\n\n*Rewritten by local model {model}; all {len(required)} numbers verified against the template.*'
                        llm_status='local_model_used_numbers_verified'
                except Exception as exc: llm_status='local_model_unavailable_fallback_template: '+str(exc)[:180]
        context['brief_markdown']=text; context['llm_status']=llm_status
        return context

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--live',action='store_true',help='Fetch Open-Meteo forecast and official PIB RSS. Requires network access.')
    parser.add_argument('--llm',action='store_true',help='Use local Ollama-compatible model; never calls a hosted LLM.')
    args=parser.parse_args(); OUT.mkdir(parents=True,exist_ok=True)
    context=DataCollectorAgent().run(args.live)
    context=ForecastAgent().run(context)
    context=NewsReaderAgent().run(context,args.live)
    context=ReportWriterAgent(args.llm).run(context)
    (OUT/'agrisight_brief.md').write_text(context['brief_markdown']+'\n',encoding='utf-8')
    safe={k:v for k,v in context.items() if k!='brief_markdown'}
    (OUT/'agrisight_pipeline.json').write_text(json.dumps(safe,indent=2,default=str),encoding='utf-8')
    print(f"Wrote {len(context['forecasts'])} commodity forecasts; weather={context.get('weather_status')}; news={context.get('news_status')}; LLM={context['llm_status']}; live={args.live}")

if __name__=='__main__': main()
