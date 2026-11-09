"""Excel export of per-article recommendations and the business case."""
import numpy as np, pandas as pd, json
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.formatting.rule import CellIsRule


def write_workbook(R, K, F, FI, S, p_cls, path):
    """R: per-article table, K: policy KPIs, F: trade-off grid, FI: feature relevance,
    S: sensitivity KPIs, p_cls: calibrated service parameter per ABC class."""
    AR='Arial'; H=Font(name=AR,bold=True,color='FFFFFF'); HF=PatternFill('solid',fgColor='1F3A5F')
    B=Font(name=AR); BB=Font(name=AR,bold=True); BLUE=Font(name=AR,color='0000FF'); TITLE=Font(name=AR,bold=True,size=14)
    NOTE=Font(name=AR,italic=True,color='595959',size=9); YEL=PatternFill('solid',fgColor='FFFF00')
    wb=Workbook()
    # ---------------- Recommendations
    ws=wb.active; ws.title='Recommendations'
    cols=list(R.reset_index().columns)
    ins=cols.index('Recommended ROP')+1
    cols.insert(ins,'ROP change %')
    df=R.reset_index()
    ws.append(cols)
    for c in ws[1]: c.font=H; c.fill=HF; c.alignment=Alignment(wrap_text=True,vertical='center')
    L={c:get_column_letter(i+1) for i,c in enumerate(cols)}
    for r,row in enumerate(df.itertuples(index=False),start=2):
        vals=list(row); vals.insert(ins,None)
        for j,v in enumerate(vals):
            if isinstance(v,float) and not np.isfinite(v): v=None
            ws.cell(r,j+1,v).font=B
        ws.cell(r,ins+1,f'=IF({L["Current ROP"]}{r}>0,{L["Recommended ROP"]}{r}/{L["Current ROP"]}{r}-1,"")').font=B
    n=len(df)+1
    fmt={'Purchase price':'#,##0.00','Usage last 12m (units)':'#,##0','Avg daily base demand':'#,##0.00','Current ROP':'#,##0','Recommended ROP':'#,##0',
         'Recommended safety stock':'#,##0','ROP change %':'0%;-0%;0%','Service parameter':'0.0%','MOQ':'#,##0','Typical order qty':'#,##0',
         'Procure-to-order above (units/day)':'#,##0','Sim. avg stock value - current':'#,##0','Sim. avg stock value - recommended':'#,##0',
         'Sim. fill rate - current':'0.0%','Sim. fill rate - recommended':'0.0%','Actual avg stock value 2021':'#,##0'}
    for c,f in fmt.items():
        for r in range(2,n+1): ws[f'{L[c]}{r}'].number_format=f
    widths={'Action':44,'Notes':48,'Method':30,'Product type':22,'Vendor':20,'Demand pattern':13}
    for c in cols: ws.column_dimensions[L[c]].width=widths.get(c,13)
    ws.row_dimensions[1].height=45; ws.freeze_panes='B2'
    t=Table(displayName='Recommendations',ref=f'A1:{get_column_letter(len(cols))}{n}')
    t.tableStyleInfo=TableStyleInfo(name='TableStyleLight9',showRowStripes=True); ws.add_table(t)
    g=PatternFill('solid',fgColor='E2EFDA'); o=PatternFill('solid',fgColor='FCE4D6')
    rng=f'{L["Action"]}2:{L["Action"]}{n}'
    ws.conditional_formatting.add(rng,CellIsRule(operator='equal',formula=['"Reduce ROP"'],fill=g))
    ws.conditional_formatting.add(rng,CellIsRule(operator='equal',formula=['"Increase ROP"'],fill=o))
    RS="Recommendations"
    # ---------------- Summary
    s=wb.create_sheet('Summary',0)
    s['A1']='Part 3 · Demand-driven reorder points & safety stock — summary'; s['A1'].font=TITLE
    s['A2']='Inventory articles (safety stock > 0). Simulation test year 21.01.2021–21.01.2022; values in dataset currency units at current purchase price.'; s['A2'].font=NOTE
    rows=[('Business case',None,None),
    ('Holding cost rate (assumption, p.a.)',0.20,'Input: typical 15–25% (capital, storage, obsolescence). Not given in the case.'),
    ('Actual avg stock value 2021',f"=SUM({RS}[Actual avg stock value 2021])",'Observed stock, rebuilt from transactions'),
    ('Recommended policy: simulated avg stock value',f"=SUM({RS}[Sim. avg stock value - recommended])",'Monthly-updated demand-driven ROPs, same order sizes as today'),
    ('Capital released vs actual 2021','=B5-B6',None),
    ('Capital released vs actual 2021 (%)','=IF(B5>0,B7/B5,0)',None),
    ('Annual holding-cost saving','=B7*B4',None),
    ('Recommended policy: fill rate (value-weighted)',float(K.loc['Demand-driven, monthly update (recommended)','fill']),'Simulation output'),
    ('Recommended policy: fill rate A-articles',float(K.loc['Demand-driven, monthly update (recommended)','fill_A']),'Simulation output'),
    ('Current ROPs followed strictly: fill rate',float(K.loc['Current ROP (master data)','fill']),'Simulation output: today\'s ROPs alone do not protect availability'),
    (None,None,None),
    ('Article actions',None,None)]
    for i,(a,b,c) in enumerate(rows,start=3):
        s[f'A{i}']=a; s[f'B{i}']=b; s[f'C{i}']=c
        s[f'A{i}'].font=BB if b is None else B; s[f'C{i}'].font=NOTE
        if isinstance(b,str) and b.startswith('='): s[f'B{i}'].font=B
    s['B4'].font=BLUE; s['B4'].fill=YEL
    for r in [5,6,7,9]: s[f'B{r}'].number_format='#,##0'
    for r in [4,8,10,11,12]: s[f'B{r}'].number_format='0.0%'
    r=15; s[f'A{r}']='Action'; s[f'B{r}']='Articles'; s[f'C{r}']='Recommended stock value'
    for c in 'ABC': s[f'{c}{r}'].font=H; s[f'{c}{r}'].fill=HF
    for a in R.Action.value_counts().index:
        r+=1; s[f'A{r}']=a; s[f'B{r}']=f'=COUNTIF({RS}[Action],A{r})'; s[f'C{r}']=f'=SUMIF({RS}[Action],A{r},{RS}[Sim. avg stock value - recommended])'
        s[f'C{r}'].number_format='#,##0'
        for c in 'ABC': s[f'{c}{r}'].font=B
    r+=1; s[f'A{r}']='Total'; s[f'B{r}']=f'=SUM(B16:B{r-1})'; s[f'C{r}']=f'=SUM(C16:C{r-1})'; s[f'C{r}'].number_format='#,##0'
    for c in 'ABC': s[f'{c}{r}'].font=BB
    r+=2; s[f'A{r}']='Calibrated service parameter by ABC class (set by simulation on 2020)'; s[f'A{r}'].font=BB
    for k,v in p_cls.items():
        r+=1; s[f'A{r}']=f'Class {k}'; s[f'B{r}']=v; s[f'B{r}'].number_format='0.0%'; s[f'A{r}'].font=B; s[f'B{r}'].font=B
    s.column_dimensions['A'].width=52; s.column_dimensions['B'].width=18; s.column_dimensions['C'].width=70
    # ---------------- Policy comparison
    pc=wb.create_sheet('Policy comparison')
    pc['A1']='Same simulator, same demand (peaks procured to order), same order sizes; test year 2021'; pc['A1'].font=NOTE
    hdr=['Policy','Avg stock value','Fill rate','Fill A','Fill B','Fill C','Articles with stock-out','Orders']
    pc.append([]); pc.append(hdr)
    for c in pc[3]: c.font=H; c.fill=HF
    allK=pd.concat([K,S.iloc[1:]])
    for name,row in allK.iterrows():
        pc.append([name,row.lockup,row.fill,row.fill_A,row.fill_B,row.fill_C,int(row.stockout_articles),int(row.orders)])
    for row in pc.iter_rows(min_row=4):
        for c in row: c.font=B
        row[1].number_format='#,##0'
        for c in row[2:6]: c.number_format='0.0%'
    pc.column_dimensions['A'].width=55
    for c in 'BCDEFGH': pc.column_dimensions[c].width=14
    # ---------------- Trade-off
    tf=wb.create_sheet('Trade-off curve')
    tf.append(['Service parameter','Avg stock value','Fill rate','Fill A'])
    for c in tf[1]: c.font=H; c.fill=HF
    for _,x in F.iterrows(): tf.append([x.p,x.lockup,x.fill,x.fill_A])
    for row in tf.iter_rows(min_row=2):
        row[0].number_format='0.0%'; row[1].number_format='#,##0'; row[2].number_format='0.0%'; row[3].number_format='0.0%'
        for c in row: c.font=B
    for c in 'ABCD': tf.column_dimensions[c].width=18
    # ---------------- Features
    fs=wb.create_sheet('Feature relevance')
    fs['A1']='Drivers of the simulation-optimal ROP (in days of demand) · Random forest, 5-fold CV R² ≈ 0.61'; fs['A1'].font=NOTE
    fs.append([]); fs.append(['Feature','Permutation importance','Mutual information','Spearman rho'])
    for c in fs[3]: c.font=H; c.fill=HF
    for name,x in FI.iterrows(): fs.append([name,x.permutation_importance,x.mutual_information,x.spearman_rho])
    for row in fs.iter_rows(min_row=4):
        for c in row: c.font=B
        for c in row[1:]: c.number_format='0.000'
    fs.column_dimensions['A'].width=38
    for c in 'BCD': fs.column_dimensions[c].width=20
    # ---------------- Method
    m=wb.create_sheet('Method & assumptions')
    txt=["Method",
    "1. Demand = net sales (type 1) + usage for production (type 5). One-off peaks (daily demand > Q3 + 3·IQR of the article's non-zero days) are 'searched demand' and procured to order.",
    "2. Every month, for each article, ROP is recalculated on the last 365 days of base demand (from first demand for new articles).",
    "3. Smooth/erratic demand: ROP = mean daily demand × LT + z(p) × σ(weekly) × √(LT/7).  Intermittent/lumpy/sporadic: ROP = p-quantile of historical lead-time demand.",
    "4. No demand in 12 months → ROP = 0.  No lead time maintained → company fallback (usage 12m / 4).",
    "5. Service parameter p per ABC class calibrated by simulation on 2020 to reach fill targets A 98% / B 95% / C 90% (A and B cap at 99.5%).",
    "6. Policies evaluated out-of-sample on 2021 with a daily (s, Q) simulation: lead time from master data, today's typical order size, back-orders.",
    "Safety stock = recommended ROP − mean demand during lead time.",
    "",
    "Assumptions & limitations",
    "• Master data (safety stock, lead time, MOQ, price) is a 2022 snapshot; history is valued at today's price.",
    "• Quantities are anonymised by a constant factor (≈1.1107); ratios are unaffected.",
    "• No order dates → lead-time variability cannot be measured. Stress test: +50% lead time drops fill to ~87%.",
    "• The recorded actual fill rate (~99.6%) is likely censored (usage is only booked when stock exists), so service is compared within the simulation.",
    "• Holding cost rate is an assumption (input cell on Summary)."]
    for i,t_ in enumerate(txt,1):
        m[f'A{i}']=t_; m[f'A{i}'].font=BB if t_ in ('Method','Assumptions & limitations') else B
    m.column_dimensions['A'].width=150
    wb.save(path)
