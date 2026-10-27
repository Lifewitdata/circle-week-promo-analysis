"""Create a native CSV-backed Tableau package without advanced XML extensions.

XML/ZIP validation is automatic. Native Tableau rendering requires Tableau Desktop
or Tableau Public and is deliberately not represented as tested in this container.
"""
from pathlib import Path
import xml.etree.ElementTree as E
from zipfile import ZipFile,ZIP_DEFLATED
import shutil
import pandas as pd


def add(parent,tag,text=None,**attrs):
    node=E.SubElement(parent,tag,{k.replace('_','-'):str(v) for k,v in attrs.items()})
    if text is not None:
        node.text=text
    return node


def package(dashboard,reports):
    data=dashboard/'Data';data.mkdir(exist_ok=True)
    definitions=[('Weekly revenue','weekly_trend.csv','week_start_date','revenue','test_group','Line'),
                 ('Category effects','category_effects.csv','category','effect_usd_per_store_week',None,'Bar'),
                 ('Regional effects','region_effects.csv','region','effect_usd_per_store_week',None,'Bar'),
                 ('Cost scenarios','scenarios.csv','scenario','incremental_contribution_usd',None,'Bar')]
    root=E.Element('workbook',{'original-version':'18.1','source-build':'2021.4.0 (20214.21.1112.1435)','source-platform':'win','version':'18.1','xmlns:user':'http://www.tableausoftware.com/xml/user'})
    add(root,'preferences')
    sources=add(root,'datasources')
    worksheets=add(root,'worksheets')
    for i,(title,file,dimension,measure,color,mark) in enumerate(definitions):
        shutil.copy2(reports/file,data/file)
        df=pd.read_csv(data/file)
        name=f'csv{i}'
        ds=add(sources,'datasource',caption=title,inline='true',name=name,version='18.1')
        con=add(ds,'connection',**{'class':'textscan','directory':'Data','filename':file,'password':'','server':'','header':'yes','separator':','})
        rel=add(con,'relation',name=file,table=f'[{file}]',type='table')
        columns=add(rel,'columns',header='yes',separator=',')
        kinds={}
        for ordinal,column in enumerate(df.columns):
            kind='real' if pd.api.types.is_numeric_dtype(df[column]) else 'string'
            kinds[column]=kind
            add(columns,'column',datatype=kind,name=column,ordinal=ordinal)
        metadata=add(con,'metadata-records')
        for ordinal,column in enumerate(df.columns):
            rec=add(metadata,'metadata-record',**{'class':'column'})
            for tag,value in [('remote-name',column),('remote-type','5' if kinds[column]=='real' else '129'),('local-name',f'[{column}]'),('parent-name',f'[{file}]'),('remote-alias',column),('ordinal',ordinal),('local-type',kinds[column]),('aggregation','Sum' if kinds[column]=='real' else 'Count'),('contains-null','true')]:
                add(rec,tag,text=str(value))
        for column,kind in kinds.items():
            add(ds,'column',datatype=kind,name=f'[{column}]',role='measure' if kind=='real' else 'dimension',type='quantitative' if kind=='real' else 'nominal')
        sheet=add(worksheets,'worksheet',name=title)
        layout=add(sheet,'layout-options'); run=add(add(add(layout,'title'),'formatted-text'),'run',text=f'{title} | synthetic data')
        table=add(sheet,'table');view=add(table,'view')
        add(add(view,'datasources'),'datasource',caption=title,name=name)
        dep=add(view,'datasource-dependencies',datasource=name)
        used=[dimension,measure]+([color] if color else [])
        for column in used:
            kind=kinds[column]
            add(dep,'column',datatype=kind,name=f'[{column}]',role='measure' if kind=='real' else 'dimension',type='quantitative' if kind=='real' else 'nominal')
            add(dep,'column-instance',column=f'[{column}]',derivation='Avg' if kind=='real' else 'None',name=f'[avg:{column}:qk]' if kind=='real' else f'[none:{column}:nk]',pivot='key',type='quantitative' if kind=='real' else 'nominal')
        add(view,'aggregation',value='true')
        add(table,'style')
        pane=add(add(table,'panes'),'pane',selection_relaxation_option='selection-relaxation-allow')
        add(add(pane,'view'),'breakdown',value='auto')
        add(pane,'mark',**{'class':mark})
        enc=add(pane,'encodings')
        if color:
            add(enc,'color',column=f'[{name}].[none:{color}:nk]')
        if mark=='Line':
            add(table,'rows',text=f'[{name}].[avg:{measure}:qk]')
            add(table,'cols',text=f'[{name}].[none:{dimension}:nk]')
        else:
            add(table,'rows',text=f'[{name}].[none:{dimension}:nk]')
            add(table,'cols',text=f'[{name}].[avg:{measure}:qk]')
    dashboards=add(root,'dashboards')
    board=add(dashboards,'dashboard',name='Promotion decision brief')
    add(board,'style')
    add(board,'size',maxheight='900',maxwidth='1300',minheight='900',minwidth='1300',sizing_mode='fixed')
    zones=add(board,'zones')
    for i,(title,*_) in enumerate(definitions):
        add(zones,'zone',h='46000',w='47000',x=str(1500+(i%2)*50000),y=str(1500+(i//2)*50000),id=i+1,name=title)
    windows=add(root,'windows',source_height='30')
    for title,*_ in definitions:
        win=add(windows,'window',**{'class':'worksheet','name':title});add(win,'viewpoint',zoom='entire-view')
    win=add(windows,'window',**{'class':'dashboard','name':'Promotion decision brief'})
    views=add(win,'viewpoints')
    for title,*_ in definitions:
        add(views,'viewpoint',name=title,zoom='entire-view')
    twb=dashboard/'Circle_Week.twb'
    E.indent(root)
    E.ElementTree(root).write(twb,encoding='utf-8',xml_declaration=True)
    with ZipFile(dashboard/'Circle_Week.twbx','w',ZIP_DEFLATED) as z:
        z.write(twb,twb.name)
        for file in sorted(data.glob('*.csv')):
            z.write(file,'Data/'+file.name)
    # Structural validation: no missing files or unresolved dataset references.
    E.parse(twb)
    with ZipFile(dashboard/'Circle_Week.twbx') as z:
        if z.testzip() is not None:
            raise ValueError('Corrupt Tableau package')
