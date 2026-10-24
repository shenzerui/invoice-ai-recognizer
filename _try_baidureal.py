"""用新上传的真实图片走完整链路"""
import base64, json, requests, sys, os
sys.path.insert(0, r'C:\Users\Shen Zerui\Documents\Trae-CN\temp_20261023_01\backend')
from app.utils.settings_manager import SettingsManager

SRC = r"c:\Users\Shen Zerui\.trae-cn\attachments\8a35614c-43ca-4ad7-88f4-cfdc878675ab_fe028399-5fb6-4094-85d6-e5d973d54f10_e35de0c5-4fd0-4ae3-a04c-6130112fd374.png"
print(f"图片存在: {os.path.exists(SRC)}, 大小: {os.path.getsize(SRC)} bytes")

# 先试通用 OCR —— 看是什么票据
s = SettingsManager.load()
r = requests.get(
    "https://aip.baidubce.com/oauth/2.0/token",
    params={"grant_type":"client_credentials","client_id":s["baidu_api_key"],"client_secret":s["baidu_secret_key"]},
    timeout=10,
)
TOKEN = r.json()["access_token"]
with open(SRC, "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

# 1. 通用 OCR 先看是什么
url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic?access_token={TOKEN}"
r = requests.post(url, data={"image": b64}, headers={"Content-Type":"application/x-www-form-urlencoded"}, timeout=30)
data = r.json()
print("\n===== 通用 OCR 识别到的文字 =====")
for it in data.get("words_result", []):
    print("  ", it["words"])

# 2. 再打 vat_invoice 看能不能直接结构化
url2 = f"https://aip.baidubce.com/rest/2.0/ocr/v1/vat_invoice?access_token={TOKEN}"
r2 = requests.post(url2, data={"image": b64}, headers={"Content-Type":"application/x-www-form-urlencoded"}, timeout=30)
data2 = r2.json()
print("\n===== vat_invoice 增值税发票接口 =====")
if "result" in data2:
    result = data2["result"]
    print(f"票据类型: {result.get('invoice_type')}")
    print(f"发票代码: {result.get('invoice_code')}")
    print(f"发票号码: {result.get('invoice_number')}")
    print(f"开票日期: {result.get('invoice_date')}")
    print(f"购买方:   {result.get('buyer_name')}")
    print(f"销售方:   {result.get('seller_name')}")
    print(f"金额不含税: {result.get('amount_without_tax')}")
    print(f"税额:       {result.get('tax_amount')}")
    print(f"价税合计:   {result.get('total_amount')}")
else:
    print(json.dumps(data2, ensure_ascii=False, indent=2))
