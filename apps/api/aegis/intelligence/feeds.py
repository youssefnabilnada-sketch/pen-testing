"""Provenance-constrained official-source adapters. Never execute feed content.
CISA full catalog; NVD incremental windows; reviewed GHSA incremental cursor pages;
OSV refreshes public advisory identifiers, never sends customer inventory externally.
"""
import http.client
import json
import re
import socket
import ssl
import threading
import time
from datetime import datetime, timezone
from urllib.parse import urlencode, urlsplit, parse_qs
from pydantic import BaseModel, Field
from ..safety import resolve

SOURCES = {
 'cisa':('www.cisa.gov','/sites/default/files/feeds/known_exploited_vulnerabilities.json'),
 'nvd':('services.nvd.nist.gov','/rest/json/cves/2.0'),
 'github':('api.github.com','/advisories'),
 'osv':('api.osv.dev','/v1/vulns/'),
}
REFERENCE_PAGES = {
 'cisa':'https://www.cisa.gov/known-exploited-vulnerabilities-catalog',
 'nvd':'https://nvd.nist.gov/developers/vulnerabilities',
 'github':'https://docs.github.com/en/rest/security-advisories/global-advisories',
 'osv':'https://google.github.io/osv.dev/api/',
}
ID_PATTERN = r'(?:CVE-\d{4}-\d{4,}|GHSA-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}|[A-Z][A-Z0-9-]{2,90})'

class FeedError(ValueError):pass

class Record(BaseModel):
    identifiers: list[str] = Field(min_length=1,max_length=30)
    title: str = Field(min_length=1,max_length=400)
    description: str = Field(max_length=30000)
    affected: list[dict] = Field(default_factory=list,max_length=3000)
    severity: str = 'unknown'
    exploited: bool = False
    published: str = ''
    modified: str = ''
    remediation: str = 'Review the official advisory; a specific patch has not been established by this source.'
    references: list[str] = Field(default_factory=list,max_length=100)
    withdrawn: bool = False


def safe_link(url):
    try:
        p=urlsplit(url)
        return p.scheme=='https' and bool(p.hostname) and not p.username and not p.password and p.port in (None,443) and len(url)<2000
    except (TypeError,ValueError):return False


def record(data):
    result=Record(**data).model_dump()
    if not all(re.fullmatch(ID_PATTERN,x) for x in result['identifiers']):raise FeedError('Invalid advisory identifier')
    if result['severity'] not in ('unknown','low','medium','high','critical'):result['severity']='unknown'
    result['references']=[x for x in result['references'] if safe_link(x)]
    if not result['references']:raise FeedError('Advisory has no valid provenance link')
    return result


def request(source, path, params=None):
    if source not in SOURCES:raise FeedError('Source is not approved')
    host,base=SOURCES[source]
    if source=='osv':
        if not path.startswith(base) or not re.fullmatch(ID_PATTERN,path[len(base):]):raise FeedError('Unapproved OSV record path')
    elif path!=base:raise FeedError('Unapproved source path')
    _,port,ip,_=resolve('https://'+host)
    conn=http.client.HTTPConnection(host,443,timeout=10)
    sock=socket.create_connection((ip,port),timeout=10)
    def abort():
        try:sock.shutdown(socket.SHUT_RDWR)
        except OSError:pass
    timer=threading.Timer(25,abort);timer.daemon=True;timer.start()
    try:
        sock=ssl.create_default_context().wrap_socket(sock,server_hostname=host);conn.sock=sock
        target=path+('?' + urlencode(params) if params else '')
        conn.request('GET',target,headers={'Host':host,'User-Agent':'AEGIS-Defensive-Intelligence/0.2','Accept':'application/json','Accept-Encoding':'identity','Connection':'close'})
        response=conn.getresponse()
        if response.status!=200:raise FeedError(f'Official source returned HTTP {response.status}; no redirect followed')
        payload=response.read(12*1024*1024+1)
        if len(payload)>12*1024*1024:raise FeedError('Source response exceeds 12 MiB')
        return json.loads(payload),dict(response.getheaders())
    finally:
        timer.cancel();conn.close();sock.close()


def cisa(data):
    rows=data['vulnerabilities']
    if not isinstance(rows,list) or data.get('count')!=len(rows) or not rows:raise FeedError('Incomplete CISA catalog')
    return [record({'identifiers':[r['cveID']],'title':r['vulnerabilityName'],'description':r['shortDescription'],
        'affected':[{'ecosystem':'vendor','name':r['product'],'vendor':r['vendorProject'],'range':None,'fixed':None}],
        'exploited':True,'published':r['dateAdded'],'modified':r['dateAdded'],'remediation':r['requiredAction'],
        'references':['https://www.cisa.gov/known-exploited-vulnerabilities-catalog']+re.findall(r'https://[^\s;]+',r.get('notes',''))}) for r in rows]


