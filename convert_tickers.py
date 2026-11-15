import pandas as pd
import requests
import urllib3

# 忽略政府網站 SSL 憑證警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_tw_stock_suffix_map():
    suffix_map = {}
    
    # 1. 抓取上市股票清單 (TWSE, mode=2) -> 加上 .TW
    url_twse = "https://twse.com.tw"
    res_twse = requests.get(url_twse, verify=False)
    df_twse = pd.read_html(res_twse.text)[0]
    for item in df_twse[0]:
        if isinstance(item, str) and "\u3000" in item:
            code = item.split("\u3000")[0].strip()
            suffix_map[code] = f"{code}.TW"
            
    # 2. 抓取上櫃股票清單 (TPEx, mode=4) -> 加上 .TWO
    url_tpex = "https://twse.com.tw"
    res_tpex = requests.get(url_tpex, verify=False)
    df_tpex = pd.read_html(res_tpex.text)[0]
    for item in df_tpex[0]:
        if isinstance(item, str) and "\u3000" in item:
            code = item.split("\u3000")[0].strip()
            suffix_map[code] = f"{code}.TWO"
            
    return suffix_map

def convert_csv(input_file="raw_stocks.csv", output_file="stock_list.csv"):
    # 讀取原始 CSV，強制將第一欄讀取為字串以免 0050 變成 50
    df = pd.read_csv(input_file, dtype={0: str})
    
    # 取得欄位名稱
    code_col = df.columns[0]
    name_col = df.columns[1]
    
    # 清理空白字元
    df[code_col] = df[code_col].str.strip()
    
    print("正在從證交所/櫃買中心比對上市櫃屬性...")
    suffix_map = get_tw_stock_suffix_map()
    
    # 對應轉換代號
    df["查詢代號"] = df[code_col].map(suffix_map)
    
    # 檢查是否有找不到的代號（例如興櫃或已下市）
    missing = df[df["查詢代號"].isna()]
    if not missing.empty:
        print(f"警告：以下 {len(missing)} 檔找不到上市/上櫃資料，將被略過：")
        print(missing[[code_col, name_col]])
    
    # 保留成功配對的股票並存檔
    valid_df = df.dropna(subset=["查詢代號"]).copy()
    valid_df = valid_df[["查詢代號", name_col]]
    valid_df.columns = ["Ticker", "Name"]
    valid_df.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"轉換完成！共 {len(valid_df)} 檔股票已儲存至 {output_file}")

if __name__ == "__main__":
    convert_csv()
