import json, re, sys, collections, csv
POS = re.compile("行政处罚|处罚决定|事先告知书|立案|留置|被调查|接受调查|监管措施|警示函|监管函|监管工作函|监管关注|通报批评|公开谴责|纪律处分|责令改正|年度报告.{0,12}问询函|年报.{0,6}问询函|半年度报告.{0,12}问询函|诉讼|仲裁|安全事故|制裁名单|337调查|反倾销|反补贴|召回|保留意见|无法表示意见|否定意见|会计差错更正|前期差错|非经营性占用|失信被执行|被冻结|澄清")
NEG = re.compile("最近五年|管理办法|管理制度|制度\\(|审核问询函|汇总表|专项说明|专项审核|法律意见|募集资金专户|反洗钱|责任追究|内部问责|标准\\(")
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8")]
hits = [r for r in rows if POS.search(r["title"]) and not NEG.search(r["title"])]
by_month = collections.Counter(r["date"][:7] for r in hits)
print("命中", len(hits), "条", len({r["code"] for r in hits}), "家；按公司日去重", len({(r["code"], r["date"]) for r in hits}), "个公司日")
print(sorted(by_month.items()))
days = sorted({r["date"] for r in hits})
print("有命中的日数", len(days))
if len(sys.argv) > 2:
    with open(sys.argv[2], "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n"); w.writerow(["security_code", "security_name", "notice_date", "columns", "title", "url"])
        for r in sorted(hits, key=lambda x: (x["code"], x["date"])):
            w.writerow([r["code"], r["name"], r["date"], "|".join(r["cols"]), r["title"], f"https://pdf.dfcfw.com/pdf/H2_{r['art']}_1.pdf"])
for r in sorted(hits, key=lambda x: (x["code"], x["date"])):
    print(r["code"], r["name"], r["date"], "|", r["title"][len(r["name"]) + 1:][:46] if r["title"].startswith(r["name"]) else r["title"][:50])