def nvd(data):
    result=[]
    def affected(nodes):
        out=[]
        for node in nodes:
            for m in node.get('cpeMatch',[]):
                if m.get('vulnerable'):
                    parts=m['criteria'].split(':')
                    if len(parts)>=6:out.append({'ecosystem':'cpe','name':parts[3]+':'+parts[4],'version':parts[5], 'constraints':{k:v for k,v in m.items() if k.startswith('version')},'range':None,'fixed':None})
            out.extend(affected(node.get('nodes',[])));out.extend(affected(node.get('children',[])))
        return out
    for item in data['vulnerabilities']:
        r=item['cve'];identifier=r['id'];description=next((d['value'] for d in r['descriptions'] if d['lang']=='en'),identifier)
        metrics=r.get('metrics',{});metric=next((metrics[k][0] for k in ['cvssMetricV40','cvssMetricV31','cvssMetricV30','cvssMetricV2'] if metrics.get(k)),{})
        result.append(record({'identifiers':[identifier],'title':description[:400],'description':description[:30000],
            'affected':affected(r.get('configurations',[])),'severity':metric.get('cvssData',{}).get('baseSeverity',metric.get('baseSeverity','unknown')).lower(),
            'published':r['published'],'modified':r['lastModified'],'withdrawn':r.get('vulnStatus')=='Rejected',
            'references':['https://nvd.nist.gov/vuln/detail/'+identifier]+[x['url'] for x in r.get('references',[])][:99]}))
    return result


def github(data):
    if not isinstance(data,list):raise FeedError('Expected advisory list')
    result=[]
    for r in data:
        if r['type']!='reviewed' or not r.get('github_reviewed_at'):raise FeedError('Unreviewed GitHub advisory rejected')
        result.append(record({'identifiers':[r['ghsa_id']]+([r['cve_id']] if r.get('cve_id') else []),
            'title':r['summary'][:400],'description':(r.get('description') or r['summary'])[:30000],
            'severity':r['severity'],'published':r['published_at'],'modified':r['updated_at'],'withdrawn':bool(r.get('withdrawn_at')),
            'affected':[{'ecosystem':'PyPI' if v['package']['ecosystem']=='pip' else v['package']['ecosystem'], 'name':v['package']['name'],'range':v.get('vulnerable_version_range'),'fixed':v.get('first_patched_version')} for v in r.get('vulnerabilities',[])],
            'references':['https://github.com/advisories/'+r['ghsa_id']]+r.get('references',[])[:99]}))
    return result


def osv(data):
    identifier=data['id']
    return record({'identifiers':[identifier]+data.get('aliases',[])[:29],'title':(data.get('summary') or identifier)[:400],
        'description':data.get('details','')[:30000],'modified':data['modified'],'published':data.get('published',''),'withdrawn':bool(data.get('withdrawn')),
        'affected':[{'ecosystem':a['package']['ecosystem'],'name':a['package']['name'],'versions':a.get('versions',[]), 'ranges':a.get('ranges',[]), 'fixed':[e['fixed'] for rg in a.get('ranges',[]) for e in rg.get('events',[]) if 'fixed' in e]} for a in data.get('affected',[])],
        'references':['https://osv.dev/vulnerability/'+identifier]+[x['url'] for x in data.get('references',[])][:99]})


def iso(timestamp):return datetime.fromtimestamp(timestamp,timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')


def collect(source, cursor, now, known_ids=(), transport=request, pause=time.sleep):
    """Do not advance the checkpoint until every bounded page has validated."""
    if source=='cisa':return cisa(transport(source,SOURCES[source][1])[0]),{'through':now}
    start=float(cursor.get('through',now-86400))-60
    end=min(now,start+119*86400)
    if source=='nvd':
        rows=[];index=0
        for page in range(20):
            if page:pause(6) # Conservative unauthenticated NVD request pacing.
            data,_=transport(source,SOURCES[source][1],{'lastModStartDate':iso(start),'lastModEndDate':iso(end),'startIndex':index,'resultsPerPage':2000})
            parsed=nvd(data)
            if data['startIndex']!=index or (not parsed and index<data['totalResults']):raise FeedError('Incomplete NVD pagination')
            rows.extend(parsed);index+=len(parsed)
            if index>=data['totalResults']:return rows,{'through':end}
        raise FeedError('NVD page budget exceeded; checkpoint retained')
    if source=='github':
        rows=[];after=None
        for page in range(20):
            if page:pause(1)
            params={'type':'reviewed','modified':iso(start)+'..'+iso(end),'sort':'updated','direction':'asc','per_page':100}
            if after:params['after']=after
            data,headers=transport(source,SOURCES[source][1],params);rows.extend(github(data))
            link=next((v for k,v in headers.items() if k.lower()=='link'),'')
            next_link=next((x for x in link.split(',') if 'rel="next"' in x),None)
            if not next_link:return rows,{'through':end}
            match=re.search(r'<([^>]+)>',next_link)
            if not match:raise FeedError('Malformed pagination')
            p=urlsplit(match.group(1))
            if p.scheme!='https' or p.netloc!='api.github.com' or p.path!='/advisories':raise FeedError('Pagination source escape rejected')
            after=parse_qs(p.query).get('after',[''])[0]
            if not after or len(after)>500:raise FeedError('Invalid pagination cursor')
        raise FeedError('GitHub page budget exceeded; checkpoint retained')
    if source=='osv':
        # Rotating refresh of public IDs already discovered from official sources.
        ids=sorted(set(i for i in known_ids if i.startswith('GHSA-')))
        offset=int(cursor.get('offset',0));batch=ids[offset:offset+25]
        rows=[]
        for identifier in batch:
            data,_=transport(source,SOURCES[source][1]+identifier);rows.append(osv(data))
        return rows,{'offset':offset+len(batch) if offset+len(batch)<len(ids) else 0,'through':now,'coverage':'known public advisory IDs only'}
    raise FeedError('Unknown intelligence source')
