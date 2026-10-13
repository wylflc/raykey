import json, sys, urllib.request, urllib.parse
UA={"User-Agent":"Mozilla/5.0"}
def page(code, begin, end, idx, size=100):
    q=urllib.parse.urlencode(dict(sr=-1,page_size=size,page_index=idx,ann_type="A",client_source="web",stock_list=code,begin_time=begin,end_time=end))
    return json.load(urllib.request.urlopen(urllib.request.Request("https://np-anotice-stock.eastmoney.com/api/security/ann?"+q,headers=UA),timeout=30))
if __name__=="__main__":
    code,begin,end=sys.argv[1:4]
    r=page(code,begin,end,1)
    d=r.get("data") or {}
    print("total_hits",d.get("total_hits"),"rows",len(d.get("list") or []))
    for a in (d.get("list") or []):
        print(a["notice_date"][:10], "|", ",".join(c["column_name"] for c in a.get("columns") or []), "|", a["title"][:70])
