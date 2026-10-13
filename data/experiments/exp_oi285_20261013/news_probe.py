import json, sys, urllib.request, urllib.parse, re
UA={"User-Agent":"Mozilla/5.0","Referer":"https://so.eastmoney.com/"}
def search(keyword, page=1, size=50, sort="time"):
    param={"uid":"","keyword":keyword,"type":["cmsArticleWebOld"],"client":"web","clientType":"web","clientVersion":"curr",
           "param":{"cmsArticleWebOld":{"searchScope":"default","sort":sort,"pageIndex":page,"pageSize":size,"preTag":"","postTag":""}}}
    url="https://search-api-web.eastmoney.com/search/jsonp?cb=cb&param="+urllib.parse.quote(json.dumps(param,ensure_ascii=False))
    raw=urllib.request.urlopen(urllib.request.Request(url,headers=UA),timeout=30).read().decode("utf-8","replace")
    return json.loads(raw[raw.index("(")+1:raw.rindex(")")])
if __name__=="__main__":
    kw=sys.argv[1]; pages=int(sys.argv[2]) if len(sys.argv)>2 else 1
    for p in range(1,pages+1):
        r=search(kw,p)
        res=(r.get("result") or {}).get("cmsArticleWebOld") or []
        print("page",p,"n",len(res),"hitsTotal",r.get("hitsTotal"))
        for a in res:
            print(a.get("date","")[:10],"|",a.get("mediaName",""),"|",a.get("title","")[:60])
