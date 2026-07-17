import pandas as pd
import json
# 读取 Excel 文件，默认取第一个工作表
file_path = r"E:\MiniEnz_Methodology\reports\figures_and_data\data\1323.xlsx"
df = pd.read_excel(file_path, sheet_name='Figure2_MPNN_all_scores')

# 转为 JSON，orient='records' 表示生成对象数组
unique_enzymes = df["enzyme"].drop_duplicates().tolist()
result_dict = {}
for enzyme_name in unique_enzymes:
     group = df[df["enzyme"] == enzyme_name]
     scores_list = group["score"].tolist()
     result_dict[enzyme_name] = {
         "enzyme": enzyme_name,
         "n_sequences": len(scores_list),
         "mean": round(group["score"].mean(),4),
         "std": round(group["score"].std(),4),
         "min": round(group["score"].min(),4),
         "max": round(group["score"].max(),4),
         "q25": round(group["score"].quantile(0.25),4),
         "q50": round(group["score"].quantile(0.50),4),
         "q75": round(group["score"].quantile(0.75),4),
         "scores": scores_list
     }
with open("输出.json", "w", encoding="utf-8") as f:
     json.dump(result_dict, f, ensure_ascii=False, indent=2)
print("JSON")